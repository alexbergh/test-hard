"""Prometheus custom business metrics."""

from prometheus_client import Counter, Gauge, Histogram

# Scan metrics
scans_total = Counter(
    "scans_total",
    "Total number of scans started",
    ["scanner", "status"],
)

scans_duration_seconds = Histogram(
    "scans_duration_seconds",
    "Scan execution duration in seconds",
    ["scanner"],
    buckets=[10, 30, 60, 120, 300, 600, 1200],
)

scans_in_progress = Gauge(
    "scans_in_progress",
    "Number of scans currently running",
    ["scanner"],
)

# Host metrics
active_hosts_gauge = Gauge(
    "active_hosts_total",
    "Number of active hosts",
)

# Auth metrics
auth_login_total = Counter(
    "auth_login_total",
    "Total login attempts",
    ["result"],
)

auth_register_total = Counter(
    "auth_register_total",
    "Total registration attempts",
    ["result"],
)
