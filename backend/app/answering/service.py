from __future__ import annotations

from app.llm import (
    LLMEvidence,
    LLMService,
)
from app.rag_ingestion.retrieval import (
    RetrievalService,
)

from .models import (
    AnswerResult,
    AnswerSource,
)


class AnswerService:
    DEFAULT_TOP_K = 30

    SYSTEM_INSTRUCTIONS = """You are answering questions about business reports.

Rules:
- Answer only from the supplied evidence.
- Do not invent facts.
- Do not assume missing values.
- If the evidence is insufficient, explicitly say:
  "There is insufficient evidence to answer this question."
- Preserve important identifiers exactly, including transaction numbers,
  product names, invoice numbers and barcodes.
- Do not treat similarity scores as factual evidence.
- When useful, mention the relevant transaction or source information.
- Do not claim that a calculation is reliable unless the supplied evidence
  contains all values required for that calculation."""

    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        llm_service: LLMService,
    ):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service

    def answer(
        self,
        question: str,
        *,
        top_k: int = DEFAULT_TOP_K,
    ) -> AnswerResult:
        question = self._validate_question(
            question
        )

        evidence = self.retrieval_service.retrieve(
            question,
            top_k=top_k,
        )

        if not evidence:
            return AnswerResult(
                answer=(
                    "There is insufficient evidence "
                    "in the indexed reports to answer "
                    "this question."
                ),
                sources=[],
            )

        llm_evidence = [
            LLMEvidence(
                chunk_id=item.chunk_id,
                text=item.text,
                score=item.score,
                metadata=item.metadata,
            )
            for item in evidence
        ]

        llm_response = (
            self.llm_service.generate_answer(
                question=question,
                evidence=llm_evidence,
                system_instructions=(
                    self.SYSTEM_INSTRUCTIONS
                ),
            )
        )

        sources = [
            AnswerSource(
                chunk_id=item.chunk_id,
                score=item.score,
                metadata=item.metadata,
            )
            for item in evidence
        ]

        return AnswerResult(
            answer=llm_response.text,
            sources=sources,
        )

    @staticmethod
    def _validate_question(
        question: str,
    ) -> str:
        if not isinstance(question, str):
            raise TypeError(
                "Question must be a string."
            )

        question = question.strip()

        if not question:
            raise ValueError(
                "Question cannot be empty."
            )

        return question