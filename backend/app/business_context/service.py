from __future__ import annotations

from dataclasses import replace

from app.report_understanding import ReportProfile

from .models import (
    BusinessContextProfile,
    BusinessContextScope,
    ConfirmationStatus,
    FieldMapping,
    ProfileStatus,
)


class BusinessContextService:
    """Pure review/domain service. It performs no database persistence."""

    def create_from_report_profile(
        self,
        *,
        profile_id: str,
        report_profile: ReportProfile,
        scope: BusinessContextScope,
        description: str | None = None,
        notes: str | None = None,
    ) -> BusinessContextProfile:
        profile_id = profile_id.strip()
        if not profile_id:
            raise ValueError("profile_id is required")
        if not scope.source_format_id.strip():
            raise ValueError("source_format_id is required")

        mappings = [
            FieldMapping(source_field=column.source_column_name)
            for column in report_profile.columns
        ]

        return BusinessContextProfile(
            profile_id=profile_id,
            scope=scope,
            report_profile=report_profile,
            description=description,
            field_mappings=mappings,
            status=ProfileStatus.DRAFT,
            notes=notes,
        )

    def confirm_field(
        self,
        profile: BusinessContextProfile,
        *,
        source_field: str,
        business_meaning: str,
        canonical_role: str,
        implementor_note: str | None = None,
        transformation: str = "NONE",
    ) -> FieldMapping:
        meaning = business_meaning.strip()
        role = canonical_role.strip()
        if not meaning:
            raise ValueError("business_meaning is required when confirming a mapping")
        if not role:
            raise ValueError("canonical_role is required when confirming a mapping")

        mapping = profile.get_mapping(source_field)
        mapping.business_meaning = meaning
        mapping.canonical_role = role
        mapping.confirmation_status = ConfirmationStatus.CONFIRMED
        mapping.implementor_note = implementor_note
        mapping.transformation = transformation
        profile.status = ProfileStatus.IN_REVIEW
        return mapping

    def reject_field(
        self,
        profile: BusinessContextProfile,
        *,
        source_field: str,
        implementor_note: str | None = None,
    ) -> FieldMapping:
        mapping = profile.get_mapping(source_field)
        mapping.business_meaning = None
        mapping.canonical_role = None
        mapping.confirmation_status = ConfirmationStatus.REJECTED
        mapping.implementor_note = implementor_note
        profile.status = ProfileStatus.IN_REVIEW
        return mapping

    def mark_unmapped(
        self,
        profile: BusinessContextProfile,
        *,
        source_field: str,
        implementor_note: str | None = None,
    ) -> FieldMapping:
        mapping = profile.get_mapping(source_field)
        mapping.business_meaning = None
        mapping.canonical_role = None
        mapping.confirmation_status = ConfirmationStatus.UNMAPPED
        mapping.implementor_note = implementor_note
        profile.status = ProfileStatus.IN_REVIEW
        return mapping

    def leave_pending(
        self,
        profile: BusinessContextProfile,
        *,
        source_field: str,
        implementor_note: str | None = None,
    ) -> FieldMapping:
        mapping = profile.get_mapping(source_field)
        mapping.business_meaning = None
        mapping.canonical_role = None
        mapping.confirmation_status = ConfirmationStatus.PENDING_REVIEW
        mapping.implementor_note = implementor_note
        profile.status = ProfileStatus.IN_REVIEW
        return mapping

    def finalize_review(self, profile: BusinessContextProfile) -> BusinessContextProfile:
        """Marks the profile reviewed without auto-resolving pending fields."""
        profile.status = ProfileStatus.REVIEWED
        return profile
