from fastapi.testclient import TestClient

from app.answering import (
    AnswerResult,
    AnswerSource,
)
from app.dependencies import (
    get_answer_service,
)
from app.main import app


class FakeAnswerService:
    def answer(
        self,
        question,
        *,
        top_k=3,
    ):
        return AnswerResult(
            answer=(
                "D1IN0818 contains the "
                "requested inventory evidence."
            ),
            sources=[
                AnswerSource(
                    chunk_id=(
                        "Inventory_transactions-"
                        "Sheet1-transaction-"
                        "D1IN0818"
                    ),
                    score=0.646921,
                    metadata={
                        "source_file":
                            "Inventory_transactions.xlsx",
                        "sheet":
                            "Sheet1",
                        "source_rows":
                            [2, 3, 4, 5],
                        "transaction_number":
                            "D1IN0818",
                    },
                )
            ],
        )


def test_ask_api_returns_answer_and_sources():
    app.dependency_overrides[
        get_answer_service
    ] = lambda: FakeAnswerService()

    client = TestClient(app)

    response = client.post(
        "/api/ask",
        json={
            "question":
                "Which products were "
                "received under D1IN0818?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"]
    assert len(data["sources"]) == 1

    assert (
        data["sources"][0]
        ["transaction_number"]
        == "D1IN0818"
    )

    assert (
        data["sources"][0]
        ["source_rows"]
        == [2, 3, 4, 5]
    )

    app.dependency_overrides.clear()


def test_empty_question_is_rejected():
    client = TestClient(app)

    response = client.post(
        "/api/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422