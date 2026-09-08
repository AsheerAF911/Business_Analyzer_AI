from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ParsedRecord:
    """
    Generic representation of one parsed source record.

    The parser preserves source information without assigning
    business meaning to the original fields.
    """

    def __init__(
        self,
        *,
        source_file: str,
        sheet: str | None,
        row_number: int | None,
        fields: dict[str, Any],
    ):
        self.source_file = source_file
        self.sheet = sheet
        self.row_number = row_number
        self.fields = fields

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "sheet": self.sheet,
            "row_number": self.row_number,
            "fields": self.fields,
        }


class BaseParser(ABC):

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        source_file: str,
    ) -> list[ParsedRecord]:
        """
        Parse a source file into generic records.

        Business interpretation should happen after parsing.
        """
        raise NotImplementedError