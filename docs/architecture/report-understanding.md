# Day 7 Part 1 — Report Understanding / Column Profiling

## Purpose

Report understanding is an observational stage between parsing and future business normalization.

```text
Uploaded Report
    ↓
Parser
    ↓
ParsedRecord
    ↓
Report / Column Profiling
    ↓
ReportProfile
    ↓
Future Implementor Review
    ↓
Future Canonical Mapping
```

This stage does not modify source records, PostgreSQL, Qdrant, or `/api/ask`.

## Why source labels are not canonical semantics

A source label is evidence, not an approved business meaning. `VENDOR NAME`, for example, may suggest supplier but could also describe a sending entity, receiving entity, or other party in a company-specific report. `PRODUCTION` is even more ambiguous and must not silently become a production unit, department, or location.

The profiler therefore produces semantic suggestions and an explicit ambiguity status rather than confirmed mappings.

## Output

`ReportProfile` contains:

- source file;
- optional existing report type;
- sheets;
- record count;
- column count;
- optional profiling timestamp;
- `ColumnProfile[]`;
- warnings.

Each `ColumnProfile` contains:

- source column name;
- inferred data type;
- bounded deterministic example values;
- total/null counts and null percentage;
- unique value count;
- possible semantic meanings;
- possible canonical concepts;
- `CLEAR`, `AMBIGUOUS`, or `UNKNOWN` status;
- profiling notes.

## Observation vs suggestion vs approval

**Observation** describes the data: type, values, nulls, cardinality.

**Semantic suggestion** is a deterministic hypothesis based on transparent rules.

**Implementor approval** belongs to Day 7 Part 2 and is not implemented here.

**Canonical mapping** occurs only after approval and is also outside Part 1.

`CLEAR` does not mean approved for persistence. It only means the profiler found a relatively clear generic interpretation.

## Date-like values

The existing Excel parser preserves plain numeric values. Therefore a date column may contain an Excel serial such as `46143`. The profiler may classify such a value as date-like when both the source label and numeric range support that interpretation. It does not rewrite the underlying `ParsedRecord`.

## Semantic rules

Rules are deterministic and intentionally conservative. They provide possible concepts such as:

- `PRODUCT_IDENTIFIER`
- `PRODUCT_NAME`
- `TRANSACTION_DATE`
- `QUANTITY`
- `UNIT_OF_MEASURE`
- `SUPPLIER`
- `CUSTOMER`
- `SOURCE_ENTITY`
- `DESTINATION_ENTITY`
- `BUSINESS_REFERENCE`
- `DOCUMENT_TYPE`
- `LOCATION`
- `DEPARTMENT`
- `UNKNOWN`

No LLM is used. This keeps profiling explainable, stable, testable, and reviewable before human confirmation is introduced.

## Part 2 handoff

The future implementor-review stage can consume `ReportProfile` and show:

- observations;
- representative values;
- suggested meanings;
- ambiguity warnings;
- possible canonical concepts.

An implementor can then approve, reject, or modify mappings before any canonical persistence occurs.

## Explicit non-goals

Part 1 does not:

- alter PostgreSQL schema;
- insert canonical business records;
- create entity relationships;
- create a mapping profile automatically;
- call an LLM;
- modify Qdrant;
- change retrieval;
- change `/api/ask`;
- modify uploaded files.
