import numpy as np
import pytest

import app.rag_ingestion.embeddings.bge_m3 as bge_module
from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)


class FakeSentenceTransformer:
    load_count = 0

    def __init__(
        self,
        model_name,
        **kwargs,
    ):
        FakeSentenceTransformer.load_count += 1
        self.model_name = model_name

    def get_sentence_embedding_dimension(self):
        return 1024

    def encode(
        self,
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
    ):
        embeddings = []

        for index, _ in enumerate(texts):
            vector = np.full(
                1024,
                fill_value=float(index + 1),
                dtype=np.float32,
            )

            embeddings.append(vector)

        return np.stack(embeddings)


@pytest.fixture
def embedding_service(monkeypatch):
    FakeSentenceTransformer.load_count = 0

    monkeypatch.setattr(
        bge_module,
        "SentenceTransformer",
        FakeSentenceTransformer,
    )

    return BGEM3EmbeddingService()


def test_one_text_produces_one_embedding(
    embedding_service,
):
    embedding = embedding_service.embed_text(
        "Inventory transaction D1IN0818"
    )

    assert embedding.shape == (1024,)


def test_three_texts_produce_three_embeddings(
    embedding_service,
):
    embeddings = embedding_service.embed_texts(
        [
            "Transaction one",
            "Transaction two",
            "Transaction three",
        ]
    )

    assert embeddings.shape == (3, 1024)


def test_each_embedding_has_1024_dimensions(
    embedding_service,
):
    embeddings = embedding_service.embed_texts(
        [
            "Transaction one",
            "Transaction two",
            "Transaction three",
        ]
    )

    assert all(
        len(vector) == 1024
        for vector in embeddings
    )


def test_embeddings_are_numeric(
    embedding_service,
):
    embedding = embedding_service.embed_text(
        "Inventory transaction"
    )

    assert np.issubdtype(
        embedding.dtype,
        np.number,
    )


def test_empty_text_is_rejected(
    embedding_service,
):
    with pytest.raises(ValueError):
        embedding_service.embed_text("   ")


def test_empty_batch_is_rejected(
    embedding_service,
):
    with pytest.raises(ValueError):
        embedding_service.embed_texts([])


def test_non_string_text_is_rejected(
    embedding_service,
):
    with pytest.raises(TypeError):
        embedding_service.embed_texts(
            ["valid", None]
        )


def test_batch_preserves_input_order(
    embedding_service,
):
    embeddings = embedding_service.embed_texts(
        [
            "chunk-1",
            "chunk-2",
            "chunk-3",
        ]
    )

    assert embeddings[0][0] == 1.0
    assert embeddings[1][0] == 2.0
    assert embeddings[2][0] == 3.0


def test_model_is_loaded_only_once(
    embedding_service,
):
    embedding_service.embed_text("first")
    embedding_service.embed_text("second")

    assert FakeSentenceTransformer.load_count == 1