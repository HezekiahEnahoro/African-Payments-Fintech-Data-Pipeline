CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.merchants (
    id              VARCHAR(36) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    business_type   VARCHAR(100),
    country         VARCHAR(3) DEFAULT 'NGN',
    city            VARCHAR(100),
    settlement_bank VARCHAR(100),
    settlement_account VARCHAR(20),
    tier            SMALLINT DEFAULT 1,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.customers (
    id              VARCHAR(36) PRIMARY KEY,
    email           VARCHAR(255),
    phone           VARCHAR(20),
    country         VARCHAR(3) DEFAULT 'NGN',
    created_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.transactions (
    id              VARCHAR(36) PRIMARY KEY,
    reference       VARCHAR(100) UNIQUE NOT NULL,
    merchant_id     VARCHAR(36) REFERENCES raw.merchants(id),
    customer_id     VARCHAR(36) REFERENCES raw.customers(id),
    amount          NUMERIC(15, 2) NOT NULL,
    currency        VARCHAR(3) NOT NULL,
    amount_ngn      NUMERIC(15, 2),
    status          VARCHAR(20) NOT NULL,
    channel         VARCHAR(50),
    description     TEXT,
    metadata        JSONB,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.fx_rates (
    id              SERIAL PRIMARY KEY,
    from_currency   VARCHAR(3) NOT NULL,
    to_currency     VARCHAR(3) NOT NULL,
    rate            NUMERIC(18, 6) NOT NULL,
    source          VARCHAR(50) DEFAULT 'CBN',
    captured_at     TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.chargebacks (
    id              VARCHAR(36) PRIMARY KEY,
    transaction_id  VARCHAR(36) REFERENCES raw.transactions(id),
    merchant_id     VARCHAR(36) REFERENCES raw.merchants(id),
    reason          VARCHAR(100),
    amount          NUMERIC(15, 2),
    currency        VARCHAR(3),
    status          VARCHAR(20) DEFAULT 'open',
    resolved_at     TIMESTAMP,
    created_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.settlements (
    id              VARCHAR(36) PRIMARY KEY,
    merchant_id     VARCHAR(36) REFERENCES raw.merchants(id),
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    gross_amount    NUMERIC(15, 2),
    fee_amount      NUMERIC(15, 2),
    net_amount      NUMERIC(15, 2),
    currency        VARCHAR(3) DEFAULT 'NGN',
    status          VARCHAR(20) DEFAULT 'pending',
    settled_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON raw.transactions(merchant_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created  ON raw.transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_status   ON raw.transactions(status);
CREATE INDEX IF NOT EXISTS idx_chargebacks_merchant  ON raw.chargebacks(merchant_id);
CREATE INDEX IF NOT EXISTS idx_settlements_merchant  ON raw.settlements(merchant_id);
CREATE INDEX IF NOT EXISTS idx_fx_rates_currencies   ON raw.fx_rates(from_currency, to_currency);
