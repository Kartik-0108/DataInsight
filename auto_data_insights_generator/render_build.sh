#!/usr/bin/env bash
# Render build script — runs on every deploy
set -o errexit

echo ">>> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ">>> Running Django migrations..."
cd backend
python manage.py migrate --noinput

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Creating superuser if not exists..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'changeme123')
    print('Superuser created: admin / changeme123')
else:
    print('Superuser already exists, skipping.')
"

echo ">>> Build complete!"
