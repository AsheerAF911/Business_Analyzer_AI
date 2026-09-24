from app.business_context import (
    BusinessContextProfile,
    BusinessContextScope,
    ConfirmationStatus,
    FieldMapping,
    ProfileStatus,
)
from app.normalization import NormalizationService
from app.report_understanding import CanonicalConcept, ReportProfile


class FakeParsedRecord:
    source_file = "Inventory_transactions.xlsx"
    sheet = "Sheet1"
    row_number = 2
    fields = {
        "DATE": 46143,
        "VENDOR NAME": "D1",
        "PRODUCTION": "D17",
        "INWARD NO": "D1IN0818",
        "PRODUCT DESCRIPTION": "RM_CHILLI POWDER",
        "TOTAL QUANTITY RECEIVED (KG)": 160,
        "INV/DO": "TRN",
        "INVOICE": "DD09883",
    }


def mapping(source, meaning, role, transformation="NONE"):
    return FieldMapping(
        source_field=source,
        business_meaning=meaning,
        canonical_role=role,
        confirmation_status=ConfirmationStatus.CONFIRMED,
        transformation=transformation,
    )


def test_current_inventory_example_normalizes_from_profile_not_source_alias_rules():
    profile = BusinessContextProfile(
        profile_id="inventory-example",
        scope=BusinessContextScope(
            company_context="example-company",
            report_type="Inventory",
            source_format_id="inventory-format-a",
        ),
        report_profile=ReportProfile(
            source_file="Inventory_transactions.xlsx",
            report_type="Inventory",
            sheets=["Sheet1"],
            record_count=1,
            column_count=8,
            columns=[],
            warnings=[],
        ),
        field_mappings=[
            mapping("DATE", "Inventory movement date", "TRANSACTION_DATE", "DATE_NORMALIZATION"),
            mapping("VENDOR NAME", "Receiving Entity", "DESTINATION_ENTITY", "TEXT_NORMALIZATION"),
            mapping("PRODUCTION", "Sending Entity", "SOURCE_ENTITY", "TEXT_NORMALIZATION"),
            mapping("INWARD NO", "Transaction reference", "EXTERNAL_REFERENCE", "TEXT_NORMALIZATION"),
            mapping("PRODUCT DESCRIPTION", "Product name", "PRODUCT_NAME", "TEXT_NORMALIZATION"),
            mapping("TOTAL QUANTITY RECEIVED (KG)", "Quantity received", "QUANTITY", "NUMBER_NORMALIZATION"),
            FieldMapping(source_field="INV/DO", confirmation_status=ConfirmationStatus.UNMAPPED),
        ],
        status=ProfileStatus.REVIEWED,
    )

    draft = NormalizationService().normalize_record(FakeParsedRecord(), profile)

    assert draft.values_for(CanonicalConcept.TRANSACTION_DATE)[0].value.isoformat() == "2026-05-01"
    assert draft.values_for(CanonicalConcept.DESTINATION_ENTITY)[0].value == "D1"
    assert draft.values_for(CanonicalConcept.SOURCE_ENTITY)[0].value == "D17"
    assert draft.values_for(CanonicalConcept.EXTERNAL_REFERENCE)[0].value == "D1IN0818"
    assert draft.values_for(CanonicalConcept.PRODUCT_NAME)[0].value == "RM_CHILLI POWDER"
    assert draft.values_for(CanonicalConcept.QUANTITY)[0].value == 160

    unmapped = {item.source_field: item.value for item in draft.unmapped_fields}
    assert unmapped["INV/DO"] == "TRN"
    assert unmapped["INVOICE"] == "DD09883"
