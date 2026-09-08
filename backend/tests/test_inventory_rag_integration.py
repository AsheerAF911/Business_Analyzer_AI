from pathlib import Path

from app.ingestion.parsers.excel import ExcelParser
from app.rag_ingestion import DocumentBuilder
from app.rag_ingestion.chunking import (
    InventoryTransactionChunkingStrategy,
)


def test_real_inventory_file_creates_expected_transaction_chunks():
    file_path = (
        Path(__file__).resolve().parents[1]
        / "Inventory_transactions.xlsx"
    )

    parser = ExcelParser()

    records = parser.parse(
        file_path=file_path,
        source_file="Inventory_transactions.xlsx",
    )

    assert len(records) == 13

    document = DocumentBuilder().build(
        records=records,
        report_type="inventory",
    )

    chunks = (
        InventoryTransactionChunkingStrategy()
        .create_chunks(document)
    )

    assert len(chunks) == 3

    chunks_by_transaction = {
        chunk.metadata["transaction_number"]: chunk
        for chunk in chunks
    }

    assert set(chunks_by_transaction) == {
        "D1IN0818",
        "D1IN0819",
        "D1IN0820",
    }

    assert (
        chunks_by_transaction["D1IN0818"]
        .metadata["source_rows"]
        == [2, 3, 4, 5]
    )

    assert (
        chunks_by_transaction["D1IN0819"]
        .metadata["source_rows"]
        == [6]
    )

    assert (
        chunks_by_transaction["D1IN0820"]
        .metadata["source_rows"]
        == [7, 8, 9, 10, 11, 12, 13, 14]
    )

    for transaction_number, chunk in chunks_by_transaction.items():
        print("\n")
        print("=" * 80)
        print(f"TRANSACTION: {transaction_number}")
        print(f"CHUNK ID: {chunk.chunk_id}")
        print(f"METADATA: {chunk.metadata}")
        print("TEXT:")
        print(chunk.text)