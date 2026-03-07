# Changelog

All notable changes to this project will be documented in this file.

The format is intentionally simple and human-readable.

## [0.1.0] - 2026-03-06

### Added
- Clean architecture project structure
- Canonical long-format monitoring input model (`cd_key`, `ds`, `y`, `y_hat`)
- Forecast quality metrics: MAE, RMSE, MAPE
- Rolling degradation detection
- Drift detection using KS test and PSI
- JSON and Markdown reporting
- CLI entrypoint for monitoring execution
- Severity policy layer (`ok`, `warn`, `crit`)
- Validation summary and rule breach reporting
- Per-key quality and top offenders analysis
- CSV and Parquet ingestion
- Demo dataset generator and demo CLI
- Deterministic test suite
- GitHub Actions CI workflow
- Architecture and demo documentation

### Fixed
- Date normalization for JSON serialization
- Enum normalization for CLI severity gating and Markdown rendering
- Circular import between validation and domain models
- Test dataset date generation bugs

### Licensing
- Project metadata aligned to GNU Affero General Public License v3.0