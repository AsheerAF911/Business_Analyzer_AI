from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (
    Base,
    Company,
    InventoryTransaction,
    InventoryTransactionType,
    Product,
    Report,
    ReportStatus,
    ReportType,
)
from app.structured_data import (
    StructuredDataFilters,
    StructuredDataService,
)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    TestSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestSession()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def structured_data(db):
    company = Company(
        name="Test Company",
    )

    db.add(company)
    db.flush()

    product_a = Product(
        company_id=company.id,
        sku="PROD-A",
        name="Product A",
        category="Test",
        unit="kg",
    )

    product_b = Product(
        company_id=company.id,
        sku="PROD-B",
        name="Product B",
        category="Test",
        unit="kg",
    )

    db.add_all([
        product_a,
        product_b,
    ])
    db.flush()

    report = Report(
        original_filename="test_inventory.xlsx",
        stored_filename="test_inventory_stored.xlsx",
        file_type="XLSX",
        report_type=ReportType.INVENTORY,
        status=ReportStatus.PROCESSED,
    )

    db.add(report)
    db.flush()

    transactions = [
        InventoryTransaction(
            company_id=company.id,
            report_id=report.id,
            product_id=product_a.id,
            transaction_date=date(
                2026, 1, 15
            ),
            transaction_type=(
                InventoryTransactionType.RECEIPT
            ),
            quantity=Decimal("100"),
        ),
        InventoryTransaction(
            company_id=company.id,
            report_id=report.id,
            product_id=product_b.id,
            transaction_date=date(
                2026, 2, 10
            ),
            transaction_type=(
                InventoryTransactionType.RECEIPT
            ),
            quantity=Decimal("200"),
        ),
        InventoryTransaction(
            company_id=company.id,
            report_id=report.id,
            product_id=product_a.id,
            transaction_date=date(
                2026, 3, 5
            ),
            transaction_type=(
                InventoryTransactionType.RECEIPT
            ),
            quantity=Decimal("50"),
        ),
        InventoryTransaction(
            company_id=company.id,
            report_id=report.id,
            product_id=product_a.id,
            transaction_date=date(
                2026, 5, 1
            ),
            transaction_type=(
                InventoryTransactionType.RECEIPT
            ),
            quantity=Decimal("75"),
        ),
    ]

    db.add_all(transactions)
    db.commit()


    return {
    "company": company,
    "product_a": product_a,
    "product_b": product_b,
    "report": report,
}

def test_no_filters_returns_all_records(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters()
    )

    assert len(results) == 4


def test_date_only_filter(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        )
    )

    assert len(results) == 3


def test_product_only_filter(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            product="Product B",
        )
    )

    assert len(results) == 1
    assert results[0].product == "Product B"


def test_date_and_product_filter(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
            product="Product A",
        )
    )

    assert len(results) == 2

    assert all(
        result.product == "Product A"
        for result in results
    )


def test_report_type_filter(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            report_type=ReportType.INVENTORY,
        )
    )

    assert len(results) == 4


def test_no_matching_records(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            product="Does Not Exist",
        )
    )

    assert results == []


def test_invalid_date_range(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    with pytest.raises(
        ValueError,
        match=(
            "start_date cannot be after end_date"
        ),
    ):
        service.retrieve(
            StructuredDataFilters(
                start_date=date(
                    2026, 4, 1
                ),
                end_date=date(
                    2026, 1, 1
                ),
            )
        )


def test_department_is_explicitly_unsupported(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    with pytest.raises(
        ValueError,
        match="Department filtering is not supported",
    ):
        service.retrieve(
            StructuredDataFilters(
                department="Manufacturing",
            )
        )


def test_result_preserves_report_traceability(
    db,
    structured_data,
):
    service = StructuredDataService(db)

    results = service.retrieve(
        StructuredDataFilters(
            product="Product B",
        )
    )

    assert len(results) == 1

    result = results[0]

    assert result.report_id == (
        structured_data["report"].id
    )

    assert (
        result.source_file
        == "test_inventory.xlsx"
    )

    assert (
        result.report_type
        == "Inventory"
    )

    assert result.company_id == (
        structured_data["company"].id
    )