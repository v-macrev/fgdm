from __future__ import annotations

import pytest

from fgdm.domain.drift import DriftConfig, detect_drift, ks_test, psi
from fgdm.domain.errors import ValidationError


def test_ks_test_identical_series() -> None:
    stat, pvalue = ks_test([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert stat == pytest.approx(0.0)
    assert 0.0 <= pvalue <= 1.0


def test_detect_drift_returns_non_negative_psi() -> None:
    result = detect_drift(
        baseline=[1.0, 1.5, 2.0, 2.5, 3.0],
        current=[3.0, 3.5, 4.0, 4.5, 5.0],
        cfg=DriftConfig(psi_bins=5),
    )
    assert 0.0 <= result.ks_stat <= 1.0
    assert 0.0 <= result.ks_pvalue <= 1.0
    assert result.psi >= 0.0


def test_psi_small_for_identical_distributions() -> None:
    value = psi(
        baseline=[1.0, 2.0, 3.0, 4.0, 5.0],
        current=[1.0, 2.0, 3.0, 4.0, 5.0],
        bins=5,
    )
    assert value == pytest.approx(0.0, abs=1e-6)


def test_drift_config_validation() -> None:
    with pytest.raises(ValidationError):
        DriftConfig(psi_bins=1).validate()


def test_detect_drift_raises_on_empty() -> None:
    with pytest.raises(ValidationError):
        detect_drift([], [1.0, 2.0])
    with pytest.raises(ValidationError):
        detect_drift([1.0, 2.0], [])