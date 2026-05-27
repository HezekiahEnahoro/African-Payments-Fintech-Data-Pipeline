from __future__ import annotations
import psycopg2
import psycopg2.extras
import logging
from typing import Any

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import DB_CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def upsert_merchants(merchants: list[dict]) -> int:
    sql = """
        INSERT INTO raw.merchants
            (id, name, business_type, country, city, settlement_bank,
             settlement_account, tier, is_active, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            name             = EXCLUDED.name,
            business_type    = EXCLUDED.business_type,
            tier             = EXCLUDED.tier,
            is_active        = EXCLUDED.is_active,
            updated_at       = EXCLUDED.updated_at
    """
    rows = [(
        m["id"], m["name"], m["business_type"], m["country"],
        m["city"], m["settlement_bank"], m["settlement_account"],
        m["tier"], m["is_active"], m["created_at"], m["updated_at"]
    ) for m in merchants]
    return _bulk_execute(sql, rows, "merchants")


def upsert_customers(customers: list[dict]) -> int:
    sql = """
        INSERT INTO raw.customers (id, email, phone, country, created_at)
        VALUES %s
        ON CONFLICT (id) DO NOTHING
    """
    rows = [(c["id"], c["email"], c["phone"], c["country"], c["created_at"]) for c in customers]
    return _bulk_execute(sql, rows, "customers")


def upsert_transactions(transactions: list[dict]) -> int:
    sql = """
        INSERT INTO raw.transactions
            (id, reference, merchant_id, customer_id, amount, currency,
             amount_ngn, status, channel, description, metadata, created_at, updated_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status     = EXCLUDED.status,
            updated_at = EXCLUDED.updated_at
    """
    rows = [(
        t["id"], t["reference"], t["merchant_id"], t["customer_id"],
        t["amount"], t["currency"], t["amount_ngn"], t["status"],
        t["channel"], t["description"], t["metadata"],
        t["created_at"], t["updated_at"]
    ) for t in transactions]
    return _bulk_execute(sql, rows, "transactions")


def insert_fx_rates(rates: list[dict]) -> int:
    sql = """
        INSERT INTO raw.fx_rates
            (from_currency, to_currency, rate, source, captured_at)
        VALUES %s
        ON CONFLICT DO NOTHING
    """
    rows = [(r["from_currency"], r["to_currency"], r["rate"], r["source"], r["captured_at"]) for r in rates]
    return _bulk_execute(sql, rows, "fx_rates")


def upsert_chargebacks(chargebacks: list[dict]) -> int:
    sql = """
        INSERT INTO raw.chargebacks
            (id, transaction_id, merchant_id, reason, amount, currency,
             status, resolved_at, created_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status      = EXCLUDED.status,
            resolved_at = EXCLUDED.resolved_at
    """
    rows = [(
        c["id"], c["transaction_id"], c["merchant_id"], c["reason"],
        c["amount"], c["currency"], c["status"],
        c["resolved_at"], c["created_at"]
    ) for c in chargebacks]
    return _bulk_execute(sql, rows, "chargebacks")


def upsert_settlements(settlements: list[dict]) -> int:
    sql = """
        INSERT INTO raw.settlements
            (id, merchant_id, period_start, period_end, gross_amount,
             fee_amount, net_amount, currency, status, settled_at, created_at)
        VALUES %s
        ON CONFLICT (id) DO UPDATE SET
            status     = EXCLUDED.status,
            settled_at = EXCLUDED.settled_at
    """
    rows = [(
        s["id"], s["merchant_id"], s["period_start"], s["period_end"],
        s["gross_amount"], s["fee_amount"], s["net_amount"],
        s["currency"], s["status"], s["settled_at"], s["created_at"]
    ) for s in settlements]
    return _bulk_execute(sql, rows, "settlements")


def _bulk_execute(sql: str, rows: list[tuple], table_name: str) -> int:
    if not rows:
        logger.warning("No rows to insert for %s", table_name)
        return 0
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                psycopg2.extras.execute_values(cur, sql, rows, page_size=500)
            conn.commit()
        logger.info("Upserted %d rows into raw.%s", len(rows), table_name)
        return len(rows)
    except Exception as e:
        logger.error("Failed to upsert %s: %s", table_name, e)
        raise
