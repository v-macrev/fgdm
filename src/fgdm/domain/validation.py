from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fgdm.domain.errors import ValidationError
from fgdm.domain.validation_models import ValidationSummary

if TYPE_CHECKING:
    from fgdm.domain.models import CanonicalRow


@dataclass(frozen=True)
class ValidationConfig:
    
    allow_negative_actuals: bool = False
    allow_negative_predictions: bool = True
    max_zero_actual_ratio: float = 0.2
    max_duplicate_key_ds_ratio: float = 0.05
    min_unique_keys: int = 1
    min_unique_days: int = 1

    def validate(self) -> None:
        if not (0.0 <= self.max_zero_actual_ratio <= 1.0):
            raise ValidationError("max_zero_actual_ratio must be in [0,1].")
        if not (0.0 <= self.max_duplicate_key_ds_ratio <= 1.0):
            raise ValidationError("max_duplicate_key_ds_ratio must be in [0,1].")
        if self.min_unique_keys < 1:
            raise ValidationError("min_unique_keys must be >= 1.")
        if self.min_unique_days < 1:
            raise ValidationError("min_unique_days must be >= 1.")


def summarize_rows(rows: Sequence[CanonicalRow]) -> ValidationSummary:
    if not rows:
        raise ValidationError("Cannot summarize empty canonical rows.")

    keys = set()
    days = set()

    pair_counts: dict[tuple[str, object], int] = {}

    zero_actual_rows = 0
    negative_actual_rows = 0
    negative_prediction_rows = 0

    for r in rows:
        keys.add(r.cd_key)
        days.add(r.ds)

        pair = (r.cd_key, r.ds)
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

        if r.y == 0.0:
            zero_actual_rows += 1
        if r.y < 0.0:
            negative_actual_rows += 1
        if r.y_hat < 0.0:
            negative_prediction_rows += 1

    duplicate_key_ds_rows = sum(count - 1 for count in pair_counts.values() if count > 1)
    row_count = len(rows)

    return ValidationSummary(
        row_count=row_count,
        unique_keys=len(keys),
        unique_days=len(days),
        duplicate_key_ds_rows=duplicate_key_ds_rows,
        duplicate_key_ds_ratio=duplicate_key_ds_rows / float(row_count),
        zero_actual_rows=zero_actual_rows,
        zero_actual_ratio=zero_actual_rows / float(row_count),
        negative_actual_rows=negative_actual_rows,
        negative_prediction_rows=negative_prediction_rows,
    )


def evaluate_validation_breaches(
    summary: ValidationSummary,
    cfg: ValidationConfig,
) -> list[str]:
    cfg.validate()

    breaches: list[str] = []

    if summary.unique_keys < cfg.min_unique_keys:
        breaches.append(
            f"unique_keys_below_min: got={summary.unique_keys}, min={cfg.min_unique_keys}"
        )

    if summary.unique_days < cfg.min_unique_days:
        breaches.append(
            f"unique_days_below_min: got={summary.unique_days}, min={cfg.min_unique_days}"
        )

    if summary.duplicate_key_ds_ratio > cfg.max_duplicate_key_ds_ratio:
        breaches.append(
            "duplicate_key_ds_ratio_above_max: "
            f"got={summary.duplicate_key_ds_ratio:.6f}, "
            f"max={cfg.max_duplicate_key_ds_ratio:.6f}"
        )

    if summary.zero_actual_ratio > cfg.max_zero_actual_ratio:
        breaches.append(
            "zero_actual_ratio_above_max: "
            f"got={summary.zero_actual_ratio:.6f}, "
            f"max={cfg.max_zero_actual_ratio:.6f}"
        )

    if (not cfg.allow_negative_actuals) and summary.negative_actual_rows > 0:
        breaches.append(
            f"negative_actuals_not_allowed: rows={summary.negative_actual_rows}"
        )

    if (not cfg.allow_negative_predictions) and summary.negative_prediction_rows > 0:
        breaches.append(
            f"negative_predictions_not_allowed: rows={summary.negative_prediction_rows}"
        )

    return breaches