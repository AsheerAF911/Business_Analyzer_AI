from __future__ import annotations

import pytest

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
    def __init__(self, fields, *, company="x", row_number=2):
        self.source_file = f"{company}.xlsx"
        self.sheet = "Sheet1"
        self.row_number = row_number
        self.fields = fields


def profile(*mappings, company="company-a"):
    return BusinessContextProfile(
        profile_id=f"{company}-profile",
        scope=BusinessContextScope(
            company_context=company,
            report_type="Inventory",
            source_format_id="format-1",
        ),
        report_profile=ReportProfile(
            source_file=f"{company}.xlsx",
            report_type="Inventory",
            sheets=["Sheet1"],
            record_count=1,
            column_count=len(mappings),
            columns=[],
            warnings=[],
        ),
        field_mappings=list(mappings),
        status=ProfileStatus.REVIEWED,
    )


def confirmed(source, meaning, concept, transformation="NONE"):
    return FieldMapping(
        source_field=source,
        business_meaning=meaning,
        canonical_role=concept,
        confirmation_status=ConfirmationStatus.CONFIRMED,
        transformation=transformation,
    )


def test_confirmed_profile_drives_normalization():
    record = FakeParsedRecord({"DATE": 46143, "NAME": "  Widget  "})
    ctx = profile(
        confirmed("DATE", "Movement date", "TRANSACTION_DATE", "DATE_NORMALIZATION"),
        confirmed("NAME", "Product name", "PRODUCT_NAME", "TEXT_NORMALIZATION"),
    )

    draft = NormalizationService().normalize_record(record, ctx)

    assert draft.values_for(CanonicalConcept.TRANSACTION_DATE)[0].value.isoformat() == "2026-05-01"
    assert draft.values_for(CanonicalConcept.PRODUCT_NAME)[0].value == "Widget"


def test_same_source_field_maps_differently_by_company_profile():
    service = NormalizationService()
    record_a = FakeParsedRecord({"VENDOR": "D1"}, company="a")
    record_b = FakeParsedRecord({"VENDOR": "ABC Supplies"}, company="b")
    company_a = profile(
        confirmed("VENDOR", "Receiving Entity", "DESTINATION_ENTITY", "TEXT_NORMALIZATION"),
        company="company-a",
    )
    company_b = profile(
        confirmed("VENDOR", "Supplier", "SUPPLIER", "TEXT_NORMALIZATION"),
        company="company-b",
    )

    draft_a = service.normalize_record(record_a, company_a)
    draft_b = service.normalize_record(record_b, company_b)

    assert draft_a.values_for(CanonicalConcept.DESTINATION_ENTITY)[0].value == "D1"
    assert not draft_a.values_for(CanonicalConcept.SUPPLIER)
    assert draft_b.values_for(CanonicalConcept.SUPPLIER)[0].value == "ABC Supplies"
    assert not draft_b.values_for(CanonicalConcept.DESTINATION_ENTITY)


@pytest.mark.parametrize("source_field", ["BARCODE", "SKU", "ITEM CODE", "MATERIAL CODE", "PRODUCT CODE"])
def test_different_source_fields_can_map_to_product_identifier(source_field):
    record = FakeParsedRecord({source_field: "ABC-001"})
    ctx = profile(confirmed(source_field, "Product identifier", "PRODUCT_IDENTIFIER"))
    draft = NormalizationService().normalize_record(record, ctx)
    assert draft.values_for(CanonicalConcept.PRODUCT_IDENTIFIER)[0].value == "ABC-001"


def test_unconfirmed_and_missing_mapping_fields_are_preserved_unmapped():
    record = FakeParsedRecord({"PARTY": "D1", "UNKNOWN FIELD": "raw"})
    pending = FieldMapping(
        source_field="PARTY",
        business_meaning=None,
        canonical_role=None,
        confirmation_status=ConfirmationStatus.PENDING_REVIEW,
    )
    draft = NormalizationService().normalize_record(record, profile(pending))

    assert {(item.source_field, item.value) for item in draft.unmapped_fields} == {
        ("PARTY", "D1"),
        ("UNKNOWN FIELD", "raw"),
    }
    assert all(item.provenance.row_number == 2 for item in draft.unmapped_fields)


def test_transformation_failure_is_visible_and_raw_value_is_preserved():
    record = FakeParsedRecord({"QTY": "many"})
    ctx = profile(confirmed("QTY", "Quantity", "QUANTITY", "NUMBER_NORMALIZATION"))
    draft = NormalizationService().normalize_record(record, ctx)

    assert draft.values_for(CanonicalConcept.QUANTITY) == []
    assert draft.unmapped_fields[0].value == "many"
    assert draft.unmapped_fields[0].reason == "TRANSFORMATION_FAILED"
    assert any(w.code == "TRANSFORMATION_FAILED" for w in draft.transformation_warnings)


def test_duplicate_canonical_concepts_do_not_overwrite():
    record = FakeParsedRecord({"SOURCE_A": "10", "SOURCE_B": "20"})
    ctx = profile(
        confirmed("SOURCE_A", "Quantity A", "QUANTITY", "NUMBER_NORMALIZATION"),
        confirmed("SOURCE_B", "Quantity B", "QUANTITY", "NUMBER_NORMALIZATION"),
    )
    draft = NormalizationService().normalize_record(record, ctx)

    values = draft.values_for(CanonicalConcept.QUANTITY)
    assert [item.value for item in values] == [10, 20]
    assert [item.source_field for item in values] == ["SOURCE_A", "SOURCE_B"]
    assert any(w.code == "DUPLICATE_CANONICAL_CONCEPT" for w in draft.transformation_warnings)


def test_provenance_is_preserved_per_canonical_value():
    record = FakeParsedRecord({"SKU": "P-1"}, row_number=9)
    ctx = profile(confirmed("SKU", "Product identifier", "PRODUCT_IDENTIFIER"))
    draft = NormalizationService().normalize_record(record, ctx)

    value = draft.values_for(CanonicalConcept.PRODUCT_IDENTIFIER)[0]
    assert value.provenance.source_file == "x.xlsx"
    assert value.provenance.sheet == "Sheet1"
    assert value.provenance.row_number == 9
    assert value.provenance.source_field == "SKU"
    assert draft.source_record_reference == "x.xlsx:Sheet1:9"


def test_confirmed_mapping_missing_from_row_produces_warning():
    record = FakeParsedRecord({"SKU": "P-1"})
    ctx = profile(
        confirmed("SKU", "Product identifier", "PRODUCT_IDENTIFIER"),
        confirmed("DATE", "Movement date", "TRANSACTION_DATE", "DATE_NORMALIZATION"),
    )
    draft = NormalizationService().normalize_record(record, ctx)
    assert any(
        w.code == "MISSING_MAPPING_INPUT" and w.source_field == "DATE"
        for w in draft.transformation_warnings
    )
