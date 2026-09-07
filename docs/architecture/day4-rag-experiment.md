# Day 4 — RAG Experiment: Inventory Excel → Business Chunks

## Purpose

This is an educational document-processing experiment for the Business AI / AI Business Investigator project.

It deliberately stops before embeddings, Qdrant, semantic search, LLM calls, and production ingestion.

## 1. What the original Excel file contains

`Inventory_transactions.xlsx` contains one worksheet, `Sheet1`.

The inspected workbook has:

- **13 data rows** (rows 2–14)
- **26 columns in the worksheet**
- **25 named columns plus one empty trailing column**
- the populated business columns include `PRODUCTION`, `DATE`, `INWARD NO`, `BARCODE`, `PRODUCT DESCRIPTION`, packaging/quantity fields, `INV/DO`, `VENDOR NAME`, and several document/traceability fields.

In this sample, rows represent **individual inventory inward/item records**. Several rows share the same inward number (`D1IN0820`), while each row has a different barcode/product. That makes the row a useful atomic business record for this first experiment.

The `DATE` values are stored as Excel serial values. The sample value `46143` is interpreted as `2026-05-01` by the processor.

Missing values are concentrated in fields such as `FG/ RM.`, `LOOSE QTY`, `SHORTAGE`, `BATCH NO`, `BRAND NAME`, `DELIVERY NO`, `QCR NO`, `INVOICE/DELIVERY DATE`, `EXPIRY DATE`, `ERP RECIPET NO`, `Count`, and `Last received`. The processor omits empty fields from chunk text and writes `null` to metadata fields that are unavailable.

## 2. Why we do not send the raw Excel file directly to an LLM

An Excel workbook is a file format, not a clean reasoning context.

Before a future AI system can reason over the data, it needs to know:

- which sheet a record came from,
- which row produced the evidence,
- what each value means,
- which values belong together,
- which values are missing,
- and how to cite the source.

Converting rows into business-readable records makes the evidence explicit and gives the later retrieval system something meaningful to retrieve.

## 3. What is a document in this experiment?

These terms must stay separate:

- **Source file** — the original uploaded artifact: `Inventory_transactions.xlsx`.
- **Document** — a logical business source derived from that file. In a larger system, a workbook, report section, or other source unit could become a document.
- **Chunk** — a smaller retrievable unit taken from a document. Here, one meaningful inventory transaction/item row is the atomic chunk.
- **Metadata** — structured attributes attached to a chunk for filtering, identification, and source traceability. Metadata is not a replacement for the chunk's business text.

So, conceptually:

`Inventory_transactions.xlsx` (source file)
→ inventory report records (logical document content)
→ one-row business chunks
→ metadata attached to each chunk

## 4. What does a chunk mean here?

For this first experiment, a chunk is a business-readable representation of one meaningful spreadsheet row.

It is **not**:

- the raw Python dictionary,
- a CSV-style line,
- an arbitrary 500-character slice,
- or the entire worksheet.

The processor turns a row into text such as:

> Inventory transaction on 2026-05-01. Inward number: D1IN0818. Production/location: D17. Vendor/source: D1. Product: RM_CHILLI POWDER OMEGA_5390380630955. Barcode: 30955. Packaging size: 20 kg. Quantity received: 8 pcs. Total quantity received: 160 kg. Net stock quantity: 160 kg. Transaction document type: TRN. Invoice: DD09883.

Only values actually present in the source row are included.

## 5. Why one transaction row can be an appropriate atomic chunk

A row can be a strong atomic unit for tabular business data when the row itself represents a coherent business event/item.

This sample has multiple rows under the same inward number, but each row describes a different product and quantity. Keeping each row atomic gives us:

- precise evidence,
- easy row-level citations,
- simple retrieval targets,
- less unrelated context inside a chunk,
- and an easy starting point for later grouping experiments.

The strategy is intentionally easy to change. If later investigation questions require all products under one inward number together, related rows can be grouped without changing the rest of the architecture.

## 6. Metadata attached to each chunk

Each chunk contains:

- `source_file`
- `report_type` = `inventory`
- `sheet`
- `row_number`
- `date`
- `transaction_number` (mapped from `INWARD NO`)
- `product`
- `barcode`
- `vendor`

Missing metadata values are represented as `null`.

The row number is the **Excel worksheet row number**, so the first data record is row 2.

## 7. Why metadata matters

Metadata supports future retrieval and evidence handling.

For example, a future retrieval layer could filter inventory chunks by:

- report type,
- date,
- product,
- barcode,
- vendor,
- transaction/inward number,
- or source sheet.

It also preserves the evidence location:

`Inventory_transactions.xlsx → Sheet1 → Row 2`

That source location is separate from the natural-language chunk text. The text helps the AI understand the business record; metadata helps the system find, filter, and cite it.

## 8. Why we are not creating embeddings yet

Embeddings would answer a later question: "How can we represent this text numerically so that semantically similar content can be retrieved?"

That is premature here.

First we need to validate that the text representation itself is good. If the chunk is confusing, incomplete, or mixes unrelated business facts, an embedding will not fix the underlying representation.

## 9. Why we are not using Qdrant yet

Qdrant is a future vector retrieval component.

Today we are testing the more fundamental transformation:

**source data → useful retrievable units**

Until we know that our chunks and metadata are sensible, introducing a vector database adds complexity without helping us learn the core document-processing decision.

## 10. Limitations of this first chunking strategy

This prototype intentionally has limitations:

1. It assumes each non-empty data row is a meaningful inventory item/transaction.
2. It does not group related rows by inward number.
3. It does not infer business meaning that is absent from the source.
4. It does not validate quantities or reconcile totals.
5. It does not distinguish every possible inventory transaction subtype beyond the source fields.
6. It uses a fixed field-to-sentence mapping rather than a configurable schema.
7. It does not parse PDFs or other report formats.
8. It does not create embeddings or perform retrieval.
9. It does not deduplicate records.
10. It does not represent relationships between rows as a graph.

These are acceptable because this is a learning prototype, not the production ingestion layer.

## Architecture

```text
Excel
  ↓
Records
  ↓
Business-aware representation
  ↓
Chunks
  ↓
Metadata
  ↓
JSON
```

The important design principle is:

```text
SOURCE FILE ≠ DOCUMENT ≠ CHUNK ≠ METADATA
```

A source file is where the evidence originates. A document is a logical source unit. A chunk is a retrievable piece of that source. Metadata describes and locates the chunk; it is not the chunk itself.
