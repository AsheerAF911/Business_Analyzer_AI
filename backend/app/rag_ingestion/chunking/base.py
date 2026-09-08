from __future__ import annotations

from abc import ABC, abstractmethod

from app.rag_ingestion.models import Chunk, Document


class ChunkingStrategy(ABC):
    @abstractmethod
    def create_chunks(self, document: Document) -> list[Chunk]:
        raise NotImplementedError