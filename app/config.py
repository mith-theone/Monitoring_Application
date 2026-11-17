"""Application configuration from environment (demo defaults allowed)."""

from __future__ import annotations

import os
import secrets


# Demo-only defaults — change via env for anything beyond local demo.
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def load_config() -> dict:
    """Load Flask config values from environment with demo fallbacks.

    SECRET_KEY is random per process if unset (sessions reset on restart).
    Never commit real secrets; use env vars instead of hard-coding production values.
    """
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "ADMIN_USERNAME": os.environ.get("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME),
        # Plaintext is only used once at startup to seed a hash; not kept for auth checks.
        "ADMIN_PASSWORD": os.environ.get("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "WTF_CSRF_ENABLED": True,
    }
