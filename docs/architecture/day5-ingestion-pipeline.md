# Day 5 — Ingestion Pipeline

## 1. Purpose

Day 5 introduces the processing-job foundation for Business AI.

Previously:

Uploaded Report
↓
Stored File
↓
Report Record

Now:

Uploaded Report
↓
Processing Job
↓
Parser
↓
Structured / Unstructured Processing

The ProcessingJob exists to track the lifecycle of processing independently
from the uploaded Report.

---

## 2. Report vs ProcessingJob

### Report

The Report represents the uploaded business artifact.

It stores information such as:

- original filename
- stored filename
- file type
- report type
- report status
- upload timestamp

The original file remains the authoritative source.

### ProcessingJob

The ProcessingJob represents an attempt to process a Report.

It stores:

- id
- report_id
- status
- started_at
- completed_at
- error_message
- created_at

This allows processing lifecycle information to remain separate from
the uploaded file metadata.

---

## 3. Processing Lifecycle

```text
PENDING
   ↓
PROCESSING
   ↓
COMPLETED

4. Ingestion Architecture
Uploaded Report
       ↓
Processing Job
       ↓
Parser
       ↓
Structured / Unstructured

The API route is responsible for receiving the upload and initiating
processing.

The ingestion service is responsible for processing orchestration.

Parser implementations are responsible for reading source files.

5. Parser Routing

Supported file types:

.xlsx → ExcelParser
.xls  → ExcelParser
.csv  → CSVParser
.pdf  → PDFParser

The parser registry is used instead of placing parser-specific logic
inside the API route.

6. Structured Parsing

For XLSX/XLS/CSV files, the initial structured path produces generic
parsed records.

Each record preserves source information such as:

source file
sheet
row number
original fields and values

The parser does not invent business meanings for source fields.

For example:

VENDOR NAME → preserved as VENDOR NAME
PRODUCTION → preserved as PRODUCTION
INWARD NO → preserved as INWARD NO

Business-specific interpretation belongs to later processing stages.

7. Current Inventory Test

The Day 4 Inventory_transactions.xlsx sample contains:

Sheet1
13 data rows
Excel rows 2–14

The Excel parser produces one ParsedRecord for each source row.

This is a parsing representation only.

It does not yet load the records into business tables.

It does not yet generate embeddings.

8. Structured Data Responsibility

Structured business data belongs in PostgreSQL.

Examples include:

sales
purchases
inventory
production
expenses
receivables
payables

PostgreSQL will be used for:

exact records
filtering
aggregation
deterministic calculations
business metrics
9. RAG Data Responsibility

RAG data is intended for:

business-readable document context
semantic retrieval
evidence
explanations
unstructured report content

The future RAG destination is Qdrant.

Raw business records should not automatically be duplicated into Qdrant.

10. Future RAG Path
Parsed Report
       ↓
Business-aware Document Representation
       ↓
Transaction-level Chunks
       ↓
Embedding Service
       ↓
Qdrant

Day 5 does not implement:

embeddings
Qdrant
vector search
semantic retrieval
reranking
LLM reasoning
11. Why Processing Logic Is Separate

The API route should remain thin.

The ingestion service provides the orchestration boundary:

API
 ↓
IngestionService
 ↓
Parser
 ↓
Parsed Records

This makes it possible to add additional parsers and downstream
processors without continuously expanding the FastAPI route.

12. Current Limitations

PDF parsing is currently represented by an interface/placeholder only.

No PDF extraction library is installed as part of this checkpoint.

The structured parser does not yet convert generic parsed records into
specific business entities.

The RAG path does not yet create embeddings or store vectors.

Processing is synchronous.

A background worker may be introduced later if processing requirements
justify it.

13. Next Stage

The next checkpoint will build on the parsed-record boundary.

Future stages will introduce the separation between:

Structured Processing
        ↓
PostgreSQL

and:

RAG Processing
        ↓
Business-aware document representation
        ↓
Transaction-level chunks
        ↓
Embedding
        ↓
Qdrant

---

# 16. Testing

For the five tests you specified, the expected behavior is now:

| Test | Expected |
|---|---|
| `Inventory_transactions.xlsx` | Report → Job → `ExcelParser` → 13 records → COMPLETED |
| CSV | Report → Job → `CSVParser` → COMPLETED |
| PDF | Report → Job → `PDFParser` → currently FAILED with controlled "not implemented" error |
| Unsupported extension | Rejected by existing upload validation |
| Parser failure | Job → FAILED + `error_message` |

One nuance: **PDF should not be considered a successful processing test yet.** Your requirement says the PDF path should be selected or clearly identified as the next stage. With the placeholder above, the correct result is:

```text
PDF
 ↓
ProcessingJob
 ↓
PDFParser selected
 ↓
NotImplementedError
 ↓
FAILED