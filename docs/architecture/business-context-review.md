# Day 7 Part 2 — Implementor Business Context Review

## Purpose

Part 2 sits after Part 1 profiling and before future normalization.

```text
ReportProfile
    ↓
Implementor Review
    ↓
BusinessContextProfile
    ↓
Confirmed / Unmapped / Pending decisions
    ↓
Future Part 3 Normalization
```

Part 2 records what a human implementor decides. It does not change the uploaded report and does not create canonical business records.

## Part 1 vs Part 2

Part 1 is observational. It records data types, examples, nulls, possible meanings, possible canonical concepts, and ambiguity.

Part 2 is human confirmation. It stores:

- original source field name;
- human business meaning;
- canonical role;
- confirmation status;
- implementor note;
- company/report/source-format scope.

`CLEAR` from Part 1 is not `CONFIRMED` in Part 2.

## Source field, business meaning, canonical role

These remain separate:

```text
Source field:      VENDOR NAME
Business meaning: Receiving Entity
Canonical role:   DESTINATION_ENTITY
```

The original terminology is retained for traceability.

## Scope

Mappings are not global. `BusinessContextScope` contains:

- `company_context` — opaque tenant/company context supplied by the caller;
- `report_type`;
- `source_format_id`.

The application currently does not have a legitimate authenticated company boundary in the inspected upload flow, so Part 2 does not fabricate `company_id=1`. A future authenticated tenant context can supply the company scope.

## Confirmation states

- `PENDING_REVIEW` — no human decision yet;
- `CONFIRMED` — human accepted a meaning/role;
- `REJECTED` — reviewed interpretation rejected;
- `UNMAPPED` — no reliable canonical meaning established.

## Auditability

The complete Part 1 `ReportProfile` snapshot is preserved inside the Business Context Profile. Human decisions are stored separately in `field_mappings`.

This keeps:

```text
profiler observation != implementor decision
```

and supports later debugging.

## Persistence

For this MVP, profiles use a JSON application-configuration store under:

```text
config/business_context_profiles/
```

(or `BUSINESS_CONTEXT_PROFILE_DIR` when configured).

This avoids adding a PostgreSQL table before the profile model is stable. These JSON profiles are configuration, not canonical business data.

No source-specific mapping is hardcoded in Python. The current inventory example is represented as profile data created by a human/test client.

## Backend review API

Part 2 exposes a minimal backend-first API:

```text
POST /api/business-context/profiles
GET  /api/business-context/profiles
GET  /api/business-context/profiles/{profile_id}
PUT  /api/business-context/profiles/{profile_id}/fields/{source_field}
```

The field review endpoint supports pending, confirmed, rejected, and unmapped decisions.

This is intentionally a functional API rather than a polished UI. A future UI can render the preserved Part 1 observations beside the Part 2 decisions.

## Explicit non-goals

Part 2 does not:

- modify PostgreSQL canonical tables;
- insert inventory, product, or supplier records;
- change Report, Product, Supplier, or InventoryTransaction schema;
- change Qdrant;
- call an LLM;
- change `/api/ask`;
- implement normalization;
- modify source Excel files.

## Part 3 handoff

Future normalization should consume only mappings appropriate to the current context/profile. A confirmed mapping can become eligible normalization input; pending/rejected/unmapped fields must not silently become canonical facts.
