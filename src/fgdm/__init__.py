from __future__ import annotations

from fgdm.application.dto import MonitoringRequest, MonitoringResponse
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.drift import DriftConfig
from fgdm.domain.governance import PolicyConfig, Severity
from fgdm.domain.rolling import RollingConfig
from fgdm.domain.validation import ValidationConfig
from fgdm.infrastructure.io import load_canonical_data
from fgdm.infrastructure.reporting.markdown_reporter import write_markdown
from fgdm.infrastructure.reporting.json_reporter import write_json


__all__ = [
    "__version__",
    "MonitoringRequest",
    "MonitoringResponse",
    "run_monitoring",
    "DriftConfig",
    "PolicyConfig",
    "Severity",
    "RollingConfig",
    "ValidationConfig",
    "load_canonical_data",
    "write_markdown",
    "write_json",
    
]

__version__ = "0.1.0"