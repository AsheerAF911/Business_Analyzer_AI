from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    ProcessingJob,
    ProcessingJobStatus,
    Report,
    ReportStatus,
)

from .parsers import (
    CSVParser,
    ExcelParser,
    PDFParser,
    BaseParser,
)

from app.rag_ingestion.indexing import RAGIndexingService


PARSER_REGISTRY: dict[str, BaseParser] = {
    ".xlsx": ExcelParser(),
    ".xls": ExcelParser(),
    ".csv": CSVParser(),
    ".pdf": PDFParser(),
}


class UnsupportedFileTypeError(Exception):
    pass


class IngestionService:

    def __init__(
        self,
        db: Session,
        *,
        rag_indexing_service: RAGIndexingService,
    ):
        self.db = db
        self.rag_indexing_service = rag_indexing_service

    def get_parser(
        self,
        file_path: Path,
    ) -> BaseParser:

        extension = file_path.suffix.lower()

        parser = PARSER_REGISTRY.get(
            extension
        )

        if parser is None:
            raise UnsupportedFileTypeError(
                f"Unsupported file type: {extension}"
            )

        return parser

    def create_job(
        self,
        report: Report,
    ) -> ProcessingJob:

        job = ProcessingJob(
            report_id=report.id,
            status=ProcessingJobStatus.PENDING,
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job

    def process(
        self,
        job: ProcessingJob,
        report: Report,
        file_path: Path,
    ) -> list:

        job.status = ProcessingJobStatus.PROCESSING
        job.started_at = datetime.now(timezone.utc)

        report.status = ReportStatus.PROCESSING

        self.db.commit()

        try:
            parser = self.get_parser(
                file_path
            )

            records = parser.parse(
                file_path=file_path,
                source_file=report.original_filename,
            )
            print(f"Parser selected: {parser.__class__.__name__}")
            print(f"Parsed records: {len(records)}")

            for record in records[:3]:
                print(record.to_dict())
            # Day 5 M1:
            #
            # We only establish the parsed-record
            # boundary here.
            #
            # Future stages will consume `records`
            # for structured loading and/or RAG
            # document/chunk generation.
            rag_result = self.rag_indexing_service.index_records(
                records=records,
                report_type=report.report_type.value,
            )

            job.status = (
                ProcessingJobStatus.COMPLETED
            )

            job.completed_at = (
                datetime.now(timezone.utc)
            )

            job.error_message = None

            report.status = ReportStatus.PROCESSED

            self.db.commit()

            return records

        except Exception as exc:

            job.status = (
                ProcessingJobStatus.FAILED
            )

            job.completed_at = (
                datetime.now(timezone.utc)
            )

            # Store the useful error message,
            # but don't expose the traceback through
            # the API.
            job.error_message = str(exc)[:4000]

            report.status = ReportStatus.FAILED

            self.db.commit()

            raise