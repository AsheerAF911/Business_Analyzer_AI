from functools import lru_cache
import os

from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
    EmbeddingService,
)
from app.rag_ingestion.indexing import (
    RAGIndexingService,
)
from app.rag_ingestion.retrieval import (
    RetrievalService,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return BGEM3EmbeddingService()


@lru_cache
def get_qdrant_service() -> QdrantService:
    embedding_service = get_embedding_service()

    return QdrantService(
        vector_dimension=embedding_service.dimension,
    )


@lru_cache
def get_rag_indexing_service() -> RAGIndexingService:
    return RAGIndexingService(
        embedding_service=get_embedding_service(),
        vector_store=get_qdrant_service(),
    )


@lru_cache
def get_retrieval_service() -> RetrievalService:
    return RetrievalService(
        embedding_service=get_embedding_service(),
        vector_store=get_qdrant_service(),
    )

from app.llm import (
    LLMService,
    OpenAILLMService,
)


@lru_cache
def get_llm_service() -> LLMService:
    provider = os.getenv(
        "LLM_PROVIDER",
        "openai",
    ).lower()

    if provider == "openai":
        return OpenAILLMService(
            api_key=os.getenv(
                "OPENAI_API_KEY",
                "",
            ),
            model=os.getenv(
                "OPENAI_MODEL",
                "",
            ),
        )

    raise RuntimeError(
        f"Unsupported LLM provider: {provider}"
    )