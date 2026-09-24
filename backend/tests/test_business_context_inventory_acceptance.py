from __future__ import annotations

from app.business_context import (
    BusinessContextScope,
    BusinessContextService,
    ConfirmationStatus,
)
from app.report_understanding import ReportProfiler


class FakeParsedRecord:
    def __init__(self, row_number, fields):
        self.source_file = "Inventory_transactions.xlsx"
        self.sheet = "Sheet1"
        self.row_number = row_number
        self.fields = fields


def test_current_inventory_report_can_be_human_reviewed_without_canonical_persistence():
    records = [
        FakeParsedRecord(2, {
            "BARCODE": 30955,
            "PRODUCT DESCRIPTION": "RM_CHILLI POWDER OMEGA_5390380630955",
            "VENDOR NAME": "D1",
            "PRODUCTION": "D17",
            "INWARD NO": "D1IN0818",
            "DATE": 46143,
            "TOTAL QUANTITY RECEIVED (KG)": 10170,
            "INV/DO": "INV",
        })
    ]

    report_profile = ReportProfiler().profile(records, report_type="Inventory")
    service = BusinessContextService()
    profile = service.create_from_report_profile(
        profile_id="inventory-format-example",
        report_profile=report_profile,
        scope=BusinessContextScope(
            company_context="example-company-context",
            report_type="Inventory",
            source_format_id="inventory-format-a",
        ),
    )

    decisions = {
        "BARCODE": ("Product identifier", "PRODUCT_IDENTIFIER"),
        "PRODUCT DESCRIPTION": ("Product name", "PRODUCT_NAME"),
        "VENDOR NAME": ("Receiving entity", "DESTINATION_ENTITY"),
        "PRODUCTION": ("Sending entity", "SOURCE_ENTITY"),
        "INWARD NO": ("Transaction reference", "EXTERNAL_REFERENCE"),
        "DATE": ("Inventory movement date", "TRANSACTION_DATE"),
        "TOTAL QUANTITY RECEIVED (KG)": ("Quantity received", "QUANTITY"),
    }

    for source_field, (meaning, role) in decisions.items():
        service.confirm_field(
            profile,
            source_field=source_field,
            business_meaning=meaning,
            canonical_role=role,
        )

    service.mark_unmapped(
        profile,
        source_field="INV/DO",
        implementor_note="Exact meaning not established yet.",
    )

    for source_field, (_, role) in decisions.items():
        mapping = profile.get_mapping(source_field)
        assert mapping.confirmation_status == ConfirmationStatus.CONFIRMED
        assert mapping.canonical_role == role

    assert profile.get_mapping("INV/DO").confirmation_status == ConfirmationStatus.UNMAPPED
    assert profile.report_profile.source_file == "Inventory_transactions.xlsx"
