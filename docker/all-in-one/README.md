# ChatNoir All-in-One Docker Image

Builds a single image bundling Elasticsearch, a MinIO S3-compatible object store, and the ChatNoir
frontend/backend, all managed by `supervisord` inside one container. Intended for local testing/demos only,
**not** for production use.

It ships with a baked-in demo `local_settings.py` that points ChatNoir at the bundled Elasticsearch (security
disabled, no credentials needed) and MinIO (fixed default root credentials, so no manual S3 setup is required).

## Build

```bash
./docker/all-in-one/build.sh
```

## Run

```bash
docker run --rm --init -p 8000:8000 -p 9200:9200 -p 9000:9000 -p 9001:9001 ghcr.io/chatnoir-eu/chatnoir-complete
```

- ChatNoir frontend/backend: `http://localhost:8000`
- Elasticsearch API: `http://localhost:9200`
- MinIO S3 API / console: `http://localhost:9000` / `http://localhost:9001`

No `SEARCH_INDICES` are pre-configured; add your own indices/buckets by mounting a custom `local_settings.py` over
`/opt/chatnoir-web/chatnoir/chatnoir/local_settings.py` once you've ingested data into the bundled services.

Note that Elasticsearch normally requires the host's `vm.max_map_count` to be raised; this image sets
`node.store.allow_mmap: false` instead so it also works unmodified on restricted hosts (with a performance cost).
