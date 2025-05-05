# ChatNoir Web UI

ChatNoir web UI and search backend.

The search backend ist written in Python3 with Django, the frontend in Javascript with VueJS.

## Build and Run Web Frontend
Install dependencies:
```bash
cd chatnoir_ui
npm install
```

Build production distribution:
```bash
npm run build
```

Run dev server (for development only):
```bash
npm run serve
```

Hint: If the website is missing assets (images or CSS) when running the dev server, delete `node_modules/.cache` and restart the Node dev server.

## Build Search Backend
The backend uses [Poetry](https://python-poetry.org/) as a package manager. If you haven't installed it yet, do that first:
```bash
python3 -m pip install poetry
```

Next, install all Python dependencies and start a Poetry shell:
```bash
cd chatnoir
poetry install
poetry shell
```

At first run or after an upgrade, you have to set up the models:
```bash
./manage.py createcachetable
./manage.py migrate
```

Before you can actually run the backend, you need to create a local configuration file (see `chatnoir/chatnoir/local_settings.example.py` for examples) and build the frontend production distribution first (see above).

Finally, start the backend server:
```bash
./manage.py runserver
```

The web UI served by the Django server runs at `localhost:8000`. The Node development server runs at `localhost:8080`. You can use either one, but communication between frontend backend will only work properly with the former due to CORS- and CSRF protections. As long as the Node server is running also in the background, the frontend when served via Django on port `8000` will behave just as if served via Node. If you start only the Django server and not the Node development server, you will have to recompile the frontend manually with `npm run build` and reload the page in order so see changes.

*Note:* The order in which you start the servers is important. Always start the Node server before the Django server. If you switch between running the Node development server or building a production version of the frontend, you need to restart the Django server afterwards.

## Start the Admin backend

Before you can start the admin backend, you have to apply the pending migrations and create a superuser:

```bash
DJANGO_SETTINGS_MODULE=chatnoir_admin.settings ./manage.py migrate
DJANGO_SETTINGS_MODULE=chatnoir_admin.settings ./manage.py createsuperuser
```

Afterwards, the server can be started like so:

```bash
DJANGO_SETTINGS_MODULE=chatnoir_admin.settings ./manage.py runserver localhost:8001
```

This should spawn the Admin backend on `localhost:8001`.

## Build the docker image

```
docker build -t registry.webis.de/code-lib/public-images/chatnoir:testing-ir-datasets .
```
