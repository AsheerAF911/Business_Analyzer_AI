from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import engine
from app.models import Base, Company, Customer, Product, Supplier


EXPECTED_TABLES = {
    "reports",
    "companies",
    "products",
    "customers",
    "suppliers",
    "sales",
    "sale_items",
    "purchases",
    "purchase_items",
    "inventory_transactions",
    "productions",
    "production_items",
    "expenses",
    "receivables",
    "payables",
}


def main() -> None:
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    missing_tables = EXPECTED_TABLES - actual_tables

    if missing_tables:
        raise RuntimeError(f"Missing tables: {sorted(missing_tables)}")

    with Session(engine) as db:
        company = Company(name="Schema Verification Company")
        db.add(company)
        db.flush()

        product = Product(
            company_id=company.id,
            sku="VERIFY-001",
            name="Schema Verification Product",
        )
        customer = Customer(
            company_id=company.id,
            name="Schema Verification Customer",
        )
        supplier = Supplier(
            company_id=company.id,
            name="Schema Verification Supplier",
        )
        db.add_all([product, customer, supplier])
        db.flush()

        assert product.company is company
        assert customer.company is company
        assert supplier.company is company

        db.rollback()

    print(f"Schema verification passed: {len(EXPECTED_TABLES)} expected tables exist.")
    print("Basic Company -> Product/Customer/Supplier relationships are valid.")


if __name__ == "__main__":
    main()
