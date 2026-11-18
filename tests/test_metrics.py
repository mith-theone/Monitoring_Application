"""Tests for metrics API and collectors (mocked where needed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.collectors.local import collect_local_metrics
from app.collectors.ssh_metrics import collect_ssh_metrics


def _login(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})


def test_metrics_requires_login(client):
    r = client.get("/api/metrics?target=localhost", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_localhost_metrics_json(client):
    _login(client)
    with patch("app.routes.collect_local_metrics") as mock_collect:
        mock_collect.return_value = {
            "ok": True,
            "source": "localhost",
            "error": None,
            "cpu": {"percent": 12.5},
            "memory": {
                "total": 1000,
                "used": 400,
                "free": 600,
                "percent": 40.0,
                "swap_total": 0,
                "swap_used": 0,
            },
            "network": [{"interface": "eth0", "bytes_sent": 1, "bytes_recv": 2}],
            "ports": [{"port": 22, "proto": "tcp", "process": "sshd"}],
        }
        r = client.get("/api/metrics?target=localhost")
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is True
    assert data["cpu"]["percent"] == 12.5
    assert b"admin123" not in r.data


def test_dashboard_requires_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 302


def test_dashboard_ok(client):
    _login(client)
    r = client.get("/")
    assert r.status_code == 200
    assert b"CPU" in r.data
    assert b"Refresh" in r.data


def test_collect_local_metrics_shape():
    data = collect_local_metrics()
    assert data["ok"] is True
    assert "percent" in data["cpu"]
    assert "total" in data["memory"]
    assert isinstance(data["network"], list)
    assert isinstance(data["ports"], list)


def test_ssh_metrics_success_with_mock_client():
    client = MagicMock()
    outputs = {
        "grep '^cpu ' /proc/stat": "cpu  100 0 50 850 0 0 0 0 0 0\n",
        "cat /proc/meminfo": (
            "MemTotal:        2048000 kB\n"
            "MemAvailable:    1024000 kB\n"
            "SwapTotal:       1024000 kB\n"
            "SwapFree:         512000 kB\n"
        ),
        "cat /proc/net/dev": (
            "Inter-|   Receive                                                |  Transmit\n"
            " face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets\n"
            "  eth0: 1000 1 0 0 0 0 0 0 2000 1 0 0 0 0 0 0\n"
            "    lo: 10 1 0 0 0 0 0 0 10 1 0 0 0 0 0 0\n"
        ),
        "ss -tulnH 2>/dev/null || netstat -tuln 2>/dev/null || true": (
            "tcp   LISTEN 0 128 0.0.0.0:22 0.0.0.0:*\n"
        ),
    }

    def exec_command(cmd, timeout=None):
        stdout = MagicMock()
        stderr = MagicMock()
        stdout.read.return_value = outputs.get(cmd, "").encode()
        stderr.read.return_value = b""
        return MagicMock(), stdout, stderr

    client.exec_command.side_effect = exec_command
    data = collect_ssh_metrics(
        host="10.0.0.1",
        port=22,
        username="ubuntu",
        key_path="/tmp/key",
        client=client,
    )
    assert data["ok"] is True
    assert data["cpu"]["percent"] > 0
    assert data["memory"]["total"] > 0
    assert data["network"][0]["interface"] == "eth0"
    assert any(p["port"] == 22 for p in data["ports"])


def test_ssh_metrics_unreachable():
    with patch("app.collectors.ssh_metrics.paramiko.SSHClient") as mock_cls:
        inst = MagicMock()
        mock_cls.return_value = inst
        inst.connect.side_effect = OSError("down")
        data = collect_ssh_metrics(
            host="10.0.0.9",
            port=22,
            username="u",
            password="secret",
        )
    assert data["ok"] is False
    assert "unreachable" in data["error"].lower()
    # password must not appear in error
    assert "secret" not in str(data)


def test_remote_server_metrics_route(client, app):
    _login(client)
    with app.app_context():
        from app import db as db_module

        sid = db_module.add_server(
            display_name="r1",
            host="10.1.1.1",
            ssh_user="ubuntu",
            ssh_key_path="/k",
        )
    with patch("app.routes.collect_ssh_metrics") as mock_ssh:
        mock_ssh.return_value = {
            "ok": False,
            "source": "ssh",
            "error": "Host unreachable or SSH failed",
            "cpu": None,
            "memory": None,
            "network": [],
            "ports": [],
        }
        r = client.get(f"/api/metrics?target={sid}")
    assert r.status_code == 200
    assert r.get_json()["ok"] is False
