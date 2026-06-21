#!/bin/sh

echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database ready!"

python manage.py migrate --noinput
python manage.py collectstatic --noinput


# gunicorn servicesapp.wsgi:application --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 4 --timeout 120
python manage.py runserver 0.0.0.0:8000
