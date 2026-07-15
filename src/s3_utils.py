"""Thin S3 helpers.

The production pipeline lands raw files in S3 and writes curated Parquet
back to a separate prefix. In tests these calls run against a moto-mocked
S3 endpoint, so no AWS account or network access is required.
"""
from __future__ import annotations

from pathlib import Path

import boto3

from .config import settings


def client():
    return boto3.client("s3", region_name=settings.s3_region)


def ensure_bucket(bucket: str | None = None) -> str:
    bucket = bucket or settings.s3_bucket
    s3 = client()
    existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
    if bucket not in existing:
        kwargs = {"Bucket": bucket}
        if settings.s3_region != "us-east-1":
            kwargs["CreateBucketConfiguration"] = {"LocationConstraint": settings.s3_region}
        s3.create_bucket(**kwargs)
    return bucket


def upload(local_path: str | Path, key: str, bucket: str | None = None) -> str:
    bucket = ensure_bucket(bucket)
    client().upload_file(str(local_path), bucket, key)
    return f"s3://{bucket}/{key}"


def download(key: str, local_path: str | Path, bucket: str | None = None) -> Path:
    bucket = bucket or settings.s3_bucket
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    client().download_file(bucket, key, str(local_path))
    return local_path


def list_keys(prefix: str, bucket: str | None = None) -> list[str]:
    bucket = bucket or settings.s3_bucket
    resp = client().list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [o["Key"] for o in resp.get("Contents", [])]
