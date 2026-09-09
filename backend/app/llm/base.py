from abc import ABC, abstractmethod


class LLMServiceError(RuntimeError):
    pass


class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError