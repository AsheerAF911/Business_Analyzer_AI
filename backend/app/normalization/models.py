from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.report_understanding import CanonicalConcept


class TransformationType(str, Enum):
    NONE = "NONE"
    DATE_NORMALIZATION = "DATE_NORMALIZATION"
    NUMBER_NORMALIZATION = "NUMBER_NORMALIZATION"
    TEXT_NORMALIZATION = "TEXT_NORMALIZATION"
    UNIT_NORMALIZATION = "UNIT_NORMALIZATION"


@dataclass(frozen=True)
class SourceProvenance:
    source_file: str
    sheet: str
    row_number: int
    source_field: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "sheet": self.sheet,
            "row_number": self.row_number,
            "source_field": self.source_field,
        }


@dataclass(frozen=True)
class CanonicalValue:
    concept: CanonicalConcept
    value: Any
    business_meaning: str
    source_field: str
    transformation: TransformationType
    provenance: SourceProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept": self.concept.value,
            "value": self.value,
            "business_meaning": self.business_meaning,
            "source_field": self.source_field,
            "transformation": self.transformation.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class UnmappedField:
    source_field: str
    value: Any
    reason: str
    provenance: SourceProvenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_field": self.source_field,
            "value": self.value,
            "reason": self.reason,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True)
class NormalizationWarning:
    code: str
    message: str
    source_field: str | None = None
    canonical_concept: CanonicalConcept | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "source_field": self.source_field,
            "canonical_concept": (
                self.canonical_concept.value if self.canonical_concept else None
            ),
        }


@dataclass
class CanonicalDraft:
    """Normalized intermediate representation before Part 4 validation.

    canonical_values stores a list per concept so two source fields mapping to
    the same concept cannot silently overwrite each other.
    """

    canonical_values: dict[CanonicalConcept, list[CanonicalValue]] = field(
        default_factory=dict
    )
    unmapped_fields: list[UnmappedField] = field(default_factory=list)
    transformation_warnings: list[NormalizationWarning] = field(default_factory=list)
    provenance: SourceProvenance | None = None
    source_record_reference: str = ""

    def add_canonical_value(self, value: CanonicalValue) -> None:
        self.canonical_values.setdefault(value.concept, []).append(value)

    def values_for(self, concept: CanonicalConcept) -> list[CanonicalValue]:
        return list(self.canonical_values.get(concept, []))

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_values": {
                concept.value: [item.to_dict() for item in values]
                for concept, values in self.canonical_values.items()
            },
            "unmapped_fields": [item.to_dict() for item in self.unmapped_fields],
            "transformation_warnings": [
                warning.to_dict() for warning in self.transformation_warnings
            ],
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "source_record_reference": self.source_record_reference,
        }
