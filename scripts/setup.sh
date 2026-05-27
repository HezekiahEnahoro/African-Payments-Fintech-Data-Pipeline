#!/usr/bin/env bash
set -e

echo "========================================"
echo " African Payments Pipeline — Local Setup"
echo "========================================"

if [ ! -f .env ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
  echo "Edit .env with your AWS credentials before running S3 upload tasks."
fi

echo ""
echo "Starting Docker services..."
docker-compose up -d postgres-payments postgres-airflow

echo ""
echo "Waiting for PostgreSQL to be ready..."
sleep 8

echo ""
echo "Running DB migrations..."
docker-compose exec postgres-payments psql \
  -U payments -d payments_db \
  -f /docker-entrypoint-initdb.d/01_create_raw_tables.sql || true

echo ""
echo "Installing Python dependencies locally..."
pip install -r requirements.txt -q

echo ""
echo "Running a quick data generation test..."
python -c "
import sys
sys.path.insert(0, '.')
from data_generator.generate_merchants import generate_merchants
from data_generator.generate_transactions import generate_transaction, generate_customer
import random, uuid

merchants = generate_merchants(5)
customers = [generate_customer() for _ in range(20)]
merchant_ids = [m['id'] for m in merchants]
customer_ids = [c['id'] for c in customers]

txns = [generate_transaction(random.choice(merchant_ids), random.choice(customer_ids)) for _ in range(10)]
print(f'Generated {len(merchants)} merchants, {len(customers)} customers, {len(txns)} transactions')
print('Sample transaction:', {k: v for k, v in list(txns[0].items())[:6]})
print('')
print('Data generation works correctly.')
"

echo ""
echo "Starting Airflow..."
docker-compose up -d airflow-init
sleep 10
docker-compose up -d airflow-webserver airflow-scheduler

echo ""
echo "========================================"
echo " Setup complete!"
echo ""
echo " Airflow UI: http://localhost:8080"
echo " Username:   admin"
echo " Password:   admin"
echo ""
echo " PostgreSQL: localhost:5432"
echo " Database:   payments_db"
echo " User:       payments"
echo "========================================"
