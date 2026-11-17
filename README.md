# Demo Monitoring Infrastructure

Local Flask demo that shows read-only Linux server health (CPU, memory, network, ports) in a simple web UI.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## How to run

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) (or the host’s IP on port 5000).

The app binds to `0.0.0.0:5000`. Debug mode is off by default.

Unauthenticated visitors are redirected to `/login`. After sign-in, `/` (dashboard) is available. Use **Sign out** (POST) to clear the session.

## Demo credentials (local only)

| Variable | Demo default |
|----------|----------------|
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | `admin123` |
| `SECRET_KEY` | random per process if unset |

Example:

```bash
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin123
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python app.py
```

The password is hashed at startup (Werkzeug); see [docs/auth.md](docs/auth.md). Change the demo password by setting `ADMIN_PASSWORD` before starting the app.

## Database

Server definitions are stored in local SQLite at `instance/monitoring.db` (gitignored, local-only). Prefer SSH key path over password; see [docs/db.md](docs/db.md).

## Tests

```bash
pytest
```

`pytest` covers auth flows and DB init/CRUD helpers.

## UI

The home page is a dashboard shell with four read-only panels — **CPU**, **Memory**, **Network**, and **Ports** — each showing an empty state until metrics collectors are wired up. There are no forms that mutate remote hosts.
