from __future__ import annotations

from collections import defaultdict
from typing import Any

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ingestion.parsers.base import ParsedRecord
from app.rag_ingestion.models import Chunk, Document

from .base import ChunkingStrategy


class InventoryTransactionChunkingStrategy(ChunkingStrategy):

    TRANSACTION_FIELD = "INWARD NO"

    # These are explicit source-to-metadata mappings.
    METADATA_FIELD_MAP = {
        "DATE": "date",
        "VENDOR NAME": "supplier",
        "PRODUCTION": "production",
    }

    def create_chunks(self, document: Document) -> list[Chunk]:
        grouped_records: dict[str, list[ParsedRecord]] = defaultdict(list)

        for record in document.records:
            transaction_number = record.fields.get(
                self.TRANSACTION_FIELD
            )

            if transaction_number in (None, ""):
                continue

            grouped_records[str(transaction_number)].append(record)

        chunks = []

        for transaction_number, records in grouped_records.items():
            chunk = self._create_transaction_chunk(
                document=document,
                transaction_number=transaction_number,
                records=records,
            )

            chunks.append(chunk)

        return chunks

    def _create_transaction_chunk(
        self,
        *,
        document: Document,
        transaction_number: str,
        records: list[ParsedRecord],
    ) -> Chunk:

        sheet = self._single_common_value(
            [record.sheet for record in records]
        )

        source_rows = [
            record.row_number
            for record in records
            if record.row_number is not None
        ]

        metadata: dict[str, Any] = {
            "source_file": document.source_file,
            "transaction_number": transaction_number,
            "source_rows": source_rows,
        }

        if document.report_type is not None:
            metadata["report_type"] = document.report_type

        if sheet is not None:
            metadata["sheet"] = sheet

        first_fields = records[0].fields

        for source_field, metadata_field in self.METADATA_FIELD_MAP.items():
            value = first_fields.get(source_field)

            if value not in (None, ""):
                metadata[metadata_field] = value

        text = self._build_transaction_text(
            transaction_number=transaction_number,
            records=records,
        )

        sheet_part = sheet or "unknown-sheet"

        chunk_id = (
            f"{document.document_id}-"
            f"{sheet_part}-"
            f"transaction-"
            f"{transaction_number}"
        )

        return Chunk(
            chunk_id=chunk_id,
            document_id=document.document_id,
            text=text,
            metadata=metadata,
        )

    def _build_transaction_text(
        self,
        *,
        transaction_number: str,
        records: list[ParsedRecord],
    ) -> str:

        first_fields = records[0].fields

        lines = [
            f"Inventory transaction {transaction_number}."
        ]

        date = first_fields.get("DATE")

        if date not in (None, ""):
            lines.append(f"Date: {date}")

        production = first_fields.get("PRODUCTION")

        if production not in (None, ""):
            lines.append(f"Production: {production}")

        vendor = first_fields.get("VENDOR NAME")

        if vendor not in (None, ""):
            lines.append(f"Vendor: {vendor}")

        invoice = first_fields.get("INVOICE")

        if invoice not in (None, ""):
            lines.append(f"Invoice: {invoice}")

        lines.append("")
        lines.append("Items:")

        for index, record in enumerate(records, start=1):
            fields = record.fields

            product = fields.get("PRODUCT DESCRIPTION")

            if product not in (None, ""):
                lines.append(
                    f"- {index}. Product: {product}"
                )
            else:
                lines.append(
                    f"- {index}. Source row: {record.row_number}"
                )

            self._append_if_present(
                lines,
                "Barcode",
                fields.get("BARCODE"),
            )

            self._append_if_present(
                lines,
                "Packaging size",
                fields.get("PACKAGING SIZE (KG)"),
            )

            self._append_if_present(
                lines,
                "Quantity received",
                fields.get(
                    "QUANTITY RECEIVED (NO. OF PCS.)"
                ),
            )

            self._append_if_present(
                lines,
                "Total quantity received",
                fields.get(
                    "TOTAL QUANTITY RECEIVED (KG)"
                ),
            )

            self._append_if_present(
                lines,
                "Net stock quantity",
                fields.get("NET STOCK QTY"),
            )

        source_rows = [
            record.row_number
            for record in records
            if record.row_number is not None
        ]

        lines.append("")
        lines.append(
            self._build_source_reference(
                source_file=records[0].source_file,
                sheet=records[0].sheet,
                source_rows=source_rows,
            )
        )

        return "\n".join(lines)

    @staticmethod
    def _append_if_present(
        lines: list[str],
        label: str,
        value: Any,
    ) -> None:
        if value not in (None, ""):
            lines.append(f"  {label}: {value}")

    @staticmethod
    def _single_common_value(values: list[Any]) -> Any:
        meaningful_values = [
            value
            for value in values
            if value not in (None, "")
        ]

        if not meaningful_values:
            return None

        first_value = meaningful_values[0]

        if all(
            value == first_value
            for value in meaningful_values
        ):
            return first_value

        return None

    @staticmethod
    def _build_source_reference(
        *,
        source_file: str,
        sheet: str | None,
        source_rows: list[int],
    ) -> str:

        parts = [f"Source: {source_file}"]

        if sheet is not None:
            parts.append(f"Sheet: {sheet}")

        if source_rows:
            parts.append(
                "Rows: "
                + ", ".join(str(row) for row in source_rows)
            )

        return ", ".join(parts)