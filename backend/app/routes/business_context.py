from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.business_context import (
    BusinessContextScope,
    BusinessContextService,
    ConfirmationStatus,
    JsonBusinessContextProfileStore,
    ProfileNotFoundError,
)
from app.business_context.serialization import report_profile_from_dict


router = APIRouter(
    prefix="/api/business-context",
    tags=["business-context"],
)


DEFAULT_PROFILE_DIR = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "business_context_profiles"
)


def get_profile_store() -> JsonBusinessContextProfileStore:
    configured = os.getenv("BUSINESS_CONTEXT_PROFILE_DIR")
    return JsonBusinessContextProfileStore(
        Path(configured) if configured else DEFAULT_PROFILE_DIR
    )


class CreateProfileRequest(BaseModel):
    profile_id: str
    company_context: str | None = None
    report_type: str | None = None
    source_format_id: str
    description: str | None = None
    notes: str | None = None
    report_profile: dict[str, Any]


class ReviewFieldRequest(BaseModel):
    confirmation_status: ConfirmationStatus
    business_meaning: str | None = None
    canonical_role: str | None = None
    implementor_note: str | None = None
    transformation: str = "NONE"


@router.post("/profiles")
def create_profile(payload: CreateProfileRequest):
    store = get_profile_store()
    service = BusinessContextService()
    profile = service.create_from_report_profile(
        profile_id=payload.profile_id,
        report_profile=report_profile_from_dict(payload.report_profile),
        scope=BusinessContextScope(
            company_context=payload.company_context,
            report_type=payload.report_type,
            source_format_id=payload.source_format_id,
        ),
        description=payload.description,
        notes=payload.notes,
    )
    store.save(profile)
    return profile.to_dict()


@router.get("/profiles")
def list_profiles():
    return [profile.to_dict() for profile in get_profile_store().list_profiles()]


@router.get("/profiles/{profile_id}")
def get_profile(profile_id: str):
    try:
        return get_profile_store().get(profile_id).to_dict()
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Business context profile not found") from exc


@router.put("/profiles/{profile_id}/fields/{source_field}")
def review_field(profile_id: str, source_field: str, payload: ReviewFieldRequest):
    store = get_profile_store()
    service = BusinessContextService()

    try:
        profile = store.get(profile_id)
    except ProfileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Business context profile not found") from exc

    try:
        if payload.confirmation_status == ConfirmationStatus.CONFIRMED:
            mapping = service.confirm_field(
                profile,
                source_field=source_field,
                business_meaning=payload.business_meaning or "",
                canonical_role=payload.canonical_role or "",
                implementor_note=payload.implementor_note,
                transformation=payload.transformation,
            )
        elif payload.confirmation_status == ConfirmationStatus.REJECTED:
            mapping = service.reject_field(
                profile,
                source_field=source_field,
                implementor_note=payload.implementor_note,
            )
        elif payload.confirmation_status == ConfirmationStatus.UNMAPPED:
            mapping = service.mark_unmapped(
                profile,
                source_field=source_field,
                implementor_note=payload.implementor_note,
            )
        else:
            mapping = service.leave_pending(
                profile,
                source_field=source_field,
                implementor_note=payload.implementor_note,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Source field not found in profile") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    store.save(profile)
    return {
        "profile_id": profile.profile_id,
        "mapping": mapping.to_dict(),
        "profile_status": profile.status.value,
    }
