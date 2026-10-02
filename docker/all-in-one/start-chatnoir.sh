#!/usr/bin/env bash
set -e

export CHATNOIR_APP="${CHATNOIR_APP:-chatnoir}"

# Wait for Elasticsearch to become available before running migrations/starting uWSGI.
echo "Waiting for Elasticsearch to become available..."
for i in $(seq 1 60); do
    if curl -s -o /dev/null "http://127.0.0.1:9200"; then
        break
    fi
    sleep 2
done

if [ "$CHATNOIR_APP" != "web_cache" ]; then
    chatnoir-manage migrate --no-input
fi

if [ "$CHATNOIR_APP" = "chatnoir_admin" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    chatnoir-manage createsuperuser --no-input 2> /dev/null || true
    unset DJANGO_SUPERUSER_USERNAME
    unset DJANGO_SUPERUSER_PASSWORD
fi

exec uwsgi --ini /opt/chatnoir-web/chatnoir/wsgi.ini \
    --module="${CHATNOIR_APP}.wsgi" \
    --env=DJANGO_SETTINGS_MODULE="${CHATNOIR_APP}.settings"
