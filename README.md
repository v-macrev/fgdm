# Forecast Governance & Drift Monitoring (FGDM)

Lightweight micro-framework for monitoring forecast quality and detecting statistical drift in production environments.

FGDM analyzes canonical forecast outputs and produces deterministic monitoring reports with statistical diagnostics, rolling degradation detection, and governance signals.

The project follows clean architecture principles and emphasizes reproducibility, explicit types, and engineering transparency.

---

# Core Capabilities

FGDM evaluates forecasting outputs using a canonical long-format dataset:

```
cd_key | ds | y | y_hat
```

Where:

* **cd_key** → entity identifier (SKU, store, product, etc.)
* **ds** → observation date
* **y** → actual value
* **y_hat** → predicted value

The framework provides:

* Forecast error metrics
* Rolling performance degradation detection
* Statistical drift detection
* Dataset validation checks
* Per-key quality diagnostics
* Deterministic monitoring reports

---

# Metrics

FGDM computes the following metrics:

* **MAE** — Mean Absolute Error
* **RMSE** — Root Mean Squared Error
* **MAPE** — Mean Absolute Percentage Error

Metrics are computed for:

* the entire dataset
* baseline vs current windows
* per-key diagnostics

---

# Drift Detection

FGDM detects distribution changes between baseline and current windows using:

### Kolmogorov-Smirnov Test (KS)

Measures whether two samples come from the same distribution.

Outputs:

* KS statistic
* p-value

### Population Stability Index (PSI)

Measures distribution shift using histogram binning.

Typical interpretation:

| PSI        | Interpretation    |
| ---------- | ----------------- |
| < 0.1      | stable            |
| 0.1 – 0.25 | moderate drift    |
| > 0.25     | significant drift |

---

# Rolling Degradation Detection

The framework compares two time windows:

```
Baseline Window (historical)
Current Window (recent)
```

Metrics are evaluated across rolling windows to detect:

* sudden performance degradation
* gradual error accumulation
* metric instability

---

# Validation Layer

FGDM validates incoming datasets before analysis.

Checks include:

* duplicate `(cd_key, ds)`
* zero-value ratios
* negative actual values
* negative predictions
* minimum unique keys
* minimum unique days

Validation breaches are recorded in the monitoring report.

---

# Input Formats

FGDM supports:

```
.csv
.parquet
```

Input format is detected automatically based on file extension.

---

# Installation

Install the project in editable mode:

```bash
pip install -e .
```

For development tools:

```bash
pip install -e ".[dev]"
```

---

# Running FGDM

### CSV Input

```bash
fgdm \
  --input ./data/canonical.csv \
  --output-dir ./fgdm_out \
  --run-id exp_csv
```

### Parquet Input

```bash
fgdm \
  --input ./data/canonical.parquet \
  --output-dir ./fgdm_out \
  --run-id exp_parquet
```

---

# Deterministic Runs

FGDM supports reproducible outputs.

You can fix the report timestamp:

```bash
fgdm \
  --input ./data/canonical.csv \
  --generated-at 2026-03-03T00:00:00+00:00
```

Alternatively:

```
SOURCE_DATE_EPOCH
```

can be used in CI environments.

---

# Pipeline Gating

FGDM can fail CI/CD pipelines based on severity.

Example:

```bash
fgdm \
  --input ./data/canonical.csv \
  --fail-on-severity warn
```

Severity levels:

```
ok
warn
crit
```

Exit codes:

| Code | Meaning                   |
| ---- | ------------------------- |
| 0    | success                   |
| 2    | FGDM domain error         |
| 3    | unexpected runtime error  |
| 4    | governance gate triggered |

---

# Outputs

FGDM produces two report formats:

### JSON

Machine-readable monitoring report.

Used for:

* CI validation
* dashboards
* automated pipelines

### Markdown

Human-readable analysis report.

Useful for:

* debugging
* experiment tracking
* audit trails

---

# Example Output Structure

```
FGDM Report

Overall metrics
Baseline vs Current comparison
Rolling performance series
Drift statistics
Degradation events
Top forecast offenders
Per-key diagnostics
Validation results
```

---

# Project Architecture

FGDM follows **Clean Architecture** principles.

```
src/fgdm
│
├── domain
│   ├── metrics
│   ├── drift
│   ├── rolling
│   ├── validation
│   └── governance
│
├── application
│   ├── dto
│   └── monitoring_service
│
└── infrastructure
    ├── cli
    ├── io
    └── reporting
```

Design goals:

* deterministic outputs
* explicit domain boundaries
* minimal dependencies
* testable components
* reproducible experiments

---

# Running Tests

```bash
pytest
```

---

# License

This project is licensed under the:

**GNU Affero General Public License v3.0**

```
GNU Affero General Public License
Version 3, 19 November 2007
```

See the `LICENSE` file for full terms.

---

# Project Status

FGDM is a lightweight monitoring framework designed for:

* forecasting pipelines
* MLOps governance
* drift detection
* model performance auditing

The project is intentionally minimal while remaining production-oriented.