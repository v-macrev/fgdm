from __future__ import annotations


def test_smoke_imports() -> None:
    import fgdm
    from fgdm.application.monitoring_service import run_monitoring
    from fgdm.domain.metrics import mae, mape, rmse
    from fgdm.domain.drift import detect_drift

    assert True