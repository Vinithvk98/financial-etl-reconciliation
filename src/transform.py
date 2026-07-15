"""Transform stage: source-to-target mapping and standardisation.

Renames and retypes raw source columns into the curated warehouse schema
defined in ``mapping/source_to_target.yaml``. Cleaning is deterministic and
non-destructive: rows that cannot be coerced are flagged rather than
silently dropped, so the data-quality stage can quarantine them with a
reason code.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from .config import ROOT, settings

MAPPING_PATH = ROOT / "mapping" / "source_to_target.yaml"


def load_mapping(path: Path | None = None) -> dict:
    with open(path or MAPPING_PATH) as fh:
        return yaml.safe_load(fh)


def apply_mapping(df: pd.DataFrame, mapping: dict | None = None) -> pd.DataFrame:
    """Rename source columns to target names per the mapping spec."""
    mapping = mapping or load_mapping()
    rename = {c["source"]: c["target"] for c in mapping["columns"]}
    out = df.rename(columns=rename)
    keep = [c["target"] for c in mapping["columns"]]
    return out[[c for c in keep if c in out.columns]]


def standardise(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce types and normalise values without dropping rows."""
    out = df.copy()
    out["amount_minor"] = (
        pd.to_numeric(out["amount"], errors="coerce") * 100
    ).round().astype("Int64")
    out["posted_at"] = pd.to_datetime(out["posted_at"], errors="coerce")
    out["currency_code"] = out["currency_code"].str.upper().str.strip()
    out["merchant_name"] = out["merchant_name"].str.strip().str.title()
    out["status"] = out["status"].str.upper().str.strip()
    return out


def transform(df: pd.DataFrame, mapping: dict | None = None) -> pd.DataFrame:
    return standardise(apply_mapping(df, mapping))
