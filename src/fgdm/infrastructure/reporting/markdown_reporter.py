from __future__ import annotations

from pathlib import Path
from typing import Any


def render_markdown(report: dict[str, Any]) -> str:
    run_id = str(report.get("run_id", ""))
    generated_at = str(report.get("generated_at", ""))

    quality_sev = str((report.get("quality_severity") or ""))
    drift_sev = str((report.get("drift_severity") or ""))
    overall_sev = str((report.get("overall_severity") or ""))

    overall = report.get("overall_metrics", {}) or {}
    baseline = report.get("baseline_metrics", {}) or {}
    current = report.get("current_metrics", {}) or {}

    rolling_window_days = int(report.get("rolling_window_days", 0) or 0)
    baseline_window_days = int(report.get("baseline_window_days", 0) or 0)

    drift = report.get("drift", {}) or {}
    events = report.get("degradation_events", []) or []
    rolling_series = report.get("rolling_series", []) or []
    offenders = report.get("top_offenders", []) or []
    notes = report.get("notes", []) or []

    def f6(x: Any) -> str:
        return f"{float(x):.6f}"

    lines: list[str] = []
    lines.append("# FGDM Report")
    lines.append("")
    lines.append(f"- run_id: `{run_id}`")
    lines.append(f"- generated_at (UTC): `{generated_at}`")
    lines.append(f"- quality_severity: `{quality_sev}`")
    lines.append(f"- drift_severity: `{drift_sev}`")
    lines.append(f"- overall_severity: `{overall_sev}`")
    lines.append("")

    lines.append("## Overall metrics")
    lines.append(f"- MAE: {f6(overall.get('mae', 0.0))}")
    lines.append(f"- RMSE: {f6(overall.get('rmse', 0.0))}")
    lines.append(f"- MAPE: {f6(overall.get('mape', 0.0))}")
    lines.append("")

    lines.append("## Baseline vs Current")
    lines.append(f"- Baseline window (days): {baseline_window_days}")
    lines.append(f"- Current window (days): {rolling_window_days}")
    lines.append("")
    lines.append(f"- Baseline MAE: {f6(baseline.get('mae', 0.0))}")
    lines.append(f"- Current  MAE: {f6(current.get('mae', 0.0))}")
    lines.append(f"- Baseline RMSE: {f6(baseline.get('rmse', 0.0))}")
    lines.append(f"- Current  RMSE: {f6(current.get('rmse', 0.0))}")
    lines.append(f"- Baseline MAPE: {f6(baseline.get('mape', 0.0))}")
    lines.append(f"- Current  MAPE: {f6(current.get('mape', 0.0))}")
    lines.append("")

    lines.append("## Drift")
    if not drift:
        lines.append("_No drift series computed._")
    else:
        lines.append("| series | KS stat | KS p-value | PSI |")
        lines.append("|---|---:|---:|---:|")
        for name in sorted(drift.keys()):
            d = drift.get(name, {}) or {}
            lines.append(
                f"| {name} | {f6(d.get('ks_stat', 0.0))} | {float(d.get('ks_pvalue', 0.0)):.6g} | {f6(d.get('psi', 0.0))} |"
            )
    lines.append("")

    lines.append("## Rolling series (tail)")
    tail = rolling_series[-10:]
    if not tail:
        lines.append("_No rolling windows met min_points_per_window._")
    else:
        lines.append("| window_end | n_points | MAE | RMSE | MAPE |")
        lines.append("|---|---:|---:|---:|---:|")
        for pt in tail:
            lines.append(
                f"| {pt.get('window_end','')} | {int(pt.get('n_points',0))} | "
                f"{f6(pt.get('mae',0.0))} | {f6(pt.get('rmse',0.0))} | {f6(pt.get('mape',0.0))} |"
            )
    lines.append("")

    lines.append("## Degradation events")
    if not events:
        lines.append("_No degradation events detected under current thresholds._")
    else:
        lines.append("| window_end | metric | baseline | current | delta | rel_delta |")
        lines.append("|---|---|---:|---:|---:|---:|")
        for ev in events:
            lines.append(
                f"| {ev.get('window_end','')} | {ev.get('metric_name','')} | "
                f"{f6(ev.get('baseline',0.0))} | {f6(ev.get('current',0.0))} | "
                f"{f6(ev.get('delta',0.0))} | {float(ev.get('rel_delta',0.0)):.6f} |"
            )
    lines.append("")

    lines.append("## Top offenders (current window)")
    if not offenders:
        lines.append("_No offenders (or insufficient per-key points)._")
    else:
        lines.append("| rank | cd_key | n_points | MAE | RMSE | MAPE |")
        lines.append("|---:|---|---:|---:|---:|---:|")
        for i, o in enumerate(offenders, start=1):
            lines.append(
                f"| {i} | {o.get('cd_key','')} | {int(o.get('n_points',0))} | "
                f"{f6(o.get('mae',0.0))} | {f6(o.get('rmse',0.0))} | {f6(o.get('mape',0.0))} |"
            )
    lines.append("")

    if notes:
        lines.append("## Notes")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")