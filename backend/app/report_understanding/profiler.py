from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Protocol

from .models import ColumnProfile, InferredDataType, ReportProfile
from .semantic_rules import suggest_semantics


class ParsedRecordLike(Protocol):
    source_file: str
    sheet: str
    row_number: int
    fields: dict[str, Any]


def _is_null(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _is_iso_date_string(value: str) -> bool:
    text = value.strip()
    if not text:
        return False

    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        return True
    except ValueError:
        pass

    try:
        date.fromisoformat(text)
        return True
    except ValueError:
        return False


def _is_boolean_string(value: str) -> bool:
    return value.strip().lower() in {"true", "false", "yes", "no"}


def _is_plausible_excel_date_serial(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return False

    numeric = float(value)
    # Broad, deterministic guardrail for typical modern business workbooks.
    # Roughly covers 1954-2119 in Excel's 1900 date system.
    return 20000 <= numeric <= 80000


def _header_suggests_date(column_name: str) -> bool:
    label = " ".join(column_name.lower().replace("_", " ").split())
    return "date" in label or label in {"posting", "posted on"}


def _value_type(value: Any) -> InferredDataType:
    if isinstance(value, bool):
        return InferredDataType.BOOLEAN_LIKE
    if isinstance(value, (datetime, date)):
        return InferredDataType.DATE_LIKE
    if isinstance(value, int):
        return InferredDataType.INTEGER
    if isinstance(value, (float, Decimal)):
        return InferredDataType.DECIMAL
    if isinstance(value, str):
        if _is_iso_date_string(value):
            return InferredDataType.DATE_LIKE
        if _is_boolean_string(value):
            return InferredDataType.BOOLEAN_LIKE
        return InferredDataType.STRING
    return InferredDataType.STRING


def _infer_type(column_name: str, non_null_values: list[Any]) -> InferredDataType:
    if not non_null_values:
        return InferredDataType.EMPTY

    if _header_suggests_date(column_name) and all(
        _is_plausible_excel_date_serial(value) for value in non_null_values
    ):
        return InferredDataType.DATE_LIKE

    types = {_value_type(value) for value in non_null_values}

    if len(types) == 1:
        return next(iter(types))

    if types <= {InferredDataType.INTEGER, InferredDataType.DECIMAL}:
        return InferredDataType.DECIMAL

    return InferredDataType.MIXED


def _stable_distinct(values: Iterable[Any]) -> list[Any]:
    seen: set[tuple[str, str]] = set()
    result: list[Any] = []

    for value in values:
        key = (type(value).__name__, repr(value))
        if key in seen:
            continue
        seen.add(key)
        result.append(value)

    return result


class ColumnProfiler:
    def __init__(self, *, example_limit: int = 5):
        if example_limit < 1:
            raise ValueError("example_limit must be at least 1")
        self.example_limit = example_limit

    def profile(self, column_name: str, values: list[Any]) -> ColumnProfile:
        total_count = len(values)
        null_count = sum(1 for value in values if _is_null(value))
        non_null_values = [value for value in values if not _is_null(value)]
        distinct_values = _stable_distinct(non_null_values)
        inferred_type = _infer_type(column_name, non_null_values)
        suggestion = suggest_semantics(column_name, inferred_type)

        notes = suggestion.notes
        if inferred_type == InferredDataType.DATE_LIKE and any(
            _is_plausible_excel_date_serial(value) for value in non_null_values
        ):
            notes += (
                " Numeric values are also consistent with plausible Excel date serials; "
                "the profiler does not mutate or normalize the source values."
            )

        null_percentage = (
            round((null_count / total_count) * 100, 2)
            if total_count
            else 0.0
        )

        return ColumnProfile(
            source_column_name=column_name,
            inferred_data_type=inferred_type,
            example_values=distinct_values[: self.example_limit],
            null_count=null_count,
            total_count=total_count,
            null_percentage=null_percentage,
            unique_value_count=len(distinct_values),
            possible_semantic_meanings=list(suggestion.meanings),
            possible_canonical_concepts=list(suggestion.concepts),
            ambiguity_status=suggestion.status,
            profiling_notes=notes,
        )


class ReportProfiler:
    def __init__(self, *, column_profiler: ColumnProfiler | None = None):
        self.column_profiler = column_profiler or ColumnProfiler()

    def profile(
        self,
        records: list[ParsedRecordLike],
        *,
        report_type: str | None = None,
        profiled_at: datetime | None = None,
    ) -> ReportProfile:
        if not records:
            return ReportProfile(
                source_file="",
                report_type=report_type,
                sheets=[],
                record_count=0,
                column_count=0,
                columns=[],
                warnings=["No parsed records were available for profiling."],
                profiled_at=profiled_at,
            )

        source_files = _stable_distinct(record.source_file for record in records)
        sheets = _stable_distinct(record.sheet for record in records)

        ordered_columns: list[str] = []
        seen_columns: set[str] = set()
        for record in records:
            for column_name in record.fields:
                if column_name not in seen_columns:
                    seen_columns.add(column_name)
                    ordered_columns.append(column_name)

        column_profiles: list[ColumnProfile] = []
        for column_name in ordered_columns:
            values = [record.fields.get(column_name) for record in records]
            column_profiles.append(self.column_profiler.profile(column_name, values))

        warnings: list[str] = []
        if len(source_files) > 1:
            warnings.append(
                "Parsed records contain multiple source_file values; the profile uses the first source file name."
            )

        ambiguous_count = sum(
            column.ambiguity_status.value == "AMBIGUOUS" for column in column_profiles
        )
        unknown_count = sum(
            column.ambiguity_status.value == "UNKNOWN" for column in column_profiles
        )
        if ambiguous_count:
            warnings.append(f"{ambiguous_count} column(s) require semantic review.")
        if unknown_count:
            warnings.append(f"{unknown_count} column(s) have no reliable semantic suggestion.")

        return ReportProfile(
            source_file=str(source_files[0]),
            report_type=report_type,
            sheets=[str(sheet) for sheet in sheets],
            record_count=len(records),
            column_count=len(ordered_columns),
            columns=column_profiles,
            warnings=warnings,
            profiled_at=profiled_at,
        )
