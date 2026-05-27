from __future__ import annotations
import uuid
import random
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import CURRENCIES, CHARGEBACK_REASONS


def generate_fx_rates(days_back: int = 365) -> list[dict]:
    """Generate daily FX rates vs NGN for all currency pairs."""
    rates = []
    base_rates = {
        "USD": 1580.0, "GBP": 2010.0, "EUR": 1720.0,
        "KES": 12.2,   "GHS": 107.0,  "ZAR": 86.0,
    }
    now = datetime.utcnow()

    for day_offset in range(days_back, 0, -1):
        captured_at = now - timedelta(days=day_offset)
        for currency, base_rate in base_rates.items():
            drift = random.uniform(-0.015, 0.015)
            rate = round(base_rate * (1 + drift), 4)
            base_rates[currency] = rate
            rates.append({
                "from_currency": "NGN",
                "to_currency": currency,
                "rate": round(1 / rate, 8),
                "source": "CBN",
                "captured_at": captured_at,
            })
            rates.append({
                "from_currency": currency,
                "to_currency": "NGN",
                "rate": rate,
                "source": "CBN",
                "captured_at": captured_at,
            })
    return rates


def generate_chargebacks(transactions: list[dict]) -> list[dict]:
    """Generate chargebacks for ~2% of successful transactions."""
    chargebacks = []
    eligible = [t for t in transactions if t["status"] == "success"]
    sampled = random.sample(eligible, max(1, int(len(eligible) * 0.02)))

    for txn in sampled:
        created_at = txn["created_at"] + timedelta(days=random.randint(1, 14))
        status = random.choices(
            ["open", "won", "lost"],
            weights=[30, 45, 25]
        )[0]
        chargebacks.append({
            "id": str(uuid.uuid4()),
            "transaction_id": txn["id"],
            "merchant_id": txn["merchant_id"],
            "reason": random.choice(CHARGEBACK_REASONS),
            "amount": txn["amount"],
            "currency": txn["currency"],
            "status": status,
            "resolved_at": created_at + timedelta(days=random.randint(3, 21)) if status != "open" else None,
            "created_at": created_at,
        })
    return chargebacks


def generate_settlements(merchant_ids: list, transactions: list[dict]) -> list[dict]:
    """Generate weekly settlement batches per merchant."""
    settlements = []
    success_txns = [t for t in transactions if t["status"] == "success"]

    from collections import defaultdict
    merchant_txns = defaultdict(list)
    for t in success_txns:
        merchant_txns[t["merchant_id"]].append(t)

    for merchant_id in merchant_ids:
        txns = merchant_txns.get(merchant_id, [])
        if not txns:
            continue

        min_date = min(t["created_at"].date() for t in txns)
        max_date = max(t["created_at"].date() for t in txns)
        current = min_date

        while current <= max_date:
            week_end = current + timedelta(days=6)
            week_txns = [
                t for t in txns
                if current <= t["created_at"].date() <= week_end
            ]
            if week_txns:
                gross = sum(t["amount_ngn"] for t in week_txns)
                fee_rate = random.uniform(0.014, 0.016)
                fee = round(gross * fee_rate, 2)
                net = round(gross - fee, 2)
                status = "settled" if week_end < datetime.utcnow().date() else "pending"
                settlements.append({
                    "id": str(uuid.uuid4()),
                    "merchant_id": merchant_id,
                    "period_start": current,
                    "period_end": week_end,
                    "gross_amount": round(gross, 2),
                    "fee_amount": fee,
                    "net_amount": net,
                    "currency": "NGN",
                    "status": status,
                    "settled_at": datetime.combine(week_end + timedelta(days=2), datetime.min.time()) if status == "settled" else None,
                    "created_at": datetime.combine(week_end + timedelta(days=1), datetime.min.time()),
                })
            current += timedelta(days=7)

    return settlements
