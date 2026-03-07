from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from scipy.stats import ks_2samp

from fgdm.domain.errors import ValidationError
from fgdm.domain.models import DriftResult


@dataclass(frozen=True)
class DriftConfig:
    psi_bins: int = 10

    def validate(self) -> None:
        if self.psi_bins < 2:
            raise ValidationError("psi_bins must be >= 2.")


def _to_1d_float_array(values: Iterable[float], name: str) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        raise ValidationError(f"{name} must not be empty.")
    if not np.isfinite(arr).all():
        raise ValidationError(f"{name} contains non-finite values.")
    return arr


def ks_test(baseline: Iterable[float], current: Iterable[float]) -> tuple[float, float]:
    b = _to_1d_float_array(baseline, "baseline")
    c = _to_1d_float_array(current, "current")
    res = ks_2samp(b, c, alternative="two-sided", mode="auto")
    return float(res.statistic), float(res.pvalue)


def psi(baseline: Iterable[float], current: Iterable[float], bins: int) -> float:
    if bins < 2:
        raise ValidationError("bins must be >= 2.")

    b = _to_1d_float_array(baseline, "baseline")
    c = _to_1d_float_array(current, "current")

    quantiles = np.linspace(0.0, 1.0, bins + 1)
    edges = np.quantile(b, quantiles)

    eps = 1e-12
    for i in range(1, edges.size):
        if edges[i] <= edges[i - 1]:
            edges[i] = edges[i - 1] + eps

    b_counts, _ = np.histogram(b, bins=edges)
    c_counts, _ = np.histogram(c, bins=edges)

    b_pct = b_counts / max(float(b.size), 1.0)
    c_pct = c_counts / max(float(c.size), 1.0)

    smooth = 1e-9
    b_pct = np.clip(b_pct, smooth, 1.0)
    c_pct = np.clip(c_pct, smooth, 1.0)

    return float(np.sum((c_pct - b_pct) * np.log(c_pct / b_pct)))


def detect_drift(
    baseline: Iterable[float],
    current: Iterable[float],
    cfg: DriftConfig | None = None,
) -> DriftResult:
    cfg = cfg or DriftConfig()
    cfg.validate()
    ks_stat, ks_pvalue = ks_test(baseline, current)
    psi_value = psi(baseline, current, bins=cfg.psi_bins)
    return DriftResult(ks_stat=ks_stat, ks_pvalue=ks_pvalue, psi=psi_value)