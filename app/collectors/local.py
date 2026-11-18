"""Localhost metrics via psutil — read-only, no shell=True."""

from __future__ import annotations

from typing import Any

import psutil


def collect_local_metrics() -> dict[str, Any]:
    """Return CPU, memory, network, and listening ports for this host."""
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    net_io = psutil.net_io_counters(pernic=True)
    network = [
        {
            "interface": name,
            "bytes_sent": int(stats.bytes_sent),
            "bytes_recv": int(stats.bytes_recv),
        }
        for name, stats in sorted(net_io.items())
        if name != "lo"
    ]

    ports: list[dict[str, Any]] = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != psutil.CONN_LISTEN:
                continue
            if not conn.laddr:
                continue
            proc_name = None
            if conn.pid:
                try:
                    proc_name = psutil.Process(conn.pid).name()
                except (psutil.Error, ProcessLookupError):
                    proc_name = None
            ports.append(
                {
                    "port": int(conn.laddr.port),
                    "proto": "tcp" if conn.type == 1 else "udp",
                    "process": proc_name,
                }
            )
    except (psutil.Error, PermissionError):
        ports = []

    # Deduplicate listen entries
    seen: set[tuple] = set()
    unique_ports = []
    for p in ports:
        key = (p["port"], p["proto"], p["process"])
        if key in seen:
            continue
        seen.add(key)
        unique_ports.append(p)
    unique_ports.sort(key=lambda x: (x["port"], x["proto"]))

    return {
        "ok": True,
        "source": "localhost",
        "error": None,
        "cpu": {"percent": float(cpu_percent)},
        "memory": {
            "total": int(mem.total),
            "used": int(mem.used),
            "free": int(mem.available),
            "percent": float(mem.percent),
            "swap_total": int(swap.total),
            "swap_used": int(swap.used),
        },
        "network": network,
        "ports": unique_ports[:100],
    }
