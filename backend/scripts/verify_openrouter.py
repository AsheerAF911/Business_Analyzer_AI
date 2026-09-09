import os

from dotenv import load_dotenv

from app.llm import (
    OpenRouterLLMService,
)


def main():
    load_dotenv()

    service = OpenRouterLLMService(
        api_key=os.getenv(
            "OPENROUTER_API_KEY",
            "",
        ),
        model=os.getenv(
            "OPENROUTER_MODEL",
            "openrouter/free",
        ),
    )

    response = service.generate(
        """
Answer using only this evidence.

Evidence:
Transaction D1IN0818 was received
from vendor D1.

Question:
Which vendor is associated with
D1IN0818?
"""
    )

    print("=" * 60)
    print("OpenRouter response")
    print("=" * 60)
    print(response)


if __name__ == "__main__":
    main()