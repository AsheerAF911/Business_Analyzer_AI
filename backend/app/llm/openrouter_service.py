from openai import OpenAI

from .base import LLMService, LLMServiceError


class OpenRouterLLMService(LLMService):
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
        prompt: str,
    ) -> str:
        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
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
                raise LLMServiceError(
                    "LLM returned an empty response."
                )

            return content.strip()

        except LLMServiceError:
            raise

        except Exception as exc:
            raise LLMServiceError(
                "OpenRouter request failed."
            ) from exc