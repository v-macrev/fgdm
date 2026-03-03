from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone

from fgdm.application.dto import MonitoringRequest, MonitoringResponse
from fgdm.domain.drift import detect_drift
from fgdm.domain.errors import ValidationError
from fgdm.domain.metrics import mae, mape, rmse
from fgdm.domain.models import MetricResult, MonitoringReport


def run_monitoring(req: MonitoringRequest) -> MonitoringResponse:
    if not req.run_id.strip():
        raise ValidationError("run_id must not be empty.")

    y = [r.y for r in req.canonical_rows]
    y_hat = [r.y_hat for r in req.canonical_rows]

    overall = MetricResult(
        mae=mae(y, y_hat),
        rmse=rmse(y, y_hat),
        mape=mape(y, y_hat),
    )

    drift_out: dict[str, object] = {}
    for name, base_vals in req.drift_series_baseline.items():
        cur_vals = req.drift_series_current.get(name)
        if cur_vals is None:
            raise ValidationError(f"Missing current drift series for '{name}'.")
        drift_out[name] = detect_drift(base_vals, cur_vals, cfg=req.drift_config)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    report = MonitoringReport(
        run_id=req.run_id,
        generated_at=generated_at,
        overall_metrics=overall,
        degradation_events=[],
        drift={k: v for k, v in drift_out.items()},  # typed in Step 2
        notes=["Step 1 skeleton report (rolling degradation not implemented yet)."],
    )

    report_json = asdict(report)
    report_md = (
        f"# FGDM Report\n\n"
        f"- run_id: `{report.run_id}`\n"
        f"- generated_at: `{report.generated_at}`\n\n"
        f"## Overall metrics\n"
        f"- MAE: {report.overall_metrics.mae:.6f}\n"
        f"- RMSE: {report.overall_metrics.rmse:.6f}\n"
        f"- MAPE: {report.overall_metrics.mape:.6f}\n"
    )

    return MonitoringResponse(report_json=report_json, report_markdown=report_md)