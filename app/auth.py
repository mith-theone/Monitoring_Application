"""Authentication helpers — passwords are hashed; never log plaintext."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# Generic message only — do not reveal whether username or password failed.
LOGIN_ERROR_MESSAGE = "Invalid username or password."


def hash_password(password: str) -> str:
    """Return a Werkzeug password hash (scrypt/pbkdf2). Reject empty input."""
    if not password:
        raise ValueError("Password must not be empty")
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Constant-time hash check via Werkzeug. Empty password always fails."""
    if not password or not password_hash:
        return False
    return check_password_hash(password_hash, password)


def authenticate(
    username: str,
    password: str,
    *,
    admin_username: str,
    admin_password_hash: str,
) -> bool:
    """Verify the single demo admin user against a stored hash."""
    if not username or not password:
        return False
    if username != admin_username:
        return False
    return verify_password(admin_password_hash, password)


def login_user(username: str) -> None:
    """Establish an authenticated session."""
    session.clear()
    session["user"] = username
    session.permanent = False


def logout_user() -> None:
    """Invalidate the current session."""
    session.clear()


def is_authenticated() -> bool:
    return bool(session.get("user"))


def login_required(view: Callable) -> Callable:
    """Redirect unauthenticated users to /login."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped
