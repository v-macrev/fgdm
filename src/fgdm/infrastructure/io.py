from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pyarrow.parquet as pq

from fgdm.domain.errors import ValidationError
from fgdm.domain.models import CanonicalRow


@dataclass(frozen=True)
class CanonicalCSVConfig:

    cd_key_col: str = "cd_key"
    ds_col: str = "ds"
    y_col: str = "y"
    y_hat_col: str = "y_hat"
    delimiter: str = ","
    encoding: str = "utf-8"

    def validate(self) -> None:
        if not self.cd_key_col or not self.ds_col or not self.y_col or not self.y_hat_col:
            raise ValidationError("CSV column names must not be empty.")
        if not self.delimiter:
            raise ValidationError("CSV delimiter must not be empty.")
        if not self.encoding:
            raise ValidationError("CSV encoding must not be empty.")


@dataclass(frozen=True)
class CanonicalParquetConfig:

    cd_key_col: str = "cd_key"
    ds_col: str = "ds"
    y_col: str = "y"
    y_hat_col: str = "y_hat"

    def validate(self) -> None:
        if not self.cd_key_col or not self.ds_col or not self.y_col or not self.y_hat_col:
            raise ValidationError("Parquet column names must not be empty.")


def _parse_date_iso(value: str, *, field: str) -> date:
    v = value.strip()
    try:
        return date.fromisoformat(v)
    except ValueError as e:
        raise ValidationError(f"Invalid {field} date '{value}'. Expected YYYY-MM-DD.") from e


def _parse_date_any(value: object, *, field: str) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return _parse_date_iso(value, field=field)
    raise ValidationError(f"Invalid {field} value '{value}'. Expected date or YYYY-MM-DD string.")


def _parse_float(value: object, *, field: str) -> float:
    if isinstance(value, float):
        x = value
    elif isinstance(value, int):
        x = float(value)
    elif isinstance(value, str):
        v = value.strip()
        try:
            x = float(v)
        except ValueError as e:
            raise ValidationError(f"Invalid float for {field}: '{value}'.") from e
    else:
        raise ValidationError(f"Invalid float for {field}: '{value}'.")

    if x != x:
        raise ValidationError(f"Non-finite value for {field}: '{value}'.")
    if x in (float("inf"), float("-inf")):
        raise ValidationError(f"Non-finite value for {field}: '{value}'.")
    return x


def _validate_input_file(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"Input file not found: {path}")
    if not path.is_file():
        raise ValidationError(f"Input path is not a file: {path}")


def detect_input_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".parquet":
        return "parquet"
    raise ValidationError(
        f"Unsupported input format for file '{path.name}'. Supported extensions: .csv, .parquet"
    )


def load_canonical_csv(
    path: Path,
    cfg: CanonicalCSVConfig | None = None,
) -> list[CanonicalRow]:
    cfg = cfg or CanonicalCSVConfig()
    cfg.validate()
    _validate_input_file(path)

    rows: list[CanonicalRow] = []
    with path.open("r", encoding=cfg.encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=cfg.delimiter)
        if reader.fieldnames is None:
            raise ValidationError("CSV has no header row.")
        header = set(reader.fieldnames)

        required = {cfg.cd_key_col, cfg.ds_col, cfg.y_col, cfg.y_hat_col}
        missing = sorted(required - header)
        if missing:
            raise ValidationError(f"CSV missing required columns: {missing}")

        for i, rec in enumerate(reader, start=2):
            try:
                cd_key = (rec.get(cfg.cd_key_col) or "").strip()
                if not cd_key:
                    raise ValidationError("cd_key must not be empty.")
                ds = _parse_date_iso(rec.get(cfg.ds_col) or "", field=cfg.ds_col)
                y = _parse_float(rec.get(cfg.y_col) or "", field=cfg.y_col)
                y_hat = _parse_float(rec.get(cfg.y_hat_col) or "", field=cfg.y_hat_col)
            except ValidationError as e:
                raise ValidationError(f"Row {i}: {e}") from e

            rows.append(CanonicalRow(cd_key=cd_key, ds=ds, y=y, y_hat=y_hat))

    if not rows:
        raise ValidationError("CSV contains no data rows.")
    return rows


def load_canonical_parquet(
    path: Path,
    cfg: CanonicalParquetConfig | None = None,
) -> list[CanonicalRow]:
    cfg = cfg or CanonicalParquetConfig()
    cfg.validate()
    _validate_input_file(path)

    table = pq.read_table(path)
    columns = set(table.column_names)

    required = {cfg.cd_key_col, cfg.ds_col, cfg.y_col, cfg.y_hat_col}
    missing = sorted(required - columns)
    if missing:
        raise ValidationError(f"Parquet missing required columns: {missing}")

    data = table.to_pylist()
    if not data:
        raise ValidationError("Parquet contains no data rows.")

    rows: list[CanonicalRow] = []
    for i, rec in enumerate(data, start=1):
        try:
            raw_key = rec.get(cfg.cd_key_col)
            cd_key = "" if raw_key is None else str(raw_key).strip()
            if not cd_key:
                raise ValidationError("cd_key must not be empty.")

            ds = _parse_date_any(rec.get(cfg.ds_col), field=cfg.ds_col)
            y = _parse_float(rec.get(cfg.y_col), field=cfg.y_col)
            y_hat = _parse_float(rec.get(cfg.y_hat_col), field=cfg.y_hat_col)
        except ValidationError as e:
            raise ValidationError(f"Row {i}: {e}") from e

        rows.append(CanonicalRow(cd_key=cd_key, ds=ds, y=y, y_hat=y_hat))

    return rows


def load_canonical_data(
    path: Path,
    *,
    csv_cfg: CanonicalCSVConfig | None = None,
    parquet_cfg: CanonicalParquetConfig | None = None,
) -> list[CanonicalRow]:
    fmt = detect_input_format(path)
    if fmt == "csv":
        return load_canonical_csv(path, csv_cfg)
    if fmt == "parquet":
        return load_canonical_parquet(path, parquet_cfg)
    raise ValidationError(f"Unsupported input format: {fmt}")