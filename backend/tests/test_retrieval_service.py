import numpy as np
import pytest

from app.rag_ingestion.retrieval import (
    RetrievalService,
)


class FakeEmbeddingService:
    @property
    def dimension(self):
        return 1024

    def embed_text(self, text):
        return np.ones(
            1024,
            dtype=np.float32,
        )

    def embed_texts(self, texts):
        return np.ones(
            (len(texts), 1024),
            dtype=np.float32,
        )


class FakePoint:
    def __init__(
        self,
        *,
        chunk_id,
        score,
        text,
        metadata,
    ):
        self.score = score

        self.payload = {
            "chunk_id": chunk_id,
            "text": text,
            "metadata": metadata,
        }


class FakeQdrantService:
    def __init__(self):
        self.last_top_k = None
        self.last_query_vector = None

        self.points = [
            FakePoint(
                chunk_id=(
                    "Inventory_transactions-"
                    "Sheet1-transaction-D1IN0818"
                ),
                score=0.95,
                text=(
                    "Inventory transaction "
                    "D1IN0818."
                ),
                metadata={
                    "source_file":
                        "Inventory_transactions.xlsx",
                    "sheet": "Sheet1",
                    "source_rows": [2, 3, 4, 5],
                    "transaction_number":
                        "D1IN0818",
                    "supplier": "D1",
                },
            ),
            FakePoint(
                chunk_id=(
                    "Inventory_transactions-"
                    "Sheet1-transaction-D1IN0820"
                ),
                score=0.80,
                text=(
                    "Inventory transaction "
                    "D1IN0820."
                ),
                metadata={
                    "source_file":
                        "Inventory_transactions.xlsx",
                    "sheet": "Sheet1",
                    "source_rows": [
                        7, 8, 9, 10,
                        11, 12, 13, 14,
                    ],
                    "transaction_number":
                        "D1IN0820",
                },
            ),
            FakePoint(
                chunk_id=(
                    "Inventory_transactions-"
                    "Sheet1-transaction-D1IN0819"
                ),
                score=0.65,
                text=(
                    "Inventory transaction "
                    "D1IN0819."
                ),
                metadata={
                    "source_file":
                        "Inventory_transactions.xlsx",
                    "sheet": "Sheet1",
                    "source_rows": [6],
                    "transaction_number":
                        "D1IN0819",
                },
            ),
        ]

    def search_by_vector(
        self,
        *,
        query_vector,
        top_k=3,
    ):
        self.last_query_vector = query_vector
        self.last_top_k = top_k

        return self.points[:top_k]


@pytest.fixture
def vector_store():
    return FakeQdrantService()


@pytest.fixture
def service(vector_store):
    return RetrievalService(
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
    )


def test_query_is_embedded(
    service,
    vector_store,
):
    service.retrieve(
        "Which products were received "
        "under D1IN0818?"
    )

    assert (
        vector_store.last_query_vector.shape
        == (1024,)
    )


def test_top_k_is_respected(
    service,
):
    results = service.retrieve(
        "inventory",
        top_k=2,
    )

    assert len(results) == 2


def test_result_order_is_preserved(
    service,
):
    results = service.retrieve(
        "inventory",
        top_k=3,
    )

    assert results[0].score == 0.95
    assert results[1].score == 0.80
    assert results[2].score == 0.65


def test_results_contain_required_fields(
    service,
):
    result = service.retrieve(
        "D1IN0818",
        top_k=1,
    )[0]

    assert result.chunk_id
    assert isinstance(result.score, float)
    assert result.text
    assert isinstance(result.metadata, dict)


def test_original_metadata_is_preserved(
    service,
):
    result = service.retrieve(
        "D1IN0818",
        top_k=1,
    )[0]

    assert (
        result.metadata["source_rows"]
        == [2, 3, 4, 5]
    )

    assert (
        result.metadata[
            "transaction_number"
        ]
        == "D1IN0818"
    )


def test_empty_query_is_rejected(
    service,
):
    with pytest.raises(ValueError):
        service.retrieve("   ")


def test_invalid_top_k_is_rejected(
    service,
):
    with pytest.raises(ValueError):
        service.retrieve(
            "inventory",
            top_k=0,
        )