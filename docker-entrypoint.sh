#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    export DJANGO_APP="${DJANGO_APP:-chatnoir}"
    export DJANGO_SETTINGS_MODULE="${DJANGO_APP}.settings"

    gosu chatnoir ./manage.py collectstatic
    gosu chatnoir ./manage.py migrate
    set -- gosu chatnoir "$@" --module "${DJANGO_APP}.wsgi"
fi

exec "$@"
