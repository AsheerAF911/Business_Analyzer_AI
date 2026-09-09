import numpy as np

from app.rag_ingestion.models import Chunk
from app.rag_ingestion.vector_store import (
    QdrantService,
)


def test_real_qdrant_storage():
    service = QdrantService(
        vector_dimension=1024,
        collection_name="business_ai_rag_test",
    )

    chunk = Chunk(
        chunk_id="integration-test-chunk",
        document_id="integration-test-document",
        text="Integration test chunk.",
        metadata={
            "source_file": "test.xlsx",
            "sheet": "Sheet1",
            "source_rows": [2],
        },
    )

    embeddings = np.ones(
        (1, 1024),
        dtype=np.float32,
    )

    service.upsert_chunks(
        chunks=[chunk],
        embeddings=embeddings,
    )

    point = service.get_chunk_point(
        chunk.chunk_id
    )

    assert point is not None
    assert len(point.vector) == 1024
    assert point.payload["chunk_id"] == chunk.chunk_id
    assert point.payload["text"] == chunk.text
    assert point.payload["metadata"] == chunk.metadata