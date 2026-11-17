"""Unit tests for auth helpers and login/logout flows."""

from __future__ import annotations

from app.auth import (
    LOGIN_ERROR_MESSAGE,
    authenticate,
    hash_password,
    verify_password,
)
from app.config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME, load_config


def test_hash_password_not_plaintext():
    hashed = hash_password("admin123")
    assert hashed != "admin123"
    assert "admin123" not in hashed


def test_verify_password_success_and_failure():
    hashed = hash_password("correct-horse")
    assert verify_password(hashed, "correct-horse") is True
    assert verify_password(hashed, "wrong") is False
    assert verify_password(hashed, "") is False


def test_hash_password_rejects_empty():
    try:
        hash_password("")
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_authenticate_admin_ok():
    hashed = hash_password("admin123")
    assert (
        authenticate(
            "admin",
            "admin123",
            admin_username="admin",
            admin_password_hash=hashed,
        )
        is True
    )


def test_authenticate_wrong_password():
    hashed = hash_password("admin123")
    assert (
        authenticate(
            "admin",
            "nope",
            admin_username="admin",
            admin_password_hash=hashed,
        )
        is False
    )


def test_authenticate_missing_user():
    hashed = hash_password("admin123")
    assert (
        authenticate(
            "nobody",
            "admin123",
            admin_username="admin",
            admin_password_hash=hashed,
        )
        is False
    )


def test_authenticate_empty_credentials():
    hashed = hash_password("admin123")
    assert (
        authenticate(
            "",
            "admin123",
            admin_username="admin",
            admin_password_hash=hashed,
        )
        is False
    )
    assert (
        authenticate(
            "admin",
            "",
            admin_username="admin",
            admin_password_hash=hashed,
        )
        is False
    )


def test_dashboard_requires_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_get(client):
    response = client.get("/login")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "username" in body.lower()
    assert "password" in body.lower()
    assert "admin123" not in body


def test_login_success_sets_session_and_httponly(client, app):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")

    # Session cookie should be HttpOnly
    set_cookie = response.headers.getlist("Set-Cookie")
    joined = "; ".join(set_cookie)
    assert "HttpOnly" in joined or app.config["SESSION_COOKIE_HTTPONLY"] is True

    dash = client.get("/")
    assert dash.status_code == 200
    assert b"CPU" in dash.data
    assert b"admin123" not in dash.data


def test_login_failure_generic_message(client):
    response = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert LOGIN_ERROR_MESSAGE in body
    assert "admin123" not in body
    # Still redirected away from dashboard when not logged in
    protected = client.get("/", follow_redirects=False)
    assert protected.status_code == 302


def test_logout_clears_session(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    assert client.get("/").status_code == 200

    response = client.post("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    protected = client.get("/", follow_redirects=False)
    assert protected.status_code == 302


def test_plaintext_password_not_in_login_error_response(client):
    secret = "super-secret-demo-pass"
    # Wrong username with a distinctive password must not echo it back
    response = client.post(
        "/login",
        data={"username": "admin", "password": secret},
        follow_redirects=True,
    )
    assert secret not in response.get_data(as_text=True)


def test_config_defaults():
    cfg = load_config()
    assert cfg["ADMIN_USERNAME"] == DEFAULT_ADMIN_USERNAME
    assert cfg["ADMIN_PASSWORD"] == DEFAULT_ADMIN_PASSWORD
    assert cfg["SESSION_COOKIE_HTTPONLY"] is True
    assert cfg["SECRET_KEY"]
    assert len(cfg["SECRET_KEY"]) >= 32


def test_create_app_stores_hash_not_plaintext_password(app):
    assert "ADMIN_PASSWORD" not in app.config
    assert "ADMIN_PASSWORD_HASH" in app.config
    assert app.config["ADMIN_PASSWORD_HASH"] != "admin123"
    assert "admin123" not in app.config["ADMIN_PASSWORD_HASH"]


def test_csrf_required_when_enabled(csrf_app):
    client = csrf_app.test_client()
    response = client.post(
        "/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=False,
    )
    # Flask-WTF returns 400 when CSRF token is missing
    assert response.status_code == 400
