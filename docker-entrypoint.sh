#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    gosu chatnoir ./manage.py collectstatic
    gosu chatnoir ./manage.py migrate
    set -- gosu chatnoir "$@"
fi

exec "$@"
