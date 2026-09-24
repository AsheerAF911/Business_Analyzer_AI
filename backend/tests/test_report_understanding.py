from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.report_understanding import (
    AmbiguityStatus,
    CanonicalConcept,
    ColumnProfiler,
    InferredDataType,
    ReportProfiler,
)


@dataclass
class FakeParsedRecord:
    source_file: str
    sheet: str
    row_number: int
    fields: dict


def test_string_column_profiling():
    profile = ColumnProfiler().profile("SKU", ["A-1", "B-2", "A-1"])
    assert profile.inferred_data_type == InferredDataType.STRING
    assert profile.unique_value_count == 2
    assert profile.example_values == ["A-1", "B-2"]


def test_numeric_column_profiling():
    profile = ColumnProfiler().profile("Quantity", [1, 2, Decimal("3.5")])
    assert profile.inferred_data_type == InferredDataType.DECIMAL


def test_date_like_excel_serial_profiling():
    profile = ColumnProfiler().profile("DATE", [46143, 46143])
    assert profile.inferred_data_type == InferredDataType.DATE_LIKE
    assert profile.example_values == [46143]
    assert "Excel date serials" in profile.profiling_notes


def test_null_and_empty_calculation():
    profile = ColumnProfiler().profile("Other", [None, "", "   ", "x"])
    assert profile.total_count == 4
    assert profile.null_count == 3
    assert profile.null_percentage == 75.0
    assert profile.unique_value_count == 1


def test_example_value_extraction_is_bounded_and_distinct():
    profile = ColumnProfiler(example_limit=3).profile(
        "SKU",
        ["A", "A", "B", "C", "D"],
    )
    assert profile.example_values == ["A", "B", "C"]
    assert profile.unique_value_count == 4


def test_report_output_is_deterministic_with_fixed_timestamp():
    records = [
        FakeParsedRecord("x.xlsx", "Sheet1", 2, {"SKU": "A", "Quantity": 1}),
        FakeParsedRecord("x.xlsx", "Sheet1", 3, {"SKU": "B", "Quantity": 2}),
    ]
    fixed = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    profiler = ReportProfiler()
    first = profiler.profile(records, report_type="Inventory", profiled_at=fixed).to_dict()
    second = profiler.profile(records, report_type="Inventory", profiled_at=fixed).to_dict()
    assert first == second


def test_vendor_name_remains_ambiguous():
    profile = ColumnProfiler().profile("VENDOR NAME", ["D1", "D2", "TEAM 2"])
    assert profile.ambiguity_status == AmbiguityStatus.AMBIGUOUS
    assert CanonicalConcept.SUPPLIER in profile.possible_canonical_concepts
    assert len(profile.possible_canonical_concepts) > 1


def test_clear_semantic_suggestion_does_not_mean_approval():
    profile = ColumnProfiler().profile("SKU", ["A", "B"])
    assert profile.ambiguity_status == AmbiguityStatus.CLEAR
    assert profile.possible_canonical_concepts == [CanonicalConcept.PRODUCT_IDENTIFIER]
    assert "not approval" in profile.profiling_notes


def test_unknown_unrecognized_column():
    profile = ColumnProfiler().profile("MYSTERY FLAG", ["X", "Y"])
    assert profile.ambiguity_status == AmbiguityStatus.UNKNOWN
    assert profile.possible_canonical_concepts == [CanonicalConcept.UNKNOWN]


def test_production_never_becomes_confirmed_business_meaning():
    profile = ColumnProfiler().profile("PRODUCTION", ["D17", "TEAM 2"])
    assert profile.ambiguity_status == AmbiguityStatus.AMBIGUOUS
    assert CanonicalConcept.UNKNOWN in profile.possible_canonical_concepts


def test_report_profile_contains_every_source_column_and_missing_fields_count_as_null():
    records = [
        FakeParsedRecord("x.xlsx", "Sheet1", 2, {"SKU": "A", "Quantity": 1}),
        FakeParsedRecord("x.xlsx", "Sheet2", 3, {"SKU": "B", "Vendor": "D1"}),
    ]
    profile = ReportProfiler().profile(records, report_type="Inventory")
    assert profile.source_file == "x.xlsx"
    assert profile.report_type == "Inventory"
    assert profile.sheets == ["Sheet1", "Sheet2"]
    assert profile.record_count == 2
    assert profile.column_count == 3
    by_name = {column.source_column_name: column for column in profile.columns}
    assert by_name["Quantity"].null_count == 1
    assert by_name["Vendor"].null_count == 1


def test_does_not_treat_na_or_dash_as_null():
    profile = ColumnProfiler().profile("Other", ["N/A", "-", None])
    assert profile.null_count == 1
    assert profile.unique_value_count == 2


def test_empty_column():
    profile = ColumnProfiler().profile("Other", [None, "", "  "])
    assert profile.inferred_data_type == InferredDataType.EMPTY
    assert profile.null_percentage == 100.0
