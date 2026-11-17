# Database (SQLite)

## Location

- File: `instance/monitoring.db` (project `instance/` folder)
- Local-only demo storage — the `instance/` directory and `*.db` files are gitignored
- Directory permissions set to `0700` and DB file to `0600` where the OS allows

## `servers` table (PRD Feature 3)

| Column | Type | Notes |
|--------|------|--------|
| `id` | INTEGER PK | Auto-increment |
| `display_name` | TEXT | UI label |
| `host` | TEXT | Hostname or IP |
| `ssh_user` | TEXT | e.g. `ubuntu`, `jumpuser` |
| `ssh_key_path` | TEXT nullable | **Preferred** auth — path to private key on the app host |
| `ssh_password` | TEXT nullable | Demo fallback only if no key path; **residual risk** (stored for demo convenience) |
| `ssh_port` | INTEGER | Default `22` |
| `created_at` | TEXT | UTC-ish timestamp from SQLite `datetime('now')` |

Prefer key-based auth. Avoid putting real production SSH passwords in the demo DB.
