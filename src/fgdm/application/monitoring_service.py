from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import os
from typing import Iterable

from fgdm.application.dto import MonitoringRequest, MonitoringResponse
from fgdm.domain.drift import detect_drift
from fgdm.domain.errors import ValidationError
from fgdm.domain.governance import (
    Severity,
    max_severity,
    severity_from_degradation_rel,
    severity_from_drift,
)
from fgdm.domain.models import (
    CanonicalRow,
    DegradationEvent,
    MetricResult,
    MonitoringReport,
    Offender,
    PerKeyQuality,
)
from fgdm.domain.rolling import (
    build_rolling_series,
    compute_metrics,
    split_baseline_current_days,
)
from fgdm.domain.validation import (
    evaluate_validation_breaches,
    summarize_rows,
)


REPORT_SCHEMA_VERSION = "1.1"


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


def _index_rows(rows: list[CanonicalRow]) -> tuple[list, dict, dict, list[float], list[float]]:
    days: list = []
    y_by_day: dict = {}
    yhat_by_day: dict = {}

    y_all: list[float] = []
    yhat_all: list[float] = []

    for r in rows:
        days.append(r.ds)
        y_by_day.setdefault(r.ds, []).append(float(r.y))
        yhat_by_day.setdefault(r.ds, []).append(float(r.y_hat))
        y_all.append(float(r.y))
        yhat_all.append(float(r.y_hat))

    return days, y_by_day, yhat_by_day, y_all, yhat_all


def _collect_for_days(y_by_day: dict, yhat_by_day: dict, target_days: list) -> tuple[list[float], list[float], list[float]]:
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


def _normalize_series_names(series: Iterable[str]) -> list[str]:
    allowed = {"residual", "y", "y_hat"}
    out: list[str] = []
    for s in series:
        name = s.strip()
        if not name:
            continue
        if name not in allowed:
            raise ValidationError(f"Unsupported drift series '{name}'. Allowed: {sorted(allowed)}.")
        out.append(name)
    if not out:
        raise ValidationError("drift_series must include at least one of: residual, y, y_hat.")
    order = {"residual": 0, "y": 1, "y_hat": 2}
    return sorted(set(out), key=lambda x: order[x])


def _compute_top_offenders_current_window(
    *,
    rows: list[CanonicalRow],
    current_days: list,
    rolling_eps: float,
    min_points: int,
    top_n: int,
) -> list[Offender]:
    y_by_key: dict[str, list[float]] = {}
    yhat_by_key: dict[str, list[float]] = {}

    current_days_set = set(current_days)
    for r in rows:
        if r.ds not in current_days_set:
            continue
        y_by_key.setdefault(r.cd_key, []).append(float(r.y))
        yhat_by_key.setdefault(r.cd_key, []).append(float(r.y_hat))

    offenders: list[Offender] = []
    for k in sorted(y_by_key.keys()):
        y = y_by_key[k]
        y_hat = yhat_by_key.get(k, [])
        if len(y) != len(y_hat):
            raise ValidationError(f"Mismatch y/y_hat for cd_key={k} in current window.")
        if len(y) < min_points:
            continue
        m = compute_metrics(y, y_hat, rolling_eps)
        offenders.append(Offender(cd_key=k, n_points=len(y), mae=m.mae, rmse=m.rmse, mape=m.mape))

    offenders.sort(key=lambda o: (-o.mae, o.cd_key))
    return offenders[:top_n]


def _compute_per_key_quality(
    *,
    rows: list[CanonicalRow],
    current_days: list,
    mape_eps: float,
    min_points_per_key: int,
) -> list[PerKeyQuality]:
    y_by_key: dict[str, list[float]] = {}
    yhat_by_key: dict[str, list[float]] = {}

    current_days_set = set(current_days)
    for r in rows:
        if r.ds not in current_days_set:
            continue
        y_by_key.setdefault(r.cd_key, []).append(float(r.y))
        yhat_by_key.setdefault(r.cd_key, []).append(float(r.y_hat))

    out: list[PerKeyQuality] = []
    for k in sorted(y_by_key.keys()):
        y = y_by_key[k]
        y_hat = yhat_by_key.get(k, [])
        if len(y) != len(y_hat):
            raise ValidationError(f"Mismatch y/y_hat for cd_key={k} in current window.")
        if len(y) < min_points_per_key:
            continue
        m = compute_metrics(y, y_hat, mape_eps)
        out.append(PerKeyQuality(cd_key=k, n_points=len(y), metrics=m))

    out.sort(key=lambda pk: (-pk.metrics.mae, pk.cd_key))
    return out


def run_monitoring(req: MonitoringRequest, *, generated_at: str | None = None) -> MonitoringResponse:
    if not req.run_id.strip():
        raise ValidationError("run_id must not be empty.")

    req.rolling.validate()
    req.drift.validate()
    req.policy.validate()
    req.validation.validate()

    drift_series = _normalize_series_names(req.drift_series)

    rows = _require_rows(req.canonical_rows)
    validation_summary = summarize_rows(rows)
    rule_breaches = evaluate_validation_breaches(validation_summary, req.validation)

    days, y_by_day, yhat_by_day, y_all, yhat_all = _index_rows(rows)

    overall = compute_metrics(y_all, yhat_all, req.rolling.mape_eps)

    baseline_days, current_days = split_baseline_current_days(
        all_days=days,
        baseline_window_days=req.rolling.baseline_window_days,
        current_window_days=req.rolling.rolling_window_days,
    )

    y_base, yhat_base, resid_base = _collect_for_days(y_by_day, yhat_by_day, baseline_days)
    y_cur, yhat_cur, resid_cur = _collect_for_days(y_by_day, yhat_by_day, current_days)

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

    quality_sev = Severity.OK
    for metric_name in ("mae", "rmse", "mape"):
        b = _metric_get(baseline_metrics, metric_name)
        c = _metric_get(current_metrics, metric_name)
        rel = 0.0 if b == 0.0 else (c - b) / b
        quality_sev = max_severity(
            quality_sev,
            severity_from_degradation_rel(
                rel,
                warn_rel=req.policy.degradation_warn_rel,
                crit_rel=req.policy.degradation_crit_rel,
            ),
        )

    drift: dict[str, object] = {}
    drift_sev = Severity.OK
    for s in drift_series:
        if s == "residual":
            d = detect_drift(resid_base, resid_cur, cfg=req.drift)
        elif s == "y":
            d = detect_drift(y_base, y_cur, cfg=req.drift)
        elif s == "y_hat":
            d = detect_drift(yhat_base, yhat_cur, cfg=req.drift)
        else:
            raise ValidationError(f"Unsupported drift series: {s}")

        drift[s] = d
        drift_sev = max_severity(
            drift_sev,
            severity_from_drift(
                psi_value=d.psi,
                ks_pvalue=d.ks_pvalue,
                warn_psi=req.policy.drift_warn_psi,
                crit_psi=req.policy.drift_crit_psi,
                warn_p=req.policy.drift_warn_ks_pvalue,
                crit_p=req.policy.drift_crit_ks_pvalue,
            ),
        )

    if rule_breaches:
        quality_sev = max_severity(quality_sev, Severity.WARN)

    overall_sev = max_severity(quality_sev, drift_sev)

    min_points_per_key = max(1, req.rolling.min_points_per_window // max(1, req.rolling.rolling_window_days))

    top_offenders = _compute_top_offenders_current_window(
        rows=rows,
        current_days=current_days,
        rolling_eps=req.rolling.mape_eps,
        min_points=min_points_per_key,
        top_n=req.policy.top_offenders_n,
    )

    per_key_quality = _compute_per_key_quality(
        rows=rows,
        current_days=current_days,
        mape_eps=req.rolling.mape_eps,
        min_points_per_key=min_points_per_key,
    )

    gen_at = _iso_utc_generated_at(generated_at)

    config_snapshot = {
        "rolling": {
            "rolling_window_days": req.rolling.rolling_window_days,
            "baseline_window_days": req.rolling.baseline_window_days,
            "min_points_per_window": req.rolling.min_points_per_window,
            "mape_eps": req.rolling.mape_eps,
            "degradation_abs_threshold": req.rolling.degradation_abs_threshold,
            "degradation_rel_threshold": req.rolling.degradation_rel_threshold,
        },
        "drift": {"psi_bins": req.drift.psi_bins},
        "policy": {
            "degradation_warn_rel": req.policy.degradation_warn_rel,
            "degradation_crit_rel": req.policy.degradation_crit_rel,
            "drift_warn_psi": req.policy.drift_warn_psi,
            "drift_crit_psi": req.policy.drift_crit_psi,
            "drift_warn_ks_pvalue": req.policy.drift_warn_ks_pvalue,
            "drift_crit_ks_pvalue": req.policy.drift_crit_ks_pvalue,
            "top_offenders_n": req.policy.top_offenders_n,
        },
        "validation": {
            "allow_negative_actuals": req.validation.allow_negative_actuals,
            "allow_negative_predictions": req.validation.allow_negative_predictions,
            "max_zero_actual_ratio": req.validation.max_zero_actual_ratio,
            "max_duplicate_key_ds_ratio": req.validation.max_duplicate_key_ds_ratio,
            "min_unique_keys": req.validation.min_unique_keys,
            "min_unique_days": req.validation.min_unique_days,
        },
        "drift_series": drift_series,
        "min_points_per_key": min_points_per_key,
    }

    notes: list[str] = []
    notes.append("Baseline/current windows are defined over distinct ds values (days).")
    notes.append("Rolling series windows with insufficient points are skipped deterministically.")
    notes.append("Drift is computed with KS-test and PSI over selected series.")
    notes.append("Top offenders and per_key_quality are computed on the current window only.")
    notes.append("Per-key min points is derived from global min_points_per_window and rolling_window_days.")
    if rule_breaches:
        notes.append("Validation rule breaches raise quality severity to at least WARN.")

    report = MonitoringReport(
        schema_version=REPORT_SCHEMA_VERSION,
        run_id=req.run_id,
        generated_at=gen_at,
        config=config_snapshot,
        validation_summary=validation_summary,
        rule_breaches=rule_breaches,
        overall_metrics=overall,
        baseline_metrics=baseline_metrics,
        current_metrics=current_metrics,
        rolling_window_days=req.rolling.rolling_window_days,
        baseline_window_days=req.rolling.baseline_window_days,
        rolling_series=rolling_series,
        degradation_events=events,
        drift=drift,  # type: ignore[assignment]
        quality_severity=quality_sev,
        drift_severity=drift_sev,
        overall_severity=overall_sev,
        top_offenders=top_offenders,
        per_key_quality=per_key_quality,
        notes=notes,
    )

    report_dict = asdict(report)

    md_lines: list[str] = []
    md_lines.append("# FGDM Report")
    md_lines.append("")
    md_lines.append(f"- schema_version: `{report.schema_version}`")
    md_lines.append(f"- run_id: `{report.run_id}`")
    md_lines.append(f"- generated_at (UTC): `{report.generated_at}`")
    md_lines.append(f"- quality_severity: `{report.quality_severity.value}`")
    md_lines.append(f"- drift_severity: `{report.drift_severity.value}`")
    md_lines.append(f"- overall_severity: `{report.overall_severity.value}`")
    md_lines.append("")
    report_markdown = "\n".join(md_lines)

    return MonitoringResponse(report_dict=report_dict, report_markdown=report_markdown)