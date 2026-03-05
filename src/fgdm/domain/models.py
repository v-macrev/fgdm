from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Sequence

from fgdm.domain.governance import Severity


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
class Offender:
    cd_key: str
    n_points: int
    mae: float
    rmse: float
    mape: float


@dataclass(frozen=True)
class PerKeyQuality:
    cd_key: str
    n_points: int
    metrics: MetricResult


@dataclass(frozen=True)
class MonitoringReport:
    schema_version: str
    run_id: str
    generated_at: str  # ISO-8601 UTC

    config: Mapping[str, Any]

    overall_metrics: MetricResult
    baseline_metrics: MetricResult
    current_metrics: MetricResult

    rolling_window_days: int
    baseline_window_days: int
    rolling_series: Sequence[RollingPoint]

    degradation_events: Sequence[DegradationEvent]

    drift: Mapping[str, DriftResult]  # e.g., residual, y, y_hat

    quality_severity: Severity
    drift_severity: Severity
    overall_severity: Severity

    top_offenders: Sequence[Offender]
    per_key_quality: Sequence[PerKeyQuality]

    notes: Sequence[str]