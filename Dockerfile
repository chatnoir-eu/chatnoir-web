FROM node:24 as node_build

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
LABEL org.opencontainers.image.source=https://github.com/chatnoir-eu/chatnoir-web
LABEL org.opencontainers.image.description="ChatNoir Web Frontend"
LABEL org.opencontainers.image.licenses=Apache-2.0

# Force UTF-8 locale
RUN set -x \
    && apt update \
    && apt install -y locales \
    && sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen \
    && dpkg-reconfigure --frontend=noninteractive locales \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives

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

RUN set -x \
    && (cd chatnoir \
        && for s in $(ls **/settings.py); do \
            yes yes | chatnoir-manage collectstatic --settings "$(echo "$s" | sed 's/\//./g' | sed 's/\.py//')"; done) \
    && chown -R chatnoir:chatnoir /opt/chatnoir-web/chatnoir_static/

COPY ./docker-entrypoint.sh /docker-entrypoint.sh

USER chatnoir
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/opt/chatnoir-web/chatnoir/wsgi.ini"]
