# Architecture & Design Notes

## Design goals

1. **Scale to 10M+ rows on modest hardware.** The extract and load stages
   stream the source in fixed-size chunks, so peak memory is bounded by the
   chunk size, not the file size. This is the single most important property
   for processing daily feeds cost-effectively.
2. **Never silently lose data.** The data-quality gate quarantines bad rows
   with a reason code instead of dropping them. Nothing disappears without a
   trace, which is a hard requirement in a regulated context.
3. **Prove correctness.** Reconciliation against an independent bank feed
   turns "the ETL ran" into "the warehouse provably agrees with the source of
   truth, and here are the exact breaks."
4. **Run anywhere unchanged.** Environment-driven config and a SQLAlchemy
   abstraction mean the same code targets SQLite (demo), PostgreSQL or MSSQL
   (prod) and runs locally, in CI, or in Lambda.

## Data flow

Source files land in an S3 bucket. An `ObjectCreated` event invokes the
Lambda handler, which pulls the files, runs the pipeline, and writes a run
summary back to a curated prefix. The pipeline itself is a linear chain:

```
extract → transform → data-quality gate → load(clean|quarantine) → reconcile → load(breaks)
```

Each stage emits an audit event, so a run can be reconstructed end to end
from `data/audit/<run_id>.jsonl`.

## Source-to-target mapping

The mapping lives in `mapping/source_to_target.yaml` rather than in code. It
drives both the transform (renames, kept columns) and the data-quality checks
(not-null, domain, key). Keeping schema and quality in one declarative file
prevents the two drifting apart, and means a schema change is a data edit, not
a code change.

## Data-quality rules

| Rule | Trigger | Reason code |
|---|---|---|
| Not null | key/foreign-key column missing | `null_<col>` |
| Numeric | amount not parseable | `amount_not_numeric` |
| Timestamp | `posted_at` not parseable | `bad_timestamp` |
| Domain | value outside allowed set | `invalid_<col>` |
| Uniqueness | duplicate business key | `duplicate_<col>` |

The first failing rule wins, so each quarantined row carries exactly one
deterministic reason — important for building trustworthy exception reports.

## Reconciliation model

Two feeds are joined on `transaction_id` with an outer join and an indicator:

* `both` + `|Δ| ≤ tolerance` → **matched**
* `both` + `|Δ| > tolerance` → **amount_break**
* `left_only` → **missing_bank** (in ledger, not in bank)
* `right_only` → **missing_ledger** (in bank, not in ledger)

The tolerance defaults to £0.01 to absorb rounding while still catching real
breaks.

## Deployment notes

* **Warehouse:** apply `sql/postgres/schema.sql` or `sql/mssql/schema.sql`,
  then set `ETL_TARGET_DSN`.
* **Lambda:** package `src/` with `requirements.txt`, set the S3 trigger on the
  landing bucket, and grant `s3:GetObject`/`s3:PutObject` on the relevant
  prefixes.
* **Scale-out:** for feeds beyond a single Lambda's limits, the same stage
  functions drop into a Glue/Spark job unchanged because they operate on
  DataFrames, not on a specific runtime.
