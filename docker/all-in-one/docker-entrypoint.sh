#!/usr/bin/env bash
set -e

# Use the baked-in demo local_settings.py if the user hasn't mounted their own.
if [ ! -f /opt/chatnoir-web/chatnoir/chatnoir/local_settings.py ]; then
    cp /opt/chatnoir-web/local_settings.all-in-one.py /opt/chatnoir-web/chatnoir/chatnoir/local_settings.py
fi

# Make sure data directories exist and are writable by the service users
# (important when they are bind-mounted/volume-mounted from the host).
mkdir -p /var/lib/elasticsearch /var/log/elasticsearch /data/s3
chown -R elasticsearch:elasticsearch /var/lib/elasticsearch /var/log/elasticsearch
chown -R minio:minio /data/s3
chown -R chatnoir:chatnoir /opt/chatnoir-web/db.sqlite3 2>/dev/null || true

exec "$@"
