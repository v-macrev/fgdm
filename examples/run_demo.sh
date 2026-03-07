#!/usr/bin/env bash

set -e

echo "Generating demo dataset..."
fgdm-demo-data --output-dir ./demo_data

echo "Running FGDM..."
fgdm \
  --input ./demo_data/forecast_demo.csv \
  --output-dir ./demo_output \
  --run-id demo_run

echo "Demo complete."