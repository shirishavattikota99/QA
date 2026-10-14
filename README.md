Project Deployments Management API

## Run app

```sh
. .venv/bin/activate
python3 main.py
# OR
uvicorn main:app --reload
# Run in docker mode
docker compose up -d
```

### First time setup

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
# then run with above commands
```

### Versions

- python 3.13
- pip 25
