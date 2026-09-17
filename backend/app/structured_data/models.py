from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models import ReportType


@dataclass(frozen=True)
class StructuredDataFilters:
    start_date: date | None = None
    end_date: date | None = None
    department: str | None = None
    product: str | None = None
    report_type: ReportType | None = None


@dataclass(frozen=True)
class StructuredDataResult:
    record_id: int
    record_type: str

    company_id: int | None
    report_id: int

    source_file: str
    report_type: str

    date: date | None
    department: str | None

    product_id: int | None
    product: str | None

    quantity: Decimal | None
    amount: Decimal | None