from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from fgdm.domain.drift import DriftConfig
from fgdm.domain.governance import PolicyConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig


@dataclass(frozen=True)
class MonitoringRequest:
    run_id: str
    canonical_rows: Sequence[CanonicalRow]
    rolling: RollingConfig
    drift: DriftConfig
    policy: PolicyConfig
    drift_series: Sequence[str]  # e.g. ["residual"] or ["residual","y","y_hat"]


@dataclass(frozen=True)
class MonitoringResponse:
    report_dict: dict
    report_markdown: str