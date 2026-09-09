from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)
from app.rag_ingestion.retrieval import (
    RetrievalService,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)


def print_results(
    service,
    query,
    *,
    top_k=3,
):
    print()
    print("=" * 80)
    print(f"Query: {query}")
    print()

    results = service.retrieve(
        query,
        top_k=top_k,
    )

    for rank, result in enumerate(
        results,
        start=1,
    ):
        metadata = result.metadata

        transaction = metadata.get(
            "transaction_number",
            "N/A",
        )

        print(
            f"{rank}. {transaction}"
        )

        print(
            f"   Chunk ID: "
            f"{result.chunk_id}"
        )

        print(
            f"   Score: "
            f"{result.score:.6f}"
        )

        print(
            f"   Source: "
            f"{metadata.get('source_file')}"
        )

        print(
            f"   Sheet: "
            f"{metadata.get('sheet')}"
        )

        print(
            f"   Rows: "
            f"{metadata.get('source_rows')}"
        )

        print(
            f"   Supplier: "
            f"{metadata.get('supplier')}"
        )

        print(
            "   Text preview: "
            f"{result.text[:300]}"
        )

        print()


def main():
    embedding_service = (
        BGEM3EmbeddingService()
    )

    qdrant = QdrantService(
        vector_dimension=(
            embedding_service.dimension
        )
    )

    retrieval_service = RetrievalService(
        embedding_service=embedding_service,
        vector_store=qdrant,
    )

    queries = [
        (
            "Which products were received "
            "under D1IN0818?"
        ),
        "Tell me about D1IN0820",
        (
            "Which transaction contains "
            "chilli powder?"
        ),
        (
            "What was received from "
            "TEAM 2?"
        ),
    ]

    for query in queries:
        print_results(
            retrieval_service,
            query,
            top_k=3,
        )


if __name__ == "__main__":
    main()