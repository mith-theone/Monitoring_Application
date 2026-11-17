"""Unit tests for SQLite init and server CRUD helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app import db as db_module


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test_monitoring.db"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "admin123",
            "WTF_CSRF_ENABLED": False,
            "DATABASE": str(db_path),
        }
    )
    yield application


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield app


def test_init_db_creates_servers_table(app_ctx, tmp_path):
    db_path = Path(app_ctx.config["DATABASE"])
    assert db_path.is_file()

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='servers'"
        ).fetchall()
        assert rows == [("servers",)]
    finally:
        conn.close()


def test_add_and_list_server_prefers_key_path(app_ctx):
    server_id = db_module.add_server(
        display_name="Web-1",
        host="10.0.0.5",
        ssh_user="ubuntu",
        ssh_port=22,
        ssh_key_path="/home/demo/.ssh/id_ed25519",
        ssh_password="should-not-be-stored",
    )
    assert server_id >= 1

    servers = db_module.list_servers()
    assert len(servers) == 1
    row = servers[0]
    assert row["display_name"] == "Web-1"
    assert row["host"] == "10.0.0.5"
    assert row["ssh_user"] == "ubuntu"
    assert row["ssh_port"] == 22
    assert row["ssh_key_path"] == "/home/demo/.ssh/id_ed25519"
    # Key path wins — password not persisted when key is present
    assert row["ssh_password"] is None


def test_add_server_password_fallback_when_no_key(app_ctx):
    db_module.add_server(
        display_name="Legacy",
        host="192.168.1.10",
        ssh_user="jumpuser",
        ssh_password="demo-only",
    )
    row = db_module.list_servers()[0]
    assert row["ssh_key_path"] is None
    assert row["ssh_password"] == "demo-only"


def test_get_and_delete_server(app_ctx):
    sid = db_module.add_server(
        display_name="ToRemove",
        host="127.0.0.1",
        ssh_user="local",
        ssh_key_path="/tmp/id_rsa",
    )
    assert db_module.get_server(sid) is not None
    assert db_module.count_servers() == 1

    assert db_module.delete_server(sid) is True
    assert db_module.get_server(sid) is None
    assert db_module.count_servers() == 0
    assert db_module.delete_server(sid) is False


def test_queries_are_parameterized(app_ctx):
    """Injection-looking input is stored as data, not executed as SQL."""
    nasty_name = "x'; DROP TABLE servers;--"
    sid = db_module.add_server(
        display_name=nasty_name,
        host="evil.example",
        ssh_user="u",
        ssh_key_path="/keys/a",
    )
    row = db_module.get_server(sid)
    assert row is not None
    assert row["display_name"] == nasty_name
    assert db_module.count_servers() == 1


def test_row_to_dict(app_ctx):
    sid = db_module.add_server(
        display_name="Dict",
        host="host1",
        ssh_user="u",
        ssh_port=2222,
        ssh_key_path="/k",
    )
    data = db_module.row_to_dict(db_module.get_server(sid))
    assert data["id"] == sid
    assert data["ssh_port"] == 2222
    assert data["display_name"] == "Dict"
