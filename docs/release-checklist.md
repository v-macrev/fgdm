# Release Checklist

## Pre-release validation

- [ ] `pip install -e ".[dev]"`
- [ ] `ruff check .`
- [ ] `mypy src`
- [ ] `pytest`

## Demo validation

- [ ] `fgdm-demo-data --output-dir demo_data`
- [ ] `fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id demo_csv`
- [ ] `fgdm --input demo_data/forecast_demo.parquet --output-dir demo_output --run-id demo_parquet`

## Repository validation

- [ ] `README.md` is current and in English
- [ ] `LICENSE` contains the full AGPL v3 text
- [ ] `CHANGELOG.md` has a release entry
- [ ] CI passes on GitHub Actions

## Release metadata

- [ ] version updated consistently
- [ ] tag created
- [ ] release notes prepared