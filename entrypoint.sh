#!/bin/sh

echo "Waiting for the database to become available..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database ready!"

# Apply migrations
echo "Running migrations..."
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files (optional)
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# # Remove old socket if exists
# rm -f /run/gunicorn/gunicorn.sock

# Create socket directory (if it does not exist)
mkdir -p /run/gunicorn
chown -R root:www-data /run/gunicorn
chmod -R 775 /run/gunicorn

# Start Gunicorn on port 8000
echo "Starting Gunicorn..."
exec gunicorn --preload vesalus.wsgi:application \
    --workers 5 \
    --bind 0.0.0.0:8000 \
    --timeout 0 \
    --access-logfile /var/log/gunicorn_access.log \
    --error-logfile /var/log/gunicorn_error.log \
    --log-level debug
