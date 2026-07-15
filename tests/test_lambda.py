"""End-to-end Lambda test against a moto-mocked S3.

Exercises the full contract: land both feeds in S3, fire the S3 event at
the handler, and assert a run summary is written back to the curated prefix.
"""
import os

import boto3
import pytest
from moto import mock_aws

from src import generate_data, s3_utils
from src.config import settings


@pytest.fixture
def s3_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", settings.s3_region)
    # Isolate the target warehouse in the test's temp dir.
    monkeypatch.setenv("ETL_TARGET_DSN", f"sqlite:///{tmp_path / 'wh.db'}")
    with mock_aws():
        s3_utils.ensure_bucket()
        # Generate a tiny feed and land it in S3.
        src = tmp_path / "source"
        generate_data.generate(2000, src)
        base = "raw/transactions/2024-03-01"
        s3_utils.upload(src / "transactions.csv", f"{base}/transactions.csv")
        s3_utils.upload(src / "bank_statement.csv", f"{base}/bank_statement.csv")
        yield base


def test_lambda_processes_s3_event(s3_env):
    from src.lambda_handler import handler

    event = {
        "Records": [
            {"s3": {"bucket": {"name": settings.s3_bucket},
                    "object": {"key": f"{s3_env}/transactions.csv"}}}
        ]
    }
    resp = handler(event)
    assert resp["statusCode"] == 200

    curated = s3_utils.list_keys(settings.curated_prefix)
    assert any(k.endswith(".json") for k in curated)
