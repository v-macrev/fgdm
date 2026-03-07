from __future__ import annotations

import math

import pytest

from fgdm.domain.errors import ValidationError
from fgdm.domain.metrics import mae, mape, rmse


def test_mae_basic() -> None:
    actual = [10.0, 20.0, 30.0]
    pred = [8.0, 18.0, 33.0]
    assert mae(actual, pred) == pytest.approx((2.0 + 2.0 + 3.0) / 3.0)


def test_rmse_basic() -> None:
    actual = [10.0, 20.0, 30.0]
    pred = [8.0, 18.0, 33.0]
    expected = math.sqrt((4.0 + 4.0 + 9.0) / 3.0)
    assert rmse(actual, pred) == pytest.approx(expected)


def test_mape_basic() -> None:
    actual = [10.0, 20.0, 40.0]
    pred = [9.0, 18.0, 44.0]
    expected = ((1.0 / 10.0) + (2.0 / 20.0) + (4.0 / 40.0)) / 3.0
    assert mape(actual, pred) == pytest.approx(expected)


def test_mape_uses_eps_for_zero_actual() -> None:
    actual = [0.0, 10.0]
    pred = [1.0, 8.0]
    result = mape(actual, pred, eps=1e-6)
    expected = ((1.0 / 1e-6) + (2.0 / 10.0)) / 2.0
    assert result == pytest.approx(expected)


def test_metrics_raise_on_empty() -> None:
    with pytest.raises(ValidationError):
        mae([], [])
    with pytest.raises(ValidationError):
        rmse([], [])
    with pytest.raises(ValidationError):
        mape([], [])


def test_metrics_raise_on_length_mismatch() -> None:
    with pytest.raises(ValidationError):
        mae([1.0], [1.0, 2.0])
    with pytest.raises(ValidationError):
        rmse([1.0], [1.0, 2.0])
    with pytest.raises(ValidationError):
        mape([1.0], [1.0, 2.0])


def test_mape_requires_positive_eps() -> None:
    with pytest.raises(ValidationError):
        mape([1.0], [1.0], eps=0.0)