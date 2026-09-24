from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from app.ingestion.parsers.excel import ExcelParser
from app.report_understanding import AmbiguityStatus, InferredDataType, ReportProfiler


def test_existing_excel_parser_output_can_be_profiled(tmp_path: Path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Sheet1"
    sheet.append(["DATE", "VENDOR NAME", "PRODUCTION", "SKU", "Quantity"])
    sheet.append([46143, "D1", "D17", "SKU-1", 10])
    sheet.append([46143, "TEAM 2", "TEAM 2", "SKU-2", 20])

    path = tmp_path / "inventory-like.xlsx"
    workbook.save(path)

    records = ExcelParser().parse(path, source_file=path.name)
    profile = ReportProfiler().profile(records, report_type="Inventory")
    by_name = {column.source_column_name: column for column in profile.columns}

    assert profile.record_count == 2
    assert by_name["DATE"].inferred_data_type == InferredDataType.DATE_LIKE
    assert by_name["VENDOR NAME"].ambiguity_status == AmbiguityStatus.AMBIGUOUS
    assert by_name["PRODUCTION"].ambiguity_status == AmbiguityStatus.AMBIGUOUS
