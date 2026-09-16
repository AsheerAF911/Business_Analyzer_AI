from __future__ import annotations

import json

from openai import OpenAI

from app.llm.models import (
    LLMRequest,
    LLMResponse,
)
from app.llm.provider import (
    LLMProvider,
    LLMProviderError,
)


class OpenRouterProvider(LLMProvider):

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ):
        if not api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is required."
            )

        if not model:
            raise ValueError(
                "OPENROUTER_MODEL is required."
            )

        self.model = model

        self.client = OpenAI(
            api_key=api_key,
            base_url=self.BASE_URL,
        )

    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:

        prompt = self._build_prompt(
            request
        )

        try:
            response = (
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )
            )

            content = (
                response
                .choices[0]
                .message
                .content
            )

            if not content:
                raise LLMProviderError(
                    "LLM provider returned "
                    "an empty response."
                )

            return LLMResponse(
                text=content.strip()
            )

        except LLMProviderError:
            raise

        except Exception as exc:
            raise LLMProviderError(
                "OpenRouter request failed."
            ) from exc

    @staticmethod
    def _build_prompt(
        request: LLMRequest,
    ) -> str:

        sections: list[str] = []

        if request.system_instructions:
            sections.append(
                request.system_instructions.strip()
            )

        sections.append(
            f"QUESTION:\n{request.question}"
        )

        evidence_sections: list[str] = []

        for index, item in enumerate(
            request.evidence,
            start=1,
        ):
            evidence_sections.append(
                "\n".join(
                    [
                        f"EVIDENCE {index}",
                        f"Chunk ID: {item.chunk_id}",
                        f"Score: {item.score}",
                        "Metadata: "
                        + json.dumps(
                            item.metadata,
                            default=str,
                        ),
                        "Content:",
                        item.text,
                    ]
                )
            )

        sections.append(
            "RETRIEVED EVIDENCE:\n\n"
            + "\n\n".join(
                evidence_sections
            )
        )

        return "\n\n".join(sections)