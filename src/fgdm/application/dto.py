from __future__ import annotations
from dataclasses import dataclass
from typing import Sequence
from fgdm.domain.drift import DriftConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig


@dataclass(frozen=True)
class MonitoringRequest:
    run_id: str
    canonical_rows: Sequence[CanonicalRow]
    rolling: RollingConfig
    drift: DriftConfig


@dataclass(frozen=True)
class MonitoringResponse:
    report_dict: dict
    report_markdown: str