"""Remote Linux metrics over SSH — fixed command allowlist only."""

from __future__ import annotations

import logging
import re
from typing import Any

import paramiko

logger = logging.getLogger(__name__)

# Demo: AutoAddPolicy with documented warning — prefer known_hosts in real ops.
SSH_CONNECT_TIMEOUT = 8
SSH_BANNER_TIMEOUT = 8

# Allowlisted remote commands only — never interpolate user input into shell.
CMD_CPU = "grep '^cpu ' /proc/stat"
CMD_MEM = "cat /proc/meminfo"
CMD_NET = "cat /proc/net/dev"
CMD_PORTS = "ss -tulnH 2>/dev/null || netstat -tuln 2>/dev/null || true"


def _unreachable(message: str = "Host unreachable or SSH failed") -> dict[str, Any]:
    return {
        "ok": False,
        "source": "ssh",
        "error": message,
        "cpu": None,
        "memory": None,
        "network": [],
        "ports": [],
    }


def collect_ssh_metrics(
    *,
    host: str,
    port: int,
    username: str,
    key_path: str | None = None,
    password: str | None = None,
    client: paramiko.SSHClient | None = None,
) -> dict[str, Any]:
    """Collect metrics via Paramiko. Never logs keys/passwords."""
    owns_client = client is None
    ssh = client or paramiko.SSHClient()
    try:
        if owns_client:
            # Demo warning: auto-accept host keys (see docs/ssh.md).
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            connect_kwargs: dict[str, Any] = {
                "hostname": host,
                "port": int(port),
                "username": username,
                "timeout": SSH_CONNECT_TIMEOUT,
                "banner_timeout": SSH_BANNER_TIMEOUT,
                "allow_agent": False,
                "look_for_keys": False,
            }
            if key_path:
                connect_kwargs["key_filename"] = key_path
            elif password:
                connect_kwargs["password"] = password
            else:
                return _unreachable("No SSH key path or password configured")
            ssh.connect(**connect_kwargs)

        cpu = _parse_cpu(_run(ssh, CMD_CPU))
        memory = _parse_mem(_run(ssh, CMD_MEM))
        network = _parse_net(_run(ssh, CMD_NET))
        ports = _parse_ports(_run(ssh, CMD_PORTS))
        return {
            "ok": True,
            "source": "ssh",
            "error": None,
            "cpu": cpu,
            "memory": memory,
            "network": network,
            "ports": ports,
        }
    except Exception as exc:  # noqa: BLE001 — map all SSH failures to generic UI error
        logger.warning("SSH metrics failed for host=%s: %s", host, type(exc).__name__)
        return _unreachable("Host unreachable or SSH failed")
    finally:
        if owns_client:
            try:
                ssh.close()
            except Exception:  # noqa: BLE001
                pass


def _run(ssh: paramiko.SSHClient, command: str) -> str:
    _stdin, stdout, stderr = ssh.exec_command(command, timeout=SSH_CONNECT_TIMEOUT)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if err and not out:
        logger.debug("remote stderr for allowlisted cmd: %s", err[:200])
    return out


def _parse_cpu(text: str) -> dict[str, Any]:
    # /proc/stat: cpu user nice system idle iowait irq softirq ...
    match = re.search(
        r"^cpu\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)",
        text,
        re.MULTILINE,
    )
    if not match:
        return {"percent": 0.0}
    user, nice, system, idle = (int(x) for x in match.groups())
    total = user + nice + system + idle
    busy = user + nice + system
    percent = (busy / total * 100.0) if total else 0.0
    return {"percent": round(percent, 1)}


def _parse_mem(text: str) -> dict[str, Any]:
    def kb(key: str) -> int:
        m = re.search(rf"^{key}:\s+(\d+)", text, re.MULTILINE)
        return int(m.group(1)) * 1024 if m else 0

    total = kb("MemTotal")
    free = kb("MemAvailable") or kb("MemFree")
    used = max(total - free, 0)
    swap_total = kb("SwapTotal")
    swap_free = kb("SwapFree")
    swap_used = max(swap_total - swap_free, 0)
    percent = (used / total * 100.0) if total else 0.0
    return {
        "total": total,
        "used": used,
        "free": free,
        "percent": round(percent, 1),
        "swap_total": swap_total,
        "swap_used": swap_used,
    }


def _parse_net(text: str) -> list[dict[str, Any]]:
    rows = []
    for line in text.splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        name = name.strip()
        if name == "lo":
            continue
        parts = rest.split()
        if len(parts) < 9:
            continue
        rows.append(
            {
                "interface": name,
                "bytes_recv": int(parts[0]),
                "bytes_sent": int(parts[8]),
            }
        )
    return rows


def _parse_ports(text: str) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # ss: Netid State Recv-Q Send-Q Local Address:Port Peer...
        parts = line.split()
        if len(parts) < 5:
            continue
        proto = parts[0].lower()
        # Prefer Local Address column (index 4 for ss), then any addr:port with digits.
        candidates = []
        if len(parts) > 4:
            candidates.append(parts[4])
        candidates.extend(parts)
        port_s = None
        for token in candidates:
            if ":" not in token:
                continue
            maybe = token.rsplit(":", 1)[-1]
            if maybe.isdigit():
                port_s = maybe
                break
        if port_s is None:
            continue
        ports.append(
            {
                "port": int(port_s),
                "proto": "tcp" if proto.startswith("tcp") else "udp",
                "process": None,
            }
        )
    # unique
    seen: set[tuple] = set()
    out = []
    for p in ports:
        key = (p["port"], p["proto"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    out.sort(key=lambda x: (x["port"], x["proto"]))
    return out[:100]
