import os
import re
from pathlib import Path

from backend.app.models.ast import ImportEdge, SymbolGraph, SymbolNode, SymbolType


class RegexExtractor:
    LANGUAGE_PATTERNS: dict[str, dict] = {
        ".py": {
            "symbols": [
                (
                    re.compile(r"^class\s+(\w+)\s*[:\(]"),
                    SymbolType.CLASS,
                ),
                (
                    re.compile(r"^async\s+def\s+(\w+)\s*\("),
                    SymbolType.FUNCTION,
                ),
                (
                    re.compile(r"^def\s+(\w+)\s*\("),
                    SymbolType.FUNCTION,
                ),
            ],
            "imports": [
                re.compile(
                    r"^\s*import\s+([\w.]+(?:\s+as\s+\w+)?(?:\s*,\s*[\w.]+(?:\s+as\s+\w+)?)*)"
                ),
                re.compile(r"^\s*from\s+([\w.]+)\s+import\s+(.+)"),
            ],
        },
        ".js": {
            "symbols": [
                (re.compile(r"^function\s+(\w+)\s*\("), SymbolType.FUNCTION),
                (re.compile(r"^class\s+(\w+)"), SymbolType.CLASS),
                (
                    re.compile(r"^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
                    SymbolType.FUNCTION,
                ),
                (
                    re.compile(r"^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\w+\s*=>"),
                    SymbolType.FUNCTION,
                ),
                (
                    re.compile(r"^(?:export\s+)?(?:default\s+)?function\s+(\w+)"),
                    SymbolType.FUNCTION,
                ),
            ],
            "imports": [
                re.compile(r"""import\s+(?:\{[^}]*\}\s*from\s+)?['"]([^'"]+)['"]"""),
                re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
                re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]"""),
            ],
        },
        ".jsx": {
            "symbols": [
                (re.compile(r"^function\s+(\w+)\s*\("), SymbolType.FUNCTION),
                (re.compile(r"^class\s+(\w+)"), SymbolType.CLASS),
                (
                    re.compile(r"^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
                    SymbolType.FUNCTION,
                ),
                (
                    re.compile(r"^(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\w+\s*=>"),
                    SymbolType.FUNCTION,
                ),
                (
                    re.compile(r"^(?:export\s+)?(?:default\s+)?function\s+(\w+)"),
                    SymbolType.FUNCTION,
                ),
            ],
            "imports": [
                re.compile(r"""import\s+(?:\{[^}]*\}\s*from\s+)?['"]([^'"]+)['"]"""),
                re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
                re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]"""),
            ],
        },
        ".ts": {
            "symbols": [
                (
                    re.compile(r"^(?:export\s+)?function\s+(\w+)\s*\("),
                    SymbolType.FUNCTION,
                ),
                (re.compile(r"^(?:export\s+)?class\s+(\w+)"), SymbolType.CLASS),
                (re.compile(r"^(?:export\s+)?interface\s+(\w+)"), SymbolType.INTERFACE),
                (
                    re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*:\s*(?:\w+)\s*="),
                    SymbolType.VARIABLE,
                ),
                (
                    re.compile(
                        r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(?[^)]*\)?\s*=>"
                    ),
                    SymbolType.FUNCTION,
                ),
            ],
            "imports": [
                re.compile(r"""import\s+(?:\{[^}]*\}\s*from\s+)?['"]([^'"]+)['"]"""),
                re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]"""),
                re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
            ],
        },
        ".tsx": {
            "symbols": [
                (
                    re.compile(r"^(?:export\s+)?function\s+(\w+)\s*\("),
                    SymbolType.FUNCTION,
                ),
                (re.compile(r"^(?:export\s+)?class\s+(\w+)"), SymbolType.CLASS),
                (re.compile(r"^(?:export\s+)?interface\s+(\w+)"), SymbolType.INTERFACE),
                (
                    re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*:\s*(?:\w+)\s*="),
                    SymbolType.VARIABLE,
                ),
                (
                    re.compile(
                        r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(?[^)]*\)?\s*=>"
                    ),
                    SymbolType.FUNCTION,
                ),
            ],
            "imports": [
                re.compile(r"""import\s+(?:\{[^}]*\}\s*from\s+)?['"]([^'"]+)['"]"""),
                re.compile(r"""import\s+(\w+)\s+from\s+['"]([^'"]+)['"]"""),
                re.compile(r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""),
            ],
        },
        ".go": {
            "symbols": [
                (re.compile(r"^func\s+(\w+)\s*\("), SymbolType.FUNCTION),
                (re.compile(r"^type\s+(\w+)\s+struct"), SymbolType.CLASS),
                (re.compile(r"^func\s+\([^)]+\)\s+(\w+)\s*\("), SymbolType.FUNCTION),
            ],
            "imports": [
                re.compile(r'^\s*import\s+"([^"]+)"'),
                re.compile(r"^\s*import\s+\(([^)]*(?:\([^)]*\)[^)]*)*)"),
                re.compile(r'^\s+"([^"]+)"'),
            ],
        },
    }

    def extract(self, file_path: str, content: str) -> SymbolGraph | None:
        ext = Path(file_path).suffix
        patterns = self.LANGUAGE_PATTERNS.get(ext)
        if not patterns:
            return None

        graph = SymbolGraph()
        lines = content.split("\n")

        self._extract_symbols(lines, patterns["symbols"], file_path, graph)
        self._extract_imports(lines, patterns["imports"], file_path, graph)

        return graph

    def _extract_symbols(
        self,
        lines: list[str],
        patterns: list[tuple[re.Pattern, SymbolType]],
        file_path: str,
        graph: SymbolGraph,
    ):
        for i, line in enumerate(lines):
            for pattern, sym_type in patterns:
                m = pattern.match(line.strip())
                if m:
                    graph.symbols.append(
                        SymbolNode(
                            name=m.group(1),
                            type=sym_type,
                            file_path=file_path,
                            line_number=i + 1,
                        )
                    )
                    break

    def _extract_imports(
        self,
        lines: list[str],
        patterns: list[re.Pattern],
        file_path: str,
        graph: SymbolGraph,
    ):
        go_multiline = False
        go_imports: list[str] = []

        for _, line in enumerate(lines):
            stripped = line.strip()

            if file_path.endswith(".go"):
                if stripped.startswith("import ("):
                    go_multiline = True
                    continue
                if go_multiline:
                    if stripped == ")":
                        go_multiline = False
                        for imp in go_imports:
                            graph.imports.append(ImportEdge(from_path=file_path, to_path=imp))
                        go_imports = []
                        continue
                    if stripped.startswith('"') and stripped.endswith('"'):
                        go_imports.append(stripped.strip('"'))
                        continue
                    continue

                if stripped.startswith('import "'):
                    pkg = stripped[len('import "') :].rstrip('"')
                    graph.imports.append(ImportEdge(from_path=file_path, to_path=pkg))
                    continue

            if file_path.endswith(".py"):
                from_match = re.match(r"^from\s+([\w.]+)\s+import\s+(.+)", stripped)
                if from_match:
                    module = from_match.group(1)
                    names_part = from_match.group(2)
                    for name in re.split(r"\s*,\s*", names_part):
                        clean_name = name.strip().split(" as ")[0].strip()
                        if clean_name:
                            graph.imports.append(
                                ImportEdge(
                                    from_path=file_path,
                                    to_path=f"{module}.{clean_name}",
                                )
                            )
                    continue

            for pattern in patterns:
                m = pattern.search(stripped)
                if m:
                    if file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                        if pattern == patterns[-1]:
                            to_path = m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(1)
                        else:
                            to_path = m.group(1)
                    else:
                        to_path = m.group(1)

                    parts = [p.strip() for p in to_path.split(",")]
                    for part in parts:
                        if part:
                            clean = part.split(" as ")[0].strip() if " as " in part else part
                            if clean:
                                graph.imports.append(ImportEdge(from_path=file_path, to_path=clean))
                    break

    def extract_from_directory(self, directory: str) -> dict[str, SymbolGraph]:
        results: dict[str, SymbolGraph] = {}
        for root, dirs, files in os.walk(directory):
            dirs[:] = [
                d
                for d in dirs
                if d
                not in {
                    "node_modules",
                    ".git",
                    "__pycache__",
                    "venv",
                    ".venv",
                    "dist",
                    "build",
                    ".next",
                    "target",
                    "vendor",
                }
            ]
            for file in files:
                file_path = os.path.join(root, file)
                ext = Path(file_path).suffix
                if ext in self.LANGUAGE_PATTERNS:
                    try:
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        graph = self.extract(file_path, content)
                        if graph and (graph.symbols or graph.imports):
                            results[file_path] = graph
                    except Exception:
                        pass
        return results
