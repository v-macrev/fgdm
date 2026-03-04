from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from fgdm.domain.errors import ValidationError


class Severity(str, Enum):
    OK = "ok"
    WARN = "warn"
    CRIT = "crit"


@dataclass(frozen=True)
class PolicyConfig:
    degradation_warn_rel: float = 0.2
    degradation_crit_rel: float = 0.5

    drift_warn_psi: float = 0.2
    drift_crit_psi: float = 0.5

    drift_warn_ks_pvalue: float = 0.05
    drift_crit_ks_pvalue: float = 0.01

    top_offenders_n: int = 10

    def validate(self) -> None:
        if self.degradation_warn_rel < 0 or self.degradation_crit_rel < 0:
            raise ValidationError("Degradation thresholds must be >= 0.")
        if self.degradation_warn_rel > self.degradation_crit_rel:
            raise ValidationError("degradation_warn_rel must be <= degradation_crit_rel.")

        if self.drift_warn_psi < 0 or self.drift_crit_psi < 0:
            raise ValidationError("PSI thresholds must be >= 0.")
        if self.drift_warn_psi > self.drift_crit_psi:
            raise ValidationError("drift_warn_psi must be <= drift_crit_psi.")

        if not (0 < self.drift_warn_ks_pvalue <= 1.0) or not (0 < self.drift_crit_ks_pvalue <= 1.0):
            raise ValidationError("KS p-value thresholds must be in (0,1].")
        if self.drift_warn_ks_pvalue < self.drift_crit_ks_pvalue:
            raise ValidationError("drift_warn_ks_pvalue must be >= drift_crit_ks_pvalue.")

        if self.top_offenders_n < 1:
            raise ValidationError("top_offenders_n must be >= 1.")


def max_severity(a: Severity, b: Severity) -> Severity:
    if a == Severity.CRIT or b == Severity.CRIT:
        return Severity.CRIT
    if a == Severity.WARN or b == Severity.WARN:
        return Severity.WARN
    return Severity.OK


def severity_from_degradation_rel(rel_delta: float, *, warn_rel: float, crit_rel: float) -> Severity:
    if rel_delta >= crit_rel:
        return Severity.CRIT
    if rel_delta >= warn_rel:
        return Severity.WARN
    return Severity.OK


def severity_from_drift(*, psi_value: float, ks_pvalue: float, warn_psi: float, crit_psi: float,
                        warn_p: float, crit_p: float) -> Severity:
    psi_sev = Severity.OK
    if psi_value >= crit_psi:
        psi_sev = Severity.CRIT
    elif psi_value >= warn_psi:
        psi_sev = Severity.WARN

    p_sev = Severity.OK
    if ks_pvalue <= crit_p:
        p_sev = Severity.CRIT
    elif ks_pvalue <= warn_p:
        p_sev = Severity.WARN

    return max_severity(psi_sev, p_sev)