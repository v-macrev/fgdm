from __future__ import annotations

from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    run_id = report.get("run_id", "")
    generated_at = report.get("generated_at", "")
    overall = report.get("overall_metrics", {}) or {}

    lines: list[str] = []
    lines.append("# FGDM Report")
    lines.append("")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- generated_at: `{generated_at}`")
    lines.append("")
    lines.append("## Overall metrics")
    lines.append(f"- MAE: {float(overall.get('mae', 0.0)):.6f}")
    lines.append(f"- RMSE: {float(overall.get('rmse', 0.0)):.6f}")
    lines.append(f"- MAPE: {float(overall.get('mape', 0.0)):.6f}")
    lines.append("")
    return "\n".join(lines)