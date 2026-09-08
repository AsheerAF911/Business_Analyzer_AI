from app.ingestion.parsers.base import ParsedRecord
from app.rag_ingestion import DocumentBuilder
from app.rag_ingestion.chunking import (
    InventoryTransactionChunkingStrategy,
)


def make_record(
    *,
    row_number,
    inward_no,
    product,
    vendor="D1",
    production="D17",
    date=46143,
):
    return ParsedRecord(
        source_file="Inventory_transactions.xlsx",
        sheet="Sheet1",
        row_number=row_number,
        fields={
            "PRODUCTION": production,
            "DATE": date,
            "INWARD NO": inward_no,
            "PRODUCT DESCRIPTION": product,
            "VENDOR NAME": vendor,
        },
    )


def build_chunks(records):
    document = DocumentBuilder().build(
        records=records,
        report_type="inventory",
    )

    return (
        InventoryTransactionChunkingStrategy()
        .create_chunks(document)
    )


def test_d1in0818_becomes_single_transaction_chunk():
    records = [
        make_record(
            row_number=2,
            inward_no="D1IN0818",
            product="Product A",
        ),
        make_record(
            row_number=3,
            inward_no="D1IN0818",
            product="Product B",
        ),
        make_record(
            row_number=4,
            inward_no="D1IN0818",
            product="Product C",
        ),
        make_record(
            row_number=5,
            inward_no="D1IN0818",
            product="Product D",
        ),
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.metadata["transaction_number"] == "D1IN0818"
    assert chunk.metadata["source_rows"] == [2, 3, 4, 5]


def test_d1in0820_becomes_single_transaction_chunk():
    records = [
        make_record(
            row_number=row_number,
            inward_no="D1IN0820",
            product=f"Product {row_number}",
        )
        for row_number in range(7, 15)
    ]

    chunks = build_chunks(records)

    assert len(chunks) == 1

    assert chunks[0].metadata["transaction_number"] == "D1IN0820"

    assert chunks[0].metadata["source_rows"] == [
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
    ]


def test_source_traceability_is_preserved():
    records = [
        make_record(
            row_number=2,
            inward_no="D1IN0818",
            product="Product A",
        )
    ]

    chunks = build_chunks(records)

    metadata = chunks[0].metadata

    assert (
        metadata["source_file"]
        == "Inventory_transactions.xlsx"
    )

    assert metadata["sheet"] == "Sheet1"
    assert metadata["source_rows"] == [2]


def test_missing_optional_metadata_is_safe():
    record = ParsedRecord(
        source_file="Inventory_transactions.xlsx",
        sheet="Sheet1",
        row_number=2,
        fields={
            "INWARD NO": "D1IN0818",
            "PRODUCT DESCRIPTION": "Product A",
        },
    )

    chunks = build_chunks([record])

    metadata = chunks[0].metadata

    assert "supplier" not in metadata
    assert "production" not in metadata
    assert "date" not in metadata


def test_no_invented_metadata_is_created():
    records = [
        make_record(
            row_number=2,
            inward_no="D1IN0818",
            product="Product A",
        )
    ]

    chunks = build_chunks(records)

    metadata = chunks[0].metadata

    assert "location" not in metadata
    assert "factory" not in metadata
    assert "department" not in metadata
    assert "customer" not in metadata


def test_vendor_name_mapping_is_explicit():
    records = [
        make_record(
            row_number=2,
            inward_no="D1IN0818",
            product="Product A",
            vendor="D1",
        )
    ]

    chunks = build_chunks(records)

    assert chunks[0].metadata["supplier"] == "D1"


def test_excel_date_serial_is_preserved():
    records = [
        make_record(
            row_number=2,
            inward_no="D1IN0818",
            product="Product A",
            date=46143,
        )
    ]

    chunks = build_chunks(records)

    assert chunks[0].metadata["date"] == 46143