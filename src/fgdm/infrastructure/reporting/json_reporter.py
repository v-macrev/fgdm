from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


def _normalize(obj: Any) -> Any:
    if isinstance(obj, date):
        return obj.isoformat()

    if isinstance(obj, dict):
        return {k: _normalize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_normalize(v) for v in obj]

    return obj


def render_json(report: dict[str, Any]) -> str:
    normalized = _normalize(report)
    return json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_json(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(report), encoding="utf-8")