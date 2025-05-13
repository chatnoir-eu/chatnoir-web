#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    export CHATNOIR_APP="${CHATNOIR_APP:-chatnoir}"

    if [ "$CHATNOIR_APP" != "web_cache" ]; then
        chatnoir-manage migrate --no-input
        chatnoir-manage collectstatic
    fi
    if [ "$CHATNOIR_APP" = "chatnoir_admin" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
        chatnoir-manage createsuperuser --no-input 2> /dev/null || true
        unset DJANGO_SUPERUSER_USERNAME
        unset DJANGO_SUPERUSER_PASSWORD
    fi
    set -- "$@" --module="${CHATNOIR_APP}.wsgi" --env=DJANGO_SETTINGS_MODULE="${CHATNOIR_APP}.settings"
fi

exec "$@"
