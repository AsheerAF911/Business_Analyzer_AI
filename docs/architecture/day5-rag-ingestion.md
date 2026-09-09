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

## Embedding Layer

### What is an embedding?

An embedding is a numeric vector representation of text.

Texts with related semantic meaning can be represented in a
shared vector space.

For the current RAG ingestion pipeline, embeddings are generated
from Chunk.text.

The embedding is not a replacement for the original chunk.

The Chunk continues to preserve:

- chunk_id
- text
- metadata
- source traceability

The vector is an additional representation used by future
retrieval infrastructure.

---

## Current RAG Preparation Flow

Source Report
→ ParsedRecord
→ Document
→ Chunk
→ Embedding

The vector database is not part of this stage.

---

## BGE-M3

The MVP embedding model is:

BAAI/bge-m3

It runs locally through Sentence Transformers.

No external embedding API is used.

The expected dense embedding dimension is:

1024

Example:

D1IN0818 transaction chunk
→ BGE-M3
→ 1024-dimensional dense vector

---

## EmbeddingService

Application code does not directly depend on BGE-M3.

The abstraction is:

EmbeddingService

It supports:

- embedding one text
- embedding multiple texts as a batch

The current implementation is:

BGEM3EmbeddingService

This allows another embedding implementation to be introduced
later without rewriting the document or chunking layers.

---

## Batch Embedding

Chunks are embedded in batches.

For the current inventory example:

3 Chunks
→ one batch embedding call
→ 3 vectors

The ordering is preserved:

chunks[0] → embeddings[0]
chunks[1] → embeddings[1]
chunks[2] → embeddings[2]

---

## Local Model Loading

The first BGE-M3 execution may download model files from
Hugging Face.

The files are stored in the Hugging Face local model cache.

Later executions can reuse the locally cached model.

Downloaded model files must not be committed into Git.

The BGEM3EmbeddingService loads its model lazily and reuses the
loaded model for subsequent calls on the same service instance.

---

## Embeddings vs Qdrant

Embedding generation and vector storage are separate
responsibilities.

EmbeddingService is responsible for:

Chunk text
→ numeric vector

Future Qdrant integration will be responsible for storing:

- chunk identity
- vector
- metadata
- source attribution

This separation allows embedding generation to be tested before
introducing persistent vector infrastructure.

---

## Not Implemented

This stage does not implement:

- Qdrant
- semantic retrieval
- similarity search
- reranking
- LLM reasoning
- answer generation
- PostgreSQL vector storage

---

## Next Step

After embedding generation is validated:

Chunk
→ Embedding
→ Qdrant

Qdrant integration should preserve the relationship between:

- document_id
- chunk_id
- vector
- metadata
- source evidence

## Qdrant Vector Storage

### Current pipeline

ParsedRecord
→ Document
→ Chunk
→ BGE-M3 Embedding
→ Qdrant Point

Qdrant is introduced only as the persistent vector store.

Semantic retrieval is not implemented in this stage.

---

## Why Qdrant

Qdrant stores vector representations together with payload data.

For the Business AI RAG pipeline, one Chunk corresponds to one
Qdrant point.

Each point contains:

- deterministic point ID
- 1024-dimensional dense vector
- original chunk text
- chunk metadata

---

## Vector vs Payload

The vector is the BGE-M3 numeric representation of Chunk.text.

The payload contains the evidence required after future
retrieval:

- chunk_id
- text
- metadata

The vector answers:

"Which chunks are mathematically similar?"

The payload answers:

"What evidence did this vector represent?"

---

## Why Chunk Text Is Stored

An embedding is not readable business evidence.

After future retrieval, the system needs the original Chunk.text
for reasoning and answer generation.

Therefore Qdrant stores both:

vector + original chunk text

---

## Why Metadata Is Stored

Metadata preserves source traceability.

Examples include:

- source_file
- report_type
- sheet
- source_rows
- transaction_number
- supplier
- date

Metadata is copied from Chunk.metadata without inventing new
business meanings.

---

## Collection Configuration

Current collection:

business_ai_rag

Dense vector dimension:

1024

Distance:

COSINE

The dimension corresponds to the dense vector output of the
current BGE-M3 EmbeddingService.

The Qdrant service validates existing collection configuration
rather than silently accepting a different vector dimension.

---

## Why Cosine Distance

The current dense embedding collection uses cosine distance.

Cosine comparison measures the directional similarity between
embedding vectors and is appropriate for comparing semantic
representations generated by the same embedding model.

---

## Idempotent Chunk Storage

Qdrant point IDs support integer or UUID identifiers.

Business chunk IDs are therefore deterministically mapped to
UUID5 point IDs.

Conceptually:

chunk_id
→ deterministic UUID
→ Qdrant point ID

The same chunk_id always produces the same Qdrant point ID.

Repeated ingestion therefore performs an upsert on the existing
logical point instead of creating a duplicate.

The original human-readable chunk_id remains stored in payload.

---

## Local Qdrant

Qdrant runs locally using Docker.

REST:
http://localhost:6333

Dashboard:
http://localhost:6333/dashboard

Environment configuration:

QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=business_ai_rag

Qdrant storage is kept outside Git.

---

## Not Implemented

This stage does not implement:

- semantic search
- similarity retrieval
- query embeddings
- reranking
- LLM reasoning
- answer generation
- PostgreSQL business normalization

---

## Next Step

After storage is validated, the future retrieval pipeline will
be:

Question
→ BGE-M3 query embedding
→ Qdrant similarity search
→ Retrieved evidence chunks
→ LLM reasoning

That work is intentionally outside the current Qdrant storage
stage.


## Semantic Retrieval

### Completed Pipeline

ParsedRecord
→ Document
→ Chunk
→ BGE-M3 Embedding
→ Qdrant Point

At query time:

Question
→ BGE-M3 Query Embedding
→ Query Vector
→ Qdrant Cosine Similarity
→ Top-K Chunks
→ Retrieved Evidence

No LLM reasoning is performed at this stage.

---

## Stored Embedding vs Query Embedding

A stored embedding represents an existing Chunk.

Example:

D1IN0818 Chunk
→ BGE-M3
→ 1024-dimensional vector
→ Qdrant

A query embedding represents the user's question.

Example:

"Which products were received under D1IN0818?"
→ BGE-M3
→ 1024-dimensional query vector

Both use the same EmbeddingService and embedding model.

Qdrant compares the query vector against stored chunk vectors and
returns the closest points according to cosine similarity.

---

## RetrievalResult

The retrieval layer converts Qdrant search results into an
application-level RetrievalResult.

Each result contains:

- chunk_id
- similarity score
- chunk text
- original metadata

This prevents the rest of the application from depending directly
on Qdrant SDK response objects.

---

## Top-K Retrieval

The retrieval layer supports top_k.

Example:

top_k = 3

returns up to the three highest-ranked chunks.

Qdrant determines their ordering according to vector similarity.

---

## Semantic Retrieval Is Not Answer Generation

Semantic retrieval does not mean the system understands or answers
the user's question.

It identifies stored chunks whose vector representations are
similar to the query vector.

The output of this stage is evidence, not an answer.

Future LLM reasoning may consume retrieved evidence, but LLM
integration is outside this stage.

---

## Evidence Limitation

A highly similar chunk does not necessarily contain sufficient
evidence to answer a question.

For example:

"Which supplier has the highest inventory value?"

cannot be answered reliably when the available source data does
not contain the required inventory valuation or unit-cost facts.

Retrieval can identify potentially relevant evidence, but it must
not invent missing business data.

---

## Date Normalization

Current metadata may still contain raw Excel date values such as:

date = 46143

Date normalization belongs to a separate normalization stage and
is intentionally not addressed during semantic retrieval.

---

## Current Retrieval Scope

Implemented:

Question
→ Embedding
→ Qdrant
→ Ranked Evidence

Not implemented:

- LLM reasoning
- answer generation
- reranking
- business calculations
- forecasting
- recommendations
- citation UI