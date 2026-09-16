from __future__ import annotations

import re
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ingestion.parsers.base import ParsedRecord

from .models import Document


def _safe_identifier(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
    return value.strip("-")


class DocumentBuilder:
    def build(
        self,
        records: list[ParsedRecord],
        report_type: str | None = None,
    ) -> Document:
        if not records:
            raise ValueError("Cannot create a document from empty parsed records.")

        source_file = records[0].source_file

        for record in records:
            if record.source_file != source_file:
                raise ValueError(
                    "All ParsedRecord objects in one Document must come "
                    "from the same source file."
                )

        source_stem = Path(source_file).stem

        document_id = _safe_identifier(source_stem)

        metadata = {
            "source_file": source_file,
        }

        if report_type is not None:
            metadata["report_type"] = report_type

        return Document(
            document_id=document_id,
            source_file=source_file,
            report_type=report_type,
            records=records,
            metadata=metadata,
        )