from unittest.mock import MagicMock, patch

import pytest

from backend.app.models.repo import FileTree, RepoMetadata
from backend.app.services.fetcher import GitHubFetcher


@pytest.mark.asyncio
async def test_parse_github_url_https():
    owner, repo = GitHubFetcher.parse_github_url("https://github.com/owner/repo")
    assert owner == "owner"
    assert repo == "repo"


@pytest.mark.asyncio
async def test_parse_github_url_owner_slash_repo():
    owner, repo = GitHubFetcher.parse_github_url("owner/repo")
    assert owner == "owner"
    assert repo == "repo"


@pytest.mark.asyncio
async def test_parse_github_url_with_git_suffix():
    owner, repo = GitHubFetcher.parse_github_url("https://github.com/owner/repo.git")
    assert owner == "owner"
    assert repo == "repo"


@pytest.mark.asyncio
async def test_parse_github_url_trailing_slash():
    owner, repo = GitHubFetcher.parse_github_url("https://github.com/owner/repo/")
    assert owner == "owner"
    assert repo == "repo"


@pytest.mark.asyncio
async def test_parse_github_url_invalid_host():
    result = GitHubFetcher.parse_github_url("https://gitlab.com/owner/repo")
    assert result is None


@pytest.mark.asyncio
async def test_parse_github_url_empty():
    result = GitHubFetcher.parse_github_url("")
    assert result is None


@pytest.mark.asyncio
async def test_parse_github_url_malformed():
    result = GitHubFetcher.parse_github_url("not-a-url")
    assert result is None


def test_is_source_file_py():
    assert GitHubFetcher._is_source_file("main.py")


def test_is_source_file_ts():
    assert GitHubFetcher._is_source_file("component.ts")


def test_is_source_file_tsx():
    assert GitHubFetcher._is_source_file("component.tsx")


def test_is_source_file_js():
    assert GitHubFetcher._is_source_file("index.js")


def test_is_source_file_go():
    assert GitHubFetcher._is_source_file("server.go")


def test_is_source_file_rs():
    assert GitHubFetcher._is_source_file("lib.rs")


def test_is_source_file_non_source():
    assert not GitHubFetcher._is_source_file("readme.md")


def test_is_source_file_no_ext():
    assert not GitHubFetcher._is_source_file("Dockerfile")


def test_should_skip_dir_node_modules():
    assert GitHubFetcher._should_skip_dir("node_modules/foo/bar.js")


def test_should_skip_dir_git():
    assert GitHubFetcher._should_skip_dir(".git/config")


def test_should_skip_dir_pycache():
    assert GitHubFetcher._should_skip_dir("src/__pycache__/module.pyc")


def test_should_skip_dir_venv():
    assert GitHubFetcher._should_skip_dir("venv/lib/site-packages/pkg/main.py")


def test_should_skip_dir_dist():
    assert GitHubFetcher._should_skip_dir("dist/bundle.js")


def test_should_skip_dir_not_skipped():
    assert not GitHubFetcher._should_skip_dir("src/main.py")


def test_should_skip_dir_src_not_skipped():
    assert not GitHubFetcher._should_skip_dir("src/utils/helpers.py")


@pytest.mark.asyncio
async def test_fetch_metadata():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "owner": {"login": "test-owner"},
        "name": "test-repo",
        "description": "A test repository",
        "stargazers_count": 42,
        "topics": ["python", "cli"],
        "language": "Python",
        "pushed_at": "2024-06-01T12:00:00Z",
    }
    mock_response.raise_for_status = MagicMock()

    fetcher = GitHubFetcher()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )
        result = await fetcher.fetch_metadata("test-owner", "test-repo")

    assert isinstance(result, RepoMetadata)
    assert result.owner == "test-owner"
    assert result.name == "test-repo"
    assert result.description == "A test repository"
    assert result.stars == 42
    assert result.topics == ["python", "cli"]
    assert result.language == "Python"
    assert result.last_commit_date == "2024-06-01T12:00:00Z"


@pytest.mark.asyncio
async def test_fetch_metadata_sends_auth():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "owner": {"login": "o"},
        "name": "r",
    }
    mock_response.raise_for_status = MagicMock()

    fetcher = GitHubFetcher()

    with patch("httpx.AsyncClient") as mock_client:
        mock_instance = mock_client.return_value.__aenter__.return_value
        mock_instance.get.return_value = mock_response
        await fetcher.fetch_metadata("o", "r")

    mock_instance.get.assert_called_once()
    call_kwargs = mock_instance.get.call_args.kwargs
    assert "headers" in call_kwargs
    assert call_kwargs["headers"]["Accept"] == "application/vnd.github.v3+json"
    assert call_kwargs["headers"]["User-Agent"] == "vibe-arch/0.1.0"


@pytest.mark.asyncio
async def test_fetch_file_tree():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "tree": [
            {"path": "src/main.py", "type": "blob", "sha": "abc", "mode": "100644"},
            {
                "path": "src/utils/helpers.py",
                "type": "blob",
                "sha": "def",
                "mode": "100644",
            },
            {
                "path": "node_modules/pkg/index.js",
                "type": "blob",
                "sha": "ghi",
                "mode": "100644",
            },
            {"path": "README.md", "type": "blob", "sha": "jkl", "mode": "100644"},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    fetcher = GitHubFetcher()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )
        result = await fetcher.fetch_file_tree("test-owner", "test-repo")

    assert isinstance(result, FileTree)
    assert len(result.root.children) == 1
    src_dir = result.root.children[0]
    assert src_dir.type == "directory"
    assert src_dir.path == "src"
    assert len(src_dir.children) == 2

    main_py = src_dir.children[0]
    assert main_py.type == "file"
    assert main_py.path == "src/main.py"

    utils_dir = src_dir.children[1]
    assert utils_dir.type == "directory"
    assert utils_dir.path == "src/utils"
    assert len(utils_dir.children) == 1
    assert utils_dir.children[0].path == "src/utils/helpers.py"


@pytest.mark.asyncio
async def test_fetch_file_tree_empty():
    mock_response = MagicMock()
    mock_response.json.return_value = {"tree": []}
    mock_response.raise_for_status = MagicMock()

    fetcher = GitHubFetcher()

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value = (
            mock_response
        )
        result = await fetcher.fetch_file_tree("o", "r")

    assert isinstance(result, FileTree)
    assert len(result.root.children) == 0
