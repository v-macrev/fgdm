from __future__ import annotations

from datetime import date

from fgdm.domain.governance import Severity
from fgdm.infrastructure.reporting.json_reporter import render_json


def test_json_normalization_handles_date_and_enum() -> None:
    payload = {
        "d": date(2026, 3, 3),
        "sev": Severity.CRIT,
        "nested": {"d2": date(2026, 1, 1), "sev2": Severity.WARN},
        "arr": [date(2026, 2, 2), Severity.OK],
    }
    out = render_json(payload)
    assert "2026-03-03" in out
    assert '"crit"' in out
    assert '"warn"' in out
    assert '"ok"' in out