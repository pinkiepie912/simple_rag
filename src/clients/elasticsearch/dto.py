from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class DocumentDTO:
    doc_id: Optional[str] = None
    content: str = ""
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)


@dataclass
class QueryDTO:
    query_text: str
    top_n: int = 5
