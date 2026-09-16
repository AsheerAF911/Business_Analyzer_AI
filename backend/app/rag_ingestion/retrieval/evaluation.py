from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from app.rag_ingestion.retrieval.models import (
    RetrievalResult,
)


EXPECT_RELEVANT_TRANSACTIONS = (
    "relevant_transactions"
)

EXPECT_INSUFFICIENT_EVIDENCE = (
    "insufficient_evidence"
)


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expectation: str
    expected_transaction_numbers: tuple[str, ...]

    @property
    def is_insufficient_evidence(self) -> bool:
        return (
            self.expectation
            == EXPECT_INSUFFICIENT_EVIDENCE
        )


@dataclass(frozen=True)
class EvaluatedResult:
    rank: int
    chunk_id: str
    score: float
    transaction_number: str | None
    source_file: str | None
    source_rows: list[int] | None
    text: str
    relevant: bool


@dataclass(frozen=True)
class EvaluationOutcome:
    case: EvaluationCase
    results: list[EvaluatedResult]

    @property
    def top1_hit(self) -> bool:
        if self.case.is_insufficient_evidence:
            return False

        return any(
            result.relevant
            for result in self.results[:1]
        )

    def top_k_hit(
        self,
        top_k: int,
    ) -> bool:
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        if self.case.is_insufficient_evidence:
            return False

        return any(
            result.relevant
            for result in self.results[:top_k]
        )


def load_evaluation_cases(
    dataset_path: Path,
) -> list[EvaluationCase]:
    with dataset_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    raw_cases = payload.get("cases")

    if not isinstance(raw_cases, list):
        raise ValueError(
            "Evaluation dataset must contain a cases list."
        )

    cases: list[EvaluationCase] = []

    for raw_case in raw_cases:
        case_id = raw_case.get("id")
        question = raw_case.get("question")
        expectation = raw_case.get("expectation")

        expected = raw_case.get(
            "expected_transaction_numbers",
            [],
        )

        if not isinstance(case_id, str) or not case_id:
            raise ValueError(
                "Every evaluation case requires an id."
            )

        if (
            not isinstance(question, str)
            or not question.strip()
        ):
            raise ValueError(
                f"{case_id} requires a question."
            )

        if expectation not in {
            EXPECT_RELEVANT_TRANSACTIONS,
            EXPECT_INSUFFICIENT_EVIDENCE,
        }:
            raise ValueError(
                f"{case_id} has an unsupported "
                f"expectation: {expectation}"
            )

        if not isinstance(expected, list):
            raise ValueError(
                f"{case_id} expected evidence "
                "must be a list."
            )

        if (
            expectation
            == EXPECT_INSUFFICIENT_EVIDENCE
            and expected
        ):
            raise ValueError(
                f"{case_id} is marked as insufficient "
                "evidence but has expected transactions."
            )

        cases.append(
            EvaluationCase(
                id=case_id,
                question=question.strip(),
                expectation=expectation,
                expected_transaction_numbers=tuple(
                    str(value)
                    for value in expected
                ),
            )
        )

    return cases


def evaluate_results(
    *,
    case: EvaluationCase,
    retrieved: Sequence[RetrievalResult],
) -> EvaluationOutcome:
    expected = set(
        case.expected_transaction_numbers
    )

    evaluated_results: list[
        EvaluatedResult
    ] = []

    for rank, result in enumerate(
        retrieved,
        start=1,
    ):
        metadata: dict[str, Any] = (
            result.metadata or {}
        )

        transaction_number = metadata.get(
            "transaction_number"
        )

        source_file = metadata.get(
            "source_file"
        )

        source_rows = metadata.get(
            "source_rows"
        )

        relevant = (
            not case.is_insufficient_evidence
            and transaction_number in expected
        )

        evaluated_results.append(
            EvaluatedResult(
                rank=rank,
                chunk_id=result.chunk_id,
                score=float(result.score),
                transaction_number=(
                    transaction_number
                    if isinstance(
                        transaction_number,
                        str,
                    )
                    else None
                ),
                source_file=(
                    source_file
                    if isinstance(source_file, str)
                    else None
                ),
                source_rows=(
                    source_rows
                    if isinstance(source_rows, list)
                    else None
                ),
                text=result.text,
                relevant=relevant,
            )
        )

    return EvaluationOutcome(
        case=case,
        results=evaluated_results,
    )


def make_text_preview(
    text: str,
    *,
    max_length: int = 180,
) -> str:
    cleaned = " ".join(
        text.split()
    )

    if len(cleaned) <= max_length:
        return cleaned

    return (
        cleaned[: max_length - 3].rstrip()
        + "..."
    )