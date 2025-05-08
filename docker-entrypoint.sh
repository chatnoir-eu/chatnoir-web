#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    export DJANGO_APP="${DJANGO_APP:-chatnoir}"

    if [ "$DJANGO_APP" != "web_cache" ]; then
        chatnoir-manage migrate --no-input
    fi
    if [ "$DJANGO_APP" = "chatnoir_admin" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
        chatnoir-manage createsuperuser --no-input 2> /dev/null || true
        unset DJANGO_SUPERUSER_USERNAME
        unset DJANGO_SUPERUSER_PASSWORD
    fi
    set -- "$@" --module="${DJANGO_APP}.wsgi" --env=DJANGO_SETTINGS_MODULE="${DJANGO_APP}.settings"
fi

exec "$@"
