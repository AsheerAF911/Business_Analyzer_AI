from types import SimpleNamespace
from unittest.mock import MagicMock

from app.llm import (
    LLMEvidence,
    LLMRequest,
)
from app.llm.providers import (
    OpenRouterProvider,
)


def test_openrouter_provider_converts_response():
    provider = OpenRouterProvider(
        api_key="test-key",
        model="test-model",
    )

    provider.client = MagicMock()

    provider.client.chat.completions.create.return_value = (
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Provider answer"
                    )
                )
            ]
        )
    )

    request = LLMRequest(
        question="What was received?",
        evidence=[
            LLMEvidence(
                chunk_id="chunk-1",
                text="Inventory evidence",
                score=0.8,
                metadata={
                    "transaction_number":
                        "D1IN0818"
                },
            )
        ],
        system_instructions=(
            "Answer only from evidence."
        ),
    )

    result = provider.generate(
        request
    )

    assert result.text == "Provider answer"

    provider.client.chat.completions.create.assert_called_once()