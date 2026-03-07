# Forecast Governance & Drift Monitoring (FGDM)

Lightweight, production-oriented micro-framework for forecast quality monitoring and statistical drift detection.

FGDM evaluates canonical forecast outputs and produces deterministic governance reports for validation, auditing, and CI/CD gating.

## Why this project exists

Forecasting systems rarely fail in dramatic ways. They degrade quietly, drift statistically, and then ruin decisions with the calm confidence of a broken compass.

FGDM exists to monitor that behaviour explicitly.

It provides:

- forecast error metrics
- rolling degradation detection
- statistical drift diagnostics
- dataset validation rules
- governance severity signals
- deterministic JSON and Markdown reporting
- CI-friendly exit codes

## Canonical input schema

FGDM expects long-format forecast outputs with the following columns:

```text
cd_key | ds | y | y_hat
````

Where:

* `cd_key` = entity identifier
* `ds` = date
* `y` = actual value
* `y_hat` = predicted value

Supported formats:

* `.csv`
* `.parquet`

## Core capabilities

### Metrics

* MAE
* RMSE
* MAPE

### Drift detection

* KS test
* PSI

### Performance monitoring

* rolling window degradation
* baseline vs current comparison
* top offenders by `cd_key`
* per-key quality breakdown

### Governance

* validation summary
* rule breaches
* quality / drift / overall severity
* fail-on-severity CLI gating

## Architecture

FGDM follows a lightweight Clean Architecture approach.

* `domain` → pure computations and typed models
* `application` → orchestration and use-cases
* `infrastructure` → CLI, loaders, reporters

See [docs/architecture.md](docs/architecture.md).

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick demo

Generate demo data:

```bash
fgdm-demo-data --output-dir demo_data
```

Run monitoring:

```bash
fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id demo_csv
```

For a full walkthrough, see [docs/demo.md](docs/demo.md).

## Deterministic execution

FGDM supports reproducible timestamps via:

* `--generated-at`
* `SOURCE_DATE_EPOCH`

Example:

```bash
fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id deterministic_demo --generated-at 2026-03-03T00:00:00+00:00
```

## CI / pipeline gating

Fail the process when severity reaches a threshold:

```bash
fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id gated_demo --fail-on-severity warn
```

Exit codes:

* `0` → success
* `2` → FGDM domain error
* `3` → unexpected runtime error
* `4` → governance gate triggered

## Example outputs

FGDM generates:

* JSON report for automation
* Markdown report for humans

Reports include:

* overall metrics
* baseline vs current metrics
* rolling performance windows
* drift results
* degradation events
* top offenders
* per-key quality
* validation summary
* rule breaches

## Testing

```bash
pytest
```

## License

GNU Affero General Public License v3.0

See the `LICENSE` file.