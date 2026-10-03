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
docker run --rm --init -p 8000:8000 -p 8001:8001 -p 9200:9200 -p 9000:9000 -p 9001:9001 ghcr.io/chatnoir-eu/chatnoir-complete
```

- ChatNoir frontend/backend: `http://localhost:8000`
- ChatNoir web cache / document viewer (used by search result "cache" links): `http://localhost:8001`
- Elasticsearch API: `http://localhost:9200`
- MinIO S3 API / console: `http://localhost:9000` / `http://localhost:9001`

A demo `cranfield` entry is pre-configured in `SEARCH_INDICES` (pointing at indices `chatnoir_data_cranfield` /
`chatnoir_meta_cranfield`); add your own indices/buckets by mounting a custom `local_settings.py` over
`/opt/chatnoir-web/chatnoir/chatnoir/local_settings.py` once you've ingested data into the bundled services.

Note that Elasticsearch normally requires the host's `vm.max_map_count` to be raised; this image sets
`node.store.allow_mmap: false` instead so it also works unmodified on restricted hosts (with a performance cost).
Disk-based shard allocation is also disabled (`cluster.routing.allocation.disk.threshold_enabled: false`), since
demo/dev hosts are often low on free disk space. The `analysis-icu`, `analysis-kuromoji`, and `analysis-smartcn`
plugins are installed, as required by ChatNoir's multilingual index mappings.

## API key

The ChatNoir migrations already create keys restricted to `127.0.0.1`/`::1`, which don't work from outside the
container (e.g. through a mapped Docker port). On every startup, the entrypoint also issues (or reuses) an
**unrestricted demo API key** for testing, prints it to the container logs, and saves it to
`/opt/chatnoir-web/demo-apikey.txt` inside the container:

```bash
docker logs <container> 2>&1 | grep -A2 "demo API key"
# or
docker exec <container> cat /opt/chatnoir-web/demo-apikey.txt
```

Use it against the API, e.g.:

```bash
curl "http://localhost:8000/api/v1/_search?q=aerodynamics&index=cranfield&apikey=<key>"
```

This key is unrestricted and meant for local testing only — don't expose it or this image publicly.
