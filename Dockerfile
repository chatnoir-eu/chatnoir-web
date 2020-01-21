FROM ubuntu:18.04

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gosu \
        locales \
        python3 \
        python3-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
    && rm -rf /var/lib/apt/lists/*

# Force UTF-8 locale
RUN set -x && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

RUN set -x \
    && groupadd -g 3000 chatnoir \
    && useradd -u 3000 -g chatnoir -d /opt/apikey-frontned -s /bin/bash chatnoir \
    && mkdir /opt/apikey-frontend \
    && chown chatnoir /opt/apikey-frontend

WORKDIR /opt/apikey-frontend

COPY ./requirements.txt /opt/apikey-frontend/requirements.txt
RUN set -x \
    && ln -nfs /usr/bin/python3 /usr/bin/python \
    && pip3 install --no-cache-dir -r requirements.txt

COPY ./src/ /opt/apikey-frontend/

COPY ./wsgi.ini /opt/apikey-frontend/wsgi.ini
COPY ./docker-entrypoint.sh /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/opt/apikey-frontend/wsgi.ini"]
