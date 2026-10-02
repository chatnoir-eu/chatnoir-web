#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

docker build -t ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1 -f "${SCRIPT_DIR}/Dockerfile" "${REPO_ROOT}"
docker tag ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1 ghcr.io/chatnoir-eu/chatnoir-complete:latest
if [ "$1" = "--push" ]; then
    docker push ghcr.io/chatnoir-eu/chatnoir-complete:0.0.1
    docker push ghcr.io/chatnoir-eu/chatnoir-complete:latest
fi
