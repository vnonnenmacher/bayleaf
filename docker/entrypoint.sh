#!/usr/bin/env bash
set -e

# Wait for DB if needed (optional, uncomment if you want)
# python manage.py check --database default || true

# Always run migrations (safe to re-run)
python manage.py migrate --noinput

# Only collectstatic in prod (keeps dev fast)
if [ "$RUN_MODE" != "dev" ]; then
  python manage.py collectstatic --noinput
fi

if [ "$RUN_MODE" = "dev" ]; then
  echo "➡️  Starting Django runserver (dev mode)…"
  exec python manage.py runserver 0.0.0.0:8000
else
  echo "➡️  Starting uWSGI (prod mode)…"
  exec uwsgi --ini /usr/src/app/uwsgi.ini
fi
