from __future__ import annotations

from app.rag_ingestion.embeddings import (
    EmbeddingService,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)

from .models import RetrievalResult


class RetrievalService:
    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        vector_store: QdrantService,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        self._validate_query(
            query=query,
            top_k=top_k,
        )

        query_vector = (
            self.embedding_service.embed_text(
                query
            )
        )

        points = (
            self.vector_store.search_by_vector(
                query_vector=query_vector,
                top_k=top_k,
            )
        )

        results: list[RetrievalResult] = []

        for point in points:
            payload = point.payload or {}

            chunk_id = payload.get("chunk_id")
            text = payload.get("text")
            metadata = payload.get("metadata")

            if not isinstance(chunk_id, str):
                raise RuntimeError(
                    "Retrieved Qdrant point is missing "
                    "a valid chunk_id."
                )

            if not isinstance(text, str):
                raise RuntimeError(
                    "Retrieved Qdrant point is missing "
                    "valid chunk text."
                )

            if not isinstance(metadata, dict):
                raise RuntimeError(
                    "Retrieved Qdrant point is missing "
                    "valid chunk metadata."
                )

            results.append(
                RetrievalResult(
                    chunk_id=chunk_id,
                    score=float(point.score),
                    text=text,
                    metadata=metadata,
                )
            )

        return results

    @staticmethod
    def _validate_query(
        *,
        query: str,
        top_k: int,
    ) -> None:
        if not isinstance(query, str):
            raise TypeError(
                "Query must be a string."
            )

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )