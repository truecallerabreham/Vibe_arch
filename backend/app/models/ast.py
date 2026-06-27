from enum import Enum
from pydantic import BaseModel


class SymbolType(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"
    VARIABLE = "variable"


class SymbolNode(BaseModel):
    name: str
    type: SymbolType
    file_path: str
    line_number: int


class ImportEdge(BaseModel):
    from_path: str
    to_path: str
    import_type: str = "explicit"


class SymbolGraph(BaseModel):
    symbols: list[SymbolNode] = []
    imports: list[ImportEdge] = []
