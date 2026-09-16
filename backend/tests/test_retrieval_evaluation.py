from pathlib import Path

import pytest

from app.rag_ingestion.retrieval import (
    RetrievalResult,
)
from app.rag_ingestion.retrieval.evaluation import (
    EXPECT_INSUFFICIENT_EVIDENCE,
    EvaluationCase,
    evaluate_results,
    load_evaluation_cases,
)


BACKEND_DIR = (
    Path(__file__).resolve().parents[1]
)

DATASET_PATH = (
    BACKEND_DIR
    / "evaluation"
    / "inventory_retrieval_cases.json"
)


def make_result(
    transaction_number: str,
    *,
    score: float,
) -> RetrievalResult:
    return RetrievalResult(
        chunk_id=(
            "Inventory_transactions-"
            "Sheet1-transaction-"
            f"{transaction_number}"
        ),
        score=score,
        text=(
            "Inventory transaction "
            f"{transaction_number}"
        ),
        metadata={
            "source_file":
                "Inventory_transactions.xlsx",
            "sheet": "Sheet1",
            "source_rows": [2, 3],
            "transaction_number":
                transaction_number,
        },
    )


def test_evaluation_dataset_loads():
    cases = load_evaluation_cases(
        DATASET_PATH
    )

    assert len(cases) == 10


def test_expected_identifiers_are_loaded():
    cases = load_evaluation_cases(
        DATASET_PATH
    )

    q1 = next(
        case
        for case in cases
        if case.id == "q1"
    )

    assert (
        q1.expected_transaction_numbers
        == ("D1IN0818",)
    )


def test_multiple_expected_identifiers_load():
    cases = load_evaluation_cases(
        DATASET_PATH
    )

    q5 = next(
        case
        for case in cases
        if case.id == "q5"
    )

    assert set(
        q5.expected_transaction_numbers
    ) == {
        "D1IN0818",
        "D1IN0820",
    }


def test_retrieved_chunk_matches_expected():
    case = EvaluationCase(
        id="test",
        question="test",
        expectation=(
            "relevant_transactions"
        ),
        expected_transaction_numbers=(
            "D1IN0818",
        ),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[
            make_result(
                "D1IN0818",
                score=0.8,
            )
        ],
    )

    assert outcome.results[0].relevant


def test_unexpected_chunk_is_not_relevant():
    case = EvaluationCase(
        id="test",
        question="test",
        expectation=(
            "relevant_transactions"
        ),
        expected_transaction_numbers=(
            "D1IN0818",
        ),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[
            make_result(
                "D1IN0820",
                score=0.8,
            )
        ],
    )

    assert not outcome.results[0].relevant


def test_top1_hit():
    case = EvaluationCase(
        id="test",
        question="test",
        expectation=(
            "relevant_transactions"
        ),
        expected_transaction_numbers=(
            "D1IN0818",
        ),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[
            make_result(
                "D1IN0818",
                score=0.8,
            ),
            make_result(
                "D1IN0820",
                score=0.7,
            ),
        ],
    )

    assert outcome.top1_hit is True


def test_top1_miss_but_top3_hit():
    case = EvaluationCase(
        id="test",
        question="test",
        expectation=(
            "relevant_transactions"
        ),
        expected_transaction_numbers=(
            "D1IN0818",
        ),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[
            make_result(
                "D1IN0820",
                score=0.8,
            ),
            make_result(
                "D1IN0819",
                score=0.7,
            ),
            make_result(
                "D1IN0818",
                score=0.6,
            ),
        ],
    )

    assert outcome.top1_hit is False
    assert outcome.top_k_hit(3) is True


def test_insufficient_evidence_cases_load():
    cases = load_evaluation_cases(
        DATASET_PATH
    )

    insufficient = [
        case
        for case in cases
        if case.is_insufficient_evidence
    ]

    assert len(insufficient) == 2

    assert all(
        case.expectation
        == EXPECT_INSUFFICIENT_EVIDENCE
        for case in insufficient
    )

    assert all(
        not case.expected_transaction_numbers
        for case in insufficient
    )


def test_insufficient_evidence_is_not_marked_relevant():
    case = EvaluationCase(
        id="test",
        question=(
            "Why did profit decline?"
        ),
        expectation=(
            EXPECT_INSUFFICIENT_EVIDENCE
        ),
        expected_transaction_numbers=(),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[
            make_result(
                "D1IN0818",
                score=0.5,
            )
        ],
    )

    assert (
        outcome.results[0].relevant
        is False
    )

    assert outcome.top1_hit is False
    assert outcome.top_k_hit(3) is False


def test_invalid_top_k_rejected():
    case = EvaluationCase(
        id="test",
        question="test",
        expectation=(
            "relevant_transactions"
        ),
        expected_transaction_numbers=(
            "D1IN0818",
        ),
    )

    outcome = evaluate_results(
        case=case,
        retrieved=[],
    )

    with pytest.raises(ValueError):
        outcome.top_k_hit(0)