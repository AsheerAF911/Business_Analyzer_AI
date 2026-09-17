from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    InventoryTransaction,
    Product,
    Report,
)

from .models import (
    StructuredDataFilters,
    StructuredDataResult,
)


class StructuredDataService:
    def __init__(
        self,
        db: Session,
    ):
        self.db = db

    def retrieve(
        self,
        filters: StructuredDataFilters,
    ) -> list[StructuredDataResult]:
        self._validate_filters(filters)

        statement = (
            select(
                InventoryTransaction,
                Product,
                Report,
            )
            .join(
                Product,
                InventoryTransaction.product_id
                == Product.id,
            )
            .join(
                Report,
                InventoryTransaction.report_id
                == Report.id,
            )
        )

        if filters.start_date is not None:
            statement = statement.where(
                InventoryTransaction.transaction_date
                >= filters.start_date
            )

        if filters.end_date is not None:
            statement = statement.where(
                InventoryTransaction.transaction_date
                <= filters.end_date
            )

        if filters.product:
            statement = statement.where(
                Product.name == filters.product
            )

        if filters.report_type is not None:
            statement = statement.where(
                Report.report_type
                == filters.report_type
            )

        statement = statement.order_by(
            InventoryTransaction.id
        )

        rows = self.db.execute(
            statement
        ).all()

        return [
            self._to_result(
                transaction,
                product,
                report,
            )
            for transaction, product, report
            in rows
        ]

    @staticmethod
    def _validate_filters(
        filters: StructuredDataFilters,
    ) -> None:
        if (
            filters.start_date is not None
            and filters.end_date is not None
            and filters.start_date > filters.end_date
        ):
            raise ValueError(
                "start_date cannot be after end_date."
            )

        if filters.department:
            raise ValueError(
                "Department filtering is not supported "
                "by the current structured schema."
            )

    @staticmethod
    def _to_result(
        transaction: InventoryTransaction,
        product: Product,
        report: Report,
    ) -> StructuredDataResult:
        return StructuredDataResult(
            record_id=transaction.id,
            record_type="inventory_transaction",
            company_id=transaction.company_id,
            report_id=report.id,
            source_file=report.original_filename,
            report_type=report.report_type.value,
            date=transaction.transaction_date,
            department=None,
            product_id=product.id,
            product=product.name,
            quantity=transaction.quantity,
            amount=None,
        )