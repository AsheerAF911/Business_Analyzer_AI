from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)
from app.rag_ingestion.retrieval import (
    RetrievalService,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)


def create_retrieval_service():
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


def test_d1in0818_query_retrieves_transaction():
    service = create_retrieval_service()

    results = service.retrieve(
        "Which products were received "
        "under D1IN0818?",
        top_k=3,
    )

    assert results

    assert any(
        result.metadata.get(
            "transaction_number"
        )
        == "D1IN0818"
        for result in results
    )


def test_d1in0820_query_retrieves_transaction():
    service = create_retrieval_service()

    results = service.retrieve(
        "Tell me about D1IN0820",
        top_k=3,
    )

    assert any(
        result.metadata.get(
            "transaction_number"
        )
        == "D1IN0820"
        for result in results
    )


def test_chilli_powder_retrieval():
    service = create_retrieval_service()

    results = service.retrieve(
        "Which transaction contains "
        "chilli powder?",
        top_k=3,
    )

    assert any(
        result.metadata.get(
            "transaction_number"
        )
        == "D1IN0818"
        for result in results
    )


def test_real_top_k():
    service = create_retrieval_service()

    results = service.retrieve(
        "inventory products received",
        top_k=2,
    )

    assert len(results) <= 2


def test_real_results_have_required_data():
    service = create_retrieval_service()

    results = service.retrieve(
        "D1IN0818",
        top_k=1,
    )

    assert len(results) == 1

    result = results[0]

    assert result.chunk_id
    assert isinstance(
        result.score,
        float,
    )
    assert result.text
    assert result.metadata