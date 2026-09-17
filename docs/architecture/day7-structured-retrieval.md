Current PostgreSQL state
========================

Infrastructure tables:
reports             12
processing_jobs      9

Structured business tables:
companies            0
customers            0
expenses             0
inventory_transactions 0
payables             0
production_items     0
productions          0
products             0
purchase_items       0
purchases            0
receivables          0
sale_items           0
sales                0
suppliers            0

# Day 7 — Structured Business Data Retrieval

## 1. Objective

Day 7 M1 establishes the structured retrieval boundary for the
Business AI / AI Business Investigator.

The purpose of M1 is to allow application code to retrieve structured
business facts from PostgreSQL using deterministic database-level
filters.

This work is intentionally separate from the existing semantic RAG
pipeline.

Day 7 M1 does not implement hybrid retrieval or evidence fusion.


## 2. Current Retrieval Architecture

The application currently has two separate retrieval paths:

                    Query / Criteria
                          |
                 +--------+--------+
                 |                 |
                 v                 v
          Structured           Semantic
          Retrieval            Retrieval
                 |                 |
                 v                 v
        StructuredDataService  RetrievalService
                 |                 |
                 v                 v
            PostgreSQL          BGE-M3
                                   |
                                   v
                                Qdrant

                NOT FUSED IN DAY 7 M1


The semantic path existed before Day 7:

Question
→ RetrievalService
→ BGE-M3 embeddings
→ Qdrant
→ retrieved evidence

Day 7 M1 adds:

StructuredDataFilters
→ StructuredDataService
→ PostgreSQL
→ StructuredDataResult[]

The two paths remain independent.


## 3. PostgreSQL Domain Model

The application already contains a normalized structured business
schema consisting of 16 tables:

1. companies
2. customers
3. expenses
4. inventory_transactions
5. payables
6. processing_jobs
7. production_items
8. productions
9. products
10. purchase_items
11. purchases
12. receivables
13. reports
14. sale_items
15. sales
16. suppliers

The schema represents the target canonical structured business model.

It should not be interpreted as meaning that every uploaded report is
automatically transformed into these tables.


## 4. Actual Database State During Day 7 M1

The PostgreSQL database was inspected before implementing structured
retrieval.

Observed row counts:

| Table | Rows |
|---|---:|
| companies | 0 |
| customers | 0 |
| expenses | 0 |
| inventory_transactions | 0 |
| payables | 0 |
| processing_jobs | 9 |
| production_items | 0 |
| productions | 0 |
| products | 0 |
| purchase_items | 0 |
| purchases | 0 |
| receivables | 0 |
| reports | 12 |
| sale_items | 0 |
| sales | 0 |
| suppliers | 0 |

Only the report-processing infrastructure currently contains real
application data:

- reports: 12 records
- processing_jobs: 9 records

The normalized structured business tables are currently empty.


## 5. Important Data Availability Distinction

The application must distinguish between three states:

1. Structured data exists in PostgreSQL.
2. Information exists only as document/RAG evidence.
3. Information does not exist.

For example, Inventory_transactions.xlsx has been parsed and indexed
through the RAG pipeline.

Its current flow is:

Inventory_transactions.xlsx
→ ExcelParser
→ ParsedRecords
→ DocumentBuilder
→ transaction-level chunks
→ BGE-M3
→ Qdrant

The report currently produces three transaction-level semantic chunks:

- D1IN0818
- D1IN0819
- D1IN0820

Those records have NOT been normalized into the PostgreSQL
inventory_transactions table.

Day 7 M1 intentionally does not introduce an automatic
Excel-to-PostgreSQL ETL pipeline.


## 6. StructuredDataService

Day 7 M1 introduces:

app/structured_data/
├── __init__.py
├── models.py
└── service.py

The service accepts StructuredDataFilters and executes database-level
queries through SQLAlchemy.

Current filter contract:

- start_date
- end_date
- department
- product
- report_type

Filtering is performed by SQL/ORM query conditions.

The service does not load all records and perform filtering in Python.


## 7. Current Structured Query Implementation

The initial implementation queries:

InventoryTransaction
→ Product
→ Report

This provides a clean first structured business retrieval path using
the existing normalized domain model.

The following fields are available through this relationship:

InventoryTransaction:
- transaction_date
- transaction_type
- quantity
- company_id
- report_id
- product_id

Product:
- id
- sku
- name
- category
- unit

Report:
- id
- original_filename
- report_type

The service maps matching database records into
StructuredDataResult objects.


## 8. Current Filter Support

### Date

Supported by the service through:

InventoryTransaction.transaction_date

Supported operators:

transaction_date >= start_date
transaction_date <= end_date


### Product

Supported through:

InventoryTransaction.product_id
→ Product.id
→ Product.name


### Report Type

Supported through:

InventoryTransaction.report_id
→ Report.id
→ Report.report_type


### Department

Department filtering is NOT currently supported.

The existing normalized PostgreSQL schema does not contain a reliable
department dimension for the current structured retrieval path.

If department is supplied, StructuredDataService explicitly rejects
the filter rather than silently ignoring it or returning a misleading
empty result.

No department field was invented for Day 7 M1.


## 9. Current Data Limitation

Although date, product, and report-type filtering are implemented
against the canonical schema, the development PostgreSQL database
currently contains zero InventoryTransaction and Product records.

Therefore a real request such as:

GET /api/business-data?product=Product%20A

currently returns:

[]

This means:

"No matching normalized structured record currently exists in
PostgreSQL."

It does NOT mean:

"The product does not occur in any uploaded report."

Relevant information may currently exist only in Qdrant as semantic
document evidence.


## 10. API Endpoint

Day 7 M1 exposes:

GET /api/business-data

Supported query parameters:

- start_date
- end_date
- department
- product
- report_type

Examples:

GET /api/business-data

GET /api/business-data?product=Product%20A

GET /api/business-data?start_date=2026-01-01&end_date=2026-03-31

GET /api/business-data?report_type=Inventory

Invalid date formats are rejected by FastAPI validation.

A start date later than the end date is rejected with HTTP 422.

Department filtering is explicitly rejected with HTTP 422 because
that dimension is not currently represented in the structured schema.


## 11. Testing Strategy

Structured retrieval is tested independently from the semantic RAG
system.

Service tests use isolated structured test fixtures.

The test data exists only inside the test database and is not inserted
into the application's development PostgreSQL database.

Service tests cover:

- no filters
- date filtering
- product filtering
- date + product filtering
- report type filtering
- no matching records
- invalid date ranges
- unsupported department filtering
- report/source traceability

API tests separately verify:

- HTTP endpoint behavior
- query parameter conversion
- date parsing
- product filtering input
- report type parsing
- invalid date handling
- unsupported department handling
- whitespace normalization

Day 7 M1 test result:

Service tests: 9 passed
API tests: 8 passed

Total: 17 passed


## 12. Test Isolation

Structured retrieval tests do not require:

- Qdrant
- BGE-M3
- embedding generation
- OpenRouter
- external LLM APIs
- semantic RetrievalService

This confirms that StructuredDataService forms an independent
application boundary around PostgreSQL structured retrieval.


## 13. RAG Pipeline Status

The existing RAG pipeline was not modified during Day 7 M1.

It remains:

Question
→ RetrievalService
→ BGE-M3
→ Qdrant

The existing answer path also remains unchanged.

StructuredDataService is not connected to /api/ask.


## 14. Multi-Tenancy

Several structured business tables already contain company_id,
including InventoryTransaction, Product, Sale, Purchase, Production,
Expense, Receivable, and Payable.

However, authenticated tenant/company context is not yet available in
the structured retrieval API.

Day 7 M1 therefore does not invent a partial tenant-security model.

In particular, company_id is not exposed as a user-selectable query
parameter for tenant isolation.

Before multi-company production deployment, structured retrieval must
derive the allowed company scope from authenticated application
context and enforce it in every structured query.


## 15. Intentionally Not Implemented

Day 7 M1 does NOT implement:

- automatic report normalization
- Excel → PostgreSQL ETL
- copying Qdrant chunks into PostgreSQL
- hybrid retrieval
- structured + semantic evidence fusion
- query understanding
- natural-language-to-SQL
- LLM-generated filters
- LLM filtering
- reranking
- agents
- LangChain
- Elasticsearch
- modifications to Qdrant retrieval
- modifications to the existing RAG ingestion pipeline

These exclusions are deliberate.


## 16. Architectural Boundary Established

Day 7 M1 establishes:

Structured criteria
→ StructuredDataService
→ PostgreSQL
→ deterministic structured records

Existing semantic retrieval remains:

Natural-language question
→ RetrievalService
→ BGE-M3
→ Qdrant
→ semantic evidence

PostgreSQL is responsible for exact structured business facts,
filtering, joins, aggregation, calculations, and future business KPIs.

Qdrant is responsible for semantic document evidence and contextual
retrieval.

The LLM will eventually reason over evidence produced by these systems,
but that integration is outside M1.


## 17. Remaining Work

Future work may include:

1. deliberate structured ingestion/normalization for supported report
   formats;
2. population of the canonical business tables;
3. authenticated company/tenant scope;
4. additional structured retrieval domains such as sales, purchases,
   production, expenses, receivables, and payables;
5. additional structured dimensions where supported by the domain
   model;
6. deterministic calculation and aggregation services;
7. query understanding;
8. structured and semantic evidence fusion;
9. integration with the answer-generation pipeline.

These should be implemented incrementally rather than coupling all
retrieval mechanisms at once.


## 18. Day 7 M1 Conclusion

Day 7 M1 successfully establishes a clean structured retrieval
boundary without modifying the existing semantic RAG architecture.

Current production/development data availability remains limited:
the normalized business tables are empty.

That limitation is explicitly preserved rather than hidden by
manufacturing structured data or automatically converting the RAG
test report into canonical PostgreSQL records.

Structured retrieval and semantic retrieval now have clearly defined
responsibilities and can evolve independently before being deliberately
combined in a later milestone.