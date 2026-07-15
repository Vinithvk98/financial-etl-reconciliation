import pandas as pd
import pytest


@pytest.fixture
def raw_frame() -> pd.DataFrame:
    """Small raw frame mirroring the generator's output columns."""
    return pd.DataFrame(
        [
            # clean rows
            {"txn_id": "TXN000000000001", "account_id": "AC00000001",
             "posted_at": "2024-03-01 10:00:00", "merchant": "tesco",
             "channel": "CARD", "currency": "gbp", "amount": "12.50",
             "status": "posted"},
            {"txn_id": "TXN000000000002", "account_id": "AC00000002",
             "posted_at": "2024-03-01 11:00:00", "merchant": "uber",
             "channel": "CARD", "currency": "USD", "amount": "-8.00",
             "status": "SETTLED"},
            # bad currency
            {"txn_id": "TXN000000000003", "account_id": "AC00000003",
             "posted_at": "2024-03-01 12:00:00", "merchant": "shell",
             "channel": "WIRE", "currency": "XXX", "amount": "100.00",
             "status": "POSTED"},
            # missing amount
            {"txn_id": "TXN000000000004", "account_id": "AC00000004",
             "posted_at": "2024-03-01 13:00:00", "merchant": "apple",
             "channel": "ACH", "currency": "EUR", "amount": "",
             "status": "POSTED"},
            # duplicate id
            {"txn_id": "TXN000000000001", "account_id": "AC00000005",
             "posted_at": "2024-03-01 14:00:00", "merchant": "costa",
             "channel": "CARD", "currency": "GBP", "amount": "3.20",
             "status": "POSTED"},
        ]
    )
