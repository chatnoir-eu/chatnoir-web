FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN set -x \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        gnupg2 \
        gosu \
        locales \
        lsb-release \
        python3 \
        python3-dev \
        python3-pip \
        python3-psycopg2 \
        python3-setuptools \
        python3-wheel \
    && curl -sfL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - \
    && echo "deb https://deb.nodesource.com/node_19.x/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/node.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Force UTF-8 locale
RUN set -x && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8

COPY ./chatnoir/ /opt/chatnoir/
RUN set -x \
    && groupadd -g 1000 chatnoir \
    && useradd -u 1000 -g chatnoir -d /opt/chatnoir -s /bin/bash chatnoir \
    && (cd /opt/chatnoir \
        && ln -nfs /usr/bin/python3 /usr/bin/python \
        && python3 -m pip install --no-cache-dir -r requirements.txt) \
    && chown -R chatnoir:chatnoir /opt/chatnoir

COPY ./chatnoir_ui/ /opt/chatnoir_ui/
RUN set -x \
    && (cd /opt/chatnoir_ui \
        && npm install \
        && npm run build \
        && rm -rf node_modules) \
    && chown -R chatnoir:chatnoir /opt/chatnoir_ui

RUN set -x \
    && mkdir /opt/chatnoir_static \
    && chown chatnoir:chatnoir /opt/chatnoir_static

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /opt/chatnoir
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/opt/chatnoir/wsgi.ini"]
