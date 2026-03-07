from __future__ import annotations

from datetime import date, timedelta

import pytest

from fgdm.domain.errors import ValidationError
from fgdm.domain.rolling import (
    RollingConfig,
    build_rolling_series,
    compute_metrics,
    split_baseline_current_days,
)


def _day(n: int) -> date:
    return date(2026, 1, 1) + timedelta(days=n)


def test_split_baseline_current_days_basic() -> None:
    days = [_day(i) for i in range(10)]
    baseline, current = split_baseline_current_days(
        all_days=days,
        baseline_window_days=6,
        current_window_days=4,
    )
    assert baseline == [_day(i) for i in range(6)]
    assert current == [_day(i) for i in range(6, 10)]


def test_split_baseline_current_days_requires_enough_distinct_days() -> None:
    days = [_day(i) for i in range(5)]
    with pytest.raises(ValidationError):
        split_baseline_current_days(
            all_days=days,
            baseline_window_days=4,
            current_window_days=3,
        )


def test_compute_metrics_wrapper() -> None:
    m = compute_metrics([10.0, 20.0], [9.0, 18.0], mape_eps=1e-9)
    assert m.mae == pytest.approx(1.5)
    assert m.rmse == pytest.approx(((1.0**2 + 2.0**2) / 2.0) ** 0.5)
    assert m.mape == pytest.approx(((1.0 / 10.0) + (2.0 / 20.0)) / 2.0)


def test_build_rolling_series_skips_windows_below_min_points() -> None:
    days = [_day(i) for i in range(5)]
    y_by_day = {_day(i): [10.0] for i in range(5)}
    yhat_by_day = {_day(i): [9.0] for i in range(5)}

    cfg = RollingConfig(
        rolling_window_days=2,
        baseline_window_days=2,
        min_points_per_window=3,
        mape_eps=1e-9,
    )

    series = build_rolling_series(
        days=days,
        y_by_day=y_by_day,
        yhat_by_day=yhat_by_day,
        cfg=cfg,
    )

    assert series == []


def test_build_rolling_series_builds_expected_points() -> None:
    days = [_day(i) for i in range(4)]
    y_by_day = {
        _day(0): [10.0, 12.0],
        _day(1): [11.0, 13.0],
        _day(2): [14.0, 15.0],
        _day(3): [16.0, 17.0],
    }
    yhat_by_day = {
        _day(0): [9.0, 12.0],
        _day(1): [10.0, 14.0],
        _day(2): [13.0, 14.0],
        _day(3): [16.0, 15.0],
    }

    cfg = RollingConfig(
        rolling_window_days=2,
        baseline_window_days=2,
        min_points_per_window=4,
        mape_eps=1e-9,
    )

    series = build_rolling_series(
        days=days,
        y_by_day=y_by_day,
        yhat_by_day=yhat_by_day,
        cfg=cfg,
    )

    assert len(series) == 3
    assert series[0].window_end == _day(1)
    assert series[0].n_points == 4
    assert series[1].window_end == _day(2)
    assert series[2].window_end == _day(3)


def test_rolling_config_validation() -> None:
    with pytest.raises(ValidationError):
        RollingConfig(rolling_window_days=0).validate()
    with pytest.raises(ValidationError):
        RollingConfig(baseline_window_days=0).validate()
    with pytest.raises(ValidationError):
        RollingConfig(min_points_per_window=0).validate()
    with pytest.raises(ValidationError):
        RollingConfig(mape_eps=0.0).validate()
    with pytest.raises(ValidationError):
        RollingConfig(degradation_abs_threshold=-1.0).validate()
    with pytest.raises(ValidationError):
        RollingConfig(degradation_rel_threshold=-0.1).validate()