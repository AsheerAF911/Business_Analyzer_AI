from __future__ import annotations

import json

from app.llm import LLMService
from app.rag_ingestion.retrieval import (
    RetrievalResult,
    RetrievalService,
)

from .models import (
    AnswerResult,
    AnswerSource,
)


class AnswerService:
    DEFAULT_TOP_K = 30

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

        prompt = self._build_prompt(
            question=question,
            evidence=evidence,
        )

        answer = self.llm_service.generate(
            prompt
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
            answer=answer,
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

    @staticmethod
    def _build_prompt(
        *,
        question: str,
        evidence: list[RetrievalResult],
    ) -> str:
        evidence_sections = []

        for index, item in enumerate(
            evidence,
            start=1,
        ):
            metadata_json = json.dumps(
                item.metadata,
                ensure_ascii=False,
                default=str,
            )

            evidence_sections.append(
                f"""Evidence {index}
Chunk ID: {item.chunk_id}
Similarity score: {item.score}
Metadata: {metadata_json}
Content:
{item.text}"""
            )

        evidence_text = "\n\n".join(
            evidence_sections
        )

        return f"""You are answering questions about business reports.

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
  contains all values required for that calculation.

User question:
{question}

Retrieved evidence:
{evidence_text}

Answer:"""