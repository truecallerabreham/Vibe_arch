import os
from pathlib import Path
from typing import Any

from backend.app.models.ast import ImportEdge, SymbolGraph, SymbolNode, SymbolType


class ASTExtractionError(Exception):
    pass


class ASTExtractor:
    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "tsx",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "c_sharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
    }

    TSX_LANGUAGE_NAME = "tsx"
    TYPESCRIPT_LANGUAGE_NAME = "typescript"

    def __init__(self) -> None:
        self.parsers: dict[str, Any] = {}
        self._tree_sitter_available = False
        self._init_tree_sitter()

    def _init_tree_sitter(self) -> None:
        try:
            from tree_sitter import Language, Parser

            self._Language = Language
            self._Parser = Parser
            self._tree_sitter_available = True
        except ImportError:
            self._tree_sitter_available = False

    @property
    def available(self) -> bool:
        return self._tree_sitter_available

    def _get_parser(self, language_name: str) -> Any:
        if not self._tree_sitter_available:
            return None

        if language_name in self.parsers:
            return self.parsers[language_name]

        lang = self._load_language(language_name)
        if lang is None:
            return None

        parser = self._Parser(lang)
        self.parsers[language_name] = parser
        return parser

    def _load_language(self, language_name: str) -> Any:
        module_name = f"tree_sitter_{language_name}"

        if language_name == self.TSX_LANGUAGE_NAME:
            module_name = "tree_sitter_typescript"

        try:
            import importlib

            lang_module = importlib.import_module(module_name)
        except ImportError:
            return None

        try:
            if language_name == self.TSX_LANGUAGE_NAME:
                capsule = lang_module.language_tsx()
            elif language_name == self.TYPESCRIPT_LANGUAGE_NAME:
                capsule = lang_module.language_typescript()
            else:
                capsule = lang_module.language()
        except AttributeError:
            return None

        try:
            return self._Language(capsule)
        except TypeError:
            return capsule

    def extract(self, file_path: str, content: str) -> SymbolGraph | None:
        ext = Path(file_path).suffix
        language_name = self.LANGUAGE_MAP.get(ext)
        if not language_name:
            return None

        if not self._tree_sitter_available:
            return None

        parser = self._get_parser(language_name)
        if not parser:
            return None

        try:
            tree = parser.parse(bytes(content, "utf-8"))
        except Exception:
            return None

        if not tree or not tree.root_node:
            return None

        graph = SymbolGraph()
        self._extract_symbols(tree.root_node, content, file_path, graph)
        self._extract_imports(tree.root_node, content, file_path, graph)
        return graph

    def _node_text(self, node: Any, source: str) -> str:
        return source[node.start_byte : node.end_byte]

    def _query_node(self, node: Any, type_name: str) -> list[Any]:
        results: list[Any] = []
        if node.type == type_name:
            results.append(node)
        for child in node.children:
            results.extend(self._query_node(child, type_name))
        return results

    def _extract_symbols(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        stack = [node]
        while stack:
            current = stack.pop()
            children = list(current.children)

            if current.type == "function_definition":
                self._handle_py_function(current, source, file_path, graph)
            elif current.type == "class_definition":
                self._handle_py_class(current, source, file_path, graph)
            elif current.type == "function_declaration":
                self._handle_js_function(current, source, file_path, graph)
            elif current.type == "class_declaration":
                self._handle_js_class(current, source, file_path, graph)
            elif current.type == "method_definition":
                self._handle_js_method(current, source, file_path, graph)
            elif current.type == "interface_declaration":
                self._handle_ts_interface(current, source, file_path, graph)
            elif current.type == "lexical_declaration":
                self._handle_js_lexical(current, source, file_path, graph)
            elif current.type == "type_declaration":
                self._handle_go_type(current, source, file_path, graph)

            for child in children:
                stack.append(child)

    def _handle_py_function(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        for child in node.children:
            if child.type == "identifier":
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=SymbolType.FUNCTION,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_py_class(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        for child in node.children:
            if child.type == "identifier":
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=SymbolType.CLASS,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_js_function(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        for child in node.children:
            if child.type in ("identifier", "property_identifier"):
                sym_type = SymbolType.FUNCTION
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=sym_type,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_js_class(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        for child in node.children:
            if child.type in ("identifier", "type_identifier"):
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=SymbolType.CLASS,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_js_method(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        for child in node.children:
            if child.type == "property_identifier":
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=SymbolType.FUNCTION,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_ts_interface(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                graph.symbols.append(
                    SymbolNode(
                        name=self._node_text(child, source),
                        type=SymbolType.INTERFACE,
                        file_path=file_path,
                        line_number=child.start_point[0] + 1,
                    )
                )
                break

    def _handle_js_lexical(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        for child in node.children:
            if child.type == "variable_declarator":
                for sub in child.children:
                    if sub.type == "identifier":
                        arrow_found = any(gc.type == "arrow_function" for gc in child.children)
                        if arrow_found:
                            graph.symbols.append(
                                SymbolNode(
                                    name=self._node_text(sub, source),
                                    type=SymbolType.FUNCTION,
                                    file_path=file_path,
                                    line_number=sub.start_point[0] + 1,
                                )
                            )
                        return

    def _handle_go_type(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        for child in node.children:
            if child.type == "type_spec":
                for sub in child.children:
                    if sub.type == "type_identifier":
                        has_struct = any(gc.type == "struct_type" for gc in child.children)
                        graph.symbols.append(
                            SymbolNode(
                                name=self._node_text(sub, source),
                                type=SymbolType.CLASS if has_struct else SymbolType.INTERFACE,
                                file_path=file_path,
                                line_number=sub.start_point[0] + 1,
                            )
                        )
                        return

    def _extract_imports(self, node: Any, source: str, file_path: str, graph: SymbolGraph) -> None:
        ext = Path(file_path).suffix

        if ext == ".py":
            self._extract_py_imports(node, source, file_path, graph)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            self._extract_js_imports(node, source, file_path, graph)
        elif ext == ".go":
            self._extract_go_imports(node, source, file_path, graph)

    def _extract_py_imports(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == "import_statement":
                for child in current.children:
                    if child.type == "dotted_name":
                        graph.imports.append(
                            ImportEdge(
                                from_path=file_path,
                                to_path=self._node_text(child, source),
                            )
                        )
                    elif child.type == "aliased_import":
                        for sub in child.children:
                            if sub.type == "dotted_name":
                                graph.imports.append(
                                    ImportEdge(
                                        from_path=file_path,
                                        to_path=self._node_text(sub, source),
                                    )
                                )
                                break
            elif current.type == "import_from_statement":
                module_name = ""
                for child in current.children:
                    if child.type == "dotted_name":
                        module_name = self._node_text(child, source)
                        break
                for child in current.children:
                    if (
                        child.type == "dotted_name"
                        and self._node_text(child, source) != module_name
                    ):
                        graph.imports.append(
                            ImportEdge(
                                from_path=file_path,
                                to_path=f"{module_name}.{self._node_text(child, source)}",
                            )
                        )
                for child in current.children:
                    if child.type == "aliased_import":
                        for sub in child.children:
                            if sub.type == "dotted_name":
                                graph.imports.append(
                                    ImportEdge(
                                        from_path=file_path,
                                        to_path=f"{module_name}.{self._node_text(sub, source)}",
                                    )
                                )
                                break
            for child in current.children:
                stack.append(child)

    def _extract_js_imports(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        stack = [node]
        while stack:
            current = stack.pop()

            if current.type == "import_statement":
                for child in current.children:
                    if child.type == "string":
                        import_path = self._node_text(child, source).strip("'\"")
                        graph.imports.append(ImportEdge(from_path=file_path, to_path=import_path))
                        break

            if current.type == "call_expression":
                for child in current.children:
                    if child.type == "identifier" and self._node_text(child, source) == "require":
                        for arg in current.children:
                            if arg.type == "arguments":
                                for s in arg.children:
                                    if s.type == "string":
                                        import_path = self._node_text(s, source).strip("'\"")
                                        graph.imports.append(
                                            ImportEdge(
                                                from_path=file_path,
                                                to_path=import_path,
                                            )
                                        )
                        break

            for child in current.children:
                stack.append(child)

    def _extract_go_imports(
        self, node: Any, source: str, file_path: str, graph: SymbolGraph
    ) -> None:
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == "import_declaration":
                for child in current.children:
                    if child.type == "import_spec_list":
                        for spec in child.children:
                            if spec.type == "import_spec":
                                for lit in spec.children:
                                    if lit.type == "interpreted_string_literal":
                                        import_path = self._node_text(lit, source).strip('"')
                                        graph.imports.append(
                                            ImportEdge(
                                                from_path=file_path,
                                                to_path=import_path,
                                            )
                                        )
                    elif child.type == "import_spec":
                        for lit in child.children:
                            if lit.type == "interpreted_string_literal":
                                import_path = self._node_text(lit, source).strip('"')
                                graph.imports.append(
                                    ImportEdge(from_path=file_path, to_path=import_path)
                                )
            for child in current.children:
                stack.append(child)

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
                if ext in self.LANGUAGE_MAP:
                    try:
                        with open(file_path, encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        graph = self.extract(file_path, content)
                        if graph and (graph.symbols or graph.imports):
                            results[file_path] = graph
                    except Exception:
                        pass
        return results
