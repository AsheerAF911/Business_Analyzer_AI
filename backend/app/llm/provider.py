from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    LLMRequest,
    LLMResponse,
)


class LLMProviderError(RuntimeError):
    pass


class LLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        raise NotImplementedError