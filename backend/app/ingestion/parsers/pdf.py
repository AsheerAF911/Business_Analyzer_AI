from __future__ import annotations

from pathlib import Path

from .base import BaseParser, ParsedRecord


class PDFParser(BaseParser):

    def parse(
        self,
        file_path: Path,
        source_file: str,
    ) -> list[ParsedRecord]:

        raise NotImplementedError(
            "PDF parsing is not implemented yet. "
            "The unstructured ingestion path is reserved "
            "for the next processing stage."
        )