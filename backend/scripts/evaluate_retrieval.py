from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)
from app.rag_ingestion.retrieval import (
    RetrievalService,
)
from app.rag_ingestion.retrieval.evaluation import (
    EvaluationOutcome,
    evaluate_results,
    load_evaluation_cases,
    make_text_preview,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)


BACKEND_DIR = Path(__file__).resolve().parents[1]

DEFAULT_DATASET = (
    BACKEND_DIR
    / "evaluation"
    / "inventory_retrieval_cases.json"
)

DEFAULT_TOP_K = 3


def build_retrieval_service() -> RetrievalService:
    embedding_service = (
        BGEM3EmbeddingService()
    )

    vector_store = QdrantService(
        vector_dimension=(
            embedding_service.dimension
        )
    )

    return RetrievalService(
        embedding_service=embedding_service,
        vector_store=vector_store,
    )


def print_case(
    outcome: EvaluationOutcome,
) -> None:
    case = outcome.case

    print()
    print("=" * 78)
    print(f"{case.id.upper()} — {case.question}")
    print("=" * 78)

    if case.is_insufficient_evidence:
        print(
            "Expected: INSUFFICIENT_EVIDENCE"
        )
        print(
            "Note: Qdrant may still return "
            "semantically related chunks."
        )
    else:
        print(
            "Expected transactions: "
            + ", ".join(
                case.expected_transaction_numbers
            )
        )

    print()
    print("Retrieved:")

    if not outcome.results:
        print("No chunks returned.")
        return

    for result in outcome.results:
        if case.is_insufficient_evidence:
            relevance_label = (
                "OBSERVATION ONLY"
            )
        elif result.relevant:
            relevance_label = "RELEVANT"
        else:
            relevance_label = "NOT EXPECTED"

        print()
        print(f"Rank {result.rank}")
        print(
            "Transaction: "
            f"{result.transaction_number or 'N/A'}"
        )
        print(
            f"Chunk ID: {result.chunk_id}"
        )
        print(
            f"Score: {result.score:.6f}"
        )
        print(
            "Source file: "
            f"{result.source_file or 'N/A'}"
        )
        print(
            "Source rows: "
            f"{result.source_rows or 'N/A'}"
        )
        print(
            f"Evaluation: {relevance_label}"
        )
        print(
            "Preview: "
            f"{make_text_preview(result.text)}"
        )


def print_summary(
    outcomes: list[EvaluationOutcome],
    *,
    top_k: int,
) -> None:
    answerable = [
        outcome
        for outcome in outcomes
        if not outcome.case.is_insufficient_evidence
    ]

    insufficient = [
        outcome
        for outcome in outcomes
        if outcome.case.is_insufficient_evidence
    ]

    top1_hits = sum(
        outcome.top1_hit
        for outcome in answerable
    )

    topk_hits = sum(
        outcome.top_k_hit(top_k)
        for outcome in answerable
    )

    answerable_count = len(answerable)

    top1_accuracy = (
        100.0
        * top1_hits
        / answerable_count
        if answerable_count
        else 0.0
    )

    topk_success = (
        100.0
        * topk_hits
        / answerable_count
        if answerable_count
        else 0.0
    )

    print()
    print()
    print("=" * 78)
    print("RETRIEVAL EVALUATION SUMMARY")
    print("=" * 78)

    print(
        f"Total questions: {len(outcomes)}"
    )

    print(
        "Questions with expected retrievable "
        f"evidence: {answerable_count}"
    )

    print(
        "Insufficient-evidence questions: "
        f"{len(insufficient)}"
    )

    print()
    print(
        "Questions with at least one expected "
        "result in Top-1: "
        f"{top1_hits}/{answerable_count}"
    )

    print(
        "Questions with at least one expected "
        f"result in Top-{top_k}: "
        f"{topk_hits}/{answerable_count}"
    )

    print()
    print(
        "Top-1 retrieval accuracy: "
        f"{top1_accuracy:.2f}%"
    )

    print(
        f"Top-{top_k} retrieval success: "
        f"{topk_success:.2f}%"
    )

    print()
    print(
        "Important: insufficient-evidence "
        "questions are observations, not retrieval "
        "misses, because semantic search may "
        "legitimately return related chunks even "
        "when the answer is absent."
    )

    print()
    print(
        "This is a small project-specific "
        "evaluation dataset, not an industry "
        "benchmark."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the existing Business AI "
            "semantic retrieval pipeline."
        )
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help="Number of chunks to retrieve.",
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET,
        help=(
            "Path to the retrieval "
            "evaluation dataset."
        ),
    )

    args = parser.parse_args()

    if args.top_k <= 0:
        raise ValueError(
            "--top-k must be greater than zero."
        )

    load_dotenv(
        BACKEND_DIR / ".env"
    )

    cases = load_evaluation_cases(
        args.dataset
    )

    retrieval_service = (
        build_retrieval_service()
    )

    outcomes: list[
        EvaluationOutcome
    ] = []

    print()
    print("# Retrieval Evaluation")
    print(
        f"Dataset: {args.dataset.name}"
    )
    print(f"Top-K: {args.top_k}")
    print(
        "Retriever: existing "
        "BGE-M3 + Qdrant RetrievalService"
    )
    print(
        "LLM: NOT USED"
    )

    for case in cases:
        retrieved = (
            retrieval_service.retrieve(
                case.question,
                top_k=args.top_k,
            )
        )

        outcome = evaluate_results(
            case=case,
            retrieved=retrieved,
        )

        outcomes.append(outcome)

        print_case(outcome)

    print_summary(
        outcomes,
        top_k=args.top_k,
    )


if __name__ == "__main__":
    main()