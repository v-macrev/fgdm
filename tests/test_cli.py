from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fgdm.infrastructure.cli import main


def _write_csv(path: Path, rows: list[str]) -> None:
    path.write_text(
        "cd_key,ds,y,y_hat\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )


def _iso_day(offset: int) -> str:
    return (date(2026, 1, 1) + timedelta(days=offset)).isoformat()


def test_cli_success_exit_code_zero(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    output_dir = tmp_path / "out"

    rows: list[str] = []
    for i in range(35):
        ds = _iso_day(i)
        val = float(i + 1)
        rows.append(f"A,{ds},{val},{val - 0.1}")
        rows.append(f"B,{ds},{val},{val - 0.2}")

    _write_csv(input_csv, rows)

    code = main(
        [
            "--input",
            str(input_csv),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "ok_run",
            "--generated-at",
            "2026-03-03T00:00:00+00:00",
            "--min-points-per-window",
            "10",
            "--fail-on-severity",
            "none",
        ]
    )

    assert code == 0
    assert (output_dir / "ok_run.json").exists()
    assert (output_dir / "ok_run.md").exists()


def test_cli_fail_on_warn_returns_gate_code(tmp_path: Path) -> None:
    input_csv = tmp_path / "input_warn.csv"
    output_dir = tmp_path / "out_warn"

    rows: list[str] = []
    for i in range(35):
        ds = _iso_day(i)
        val = float(i + 1)
        rows.append(f"A,{ds},{val},{val - 0.1}")
        rows.append(f"A,{ds},{val + 1.0},{val - 0.2}")

    _write_csv(input_csv, rows)

    code = main(
        [
            "--input",
            str(input_csv),
            "--output-dir",
            str(output_dir),
            "--run-id",
            "warn_run",
            "--generated-at",
            "2026-03-03T00:00:00+00:00",
            "--min-points-per-window",
            "10",
            "--max-duplicate-key-ds-ratio",
            "0.0",
            "--fail-on-severity",
            "warn",
        ]
    )

    assert code == 4
    assert (output_dir / "warn_run.json").exists()
    assert (output_dir / "warn_run.md").exists()