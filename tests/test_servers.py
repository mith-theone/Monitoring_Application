"""Tests for server list/add/remove routes and authz."""

from __future__ import annotations

from app.validators import MAX_SERVERS


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )


def test_servers_list_requires_login(client):
    r = client.get("/servers", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_servers_list_ok_when_authenticated(client):
    _login(client)
    r = client.get("/servers")
    assert r.status_code == 200
    assert b"Servers" in r.data
    assert b"admin123" not in r.data


def test_add_server_and_list(client):
    _login(client)
    r = client.post(
        "/servers/add",
        data={
            "display_name": "web1",
            "host": "10.0.0.8",
            "ssh_user": "ubuntu",
            "ssh_port": "22",
            "ssh_key_path": "/home/demo/.ssh/id_ed25519",
            "ssh_password": "should-not-echo",
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    body = r.get_data(as_text=True)
    assert "web1" in body
    assert "10.0.0.8" in body
    assert "should-not-echo" not in body


def test_add_server_unauthenticated_fails(client):
    r = client.post(
        "/servers/add",
        data={
            "display_name": "x",
            "host": "1.2.3.4",
            "ssh_user": "u",
            "ssh_key_path": "/k",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_delete_requires_post_and_auth(client):
    _login(client)
    client.post(
        "/servers/add",
        data={
            "display_name": "tmp",
            "host": "192.168.0.2",
            "ssh_user": "u",
            "ssh_key_path": "/k",
        },
    )
    # GET delete must not be available
    r = client.get("/servers/1/delete", follow_redirects=False)
    assert r.status_code in (404, 405)

    client2 = client.application.test_client()
    r2 = client2.post("/servers/1/delete", follow_redirects=False)
    assert r2.status_code == 302
    assert "/login" in r2.headers["Location"]


def test_delete_server(client):
    _login(client)
    client.post(
        "/servers/add",
        data={
            "display_name": "gone",
            "host": "192.168.0.3",
            "ssh_user": "u",
            "ssh_key_path": "/k",
        },
    )
    r = client.post("/servers/1/delete", follow_redirects=True)
    assert r.status_code == 200
    assert b"gone" not in r.data or b"removed" in r.data.lower()


def test_over_limit_rejected(client, app):
    _login(client)
    with app.app_context():
        from app import db as db_module

        for i in range(MAX_SERVERS):
            db_module.add_server(
                display_name=f"s{i}",
                host=f"10.0.0.{i + 1}",
                ssh_user="u",
                ssh_key_path="/k",
            )
    r = client.post(
        "/servers/add",
        data={
            "display_name": "overflow",
            "host": "10.9.9.9",
            "ssh_user": "u",
            "ssh_key_path": "/k",
        },
        follow_redirects=True,
    )
    body = r.get_data(as_text=True)
    assert "limit" in body.lower()
    assert "overflow" not in body or "limit reached" in body.lower()
