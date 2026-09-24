from __future__ import annotations

from dataclasses import dataclass

from .models import AmbiguityStatus, CanonicalConcept, InferredDataType


@dataclass(frozen=True)
class SemanticSuggestion:
    meanings: list[str]
    concepts: list[CanonicalConcept]
    status: AmbiguityStatus
    notes: str


def _normalize_label(label: str) -> str:
    return " ".join(
        label.lower()
        .replace("_", " ")
        .replace("-", " ")
        .split()
    )


_CLEAR_RULES: dict[str, tuple[str, CanonicalConcept]] = {
    "sku": ("product/item identifier", CanonicalConcept.PRODUCT_IDENTIFIER),
    "barcode": ("product/item identifier", CanonicalConcept.PRODUCT_IDENTIFIER),
    "item code": ("product/item identifier", CanonicalConcept.PRODUCT_IDENTIFIER),
    "product code": ("product/item identifier", CanonicalConcept.PRODUCT_IDENTIFIER),
    "material code": ("product/item identifier", CanonicalConcept.PRODUCT_IDENTIFIER),
    "product name": ("product/item name", CanonicalConcept.PRODUCT_NAME),
    "product description": ("product/item description", CanonicalConcept.PRODUCT_NAME),
    "material description": ("product/item description", CanonicalConcept.PRODUCT_NAME),
    "transaction date": ("transaction/business event date", CanonicalConcept.TRANSACTION_DATE),
    "posting date": ("posting/business event date", CanonicalConcept.TRANSACTION_DATE),
    "receipt date": ("receipt/business event date", CanonicalConcept.TRANSACTION_DATE),
    "movement date": ("inventory movement date", CanonicalConcept.TRANSACTION_DATE),
    "uom": ("unit of measure", CanonicalConcept.UNIT_OF_MEASURE),
    "unit of measure": ("unit of measure", CanonicalConcept.UNIT_OF_MEASURE),
    "supplier": ("supplier", CanonicalConcept.SUPPLIER),
    "customer": ("customer", CanonicalConcept.CUSTOMER),
    "grn no": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "grn number": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "receipt no": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "receipt number": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "document number": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "document no": ("business/source document reference", CanonicalConcept.BUSINESS_REFERENCE),
    "document type": ("document type/category", CanonicalConcept.DOCUMENT_TYPE),
    "department": ("department or organizational unit", CanonicalConcept.DEPARTMENT),
    "warehouse": ("warehouse/location", CanonicalConcept.LOCATION),
    "location": ("location", CanonicalConcept.LOCATION),
    "facility": ("facility/location", CanonicalConcept.LOCATION),
}


def suggest_semantics(
    source_column_name: str,
    inferred_data_type: InferredDataType,
) -> SemanticSuggestion:
    label = _normalize_label(source_column_name)

    clear = _CLEAR_RULES.get(label)
    if clear:
        meaning, concept = clear
        return SemanticSuggestion(
            meanings=[meaning],
            concepts=[concept],
            status=AmbiguityStatus.CLEAR,
            notes=(
                "The source label has a relatively clear generic interpretation. "
                "CLEAR is only a profiling suggestion and is not approval for canonical persistence."
            ),
        )

    if "vendor" in label:
        return SemanticSuggestion(
            meanings=[
                "supplier",
                "receiving entity",
                "sending entity",
                "other party/entity",
            ],
            concepts=[
                CanonicalConcept.SUPPLIER,
                CanonicalConcept.SOURCE_ENTITY,
                CanonicalConcept.DESTINATION_ENTITY,
            ],
            status=AmbiguityStatus.AMBIGUOUS,
            notes=(
                "Values appear to identify entities, but the source label alone does not establish "
                "the entity's business role."
            ),
        )

    if label == "party" or label.endswith(" party"):
        return SemanticSuggestion(
            meanings=["supplier", "customer", "source entity", "destination entity", "other party"],
            concepts=[
                CanonicalConcept.SUPPLIER,
                CanonicalConcept.CUSTOMER,
                CanonicalConcept.SOURCE_ENTITY,
                CanonicalConcept.DESTINATION_ENTITY,
            ],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="Party is role-ambiguous without report-specific business context.",
        )

    if "production" in label:
        return SemanticSuggestion(
            meanings=[
                "production unit",
                "sending entity",
                "receiving entity",
                "location/facility",
                "department",
                "source-specific code",
            ],
            concepts=[
                CanonicalConcept.LOCATION,
                CanonicalConcept.DEPARTMENT,
                CanonicalConcept.SOURCE_ENTITY,
                CanonicalConcept.DESTINATION_ENTITY,
                CanonicalConcept.UNKNOWN,
            ],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="The label suggests several plausible business meanings; no final meaning is selected.",
        )

    if label in {"date", "business date"}:
        return SemanticSuggestion(
            meanings=["transaction date", "posting date", "document date", "other business date"],
            concepts=[CanonicalConcept.TRANSACTION_DATE],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="The value is date-like, but a generic DATE label does not establish which business date it represents.",
        )

    if any(token in label for token in ("qty", "quantity")):
        meanings = ["business quantity"]
        notes = "The label indicates a quantity, but unit and movement semantics may require review."
        return SemanticSuggestion(
            meanings=meanings,
            concepts=[CanonicalConcept.QUANTITY],
            status=AmbiguityStatus.CLEAR,
            notes=notes,
        )

    if label in {"description", "name"}:
        return SemanticSuggestion(
            meanings=["product/item name or description", "other descriptive field"],
            concepts=[CanonicalConcept.PRODUCT_NAME, CanonicalConcept.UNKNOWN],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="A generic description/name field requires surrounding report context.",
        )

    if any(token in label for token in ("inward no", "inward number", "reference", "ref no", "ref number")):
        return SemanticSuggestion(
            meanings=["business/source reference", "document reference", "source-system identifier"],
            concepts=[CanonicalConcept.BUSINESS_REFERENCE],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="The field looks reference-like, but its exact business role is not established by the label alone.",
        )

    if label in {"inv/do", "invoice/do", "inv do"}:
        return SemanticSuggestion(
            meanings=["document type", "document category", "business reference qualifier", "source-specific code"],
            concepts=[CanonicalConcept.DOCUMENT_TYPE, CanonicalConcept.BUSINESS_REFERENCE, CanonicalConcept.UNKNOWN],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="The abbreviation is source-specific and requires implementor review.",
        )

    if inferred_data_type == InferredDataType.DATE_LIKE:
        return SemanticSuggestion(
            meanings=["date-like business field"],
            concepts=[CanonicalConcept.TRANSACTION_DATE],
            status=AmbiguityStatus.AMBIGUOUS,
            notes="Data characteristics are date-like, but the business meaning of the date is not established.",
        )

    return SemanticSuggestion(
        meanings=[],
        concepts=[CanonicalConcept.UNKNOWN],
        status=AmbiguityStatus.UNKNOWN,
        notes="No reliable deterministic semantic suggestion is available from the current evidence.",
    )
