from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np


class EmbeddingService(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed one text.

        Returns:
            A one-dimensional numeric vector with shape:
            (dimension,)
        """
        raise NotImplementedError

    @abstractmethod
    def embed_texts(
        self,
        texts: Sequence[str],
    ) -> np.ndarray:
        """
        Embed multiple texts in one batch.

        Returns:
            A two-dimensional numeric array with shape:
            (number_of_texts, dimension)
        """
        raise NotImplementedError