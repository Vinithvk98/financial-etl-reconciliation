"""Audit-trail helpers.

Every pipeline run and every data-quality decision is recorded so the
process is defensible in a regulated Financial Services context. The audit
log is append-only and keyed by a run id, giving full lineage from a source
file to the curated warehouse rows it produced.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import ROOT

AUDIT_DIR = ROOT / "data" / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def new_run_id() -> str:
    return f"run-{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:8]}"


@dataclass
class AuditEvent:
    run_id: str
    stage: str
    message: str
    metrics: dict = field(default_factory=dict)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AuditTrail:
    """Append-only JSONL audit log for a single run."""

    def __init__(self, run_id: str | None = None):
        self.run_id = run_id or new_run_id()
        self.path = AUDIT_DIR / f"{self.run_id}.jsonl"
        self.events: list[AuditEvent] = []

    def record(self, stage: str, message: str, **metrics) -> AuditEvent:
        event = AuditEvent(self.run_id, stage, message, metrics)
        self.events.append(event)
        with self.path.open("a") as fh:
            fh.write(json.dumps(asdict(event)) + "\n")
        return event

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "events": len(self.events),
            "stages": [e.stage for e in self.events],
        }
