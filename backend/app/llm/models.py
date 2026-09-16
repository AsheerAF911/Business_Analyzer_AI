from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMEvidence:
    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class LLMRequest:
    question: str
    evidence: list[LLMEvidence]
    system_instructions: str | None = None


@dataclass(frozen=True)
class LLMResponse:
    text: str