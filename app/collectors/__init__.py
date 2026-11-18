"""Metric collectors (local + SSH)."""

from app.collectors.local import collect_local_metrics
from app.collectors.ssh_metrics import collect_ssh_metrics

__all__ = ["collect_local_metrics", "collect_ssh_metrics"]
