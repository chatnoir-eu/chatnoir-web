#!/usr/bin/env bash
set -e

# web_cache is a stateless, DB-less Django app (it has no migrations of its
# own) that renders cached/original document views for search results. It
# shares Elasticsearch/MinIO config with the main chatnoir app via the same
# local_settings.py, but runs as its own uwsgi process on a separate port
# (8001) since it's normally deployed as a standalone service.

echo "Waiting for Elasticsearch to become available..."
for i in $(seq 1 60); do
    if curl -s -o /dev/null "http://127.0.0.1:9200"; then
        break
    fi
    sleep 2
done

exec uwsgi --ini /opt/chatnoir-web/wsgi-web-cache.ini \
    --module=web_cache.wsgi \
    --env=DJANGO_SETTINGS_MODULE=web_cache.settings
