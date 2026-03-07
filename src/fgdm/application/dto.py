from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from fgdm.domain.drift import DriftConfig
from fgdm.domain.governance import PolicyConfig
from fgdm.domain.models import CanonicalRow
from fgdm.domain.rolling import RollingConfig
from fgdm.domain.validation import ValidationConfig


@dataclass(frozen=True)
class MonitoringRequest:
    run_id: str
    canonical_rows: Sequence[CanonicalRow]
    rolling: RollingConfig
    drift: DriftConfig
    policy: PolicyConfig
    validation: ValidationConfig
    drift_series: Sequence[str]


@dataclass(frozen=True)
class MonitoringResponse:
    report_dict: dict
    report_markdown: str