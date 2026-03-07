from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationSummary:
    row_count: int
    unique_keys: int
    unique_days: int

    duplicate_key_ds_rows: int
    duplicate_key_ds_ratio: float

    zero_actual_rows: int
    zero_actual_ratio: float

    negative_actual_rows: int
    negative_prediction_rows: int