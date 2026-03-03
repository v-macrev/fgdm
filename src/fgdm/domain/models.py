from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence


@dataclass(frozen=True)
class CanonicalRow:
    cd_key: str
    ds: date
    y: float
    y_hat: float


@dataclass(frozen=True)
class MetricResult:
    mae: float
    rmse: float
    mape: float


@dataclass(frozen=True)
class DriftResult:
    ks_stat: float
    ks_pvalue: float
    psi: float


@dataclass(frozen=True)
class DegradationEvent:
    window_end: date
    metric_name: str
    baseline: float
    current: float
    delta: float
    rel_delta: float


@dataclass(frozen=True)
class RollingPoint:

    window_end: date
    mae: float
    rmse: float
    mape: float
    n_points: int


@dataclass(frozen=True)
class MonitoringReport:
    run_id: str
    generated_at: str  # ISO-8601 string (UTC) kept as string for deterministic serialization

    overall_metrics: MetricResult

    baseline_metrics: MetricResult
    current_metrics: MetricResult

    rolling_window_days: int
    baseline_window_days: int
    rolling_series: Sequence[RollingPoint]

    degradation_events: Sequence[DegradationEvent]

    drift: Mapping[str, DriftResult]  # keyed by series name (e.g., "residual")
    notes: Sequence[str]