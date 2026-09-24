# Day 7 Part 2 patch

Add these files to the backend after the Part 1 `app/report_understanding/` package is installed.

## Files

```text
app/business_context/
  __init__.py
  models.py
  service.py
  serialization.py
  store.py
app/routes/business_context.py
tests/test_business_context.py
tests/test_business_context_inventory_acceptance.py
tests/test_business_context_api.py
docs/architecture/business-context-review.md
```

## Router registration

Register the new router in the existing `app/main.py` using the project's current router style:

```python
from app.routes.business_context import router as business_context_router

app.include_router(business_context_router)
```

Do not replace the existing `main.py`; only add the router import/registration.

## Run focused tests

```powershell
uv run python -m pytest tests/test_business_context.py tests/test_business_context_inventory_acceptance.py tests/test_business_context_api.py -v
```

Then run the full regression suite:

```powershell
uv run python -m pytest -v
```

## Scope

No database migration is included. No canonical business records are inserted. No Qdrant, LLM, `/api/ask`, or source workbook code is changed.


# Day 7 Part 3 Patch

## Add

Copy these into the backend project:

```text
app/normalization/
tests/test_normalization_transformations.py
tests/test_normalization_service.py
tests/test_normalization_inventory_example.py
docs/architecture/source-to-canonical-normalization.md
```

## Modify existing files

Replace/merge the included versions of:

```text
app/report_understanding/models.py
app/business_context/models.py
app/business_context/service.py
app/business_context/serialization.py
app/routes/business_context.py
```

The changes are backwards-compatible:

- `CanonicalConcept` gains `EXTERNAL_REFERENCE` and `TRANSACTION_TYPE` while retaining existing values.
- Part 2 `FieldMapping` gains `transformation`, default `NONE`.
- Part 2 confirm/API request accepts an optional transformation. Existing requests that omit it continue to behave as `NONE`.

## Test

```powershell
uv run python -m pytest tests/test_normalization_transformations.py tests/test_normalization_service.py tests/test_normalization_inventory_example.py -v
```

Then run regression:

```powershell
uv run python -m pytest -v
```

No new router is required for Part 3. The implementation intentionally remains service-level.

