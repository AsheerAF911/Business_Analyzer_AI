from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import business_context as route_module
from app.routes.business_context import router
from app.business_context import JsonBusinessContextProfileStore


def sample_report_profile_payload():
    return {
        "source_file": "sample.xlsx",
        "report_type": "Inventory",
        "sheets": ["Sheet1"],
        "record_count": 1,
        "column_count": 1,
        "profiled_at": None,
        "columns": [{
            "source_column_name": "VENDOR NAME",
            "inferred_data_type": "string",
            "example_values": ["D1"],
            "null_count": 0,
            "total_count": 1,
            "null_percentage": 0.0,
            "unique_value_count": 1,
            "possible_semantic_meanings": ["supplier", "receiving entity"],
            "possible_canonical_concepts": ["SUPPLIER", "DESTINATION_ENTITY"],
            "ambiguity_status": "AMBIGUOUS",
            "profiling_notes": "Needs implementor review.",
        }],
        "warnings": ["1 column(s) require semantic review."],
    }


def test_api_create_get_and_review(monkeypatch, tmp_path):
    store = JsonBusinessContextProfileStore(tmp_path)
    monkeypatch.setattr(route_module, "get_profile_store", lambda: store)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    create = client.post("/api/business-context/profiles", json={
        "profile_id": "company-a-inventory-v1",
        "company_context": "company-a",
        "report_type": "Inventory",
        "source_format_id": "inventory-format-a",
        "description": "Company A inventory layout",
        "report_profile": sample_report_profile_payload(),
    })
    assert create.status_code == 200
    assert create.json()["field_mappings"][0]["confirmation_status"] == "PENDING_REVIEW"

    review = client.put(
        "/api/business-context/profiles/company-a-inventory-v1/fields/VENDOR%20NAME",
        json={
            "confirmation_status": "CONFIRMED",
            "business_meaning": "Receiving Entity",
            "canonical_role": "DESTINATION_ENTITY",
            "implementor_note": "Confirmed with implementor.",
        },
    )
    assert review.status_code == 200
    assert review.json()["mapping"]["canonical_role"] == "DESTINATION_ENTITY"

    fetched = client.get("/api/business-context/profiles/company-a-inventory-v1")
    assert fetched.status_code == 200
    data = fetched.json()
    assert data["report_profile"]["columns"][0]["possible_semantic_meanings"] == ["supplier", "receiving entity"]
    assert data["field_mappings"][0]["business_meaning"] == "Receiving Entity"
