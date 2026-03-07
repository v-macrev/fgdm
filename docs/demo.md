# FGDM Demo Guide

This guide shows the fastest way to run FGDM locally.

## 1. Install

```bash
pip install -e ".[dev]"
````

## 2. Generate demo data

### Linux / macOS

```bash
fgdm-demo-data --output-dir demo_data
```

### Windows PowerShell

```powershell
fgdm-demo-data --output-dir demo_data
```

## 3. Run FGDM

### CSV input

```bash
fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id demo_csv
```

### Parquet input

```bash
fgdm --input demo_data/forecast_demo.parquet --output-dir demo_output --run-id demo_parquet
```

### Windows PowerShell multiline example

```powershell
fgdm `
  --input demo_data/forecast_demo.csv `
  --output-dir demo_output `
  --run-id demo_csv
```

## 4. Inspect outputs

FGDM will generate:

* `demo_output/demo_csv.json`
* `demo_output/demo_csv.md`

## 5. Run tests

```bash
pytest
```

## 6. Use severity gating

```bash
fgdm --input demo_data/forecast_demo.csv --output-dir demo_output --run-id gated_demo --fail-on-severity warn
```