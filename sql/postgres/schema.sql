-- PostgreSQL target warehouse schema.
-- Curated fact table plus quarantine and reconciliation-break tables that
-- give full auditability of what was loaded, what was rejected, and why.

CREATE SCHEMA IF NOT EXISTS curated;

CREATE TABLE IF NOT EXISTS curated.fact_transaction (
    transaction_id   VARCHAR(20)   PRIMARY KEY,
    account_id       VARCHAR(20)   NOT NULL,
    posted_at        TIMESTAMP     NOT NULL,
    merchant_name    VARCHAR(100),
    channel          VARCHAR(20),
    currency_code    CHAR(3)       NOT NULL,
    amount           NUMERIC(18,2) NOT NULL,
    amount_minor     BIGINT        NOT NULL,
    status           VARCHAR(20)   NOT NULL,
    loaded_at        TIMESTAMP     DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_fact_txn_account ON curated.fact_transaction (account_id);
CREATE INDEX IF NOT EXISTS ix_fact_txn_posted  ON curated.fact_transaction (posted_at);

CREATE TABLE IF NOT EXISTS curated.dq_quarantine (
    transaction_id   VARCHAR(20),
    account_id       VARCHAR(20),
    posted_at        TIMESTAMP,
    currency_code    VARCHAR(10),
    amount           VARCHAR(50),
    dq_reason        VARCHAR(60)   NOT NULL,
    quarantined_at   TIMESTAMP     DEFAULT now()
);

CREATE TABLE IF NOT EXISTS curated.recon_breaks (
    transaction_id   VARCHAR(20),
    amount_ledger    NUMERIC(18,2),
    amount_bank      NUMERIC(18,2),
    delta            NUMERIC(18,2),
    break_type       VARCHAR(20)   NOT NULL,
    detected_at      TIMESTAMP     DEFAULT now()
);
