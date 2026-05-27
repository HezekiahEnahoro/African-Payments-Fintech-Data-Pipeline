# African Payments & Fintech Data Pipeline

A production-grade batch data pipeline simulating a Paystack/Flutterwave-style payment processing platform. Built to demonstrate end-to-end data engineering across ingestion, transformation, warehousing, and cloud storage.

---

## Architecture

```
Data Sources (Python generators)
  └── Transactions · Merchants · FX Rates · Chargebacks · Settlements
        │
        ▼
Apache Airflow  (daily orchestration @ 01:00 UTC)
        │
   ┌────┴────┐
   ▼         ▼
PostgreSQL  AWS S3
(raw schema) (Parquet, date-partitioned)
   │
   ▼
dbt transformations
  staging → intermediate → marts
   │
   ▼
PostgreSQL analytics schema
  fct_transactions · dim_merchants (SCD Type 2) · fct_settlements
```

---

## Stack

| Layer | Technology |
|---|---|
| Orchestration | Apache Airflow 2.8 |
| Ingestion | Python, psycopg2 |
| Storage (lake) | AWS S3, Parquet, Snappy |
| Transformation | dbt-postgres 1.7 |
| Warehouse | PostgreSQL 15 |
| Containerisation | Docker, docker-compose |
| Data generation | Python, Faker |

---

## Domain Model

Simulates the core data flows of an African fintech payments processor:

- **Transactions** — payments across card, bank transfer, USSD, mobile money, QR code in NGN/USD/GBP/KES/GHS
- **Merchants** — businesses onboarded by tier (1–3), with Nigerian bank settlement accounts
- **FX Rates** — daily CBN-style exchange rates with realistic drift
- **Chargebacks** — ~2% of successful transactions with open/won/lost resolution
- **Settlements** — weekly merchant settlement batches with fee deductions

---

## Key Engineering Concepts

### SCD Type 2 on dim_merchants
When a merchant changes tier or business status, a new history record is created. Each record carries `effective_from`, `effective_to`, and `is_current` flags — the standard pattern for slowly changing dimensions.

### Date-partitioned S3 storage
All raw data is written as Parquet with Snappy compression under the path:
```
s3://bucket/raw/{table}/year=YYYY/month=MM/day=DD/
```
This enables partition pruning when querying via Athena or Spark.

### dbt lineage
Full DAG from `source(raw)` → `stg_*` → `fct_*` / `dim_*`. All sources have schema tests for uniqueness, nullability, and accepted values.

---

## Setup

```bash
git clone https://github.com/yourname/african-payments-pipeline
cd african-payments-pipeline

cp .env.example .env
# Add your AWS credentials to .env

chmod +x scripts/setup.sh
./scripts/setup.sh
```

Airflow UI available at `http://localhost:8080` (admin / admin).

To trigger the pipeline manually:
```bash
docker-compose exec airflow-scheduler \
  airflow dags trigger african_payments_pipeline
```

To run dbt transformations locally:
```bash
cd dbt_project
dbt run --profiles-dir . --target dev
dbt test --profiles-dir . --target dev
```

---

## Analytics Output

Key metrics available in the `analytics` schema after a pipeline run:

| Metric | Query |
|---|---|
| Daily transaction volume (NGN) | `SELECT transaction_date, SUM(amount_ngn) FROM analytics.fct_transactions WHERE is_successful=1 GROUP BY 1` |
| Chargeback rate by merchant tier | Join `fct_transactions` + `dim_merchants` + raw chargebacks |
| Channel success rates | `SELECT payment_channel, AVG(is_successful) FROM analytics.fct_transactions GROUP BY 1` |
| Weekly settlement lag | `SELECT merchant_id, AVG(settled_at - period_end) FROM raw.settlements GROUP BY 1` |
| FX exposure by currency | `SELECT currency, SUM(amount) FROM analytics.fct_transactions WHERE is_successful=1 GROUP BY 1` |

---

## Lessons Learned

- **SCD Type 2** requires careful handling of row hashing — using `md5()` on concatenated fields is simple but effective for detecting attribute changes
- **Parquet + Snappy** gives ~60–70% compression vs raw CSV with much faster reads for columnar analytics
- **Airflow XComs** are useful for passing row counts between tasks but not for large data payloads — use a temp file or S3 for that
- **dbt `accepted_values` tests** on `status` fields catch upstream data quality issues early in the pipeline

---

## Project Status

- [x] Data generation (merchants, transactions, FX, chargebacks, settlements)
- [x] PostgreSQL raw schema ingestion
- [x] AWS S3 Parquet upload with date partitioning
- [x] Airflow DAG with retry logic
- [x] dbt staging models + source tests
- [x] dbt mart models (fct_transactions, dim_merchants SCD Type 2)
- [ ] Grafana dashboard
- [ ] Great Expectations data quality suite (added in Project 3)
- [ ] MLOps layer — fraud scoring model (Phase 2)
