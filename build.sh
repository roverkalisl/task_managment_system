#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py migrate --noinput
python manage.py collectstatic --noinput

mkdir -p media staticfiles

# Optional: load demo data (set SEED_DEMO_DATA=true on Render for first deploy only)
if [ "${SEED_DEMO_DATA}" = "true" ]; then
  python manage.py seed_test_data
fi
