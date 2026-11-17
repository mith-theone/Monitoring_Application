# PRD: Demo Monitoring Infrastructure (Linux Servers)

## 1. Overview

Local demo application that shows live Linux server health (CPU, memory, network, ports) in a read-only web UI so L1/L2/L3 and app teams do not need to SSH in for a quick check.

**Audience:** Internal infra and application teams (L1–L3)  
**Type:** Demo only — run on the same machine where Cursor is running  
**Stack:** Python, Flask, attractive HTML/CSS/JS UI

---

## 2. Problem

Today, checking real-time memory, CPU, network, and port usage means logging into each Linux server. This is slow for triage and unsuitable for a shared demo view.

---

## 3. Goals (demo)

- Sign in as a single admin user
- Add Linux servers to monitor
- View read-only, auto-refreshing metrics in a simple dashboard
- Run locally with minimal setup

## 4. Non-goals

- Alerts / notifications
- Historical long-term storage or trend reports
- Log viewing / process kill / any write actions on servers
- Multi-user roles (L1/L2/L3 labels are viewers only; one login)
- Docker packaging (optional later; not required for v1)
- Agents installed on target servers

---

## 5. Users & access

| Role | Who | Access |
|------|-----|--------|
| Admin | Demo operator | Sign in; add/remove servers; view all metrics |
| Viewer teams (L1/L2/L3) | Infra & app groups | Same login in demo; UI is read-only for metrics |

**Authentication (Feature 2)**

- Default username: `admin`
- Password stored as a **hash** (e.g. Werkzeug / bcrypt); never store plaintext
- Demo default password: `admin123` (document in README; change via env var preferred)
- Session-based login; unauthenticated users redirected to sign-in
- No self-registration

---

## 6. Core features

### Feature 1 — Read-only, user-friendly UI

- Clean dashboard layout (cards/charts; light ops-friendly theme)
- Metrics views are **read-only** (no remote shell, no config change on targets)
- Auto-refresh every **5 seconds** (manual refresh also available)
- Clear empty/error states when a host is unreachable
- **Increment 0 status:** dashboard panels (CPU / Memory / Network / Ports) are placeholders with empty-state messaging until metrics collectors land in later increments. UI has no mutating forms for remote hosts.

### Feature 2 — Sign-in

- Login page with username + password
- Defaults as above (`admin` + hashed `admin123`)

### Feature 3 — Add Linux servers

Required fields when adding a server:

| Field | Notes |
|-------|--------|
| Display name | Label in UI |
| Hostname / IP | Target address |
| SSH user | e.g. `ubuntu`, `jumpuser` |
| Auth | SSH private key path **or** password (demo: prefer key path if available) |
| SSH port | Default `22` |

- Store server definitions in local **SQLite**
- Support **up to ~10** servers for the demo
- Ability to list and remove servers from the UI
- Optional: include **localhost** as a first demo target

---

## 7. Metrics (v1)

Collected over **SSH** from the Flask host (no agent on targets).

| Area | What to show |
|------|----------------|
| CPU | Overall usage % |
| Memory | Used / free / total / %; include swap used/total |
| Network | Bytes in/out per interface (simple counters or rate if easy) |
| Ports | Listening ports (port, proto, process name if available) |

**Out of scope for v1:** per-core CPU, latency/packet loss, open connection dumps, disk, alerts.

---

## 8. Technical approach (minimal)

| Item | Choice |
|------|--------|
| Backend | Flask |
| Frontend | Server-rendered templates + small JS for refresh; Bootstrap or similar for UI |
| Charts | Lightweight chart library (e.g. Chart.js) |
| DB | SQLite (users + servers) |
| Collection | SSH commands / remote reads from app host |
| Refresh | HTTP poll every 5s |
| Run | `python app.py` or `flask run` on localhost |

Suggested bind: `0.0.0.0:5000` — open `http://127.0.0.1:5000` or the host IP

---

## 9. Local run (minimal steps)

1. Create/activate a Python venv  
2. `pip install -r requirements.txt`  
3. Set optional env (or use defaults): `ADMIN_PASSWORD=admin123`  
4. `python app.py`  
5. Open browser → sign in as `admin` → add a Linux host (or localhost) → view dashboard  

No Docker required for the demo.

---

## 10. Success criteria

- Admin can sign in with hashed password verification  
- At least one Linux server (or localhost) can be added and listed  
- Dashboard shows CPU, memory, network, and listening ports without SSH login by the viewer  
- UI updates about every 5 seconds while the page is open  
- Metrics screens offer no mutating actions  

---

## 11. Open assumptions (defaults applied)

- Collection = SSH from the app host  
- Single admin account  
- Auto-refresh = 5 seconds  
- Password demo default = `admin123` (hashed at rest)  
- Scale = up to ~10 hosts  
- Delivery = plain Flask on localhost  

---

## 12. Future (not in this demo)

- Per-role accounts, SSO  
- Alerting and history  
- Disk / process deep dive  
- Agent-based collection  
- Docker Compose deploy  
