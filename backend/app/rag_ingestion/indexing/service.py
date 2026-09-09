from __future__ import annotations

from dataclasses import dataclass

from app.ingestion.parsers.base import ParsedRecord
from app.rag_ingestion import DocumentBuilder
from app.rag_ingestion.chunking import (
    InventoryTransactionChunkingStrategy,
)
from app.rag_ingestion.embeddings import EmbeddingService
from app.rag_ingestion.models import Chunk
from app.rag_ingestion.vector_store import QdrantService


class UnsupportedRAGReportTypeError(ValueError):
    pass


@dataclass
class RAGIndexingResult:
    parsed_record_count: int
    chunk_count: int
    indexed_point_count: int


class RAGIndexingService:
    def __init__(
        self,
        *,
        embedding_service: EmbeddingService,
        vector_store: QdrantService,
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.document_builder = DocumentBuilder()

    def index_records(
        self,
        *,
        records: list[ParsedRecord],
        report_type: str,
    ) -> RAGIndexingResult:
        if not records:
            raise ValueError(
                "Cannot index a report containing no parsed records."
            )

        document = self.document_builder.build(
            records=records,
            report_type=report_type,
        )

        chunking_strategy = self._get_chunking_strategy(
            report_type
        )

        chunks = chunking_strategy.create_chunks(
            document
        )

        if not chunks:
            raise ValueError(
                "Report processing produced no searchable chunks."
            )

        embeddings = self.embedding_service.embed_texts(
            [chunk.text for chunk in chunks]
        )

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "Embedding count does not match chunk count."
            )

        self.vector_store.upsert_chunks(
            chunks=chunks,
            embeddings=embeddings,
        )

        return RAGIndexingResult(
            parsed_record_count=len(records),
            chunk_count=len(chunks),
            indexed_point_count=len(chunks),
        )

    @staticmethod
    def _get_chunking_strategy(
        report_type: str,
    ):
        normalized = report_type.strip().lower()

        if normalized == "inventory":
            return InventoryTransactionChunkingStrategy()

        raise UnsupportedRAGReportTypeError(
            "No RAG chunking strategy is configured "
            f"for report type '{report_type}'."
        )