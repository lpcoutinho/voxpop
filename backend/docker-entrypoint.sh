#!/bin/sh
set -e

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --settings=config.settings.production

# If no command provided, use default gunicorn
if [ $# -eq 0 ]; then
    set -- gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 4 \
      --timeout 120 \
      --worker-class sync \
      --max-requests 1000 \
      --max-requests-jitter 50 \
      --access-logfile - \
      --error-logfile - \
      --log-level info
fi

echo "=== Starting Gunicorn ==="
exec "$@"
