"""Unit tests for Prometheus custom business metrics."""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent.parent / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.metrics import (
    active_hosts_gauge,
    auth_login_total,
    auth_register_total,
    scans_duration_seconds,
    scans_in_progress,
    scans_total,
)


class TestMetricDefinitions:
    """Verify that all custom metrics are properly defined."""

    def test_scans_total_counter(self):
        assert "scans" in scans_total._name
        assert "scanner" in scans_total._labelnames
        assert "status" in scans_total._labelnames

    def test_scans_duration_histogram(self):
        assert scans_duration_seconds._name == "scans_duration_seconds"
        assert "scanner" in scans_duration_seconds._labelnames

    def test_scans_in_progress_gauge(self):
        assert scans_in_progress._name == "scans_in_progress"
        assert "scanner" in scans_in_progress._labelnames

    def test_active_hosts_gauge(self):
        assert active_hosts_gauge._name == "active_hosts_total"

    def test_auth_login_counter(self):
        assert "auth_login" in auth_login_total._name
        assert "result" in auth_login_total._labelnames

    def test_auth_register_counter(self):
        assert "auth_register" in auth_register_total._name
        assert "result" in auth_register_total._labelnames

    def test_scans_total_can_increment(self):
        scans_total.labels(scanner="lynis", status="completed").inc()
        # No exception = success

    def test_scans_in_progress_can_inc_dec(self):
        scans_in_progress.labels(scanner="trivy").inc()
        scans_in_progress.labels(scanner="trivy").dec()

    def test_scans_duration_can_observe(self):
        scans_duration_seconds.labels(scanner="openscap").observe(42.5)

    def test_auth_login_can_increment(self):
        auth_login_total.labels(result="success").inc()
        auth_login_total.labels(result="failed").inc()
