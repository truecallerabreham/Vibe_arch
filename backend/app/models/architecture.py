from enum import Enum
from pydantic import BaseModel


class Confidence(str, Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    UNVERIFIABLE = "unverifiable"


class Component(BaseModel):
    id: str
    name: str
    role: str
    path: str
    confidence: Confidence
    children: list[str] = []


class Relationship(BaseModel):
    source_id: str
    target_id: str
    type: str
    confidence: Confidence


class Architecture(BaseModel):
    repo_url: str
    components: list[Component] = []
    relationships: list[Relationship] = []
