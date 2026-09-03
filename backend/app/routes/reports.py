from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, ReportStatus, ReportType


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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_report(
    file: UploadFile = File(...),
    report_type: ReportType = Form(...),
    db: Session = Depends(get_db),
):
    original_filename = Path(file.filename or "").name

    if not original_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed types: PDF, XLSX, XLS, CSV.",
        )

    file_type = ALLOWED_EXTENSIONS[extension]

    stored_filename = f"{uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_filename

    try:
        with destination.open("wb") as buffer:
            while chunk := file.file.read(1024 * 1024):
                buffer.write(chunk)

    except OSError:
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save the uploaded file.",
        )

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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register the uploaded report.",
        )

    return {
        "id": report.id,
        "original_filename": report.original_filename,
        "report_type": report.report_type.value,
        "status": report.status.value,
        "uploaded_at": report.uploaded_at,
    }