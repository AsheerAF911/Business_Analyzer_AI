from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievalResult:
    chunk_id: str
    score: float
    text: str
    metadata: dict[str, Any]