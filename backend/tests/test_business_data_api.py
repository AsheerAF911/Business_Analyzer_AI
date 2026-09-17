from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_structured_data_service
from app.main import app
from app.models import ReportType
from app.structured_data import (
    StructuredDataResult,
)


class FakeStructuredDataService:
    def __init__(self):
        self.last_filters = None

    def retrieve(self, filters):
        self.last_filters = filters

        if (
            filters.start_date is not None
            and filters.end_date is not None
            and filters.start_date > filters.end_date
        ):
            raise ValueError(
                "start_date cannot be after end_date."
            )

        if filters.department:
            raise ValueError(
                "Department filtering is not supported "
                "by the current structured schema."
            )

        return [
            StructuredDataResult(
                record_id=1,
                record_type="inventory_transaction",
                company_id=1,
                report_id=10,
                source_file="test_inventory.xlsx",
                report_type="Inventory",
                date=date(2026, 2, 10),
                department=None,
                product_id=2,
                product="Product A",
                quantity=Decimal("100"),
                amount=None,
            )
        ]


@pytest.fixture
def fake_service():
    return FakeStructuredDataService()


@pytest.fixture
def client(fake_service):
    def override_service():
        return fake_service

    app.dependency_overrides[
        get_structured_data_service
    ] = override_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(
        get_structured_data_service,
        None,
    )

def test_business_data_no_filters(
    client,
    fake_service,
):
    response = client.get(
        "/api/business-data"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["record_id"] == 1
    assert data[0]["product"] == "Product A"

    filters = fake_service.last_filters

    assert filters.start_date is None
    assert filters.end_date is None
    assert filters.department is None
    assert filters.product is None
    assert filters.report_type is None


def test_business_data_date_filters(
    client,
    fake_service,
):
    response = client.get(
        "/api/business-data",
        params={
            "start_date": "2026-01-01",
            "end_date": "2026-03-31",
        },
    )

    assert response.status_code == 200

    filters = fake_service.last_filters

    assert filters.start_date == date(
        2026, 1, 1
    )

    assert filters.end_date == date(
        2026, 3, 31
    )


def test_business_data_product_filter(
    client,
    fake_service,
):
    response = client.get(
        "/api/business-data",
        params={
            "product": "Product A",
        },
    )

    assert response.status_code == 200

    assert (
        fake_service.last_filters.product
        == "Product A"
    )


def test_business_data_report_type_filter(
    client,
    fake_service,
):
    response = client.get(
        "/api/business-data",
        params={
            "report_type": "Inventory",
        },
    )

    assert response.status_code == 200

    assert (
        fake_service.last_filters.report_type
        == ReportType.INVENTORY
    )


def test_business_data_invalid_date_format(
    client,
):
    response = client.get(
        "/api/business-data",
        params={
            "start_date": "not-a-date",
        },
    )

    assert response.status_code == 422


def test_business_data_invalid_date_range(
    client,
):
    response = client.get(
        "/api/business-data",
        params={
            "start_date": "2026-04-01",
            "end_date": "2026-01-01",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "start_date cannot be after end_date."
        )
    }


def test_business_data_department_unsupported(
    client,
):
    response = client.get(
        "/api/business-data",
        params={
            "department": "Manufacturing",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "Department filtering is not supported "
            "by the current structured schema."
        )
    }


def test_business_data_strips_whitespace(
    client,
    fake_service,
):
    response = client.get(
        "/api/business-data",
        params={
            "product": "  Product A  ",
        },
    )

    assert response.status_code == 200

    assert (
        fake_service.last_filters.product
        == "Product A"
    )