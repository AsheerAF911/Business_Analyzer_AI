import numpy as np

from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)


def test_real_bge_m3_embedding():
    service = BGEM3EmbeddingService()

    texts = [
        "Inventory transaction D1IN0818",
        "Inventory transaction D1IN0819",
        "Inventory transaction D1IN0820",
    ]

    embeddings = service.embed_texts(texts)

    assert embeddings.shape == (3, 1024)

    assert np.issubdtype(
        embeddings.dtype,
        np.number,
    )