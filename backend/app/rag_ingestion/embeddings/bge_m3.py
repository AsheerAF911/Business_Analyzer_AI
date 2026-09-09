from __future__ import annotations

from collections.abc import Sequence
from functools import cached_property

import numpy as np
from sentence_transformers import SentenceTransformer

from .base import EmbeddingService


class BGEM3EmbeddingService(EmbeddingService):
    MODEL_NAME = "BAAI/bge-m3"
    EXPECTED_DIMENSION = 1024

    def __init__(
        self,
        device: str | None = None,
    ):
        self.device = device

    @property
    def dimension(self) -> int:
        return self.EXPECTED_DIMENSION

    @cached_property
    def _model(self) -> SentenceTransformer:
        kwargs = {}

        if self.device is not None:
            kwargs["device"] = self.device

        model = SentenceTransformer(
            self.MODEL_NAME,
            **kwargs,
        )

        actual_dimension = (
            model.get_embedding_dimension()
        )

        if actual_dimension != self.EXPECTED_DIMENSION:
            raise RuntimeError(
                "Unexpected BGE-M3 embedding dimension. "
                f"Expected {self.EXPECTED_DIMENSION}, "
                f"received {actual_dimension}."
            )

        return model

    def embed_text(
        self,
        text: str,
    ) -> np.ndarray:
        embeddings = self.embed_texts([text])

        return embeddings[0]

    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        validated_texts = self._validate_texts(texts)

        embeddings = self._model.encode(
            validated_texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        embeddings = np.asarray(embeddings)

        expected_shape = (
            len(validated_texts),
            self.EXPECTED_DIMENSION,
        )

        if embeddings.shape != expected_shape:
            raise RuntimeError(
                "Unexpected embedding shape. "
                f"Expected {expected_shape}, "
                f"received {embeddings.shape}."
            )

        if not np.issubdtype(
            embeddings.dtype,
            np.number,
        ):
            raise RuntimeError(
                "Embedding model returned non-numeric values."
            )

        return embeddings

    @staticmethod
    def _validate_texts(
        texts: Sequence[str],
    ) -> list[str]:
        texts = list(texts)

        if not texts:
            raise ValueError(
                "At least one text is required for embedding."
            )

        for index, text in enumerate(texts):
            if not isinstance(text, str):
                raise TypeError(
                    f"Text at index {index} must be a string."
                )

            if not text.strip():
                raise ValueError(
                    f"Text at index {index} cannot be empty."
                )

        return texts