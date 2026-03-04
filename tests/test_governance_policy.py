from __future__ import annotations

from fgdm.domain.governance import Severity, severity_from_degradation_rel, severity_from_drift


def test_severity_from_degradation_rel() -> None:
    assert severity_from_degradation_rel(0.0, warn_rel=0.2, crit_rel=0.5) == Severity.OK
    assert severity_from_degradation_rel(0.2, warn_rel=0.2, crit_rel=0.5) == Severity.WARN
    assert severity_from_degradation_rel(0.7, warn_rel=0.2, crit_rel=0.5) == Severity.CRIT


def test_severity_from_drift() -> None:
    assert (
        severity_from_drift(
            psi_value=0.01,
            ks_pvalue=0.8,
            warn_psi=0.2,
            crit_psi=0.5,
            warn_p=0.05,
            crit_p=0.01,
        )
        == Severity.OK
    )

    assert (
        severity_from_drift(
            psi_value=0.25,
            ks_pvalue=0.8,
            warn_psi=0.2,
            crit_psi=0.5,
            warn_p=0.05,
            crit_p=0.01,
        )
        == Severity.WARN
    )

    assert (
        severity_from_drift(
            psi_value=0.01,
            ks_pvalue=0.001,
            warn_psi=0.2,
            crit_psi=0.5,
            warn_p=0.05,
            crit_p=0.01,
        )
        == Severity.CRIT
    )