"""SQLite helpers — local-only DB under instance/; parameterized queries only."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, current_app, g

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name TEXT NOT NULL,
    host TEXT NOT NULL,
    ssh_user TEXT NOT NULL,
    ssh_key_path TEXT,
    ssh_password TEXT,
    ssh_port INTEGER NOT NULL DEFAULT 22,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Prefer ssh_key_path. ssh_password is optional demo fallback with residual risk
# if populated (stored as provided for the demo — avoid real production secrets).
SERVER_COLUMNS = (
    "id",
    "display_name",
    "host",
    "ssh_user",
    "ssh_key_path",
    "ssh_password",
    "ssh_port",
    "created_at",
)


def default_database_path(app: Flask) -> str:
    """Return absolute path to instance/monitoring.db (gitignored, local-only)."""
    return str(Path(app.instance_path) / "monitoring.db")


def init_app(app: Flask) -> None:
    """Configure DB path, ensure instance dir, register teardown, create schema."""
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(app.instance_path, 0o700)
    except OSError:
        pass

    app.config.setdefault("DATABASE", default_database_path(app))
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
        _restrict_db_file_permissions(app.config["DATABASE"])


def _restrict_db_file_permissions(db_path: str) -> None:
    try:
        if Path(db_path).is_file():
            os.chmod(db_path, 0o600)
    except OSError:
        pass


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


def close_db(_: BaseException | None = None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    """Create tables if missing."""
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


def list_servers() -> list[sqlite3.Row]:
    db = get_db()
    return db.execute(
        "SELECT id, display_name, host, ssh_user, ssh_key_path, ssh_password, "
        "ssh_port, created_at FROM servers ORDER BY id ASC"
    ).fetchall()


def get_server(server_id: int) -> sqlite3.Row | None:
    db = get_db()
    return db.execute(
        "SELECT id, display_name, host, ssh_user, ssh_key_path, ssh_password, "
        "ssh_port, created_at FROM servers WHERE id = ?",
        (server_id,),
    ).fetchone()


def count_servers() -> int:
    db = get_db()
    row = db.execute("SELECT COUNT(*) AS n FROM servers").fetchone()
    return int(row["n"]) if row else 0


def add_server(
    *,
    display_name: str,
    host: str,
    ssh_user: str,
    ssh_port: int = 22,
    ssh_key_path: str | None = None,
    ssh_password: str | None = None,
) -> int:
    """Insert a server row. Prefer ssh_key_path over ssh_password when both set."""
    db = get_db()
    key = (ssh_key_path or "").strip() or None
    # Demo residual risk: password may be stored if no key path is provided.
    password = None if key else ((ssh_password or "").strip() or None)
    cur = db.execute(
        "INSERT INTO servers "
        "(display_name, host, ssh_user, ssh_key_path, ssh_password, ssh_port) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            display_name.strip(),
            host.strip(),
            ssh_user.strip(),
            key,
            password,
            int(ssh_port),
        ),
    )
    db.commit()
    _restrict_db_file_permissions(current_app.config["DATABASE"])
    return int(cur.lastrowid)


def delete_server(server_id: int) -> bool:
    db = get_db()
    cur = db.execute("DELETE FROM servers WHERE id = ?", (server_id,))
    db.commit()
    return cur.rowcount > 0


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {col: row[col] for col in SERVER_COLUMNS if col in row.keys()}
