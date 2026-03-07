from __future__ import annotations

from datetime import date, timedelta

from fgdm.application.dto import MonitoringRequest
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.drift import DriftConfig
from fgdm.domain.governance import PolicyConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig
from fgdm.domain.validation import ValidationConfig


def test_smoke_run_monitoring_with_validation_and_policy() -> None:
    rows: list[CanonicalRow] = []
    start = date(2026, 1, 1)

    for i in range(35):
        ds = start + timedelta(days=i)
        value = float(i + 1)
        rows.append(CanonicalRow(cd_key="A", ds=ds, y=value, y_hat=value - 2.0))
        rows.append(CanonicalRow(cd_key="B", ds=ds, y=value, y_hat=value - 0.1))

    req = MonitoringRequest(
        run_id="test",
        canonical_rows=rows,
        rolling=RollingConfig(
            rolling_window_days=7,
            baseline_window_days=28,
            min_points_per_window=10,
            degradation_abs_threshold=0.0,
            degradation_rel_threshold=0.0,
        ),
        drift=DriftConfig(psi_bins=10),
        policy=PolicyConfig(top_offenders_n=5),
        validation=ValidationConfig(),
        drift_series=["residual", "y_hat"],
    )

    res = run_monitoring(req, generated_at="2026-03-03T00:00:00+00:00")
    assert res.report_dict["run_id"] == "test"
    assert res.report_dict["schema_version"] == "1.1"
    assert res.report_dict["overall_severity"] in ("ok", "warn", "crit")
    assert "validation_summary" in res.report_dict
    assert "rule_breaches" in res.report_dict
    assert "top_offenders" in res.report_dict
    assert "per_key_quality" in res.report_dict