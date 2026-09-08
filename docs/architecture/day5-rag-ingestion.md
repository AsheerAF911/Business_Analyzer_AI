# Day 5 — RAG Ingestion Representation

## 1. Purpose

This stage establishes the internal evidence representation used
between source parsing and future vector ingestion.

The pipeline is:

Source Report
→ ParsedRecord
→ Document
→ Chunk

Embeddings and vector storage are not implemented in this stage.

---

## 2. ParsedRecord

ParsedRecord is the output of the ingestion parser.

It represents one parsed source record and preserves:

- source_file
- sheet
- row_number
- original source fields

ParsedRecord should remain close to the source format.

It is not the final PostgreSQL business schema and it is not
the final RAG representation.

---

## 3. Document

Document represents one logical source report.

A Document groups ParsedRecord objects belonging to the same
source report and provides a stable source/document reference.

Document does not interpret business values.

---

## 4. Chunk

A Chunk is the smallest evidence unit intended for future
retrieval.

Each Chunk contains:

- chunk_id
- document_id
- text
- metadata

The text provides a business-readable representation.

The metadata preserves evidence and source attribution.

---

## 5. Transaction-Level Chunking

Transaction-level chunking is the MVP default for structured
business reports.

Many business questions concern complete transactions rather
than individual spreadsheet rows.

For example, inventory transaction D1IN0818 spans multiple
Excel rows.

Treating each row independently would split the transaction
context.

Transaction-level chunking therefore groups rows sharing the
same transaction identifier.

For the current inventory report the transaction identifier is:

INWARD NO

This business mapping belongs to the inventory transaction
chunking strategy, not to the generic Chunk model.

---

## 6. Extensibility

Transaction-level chunking is a strategy, not a permanent
system-wide assumption.

Future strategies may include:

- row-level chunks
- page-level chunks
- accounting-period chunks
- invoice-level chunks
- production-order chunks
- document-section chunks

The Document and Chunk models should remain reusable across
these strategies.

---

## 7. Metadata

Metadata exists for filtering, evidence preservation, and
source attribution.

Potential metadata fields include:

- source_file
- report_type
- department
- date
- page
- sheet
- row
- source_rows
- product
- supplier
- customer
- transaction_number

Metadata values must only be populated when supported by the
source or by an explicitly defined field mapping.

Missing metadata should remain absent rather than being guessed.

---

## 8. Current Inventory Mappings

The current inventory transaction chunking strategy defines:

INWARD NO → transaction_number
VENDOR NAME → supplier
DATE → date
PRODUCTION → production

These mappings preserve source terminology.

For example:

VENDOR NAME = D1

becomes:

supplier = D1

No additional meaning of D1 is inferred.

Likewise:

PRODUCTION = D17

remains:

production = D17

It is not reinterpreted as a location, factory, department, or
production line.

---

## 9. Source Traceability

Every inventory transaction chunk preserves:

- source_file
- sheet
- original Excel row numbers

Example:

source_file:
Inventory_transactions.xlsx

sheet:
Sheet1

source_rows:
[2, 3, 4, 5]

This ensures a future retrieved chunk can be traced back to the
original business evidence.

---

## 10. Date Representation

The current sample exposes the Excel DATE value as serial:

46143

The chunk preparation layer currently preserves that value.

Date interpretation and normalization are deliberately outside
the responsibility of the chunking layer.

A later normalization step should handle Excel date serials
without destroying the original source representation.

---

## 11. Evidence Principle

The RAG pipeline should preserve evidence rather than merely
produce text.

Current flow:

Source Report
→ ParsedRecord
→ Document
→ Chunk

Future flow:

Chunk
→ Embedding
→ Qdrant

Later retrieval flow:

Question
→ Retrieval
→ Evidence Chunks
→ LLM Reasoning
→ Answer with Source Attribution

---

## Document Identity

The current MVP derives document_id from the source filename.

This is sufficient for local document/chunk preparation tests,
but it is not suitable as the final persistent identity because
multiple reports may be uploaded using the same filename.

Before persistent vector storage is introduced, Document should
support an identity derived from the persisted Report record.

Conceptually:

Report.id = 41
→ Document.document_id = "report-41"

This will prevent collisions between separate uploads with the
same filename.

The current filename-derived implementation remains unchanged
during this validation stage.

## 12. Not Implemented

This stage does not implement:

- embeddings
- Qdrant
- semantic search
- LLM calls
- retrieval
- reranking
- PostgreSQL business normalization
- forecasting
- business intelligence calculations

---

## 13. Next Step

After the document/chunk representation is validated, the next
stage will introduce:

Chunk
→ Embedding
→ Qdrant

Before that stage, chunk identity, metadata consistency, source
traceability, and date handling should be validated.