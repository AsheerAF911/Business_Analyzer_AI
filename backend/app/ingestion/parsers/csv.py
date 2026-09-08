from __future__ import annotations

import csv
from pathlib import Path

from .base import BaseParser, ParsedRecord


class CSVParser(BaseParser):

    def parse(
        self,
        file_path: Path,
        source_file: str,
    ) -> list[ParsedRecord]:

        records: list[ParsedRecord] = []

        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(file)

            for row_number, row in enumerate(
                reader,
                start=2,
            ):

                if not any(
                    value not in (None, "")
                    for value in row.values()
                ):
                    continue

                fields = {
                    key: value if value != "" else None
                    for key, value in row.items()
                    if key
                }

                records.append(
                    ParsedRecord(
                        source_file=source_file,
                        sheet=None,
                        row_number=row_number,
                        fields=fields,
                    )
                )

        return records