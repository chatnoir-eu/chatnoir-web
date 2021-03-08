#!/usr/bin/env bash
set -e

if [ "$1" = "uwsgi" ]; then
    export DJANGO_APP="${DJANGO_APP:-chatnoir}"
    export DJANGO_SETTINGS_MODULE="${DJANGO_APP}.settings"

    gosu chatnoir ./manage.py collectstatic
    gosu chatnoir ./manage.py migrate --no-input
    gosu chatnoir ./manage.py createsuperuser --no-input \
        --username 'webis' --email 'webis@listserv.uni-weimar.de' 2> /dev/null | true
    gosu chatnoir ./manage.py createcachetable
    set -- gosu chatnoir "$@" --module "${DJANGO_APP}.wsgi"
fi

exec "$@"
