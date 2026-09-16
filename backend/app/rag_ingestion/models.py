from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.ingestion.parsers.base import ParsedRecord



@dataclass
class Document:
    document_id: str
    source_file: str
    report_type: str | None
    records: list[ParsedRecord]

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any]