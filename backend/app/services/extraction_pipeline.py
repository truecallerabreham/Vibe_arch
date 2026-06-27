from backend.app.models.architecture import Architecture
from backend.app.services.ast_extractor import ASTExtractor
from backend.app.services.fetcher import GitHubFetcher
from backend.app.services.llm_interpreter import LLMInterpreter
from backend.app.services.regex_extractor import RegexExtractor
from backend.app.services.validator import ArchitectureValidator


class ExtractionPipeline:
    """Orchestrates the full architecture extraction pipeline."""

    def __init__(self):
        self.fetcher = GitHubFetcher()
        self.regex_extractor = RegexExtractor()
        self.ast_extractor = ASTExtractor()
        self.interpreter = LLMInterpreter()
        self.validator = ArchitectureValidator()

    async def run(self, repo_url: str, progress_callback=None) -> Architecture:
        """Run the full extraction pipeline."""
        owner, repo = GitHubFetcher.parse_github_url(repo_url)
        if not owner or not repo:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")

        if progress_callback:
            await progress_callback("Fetching repository metadata...")
        await self.fetcher.fetch_metadata(owner, repo)

        if progress_callback:
            await progress_callback("Fetching file tree...")
        file_tree = await self.fetcher.fetch_file_tree(owner, repo)

        if progress_callback:
            await progress_callback("Fetching README...")
        readme = await self.fetcher.fetch_readme(owner, repo)

        if progress_callback:
            await progress_callback("Analyzing source code structure...")
        repo_name = f"{owner}/{repo}"

        ast_graphs = {}
        source_files = [c.path for c in self._collect_files(file_tree.root)]

        for file_path in source_files[:50]:
            try:
                content = await self.fetcher.fetch_file_content(owner, repo, file_path)
                graph = self.regex_extractor.extract(file_path, content)
                if graph and (graph.symbols or graph.imports):
                    ast_graphs[file_path] = graph
            except Exception:
                pass

        if progress_callback:
            await progress_callback("Interpreting architecture with AI...")

        architecture = await self.interpreter.interpret(
            repo_url=repo_url,
            repo_name=repo_name,
            readme=readme,
            file_tree=file_tree,
            ast_graphs=ast_graphs,
        )

        if progress_callback:
            await progress_callback("Validating architecture...")

        valid, errors = await self.validator.validate(architecture, file_tree)
        if not valid:
            if progress_callback:
                await progress_callback(f"Validation found {len(errors)} issues, retrying...")
            for _attempt in range(ArchitectureValidator.MAX_RETRIES):
                architecture = await self.interpreter.interpret(
                    repo_url=repo_url,
                    repo_name=repo_name,
                    readme=readme,
                    file_tree=file_tree,
                    ast_graphs=ast_graphs,
                )
                valid, errors = await self.validator.validate(architecture, file_tree)
                if valid:
                    break

        if progress_callback:
            await progress_callback("Extraction complete!")

        return architecture

    def _collect_files(self, node):
        """Recursively collect file nodes from tree."""
        files = []
        if node.type == "file":
            files.append(node)
        for child in node.children:
            files.extend(self._collect_files(child))
        return files
