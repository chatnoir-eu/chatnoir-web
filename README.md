# ChatNoir Web

ChatNoir web UI frontend and search backend.

The search backend is written in Python3 with Django, the frontend in JavaScript with VueJS.

## Build or Run Web Frontend
Install dependencies:
```bash
npm install
```

For development purposes, it is most convenient to run a Node dev server with auto-reload:
```bash
npm run serve
```

For production deployments, you want to run only the Django backend server (ideally via uWSGI), in which case you will have to compile a static version of the frontend with:
```bash
npm run build
```

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

Finally, start the backend server:
```bash
poetry run chatnoir-serve
```

The `chatnoir-serve` command will run any pending migrations and load the default `chatnoir` Django app. The Django server runs by default at `localhost:8000`. If deployed, the Node development server runs at `localhost:8080`. Both serve the same frontend web UI. Although you can access either one, only the Django server will provide the temporary API tokens required for communication between frontend and backend.

### Hints and Troubleshooting

- Make sure you run both servers either on `localhost` or on `127.0.0.1`, but not on a mixture of the two, which would create CORS issues.
- If you use the Node dev server and the served website is missing assets (images or CSS), delete `node_modules/.cache` and restart the Node server.
- The Django server should be used for development only. Production deployments should use uWSGI instead. A `Dockerfile` for a production-ready ChatNoir image is provided in this repository.
- Instead of using `poetry run`, you can also start an interactive Poetry shell in which you can invoke `chatnoir-serve` or `chatnoir-manage` directly:
  ```bash
  poetry shell
  chatnoir-serve
  ```

### Run Admin Backend and Other Django Apps

To run any other installed Django app or to pass additional parameters to the server, specify the app name after the `chatnoir-serve` command (note: you have to pass explicit port names to run multiple apps concurrently):
```bash
poetry run chatnoir-serve chatnoir
poetry run chatnoir-serve chatnoir_admin 8001
poetry run chatnoir-serve ir_anthology 8002
```
The parameters are the same as for Django's `runserver` command (run `chatnoir-serve APPNAME --help` for more information).
