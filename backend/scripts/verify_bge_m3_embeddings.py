from pathlib import Path

from app.ingestion.parsers.excel import ExcelParser
from app.rag_ingestion import DocumentBuilder
from app.rag_ingestion.chunking import (
    InventoryTransactionChunkingStrategy,
)
from app.rag_ingestion.embeddings import (
    BGEM3EmbeddingService,
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

    embedding_service = BGEM3EmbeddingService()

    embeddings = embedding_service.embed_texts(
        [chunk.text for chunk in chunks]
    )

    print(f"Number of chunks: {len(chunks)}")
    print(
        f"Number of embeddings: "
        f"{len(embeddings)}"
    )
    print(
        f"Embedding dimension: "
        f"{embeddings.shape[1]}"
    )

    for chunk, embedding in zip(
        chunks,
        embeddings,
    ):
        print()
        print(f"Chunk ID: {chunk.chunk_id}")
        print(
            "First 5 embedding values:",
            embedding[:5],
        )


if __name__ == "__main__":
    main()