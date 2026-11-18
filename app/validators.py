"""Input validation for server forms."""

from __future__ import annotations

import re

# Cap for demo (~10 hosts).
MAX_SERVERS = 10

_DISPLAY_NAME_RE = re.compile(r"^[\w\s.\-]{1,64}$", re.UNICODE)
# Hostname label or IPv4 / simple IPv6-ish host string (no spaces / shell metacharacters).
_HOST_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9.:\-]+(?<!-)$"
)


def sanitize_display_name(value: str) -> str | None:
    name = (value or "").strip()
    if not name or not _DISPLAY_NAME_RE.match(name):
        return None
    return name


def validate_host(value: str) -> str | None:
    host = (value or "").strip()
    if not host or not _HOST_RE.match(host):
        return None
    if any(c in host for c in (" ", ";", "|", "&", "`", "$", "(", ")", "<", ">")):
        return None
    return host


def validate_ssh_user(value: str) -> str | None:
    user = (value or "").strip()
    if not user or len(user) > 64:
        return None
    if not re.match(r"^[A-Za-z0-9._\-]+$", user):
        return None
    return user


def validate_ssh_port(value: str | int | None) -> int | None:
    if value is None or value == "":
        return 22
    try:
        port = int(value)
    except (TypeError, ValueError):
        return None
    if 1 <= port <= 65535:
        return port
    return None


def validate_key_path(value: str | None) -> str | None:
    path = (value or "").strip()
    if not path:
        return None
    if len(path) > 512 or "\x00" in path:
        return None
    return path
