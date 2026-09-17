from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

import sys
sys.path.insert(0, "/opt/airflow")

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    dag_id="african_payments_pipeline",
    default_args=default_args,
    description="Daily batch pipeline for African payments data",
    schedule_interval="0 1 * * *",
    start_date=days_ago(1),
    catchup=False,
    tags=["payments", "fintech", "nigeria", "batch"],
)


def run_data_generation(**context):
    from data_generator.generate_merchants import generate_merchants, mutate_merchant
    from data_generator.generate_transactions import generate_transaction, generate_customer
    from data_generator.generate_supporting import (
        generate_fx_rates, generate_chargebacks, generate_settlements
    )
    from ingestion.load_to_postgres import (
        get_existing_merchant_ids, get_existing_merchants, get_existing_customer_ids
    )
    import random

    print("Checking for an existing merchant/customer pool...")
    existing_merchant_ids = get_existing_merchant_ids()
    existing_customer_ids = get_existing_customer_ids()

    if not existing_merchant_ids:
        print("No existing merchants found — cold start, generating an initial pool.")
        new_merchants = generate_merchants(200)
        mutated_merchants = []
    else:
        print(f"Found {len(existing_merchant_ids)} existing merchants — reusing the pool.")
        new_merchants = generate_merchants(random.randint(5, 10))

        existing_merchants = get_existing_merchants()
        sample_size = max(1, int(len(existing_merchants) * 0.05))
        to_mutate = random.sample(existing_merchants, sample_size)
        mutated_merchants = [mutate_merchant(m) for m in to_mutate]

    new_customers = [
        generate_customer() for _ in range(1000 if not existing_customer_ids else 50)
    ]

    merchants_to_upsert = new_merchants + mutated_merchants
    all_merchant_ids = existing_merchant_ids + [m["id"] for m in new_merchants]
    all_customer_ids = existing_customer_ids + [c["id"] for c in new_customers]

    print("Generating transactions...")
    transactions = [
        generate_transaction(
            merchant_id=random.choice(all_merchant_ids),
            customer_id=random.choice(all_customer_ids)
        )
        for _ in range(5000)
    ]

    print("Generating FX rates, chargebacks, settlements...")
    fx_rates    = generate_fx_rates(days_back=7)
    chargebacks = generate_chargebacks(transactions)
    settlements = generate_settlements(all_merchant_ids, transactions)

    context["ti"].xcom_push(key="merchant_count",     value=len(merchants_to_upsert))
    context["ti"].xcom_push(key="transaction_count",  value=len(transactions))
    context["ti"].xcom_push(key="chargeback_count",   value=len(chargebacks))
    context["ti"].xcom_push(key="settlement_count",   value=len(settlements))

    import json, re
    run_data = {
        "merchants": merchants_to_upsert,
        "customers": new_customers,
        "transactions": transactions,
        "fx_rates": fx_rates,
        "chargebacks": chargebacks,
        "settlements": settlements,
    }
    safe_run_id = re.sub(r"[^a-zA-Z0-9_-]", "_", context["run_id"])
    tmp_path = f"/tmp/payments_run_data_{safe_run_id}.json"
    with open(tmp_path, "w") as f:
        json.dump(run_data, f, default=str)
    context["ti"].xcom_push(key="tmp_path", value=tmp_path)

    print(
        f"Data generation complete. Merchants written: {len(merchants_to_upsert)} "
        f"({len(new_merchants)} new, {len(mutated_merchants)} mutated). "
        f"Transactions: {len(transactions)}"
    )


def run_postgres_ingestion(**context):
    import json
    from ingestion.load_to_postgres import (
        upsert_merchants, upsert_customers, upsert_transactions,
        insert_fx_rates, upsert_chargebacks, upsert_settlements
    )

    tmp_path = context["ti"].xcom_pull(task_ids="generate_data", key="tmp_path")
    with open(tmp_path) as f:
        data = json.load(f)

    from datetime import datetime
    def _parse_dates(records, date_fields):
        for r in records:
            for field in date_fields:
                if r.get(field):
                    r[field] = datetime.fromisoformat(r[field])
        return records

    merchants    = _parse_dates(data["merchants"],    ["created_at", "updated_at"])
    customers    = _parse_dates(data["customers"],    ["created_at"])
    transactions = _parse_dates(data["transactions"], ["created_at", "updated_at"])
    fx_rates     = _parse_dates(data["fx_rates"],     ["captured_at"])
    chargebacks  = _parse_dates(data["chargebacks"],  ["created_at", "resolved_at"])
    settlements  = _parse_dates(data["settlements"],  ["created_at", "settled_at", "period_start", "period_end"])

    upsert_merchants(merchants)
    upsert_customers(customers)
    upsert_transactions(transactions)
    insert_fx_rates(fx_rates)
    upsert_chargebacks(chargebacks)
    upsert_settlements(settlements)

    print("PostgreSQL ingestion complete.")


def run_s3_upload(**context):
    import json
    import os
    from airflow.exceptions import AirflowSkipException
    from ingestion.upload_to_s3 import upload_all_tables
    from datetime import datetime, timezone

    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    s3_bucket = os.getenv("S3_BUCKET", "")
    if not aws_key or not s3_bucket:
        raise AirflowSkipException("AWS credentials or S3_BUCKET not configured — skipping S3 upload.")

    tmp_path = context["ti"].xcom_pull(task_ids="generate_data", key="tmp_path")
    with open(tmp_path) as f:
        data = json.load(f)

    try:
        results = upload_all_tables(
            merchants=data["merchants"],
            customers=data["customers"],
            transactions=data["transactions"],
            fx_rates=data["fx_rates"],
            chargebacks=data["chargebacks"],
            settlements=data["settlements"],
            run_date=datetime.now(timezone.utc),
        )
        print("S3 upload complete:", results)
    except Exception as e:
        error_msg = str(e)
        if "NoSuchBucket" in error_msg or "NoCredentialProviders" in error_msg or "InvalidClientTokenId" in error_msg or "InvalidAccessKeyId" in error_msg:
            raise AirflowSkipException(f"S3 not available ({error_msg}) — skipping S3 upload.")
        raise


generate_task = PythonOperator(
    task_id="generate_data",
    python_callable=run_data_generation,
    dag=dag,
)

ingest_postgres_task = PythonOperator(
    task_id="ingest_to_postgres",
    python_callable=run_postgres_ingestion,
    dag=dag,
)

upload_s3_task = PythonOperator(
    task_id="upload_to_s3",
    python_callable=run_s3_upload,
    dag=dag,
)

run_dbt_snapshot_task = BashOperator(
    task_id="run_dbt_snapshot",
    bash_command=(
        "cd /opt/airflow/dbt_project && "
        "dbt deps --profiles-dir /opt/airflow/dbt_project --target prod && "
        "dbt snapshot --profiles-dir /opt/airflow/dbt_project --target prod"
    ),
    dag=dag,
)

run_dbt_task = BashOperator(
    task_id="run_dbt_transformations",
    bash_command=(
        "cd /opt/airflow/dbt_project && "
        "dbt deps --profiles-dir /opt/airflow/dbt_project --target prod && "
        "dbt run --profiles-dir /opt/airflow/dbt_project --target prod"
    ),
    dag=dag,
)

run_dbt_tests_task = BashOperator(
    task_id="run_dbt_tests",
    bash_command=(
        "cd /opt/airflow/dbt_project && "
        "dbt test --profiles-dir /opt/airflow/dbt_project --target prod"
    ),
    dag=dag,
)

generate_task >> [ingest_postgres_task, upload_s3_task]
ingest_postgres_task >> run_dbt_snapshot_task >> run_dbt_task >> run_dbt_tests_task
