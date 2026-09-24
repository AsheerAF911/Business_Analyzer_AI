# Part 3 — Generic Source-to-Canonical Normalization

## Purpose

Part 3 executes mappings explicitly confirmed in Part 2. It does **not** infer business meaning and does not persist PostgreSQL business records.

```text
ParsedRecord
    ↓
BusinessContextProfile
    ↓
FieldMapping
    ↓
NormalizationService
    ↓
CanonicalDraft
    ↓
Part 4 Validation
    ↓
Future Persistence
```

## Source field vs business meaning vs canonical concept

These remain separate:

- **source field**: original terminology such as `VENDOR`, `PARTY`, or `SKU`;
- **business meaning**: the implementor-confirmed interpretation for that company/report format;
- **canonical concept**: reusable concept such as `SUPPLIER`, `DESTINATION_ENTITY`, or `PRODUCT_IDENTIFIER`;
- **transformation**: deterministic value operation such as date or number normalization.

Part 3 never contains global source aliases. The same `VENDOR` field can therefore normalize to `DESTINATION_ENTITY` for one company and `SUPPLIER` for another, entirely according to the supplied BusinessContextProfile.

## Canonical concepts

The existing reusable `CanonicalConcept` vocabulary is reused and extended with `EXTERNAL_REFERENCE` and `TRANSACTION_TYPE`. It remains independent of PostgreSQL tables/columns.

## Explicit transformations

Supported MVP transformations:

- `NONE`
- `DATE_NORMALIZATION`
- `NUMBER_NORMALIZATION`
- `TEXT_NORMALIZATION`
- `UNIT_NORMALIZATION`

Transformations are stored on the confirmed Part 2 `FieldMapping`. `NONE` is the backwards-compatible default. Transformation failure is reported as a normalization warning and the raw source field is preserved as unmapped.

No unit conversion or semantic inference is performed.

## CanonicalDraft

`CanonicalDraft` is a dataclass, not an ORM model. It contains:

- `canonical_values`
- `unmapped_fields`
- `transformation_warnings`
- record provenance
- a source-record reference

Canonical values are stored as **lists per canonical concept**. This is intentional: if two source fields both map to `QUANTITY`, neither value is overwritten. Both are preserved and a `DUPLICATE_CANONICAL_CONCEPT` warning is emitted for Part 4 or human review.

## Provenance

Every canonical and unmapped value preserves:

- source file;
- sheet/source section as supplied by ParsedRecord;
- row number/source record position;
- source field.

No Excel-specific database columns are introduced.

## Unmapped fields

A source field is preserved in `unmapped_fields` when:

- no mapping exists;
- its Part 2 mapping is pending/rejected/unmapped;
- a confirmed mapping is incomplete;
- its canonical concept/transformation is unknown;
- transformation fails.

Part 3 never guesses a replacement meaning.

## Normalization-level warnings

Part 3 reports only normalization concerns, including:

- transformation failure;
- unknown canonical concept;
- unknown transformation;
- confirmed mapping input missing from a source record;
- duplicate canonical concept.

Deeper business validation belongs to Part 4.

## Multi-company behavior

Mappings come entirely from the supplied profile/configuration. No company IDs, source-column aliases, inventory-specific rules, or workbook-specific conditionals exist inside NormalizationService.

## Persistence boundary

Part 3 does not:

- import or create SQLAlchemy business records;
- alter PostgreSQL schema;
- write Product/Supplier/InventoryTransaction rows;
- call Qdrant;
- call an LLM;
- modify `/api/ask`;
- modify uploaded source files.

The output is only `CanonicalDraft`, ready for Part 4 validation.
