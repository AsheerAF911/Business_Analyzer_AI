from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.dependencies import (
    get_structured_data_service,
)
from app.models import ReportType
from app.structured_data import (
    StructuredDataFilters,
    StructuredDataService,
)


router = APIRouter(
    prefix="/api/business-data",
    tags=["business-data"],
)


@router.get("")
def get_business_data(
    start_date: date | None = None,
    end_date: date | None = None,
    department: str | None = None,
    product: str | None = None,
    report_type: ReportType | None = None,
    service: StructuredDataService = Depends(
        get_structured_data_service
    ),
):
    try:
        filters = StructuredDataFilters(
            start_date=start_date,
            end_date=end_date,
            department=(
                department.strip()
                if department
                else None
            ),
            product=(
                product.strip()
                if product
                else None
            ),
            report_type=report_type,
        )

        return service.retrieve(filters)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc