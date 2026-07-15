import pandas as pd

from src.reconciliation import reconcile


def _ledger():
    return pd.DataFrame(
        [
            {"transaction_id": "T1", "amount": 100.00},
            {"transaction_id": "T2", "amount": 50.00},
            {"transaction_id": "T3", "amount": 25.00},   # missing from bank
            {"transaction_id": "T4", "amount": 10.00},   # penny break
        ]
    )


def _bank():
    return pd.DataFrame(
        [
            {"txn_id": "T1", "amount": 100.00},
            {"txn_id": "T2", "amount": 50.00},
            {"txn_id": "T4", "amount": 10.01},           # off by a penny
            {"txn_id": "T5", "amount": 99.00},           # not in ledger
        ]
    )


def test_buckets_are_classified():
    r = reconcile(_ledger(), _bank(), tolerance=0.001)
    s = r.summary()
    assert s["matched"] == 2
    assert s["amount_break"] == 1
    assert s["missing_bank"] == 1
    assert s["missing_ledger"] == 1


def test_tolerance_absorbs_penny_break():
    r = reconcile(_ledger(), _bank(), tolerance=0.02)
    assert r.summary()["amount_break"] == 0
    assert r.summary()["matched"] == 3


def test_break_count_aggregates():
    r = reconcile(_ledger(), _bank(), tolerance=0.001)
    assert r.break_count == 3
