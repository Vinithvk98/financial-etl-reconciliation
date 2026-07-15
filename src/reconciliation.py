"""Reconciliation engine.

Matches the curated ledger against an external bank statement feed and
classifies every transaction into one of four buckets:

    matched        present in both, amounts agree within tolerance
    amount_break   present in both, amounts differ beyond tolerance
    missing_bank   in the ledger but absent from the bank feed
    missing_ledger in the bank feed but absent from the ledger

The tolerance absorbs currency rounding so genuine penny-level breaks are
surfaced without drowning in noise.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import settings


@dataclass
class ReconResult:
    matched: pd.DataFrame
    amount_break: pd.DataFrame
    missing_bank: pd.DataFrame
    missing_ledger: pd.DataFrame

    def summary(self) -> dict:
        return {
            "matched": len(self.matched),
            "amount_break": len(self.amount_break),
            "missing_bank": len(self.missing_bank),
            "missing_ledger": len(self.missing_ledger),
        }

    @property
    def break_count(self) -> int:
        return len(self.amount_break) + len(self.missing_bank) + len(self.missing_ledger)


def reconcile(ledger: pd.DataFrame, bank: pd.DataFrame,
              tolerance: float | None = None) -> ReconResult:
    tol = settings.reconciliation_tolerance if tolerance is None else tolerance

    led = ledger[["transaction_id", "amount"]].rename(columns={"amount": "amount_ledger"})
    led["amount_ledger"] = pd.to_numeric(led["amount_ledger"], errors="coerce")

    bnk = bank[["txn_id", "amount"]].rename(
        columns={"txn_id": "transaction_id", "amount": "amount_bank"}
    )
    bnk["amount_bank"] = pd.to_numeric(bnk["amount_bank"], errors="coerce")

    merged = led.merge(bnk, on="transaction_id", how="outer", indicator=True)
    merged["delta"] = (merged["amount_ledger"] - merged["amount_bank"]).abs()

    missing_bank = merged[merged["_merge"] == "left_only"]
    missing_ledger = merged[merged["_merge"] == "right_only"]
    both = merged[merged["_merge"] == "both"]

    matched = both[both["delta"] <= tol]
    amount_break = both[both["delta"] > tol]

    cols = ["transaction_id", "amount_ledger", "amount_bank", "delta"]
    return ReconResult(
        matched=matched[cols].reset_index(drop=True),
        amount_break=amount_break[cols].reset_index(drop=True),
        missing_bank=missing_bank[cols].reset_index(drop=True),
        missing_ledger=missing_ledger[cols].reset_index(drop=True),
    )
