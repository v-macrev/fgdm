from __future__ import annotations

from datetime import date

from fgdm.domain.models import CanonicalRow
from fgdm.domain.validation import (
    ValidationConfig,
    evaluate_validation_breaches,
    summarize_rows,
)


def test_validation_summary_and_breaches() -> None:
    rows = [
        CanonicalRow(cd_key="A", ds=date(2026, 1, 1), y=0.0, y_hat=1.0),
        CanonicalRow(cd_key="A", ds=date(2026, 1, 1), y=2.0, y_hat=1.5),
        CanonicalRow(cd_key="B", ds=date(2026, 1, 2), y=-1.0, y_hat=-2.0),
    ]

    summary = summarize_rows(rows)

    assert summary.row_count == 3
    assert summary.unique_keys == 2
    assert summary.unique_days == 2
    assert summary.duplicate_key_ds_rows == 1
    assert summary.zero_actual_rows == 1
    assert summary.negative_actual_rows == 1
    assert summary.negative_prediction_rows == 1

    cfg = ValidationConfig(
        allow_negative_actuals=False,
        allow_negative_predictions=False,
        max_zero_actual_ratio=0.2,
        max_duplicate_key_ds_ratio=0.2,
        min_unique_keys=1,
        min_unique_days=1,
    )

    breaches = evaluate_validation_breaches(summary, cfg)

    assert any("duplicate_key_ds_ratio_above_max" in b for b in breaches)
    assert any("zero_actual_ratio_above_max" in b for b in breaches)
    assert any("negative_actuals_not_allowed" in b for b in breaches)
    assert any("negative_predictions_not_allowed" in b for b in breaches)