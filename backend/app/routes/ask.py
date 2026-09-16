from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field

from app.answering import AnswerService
from app.dependencies import (
    get_answer_service,
)
from app.llm import LLMProviderError


router = APIRouter(
    prefix="/api",
    tags=["ask"],
)


class AskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )


class SourceResponse(BaseModel):
    chunk_id: str
    score: float
    source_file: str | None = None
    sheet: str | None = None
    source_rows: list[int] | None = None
    transaction_number: str | None = None
    metadata: dict[str, Any]


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


@router.post(
    "/ask",
    response_model=AskResponse,
)
def ask_question(
    request: AskRequest,
    answer_service: AnswerService = Depends(
        get_answer_service
    ),
):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty.",
        )

    try:
        result = answer_service.answer(
            question
        )

    except LLMProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                "The evidence database is currently "
                "unavailable."
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    sources = []

    for source in result.sources:
        metadata = source.metadata

        sources.append(
            SourceResponse(
                chunk_id=source.chunk_id,
                score=source.score,
                source_file=metadata.get(
                    "source_file"
                ),
                sheet=metadata.get(
                    "sheet"
                ),
                source_rows=metadata.get(
                    "source_rows"
                ),
                transaction_number=metadata.get(
                    "transaction_number"
                ),
                metadata=metadata,
            )
        )

    return AskResponse(
        answer=result.answer,
        sources=sources,
    )