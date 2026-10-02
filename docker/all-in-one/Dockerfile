# All-in-one ChatNoir image bundling Elasticsearch, MinIO (S3, no-auth demo
# credentials baked in) and the ChatNoir web frontend/backend in a single
# container. Intended for local testing/demos, not for production use.
#
# docker build -t ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1-base -f docker/all-in-one/Dockerfile .
# docker tag ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1 ghcr.io/chatnoir-eu/chatnoir-complete:latest
# docker push ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1
# docker push ghcr.io/chatnoir-eu/chatnoir-complete:latest

# NOTE: MinIO's "community edition" dropped pre-built binaries from dl.min.io
# in favor of their licensed "AIStor" product. The plain open-source (AGPLv3)
# server binary is still published as a GitHub release asset for this pinned
# version, which is what we use here.
ARG ELASTICSEARCH_VERSION=8.17.4
ARG MINIO_DOWNLOAD_URL=https://github.com/minio/minio/releases/download/RELEASE.2025-04-08T15-41-24Z/minio.linux-amd64.RELEASE.2025-04-08T15-41-24Z

FROM node:26 AS node_build

COPY package.* /work/
COPY chatnoir/ /work/chatnoir/
COPY chatnoir_ui/ /work/chatnoir_ui/

# Build frontend in temporary stage
WORKDIR /work/
RUN set -x \
    && ls \
    && npm install \
    && npm run build


FROM python:3.12
ARG ELASTICSEARCH_VERSION
LABEL org.opencontainers.image.source=https://github.com/chatnoir-eu/chatnoir-web
LABEL org.opencontainers.image.description="ChatNoir all-in-one image (Elasticsearch + MinIO + ChatNoir)"
LABEL org.opencontainers.image.licenses=Apache-2.0

# Force UTF-8 locale, add the Elastic APT repo and install Elasticsearch
# (as a native Debian package, so it matches this base image's libc) plus
# supervisord's runtime dependencies.
RUN set -x \
    && apt update \
    && apt install -y locales curl gnupg apt-transport-https \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && curl -fsSL https://artifacts.elastic.co/GPG-KEY-elasticsearch | gpg --dearmor -o /usr/share/keyrings/elastic.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/elastic.gpg] https://artifacts.elastic.co/packages/8.x/apt stable main" > /etc/apt/sources.list.d/elastic-8.x.list \
    && apt update \
    && apt install -y --no-install-recommends elasticsearch=${ELASTICSEARCH_VERSION} \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives

# Elasticsearch config: single-node, no security/TLS, modest heap, and
# mmap-less storage so it also runs in environments that can't raise the
# host's vm.max_map_count. The Debian package's postinst already auto-enabled
# security/TLS in elasticsearch.yml during install; strip that block first so
# our settings below aren't duplicate keys.
RUN set -x \
    && sed -i '/BEGIN SECURITY AUTO CONFIGURATION/,/END SECURITY AUTO CONFIGURATION/d' /etc/elasticsearch/elasticsearch.yml \
    && rm -rf /etc/elasticsearch/certs \
    && { \
        echo "discovery.type: single-node"; \
        echo "xpack.security.enabled: false"; \
        echo "xpack.security.enrollment.enabled: false"; \
        echo "xpack.security.http.ssl.enabled: false"; \
        echo "xpack.security.transport.ssl.enabled: false"; \
        echo "node.store.allow_mmap: false"; \
        echo "network.host: 0.0.0.0"; \
    } >> /etc/elasticsearch/elasticsearch.yml \
    && mkdir -p /etc/elasticsearch/jvm.options.d \
    && { \
        echo "-Xms512m"; \
        echo "-Xmx512m"; \
    } > /etc/elasticsearch/jvm.options.d/heap.options

# Install MinIO (statically-linked binary, downloaded directly)
ARG MINIO_DOWNLOAD_URL
RUN set -x \
    && curl -fsSL -o /usr/local/bin/minio "${MINIO_DOWNLOAD_URL}" \
    && chmod +x /usr/local/bin/minio \
    && groupadd -r minio \
    && useradd -r -g minio -d /data/s3 -s /usr/sbin/nologin minio \
    && mkdir -p /data/s3 \
    && chown -R minio:minio /data/s3

# Install supervisord (process manager for ES + MinIO + ChatNoir)
RUN python3 -m pip install --no-cache-dir --break-system-packages supervisor

# Install ChatNoir
COPY pyproject.toml poetry.lock LICENSE README.md /opt/chatnoir-web/
COPY chatnoir/ /opt/chatnoir-web/chatnoir/
COPY --from=node_build /work/chatnoir_ui/dist/ /opt/chatnoir-web/chatnoir_ui/dist/

WORKDIR /opt/chatnoir-web/
RUN set -x \
    && groupadd -g 1000 chatnoir \
    && useradd -u 1000 -g chatnoir -d /opt/chatnoir -s /bin/bash chatnoir \
    && python3 -m pip install --no-cache-dir --break-system-packages --editable /opt/chatnoir-web/ \
    && chown -R chatnoir:chatnoir /opt/chatnoir-web/

COPY docker/all-in-one/local_settings.template.py /opt/chatnoir-web/local_settings.all-in-one.py
COPY docker/all-in-one/start-chatnoir.sh /opt/chatnoir-web/start-chatnoir.sh
RUN chmod +x /opt/chatnoir-web/start-chatnoir.sh \
    && cp /opt/chatnoir-web/local_settings.all-in-one.py /opt/chatnoir-web/chatnoir/chatnoir/local_settings.py

RUN set -x \
    && (cd chatnoir \
        && for s in $(ls **/settings.py); do \
            yes yes | chatnoir-manage collectstatic --settings "$(echo "$s" | sed 's/\//./g' | sed 's/\.py//')"; done) \
    && chown -R chatnoir:chatnoir /opt/chatnoir-web/chatnoir_static/

COPY docker/all-in-one/supervisord.conf /etc/supervisord.conf
COPY docker/all-in-one/docker-entrypoint.sh /docker-entrypoint-all-in-one.sh
RUN chmod +x /docker-entrypoint-all-in-one.sh

ENV CHATNOIR_APP=chatnoir
ENV MINIO_ROOT_USER=chatnoir
ENV MINIO_ROOT_PASSWORD=chatnoirchatnoir

EXPOSE 8000 9200 9000 9001

ENTRYPOINT ["/docker-entrypoint-all-in-one.sh"]
CMD ["supervisord", "-n", "-c", "/etc/supervisord.conf"]
