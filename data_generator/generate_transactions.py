from __future__ import annotations
import uuid
import random
import json
from datetime import datetime, timedelta
from faker import Faker

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import (
    CURRENCIES, PAYMENT_CHANNELS, PAYMENT_STATUSES
)

fake = Faker(['en_GB'])

FX_RATES_NGN = {
    "NGN": 1.0,
    "USD": 1580.0,
    "GBP": 2010.0,
    "EUR": 1720.0,
    "KES": 12.2,
    "GHS": 107.0,
    "ZAR": 86.0,
}

AMOUNT_RANGES_NGN = {
    "card":           (500, 500_000),
    "bank_transfer":  (5_000, 10_000_000),
    "ussd":           (200, 50_000),
    "mobile_money":   (100, 100_000),
    "qr_code":        (500, 200_000),
}

STATUS_WEIGHTS = {
    "success": 78,
    "failed": 12,
    "pending": 6,
    "reversed": 4,
}


def _generate_reference() -> str:
    prefix = random.choice(["PAY", "TRF", "CHG", "REF"])
    return f"{prefix}_{uuid.uuid4().hex[:16].upper()}"


def generate_customer(created_at: datetime = None) -> dict:
    if not created_at:
        created_at = fake.date_time_between(start_date="-2y", end_date="now")
    return {
        "id": str(uuid.uuid4()),
        "email": fake.email(),
        "phone": f"+234{random.randint(700_000_0000, 909_999_9999)}",
        "country": "NGN",
        "created_at": created_at,
    }


def generate_transaction(merchant_id: str, customer_id: str, created_at: datetime = None) -> dict:
    if not created_at:
        created_at = fake.date_time_between(start_date="-1y", end_date="now")

    channel = random.choice(PAYMENT_CHANNELS)
    currency = random.choices(
        ["NGN", "USD", "GBP", "KES", "GHS"],
        weights=[70, 15, 8, 4, 3]
    )[0]

    min_ngn, max_ngn = AMOUNT_RANGES_NGN[channel]
    amount_ngn = round(random.uniform(min_ngn, max_ngn), 2)
    fx_rate = FX_RATES_NGN.get(currency, 1.0)
    amount = round(amount_ngn / fx_rate, 2) if currency != "NGN" else amount_ngn

    status = random.choices(
        list(STATUS_WEIGHTS.keys()),
        weights=list(STATUS_WEIGHTS.values())
    )[0]

    metadata = {
        "ip_country": random.choice(["NG", "US", "GB", "GH", "KE"]),
        "device": random.choice(["mobile", "desktop", "tablet"]),
        "attempt": random.choices([1, 2, 3], weights=[85, 12, 3])[0],
    }

    return {
        "id": str(uuid.uuid4()),
        "reference": _generate_reference(),
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "amount": amount,
        "currency": currency,
        "amount_ngn": amount_ngn,
        "status": status,
        "channel": channel,
        "description": f"Payment via {channel}",
        "metadata": json.dumps(metadata),
        "created_at": created_at,
        "updated_at": created_at + timedelta(seconds=random.randint(1, 120)),
    }


def generate_transactions(merchant_ids: list, customer_ids: list, n: int = 5000) -> list[dict]:
    transactions = []
    for _ in range(n):
        transactions.append(generate_transaction(
            merchant_id=random.choice(merchant_ids),
            customer_id=random.choice(customer_ids),
        ))
    return transactions


if __name__ == "__main__":
    sample_merchants = [str(uuid.uuid4()) for _ in range(10)]
    sample_customers = [str(uuid.uuid4()) for _ in range(50)]
    txns = generate_transactions(sample_merchants, sample_customers, n=5)
    for t in txns:
        print(t)
