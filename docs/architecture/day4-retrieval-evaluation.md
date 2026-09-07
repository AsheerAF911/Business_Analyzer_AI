# Day 4 — Retrieval Evaluation: Inventory Chunking Experiment

## Purpose

This document evaluates the first Day 4 RAG preprocessing experiment using the real `Inventory_transactions.xlsx` report and the generated `inventory_chunks.json`.

The current chunking strategy is intentionally unchanged:

> **1 meaningful Excel row = 1 chunk**

This evaluation does **not** introduce embeddings, Qdrant, semantic search, an LLM, or a new chunking strategy.

The purpose is to test whether the current row-level chunks contain enough useful business context to support realistic retrieval questions.

---

# 1. Source report observations

The workbook contains one sheet:

- **Sheet:** `Sheet1`
- **Data rows:** 13 data rows, Excel rows 2–14
- **Header row:** Excel row 1
- **Columns:** 25 named columns plus an empty trailing column

The important populated fields in the supplied sample include:

- `PRODUCTION`
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

Many other columns are empty in this sample, including fields such as batch number, brand name, shortage, delivery number, QCR number, invoice/delivery date, expiry date, and ERP receipt number.

The rows behave like item-level inventory records: a single inward number can occur on several rows, with each row describing a product and its received quantity.

For example:

- `D1IN0818` appears on rows 2–5.
- `D1IN0819` appears on row 6.
- `D1IN0820` appears on rows 7–14.

The generated chunks preserve this row-level structure.

---

# 2. Evaluation methodology

Each question below is evaluated against the current generated chunks.

The evaluation asks:

1. Which chunks should retrieval return?
2. Which source Excel rows do those chunks represent?
3. Is one chunk enough, or are multiple chunks needed?
4. Can the answer be obtained directly from the retrieved evidence?
5. Would deterministic SQL/Python calculation eventually be required?
6. Is the question ambiguous?

"Directly from retrieved evidence" means that the required fact is already stated in the retrieved chunk text and does not require arithmetic or combining values.

"Deterministic calculation required" means retrieval can supply the evidence, but a later calculation layer should perform the arithmetic rather than relying on an LLM to calculate it.

---

# 3. Ten realistic retrieval questions

## Question 1 — Single-chunk lookup

**Question**

> What product was received under inward number `D1IN0818` with barcode `30955`, and how much was received?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-2`

**Source rows**

- Excel row 2

**One or multiple chunks?**

- One chunk.

**Can the answer be obtained directly from retrieved evidence?**

- Yes. The chunk contains the inward number, barcode, product description, packaging size, quantity received, total quantity received, and net stock quantity.

**Would deterministic SQL/Python calculation eventually be required?**

- No.

**Ambiguity**

- Low. The barcode and inward number identify a single row in this sample.

---

## Question 2 — Multiple chunks from the same transaction

**Question**

> What products and quantities were included in inward number `D1IN0820`?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-7`
- `Inventory_transactions-Sheet1-8`
- `Inventory_transactions-Sheet1-9`
- `Inventory_transactions-Sheet1-10`
- `Inventory_transactions-Sheet1-11`
- `Inventory_transactions-Sheet1-12`
- `Inventory_transactions-Sheet1-13`
- `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 7–14

**One or multiple chunks?**

- Multiple chunks: 8.

**Can the answer be obtained directly from retrieved evidence?**

- Yes, if all eight relevant chunks are retrieved. Each chunk supplies one product and its quantities.

**Would deterministic SQL/Python calculation eventually be required?**

- Not if the question only asks for the list of products and their individual quantities.
- Yes if the user additionally asks for a combined total.

**Ambiguity**

- "Quantities" could mean pieces, total kilograms, or net stock quantity. The report contains all of these concepts, so a production system should clarify the requested unit or return both relevant quantity measures.

---

## Question 3 — Product filtering

**Question**

> What inventory record do we have for `RM_CUMIN POWDER_5390360622017`?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-8`

**Source rows**

- Excel row 8

**One or multiple chunks?**

- One chunk.

**Can the answer be obtained directly from retrieved evidence?**

- Yes. The chunk contains the product, barcode, inward number, date, production field, vendor-name field, packaging size, quantity, total quantity, net stock quantity, document type, and invoice.

**Would deterministic SQL/Python calculation eventually be required?**

- No for a direct record lookup.

**Ambiguity**

- Low for this sample because the product appears once.

---

## Question 4 — Barcode filtering

**Question**

> Which product has barcode `2017`, and how much was received?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-9`

**Source rows**

- Excel row 9

**One or multiple chunks?**

- One chunk.

**Can the answer be obtained directly from retrieved evidence?**

- Yes.

**Would deterministic SQL/Python calculation eventually be required?**

- No.

**Ambiguity**

- Low in this sample. The barcode `2017` occurs once.

---

## Question 5 — Date filtering

**Question**

> What inventory transactions were recorded on `2026-05-01`?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-2`
- `Inventory_transactions-Sheet1-3`
- `Inventory_transactions-Sheet1-4`
- `Inventory_transactions-Sheet1-5`
- `Inventory_transactions-Sheet1-6`
- `Inventory_transactions-Sheet1-7`
- `Inventory_transactions-Sheet1-8`
- `Inventory_transactions-Sheet1-9`
- `Inventory_transactions-Sheet1-10`
- `Inventory_transactions-Sheet1-11`
- `Inventory_transactions-Sheet1-12`
- `Inventory_transactions-Sheet1-13`
- `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 2–14

**One or multiple chunks?**

- Multiple chunks: all 13 data rows in this report.

**Can the answer be obtained directly from retrieved evidence?**

- Yes for identifying the records.
- The current sample contains the same date on every data row.

**Would deterministic SQL/Python calculation eventually be required?**

- Not for listing the transactions.
- Yes if the user asks for a total or other aggregation.

**Ambiguity**

- "Transactions" could mean individual product rows or unique inward numbers. The current report contains 13 item rows but only three distinct inward numbers.

---

## Question 6 — Vendor/source filtering

**Question**

> Which products are associated with vendor name `D1`?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-2`
- `Inventory_transactions-Sheet1-3`
- `Inventory_transactions-Sheet1-4`
- `Inventory_transactions-Sheet1-5`
- `Inventory_transactions-Sheet1-7`
- `Inventory_transactions-Sheet1-8`
- `Inventory_transactions-Sheet1-9`
- `Inventory_transactions-Sheet1-10`
- `Inventory_transactions-Sheet1-11`
- `Inventory_transactions-Sheet1-12`
- `Inventory_transactions-Sheet1-13`
- `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 2–5 and 7–14

**One or multiple chunks?**

- Multiple chunks: 12.

**Can the answer be obtained directly from retrieved evidence?**

- Yes for listing the products associated with the value `D1` in the `VENDOR NAME` column.

**Would deterministic SQL/Python calculation eventually be required?**

- No for listing.
- Yes if the user asks for a total quantity for this vendor.

**Ambiguity**

- The generated metadata calls this field `vendor`, which is strongly supported by the original column name `VENDOR NAME`.
- However, the processor also uses the phrase `vendor/source`. There is no separate `SOURCE` column in the report. Therefore, "source" should not be treated as an independently established business field.

---

## Question 7 — Location/production filtering

**Question**

> Which inventory records have `D17` in the `PRODUCTION` field?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-2`
- `Inventory_transactions-Sheet1-3`
- `Inventory_transactions-Sheet1-4`
- `Inventory_transactions-Sheet1-5`
- `Inventory_transactions-Sheet1-7`
- `Inventory_transactions-Sheet1-8`
- `Inventory_transactions-Sheet1-9`
- `Inventory_transactions-Sheet1-10`
- `Inventory_transactions-Sheet1-11`
- `Inventory_transactions-Sheet1-12`
- `Inventory_transactions-Sheet1-13`
- `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 2–5 and 7–14

**One or multiple chunks?**

- Multiple chunks: 12.

**Can the answer be obtained directly from retrieved evidence?**

- Yes, for filtering on the literal value `D17` in the `PRODUCTION` field.

**Would deterministic SQL/Python calculation eventually be required?**

- No for listing/filtering.

**Ambiguity**

- **Important.** The source column is explicitly named `PRODUCTION`. The generated text says `Production/location`, which introduces an interpretation that the value is a location.
- `D17` may represent a production area, production unit, facility, or location, but the report itself does not establish that exact meaning.
- For future processing, the raw source label `PRODUCTION` should be preserved rather than confidently renaming it to "location" unless the business definition is known.

---

## Question 8 — Aggregation across multiple records

**Question**

> What was the total quantity received in kilograms across all inventory rows in this report?

**Expected relevant chunk IDs**

- `Inventory_transactions-Sheet1-2` through `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 2–14

**One or multiple chunks?**

- Multiple chunks: 13.

**Can the answer be obtained directly from retrieved evidence?**

- No. The individual `TOTAL QUANTITY RECEIVED (KG)` values are present, but they must be added together.

**Would deterministic SQL/Python calculation eventually be required?**

- **Yes.**
- Retrieval should identify the relevant records.
- A deterministic calculation layer should sum the retrieved `TOTAL QUANTITY RECEIVED (KG)` values.

**Ambiguity**

- Low if "total quantity received" explicitly means the report's `TOTAL QUANTITY RECEIVED (KG)` field.
- The resulting total from the supplied rows is **21,405 kg**.

---

## Question 9 — Comparison between transactions

**Question**

> How does the total quantity received for inward `D1IN0818` compare with inward `D1IN0820`?

**Expected relevant chunk IDs**

For `D1IN0818`:

- `Inventory_transactions-Sheet1-2`
- `Inventory_transactions-Sheet1-3`
- `Inventory_transactions-Sheet1-4`
- `Inventory_transactions-Sheet1-5`

For `D1IN0820`:

- `Inventory_transactions-Sheet1-7`
- `Inventory_transactions-Sheet1-8`
- `Inventory_transactions-Sheet1-9`
- `Inventory_transactions-Sheet1-10`
- `Inventory_transactions-Sheet1-11`
- `Inventory_transactions-Sheet1-12`
- `Inventory_transactions-Sheet1-13`
- `Inventory_transactions-Sheet1-14`

**Source rows**

- Excel rows 2–5 and 7–14

**One or multiple chunks?**

- Multiple chunks: 12.

**Can the answer be obtained directly from retrieved evidence?**

- No. The relevant values must be aggregated for each inward number and then compared.

**Would deterministic SQL/Python calculation eventually be required?**

- **Yes.**

**Ambiguity**

- "Total quantity" should refer to `TOTAL QUANTITY RECEIVED (KG)` for a precise comparison.
- Based on the supplied data:
  - `D1IN0818` = **10,170 kg**
  - `D1IN0820` = **8,235 kg**
  - Difference = **1,935 kg**
  - `D1IN0818` is therefore higher by 1,935 kg.

---

## Question 10 — Insufficient evidence

**Question**

> Which vendor supplied the greatest inventory value in this report?

**Expected relevant chunk IDs**

- Retrieval could identify chunks using the vendor field, but **no set of chunks can provide the requested inventory value**.

**Source rows**

- Potentially rows 2–14.

**One or multiple chunks?**

- Multiple records would be relevant, but the report does not contain the required monetary evidence.

**Can the answer be obtained directly from retrieved evidence?**

- **No.**

**Would deterministic SQL/Python calculation eventually be required?**

- A calculation would be required if a monetary value existed.
- In this report, even deterministic calculation is insufficient because there is no unit cost, purchase price, or inventory value field.

**Ambiguity**

- "Inventory value" is not represented by any populated column in the supplied report.
- The report contains quantities, but quantity cannot establish monetary value without a price/cost.
- Therefore the correct future AI behavior should be to say that the report does not contain enough evidence rather than inventing a value or inferring one.

---

# 4. Metadata semantic assumptions

The experiment revealed several places where the generated representation is slightly more interpretive than the source data.

## `vendor`

The original Excel column is:

```text
VENDOR NAME
```

Therefore, treating this field as a **vendor name** is supported by the source report.

The generated metadata:

```json
"vendor": "D1"
```

is reasonable.

However, `D1` itself is only the value appearing under `VENDOR NAME`. The report does not provide additional information explaining what entity `D1` represents.

So:

- **"vendor" as the field meaning:** supported.
- **What "D1" specifically represents:** not established by this report alone.

## `source`

The generated text currently says:

```text
Vendor/source: D1.
```

This is potentially misleading.

The source workbook has a `VENDOR NAME` column, but no separate `SOURCE` column in the supplied headers.

Therefore:

> `source` is **not** an independently established business meaning in this report.

It should not be treated as equivalent to a formally defined "source" field.

## `production/location`

The original column is:

```text
PRODUCTION
```

The generated text currently says:

```text
Production/location: D17.
```

This is useful as a cautious description, but it still introduces an interpretation.

The data establishes:

```text
PRODUCTION = D17
```

It does **not** establish:

```text
D17 = warehouse location
```

or

```text
D17 = facility
```

or any other exact location semantics.

Therefore, future representations should preferably preserve the source terminology:

```text
Production: D17.
```

unless the business meaning is confirmed separately.

---

# 5. Lessons from the first chunking experiment

## Strengths of row-level chunks

### 1. Precise source traceability

Every chunk maps directly to an Excel row.

For example:

```text
Inventory_transactions.xlsx
→ Sheet1
→ Row 8
```

This is excellent for future evidence citation.

### 2. Good for exact lookups

Questions involving:

- barcode
- product
- inward number + product
- a particular inventory row

can often be answered from a single chunk.

### 3. Natural business boundaries

An inventory item row already represents a meaningful business record. Splitting it arbitrarily by character count would destroy relationships between product, quantity, inward number, and other fields.

### 4. Simple retrieval unit

The current design makes it easy to understand exactly what a retrieved result represents.

---

# 6. Weaknesses of row-level chunks

## 1. Transaction context is distributed

`D1IN0820` is one inward number but spans eight chunks.

A question about the entire inward therefore requires retrieving eight separate chunks.

## 2. Aggregations require multiple records

Questions such as:

> "How much was received in total?"

cannot be answered by one chunk.

Retrieval can locate the evidence, but a deterministic calculation layer must combine the numbers.

## 3. Comparisons require coordinated retrieval

A comparison between two inward numbers requires two groups of chunks to be retrieved and then calculated.

## 4. Repeated metadata consumes context

Every row repeats values such as date, production, vendor, and inward number.

That is acceptable for this experiment, but a future transaction-level representation could reduce repeated context for questions concerning an entire transaction.

---

# 7. Questions requiring multiple chunks

The evaluation shows that row-level chunks work particularly well for:

```text
Single row
    ↓
Single chunk
    ↓
Direct answer
```

But transaction-level questions become:

```text
One transaction
    ↓
Many row chunks
    ↓
Retrieve all related rows
    ↓
Combine evidence
```

The strongest example is `D1IN0820`, which spans eight rows.

This does not mean row-level chunking is wrong.

It means that **chunking is a retrieval design decision**.

The correct chunk size depends on the kinds of questions the system must answer.

---

# 8. Questions requiring calculations

Two clear categories require deterministic calculation:

### Aggregation

Example:

> What was the total quantity received?

Retrieval provides the numbers.

A calculation layer performs:

```text
sum(quantity)
```

### Comparison

Example:

> How does D1IN0818 compare with D1IN0820?

Retrieval provides the records.

A calculation layer performs:

```text
total_0818
vs
total_0820
difference
```

This separation is important:

```text
Retrieval
    ↓
Find the correct evidence

Deterministic calculation
    ↓
Compute the answer

LLM
    ↓
Explain the result
```

The LLM should not be treated as the authoritative calculator for business totals.

---

# 9. Possible future transaction-level chunking experiment

Do **not** implement this yet.

A future experiment could group all rows sharing the same inward number:

```text
D1IN0818
    ├── Row 2
    ├── Row 3
    ├── Row 4
    └── Row 5

D1IN0819
    └── Row 6

D1IN0820
    ├── Row 7
    ├── Row 8
    ├── Row 9
    ├── Row 10
    ├── Row 11
    ├── Row 12
    ├── Row 13
    └── Row 14
```

The resulting transaction-level chunk could contain:

```text
Inward D1IN0820
Date: 2026-05-01
Production: D17
Vendor name: D1
Invoice: DD09886

Items:
- Coriander powder — 2,120 kg
- Cumin powder — 1,360 kg
- Turmeric powder — 1,960 kg
...
```

The important point is that this should be tested **against the same evaluation questions**.

We should compare:

```text
Row-level chunks
        vs
Transaction-level chunks
```

based on:

- retrieval precision
- retrieval completeness
- source traceability
- context size
- ability to answer transaction-level questions
- ability to answer product-level questions

Only after this experiment should we decide whether transaction-level grouping is actually better.

---

# 10. Conclusion

The first experiment shows that **one meaningful inventory row = one chunk is a valid baseline**.

It performs well for precise record retrieval and gives excellent row-level traceability.

Its main weakness appears when a business question crosses row boundaries:

- complete inward/transaction questions
- aggregations
- comparisons
- questions requiring all records matching a filter

The important lesson is not that we should immediately change the chunking strategy.

The lesson is:

> **Chunking should be evaluated against the questions the business will ask.**

The next RAG stages should therefore be built only after we understand whether the current chunks provide sufficiently complete evidence for the target business questions.
