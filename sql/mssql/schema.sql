-- MSSQL (T-SQL) target warehouse schema.
-- Mirrors the PostgreSQL model so the pipeline can target either engine
-- unchanged; only the DSN differs at deploy time.

IF SCHEMA_ID(N'curated') IS NULL EXEC(N'CREATE SCHEMA curated');
GO

IF OBJECT_ID(N'curated.fact_transaction', N'U') IS NULL
CREATE TABLE curated.fact_transaction (
    transaction_id   VARCHAR(20)    NOT NULL PRIMARY KEY,
    account_id       VARCHAR(20)    NOT NULL,
    posted_at        DATETIME2      NOT NULL,
    merchant_name    VARCHAR(100)   NULL,
    channel          VARCHAR(20)    NULL,
    currency_code    CHAR(3)        NOT NULL,
    amount           DECIMAL(18,2)  NOT NULL,
    amount_minor     BIGINT         NOT NULL,
    status           VARCHAR(20)    NOT NULL,
    loaded_at        DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'curated.dq_quarantine', N'U') IS NULL
CREATE TABLE curated.dq_quarantine (
    transaction_id   VARCHAR(20)    NULL,
    account_id       VARCHAR(20)    NULL,
    posted_at        DATETIME2      NULL,
    currency_code    VARCHAR(10)    NULL,
    amount           VARCHAR(50)    NULL,
    dq_reason        VARCHAR(60)    NOT NULL,
    quarantined_at   DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

IF OBJECT_ID(N'curated.recon_breaks', N'U') IS NULL
CREATE TABLE curated.recon_breaks (
    transaction_id   VARCHAR(20)    NULL,
    amount_ledger    DECIMAL(18,2)  NULL,
    amount_bank      DECIMAL(18,2)  NULL,
    delta            DECIMAL(18,2)  NULL,
    break_type       VARCHAR(20)    NOT NULL,
    detected_at      DATETIME2      NOT NULL DEFAULT SYSUTCDATETIME()
);
GO
