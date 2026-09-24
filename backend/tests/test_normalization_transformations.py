from datetime import date
from decimal import Decimal

import pytest

from app.normalization import (
    TransformationError,
    TransformationType,
    transform_value,
)


def test_excel_serial_normalizes_to_date():
    assert transform_value(46143, TransformationType.DATE_NORMALIZATION) == date(2026, 5, 1)


def test_numeric_string_normalizes_to_number():
    assert transform_value("160", TransformationType.NUMBER_NORMALIZATION) == 160
    assert transform_value("160.25", TransformationType.NUMBER_NORMALIZATION) == Decimal("160.25")


def test_text_normalization_is_deterministic():
    assert transform_value("  Alpha   Beta  ", TransformationType.TEXT_NORMALIZATION) == "Alpha Beta"


def test_unit_normalization_does_not_convert_measurements():
    assert transform_value(" kg ", TransformationType.UNIT_NORMALIZATION) == "KG"


def test_invalid_number_raises_transformation_error():
    with pytest.raises(TransformationError):
        transform_value("not-a-number", TransformationType.NUMBER_NORMALIZATION)


def test_none_transformation_preserves_value():
    original = {"raw": "value"}
    assert transform_value(original, TransformationType.NONE) is original
