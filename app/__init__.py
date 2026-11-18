"""Demo Linux server monitoring application package."""

from __future__ import annotations

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf import CSRFProtect

from app import db as db_module
from app.auth import (
    LOGIN_ERROR_MESSAGE,
    authenticate,
    hash_password,
    is_authenticated,
    login_user,
    logout_user,
)
from app.config import load_config
from app.routes import register_routes

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory for the local demo."""
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config.from_mapping(load_config())
    if test_config:
        app.config.update(test_config)

    # Seed single admin from env/demo password — keep hash only for auth checks.
    plain_password = app.config.pop("ADMIN_PASSWORD", "")
    app.config["ADMIN_PASSWORD_HASH"] = hash_password(plain_password)

    db_module.init_app(app)
    csrf.init_app(app)

    @app.context_processor
    def inject_auth_helpers():
        return {"is_authenticated": is_authenticated}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if is_authenticated():
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            ok = authenticate(
                username,
                password,
                admin_username=app.config["ADMIN_USERNAME"],
                admin_password_hash=app.config["ADMIN_PASSWORD_HASH"],
            )
            if ok:
                login_user(username)
                next_url = request.args.get("next") or url_for("dashboard")
                if not next_url.startswith("/"):
                    next_url = url_for("dashboard")
                return redirect(next_url)
            flash(LOGIN_ERROR_MESSAGE, "error")

        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        logout_user()
        return redirect(url_for("login"))

    register_routes(app)
    return app
