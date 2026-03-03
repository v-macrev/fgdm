from __future__ import annotations

from datetime import date

import pytest

from fgdm.application.dto import MonitoringRequest
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.drift import DriftConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig


def test_smoke_run_monitoring_minimal() -> None:
    rows = []
    for i in range(1, 36):
        rows.append(CanonicalRow(cd_key="A", ds=date(2026, 1, i), y=float(i), y_hat=float(i) - 0.5))

    req = MonitoringRequest(
        run_id="test",
        canonical_rows=rows,
        rolling=RollingConfig(
            rolling_window_days=7,
            baseline_window_days=28,
            min_points_per_window=5,
            degradation_abs_threshold=0.0,
            degradation_rel_threshold=0.0,
        ),
        drift=DriftConfig(psi_bins=10),
    )

    res = run_monitoring(req, generated_at="2026-03-03T00:00:00+00:00")
    assert res.report_dict["run_id"] == "test"
    assert res.report_dict["generated_at"] == "2026-03-03T00:00:00+00:00"
    assert "overall_metrics" in res.report_dict
    assert "drift" in res.report_dict
    assert "residual" in res.report_dict["drift"]


def test_requires_enough_days() -> None:
    rows = [CanonicalRow(cd_key="A", ds=date(2026, 1, 1), y=1.0, y_hat=1.0)]
    req = MonitoringRequest(
        run_id="test",
        canonical_rows=rows,
        rolling=RollingConfig(rolling_window_days=7, baseline_window_days=28, min_points_per_window=1),
        drift=DriftConfig(psi_bins=10),
    )
    with pytest.raises(Exception):
        run_monitoring(req, generated_at="2026-03-03T00:00:00+00:00")