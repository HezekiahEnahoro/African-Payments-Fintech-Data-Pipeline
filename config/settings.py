import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "database": os.getenv("POSTGRES_DB", "payments_db"),
    "user": os.getenv("POSTGRES_USER", "payments"),
    "password": os.getenv("POSTGRES_PASSWORD", "payments123"),
}

AWS_CONFIG = {
    "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
    "region_name": os.getenv("AWS_REGION", "us-east-1"),
}

S3_BUCKET = os.getenv("S3_BUCKET", "african-payments-pipeline")

CURRENCIES = ["NGN", "USD", "GBP", "EUR", "KES", "GHS", "ZAR"]
BASE_CURRENCY = "NGN"

PAYMENT_CHANNELS = ["card", "bank_transfer", "ussd", "mobile_money", "qr_code"]
PAYMENT_STATUSES = ["success", "failed", "pending", "reversed"]

BUSINESS_TYPES = [
    "ecommerce", "logistics", "fintech", "retail",
    "food_delivery", "healthcare", "education", "telecoms"
]

NIGERIAN_BANKS = [
    "Access Bank", "GTBank", "Zenith Bank", "First Bank",
    "UBA", "Kuda Bank", "Opay", "PalmPay", "Moniepoint"
]

CHARGEBACK_REASONS = [
    "unauthorized_transaction", "item_not_received",
    "duplicate_charge", "fraudulent_transaction", "service_not_rendered"
]
