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

from app.llm import (
    LLMProvider,
    LLMService,
)
from app.llm.providers import (
    OpenRouterProvider,
)

from app.answering import AnswerService

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.structured_data import StructuredDataService


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

@lru_cache
def get_answer_service() -> AnswerService:
    return AnswerService(
        retrieval_service=get_retrieval_service(),
        llm_service=get_llm_service(),
    )

@lru_cache
def get_llm_provider() -> LLMProvider:

    provider_name = os.getenv(
        "LLM_PROVIDER",
        "openrouter",
    ).strip().lower()

    if provider_name == "openrouter":
        return OpenRouterProvider(
            api_key=os.getenv(
                "OPENROUTER_API_KEY",
                "",
            ),
            model=os.getenv(
                "OPENROUTER_MODEL",
                "openrouter/free",
            ),
        )

    raise RuntimeError(
        "Unsupported LLM provider: "
        f"{provider_name}"
    )


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService(
        provider=get_llm_provider()
    )

def get_structured_data_service(
    db: Session = Depends(get_db),
) -> StructuredDataService:
    return StructuredDataService(
        db=db,
    )