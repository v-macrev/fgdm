from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta

from fgdm.domain.models import CanonicalRow


@dataclass(frozen=True)
class DemoDatasetConfig:
    n_keys: int = 5
    n_days: int = 60
    seed: int = 42
    drift_start_day: int = 45


def generate_demo_dataset(cfg: DemoDatasetConfig) -> list[CanonicalRow]:
    rng = random.Random(cfg.seed)
    rows: list[CanonicalRow] = []

    start = date(2026, 1, 1)

    for k in range(cfg.n_keys):
        key = f"SKU_{k + 1:02d}"

        for i in range(cfg.n_days):
            ds = start + timedelta(days=i)

            base = 100.0 + (k * 5.0)
            seasonal = 10.0 * (i % 7) / 7.0
            noise = rng.uniform(-2.0, 2.0)

            y = base + seasonal + noise

            drift = 10.0 if i >= cfg.drift_start_day else 0.0
            y_hat = y - rng.uniform(0.0, 3.0) + drift

            rows.append(
                CanonicalRow(
                    cd_key=key,
                    ds=ds,
                    y=float(round(y, 3)),
                    y_hat=float(round(y_hat, 3)),
                )
            )

    return rows