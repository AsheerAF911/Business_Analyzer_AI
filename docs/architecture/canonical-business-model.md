# Canonical Business Model

## Status

Design only. No database schema changes, data loading, Qdrant changes, `/api/ask` changes, or LLM-based mapping are part of this document.

## 1. Current 16-table schema

The current PostgreSQL business schema consists of:

1. `companies`
2. `customers`
3. `expenses`
4. `inventory_transactions`
5. `payables`
6. `processing_jobs`
7. `production_items`
8. `productions`
9. `products`
10. `purchase_items`
11. `purchases`
12. `receivables`
13. `reports`
14. `sale_items`
15. `sales`
16. `suppliers`

The schema is intended to be a canonical business model, not a mirror of any one source report.

Relevant existing models are `Company`, `Product`, `Supplier`, `Report`, and `InventoryTransaction`.

Current notable constraints:
- `Product` is company-owned and has `sku`, `name`, optional `category`, and optional `unit`.
- `Supplier` is company-owned.
- `InventoryTransaction` is company-owned, linked to `Report` and `Product`, and has transaction date, type, quantity, optional unit cost, `reference_type`, and integer `reference_id`.
- `Report` currently has no `company_id`.
- `InventoryTransaction` currently has no supplier relationship and no source sheet/row provenance.

## 2. Purpose of the canonical schema

PostgreSQL should hold stable, exact, filterable business facts shared across companies and source formats. It should support deterministic filtering, joins, aggregation, KPI calculation, and business analysis.

Qdrant should hold semantic/document evidence and source context.

The same uploaded report may feed both systems independently:

```text
Source Report
    |
    v
  Parser
    |
    v
Parsed Source Records
    |
    +--------------------+
    |                    |
    v                    v
Normalization         RAG Processing
    |                    |
    v                    v
PostgreSQL             Qdrant
```

## 3. Source schema vs canonical schema

Source schemas describe how one report happens to encode data:

```text
Company A:
Barcode | Product Name | Qty Received | Date | Supplier | GRN No

Company B:
Item Code | Material Description | Inward Qty |
Posting Date | Vendor | Receipt No

Company C:
SKU | Description | Quantity | Transaction Date |
Party | Document Number
```

The canonical model should instead represent concepts such as:
- company
- product identifier
- product
- supplier
- transaction date
- quantity
- unit of measure
- transaction type
- business reference
- source report
- source record provenance

It should not contain source-specific columns merely because one workbook uses names such as `INWARD NO`, `VENDOR NAME`, `PRODUCTION`, or `INV/DO`.

## 4. Proposed canonical inventory concepts

### Company ownership

Purpose: identify which tenant owns the report and normalized facts.

Why source-independent: all canonical records belong to a company regardless of report format.

Source: authenticated/current company context, not spreadsheet inference.

Recommendation: required.

### Product

Purpose: identify the stock item affected by a transaction.

Why source-independent: systems may call it Product, Material, Item, SKU, etc.

Possible source fields:
- Barcode
- SKU
- Item Code
- Material Code
- Product Code

Recommendation: required. The current `Product.sku` can serve as the MVP identifier, while a more flexible external-identifier model may be needed later.

### Supplier / counterparty

Purpose: identify the supplier associated with supplier-related inventory movements.

Why source-independent: source systems may use Supplier, Vendor, Vendor Name, or Party.

Recommendation: optional relationship on inventory transactions, because transfers, adjustments, wastage, and production movements may have no supplier.

### Transaction date

Purpose: identify when the inventory event occurred.

Possible source fields:
- Date
- Posting Date
- Transaction Date
- Receipt Date

Recommendation: required.

### Quantity

Purpose: represent the magnitude of the inventory movement.

Possible source fields:
- Qty Received
- Inward Qty
- Quantity
- Movement Qty
- Issued Qty

Recommendation: required.

The canonical model should consistently use either signed quantity or positive quantity plus transaction type. The current model uses quantity plus transaction type.

### Unit of measure

Purpose: make quantity unambiguous.

Possible source fields:
- UOM
- Unit
- Quantity Unit
- KG
- PCS

Recommendation: likely required at transaction level. `Product.unit` alone may be insufficient because a report can express a transaction in a different unit than the product master.

### Transaction type

Purpose: describe the inventory event such as receipt, sale, transfer, adjustment, production, wastage, or return.

Recommendation: required. The existing enum is a reasonable starting point.

### Business reference

Purpose: preserve a source-system or business document identifier such as GRN, receipt number, movement number, or document number.

Possible source fields:
- INWARD NO
- GRN No
- Receipt No
- Document Number
- Movement No

Recommendation: optional string concept. The current integer `reference_id` is not sufficient for general alphanumeric business references.

### Source report

Purpose: identify which uploaded report produced the canonical record.

Recommendation: required and already represented by `InventoryTransaction.report_id`.

### Source record provenance

Purpose: trace a canonical fact to the exact source location.

Possible source locators:
- Excel sheet + row
- CSV row
- PDF page + table row
- external source record key

Recommendation: required conceptually, but should not be implemented as Excel-specific columns on every business table.

A reusable provenance model is preferable.

## 5. Multi-company ownership model

Target architecture:

```text
Authenticated User / Workspace
          |
          v
Current Company Context
          |
          v
       Report
      company_id
          |
          v
NormalizationContext
          |
          v
Canonical business records
```

The current upload flow does not supply company context, so structured normalization should not manufacture one.

Temporary boundary:

```python
class NormalizationContext:
    company_id: int
```

Until a legitimate company ID is supplied, structured normalization should not persist canonical business data. RAG may continue independently.

## 6. Source-to-canonical normalization architecture

The parser remains source-format-oriented:

```text
XLSX / CSV / PDF
      |
      v
    Parser
      |
      v
ParsedRecord
```

Normalization becomes domain-oriented:

```text
ParsedRecord
      |
      v
Source Mapping Profile
      |
      v
Canonical Concept Mapping
      |
      v
Transformation
      |
      v
Validation
      |
      v
Canonical Draft
```

Suggested interfaces:

```python
CanonicalConcept
MappingConfidence
FieldMappingRule
MappingProfile
MappingResult
NormalizationContext
InventoryReportNormalizer
```

Example canonical concepts:

```python
PRODUCT_IDENTIFIER
PRODUCT_NAME
SUPPLIER
TRANSACTION_DATE
QUANTITY
UNIT_OF_MEASURE
TRANSACTION_TYPE
BUSINESS_REFERENCE
```

Mapping profiles should support aliases rather than one exact column name.

Example:

```text
["Vendor Name", "Supplier", "Vendor"]
    -> SUPPLIER
```

## 7. Mapping confidence model

Recommended deterministic states:

### AUTO_MAPPED
Explicit, trusted mapping supported by a known profile.

Examples:
- `Supplier` -> supplier
- `Vendor Name` -> supplier
- `SKU` -> product identifier
- `Transaction Date` -> transaction date

### REVIEW_REQUIRED
Plausible but ambiguous.

Examples:
- `Party` -> supplier?
- `Date` -> transaction date?
- `Quantity` -> movement quantity?
- `Reference` -> business reference?

### UNMAPPED
No reliable canonical meaning.

Examples:
- `Production`
- `Misc Ref`
- unknown local codes

Recommended MVP persistence policy:

```text
AUTO_MAPPED     -> eligible for persistence
REVIEW_REQUIRED -> do not persist until approved
UNMAPPED        -> retain only as source/provenance information
```

This confidence is about deterministic schema mapping, not vector similarity or LLM confidence.

## 8. Traceability model

Minimum traceability:

```text
Canonical Inventory Transaction
            |
            v
          Report
            |
            v
       Source Record
            |
            +--> source file
            +--> source sheet/page
            +--> source row/record
```

The current parser already preserves source file, sheet, row number, and raw fields.

Current schema supports report-level traceability through `report_id`.

Current gap: no reusable source-record provenance entity.

Recommendation: design a reusable provenance/source-record model rather than adding `excel_sheet` and `excel_row` directly to canonical domain tables.

## 9. Example mappings for three inventory formats

### Company A

```text
Barcode | Product Name | Qty Received | Date | Supplier | GRN No
```

| Source | Canonical concept | Confidence |
|---|---|---|
| Barcode | product_identifier | AUTO_MAPPED |
| Product Name | product_name | AUTO_MAPPED |
| Qty Received | quantity | AUTO_MAPPED if profile establishes receipt semantics |
| Date | transaction_date | REVIEW_REQUIRED unless profile defines it |
| Supplier | supplier | AUTO_MAPPED |
| GRN No | business_reference | AUTO_MAPPED |

Profile-level value:
`transaction_type = RECEIPT`

### Company B

```text
Item Code | Material Description | Inward Qty |
Posting Date | Vendor | Receipt No
```

| Source | Canonical concept | Confidence |
|---|---|---|
| Item Code | product_identifier | AUTO_MAPPED |
| Material Description | product_name | AUTO_MAPPED |
| Inward Qty | quantity | AUTO_MAPPED |
| Posting Date | transaction_date | AUTO_MAPPED |
| Vendor | supplier | AUTO_MAPPED |
| Receipt No | business_reference | AUTO_MAPPED |

Profile-level value:
`transaction_type = RECEIPT`

### Company C

```text
SKU | Description | Quantity | Transaction Date |
Party | Document Number
```

| Source | Canonical concept | Confidence |
|---|---|---|
| SKU | product_identifier | AUTO_MAPPED |
| Description | product_name | AUTO_MAPPED |
| Quantity | quantity | REVIEW_REQUIRED |
| Transaction Date | transaction_date | AUTO_MAPPED |
| Party | supplier | REVIEW_REQUIRED |
| Document Number | business_reference | AUTO_MAPPED |

This report should not persist ambiguous mappings until approved.

## 10. Current `Inventory_transactions.xlsx` as an example

Observed fields include:
- `DATE`
- `INWARD NO`
- `BARCODE`
- `PRODUCT DESCRIPTION`
- `PACKAGING SIZE (KG)`
- `QUANTITY RECEIVED (NO. OF PCS.)`
- `TOTAL QUANTITY RECEIVED (KG)`
- `NET STOCK QTY`
- `INV/DO`
- `VENDOR NAME`
- `INVOICE`
- `PRODUCTION`

Proposed conceptual mapping:

| Source field | Canonical concept | Confidence |
|---|---|---|
| BARCODE | product_identifier | AUTO_MAPPED |
| PRODUCT DESCRIPTION | product_name | AUTO_MAPPED |
| VENDOR NAME | supplier | AUTO_MAPPED |
| INWARD NO | business_reference | AUTO_MAPPED |
| DATE | transaction_date | REVIEW_REQUIRED at alias level; profile can approve |
| TOTAL QUANTITY RECEIVED (KG) | quantity | AUTO_MAPPED for this approved profile |
| report semantics | transaction_type=RECEIPT | profile-level |
| source file/sheet/row | provenance | AUTO_MAPPED |

No PostgreSQL insertion should occur until company context and the canonical schema are approved.

## 11. Fields that remain unmapped

### `PRODUCTION`
Semantics are unclear. It may be a department, facility, production line, source code, or another concept.

### `INV/DO`
Meaning is insufficiently established.

### `NET STOCK QTY`
Likely a stock balance rather than a movement quantity. Balance and movement are different canonical concepts.

### `PACKAGING SIZE (KG)`
May be conversion/packaging metadata rather than transaction unit.

### `QUANTITY RECEIVED (NO. OF PCS.)`
Potentially a second quantity in another unit. The canonical model must first define how multi-unit quantities and conversions are represented.

### `INVOICE`
Potentially another business-document reference, but it should not be forced into the inventory model until document-reference semantics are designed consistently across domains.

## 12. Schema changes that appear necessary

Proposals for review only:

### `Report.company_id`
Likely required for tenant ownership and inheritance of company context into normalized records.

### Canonical string business reference on `InventoryTransaction`
Likely required because external business references are often alphanumeric. Exact naming should be source-independent, e.g. `business_reference` or `external_reference`.

### Optional `InventoryTransaction.supplier_id`
Likely required for supplier-linked movements while remaining nullable for non-supplier movements.

### Transaction-level unit of measure
Likely required; exact representation should be decided later.

### Reusable source provenance model
Likely required for source file/sheet/row/record traceability and robust idempotency.

## 13. Schema changes that should NOT be made

Do not create source-specific columns such as:

```text
inward_no
vendor_name
production
inv_do
packaging_size_kg
qty_received_pcs
net_stock_qty
```

Do not:
- mirror one workbook into the canonical schema;
- add a column for every source field;
- hardcode `company_id`;
- make supplier mandatory for all inventory movements;
- assume every inventory report is a receipt report;
- treat source column names as canonical semantics;
- place Excel-specific traceability fields directly on every domain table.

A source field must either:
1. map to an approved canonical concept;
2. be retained as source/provenance data;
3. remain unmapped.

## 14. Future extension to other domains

The normalization architecture should support:

```text
ParsedRecord
    |
    +--> InventoryReportNormalizer
    +--> PurchaseReportNormalizer
    +--> SalesReportNormalizer
    +--> ProductionReportNormalizer
    +--> ExpenseReportNormalizer
    +--> ReceivableReportNormalizer
    +--> PayableReportNormalizer
```

Each normalizer should:
1. receive source records and company/normalization context;
2. apply a mapping profile;
3. produce canonical drafts;
4. validate required concepts;
5. return mapping diagnostics;
6. leave persistence to a separate service.

Suggested conceptual abstraction:

```python
class ReportNormalizer(Protocol):
    def normalize(
        self,
        records,
        context,
        mapping_profile,
    ):
        ...
```

## Review decisions required before implementation

Before altering schema or loading data, decide:

1. Should `Report` become company-owned through `company_id`?
2. What canonical name should represent an external/business reference?
3. Should `InventoryTransaction` have optional `supplier_id`?
4. How should transaction-level unit of measure be modeled?
5. Should provenance use a reusable `source_records` model?
6. Should `Product.sku` remain the MVP product identifier?
7. How should mapping profiles be stored initially?
8. Which mapping-confidence states are allowed to persist automatically?

No database schema should be changed until these decisions are reviewed and approved.
