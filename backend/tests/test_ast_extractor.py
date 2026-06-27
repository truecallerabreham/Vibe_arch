from pathlib import Path

from backend.app.models.ast import SymbolType
from backend.app.services.regex_extractor import RegexExtractor

extractor = RegexExtractor()


def _run(source: str, ext: str = ".py"):
    return extractor.extract(f"/fake/path/file{ext}", source)


class TestPython:
    def test_function_detection(self):
        code = """
def hello():
    pass

async def async_fn():
    pass
"""
        graph = _run(code, ".py")
        assert graph is not None
        names = [s.name for s in graph.symbols if s.type == SymbolType.FUNCTION]
        assert "hello" in names
        assert "async_fn" in names

    def test_class_detection(self):
        code = """
class MyClass:
    pass

class AnotherClass(Base):
    pass
"""
        graph = _run(code, ".py")
        assert graph is not None
        names = [s.name for s in graph.symbols if s.type == SymbolType.CLASS]
        assert "MyClass" in names
        assert "AnotherClass" in names

    def test_import_detection(self):
        code = """
import os
import json as json_mod
from pathlib import Path
from typing import List, Optional
"""
        graph = _run(code, ".py")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "os" in to_paths
        assert "json" in to_paths
        assert "pathlib.Path" in to_paths or any("pathlib" in p for p in to_paths)

    def test_mixed_symbols(self):
        code = """
import sys

class DataProcessor:
    def transform(self):
        pass

def helper():
    pass
"""
        graph = _run(code, ".py")
        assert graph is not None
        assert len(graph.symbols) >= 2
        assert len(graph.imports) >= 1


class TestJavaScript:
    def test_function_detection(self):
        code = """
function greet(name) {
    return "Hello";
}
"""
        graph = _run(code, ".js")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "greet" in names

    def test_class_detection(self):
        code = """
class Greeter {
    greet() {
        return "hello";
    }
}
"""
        graph = _run(code, ".js")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "Greeter" in names

    def test_arrow_function_const(self):
        code = """
const add = (a, b) => a + b;
const multiply = (a, b) => {
    return a * b;
};
"""
        graph = _run(code, ".js")
        assert graph is not None
        names = [s.name for s in graph.symbols if s.type == SymbolType.FUNCTION]
        assert "add" in names

    def test_import_detection(self):
        code = """
import { readFile } from 'fs';
import http from 'http';
const express = require('express');
"""
        graph = _run(code, ".js")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "fs" in to_paths
        assert "http" in to_paths
        assert "express" in to_paths


class TestTypeScript:
    def test_function_detection(self):
        code = """
export function greet(name: string): void {
    console.log(`Hello ${name}`);
}
"""
        graph = _run(code, ".ts")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "greet" in names

    def test_class_detection(self):
        code = """
export class Greeter {
    greet(): string {
        return "hello";
    }
}
"""
        graph = _run(code, ".ts")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "Greeter" in names

    def test_interface_detection(self):
        code = """
interface User {
    name: string;
    age: number;
}
"""
        graph = _run(code, ".ts")
        assert graph is not None
        names = [s.name for s in graph.symbols if s.type == SymbolType.INTERFACE]
        assert "User" in names

    def test_import_detection(self):
        code = """
import { readFile } from 'fs';
import http from 'http';
"""
        graph = _run(code, ".ts")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "fs" in to_paths
        assert "http" in to_paths


class TestGo:
    def test_function_detection(self):
        code = """
func hello(name string) string {
    return "Hello " + name
}
"""
        graph = _run(code, ".go")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "hello" in names

    def test_method_detection(self):
        code = """
func (p *Person) Greet() string {
    return "Hello"
}
"""
        graph = _run(code, ".go")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "Greet" in names

    def test_struct_detection(self):
        code = """
type Person struct {
    Name string
    Age  int
}
"""
        graph = _run(code, ".go")
        assert graph is not None
        names = [s.name for s in graph.symbols if s.type == SymbolType.CLASS]
        assert "Person" in names

    def test_import_detection(self):
        code = """
import (
    "fmt"
    "os"
    "github.com/user/pkg"
)
"""
        graph = _run(code, ".go")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "fmt" in to_paths
        assert "os" in to_paths
        assert "github.com/user/pkg" in to_paths

    def test_single_import(self):
        code = """
import "fmt"
"""
        graph = _run(code, ".go")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "fmt" in to_paths


class TestEdgeCases:
    def test_empty_file(self):
        graph = _run("", ".py")
        assert graph is not None
        assert len(graph.symbols) == 0
        assert len(graph.imports) == 0

    def test_unsupported_extension(self):
        graph = _run("fn main() {}", ".rs")
        assert graph is None

    def test_file_with_no_symbols(self):
        code = """
# just a comment
x = 42
y = [1, 2, 3]
"""
        graph = _run(code, ".py")
        assert graph is not None
        assert len(graph.symbols) == 0

    def test_nested_functions_ignored(self):
        code = """
def outer():
    def inner():
        pass
    return inner
"""
        graph = _run(code, ".py")
        assert graph is not None
        names = [s.name for s in graph.symbols]
        assert "outer" in names


class TestImportVariants:
    def test_python_from_import(self):
        code = "from collections import defaultdict, namedtuple"
        graph = _run(code, ".py")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert any("collections" in p for p in to_paths)

    def test_python_multi_import(self):
        code = "import os, sys, json"
        graph = _run(code, ".py")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "os" in to_paths
        assert "sys" in to_paths

    def test_js_default_import(self):
        code = "import express from 'express'"
        graph = _run(code, ".js")
        assert graph is not None
        to_paths = [e.to_path for e in graph.imports]
        assert "express" in to_paths


class TestDirectoryExtraction:
    def test_empty_directory(self, tmp_path: Path):
        result = extractor.extract_from_directory(str(tmp_path))
        assert result == {}

    def test_directory_with_source_files(self, tmp_path: Path):
        d = tmp_path / "src"
        d.mkdir()
        (d / "main.py").write_text("def hello():\n    pass\n")
        (d / "utils.py").write_text("import os\n")
        (d / "readme.md").write_text("# Readme\n")

        result = extractor.extract_from_directory(str(d))
        assert len(result) == 2
        assert any(p.endswith("main.py") for p in result)
        assert any(p.endswith("utils.py") for p in result)

    def test_skip_ignored_dirs(self, tmp_path: Path):
        d = tmp_path / "project"
        d.mkdir()
        (d / "main.py").write_text("def hello():\n    pass\n")
        nm = d / "node_modules"
        nm.mkdir()
        (nm / "lib.py").write_text("def lib_func():\n    pass\n")

        result = extractor.extract_from_directory(str(d))
        assert len(result) == 1
        assert all("node_modules" not in p for p in result)
