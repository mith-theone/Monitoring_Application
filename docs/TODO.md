# TODO: Demo Monitoring Infrastructure (Linux)

Small, AI-friendly increments. Check boxes as you complete each step.  
Demo target: run locally on the Cursor host (bind `0.0.0.0:5000`; open `http://127.0.0.1:5000` or the host IP).

Reference: [requirements.md](./requirements.md)

---

## Increment 0 — Project initialization + basic UI

- [x] **0.1** Create project layout (`app/`, `templates/`, `static/`, `tests/`, `docs/`)
  - Security: add `.gitignore` (venv, `__pycache__`, `.env`, `*.db`, secrets, SSH keys)
  - Docs: one-line note in `README.md` describing the repo purpose
- [x] **0.2** Add `requirements.txt` with Flask (+ pin versions lightly for demo)
  - Security: no unused packages; prefer pinned versions
  - Docs: document `python -m venv .venv` and `pip install -r requirements.txt`
- [x] **0.3** Create minimal Flask app entry (`app.py` or `app/__init__.py`) serving `/`
  - Security: bind to `0.0.0.0` for local demo; debug flag off by default
  - Docs: “How to run” — `python app.py` → open `http://127.0.0.1:5000` (or host IP)
- [x] **0.4** Add base HTML layout (Bootstrap or similar) + simple home/dashboard shell
  - Security: no inline secrets; use CSP-friendly CDN or local static assets
  - Docs: screenshot or short UI description in `README.md`
- [x] **0.5** Add placeholder read-only panels (CPU / Memory / Network / Ports) with empty state
  - Security: confirm UI has no forms that mutate remote hosts
  - Docs: note in `docs/requirements.md` or README that panels are placeholders until metrics land

---

## Increment 1 — Sign-in + unit tests

- [x] **1.1** Add config for `SECRET_KEY` and `ADMIN_PASSWORD` from environment (with demo defaults)
  - Security: never commit real secrets; generate a random `SECRET_KEY` for sessions; document env vars
  - Docs: document `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=admin123`, `SECRET_KEY=...` in README
- [x] **1.2** Implement password hashing helper (Werkzeug `generate_password_hash` / `check_password_hash`)
  - Security: store/compare hashes only; no plaintext password logging
  - Docs: comment or short `docs/` note that passwords are hashed
- [x] **1.3** Add login page UI (`/login`) — username + password form
  - Security: POST-only submit; CSRF protection (Flask-WTF or equivalent minimal approach)
  - Docs: update README with default credentials (demo only)
- [x] **1.4** Implement session-based sign-in / sign-out; protect dashboard routes
  - Security: redirect unauthenticated users to `/login`; invalidate session on logout; `HttpOnly` session cookie
  - Docs: document protected routes vs public `/login`
- [x] **1.5** Seed / verify single `admin` user against hashed password
  - Security: reject empty passwords; constant-time hash check via library; generic login error message
  - Docs: “Change demo password via env” steps
- [x] **1.6** Unit tests for auth helpers and login/logout flows (`tests/test_auth.py`)
  - Security: assert plaintext password never appears in responses/logs; assert protected route returns 302/401 when logged out
  - Docs: document `pytest` run command in README
- [x] **1.7** Unit tests for config defaults and hash verification edge cases
  - Security: cover wrong password, missing user, session required
  - Docs: mark Increment 1 done in this file when green

---

## Increment 2 — Database foundation (SQLite)

- [x] **2.1** Add SQLite setup and app DB path (local file under project or `instance/`)
  - Security: keep DB outside VCS via `.gitignore`; restrictive file permissions where practical
  - Docs: where the DB file lives and that it is local-only
- [x] **2.2** Create schema for servers table (display name, host, ssh user, auth fields, port)
  - Security: do not store SSH passwords in plaintext if avoidable; prefer key path; document residual risk for demo password field
  - Docs: table fields matching PRD Feature 3
- [x] **2.3** Unit tests for DB init and basic CRUD helpers
  - Security: parameterized queries only (no string-built SQL)
  - Docs: `pytest` covers DB helpers

---

## Increment 3 — Add / list / remove servers (UI + API)

- [x] **3.1** Server list page (read-only table) behind login
  - Security: require authenticated session
  - Docs: short “Servers” section in README
- [x] **3.2** Add-server form (name, hostname/IP, SSH user, key path or password, port default 22)
  - Security: validate host/port input; cap at ~10 servers; sanitize display name; never echo SSH password back in HTML
  - Docs: field meanings and SSH key path example
- [x] **3.3** Persist new server to SQLite; show success/error flash
  - Security: CSRF on form; authorize admin session only
  - Docs: update TODO checkboxes / README “add a host” step
- [x] **3.4** Remove-server action (POST) with confirm in UI
  - Security: POST + CSRF; no GET delete; confirm dialog
  - Docs: note that remove only deletes local config, not the remote host
- [x] **3.5** Unit tests for add/list/remove and authz on those routes
  - Security: unauthenticated add/remove must fail; over-limit add rejected
  - Docs: test commands still work

---

## Increment 4 — Localhost metrics (no SSH yet)

- [x] **4.1** Implement local collectors for CPU and memory (e.g. `psutil`) for localhost demo
  - Security: read-only APIs; no shell=`True` with user input
  - Docs: explain localhost works without SSH for quick demo
- [x] **4.2** Implement local network I/O and listening ports collectors
  - Security: display-only; no bind/listen changes
  - Docs: list metrics shown on dashboard
- [x] **4.3** Wire collectors into dashboard for a “localhost” target
  - Security: still read-only UI
  - Docs: how to open dashboard and see localhost stats
- [x] **4.4** Unit tests with mocked collector outputs
  - Security: tests must not need real privileged access
  - Docs: note mocks in test docs/README

---

## Increment 5 — SSH metrics collection (remote Linux)

- [x] **5.1** Add SSH client helper (e.g. Paramiko) with connect timeout
  - Security: host key policy documented (demo: known_hosts or explicit warning); never log private keys/passwords; timeouts to avoid hangs
  - Docs: SSH prerequisites (key-based preferred)
- [x] **5.2** Remote commands/parsers for CPU + memory over SSH
  - Security: fixed command allowlist only; no user-supplied shell strings
  - Docs: which remote commands are used
- [x] **5.3** Remote network + listening ports over SSH
  - Security: same allowlist; handle permission errors gracefully
  - Docs: expected remote tools (`ss`/`ps` etc.) if any
- [x] **5.4** Per-server metrics endpoint or server detail page using SSH collectors
  - Security: auth required; do not expose raw SSH errors with secrets
  - Docs: how to add a remote host and view it
- [x] **5.5** Unit tests with mocked SSH client (success + unreachable)
  - Security: ensure credentials not asserted in plaintext in test output beyond fixtures
  - Docs: no live SSH required for CI

---

## Increment 6 — Dashboard UX (refresh + charts + errors)

- [x] **6.1** Auto-refresh metrics every 5 seconds (JS poll) + manual refresh button
  - Security: poll only authenticated JSON/HTML endpoints; no credentials in query strings
  - Docs: refresh behavior in README
- [x] **6.2** Add simple Chart.js (or similar) for CPU/memory
  - Security: load scripts from pinned CDN or local static files
  - Docs: UI overview update
- [x] **6.3** Empty / unreachable host error states in UI
  - Security: generic errors to user; details in server logs without secrets
  - Docs: troubleshooting “host unreachable”
- [x] **6.4** Light smoke/UI tests or route tests for dashboard JSON/HTML
  - Security: ensure metrics routes require login
  - Docs: how to verify refresh locally

---

## Increment 7 — Hardening + docs polish (demo)

- [x] **7.1** Review: session cookie flags, CSRF, `0.0.0.0` bind, debug off by default
  - Security: checklist pass against PRD security notes
  - Docs: “Security notes (demo)” section in README
- [x] **7.2** Ensure `.env.example` exists (no real secrets) and README run steps are minimal (venv → install → run)
  - Security: `.env` gitignored
  - Docs: final copy-paste local run instructions
- [x] **7.3** Confirm metrics UI has no mutating remote actions
  - Security: read-only guarantee
  - Docs: mark PRD success criteria mapped in README

---

## Increment 8 — CI/CD (GitHub Actions)

- [x] **8.1** Add `.github/workflows/ci.yml` — lint/format check (e.g. `ruff` or `flake8`) on PR/push
  - Security: Actions pinned to known versions (`actions/checkout`, `actions/setup-python`); least privileges (`permissions: contents: read`)
  - Docs: mention CI badge or “CI runs on push/PR” in README
- [x] **8.2** CI job: install deps + run `pytest`
  - Security: no SSH secrets in CI; tests use mocks only
  - Docs: how to read CI failures
- [x] **8.3** Optional CI job: basic import/app factory smoke test
  - Security: do not start a publicly bound server in CI
  - Docs: note what CI does *not* deploy (local demo only)
- [x] **8.4** Document that deployment is local-only (no CD deploy to cloud for this demo)
  - Security: avoid publishing demo credentials in workflow logs
  - Docs: “CI vs local run” short section

---

## Suggested order for AI-assisted sessions

1. Complete **Increment 0** end-to-end (app runs, basic UI visible).
2. Complete **Increment 1** (login works + auth tests green).
3. Then **2 → 3** (servers CRUD).
4. Then **4 → 5** (localhost metrics, then SSH).
5. Then **6 → 7** (UX + hardening).
6. Finish with **8** (GitHub Actions CI).

Keep each checkbox as one PR or one agent session when possible.
