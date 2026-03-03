from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import os
from typing import Iterable

from fgdm.application.dto import MonitoringRequest, MonitoringResponse
from fgdm.domain.drift import detect_drift
from fgdm.domain.errors import ValidationError
from fgdm.domain.models import CanonicalRow, DegradationEvent, MetricResult, MonitoringReport
from fgdm.domain.rolling import (
    RollingConfig,
    build_rolling_series,
    compute_metrics,
    split_baseline_current_days,
)


def _iso_utc_generated_at(explicit: str | None) -> str:
    if explicit is not None:
        if not explicit.strip():
            raise ValidationError("--generated-at must not be empty when provided.")
        return explicit

    sde = os.environ.get("SOURCE_DATE_EPOCH")
    if sde:
        try:
            epoch = int(sde)
        except ValueError as e:
            raise ValidationError("SOURCE_DATE_EPOCH must be an integer.") from e
        dt = datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0)
        return dt.isoformat()

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _require_rows(rows: Iterable[CanonicalRow]) -> list[CanonicalRow]:
    lst = list(rows)
    if not lst:
        raise ValidationError("canonical_rows must not be empty.")
    return lst


def _index_by_day(rows: list[CanonicalRow]) -> tuple[list, dict, dict, list[float], list[float], list[float]]:
    days: list = []
    y_by_day: dict = {}
    yhat_by_day: dict = {}

    y_all: list[float] = []
    yhat_all: list[float] = []
    resid_all: list[float] = []

    for r in rows:
        days.append(r.ds)
        y_by_day.setdefault(r.ds, []).append(float(r.y))
        yhat_by_day.setdefault(r.ds, []).append(float(r.y_hat))

        y_all.append(float(r.y))
        yhat_all.append(float(r.y_hat))
        resid_all.append(float(r.y) - float(r.y_hat))

    return days, y_by_day, yhat_by_day, y_all, yhat_all, resid_all


def _collect_for_days(
    days: list,
    y_by_day: dict,
    yhat_by_day: dict,
    target_days: list,
) -> tuple[list[float], list[float], list[float]]:
    y: list[float] = []
    y_hat: list[float] = []
    resid: list[float] = []

    for d in target_days:
        ys = y_by_day.get(d, [])
        yh = yhat_by_day.get(d, [])
        if len(ys) != len(yh):
            raise ValidationError(f"Mismatch y/y_hat count on day {d}.")
        y.extend(ys)
        y_hat.extend(yh)
        resid.extend([a - b for a, b in zip(ys, yh)])

    return y, y_hat, resid


def _metric_get(m: MetricResult, name: str) -> float:
    if name == "mae":
        return m.mae
    if name == "rmse":
        return m.rmse
    if name == "mape":
        return m.mape
    raise ValidationError(f"Unknown metric name: {name}")


def run_monitoring(req: MonitoringRequest, *, generated_at: str | None = None) -> MonitoringResponse:
    if not req.run_id.strip():
        raise ValidationError("run_id must not be empty.")

    req.rolling.validate()
    req.drift.validate()

    rows = _require_rows(req.canonical_rows)
    days, y_by_day, yhat_by_day, y_all, yhat_all, resid_all = _index_by_day(rows)

    overall = compute_metrics(y_all, yhat_all, req.rolling.mape_eps)

    baseline_days, current_days = split_baseline_current_days(
        all_days=days,
        baseline_window_days=req.rolling.baseline_window_days,
        current_window_days=req.rolling.rolling_window_days,
    )

    y_base, yhat_base, resid_base = _collect_for_days(days, y_by_day, yhat_by_day, baseline_days)
    y_cur, yhat_cur, resid_cur = _collect_for_days(days, y_by_day, yhat_by_day, current_days)

    if len(y_base) < req.rolling.min_points_per_window:
        raise ValidationError(
            "Baseline window does not have enough points: "
            f"need >= {req.rolling.min_points_per_window}, got {len(y_base)}."
        )
    if len(y_cur) < req.rolling.min_points_per_window:
        raise ValidationError(
            "Current window does not have enough points: "
            f"need >= {req.rolling.min_points_per_window}, got {len(y_cur)}."
        )

    baseline_metrics = compute_metrics(y_base, yhat_base, req.rolling.mape_eps)
    current_metrics = compute_metrics(y_cur, yhat_cur, req.rolling.mape_eps)

    rolling_series = build_rolling_series(
        days=days,
        y_by_day=y_by_day,
        yhat_by_day=yhat_by_day,
        cfg=req.rolling,
    )

    # Degradation events: compare each rolling point metric vs baseline metric.
    events: list[DegradationEvent] = []
    for pt in rolling_series:
        for name in ("mae", "rmse", "mape"):
            baseline_val = _metric_get(baseline_metrics, name)
            current_val = getattr(pt, name)
            delta = current_val - baseline_val
            rel = 0.0 if baseline_val == 0.0 else (delta / baseline_val)

            degraded = False
            if req.rolling.degradation_abs_threshold > 0 and delta >= req.rolling.degradation_abs_threshold:
                degraded = True
            if req.rolling.degradation_rel_threshold > 0 and rel >= req.rolling.degradation_rel_threshold:
                degraded = True

            if degraded:
                events.append(
                    DegradationEvent(
                        window_end=pt.window_end,
                        metric_name=name,
                        baseline=float(baseline_val),
                        current=float(current_val),
                        delta=float(delta),
                        rel_delta=float(rel),
                    )
                )

    drift = {
        "residual": detect_drift(resid_base, resid_cur, cfg=req.drift),
    }

    gen_at = _iso_utc_generated_at(generated_at)

    notes: list[str] = []
    notes.append("Baseline/current windows are defined over distinct ds values (days).")
    notes.append("Rolling series windows with insufficient points are skipped deterministically.")
    notes.append("Drift is computed over residuals (y - y_hat) using KS-test and PSI.")

    report = MonitoringReport(
        run_id=req.run_id,
        generated_at=gen_at,
        overall_metrics=overall,
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        rolling_window_days=req.rolling.rolling_window_days,
        baseline_window_days=req.rolling.baseline_window_days,
        rolling_series=rolling_series,
        degradation_events=events,
        drift=drift,
        notes=notes,
    )

    report_dict = asdict(report)

    md_lines: list[str] = []
    md_lines.append("# FGDM Report")
    md_lines.append("")
    md_lines.append(f"- run_id: `{report.run_id}`")
    md_lines.append(f"- generated_at (UTC): `{report.generated_at}`")
    md_lines.append("")
    md_lines.append("## Overall metrics")
    md_lines.append(f"- MAE: {report.overall_metrics.mae:.6f}")
    md_lines.append(f"- RMSE: {report.overall_metrics.rmse:.6f}")
    md_lines.append(f"- MAPE: {report.overall_metrics.mape:.6f}")
    md_lines.append("")
    md_lines.append("## Baseline vs Current")
    md_lines.append(f"- Baseline window (days): {report.baseline_window_days}")
    md_lines.append(f"- Current window (days): {report.rolling_window_days}")
    md_lines.append("")
    md_lines.append(f"- Baseline MAE: {report.baseline_metrics.mae:.6f}")
    md_lines.append(f"- Current  MAE: {report.current_metrics.mae:.6f}")
    md_lines.append(f"- Baseline RMSE: {report.baseline_metrics.rmse:.6f}")
    md_lines.append(f"- Current  RMSE: {report.current_metrics.rmse:.6f}")
    md_lines.append(f"- Baseline MAPE: {report.baseline_metrics.mape:.6f}")
    md_lines.append(f"- Current  MAPE: {report.current_metrics.mape:.6f}")
    md_lines.append("")
    md_lines.append("## Drift (residual)")
    md_lines.append(f"- KS stat: {report.drift['residual'].ks_stat:.6f}")
    md_lines.append(f"- KS p-value: {report.drift['residual'].ks_pvalue:.6g}")
    md_lines.append(f"- PSI: {report.drift['residual'].psi:.6f}")
    md_lines.append("")

    report_markdown = "\n".join(md_lines)

    return MonitoringResponse(report_dict=report_dict, report_markdown=report_markdown)