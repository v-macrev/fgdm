from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from fgdm.domain.models import CanonicalRow
from fgdm.domain.drift import DriftConfig


@dataclass(frozen=True)
class MonitoringRequest:
    run_id: str
    canonical_rows: Sequence[CanonicalRow]
    drift_series_baseline: Mapping[str, Sequence[float]]
    drift_series_current: Mapping[str, Sequence[float]]
    drift_config: DriftConfig | None = None


@dataclass(frozen=True)
class MonitoringResponse:
    report_json: dict
    report_markdown: str