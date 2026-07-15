from src.transform import transform


def test_columns_are_renamed_to_target(raw_frame):
    out = transform(raw_frame)
    assert "transaction_id" in out.columns
    assert "currency_code" in out.columns
    assert "amount_minor" in out.columns


def test_amount_scaled_to_minor_units(raw_frame):
    out = transform(raw_frame)
    row = out[out["transaction_id"] == "TXN000000000002"].iloc[0]
    assert row["amount_minor"] == -800


def test_currency_and_merchant_normalised(raw_frame):
    out = transform(raw_frame)
    row = out.iloc[0]
    assert row["currency_code"] == "GBP"
    assert row["merchant_name"] == "Tesco"


def test_unparseable_amount_becomes_na(raw_frame):
    out = transform(raw_frame)
    row = out[out["account_id"] == "AC00000004"].iloc[0]
    assert row["amount_minor"] is None or str(row["amount_minor"]) == "<NA>"
