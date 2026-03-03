from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

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


def _parse_date_iso(value: str, *, field: str) -> date:
    v = value.strip()
    try:
        return date.fromisoformat(v)
    except ValueError as e:
        raise ValidationError(f"Invalid {field} date '{value}'. Expected YYYY-MM-DD.") from e


def _parse_float(value: str, *, field: str) -> float:
    v = value.strip()
    try:
        x = float(v)
    except ValueError as e:
        raise ValidationError(f"Invalid float for {field}: '{value}'.") from e
    if x != x:  # NaN
        raise ValidationError(f"Non-finite value for {field}: '{value}'.")
    if x in (float("inf"), float("-inf")):
        raise ValidationError(f"Non-finite value for {field}: '{value}'.")
    return x


def load_canonical_csv(path: Path, cfg: CanonicalCSVConfig | None = None) -> list[CanonicalRow]:
    cfg = cfg or CanonicalCSVConfig()
    cfg.validate()

    if not path.exists():
        raise ValidationError(f"Input file not found: {path}")
    if not path.is_file():
        raise ValidationError(f"Input path is not a file: {path}")

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

        for i, rec in enumerate(reader, start=2):  # start=2 to account for header line
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