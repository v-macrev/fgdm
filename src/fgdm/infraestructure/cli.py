from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from fgdm.application.dto import MonitoringRequest
from fgdm.application.monitoring_service import run_monitoring
from fgdm.domain.models import CanonicalRow


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="fgdm",
        description="FGDM - Forecast Governance & Drift Monitoring (micro-framework).",
    )
    p.add_argument("--version", action="store_true", help="Print version and exit.")
    p.add_argument("--run-id", type=str, default="local-run", help="Run identifier.")

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.version:
        from fgdm import __version__

        print(__version__)
        return 0

    demo_rows = [
        CanonicalRow(cd_key="A", ds=date(2026, 1, 1), y=10.0, y_hat=9.5),
        CanonicalRow(cd_key="A", ds=date(2026, 1, 2), y=12.0, y_hat=11.0),
        CanonicalRow(cd_key="B", ds=date(2026, 1, 1), y=7.0, y_hat=7.2),
    ]

    req = MonitoringRequest(
        run_id=args.run_id,
        canonical_rows=demo_rows,
        drift_series_baseline={},
        drift_series_current={},
        drift_config=None,
    )

    res = run_monitoring(req)

    json.dump(res.report_json, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())