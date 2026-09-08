from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, ReportStatus, ReportType
from app.ingestion import (
    IngestionService,
    UnsupportedFileTypeError,
)


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


ALLOWED_EXTENSIONS = {
    ".pdf": "PDF",
    ".xlsx": "XLSX",
    ".xls": "XLS",
    ".csv": "CSV",
}


UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
def upload_report(
    file: UploadFile = File(...),
    report_type: ReportType = Form(...),
    db: Session = Depends(get_db),
):
    original_filename = Path(
        file.filename or ""
    ).name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    extension = Path(
        original_filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. "
                "Allowed types: PDF, XLSX, XLS, CSV."
            ),
        )

    file_type = ALLOWED_EXTENSIONS[
        extension
    ]

    stored_filename = (
        f"{uuid4().hex}{extension}"
    )

    destination = UPLOAD_DIR / stored_filename

    # --------------------------------------------------
    # 1. Save uploaded file
    # --------------------------------------------------

    try:
        with destination.open("wb") as buffer:
            while chunk := file.file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

    except OSError:
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to save the uploaded file."
            ),
        )

    # --------------------------------------------------
    # 2. Create Report
    # --------------------------------------------------

    try:
        report = Report(
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_type=file_type,
            report_type=report_type,
            status=ReportStatus.UPLOADED,
        )

        db.add(report)
        db.commit()
        db.refresh(report)

    except Exception:
        db.rollback()

        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to register the uploaded report."
            ),
        )

    # --------------------------------------------------
    # 3. Create Processing Job
    # --------------------------------------------------

    ingestion_service = IngestionService(db)

    try:
        job = ingestion_service.create_job(
            report
        )

    except Exception:
        db.rollback()

        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "Failed to create the processing job."
            ),
        )

    # --------------------------------------------------
    # 4. Process Report
    # --------------------------------------------------

    try:
        ingestion_service.process(
            job=job,
            report=report,
            file_path=destination,
        )

    except UnsupportedFileTypeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type.",
        )

    except Exception:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="Report processing failed.",
        )

    # --------------------------------------------------
    # 5. Return Report + Processing Job
    # --------------------------------------------------

    return {
        "id": report.id,
        "original_filename": (
            report.original_filename
        ),
        "report_type": (
            report.report_type.value
        ),
        "status": report.status.value,
        "uploaded_at": report.uploaded_at,
        "processing_job": {
            "id": job.id,
            "status": job.status.value,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        },
    }