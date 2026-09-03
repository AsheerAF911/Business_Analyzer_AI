from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReportType(str, Enum):
    SALES = "Sales"
    PURCHASE = "Purchase"
    INVENTORY = "Inventory"
    MANUFACTURING = "Manufacturing"
    ACCOUNTING = "Accounting"
    RECEIVABLES = "Receivables"
    PAYABLES = "Payables"
    OTHER = "Other"


class ReportStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)

    file_type: Mapped[str] = mapped_column(String(100), nullable=False)

    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType),
        nullable=False,
    )

    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus),
        nullable=False,
        default=ReportStatus.UPLOADED,
    )

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )