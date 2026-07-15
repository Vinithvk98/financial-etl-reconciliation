"""AWS Lambda entry point.

Triggered by an S3 ``ObjectCreated`` event on the landing bucket. It pulls
the newly-landed source file down, runs the pipeline over it, and uploads
the run summary back to the curated prefix. In tests the same handler runs
against a moto-mocked S3, so the Lambda contract is exercised without AWS.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from . import s3_utils
from .pipeline import run


def handler(event: dict, context=None) -> dict:
    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]
        with tempfile.TemporaryDirectory() as tmp:
            src_dir = Path(tmp) / "source"
            src_dir.mkdir()
            # Expect the landing folder to hold both feeds.
            base = key.rsplit("/", 1)[0]
            s3_utils.download(f"{base}/transactions.csv",
                              src_dir / "transactions.csv", bucket)
            s3_utils.download(f"{base}/bank_statement.csv",
                              src_dir / "bank_statement.csv", bucket)
            summary = run(src_dir, reset=True)
            summary_path = Path(tmp) / "summary.json"
            summary_path.write_text(json.dumps(summary, indent=2))
            s3_utils.upload(summary_path,
                            f"{s3_utils.settings.curated_prefix}{summary['run_id']}.json",
                            bucket)
            results.append(summary)
    return {"statusCode": 200, "body": json.dumps(results)}
