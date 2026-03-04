from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fgdm.application.dto import MonitoringRequest
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.drift import DriftConfig
from fgdm.domain.errors import FGDMError
from fgdm.domain.governance import PolicyConfig
from fgdm.domain.rolling import RollingConfig
from fgdm.infrastructure.io import CanonicalCSVConfig, load_canonical_csv
from fgdm.infrastructure.reporting.json_reporter import write_json
from fgdm.infrastructure.reporting.markdown_reporter import write_markdown


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fgdm",
        description="FGDM - Forecast Governance & Drift Monitoring (micro-framework).",
    )
    p.add_argument("--version", action="store_true", help="Print version and exit.")

    p.add_argument("--input", type=str, required=False, help="Path to canonical CSV input.")
    p.add_argument("--output-dir", type=str, default="fgdm_out", help="Directory for report outputs.")
    p.add_argument("--run-id", type=str, default="run", help="Run identifier (stable, user-defined).")
    p.add_argument(
        "--generated-at",
        type=str,
        default=None,
        help="Override generated_at (ISO-8601). If omitted, uses SOURCE_DATE_EPOCH or current UTC.",
    )

    # CSV config
    p.add_argument("--cd-key-col", type=str, default="cd_key")
    p.add_argument("--ds-col", type=str, default="ds")
    p.add_argument("--y-col", type=str, default="y")
    p.add_argument("--y-hat-col", type=str, default="y_hat")
    p.add_argument("--delimiter", type=str, default=",")
    p.add_argument("--encoding", type=str, default="utf-8")

    # Rolling config
    p.add_argument("--rolling-window-days", type=int, default=7)
    p.add_argument("--baseline-window-days", type=int, default=28)
    p.add_argument("--min-points-per-window", type=int, default=30)
    p.add_argument("--mape-eps", type=float, default=1e-9)

    p.add_argument("--degradation-abs", type=float, default=0.0)
    p.add_argument("--degradation-rel", type=float, default=0.2)

    # Drift config
    p.add_argument("--psi-bins", type=int, default=10)
    p.add_argument(
        "--drift-series",
        type=str,
        default="residual",
        help="Comma-separated: residual,y,y_hat",
    )

    # Policy config (severity)
    p.add_argument("--quality-warn-rel", type=float, default=0.2)
    p.add_argument("--quality-crit-rel", type=float, default=0.5)

    p.add_argument("--drift-warn-psi", type=float, default=0.2)
    p.add_argument("--drift-crit-psi", type=float, default=0.5)

    p.add_argument("--drift-warn-ks-p", type=float, default=0.05)
    p.add_argument("--drift-crit-ks-p", type=float, default=0.01)

    p.add_argument("--top-offenders-n", type=int, default=10)

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.version:
        from fgdm import __version__

        print(__version__)
        return 0

    if not args.input:
        print("ERROR: --input is required for monitoring runs.", file=sys.stderr)
        return 2

    try:
        input_path = Path(args.input).expanduser().resolve()
        output_dir = Path(args.output_dir).expanduser().resolve()

        csv_cfg = CanonicalCSVConfig(
            cd_key_col=args.cd_key_col,
            ds_col=args.ds_col,
            y_col=args.y_col,
            y_hat_col=args.y_hat_col,
            delimiter=args.delimiter,
            encoding=args.encoding,
        )
        rows = load_canonical_csv(input_path, csv_cfg)

        rolling = RollingConfig(
            rolling_window_days=args.rolling_window_days,
            baseline_window_days=args.baseline_window_days,
            min_points_per_window=args.min_points_per_window,
            mape_eps=args.mape_eps,
            degradation_abs_threshold=args.degradation_abs,
            degradation_rel_threshold=args.degradation_rel,
        )
        drift = DriftConfig(psi_bins=args.psi_bins)

        policy = PolicyConfig(
            degradation_warn_rel=args.quality_warn_rel,
            degradation_crit_rel=args.quality_crit_rel,
            drift_warn_psi=args.drift_warn_psi,
            drift_crit_psi=args.drift_crit_psi,
            drift_warn_ks_pvalue=args.drift_warn_ks_p,
            drift_crit_ks_pvalue=args.drift_crit_ks_p,
            top_offenders_n=args.top_offenders_n,
        )

        drift_series = [s.strip() for s in (args.drift_series or "").split(",") if s.strip()]

        req = MonitoringRequest(
            run_id=args.run_id,
            canonical_rows=rows,
            rolling=rolling,
            drift=drift,
            policy=policy,
            drift_series=drift_series,
        )

        res = run_monitoring(req, generated_at=args.generated_at)

        json_path = output_dir / f"{args.run_id}.json"
        md_path = output_dir / f"{args.run_id}.md"

        write_json(res.report_dict, json_path)
        write_markdown(res.report_dict, md_path)

        print(f"Wrote JSON: {json_path}")
        print(f"Wrote Markdown: {md_path}")
        return 0

    except FGDMError as e:
        print(f"FGDM error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())