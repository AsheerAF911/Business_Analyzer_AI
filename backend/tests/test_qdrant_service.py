import numpy as np
import pytest
from qdrant_client import models

from app.rag_ingestion.models import Chunk
from app.rag_ingestion.vector_store import (
    QdrantService,
)


class FakeCollectionParams:
    def __init__(self):
        self.vectors = models.VectorParams(
            size=1024,
            distance=models.Distance.COSINE,
        )


class FakeConfig:
    def __init__(self):
        self.params = FakeCollectionParams()


class FakeCollection:
    def __init__(self):
        self.config = FakeConfig()


class FakeCount:
    def __init__(self, count):
        self.count = count


class FakeClient:
    def __init__(self):
        self.exists = False
        self.points = {}
        self.created_config = None

    def collection_exists(self, name):
        return self.exists

    def create_collection(
        self,
        collection_name,
        vectors_config,
    ):
        self.exists = True
        self.created_config = vectors_config

    def get_collection(self, name):
        return FakeCollection()

    def upsert(
        self,
        collection_name,
        points,
        wait=True,
    ):
        for point in points:
            self.points[str(point.id)] = point

    def retrieve(
        self,
        collection_name,
        ids,
        with_payload=True,
        with_vectors=True,
    ):
        return [
            self.points[str(point_id)]
            for point_id in ids
            if str(point_id) in self.points
        ]

    def count(
        self,
        collection_name,
        exact=True,
    ):
        return FakeCount(len(self.points))

    def query_points(
        self,
        collection_name,
        query,
        limit,
        with_payload=True,
        with_vectors=False,
    ):
        class QueryResult:
            def __init__(self):
                self.points = []

        self.last_query = query
        self.last_limit = limit

        return QueryResult()

    def test_vector_search_uses_expected_top_k(
        service,
    ):
        query_vector = np.ones(
            1024,
            dtype=np.float32,
        )

        service.search_by_vector(
            query_vector=query_vector,
            top_k=2,
        )

        assert service.client.last_limit == 2

        assert (
            len(service.client.last_query)
            == 1024
        )


@pytest.fixture
def chunks():
    return [
        Chunk(
            chunk_id=(
                "Inventory_transactions-"
                "Sheet1-transaction-D1IN0818"
            ),
            document_id="Inventory_transactions",
            text="Inventory transaction D1IN0818",
            metadata={
                "source_file": (
                    "Inventory_transactions.xlsx"
                ),
                "sheet": "Sheet1",
                "source_rows": [2, 3, 4, 5],
                "transaction_number": "D1IN0818",
                "supplier": "D1",
            },
        ),
        Chunk(
            chunk_id=(
                "Inventory_transactions-"
                "Sheet1-transaction-D1IN0819"
            ),
            document_id="Inventory_transactions",
            text="Inventory transaction D1IN0819",
            metadata={
                "source_file": (
                    "Inventory_transactions.xlsx"
                ),
                "sheet": "Sheet1",
                "source_rows": [6],
                "transaction_number": "D1IN0819",
            },
        ),
        Chunk(
            chunk_id=(
                "Inventory_transactions-"
                "Sheet1-transaction-D1IN0820"
            ),
            document_id="Inventory_transactions",
            text="Inventory transaction D1IN0820",
            metadata={
                "source_file": (
                    "Inventory_transactions.xlsx"
                ),
                "sheet": "Sheet1",
                "source_rows": [
                    7, 8, 9, 10,
                    11, 12, 13, 14,
                ],
                "transaction_number": "D1IN0820",
            },
        ),
    ]


@pytest.fixture
def embeddings():
    return np.ones(
        (3, 1024),
        dtype=np.float32,
    )


@pytest.fixture
def service():
    client = FakeClient()

    return QdrantService(
        vector_dimension=1024,
        client=client,
    )


def test_collection_created_with_expected_config(
    service,
):
    service.ensure_collection()

    config = service.client.created_config

    assert config.size == 1024
    assert config.distance == models.Distance.COSINE


def test_three_chunks_create_three_points(
    service,
    chunks,
    embeddings,
):
    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    assert service.count_points() == 3


def test_point_contains_vector_and_payload(
    service,
    chunks,
    embeddings,
):
    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    point = service.get_chunk_point(
        chunks[0].chunk_id
    )

    assert point is not None
    assert len(point.vector) == 1024

    assert (
        point.payload["chunk_id"]
        == chunks[0].chunk_id
    )

    assert (
        point.payload["text"]
        == chunks[0].text
    )

    assert (
        point.payload["metadata"]
        == chunks[0].metadata
    )


def test_metadata_is_preserved_exactly(
    service,
    chunks,
    embeddings,
):
    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    point = service.get_chunk_point(
        chunks[0].chunk_id
    )

    assert (
        point.payload["metadata"]
        == chunks[0].metadata
    )


def test_duplicate_upsert_is_idempotent(
    service,
    chunks,
    embeddings,
):
    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    assert service.count_points() == 3

    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    assert service.count_points() == 3


def test_same_chunk_id_has_same_point_id(
    service,
    chunks,
):
    first = service.point_id_for_chunk(
        chunks[0].chunk_id
    )

    second = service.point_id_for_chunk(
        chunks[0].chunk_id
    )

    assert first == second


def test_direct_lookup_by_chunk_id(
    service,
    chunks,
    embeddings,
):
    service.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    point = service.get_chunk_point(
        chunks[1].chunk_id
    )

    assert point is not None

    assert (
        point.payload["chunk_id"]
        == chunks[1].chunk_id
    )


def test_wrong_embedding_dimension_rejected(
    service,
    chunks,
):
    bad_embeddings = np.ones(
        (3, 768),
        dtype=np.float32,
    )

    with pytest.raises(ValueError):
        service.upsert_chunks(
            chunks=chunks,
            embeddings=bad_embeddings,
        )