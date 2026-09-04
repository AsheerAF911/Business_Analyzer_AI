# Proposed RAG Architecture — Business AI

> **Status:** Proposed architecture / design documentation  
> **Day:** 3  
> **Scope:** Architecture and technical design only  
>
> This document describes the proposed Retrieval-Augmented Generation (RAG) architecture for Business AI. It does **not** represent an implemented RAG pipeline. Qdrant, embedding models, chunking, retrieval, and LLM reasoning are future components.

## 1. Current Project Context

Business AI currently has this structure:

```text
business-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── routes/
│   │       └── reports.py
│   ├── uploads/
│   ├── .env
│   └── pyproject.toml
│
└── Frontend/
    ├── .env
    ├── package.json
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        └── services/
            └── reportService.js
```

The existing application accepts supported business reports through the upload flow and records report metadata in PostgreSQL. This Day 3 task does not modify that implementation.

## 2. Proposed RAG Architecture

```text
Uploaded Business Report
        ↓
      Parser
        ↓
     Document
        ↓
     Chunker
        ↓
    Metadata
        ↓
    Embedding
        ↓
      Qdrant
```

The proposed pipeline transforms uploaded reports into searchable evidence for future business questions.

## 3. Source File

A **source file** is the original business report uploaded by the user.

Supported examples include:

- PDF
- XLSX
- XLS
- CSV

The source file is the original artifact and should remain the authoritative input to ingestion. It may contain sales, purchase, inventory, manufacturing, accounting, receivables, or payables information.

The source file is different from the searchable representations created later.

## 4. Parser

The **parser** reads the source file and extracts meaningful content while preserving useful structure.

Conceptually:

```text
PDF  → text, pages, tables, document structure
XLSX → sheets, rows, columns, cells
XLS  → sheets, rows, columns, cells
CSV  → rows, columns, records
```

For Business AI, parsing should preserve information such as sheet names, pages, tables, rows, and other source relationships wherever available.

## 5. Document

A **document** is the logical representation of content extracted from a source file.

A source file may produce one or more logical documents. A document might represent a complete report, report section, spreadsheet sheet, or another meaningful unit discovered during parsing.

The distinction is:

```text
Source File → original uploaded artifact
Document    → logical representation extracted from that artifact
```

This matters because the original file is not necessarily the ideal retrieval unit.

## 6. Chunk

A **chunk** is a smaller, retrievable piece of a document.

Conceptually:

```text
Document
    ↓
Chunk 1
Chunk 2
Chunk 3
Chunk 4
...
```

A chunk should be focused enough for retrieval while retaining enough context to be useful as evidence.

### Why chunking is necessary

Chunking is necessary because:

1. Large reports contain unrelated topics.
2. A question usually concerns only part of a report.
3. Embedding an entire report can produce an overly broad representation.
4. Retrieval works better when it can select smaller relevant units.
5. Smaller evidence units are easier to pass to a later reasoning model.
6. Chunk-level metadata can preserve source traceability.

The goal is not merely to make text smaller. The goal is to create meaningful retrieval units.

## 7. Structure-Aware Chunking

Business documents require **structure-aware chunking** rather than blindly splitting text by character count or arbitrary token boundaries.

For example:

```text
Sales Report
──────────────────────────────
Product | Customer | Quantity | Amount
A       | Customer 1 | 20      | 500
B       | Customer 2 | 10      | 300
```

A blind splitter could separate the headers from the rows that give them meaning.

A structure-aware strategy can preserve relationships such as:

```text
Sheet
  ↓
Table
  ↓
Header
  ↓
Related rows / records
```

For PDFs, useful structure may be:

```text
Page
  ↓
Section
  ↓
Heading
  ↓
Paragraph / Table
```

Future chunking should consider sections, headings, tables, sheets, table headers, related rows, pages, business records, and logical report sections.

The exact chunking algorithm is intentionally not implemented in Day 3.

## 8. Metadata

**Metadata** is information about a chunk rather than the primary content of the chunk.

Example:

```text
Chunk:
"Product A generated sales of 250 units..."

Metadata:
report_type = Sales
sheet = March Sales
page = 4
product = Product A
reporting_period = March 2026
```

Metadata helps answer:

- Which report produced this information?
- Which department owns it?
- Which period does it represent?
- Which sheet or page contains it?
- Which product, supplier, or customer is involved?

## 9. Metadata We Expect to Preserve

Where the source provides the information, the proposed architecture should preserve:

| Metadata | Purpose |
|---|---|
| Source file | Identifies the original uploaded report |
| Report type | Identifies Sales, Purchase, Inventory, etc. |
| Department | Identifies the responsible business area |
| Reporting period | Identifies month, quarter, year, etc. |
| Page | Identifies the source document page |
| Sheet | Identifies the spreadsheet worksheet |
| Row or record reference | Identifies the source row or business record |
| Product | Identifies the relevant product |
| Supplier | Identifies the relevant supplier |
| Customer | Identifies the relevant customer |

Not every source will contain every field. Metadata should only be populated when it can be reliably derived.

## 10. Embeddings

An **embedding** is a numerical representation of content.

Conceptually:

```text
Business text
      ↓
Embedding model
      ↓
Vector
```

The vector represents semantic characteristics of the content in mathematical form.

The specific embedding model has **not** been selected or implemented as part of Day 3.

## 11. Vector Similarity

**Vector similarity** measures how semantically related two vectors are.

Conceptually:

```text
User question
      ↓
Query embedding
      ↓
Compare with stored chunk embeddings
      ↓
Find semantically similar chunks
```

A question about products with the highest sales may retrieve chunks discussing product sales or performance even when the exact wording differs.

Vector similarity is a retrieval mechanism. It does not by itself prove that retrieved information is correct.

## 12. Qdrant

**Qdrant** is the proposed vector database for Business AI.

Conceptually:

```text
Chunk
 ├── content
 ├── embedding/vector
 └── metadata
          ↓
       Qdrant
```

Qdrant is **not being installed or implemented in Day 3**.

### What Qdrant will store

The future representation of each retrievable chunk will conceptually contain:

```text
Vector
+
Chunk content / payload
+
Metadata
```

Metadata may include:

```text
source_file
report_type
department
reporting_period
page
sheet
row_or_record_reference
product
supplier
customer
```

The exact collection and payload schema will be defined during implementation.

## 13. What Retrieval Returns

Future retrieval should return an **evidence set**, not merely a list of vectors.

Conceptually:

```text
User Question
      ↓
Retrieval
      ↓
Relevant chunks
      +
Metadata
      +
Source references
      ↓
Evidence Set
```

An evidence item should provide enough information to understand what the source says, where it came from, and which business context it belongs to.

A future evidence item may contain:

```text
chunk content
similarity/relevance information
source file
report type
reporting period
page/sheet
row/record reference
```

## 14. Retrieval Provides Evidence, Not the Final Answer

A core design principle is:

> **Retrieval provides evidence. The reasoning layer produces the answer.**

The vector database should not be treated as the component that answers business questions.

Instead:

```text
Question
   ↓
Retrieve evidence
   ↓
Evidence Set
   ↓
LLM reasoning
   ↓
Answer
```

The reasoning layer may need to interpret the question, compare evidence, perform calculations, reconcile information, and explain the result.

This separation is important for reducing hallucination and numerical reasoning errors.

## 15. PostgreSQL vs Qdrant

PostgreSQL and Qdrant have different responsibilities.

### PostgreSQL

PostgreSQL should remain responsible for **structured business data and application records**, including:

- uploaded report records
- report identifiers
- report types
- processing status
- structured business facts
- transactional data
- relational data
- exact numerical queries

PostgreSQL is appropriate for exact operations such as:

```text
SUM
COUNT
GROUP BY
JOIN
FILTER
```

### Qdrant

Qdrant should be responsible for **unstructured textual evidence and semantic retrieval**, including:

- extracted report text
- textual sections
- document chunks
- semantic vectors
- chunk-level retrieval metadata

The two systems complement rather than replace each other.

## 16. Future Hybrid Retrieval

The proposed architecture will eventually combine:

### Semantic / vector retrieval

```text
Question
  ↓
Embedding
  ↓
Vector similarity
  ↓
Relevant chunks
```

### Metadata filtering

Known business context can restrict retrieval, for example:

```text
report_type = Sales
reporting_period = 2026-Q1
department = Finance
product = Product A
```

### PostgreSQL structured queries

Questions requiring exact structured calculations should use PostgreSQL when appropriate.

For example:

```text
"How much did Product A sell in March?"
```

may require an exact SQL aggregation rather than relying only on semantic retrieval.

Conceptually:

```text
                    User Question
                          ↓
                 Query Understanding
                          ↓
          ┌───────────────┼────────────────┐
          ↓               ↓                ↓
   Vector Retrieval  Metadata Filter  PostgreSQL Query
          │               │                │
          └───────────────┼────────────────┘
                          ↓
                    Evidence Set
```

The exact routing strategy will be designed during implementation.

## 17. Future Query Architecture

```text
User Question
→ Query Understanding
→ Hybrid Retrieval
→ Evidence Set
→ LLM Reasoning
→ Answer + Evidence
```

### Query Understanding

The system will determine what the user is asking and may identify the business domain, report type, reporting period, relevant products/suppliers/customers, and whether structured or semantic retrieval is appropriate.

### Hybrid Retrieval

The system will retrieve information using the appropriate combination of vector similarity, metadata filtering, and PostgreSQL queries.

### Evidence Set

Retrieved information is assembled into an evidence set.

### LLM Reasoning

The LLM uses the evidence set to reason about the question.

### Answer + Evidence

The final response should provide an answer supported by retrieved evidence and, where appropriate, source references.

## 18. Data Responsibility

```text
Structured business facts → PostgreSQL
Unstructured textual evidence → Qdrant
Reasoning → LLM
```

This separation prevents the RAG database from becoming a replacement for the relational database.

## 19. Common Naive RAG Failure Modes

### 19.1 Irrelevant retrieval

Semantically similar information may still be wrong for the question.

Example:

```text
Question:
Sales for Product A in March

Retrieved:
Sales for Product B in March
```

### 19.2 Missing context

A chunk such as:

```text
"Total: 250"
```

is insufficient without knowing the product, period, currency, report, or metric.

### 19.3 Poor chunking

Blind splitting can separate table headers from the rows that give them meaning.

### 19.4 Conflicting reports

A business environment may contain multiple reports with different values, such as an original report, revised report, forecast, or reports from different periods.

### 19.5 Missing evidence

A model may generate an answer even when retrieval did not provide sufficient supporting information.

### 19.6 Numerical reasoning errors

Totals, averages, percentages, comparisons, and financial calculations may require structured queries or explicit calculation rather than model inference.

### 19.7 Hallucination

When evidence is incomplete or ambiguous, an LLM may generate a plausible answer that is not supported by source data.

## 20. How the Proposed Architecture Reduces These Failures

| Failure | Proposed mitigation |
|---|---|
| Irrelevant retrieval | Semantic retrieval combined with metadata filtering |
| Missing context | Preserve source and structural metadata |
| Poor chunking | Structure-aware chunking |
| Conflicting reports | Preserve report type, reporting period, source file, and other context |
| Missing evidence | Treat retrieval as an evidence set and allow insufficient evidence to be detected |
| Numerical reasoning errors | Use PostgreSQL structured queries for appropriate exact calculations |
| Hallucination | Ground LLM reasoning in retrieved evidence and source references |

The architecture does not claim to eliminate these failures. It provides mechanisms intended to reduce their likelihood.

## 21. Conceptual Architecture Diagrams

### A. Ingestion architecture

```text
Business Report
→ Parser
→ Document
→ Chunker
→ Metadata
→ Embedding
→ Qdrant
```

### B. Future query architecture

```text
User Question
→ Query Understanding
→ Hybrid Retrieval
→ Evidence Set
→ LLM Reasoning
→ Answer + Evidence
```

### C. Data responsibility

```text
Structured business facts → PostgreSQL
Unstructured textual evidence → Qdrant
Reasoning → LLM
```

## 22. Proposed Design Principles

1. **Preserve source traceability.** Every retrievable piece of evidence should be traceable to its source.
2. **Preserve business context.** Metadata is part of retrieval quality.
3. **Use structure-aware chunking.** Business tables, sheets, pages, records, and sections have meaning.
4. **Separate retrieval from reasoning.** Qdrant retrieves evidence; the LLM reasons over it.
5. **Use the right database for the right problem.** PostgreSQL handles structured business data; Qdrant handles semantic textual evidence.
6. **Prefer exact structured queries for exact numerical operations.**
7. **Do not assume retrieval equals truth.** Retrieved content still needs contextual interpretation and validation.
8. **Make evidence traceable.** Future answers should be able to point back to relevant source information.
9. **Treat insufficient evidence as a valid state.** The system should not be forced to answer when supporting information is unavailable.
10. **Build incrementally.** RAG components will be implemented only after architecture and data contracts are defined.

## 23. Implementation Boundary for Day 3

This document intentionally does **not** implement:

- Qdrant
- Qdrant collections
- embedding models
- embedding generation
- chunking code
- document parsers
- retrieval APIs
- hybrid retrieval
- LLM reasoning
- RAG orchestration

Day 3 establishes the proposed technical architecture and terminology that future implementation work will follow.

The next implementation phases can use this document as the architectural reference when defining document, chunk, metadata, embedding, and retrieval data contracts.
