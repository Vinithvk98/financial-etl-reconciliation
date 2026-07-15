"""Pipeline orchestrator.

Chains the stages end to end: extract source chunks -> transform (map to
target schema) -> data-quality gate -> load clean + quarantine ->
reconcile against the bank feed -> persist breaks. Every stage writes to
the audit trail so the whole run is traceable.

Chunked reads keep memory flat regardless of source size, which is what
lets the same code process a 10M+ row feed on a laptop or a Lambda.

Usage:
    python -m src.pipeline --source data/source --reset
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import data_quality, load, reconciliation, transform
from .audit import AuditTrail
from .config import settings


def run(source_dir: str | Path, reset: bool = False,
        chunk_size: int | None = None) -> dict:
    source_dir = Path(source_dir)
    chunk_size = chunk_size or settings.chunk_size
    audit = AuditTrail()
    engine = load.get_engine()
    mapping = transform.load_mapping()

    if_exists = "replace" if reset else "append"
    audit.record("start", "pipeline run started", source=str(source_dir))

    rows_in = rows_clean = rows_quarantined = 0
    curated_frames: list[pd.DataFrame] = []

    reader = pd.read_csv(source_dir / "transactions.csv",
                         dtype=str, chunksize=chunk_size)
    for i, chunk in enumerate(reader):
        tf = transform.transform(chunk, mapping)
        dq = data_quality.run_checks(tf, mapping)
        load.load_curated(dq.clean, engine, if_exists if i == 0 else "append")
        load.load_quarantine(dq.quarantine, engine, if_exists if i == 0 else "append")
        curated_frames.append(dq.clean[["transaction_id", "amount"]].assign(
            amount=pd.to_numeric(dq.clean["amount"], errors="coerce")))
        rows_in += dq.total
        rows_clean += len(dq.clean)
        rows_quarantined += len(dq.quarantine)
        audit.record("dq", f"chunk {i} checked", **dq.report())

    audit.record("load", "curated + quarantine loaded",
                 rows_in=rows_in, rows_clean=rows_clean,
                 rows_quarantined=rows_quarantined)

    # Reconciliation against the bank feed.
    ledger = pd.concat(curated_frames, ignore_index=True) if curated_frames else pd.DataFrame(
        columns=["transaction_id", "amount"])
    bank = pd.read_csv(source_dir / "bank_statement.csv")
    recon = reconciliation.reconcile(ledger, bank)
    breaks = pd.concat(
        [recon.amount_break.assign(break_type="amount_break"),
         recon.missing_bank.assign(break_type="missing_bank"),
         recon.missing_ledger.assign(break_type="missing_ledger")],
        ignore_index=True,
    )
    load.load_recon_breaks(breaks, engine, if_exists)
    audit.record("reconcile", "reconciliation complete", **recon.summary())

    result = {
        "run_id": audit.run_id,
        "rows_in": rows_in,
        "rows_clean": rows_clean,
        "rows_quarantined": rows_quarantined,
        "reconciliation": recon.summary(),
    }
    audit.record("done", "pipeline run finished", **result)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Run the ETL & reconciliation pipeline")
    p.add_argument("--source", type=Path, default=Path("data/source"))
    p.add_argument("--reset", action="store_true", help="replace target tables")
    p.add_argument("--chunk-size", type=int, default=None)
    args = p.parse_args()
    result = run(args.source, reset=args.reset, chunk_size=args.chunk_size)
    print("Pipeline complete:")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
