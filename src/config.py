"""Central configuration for the ETL & reconciliation engine.

Values are read from environment variables so the same code runs locally,
in CI, and against AWS Lambda without modification. Sensible defaults keep
the demo runnable with zero setup.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    # --- Storage --------------------------------------------------------
    # In production these point at real S3 buckets; in tests moto stubs them.
    s3_bucket: str = os.getenv("ETL_S3_BUCKET", "fin-etl-landing")
    s3_region: str = os.getenv("AWS_DEFAULT_REGION", "eu-west-1")
    raw_prefix: str = "raw/transactions/"
    curated_prefix: str = "curated/transactions/"

    # --- Target warehouse ----------------------------------------------
    # Default is a local SQLite file so the pipeline runs anywhere. Point
    # ETL_TARGET_DSN at Postgres/MSSQL for a real deployment, e.g.
    #   postgresql+psycopg2://user:pw@host:5432/warehouse
    #   mssql+pyodbc://user:pw@host/warehouse?driver=ODBC+Driver+17+for+SQL+Server
    target_dsn: str = os.getenv("ETL_TARGET_DSN", f"sqlite:///{DATA_DIR / 'warehouse.db'}")

    # --- Data generation ------------------------------------------------
    default_rows: int = int(os.getenv("ETL_ROWS", "1000000"))
    chunk_size: int = int(os.getenv("ETL_CHUNK", "250000"))
    seed: int = int(os.getenv("ETL_SEED", "42"))

    # --- Data quality thresholds ---------------------------------------
    max_null_rate: float = 0.0            # zero tolerance on key columns
    reconciliation_tolerance: float = 0.01  # currency rounding tolerance

    currencies: tuple[str, ...] = field(default_factory=lambda: ("GBP", "USD", "EUR", "INR"))


settings = Settings()
