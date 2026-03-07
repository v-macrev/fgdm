from __future__ import annotations

import csv
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from fgdm.domain.models import CanonicalRow


def write_demo_csv(rows: list[CanonicalRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["cd_key", "ds", "y", "y_hat"])

        for r in rows:
            writer.writerow([r.cd_key, r.ds.isoformat(), r.y, r.y_hat])


def write_demo_parquet(rows: list[CanonicalRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    table = pa.table(
        {
            "cd_key": [r.cd_key for r in rows],
            "ds": [r.ds for r in rows],
            "y": [r.y for r in rows],
            "y_hat": [r.y_hat for r in rows],
        }
    )

    pq.write_table(table, path)