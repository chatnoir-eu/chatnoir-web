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

# Issue an unrestricted demo API key for direct API access (the keys created
# by the ChatNoir migrations are locked to 127.0.0.1/::1 and won't work from
# outside the container, e.g. via a mapped Docker port).
if [ "$CHATNOIR_APP" = "chatnoir" ]; then
    DEMO_API_KEY="$(chatnoir-manage shell < /opt/chatnoir-web/create-demo-apikey.py | grep -oP '(?<=^DEMO_API_KEY=).*')"
    if [ -n "$DEMO_API_KEY" ]; then
        echo "=================================================================="
        echo " ChatNoir demo API key (unrestricted, for testing only):"
        echo " $DEMO_API_KEY"
        echo " Also saved to /opt/chatnoir-web/demo-apikey.txt in the container."
        echo "=================================================================="
    fi
fi

if [ "$CHATNOIR_APP" = "chatnoir_admin" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    chatnoir-manage createsuperuser --no-input 2> /dev/null || true
    unset DJANGO_SUPERUSER_USERNAME
    unset DJANGO_SUPERUSER_PASSWORD
fi

exec uwsgi --ini /opt/chatnoir-web/chatnoir/wsgi.ini \
    --module="${CHATNOIR_APP}.wsgi" \
    --env=DJANGO_SETTINGS_MODULE="${CHATNOIR_APP}.settings"
