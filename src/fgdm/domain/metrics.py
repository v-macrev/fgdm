from __future__ import annotations

import math
from typing import Iterable

from fgdm.domain.errors import ValidationError


def _require_non_empty(values: Iterable[float], name: str) -> list[float]:
    lst = list(values)
    if not lst:
        raise ValidationError(f"{name} must not be empty.")
    return lst


def mae(y: Iterable[float], y_hat: Iterable[float]) -> float:
    y_list = _require_non_empty(y, "y")
    y_hat_list = _require_non_empty(y_hat, "y_hat")
    if len(y_list) != len(y_hat_list):
        raise ValidationError("y and y_hat must have the same length.")
    return sum(abs(a - b) for a, b in zip(y_list, y_hat_list)) / float(len(y_list))


def rmse(y: Iterable[float], y_hat: Iterable[float]) -> float:
    y_list = _require_non_empty(y, "y")
    y_hat_list = _require_non_empty(y_hat, "y_hat")
    if len(y_list) != len(y_hat_list):
        raise ValidationError("y and y_hat must have the same length.")
    mse = sum((a - b) ** 2 for a, b in zip(y_list, y_hat_list)) / float(len(y_list))
    return math.sqrt(mse)


def mape(y: Iterable[float], y_hat: Iterable[float], eps: float = 1e-9) -> float:
    if eps <= 0:
        raise ValidationError("eps must be > 0.")
    y_list = _require_non_empty(y, "y")
    y_hat_list = _require_non_empty(y_hat, "y_hat")
    if len(y_list) != len(y_hat_list):
        raise ValidationError("y and y_hat must have the same length.")
    return (
        sum(abs(a - b) / max(abs(a), eps) for a, b in zip(y_list, y_hat_list))
        / float(len(y_list))
    )