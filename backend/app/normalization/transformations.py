from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from openpyxl.utils.datetime import from_excel

from .models import TransformationType


class TransformationError(ValueError):
    pass


def _normalize_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TransformationError("Boolean value cannot be normalized as a date")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float, Decimal)):
        try:
            return from_excel(float(value)).date()
        except (TypeError, ValueError, OverflowError) as exc:
            raise TransformationError(f"Invalid Excel date serial: {value!r}") from exc
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return date.fromisoformat(text)
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        except ValueError:
            pass
        try:
            return from_excel(float(text)).date()
        except (TypeError, ValueError, OverflowError) as exc:
            raise TransformationError(f"Value is not date-like: {value!r}") from exc
    raise TransformationError(f"Unsupported date value type: {type(value).__name__}")


def _normalize_number(value: Any) -> int | Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TransformationError("Boolean value cannot be normalized as a number")
    try:
        number = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise TransformationError(f"Value is not numeric: {value!r}") from exc
    if not number.is_finite():
        raise TransformationError(f"Numeric value must be finite: {value!r}")
    if number == number.to_integral_value():
        return int(number)
    return number.normalize()


def _normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    return " ".join(str(value).split())


def _normalize_unit(value: Any) -> str | None:
    if value is None:
        return None
    # Normalization only; no unit conversion or alias inference is performed.
    return " ".join(str(value).split()).upper()


def transform_value(value: Any, transformation: TransformationType) -> Any:
    if transformation == TransformationType.NONE:
        return value
    if transformation == TransformationType.DATE_NORMALIZATION:
        return _normalize_date(value)
    if transformation == TransformationType.NUMBER_NORMALIZATION:
        return _normalize_number(value)
    if transformation == TransformationType.TEXT_NORMALIZATION:
        return _normalize_text(value)
    if transformation == TransformationType.UNIT_NORMALIZATION:
        return _normalize_unit(value)
    raise TransformationError(f"Unsupported transformation: {transformation}")
