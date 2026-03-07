from __future__ import annotations

from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from fgdm.domain.errors import ValidationError
from fgdm.infrastructure.io import (
    detect_input_format,
    load_canonical_csv,
    load_canonical_data,
    load_canonical_parquet,
)


def test_detect_input_format_csv() -> None:
    assert detect_input_format(Path("sample.csv")) == "csv"


def test_detect_input_format_parquet() -> None:
    assert detect_input_format(Path("sample.parquet")) == "parquet"


def test_detect_input_format_rejects_unknown_extension() -> None:
    with pytest.raises(ValidationError):
        detect_input_format(Path("sample.txt"))


def test_load_canonical_csv(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text(
        "cd_key,ds,y,y_hat\n"
        "A,2026-01-01,10,9.5\n"
        "B,2026-01-02,20,19.0\n",
        encoding="utf-8",
    )

    rows = load_canonical_csv(path)
    assert len(rows) == 2
    assert rows[0].cd_key == "A"
    assert rows[0].ds == date(2026, 1, 1)
    assert rows[0].y == 10.0
    assert rows[0].y_hat == 9.5


def test_load_canonical_parquet(tmp_path: Path) -> None:
    path = tmp_path / "sample.parquet"

    table = pa.table(
        {
            "cd_key": ["A", "B"],
            "ds": [date(2026, 1, 1), date(2026, 1, 2)],
            "y": [10.0, 20.0],
            "y_hat": [9.5, 19.0],
        }
    )
    pq.write_table(table, path)

    rows = load_canonical_parquet(path)
    assert len(rows) == 2
    assert rows[1].cd_key == "B"
    assert rows[1].ds == date(2026, 1, 2)
    assert rows[1].y == 20.0
    assert rows[1].y_hat == 19.0


def test_load_canonical_data_routes_csv(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_text(
        "cd_key,ds,y,y_hat\n"
        "A,2026-01-01,10,9.5\n",
        encoding="utf-8",
    )

    rows = load_canonical_data(path)
    assert len(rows) == 1
    assert rows[0].cd_key == "A"


def test_load_canonical_data_routes_parquet(tmp_path: Path) -> None:
    path = tmp_path / "sample.parquet"
    table = pa.table(
        {
            "cd_key": ["A"],
            "ds": [date(2026, 1, 1)],
            "y": [10.0],
            "y_hat": [9.5],
        }
    )
    pq.write_table(table, path)

    rows = load_canonical_data(path)
    assert len(rows) == 1
    assert rows[0].cd_key == "A"