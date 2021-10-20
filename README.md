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

Run debug server (for development only):
```bash
npm run serve
```

## Build Search Backend
Install Python dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r chatnoir/requirements.txt
```

Set up models:
```bash
cd chatnoir
./manage.py createcachetable
./manage.py migrate
```

Before you can run the backend, you need to create a local configuration file (see `chatnoir/chatnoir/local_settings.example.py` for examples) and build the frontend production distribution first (see above). Then, to start the backend server, run:
```bash
./manage.py runserver
```
