from __future__ import annotations
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import BUSINESS_TYPES, NIGERIAN_BANKS

fake = Faker(['en_GB'])

NIGERIAN_CITIES = [
    "Lagos", "Abuja", "Kano", "Port Harcourt", "Ibadan",
    "Benin City", "Enugu", "Kaduna", "Owerri", "Warri"
]

def generate_merchant(created_at: datetime = None) -> dict:
    if not created_at:
        created_at = fake.date_time_between(start_date="-2y", end_date="now")

    business_name = fake.company()
    bank = random.choice(NIGERIAN_BANKS)
    account_number = "".join([str(random.randint(0, 9)) for _ in range(10)])

    return {
        "id": str(uuid.uuid4()),
        "name": business_name,
        "business_type": random.choice(BUSINESS_TYPES),
        "country": "NGN",
        "city": random.choice(NIGERIAN_CITIES),
        "settlement_bank": bank,
        "settlement_account": account_number,
        "tier": random.choices([1, 2, 3], weights=[60, 30, 10])[0],
        "is_active": random.choices([True, False], weights=[92, 8])[0],
        "created_at": created_at,
        "updated_at": created_at + timedelta(days=random.randint(0, 30)),
    }


def generate_merchants(n: int = 200) -> list[dict]:
    merchants = []
    for _ in range(n):
        merchants.append(generate_merchant())
    return merchants


def mutate_merchant(merchant: dict) -> dict:
    """Apply one realistic 'life event' to an existing merchant: a tier change
    or an active/inactive flip. Keeps the same id — this is what gives dim_merchants
    something real to detect a new version of."""
    mutated = dict(merchant)

    if random.random() < 0.5:
        current_tier = mutated["tier"]
        mutated["tier"] = random.choice([t for t in (1, 2, 3) if t != current_tier])
    else:
        mutated["is_active"] = not mutated["is_active"]

    mutated["updated_at"] = datetime.utcnow()
    return mutated


if __name__ == "__main__":
    merchants = generate_merchants(5)
    for m in merchants:
        print(m)
