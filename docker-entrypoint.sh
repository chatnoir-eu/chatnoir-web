#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    export DJANGO_APP="${DJANGO_APP:-chatnoir}"
    export DJANGO_SETTINGS_MODULE="${DJANGO_APP}.settings"

    gosu chatnoir ./manage.py collectstatic
    gosu chatnoir ./manage.py migrate --no-input
    if [ "$DJANGO_APP" = "chatnoir_admin" ] && [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
        gosu chatnoir ./manage.py createsuperuser --no-input 2> /dev/null || true
    fi
    set -- gosu chatnoir "$@" --module "${DJANGO_APP}.wsgi"
fi

exec "$@"
