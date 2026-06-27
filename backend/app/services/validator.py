from backend.app.models.architecture import Architecture
from backend.app.models.repo import FileTree


class ArchitectureValidator:
    """Validates architecture output against actual file tree."""

    MAX_RETRIES = 3

    async def validate(self, architecture: Architecture, file_tree: FileTree) -> tuple[bool, list[str]]:
        """Validate all component paths exist in the file tree. Returns (valid, errors)."""
        valid_paths = self._collect_paths(file_tree)
        errors = []

        for component in architecture.components:
            if component.path and component.path not in valid_paths:
                errors.append(f"Component '{component.name}' path '{component.path}' not found in file tree")

        return len(errors) == 0, errors

    def _collect_paths(self, file_tree: FileTree) -> set[str]:
        """Collect all file/directory paths from file tree."""
        paths = set()
        self._collect_recursive(file_tree.root, paths)
        return paths

    def _collect_recursive(self, node, paths: set[str]):
        if node.path:
            paths.add(node.path)
        for child in node.children:
            self._collect_recursive(child, paths)
