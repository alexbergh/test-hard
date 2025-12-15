"""Integration tests for Docker Compose stack."""

import subprocess
import time
from pathlib import Path

import os

import pytest
import requests


@pytest.mark.integration
@pytest.mark.requires_docker
class TestDockerComposeIntegration:
    """Test Docker Compose stack integration."""

    @pytest.fixture(scope="class")
    def docker_services(self):
        """Start Docker Compose services for testing."""
        project_root = Path(__file__).parent.parent.parent

        # Start services
        subprocess.run(["docker", "compose", "up", "-d"], cwd=project_root, check=True)

        # Wait for services to be healthy
        time.sleep(45)

        yield

        # Cleanup
        subprocess.run(["docker", "compose", "down", "-v"], cwd=project_root)

    def test_prometheus_health(self, docker_services):
        """Test Prometheus health endpoint."""
        response = requests.get("http://localhost:9090/-/healthy", timeout=5)
        assert response.status_code == 200

    def test_prometheus_targets(self, docker_services):
        """Test that Prometheus can reach its targets."""
        response = requests.get("http://localhost:9090/api/v1/targets", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "activeTargets" in data["data"]

    def test_grafana_health(self, docker_services):
        """Test Grafana health endpoint."""
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("database") == "ok"

    def test_grafana_datasource(self, docker_services):
        """Test that Grafana has Prometheus datasource configured."""
        # Grafana credentials can be overridden via env/.env in different environments.
        # Try a small set of common credentials to make local runs reliable while
        # still validating the datasource configuration.
        candidates = []

        env_user = os.getenv("GF_SECURITY_ADMIN_USER") or os.getenv("GRAFANA_ADMIN_USER")
        env_pass = os.getenv("GF_SECURITY_ADMIN_PASSWORD") or os.getenv("GRAFANA_ADMIN_PASSWORD")
        if env_user and env_pass:
            candidates.append((env_user, env_pass))

        # Defaults used in repo docs/CI templates
        candidates.append(("CHANGE_ME_ADMIN_USER", "CHANGE_ME_GENERATE_WITH_openssl_rand_base64_32"))

        # Grafana image defaults
        candidates.append(("admin", "admin"))

        response = None
        for user, password in candidates:
            response = requests.get(
                "http://localhost:3000/api/datasources",
                auth=(user, password),
                timeout=5,
            )
            if response.status_code == 200:
                break

        assert response is not None
        assert response.status_code == 200, f"Grafana /api/datasources returned {response.status_code}: {response.text}"
        datasources = response.json()
        prometheus_ds = [ds for ds in datasources if ds["type"] == "prometheus"]
        assert len(prometheus_ds) > 0

    def test_telegraf_metrics(self, docker_services):
        """Test that Telegraf exposes metrics."""
        response = requests.get("http://localhost:9091/metrics", timeout=5)
        assert response.status_code == 200
        assert "# HELP" in response.text

    def test_alertmanager_health(self, docker_services):
        """Test Alertmanager health endpoint."""
        response = requests.get("http://localhost:9093/-/healthy", timeout=5)
        assert response.status_code == 200

    def test_all_containers_running(self):
        """Test that all expected containers are running."""
        result = subprocess.run(
            ["docker", "compose", "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True,
        )

        containers = result.stdout.strip().split("\n")
        running_count = len([c for c in containers if c and '"State":"running"' in c])

        # At least monitoring services should be running
        assert running_count >= 5  # prometheus, grafana, telegraf, alertmanager, docker-proxy

    @pytest.mark.slow
    def test_prometheus_scrapes_telegraf(self, docker_services):
        """Test that Prometheus is scraping Telegraf."""
        # Wait a bit for scraping to happen
        time.sleep(30)

        response = requests.get(
            "http://localhost:9090/api/v1/query",
            params={"query": "up{job='telegraf'}"},
            timeout=5,
        )
        assert response.status_code == 200
        data = response.json()

        # Check that we have results
        assert data["status"] == "success"
        assert len(data["data"]["result"]) > 0

        # Check that telegraf is up (value should be 1)
        result = data["data"]["result"][0]
        assert float(result["value"][1]) == 1.0


@pytest.mark.integration
def test_makefile_commands():
    """Test that Makefile commands work."""
    project_root = Path(__file__).parent.parent.parent

    # Test validate command
    result = subprocess.run(["make", "validate"], cwd=project_root, capture_output=True, text=True)
    assert result.returncode == 0

    # Test test command
    result = subprocess.run(["make", "test"], cwd=project_root, capture_output=True, text=True)
    assert result.returncode == 0


@pytest.mark.integration
@pytest.mark.requires_docker
def test_scanner_images_build():
    """Test that the unified scanner Docker image can be built."""
    project_root = Path(__file__).parent.parent.parent

    result = subprocess.run(
        ["docker", "build", "-t", "ghcr.io/alexbergh/test-hard:latest", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
