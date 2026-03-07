from __future__ import annotations

import argparse
from pathlib import Path

from fgdm.application.demo_data import DemoDatasetConfig, generate_demo_dataset
from fgdm.infrastructure.demo_writer import write_demo_csv, write_demo_parquet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate demo FGDM datasets.")

    parser.add_argument("--output-dir", type=str, default="demo_data")
    parser.add_argument("--keys", type=int, default=5)
    parser.add_argument("--days", type=int, default=60)

    args = parser.parse_args(argv)

    cfg = DemoDatasetConfig(
        n_keys=args.keys,
        n_days=args.days,
    )

    rows = generate_demo_dataset(cfg)

    out = Path(args.output_dir)

    csv_path = out / "forecast_demo.csv"
    pq_path = out / "forecast_demo.parquet"

    write_demo_csv(rows, csv_path)
    write_demo_parquet(rows, pq_path)

    print(f"Demo CSV written: {csv_path}")
    print(f"Demo Parquet written: {pq_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())