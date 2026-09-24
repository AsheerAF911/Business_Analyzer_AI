from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.report_understanding import ReportProfile


class ConfirmationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    UNMAPPED = "UNMAPPED"


class ProfileStatus(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    REVIEWED = "REVIEWED"


@dataclass(frozen=True)
class BusinessContextScope:
    """Scope under which a mapping is valid.

    company_context is intentionally a caller-supplied opaque key for now.
    It is not a fabricated database company_id. A future authenticated tenant
    boundary can replace/supply this value without changing field mappings.
    """

    company_context: str | None
    report_type: str | None
    source_format_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FieldMapping:
    source_field: str
    business_meaning: str | None = None
    canonical_role: str | None = None
    confirmation_status: ConfirmationStatus = ConfirmationStatus.PENDING_REVIEW
    implementor_note: str | None = None
    transformation: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_field": self.source_field,
            "business_meaning": self.business_meaning,
            "canonical_role": self.canonical_role,
            "confirmation_status": self.confirmation_status.value,
            "implementor_note": self.implementor_note,
            "transformation": self.transformation,
        }


@dataclass
class BusinessContextProfile:
    profile_id: str
    scope: BusinessContextScope
    report_profile: ReportProfile
    description: str | None = None
    field_mappings: list[FieldMapping] = field(default_factory=list)
    status: ProfileStatus = ProfileStatus.DRAFT
    notes: str | None = None

    def get_mapping(self, source_field: str) -> FieldMapping:
        for mapping in self.field_mappings:
            if mapping.source_field == source_field:
                return mapping
        raise KeyError(f"Unknown source field: {source_field}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "scope": self.scope.to_dict(),
            "description": self.description,
            "status": self.status.value,
            "notes": self.notes,
            # Part 1 snapshot is preserved unchanged for auditability.
            "report_profile": self.report_profile.to_dict(),
            "field_mappings": [mapping.to_dict() for mapping in self.field_mappings],
        }
