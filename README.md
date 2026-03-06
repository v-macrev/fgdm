# FGDM — Forecast Governance & Drift Monitoring

A lightweight, production-grade micro-framework for monitoring forecast quality and data drift using clean architecture boundaries.

## Goals
- Accept canonical long-format forecast data: `cd_key | ds | y | y_hat`
- Compute: MAE, RMSE, MAPE
- Detect rolling degradation
- Drift detection: KS-test + PSI
- Generate deterministic JSON + Markdown reports
- Provide CLI entry point

## Architecture
- `fgdm.domain`: Pure computations (metrics, drift, models, errors). Deterministic; no I/O.
- `fgdm.application`: Use-cases orchestration (DTOs + monitoring service).
- `fgdm.infrastructure`: CLI + report writers.

## Install (editable)
```bash
pip install -e .