from __future__ import annotations

from datetime import datetime
from typing import Any

from app.report_understanding import (
    AmbiguityStatus,
    CanonicalConcept,
    ColumnProfile,
    InferredDataType,
    ReportProfile,
)

from .models import (
    BusinessContextProfile,
    BusinessContextScope,
    ConfirmationStatus,
    FieldMapping,
    ProfileStatus,
)


def report_profile_from_dict(data: dict[str, Any]) -> ReportProfile:
    columns = [
        ColumnProfile(
            source_column_name=item["source_column_name"],
            inferred_data_type=InferredDataType(item["inferred_data_type"]),
            example_values=list(item.get("example_values", [])),
            null_count=int(item.get("null_count", 0)),
            total_count=int(item.get("total_count", 0)),
            null_percentage=float(item.get("null_percentage", 0.0)),
            unique_value_count=int(item.get("unique_value_count", 0)),
            possible_semantic_meanings=list(item.get("possible_semantic_meanings", [])),
            possible_canonical_concepts=[
                CanonicalConcept(value)
                for value in item.get("possible_canonical_concepts", [])
            ],
            ambiguity_status=AmbiguityStatus(item["ambiguity_status"]),
            profiling_notes=item.get("profiling_notes", ""),
        )
        for item in data.get("columns", [])
    ]

    profiled_at = data.get("profiled_at")
    return ReportProfile(
        source_file=data.get("source_file", ""),
        report_type=data.get("report_type"),
        sheets=list(data.get("sheets", [])),
        record_count=int(data.get("record_count", 0)),
        column_count=int(data.get("column_count", len(columns))),
        columns=columns,
        warnings=list(data.get("warnings", [])),
        profiled_at=datetime.fromisoformat(profiled_at) if profiled_at else None,
    )


def business_context_profile_from_dict(data: dict[str, Any]) -> BusinessContextProfile:
    scope_data = data["scope"]
    scope = BusinessContextScope(
        company_context=scope_data.get("company_context"),
        report_type=scope_data.get("report_type"),
        source_format_id=scope_data["source_format_id"],
    )

    mappings = [
        FieldMapping(
            source_field=item["source_field"],
            business_meaning=item.get("business_meaning"),
            canonical_role=item.get("canonical_role"),
            confirmation_status=ConfirmationStatus(item["confirmation_status"]),
            implementor_note=item.get("implementor_note"),
            transformation=item.get("transformation", "NONE"),
        )
        for item in data.get("field_mappings", [])
    ]

    return BusinessContextProfile(
        profile_id=data["profile_id"],
        scope=scope,
        report_profile=report_profile_from_dict(data["report_profile"]),
        description=data.get("description"),
        field_mappings=mappings,
        status=ProfileStatus(data.get("status", ProfileStatus.DRAFT.value)),
        notes=data.get("notes"),
    )
