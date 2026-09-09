from openai import OpenAI

from .base import LLMService, LLMServiceError


class OpenAILLMService(LLMService):
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ):
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is required."
            )

        if not model:
            raise ValueError(
                "OPENAI_MODEL is required."
            )

        self.model = model
        self.client = OpenAI(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str,
    ) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                input=prompt,
            )

            answer = response.output_text.strip()

            if not answer:
                raise LLMServiceError(
                    "LLM returned an empty response."
                )

            return answer

        except LLMServiceError:
            raise

        except Exception as exc:
            raise LLMServiceError(
                "LLM request failed."
            ) from exc