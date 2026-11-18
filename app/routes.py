"""Application routes: dashboard, servers CRUD, metrics API."""

from __future__ import annotations

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from app import db as db_module
from app.auth import login_required
from app.collectors.local import collect_local_metrics
from app.collectors.ssh_metrics import collect_ssh_metrics
from app.validators import (
    MAX_SERVERS,
    sanitize_display_name,
    validate_host,
    validate_key_path,
    validate_ssh_port,
    validate_ssh_user,
)


def register_routes(app: Flask) -> None:
    @app.route("/")
    @login_required
    def dashboard():
        servers = db_module.list_servers()
        target = (request.args.get("target") or "localhost").strip()
        return render_template(
            "dashboard.html",
            servers=servers,
            selected_target=target,
        )

    @app.route("/api/metrics")
    @login_required
    def api_metrics():
        target = (request.args.get("target") or "localhost").strip()
        if target == "localhost":
            data = collect_local_metrics()
            data["target"] = "localhost"
            data["display_name"] = "localhost"
            return jsonify(data)

        if not target.isdigit():
            return jsonify({"ok": False, "error": "Unknown target", "target": target}), 400

        server = db_module.get_server(int(target))
        if server is None:
            return jsonify({"ok": False, "error": "Server not found", "target": target}), 404

        data = collect_ssh_metrics(
            host=server["host"],
            port=int(server["ssh_port"]),
            username=server["ssh_user"],
            key_path=server["ssh_key_path"],
            password=server["ssh_password"],
        )
        data["target"] = str(server["id"])
        data["display_name"] = server["display_name"]
        return jsonify(data)

    @app.route("/servers")
    @login_required
    def servers_list():
        servers = db_module.list_servers()
        # Never pass ssh_password into templates for display
        safe_rows = []
        for row in servers:
            safe_rows.append(
                {
                    "id": row["id"],
                    "display_name": row["display_name"],
                    "host": row["host"],
                    "ssh_user": row["ssh_user"],
                    "ssh_key_path": row["ssh_key_path"],
                    "ssh_port": row["ssh_port"],
                    "auth_method": "key" if row["ssh_key_path"] else ("password" if row["ssh_password"] else "none"),
                }
            )
        return render_template(
            "servers.html",
            servers=safe_rows,
            max_servers=MAX_SERVERS,
            count=len(safe_rows),
        )

    @app.route("/servers/add", methods=["GET", "POST"])
    @login_required
    def servers_add():
        if request.method == "GET":
            return render_template("server_add.html", max_servers=MAX_SERVERS)

        if db_module.count_servers() >= MAX_SERVERS:
            flash(f"Server limit reached ({MAX_SERVERS}). Remove one before adding.", "error")
            return redirect(url_for("servers_list"))

        display_name = sanitize_display_name(request.form.get("display_name", ""))
        host = validate_host(request.form.get("host", ""))
        ssh_user = validate_ssh_user(request.form.get("ssh_user", ""))
        ssh_port = validate_ssh_port(request.form.get("ssh_port", "22"))
        key_path = validate_key_path(request.form.get("ssh_key_path"))
        # Read password but never echo it back in HTML/flashes
        ssh_password = (request.form.get("ssh_password") or "").strip() or None

        if not display_name or not host or not ssh_user or ssh_port is None:
            flash("Invalid input. Check name, host, user, and port.", "error")
            return redirect(url_for("servers_add"))

        if not key_path and not ssh_password:
            flash("Provide an SSH key path or password.", "error")
            return redirect(url_for("servers_add"))

        db_module.add_server(
            display_name=display_name,
            host=host,
            ssh_user=ssh_user,
            ssh_port=ssh_port,
            ssh_key_path=key_path,
            ssh_password=ssh_password,
        )
        flash(f"Server “{display_name}” added.", "success")
        return redirect(url_for("servers_list"))

    @app.route("/servers/<int:server_id>/delete", methods=["POST"])
    @login_required
    def servers_delete(server_id: int):
        deleted = db_module.delete_server(server_id)
        if deleted:
            flash("Server removed from local config (remote host unchanged).", "success")
        else:
            flash("Server not found.", "error")
        return redirect(url_for("servers_list"))
