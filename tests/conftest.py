"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "admin123",
            "WTF_CSRF_ENABLED": False,
            "DATABASE": str(tmp_path / "test_monitoring.db"),
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_app(tmp_path):
    """App with CSRF enabled for security assertions."""
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "ADMIN_USERNAME": "admin",
            "ADMIN_PASSWORD": "admin123",
            "WTF_CSRF_ENABLED": True,
            "DATABASE": str(tmp_path / "csrf_monitoring.db"),
        }
    )
    yield application
