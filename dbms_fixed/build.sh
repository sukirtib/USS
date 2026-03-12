#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if needed
python manage.py create_admin || true

# Fix admin permissions (ensures Django admin access)
python manage.py fix_admin || true

# Seed demo data (use --force to reseed)
python manage.py seed_data --force || true
