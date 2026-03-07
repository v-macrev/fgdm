from __future__ import annotations

from fgdm.infrastructure.reporting.markdown_reporter import render_markdown


def test_markdown_reporter_renders_governance_sections() -> None:
    report = {
        "schema_version": "1.1",
        "run_id": "exp_001",
        "generated_at": "2026-03-03T00:00:00+00:00",
        "quality_severity": "warn",
        "drift_severity": "ok",
        "overall_severity": "warn",
        "config": {
            "rolling": {"rolling_window_days": 7, "baseline_window_days": 28},
            "drift_series": ["residual"],
        },
        "validation_summary": {
            "row_count": 100,
            "unique_keys": 2,
            "unique_days": 35,
            "duplicate_key_ds_rows": 0,
            "duplicate_key_ds_ratio": 0.0,
            "zero_actual_rows": 0,
            "zero_actual_ratio": 0.0,
            "negative_actual_rows": 0,
            "negative_prediction_rows": 0,
        },
        "rule_breaches": ["zero_actual_ratio_above_max: got=0.300000, max=0.200000"],
        "overall_metrics": {"mae": 1.0, "rmse": 2.0, "mape": 0.1},
        "baseline_metrics": {"mae": 0.8, "rmse": 1.8, "mape": 0.08},
        "current_metrics": {"mae": 1.2, "rmse": 2.2, "mape": 0.12},
        "rolling_window_days": 7,
        "baseline_window_days": 28,
        "rolling_series": [
            {"window_end": "2026-01-31", "n_points": 14, "mae": 1.0, "rmse": 2.0, "mape": 0.1}
        ],
        "degradation_events": [
            {
                "window_end": "2026-01-31",
                "metric_name": "mae",
                "baseline": 0.8,
                "current": 1.2,
                "delta": 0.4,
                "rel_delta": 0.5,
            }
        ],
        "drift": {
            "residual": {"ks_stat": 0.4, "ks_pvalue": 0.02, "psi": 0.25}
        },
        "top_offenders": [
            {"cd_key": "A", "n_points": 7, "mae": 2.0, "rmse": 2.5, "mape": 0.2}
        ],
        "per_key_quality": [
            {"cd_key": "A", "n_points": 7, "metrics": {"mae": 2.0, "rmse": 2.5, "mape": 0.2}}
        ],
        "notes": ["Validation rule breaches raise quality severity to at least WARN."],
    }

    out = render_markdown(report)

    assert "# FGDM Report" in out
    assert "## Validation summary" in out
    assert "## Rule breaches" in out
    assert "## Drift" in out
    assert "## Top offenders (current window)" in out
    assert "## Per-key quality (top 10)" in out
    assert "zero_actual_ratio_above_max" in out