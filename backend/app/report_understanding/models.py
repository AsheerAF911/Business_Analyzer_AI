from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class InferredDataType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE_LIKE = "date-like"
    BOOLEAN_LIKE = "boolean-like"
    EMPTY = "empty"
    MIXED = "mixed-type"


class AmbiguityStatus(str, Enum):
    CLEAR = "CLEAR"
    AMBIGUOUS = "AMBIGUOUS"
    UNKNOWN = "UNKNOWN"


class CanonicalConcept(str, Enum):
    PRODUCT_IDENTIFIER = "PRODUCT_IDENTIFIER"
    PRODUCT_NAME = "PRODUCT_NAME"
    TRANSACTION_DATE = "TRANSACTION_DATE"
    QUANTITY = "QUANTITY"
    UNIT_OF_MEASURE = "UNIT_OF_MEASURE"
    SUPPLIER = "SUPPLIER"
    CUSTOMER = "CUSTOMER"
    SOURCE_ENTITY = "SOURCE_ENTITY"
    DESTINATION_ENTITY = "DESTINATION_ENTITY"
    BUSINESS_REFERENCE = "BUSINESS_REFERENCE"
    DOCUMENT_TYPE = "DOCUMENT_TYPE"
    LOCATION = "LOCATION"
    DEPARTMENT = "DEPARTMENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ColumnProfile:
    source_column_name: str
    inferred_data_type: InferredDataType
    example_values: list[Any]
    null_count: int
    total_count: int
    null_percentage: float
    unique_value_count: int
    possible_semantic_meanings: list[str]
    possible_canonical_concepts: list[CanonicalConcept]
    ambiguity_status: AmbiguityStatus
    profiling_notes: str

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["inferred_data_type"] = self.inferred_data_type.value
        value["possible_canonical_concepts"] = [
            concept.value for concept in self.possible_canonical_concepts
        ]
        value["ambiguity_status"] = self.ambiguity_status.value
        return value


@dataclass(frozen=True)
class ReportProfile:
    source_file: str
    report_type: str | None
    sheets: list[str]
    record_count: int
    column_count: int
    columns: list[ColumnProfile]
    warnings: list[str]
    profiled_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "report_type": self.report_type,
            "sheets": list(self.sheets),
            "record_count": self.record_count,
            "column_count": self.column_count,
            "profiled_at": self.profiled_at.isoformat() if self.profiled_at else None,
            "columns": [column.to_dict() for column in self.columns],
            "warnings": list(self.warnings),
        }
