from src.data_quality import run_checks
from src.transform import transform


def test_clean_and_quarantine_partition(raw_frame):
    dq = run_checks(transform(raw_frame))
    assert dq.total == 5
    assert len(dq.clean) == 2          # two genuinely clean rows
    assert len(dq.quarantine) == 3


def test_reasons_are_tagged(raw_frame):
    dq = run_checks(transform(raw_frame))
    reasons = set(dq.quarantine["dq_reason"])
    assert "invalid_currency_code" in reasons
    assert "amount_not_numeric" in reasons
    assert "duplicate_transaction_id" in reasons


def test_pass_rate_between_zero_and_one(raw_frame):
    dq = run_checks(transform(raw_frame))
    assert 0.0 <= dq.pass_rate <= 1.0
    assert dq.report()["rows_clean"] == 2
