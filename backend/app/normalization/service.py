from __future__ import annotations

from typing import Any, Protocol

from app.business_context import BusinessContextProfile, ConfirmationStatus
from app.report_understanding import CanonicalConcept

from .models import (
    CanonicalDraft,
    CanonicalValue,
    NormalizationWarning,
    SourceProvenance,
    TransformationType,
    UnmappedField,
)
from .transformations import TransformationError, transform_value


class ParsedRecordLike(Protocol):
    source_file: str
    sheet: str
    row_number: int
    fields: dict[str, Any]


class NormalizationService:
    """Executes Part 2 decisions without making new semantic decisions."""

    def normalize_records(
        self,
        records: list[ParsedRecordLike],
        profile: BusinessContextProfile,
    ) -> list[CanonicalDraft]:
        return [self.normalize_record(record, profile) for record in records]

    def normalize_record(
        self,
        record: ParsedRecordLike,
        profile: BusinessContextProfile,
    ) -> CanonicalDraft:
        record_provenance = SourceProvenance(
            source_file=record.source_file,
            sheet=record.sheet,
            row_number=record.row_number,
        )
        draft = CanonicalDraft(
            provenance=record_provenance,
            source_record_reference=(
                f"{record.source_file}:{record.sheet}:{record.row_number}"
            ),
        )
        mappings = {mapping.source_field: mapping for mapping in profile.field_mappings}

        for source_field, raw_value in record.fields.items():
            field_provenance = SourceProvenance(
                source_file=record.source_file,
                sheet=record.sheet,
                row_number=record.row_number,
                source_field=source_field,
            )
            mapping = mappings.get(source_field)

            if mapping is None:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason="NO_MAPPING",
                        provenance=field_provenance,
                    )
                )
                continue

            if mapping.confirmation_status != ConfirmationStatus.CONFIRMED:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason=f"MAPPING_{mapping.confirmation_status.value}",
                        provenance=field_provenance,
                    )
                )
                continue

            if not mapping.business_meaning or not mapping.canonical_role:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason="CONFIRMED_MAPPING_INCOMPLETE",
                        provenance=field_provenance,
                    )
                )
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="INCOMPLETE_CONFIRMED_MAPPING",
                        message=(
                            "Confirmed mapping must contain business meaning and "
                            "canonical role."
                        ),
                        source_field=source_field,
                    )
                )
                continue

            try:
                concept = CanonicalConcept(mapping.canonical_role)
            except ValueError:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason="UNKNOWN_CANONICAL_CONCEPT",
                        provenance=field_provenance,
                    )
                )
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="UNKNOWN_CANONICAL_CONCEPT",
                        message=f"Unknown canonical concept: {mapping.canonical_role!r}",
                        source_field=source_field,
                    )
                )
                continue

            try:
                transformation = TransformationType(mapping.transformation or "NONE")
            except ValueError:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason="UNKNOWN_TRANSFORMATION",
                        provenance=field_provenance,
                    )
                )
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="UNKNOWN_TRANSFORMATION",
                        message=f"Unknown transformation: {mapping.transformation!r}",
                        source_field=source_field,
                        canonical_concept=concept,
                    )
                )
                continue

            try:
                normalized_value = transform_value(raw_value, transformation)
            except TransformationError as exc:
                draft.unmapped_fields.append(
                    UnmappedField(
                        source_field=source_field,
                        value=raw_value,
                        reason="TRANSFORMATION_FAILED",
                        provenance=field_provenance,
                    )
                )
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="TRANSFORMATION_FAILED",
                        message=str(exc),
                        source_field=source_field,
                        canonical_concept=concept,
                    )
                )
                continue

            draft.add_canonical_value(
                CanonicalValue(
                    concept=concept,
                    value=normalized_value,
                    business_meaning=mapping.business_meaning,
                    source_field=source_field,
                    transformation=transformation,
                    provenance=field_provenance,
                )
            )

        # A confirmed mapping that is missing entirely from this record is a
        # normalization-level visibility issue, not a Part 4 business error.
        for mapping in profile.field_mappings:
            if (
                mapping.confirmation_status == ConfirmationStatus.CONFIRMED
                and mapping.source_field not in record.fields
            ):
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="MISSING_MAPPING_INPUT",
                        message=(
                            f"Confirmed source field {mapping.source_field!r} is "
                            "not present in this parsed record."
                        ),
                        source_field=mapping.source_field,
                    )
                )

        for concept, values in draft.canonical_values.items():
            if len(values) > 1:
                source_fields = ", ".join(value.source_field for value in values)
                draft.transformation_warnings.append(
                    NormalizationWarning(
                        code="DUPLICATE_CANONICAL_CONCEPT",
                        message=(
                            f"Multiple source fields map to {concept.value}: "
                            f"{source_fields}. Values were preserved separately."
                        ),
                        canonical_concept=concept,
                    )
                )

        return draft
