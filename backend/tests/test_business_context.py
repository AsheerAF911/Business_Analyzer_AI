from __future__ import annotations

from pathlib import Path

from app.business_context import (
    BusinessContextScope,
    BusinessContextService,
    ConfirmationStatus,
    JsonBusinessContextProfileStore,
)
from app.report_understanding import (
    AmbiguityStatus,
    CanonicalConcept,
    ColumnProfile,
    InferredDataType,
    ReportProfile,
)


def column(name, *, meanings=None, concepts=None, ambiguity=AmbiguityStatus.UNKNOWN):
    return ColumnProfile(
        source_column_name=name,
        inferred_data_type=InferredDataType.STRING,
        example_values=["example"],
        null_count=0,
        total_count=1,
        null_percentage=0.0,
        unique_value_count=1,
        possible_semantic_meanings=list(meanings or []),
        possible_canonical_concepts=list(concepts or [CanonicalConcept.UNKNOWN]),
        ambiguity_status=ambiguity,
        profiling_notes="Part 1 observation",
    )


def report_profile():
    return ReportProfile(
        source_file="Inventory_transactions.xlsx",
        report_type="Inventory",
        sheets=["Sheet1"],
        record_count=13,
        column_count=3,
        columns=[
            column("BARCODE", meanings=["product identifier"], concepts=[CanonicalConcept.PRODUCT_IDENTIFIER], ambiguity=AmbiguityStatus.CLEAR),
            column("VENDOR NAME", meanings=["supplier", "receiving entity"], concepts=[CanonicalConcept.SUPPLIER, CanonicalConcept.DESTINATION_ENTITY], ambiguity=AmbiguityStatus.AMBIGUOUS),
            column("INV/DO", meanings=["document type"], concepts=[CanonicalConcept.DOCUMENT_TYPE], ambiguity=AmbiguityStatus.AMBIGUOUS),
        ],
        warnings=["2 column(s) require semantic review."],
    )


def make_profile(company="company-a"):
    return BusinessContextService().create_from_report_profile(
        profile_id=f"inventory-{company}",
        report_profile=report_profile(),
        scope=BusinessContextScope(
            company_context=company,
            report_type="Inventory",
            source_format_id="inventory-format-a",
        ),
    )


def test_create_profile_from_report_profile():
    profile = make_profile()
    assert profile.report_profile.source_file == "Inventory_transactions.xlsx"
    assert [m.source_field for m in profile.field_mappings] == ["BARCODE", "VENDOR NAME", "INV/DO"]


def test_field_starts_pending_review():
    profile = make_profile()
    assert profile.get_mapping("VENDOR NAME").confirmation_status == ConfirmationStatus.PENDING_REVIEW


def test_implementor_can_confirm_mapping():
    profile = make_profile()
    mapping = BusinessContextService().confirm_field(
        profile,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
    )
    assert mapping.confirmation_status == ConfirmationStatus.CONFIRMED
    assert mapping.business_meaning == "Receiving Entity"
    assert mapping.canonical_role == "DESTINATION_ENTITY"


def test_implementor_can_reject_field():
    profile = make_profile()
    mapping = BusinessContextService().reject_field(profile, source_field="INV/DO")
    assert mapping.confirmation_status == ConfirmationStatus.REJECTED
    assert mapping.canonical_role is None


def test_implementor_can_mark_unmapped():
    profile = make_profile()
    mapping = BusinessContextService().mark_unmapped(profile, source_field="INV/DO")
    assert mapping.confirmation_status == ConfirmationStatus.UNMAPPED
    assert mapping.business_meaning is None


def test_implementor_note_is_preserved():
    profile = make_profile()
    mapping = BusinessContextService().confirm_field(
        profile,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
        implementor_note="This company uses this field for the receiving entity.",
    )
    assert mapping.implementor_note == "This company uses this field for the receiving entity."


def test_source_field_name_is_preserved_exactly():
    profile = make_profile()
    BusinessContextService().confirm_field(
        profile,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
    )
    assert profile.get_mapping("VENDOR NAME").source_field == "VENDOR NAME"


def test_part1_suggestions_remain_available_after_confirmation():
    profile = make_profile()
    before = profile.report_profile.to_dict()
    BusinessContextService().confirm_field(
        profile,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
    )
    after = profile.report_profile.to_dict()
    assert before == after
    source_profile = next(c for c in profile.report_profile.columns if c.source_column_name == "VENDOR NAME")
    assert "supplier" in source_profile.possible_semantic_meanings


def test_same_source_field_can_differ_by_company_context():
    service = BusinessContextService()
    company_a = make_profile("company-a")
    company_b = make_profile("company-b")

    service.confirm_field(
        company_a,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
    )
    service.confirm_field(
        company_b,
        source_field="VENDOR NAME",
        business_meaning="Supplier",
        canonical_role="SUPPLIER",
    )

    assert company_a.scope.company_context != company_b.scope.company_context
    assert company_a.get_mapping("VENDOR NAME").canonical_role == "DESTINATION_ENTITY"
    assert company_b.get_mapping("VENDOR NAME").canonical_role == "SUPPLIER"


def test_json_store_round_trip_preserves_profile_and_part1_snapshot(tmp_path: Path):
    profile = make_profile()
    BusinessContextService().confirm_field(
        profile,
        source_field="VENDOR NAME",
        business_meaning="Receiving Entity",
        canonical_role="DESTINATION_ENTITY",
        implementor_note="Reviewed with implementor",
    )

    store = JsonBusinessContextProfileStore(tmp_path)
    store.save(profile)
    loaded = store.get(profile.profile_id)

    assert loaded.to_dict() == profile.to_dict()


def test_profile_store_is_configuration_not_business_database(tmp_path: Path):
    profile = make_profile()
    store = JsonBusinessContextProfileStore(tmp_path)
    store.save(profile)
    assert list(tmp_path.glob("*.json"))
