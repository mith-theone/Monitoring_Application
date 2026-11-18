# Demo Monitoring Infrastructure

[![CI](https://github.com/mith-theone/Monitoring_Application/actions/workflows/ci.yml/badge.svg)](https://github.com/mith-theone/Monitoring_Application/actions/workflows/ci.yml)

Local Flask demo that shows read-only Linux server health (CPU, memory, network, ports) in a simple web UI.

## Setup → run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional; edit values
python app.py
```

Open [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login). If port 5000 is busy on a shared host, use `PORT=5303 python app.py` and open that port instead. Binds `0.0.0.0`; debug off by default.

## Demo credentials (local only)

| Variable | Demo default |
|----------|----------------|
| `ADMIN_USERNAME` | `admin` |
| `ADMIN_PASSWORD` | `admin123` |
| `SECRET_KEY` | random per process if unset |

Passwords are hashed at startup — see [docs/auth.md](docs/auth.md).

## Protected vs public routes

| Route | Access |
|-------|--------|
| `/login` | Public |
| `/`, `/servers`, `/servers/add`, `/api/metrics` | Login required |
| `/logout`, `/servers/<id>/delete` | POST + login + CSRF |

## Servers

1. Sign in → **Servers** → **Add server**
2. Fields: display name, hostname/IP, SSH user, port (default 22), key path **or** password
3. Example key path: `/home/jumpuser/.ssh/id_ed25519`
4. Cap: 10 servers. **Remove** only deletes local SQLite config — not the remote host.

DB file: `instance/monitoring.db` (gitignored). See [docs/db.md](docs/db.md).

## Dashboard & metrics

- **localhost** target uses local collectors (`psutil`) — no SSH needed for a quick demo
- Remote servers use SSH (Paramiko); see [docs/ssh.md](docs/ssh.md)
- Panels: CPU %, memory (used/free/total/swap), network bytes in/out, listening ports
- Auto-refresh every **5 seconds**; manual **Refresh** button
- Charts: Chart.js (CPU / memory). Unreachable hosts show a generic error (no secrets)

Metrics UI is **read-only** — no remote shell, kill, or config changes on targets.

### Troubleshooting “host unreachable”

- Host/IP reachable from this machine? Port open?
- Key path exists and is readable by the app user?
- Prefer key auth; password is demo-only

## Tests

```bash
pytest
```

Auth, DB, servers CRUD/authz, and metrics collectors (SSH mocked — no live SSH / no privileged access required).

## Security notes (demo)

- Session cookie: `HttpOnly`, `SameSite=Lax`
- CSRF on mutating forms (Flask-WTF)
- Bind `0.0.0.0`; `debug=False` by default
- Never commit `.env` or real secrets; use `.env.example` as a template
- SSH host keys: demo uses AutoAddPolicy — not for production ([docs/ssh.md](docs/ssh.md))

## PRD success criteria (mapped)

| Criterion | Where |
|-----------|--------|
| Admin sign-in with hashed password | `/login`, `app/auth.py` |
| Add/list servers (≤10) | `/servers` |
| Dashboard CPU/memory/network/ports | `/`, `/api/metrics` |
| ~5s refresh | `static/js/dashboard.js` |
| No mutating remote actions on metrics UI | dashboard read-only |

## CI vs local run

- **CI** (GitHub Actions on push/PR): `ruff` lint, `pytest`, app-factory smoke — **no** cloud deploy, no live SSH, no public server bind
- **Local**: run `python app.py` on your machine only (this demo has no CD deploy)
