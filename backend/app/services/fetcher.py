import base64
from os.path import splitext
from urllib.parse import urlparse

import httpx

from backend.app.config import settings
from backend.app.models.repo import FileNode, FileTree, RepoMetadata


class GitHubFetcher:
    """Async GitHub repository fetcher service."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "vibe-arch/0.1.0",
        }
        if settings.github_token:
            self.headers["Authorization"] = f"Bearer {settings.github_token}"

    async def fetch_metadata(self, owner: str, repo: str) -> RepoMetadata:
        """Fetch repo metadata from GitHub API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return RepoMetadata(
                owner=data["owner"]["login"],
                name=data["name"],
                description=data.get("description"),
                stars=data.get("stargazers_count", 0),
                topics=data.get("topics", []),
                language=data.get("language"),
                last_commit_date=data.get("pushed_at"),
                contributors_count=0,
            )

    async def fetch_file_tree(self, owner: str, repo: str) -> FileTree:
        """Fetch the repository file tree via GitHub Git Trees API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()

        items = data.get("tree", [])
        root = FileNode(path="", type="directory", children=[])

        for item in items:
            if item["type"] != "blob":
                continue
            path = item["path"]
            if self._should_skip_dir(path):
                continue
            if not self._is_source_file(path):
                continue

            parts = path.split("/")
            current = root

            for i in range(len(parts) - 1):
                child_path = "/".join(parts[: i + 1])
                existing = next(
                    (c for c in current.children if c.path == child_path), None
                )
                if existing:
                    current = existing
                else:
                    new_dir = FileNode(path=child_path, type="directory", children=[])
                    current.children.append(new_dir)
                    current = new_dir

            current.children.append(FileNode(path=path, type="file", children=[]))

        return FileTree(root=root)

    async def fetch_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch a single file's content."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return base64.b64decode(data["content"]).decode("utf-8")

    async def fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch the repository README."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/readme",
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return base64.b64decode(data["content"]).decode("utf-8")

    @staticmethod
    def parse_github_url(url: str) -> tuple[str, str] | None:
        """Parse a GitHub URL into (owner, repo)."""
        url = url.strip()
        if url.count("/") == 1 and not url.startswith("http"):
            parts = url.split("/")
            return parts[0], parts[1].replace(".git", "")

        parsed = urlparse(url)
        if parsed.netloc != "github.com":
            return None
        parts = parsed.path.strip("/").rstrip("/").split("/")
        if len(parts) < 2:
            return None
        return parts[0], parts[1].replace(".git", "")

    @staticmethod
    def _is_source_file(path: str) -> bool:
        """Check if a file is a source file worth analyzing."""
        source_extensions = {
            ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java",
            ".rb", ".php", ".swift", ".kt", ".scala", ".cs", ".c", ".cpp", ".h",
        }
        _, ext = splitext(path)
        return ext in source_extensions

    @staticmethod
    def _should_skip_dir(path: str) -> bool:
        """Check if a directory should be skipped."""
        skip_dirs = {
            "node_modules", ".git", "__pycache__", "venv", ".venv",
            "dist", "build", ".next", "target", "vendor", ".tox",
        }
        return any(d in path.split("/") for d in skip_dirs)
