from pydantic import BaseModel
from typing import Optional


class RepoMetadata(BaseModel):
    owner: str
    name: str
    description: Optional[str] = None
    stars: int = 0
    topics: list[str] = []
    language: Optional[str] = None
    last_commit_date: Optional[str] = None
    contributors_count: int = 0


class FileNode(BaseModel):
    path: str
    type: str
    children: list["FileNode"] = []


class FileTree(BaseModel):
    root: FileNode
