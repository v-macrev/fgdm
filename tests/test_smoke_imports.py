from __future__ import annotations

from datetime import date

from fgdm.application.dto import MonitoringRequest
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.drift import DriftConfig
from fgdm.domain.governance import PolicyConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig


def test_smoke_run_monitoring_with_policy_and_offenders() -> None:
    rows: list[CanonicalRow] = []
    for i in range(1, 36):
        rows.append(CanonicalRow(cd_key="A", ds=date(2026, 1, i), y=float(i), y_hat=float(i) - 2.0))
        rows.append(CanonicalRow(cd_key="B", ds=date(2026, 1, i), y=float(i), y_hat=float(i) - 0.1))

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
        drift_series=["residual", "y_hat"],
    )

    res = run_monitoring(req, generated_at="2026-03-03T00:00:00+00:00")
    assert res.report_dict["run_id"] == "test"
    assert res.report_dict["overall_severity"] in ("ok", "warn", "crit")
    assert "top_offenders" in res.report_dict