# FGDM Architecture

FGDM follows a lightweight Clean Architecture approach.

## Layers

### Domain

Pure business logic and deterministic computation.

Contains:

- forecast error metrics
- rolling degradation logic
- drift detection
- governance severity rules
- validation policies
- typed report models

The domain layer does not perform file I/O or CLI parsing.

### Application

Coordinates use-cases.

Contains:

- request / response DTOs
- monitoring orchestration
- demo dataset generation

The application layer connects domain components into executable workflows.

### Infrastructure

Handles external interfaces.

Contains:

- CLI entrypoints
- CSV / Parquet loading
- JSON / Markdown reporting
- demo dataset writers

This layer translates external inputs into application requests and persists outputs.

## Request flow

1. CLI receives user arguments
2. Infrastructure loads canonical input data
3. Application service validates and orchestrates the run
4. Domain computes:
   - metrics
   - rolling degradation
   - drift
   - severity
   - validation summary
5. Infrastructure writes:
   - JSON report
   - Markdown report

## Directory structure

```text
src/fgdm
├── application
│   ├── demo_data.py
│   ├── dto.py
│   └── monitoring_service.py
├── domain
│   ├── drift.py
│   ├── errors.py
│   ├── governance.py
│   ├── metrics.py
│   ├── models.py
│   ├── rolling.py
│   ├── validation.py
│   └── validation_models.py
└── infrastructure
    ├── cli.py
    ├── demo_writer.py
    ├── generate_demo.py
    ├── io.py
    └── reporting
        ├── json_reporter.py
        └── markdown_reporter.py
````

## Design goals

* deterministic outputs
* explicit types
* minimal runtime dependencies
* auditability
* testability
* production-friendly CLI operation
