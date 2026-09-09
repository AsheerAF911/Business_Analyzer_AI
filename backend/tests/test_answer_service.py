import pytest

from app.answering import AnswerService
from app.rag_ingestion.retrieval import (
    RetrievalResult,
)


class FakeRetrievalService:
    def __init__(self, results):
        self.results = results
        self.last_question = None
        self.last_top_k = None

    def retrieve(
        self,
        query,
        *,
        top_k=3,
    ):
        self.last_question = query
        self.last_top_k = top_k
        return self.results


class FakeLLMService:
    def __init__(
        self,
        response="Test answer",
    ):
        self.response = response
        self.last_prompt = None
        self.call_count = 0

    def generate(self, prompt):
        self.call_count += 1
        self.last_prompt = prompt
        return self.response


@pytest.fixture
def evidence():
    return [
        RetrievalResult(
            chunk_id=(
                "Inventory_transactions-"
                "Sheet1-transaction-D1IN0818"
            ),
            score=0.646921,
            text=(
                "Inventory transaction "
                "D1IN0818.\n"
                "Product: RM_CHILLI POWDER\n"
                "Barcode: 30955"
            ),
            metadata={
                "source_file":
                    "Inventory_transactions.xlsx",
                "sheet": "Sheet1",
                "source_rows": [2, 3, 4, 5],
                "transaction_number":
                    "D1IN0818",
            },
        )
    ]


def test_retrieval_is_called(
    evidence,
):
    retrieval = FakeRetrievalService(
        evidence
    )

    llm = FakeLLMService()

    service = AnswerService(
        retrieval_service=retrieval,
        llm_service=llm,
    )

    service.answer(
        "Which products were received "
        "under D1IN0818?"
    )

    assert (
        retrieval.last_question
        == "Which products were received under D1IN0818?"
    )


def test_llm_receives_evidence(
    evidence,
):
    retrieval = FakeRetrievalService(
        evidence
    )

    llm = FakeLLMService()

    service = AnswerService(
        retrieval_service=retrieval,
        llm_service=llm,
    )

    service.answer("D1IN0818")

    assert llm.call_count == 1
    assert "D1IN0818" in llm.last_prompt
    assert "RM_CHILLI POWDER" in llm.last_prompt
    assert "Inventory_transactions.xlsx" in llm.last_prompt


def test_answer_preserves_sources(
    evidence,
):
    service = AnswerService(
        retrieval_service=
            FakeRetrievalService(evidence),
        llm_service=
            FakeLLMService("Answer"),
    )

    result = service.answer(
        "D1IN0818"
    )

    assert result.answer == "Answer"

    assert (
        result.sources[0]
        .metadata["source_rows"]
        == [2, 3, 4, 5]
    )


def test_empty_question_rejected():
    service = AnswerService(
        retrieval_service=
            FakeRetrievalService([]),
        llm_service=
            FakeLLMService(),
    )

    with pytest.raises(ValueError):
        service.answer("   ")


def test_no_evidence_does_not_call_llm():
    llm = FakeLLMService()

    service = AnswerService(
        retrieval_service=
            FakeRetrievalService([]),
        llm_service=llm,
    )

    result = service.answer(
        "Unknown information"
    )

    assert llm.call_count == 0
    assert result.sources == []
    assert (
        "insufficient evidence"
        in result.answer.lower()
    )


def test_llm_can_represent_insufficient_evidence(
    evidence,
):
    response = (
        "There is insufficient evidence "
        "to answer this question."
    )

    service = AnswerService(
        retrieval_service=
            FakeRetrievalService(evidence),
        llm_service=
            FakeLLMService(response),
    )

    result = service.answer(
        "Which supplier has the "
        "highest inventory value?"
    )

    assert result.answer == response