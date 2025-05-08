#!/usr/bin/env bash

docker build -t ghcr.io/chatnoir-eu/chatnoir-web .
if [ "$1" = "--push" ]; then
    docker push ghcr.io/chatnoir-eu/chatnoir-web
fi
