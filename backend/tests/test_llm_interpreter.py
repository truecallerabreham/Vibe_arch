import json

import pytest

from backend.app.models.architecture import Architecture, Component, Confidence
from backend.app.models.repo import FileNode, FileTree
from backend.app.services.llm_interpreter import LLMInterpreter
from backend.app.services.validator import ArchitectureValidator


@pytest.mark.asyncio
async def test_build_prompt():
    interpreter = LLMInterpreter()
    file_tree = FileTree(root=FileNode(path="", type="directory", children=[
        FileNode(path="src/main.py", type="file"),
        FileNode(path="src/utils/helpers.py", type="file"),
    ]))
    prompt = interpreter._build_prompt("test-repo", "A test repo", file_tree, {})
    assert "test-repo" in prompt
    assert "A test repo" in prompt
    assert "main.py" in prompt
    assert "helpers.py" in prompt


@pytest.mark.asyncio
async def test_parse_response_json():
    interpreter = LLMInterpreter()
    response = json.dumps({
        "components": [
            {"id": "api", "name": "API Layer", "role": "Handles HTTP requests",
             "path": "src/api", "confidence": "verified", "children": []}
        ],
        "relationships": [
            {"source_id": "api", "target_id": "db", "type": "depends_on", "confidence": "inferred"}
        ]
    })
    arch = interpreter._parse_response("https://github.com/test/repo", response)
    assert len(arch.components) == 1
    assert arch.components[0].name == "API Layer"
    assert arch.components[0].confidence == Confidence.VERIFIED
    assert arch.repo_url == "https://github.com/test/repo"


@pytest.mark.asyncio
async def test_parse_response_with_code_block():
    interpreter = LLMInterpreter()
    response = f"Here's the architecture:\n```json\n{json.dumps({'components': [], 'relationships': []})}\n```"
    arch = interpreter._parse_response("url", response)
    assert len(arch.components) == 0


@pytest.mark.asyncio
async def test_validator_passes_valid_architecture():
    file_tree = FileTree(root=FileNode(path="", type="directory", children=[
        FileNode(path="src/api", type="directory"),
        FileNode(path="src/api/main.py", type="file"),
    ]))
    arch = Architecture(
        repo_url="url",
        components=[Component(id="api", name="API", role="API handler", path="src/api", confidence=Confidence.VERIFIED)]
    )
    validator = ArchitectureValidator()
    valid, errors = await validator.validate(arch, file_tree)
    assert valid
    assert len(errors) == 0


@pytest.mark.asyncio
async def test_validator_rejects_hallucinated_path():
    file_tree = FileTree(root=FileNode(path="", type="directory", children=[
        FileNode(path="src/main.py", type="file"),
    ]))
    arch = Architecture(
        repo_url="url",
        components=[Component(id="fake", name="Fake Module", role="Doesn't exist",
                              path="src/fake_module", confidence=Confidence.INFERRED)]
    )
    validator = ArchitectureValidator()
    valid, errors = await validator.validate(arch, file_tree)
    assert not valid
    assert len(errors) == 1
    assert "fake_module" in errors[0]


@pytest.mark.asyncio
async def test_flatten_tree():
    interpreter = LLMInterpreter()
    tree = FileTree(root=FileNode(path="", type="directory", children=[
        FileNode(path="src", type="directory", children=[
            FileNode(path="src/main.py", type="file"),
        ]),
        FileNode(path="README.md", type="file"),
    ]))
    lines = []
    interpreter._flatten_tree(tree.root, lines, 0)
    output = "\n".join(lines)
    assert "main.py" in output
    assert "README.md" in output
