# ChatNoir Web

ChatNoir web UI frontend and search backend.

The search backend is written in Python3 with Django, the frontend in JavaScript with VueJS.

## Build or Run Web Frontend
Install dependencies:
```bash
npm install
```

For development purposes, it is most convenient to run a [Vite](https://vite.dev/) dev server with auto-reload:
```bash
npm run serve
```
The dev server will run at `http://localhost:5173` and send requests to the backend server running at `http://localhost:8000` (see next section).

A static version of the frontend can be built with:
```bash
npm run build
```
The compiled files are written to `chatnoir_ui/dist/ui`. This static version can be used for production deployments, where you want to run only the Django backend server (ideally via uWSGI). See the next section for more information.


## Run Search Backend
The backend uses [Poetry](https://python-poetry.org/) as a package manager. If you haven't installed it yet, do that first:
```bash
# Option 1: pip
python3 -m pip install poetry

# Option 2: system package manager
sudo apt install python3-poetry
```

Then create a Poetry env and install all necessary Python dependencies:
```bash
poetry install
```

After a fresh installation, you need to create a local configuration file at `chatnoir/chatnoir/local_settings.py`. You can copy the provided `local_settings.example.py` and adjust the required settings.

Once the config has been created, initialize the database and the backend superuser (this has to be done only once): 
```bash
poetry run chatnoir-manage migrate
poetry run chatnoir-manage createsuperuser
```
The `chatnoir-manage` command behaves the same way as Django's default `manage.py` script and should be used in its stead.

If you're not using the Vite dev server, compile a static version of the frontend and collect the static files for Django to serve:
```bash
npm run build
yes yes | poetry run chatnoir-manage collectstatic --clear 
```

Finally, start the backend server:
```bash
poetry run chatnoir-serve
```
The `chatnoir-serve` command runs any pending migrations and then loads the default `chatnoir` Django app. If no other port is given, the server will run at `http://localhost:8000` and serve the static version of the frontend (if compiled), as well as the API backend.


### Hints and Troubleshooting

- If you use the Vite dev server, make sure you have configured Django's `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` properly (see `local_settings.example.py`).
- The built-in Django server and the Vite dev server should be used for development only. Production deployments should use uWSGI instead. A `Dockerfile` for a production-ready ChatNoir image is provided in this repository.
- Instead of using `poetry run`, you can also start an interactive Poetry shell in which you can invoke `chatnoir-serve` or `chatnoir-manage` directly:
  ```bash
  poetry shell
  chatnoir-serve
  ```

### Run Admin Backend and Other Django Apps

To run any other installed Django app or to pass additional parameters to the server, specify the app name after the `chatnoir-serve` command (note: you have to pass explicit port names to run multiple apps concurrently):
```bash
poetry run chatnoir-serve chatnoir
poetry run chatnoir-serve web_cache 8001
poetry run chatnoir-serve chatnoir_admin 8002
poetry run chatnoir-serve ir_anthology 8003
```
The parameters are the same as for Django's `runserver` command (run `chatnoir-serve APPNAME --help` for more information).


### Run ChatNoir in Docker

You can also run the ChatNoir front- and backend(s) in Docker:
```bash
docker run --rm --init -p 8000:8000 ghcr.io/chatnoir-eu/chatnoir-web
```
This will run a production-ready uWSGI server inside the container and expose it on port `8000`. Run without additional arguments, the ChatNoir server will have no `local_settings.py`, so requests to it will fail with an error. You can mount a local config into the container like so:
```bash
docker run --rm --init -p 8000:8000 \
    -v $(pwd)/local_settings.py:/opt/chatnoir-web/chatnoir/chatnoir/local_settings.py \
    ghcr.io/chatnoir-eu/chatnoir-web
```
Set the `CHATNOIR_APP` environment variable to start any of the non-default ChatNoir Django apps:
```bash
docker run --rm --init -p 8000:8000 -e CHATNOIR_APP=web_cache ghcr.io/chatnoir-eu/chatnoir-web
```
