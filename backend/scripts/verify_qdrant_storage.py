from pathlib import Path

from app.ingestion.parsers.excel import ExcelParser
from app.rag_ingestion import DocumentBuilder
from app.rag_ingestion.chunking import (
    InventoryTransactionChunkingStrategy,
)
from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
)
from app.rag_ingestion.vector_store import (
    QdrantService,
)


def main():
    backend_dir = Path(__file__).resolve().parents[1]

    file_path = (
        backend_dir
        / "Inventory_transactions.xlsx"
    )

    parser = ExcelParser()

    records = parser.parse(
        file_path=file_path,
        source_file=file_path.name,
    )

    document = DocumentBuilder().build(
        records=records,
        report_type="inventory",
    )

    chunks = (
        InventoryTransactionChunkingStrategy()
        .create_chunks(document)
    )

    embedding_service = (
        BGEM3EmbeddingService()
    )

    embeddings = embedding_service.embed_texts(
        [chunk.text for chunk in chunks]
    )

    qdrant = QdrantService(
        vector_dimension=embedding_service.dimension,
    )

    qdrant.upsert_chunks(
        chunks=chunks,
        embeddings=embeddings,
    )

    print(
        f"Collection: "
        f"{qdrant.collection_name}"
    )

    print(
        f"Number of chunks: "
        f"{len(chunks)}"
    )

    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )

    print(
        f"Vector dimension: "
        f"{embedding_service.dimension}"
    )

    print(
        f"Stored points: "
        f"{qdrant.count_points()}"
    )

    print()

    for chunk in chunks:
        point = qdrant.get_chunk_point(
            chunk.chunk_id,
            with_vector=True,
        )

        print("=" * 80)
        print(
            f"Chunk ID: "
            f"{point.payload['chunk_id']}"
        )

        print(
            f"Metadata: "
            f"{point.payload['metadata']}"
        )

        print(
            f"Text preview: "
            f"{point.payload['text']}"
        )

        print(
            f"Vector dimension: "
            f"{len(point.vector)}"
        )


if __name__ == "__main__":
    main()