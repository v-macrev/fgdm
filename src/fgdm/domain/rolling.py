from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import date

from fgdm.domain.errors import ValidationError
from fgdm.domain.metrics import mae, mape, rmse
from fgdm.domain.models import MetricResult, RollingPoint


@dataclass(frozen=True)
class RollingConfig:
    rolling_window_days: int = 7
    baseline_window_days: int = 28
    min_points_per_window: int = 30
    mape_eps: float = 1e-9

    degradation_abs_threshold: float = 0.0
    degradation_rel_threshold: float = 0.2

    def validate(self) -> None:
        if self.rolling_window_days < 1:
            raise ValidationError("rolling_window_days must be >= 1.")
        if self.baseline_window_days < 1:
            raise ValidationError("baseline_window_days must be >= 1.")
        if self.min_points_per_window < 1:
            raise ValidationError("min_points_per_window must be >= 1.")
        if self.mape_eps <= 0:
            raise ValidationError("mape_eps must be > 0.")
        if self.degradation_abs_threshold < 0:
            raise ValidationError("degradation_abs_threshold must be >= 0.")
        if self.degradation_rel_threshold < 0:
            raise ValidationError("degradation_rel_threshold must be >= 0.")


def _unique_sorted_days(days: Iterable[date]) -> list[date]:
    s = sorted(set(days))
    if not s:
        raise ValidationError("No dates available to build rolling windows.")
    return s


def compute_metrics(y: Sequence[float], y_hat: Sequence[float], mape_eps: float) -> MetricResult:
    return MetricResult(
        mae=mae(y, y_hat),
        rmse=rmse(y, y_hat),
        mape=mape(y, y_hat, eps=mape_eps),
    )


def build_rolling_series(
    *,
    days: Sequence[date],
    y_by_day: dict[date, list[float]],
    yhat_by_day: dict[date, list[float]],
    cfg: RollingConfig,
) -> list[RollingPoint]:
    cfg.validate()
    uniq_days = _unique_sorted_days(days)

    points: list[RollingPoint] = []
    for i, window_end in enumerate(uniq_days):
        start_idx = max(0, i + 1 - cfg.rolling_window_days)
        window_days = uniq_days[start_idx : i + 1]

        y: list[float] = []
        y_hat: list[float] = []
        for d in window_days:
            y.extend(y_by_day.get(d, []))
            y_hat.extend(yhat_by_day.get(d, []))

        if len(y) < cfg.min_points_per_window:
            continue

        m = compute_metrics(y, y_hat, cfg.mape_eps)
        points.append(
            RollingPoint(
                window_end=window_end,
                mae=m.mae,
                rmse=m.rmse,
                mape=m.mape,
                n_points=len(y),
            )
        )

    return points


def split_baseline_current_days(
    *,
    all_days: Sequence[date],
    baseline_window_days: int,
    current_window_days: int,
) -> tuple[list[date], list[date]]:
    if baseline_window_days < 1 or current_window_days < 1:
        raise ValidationError("Window sizes must be >= 1.")
    uniq_days = _unique_sorted_days(all_days)

    if len(uniq_days) < baseline_window_days + current_window_days:
        raise ValidationError(
            "Not enough distinct ds values to split baseline/current windows: "
            f"need at least {baseline_window_days + current_window_days}, got {len(uniq_days)}."
        )

    baseline_days = list(uniq_days[:baseline_window_days])
    current_days = list(uniq_days[-current_window_days:])
    return baseline_days, current_days