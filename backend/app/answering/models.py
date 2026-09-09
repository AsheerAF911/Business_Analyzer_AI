from dataclasses import dataclass
from typing import Any


@dataclass
class AnswerSource:
    chunk_id: str
    score: float
    metadata: dict[str, Any]


@dataclass
class AnswerResult:
    answer: str
    sources: list[AnswerSource]