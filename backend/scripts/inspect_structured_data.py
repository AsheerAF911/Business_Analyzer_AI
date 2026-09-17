from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import (
    Company,
    Customer,
    Expense,
    InventoryTransaction,
    Payable,
    ProcessingJob,
    Production,
    ProductionItem,
    Product,
    Purchase,
    PurchaseItem,
    Receivable,
    Report,
    Sale,
    SaleItem,
    Supplier,
)


TABLES = [
    ("companies", Company),
    ("customers", Customer),
    ("expenses", Expense),
    (
        "inventory_transactions",
        InventoryTransaction,
    ),
    ("payables", Payable),
    ("processing_jobs", ProcessingJob),
    ("production_items", ProductionItem),
    ("productions", Production),
    ("products", Product),
    ("purchase_items", PurchaseItem),
    ("purchases", Purchase),
    ("receivables", Receivable),
    ("reports", Report),
    ("sale_items", SaleItem),
    ("sales", Sale),
    ("suppliers", Supplier),
]


def print_sample(
    db,
    table_name,
    model,
):
    rows = (
        db.execute(
            select(model).limit(3)
        )
        .scalars()
        .all()
    )

    if not rows:
        return

    print()
    print(f"SAMPLE: {table_name}")
    print("-" * 60)

    for row in rows:
        values = {
            column.name: getattr(
                row,
                column.name,
            )
            for column
            in model.__table__.columns
        }

        print(values)


def main():
    db = SessionLocal()

    try:
        print()
        print("STRUCTURED DATABASE INSPECTION")
        print("=" * 60)

        populated_tables = []

        for table_name, model in TABLES:
            count = db.scalar(
                select(func.count())
                .select_from(model)
            )

            print(
                f"{table_name:<25} "
                f"{count}"
            )

            if count:
                populated_tables.append(
                    (table_name, model)
                )

        print()
        print("POPULATED TABLE SAMPLES")
        print("=" * 60)

        for table_name, model in populated_tables:
            print_sample(
                db,
                table_name,
                model,
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()