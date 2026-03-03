from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Sequence


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


@dataclass(frozen=True)
class MonitoringReport:
    run_id: str
    generated_at: str  # ISO-8601 string kept as string for deterministic serialization
    overall_metrics: MetricResult
    degradation_events: Sequence[DegradationEvent]
    drift: dict[str, DriftResult]  # keyed by feature/series name
    notes: Sequence[str]