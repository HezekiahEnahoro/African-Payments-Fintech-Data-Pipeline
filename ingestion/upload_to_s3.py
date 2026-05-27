from __future__ import annotations
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
import logging
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import AWS_CONFIG, S3_BUCKET

logger = logging.getLogger(__name__)


def get_s3_client():
    return boto3.client("s3", **AWS_CONFIG)


def upload_to_s3(data: list[dict], table_name: str, partition_date: datetime = None) -> str:
    """
    Convert records to Parquet and upload to S3 with date partitioning.
    Path pattern: s3://{bucket}/raw/{table}/year=YYYY/month=MM/day=DD/{table}.parquet
    """
    if not data:
        logger.warning("No data to upload for %s", table_name)
        return ""

    if not partition_date:
        partition_date = datetime.utcnow()

    df = pd.DataFrame(data)

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str)

    buffer = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buffer, compression="snappy")
    buffer.seek(0)

    s3_key = (
        f"raw/{table_name}/"
        f"year={partition_date.year}/"
        f"month={partition_date.month:02d}/"
        f"day={partition_date.day:02d}/"
        f"{table_name}.parquet"
    )

    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=buffer.getvalue(),
            ContentType="application/octet-stream",
        )
        logger.info("Uploaded %d rows to s3://%s/%s", len(data), S3_BUCKET, s3_key)
        return f"s3://{S3_BUCKET}/{s3_key}"
    except Exception as e:
        logger.error("S3 upload failed for %s: %s", table_name, e)
        raise


def upload_all_tables(
    merchants, customers, transactions,
    fx_rates, chargebacks, settlements,
    run_date: datetime = None
):
    run_date = run_date or datetime.utcnow()
    results = {}
    for name, data in [
        ("merchants",    merchants),
        ("customers",    customers),
        ("transactions", transactions),
        ("fx_rates",     fx_rates),
        ("chargebacks",  chargebacks),
        ("settlements",  settlements),
    ]:
        results[name] = upload_to_s3(data, name, run_date)
    return results
