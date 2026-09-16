from app.llm import (
    LLMEvidence,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    LLMService,
)


class FakeLLMProvider(LLMProvider):

    def __init__(self):
        self.received_request = None

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        self.received_request = request

        return LLMResponse(
            text="Test answer"
        )


def make_evidence() -> list[LLMEvidence]:
    return [
        LLMEvidence(
            chunk_id=(
                "test-transaction-D1IN0818"
            ),
            text=(
                "Inventory transaction "
                "D1IN0818 contains chilli powder."
            ),
            score=0.8,
            metadata={
                "transaction_number":
                    "D1IN0818",
                "source_rows":
                    [2, 3, 4, 5],
            },
        )
    ]


def test_llm_service_calls_provider():
    provider = FakeLLMProvider()

    service = LLMService(
        provider=provider
    )

    service.generate_answer(
        question="What was received?",
        evidence=make_evidence(),
    )

    assert (
        provider.received_request
        is not None
    )


def test_provider_receives_question():
    provider = FakeLLMProvider()

    service = LLMService(
        provider=provider
    )

    service.generate_answer(
        question=(
            "Which transaction contains "
            "chilli powder?"
        ),
        evidence=make_evidence(),
    )

    assert (
        provider.received_request.question
        == (
            "Which transaction contains "
            "chilli powder?"
        )
    )


def test_provider_receives_evidence():
    provider = FakeLLMProvider()

    service = LLMService(
        provider=provider
    )

    service.generate_answer(
        question="Test question",
        evidence=make_evidence(),
    )

    evidence = (
        provider
        .received_request
        .evidence
    )

    assert len(evidence) == 1

    assert (
        evidence[0]
        .metadata["transaction_number"]
        == "D1IN0818"
    )


def test_provider_response_is_application_response():
    provider = FakeLLMProvider()

    service = LLMService(
        provider=provider
    )

    result = service.generate_answer(
        question="Test question",
        evidence=make_evidence(),
    )

    assert isinstance(
        result,
        LLMResponse,
    )

    assert result.text == "Test answer"


def test_system_instructions_reach_provider():
    provider = FakeLLMProvider()

    service = LLMService(
        provider=provider
    )

    service.generate_answer(
        question="Test question",
        evidence=make_evidence(),
        system_instructions=(
            "Answer only from evidence."
        ),
    )

    assert (
        provider
        .received_request
        .system_instructions
        == "Answer only from evidence."
    )