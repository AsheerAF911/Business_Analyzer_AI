from __future__ import annotations

from .models import (
    LLMEvidence,
    LLMRequest,
    LLMResponse,
)
from .provider import LLMProvider


class LLMService:

    def __init__(
        self,
        *,
        provider: LLMProvider,
    ):
        self.provider = provider

    def generate_answer(
        self,
        *,
        question: str,
        evidence: list[LLMEvidence],
        system_instructions: str | None = None,
    ) -> LLMResponse:

        if not question.strip():
            raise ValueError(
                "Question cannot be empty."
            )

        request = LLMRequest(
            question=question.strip(),
            evidence=evidence,
            system_instructions=system_instructions,
        )

        return self.provider.generate(
            request
        )