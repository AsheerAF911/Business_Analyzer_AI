from __future__ import annotations

import os
from collections.abc import Sequence
from uuid import NAMESPACE_URL, uuid5

import numpy as np
from qdrant_client import QdrantClient, models

from app.rag_ingestion.models import Chunk


class QdrantConfigurationError(RuntimeError):
    pass


class QdrantService:
    DEFAULT_URL = "http://localhost:6333"
    DEFAULT_COLLECTION_NAME = "business_ai_rag"

    def __init__(
        self,
        *,
        vector_dimension: int,
        url: str | None = None,
        collection_name: str | None = None,
        client: QdrantClient | None = None,
    ):
        if vector_dimension <= 0:
            raise ValueError(
                "vector_dimension must be greater than zero."
            )

        self.vector_dimension = vector_dimension

        self.url = (
            url
            or os.getenv("QDRANT_URL")
            or self.DEFAULT_URL
        )

        self.collection_name = (
            collection_name
            or os.getenv("QDRANT_COLLECTION_NAME")
            or self.DEFAULT_COLLECTION_NAME
        )

        self.client = client or QdrantClient(
            url=self.url
        )

    def ensure_collection(self) -> None:
        if not self.client.collection_exists(
            self.collection_name
        ):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_dimension,
                    distance=models.Distance.COSINE,
                ),
            )

            return

        collection = self.client.get_collection(
            self.collection_name
        )

        vectors_config = (
            collection.config.params.vectors
        )

        if not isinstance(
            vectors_config,
            models.VectorParams,
        ):
            raise QdrantConfigurationError(
                "Expected a single dense-vector "
                "configuration for the collection."
            )

        if vectors_config.size != self.vector_dimension:
            raise QdrantConfigurationError(
                "Existing Qdrant collection has an "
                "unexpected vector dimension. "
                f"Expected {self.vector_dimension}, "
                f"found {vectors_config.size}."
            )

        if vectors_config.distance != models.Distance.COSINE:
            raise QdrantConfigurationError(
                "Existing Qdrant collection has an "
                "unexpected distance metric. "
                "Expected COSINE."
            )

    def reset_collection(self) -> None:
        if self.client.collection_exists(
            self.collection_name
        ):
            self.client.delete_collection(
                collection_name=self.collection_name
            )

        self.ensure_collection()

    def upsert_chunks(
        self,
        *,
        chunks: Sequence[Chunk],
        embeddings: np.ndarray,
    ) -> None:
        chunks = list(chunks)
        embeddings = np.asarray(embeddings)

        if not chunks:
            raise ValueError(
                "At least one chunk is required."
            )

        expected_shape = (
            len(chunks),
            self.vector_dimension,
        )

        if embeddings.shape != expected_shape:
            raise ValueError(
                "Embedding matrix has unexpected shape. "
                f"Expected {expected_shape}, "
                f"received {embeddings.shape}."
            )

        if not np.issubdtype(
            embeddings.dtype,
            np.number,
        ):
            raise TypeError(
                "Embeddings must contain numeric values."
            )

        self.ensure_collection()

        points = []

        for chunk, embedding in zip(
            chunks,
            embeddings,
        ):
            point_id = self.point_id_for_chunk(
                chunk.chunk_id
            )

            payload = {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload=payload,
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def get_chunk_point(
        self,
        chunk_id: str,
        *,
        with_vector: bool = True,
    ):
        point_id = self.point_id_for_chunk(
            chunk_id
        )

        points = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[point_id],
            with_payload=True,
            with_vectors=with_vector,
        )

        if not points:
            return None

        return points[0]

    def count_points(self) -> int:
        result = self.client.count(
            collection_name=self.collection_name,
            exact=True,
        )

        return result.count

    @staticmethod
    def point_id_for_chunk(
        chunk_id: str,
    ) -> str:
        if not chunk_id:
            raise ValueError(
                "chunk_id cannot be empty."
            )

        return str(
            uuid5(
                NAMESPACE_URL,
                f"business-ai:{chunk_id}",
            )
        )

    def search_by_vector(
        self,
        *,
        query_vector: np.ndarray,
        top_k: int = 3,
    ):
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query_vector = np.asarray(query_vector)

        expected_shape = (
            self.vector_dimension,
        )

        if query_vector.shape != expected_shape:
            raise ValueError(
                "Query vector has unexpected shape. "
                f"Expected {expected_shape}, "
                f"received {query_vector.shape}."
            )

        if not np.issubdtype(
            query_vector.dtype,
            np.number,
        ):
            raise TypeError(
                "Query vector must contain numeric values."
            )

        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        return result.points