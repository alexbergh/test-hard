"""Pytest configuration and fixtures."""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))


@pytest.fixture
def project_root() -> Path:
    """Return project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def sample_lynis_report() -> Dict[str, Any]:
    """Return sample Lynis report data."""
    return {
        "general": {
            "hostname": "test-host",
            "hardening_index": 75
        },
        "warnings": [
            {"id": "W001", "message": "Test warning 1"},
            {"id": "W002", "message": "Test warning 2"}
        ],
        "suggestions": [
            {"id": "S001", "message": "Test suggestion 1"},
            {"id": "S002", "message": "Test suggestion 2"},
            {"id": "S003", "message": "Test suggestion 3"}
        ],
        "tests": [
            {"id": "T001", "result": "pass"},
            {"id": "T002", "result": "pass"},
            {"id": "T003", "result": "fail"}
        ],
        "plugins": [
            {"name": "plugin1"},
            {"name": "plugin2"}
        ]
    }


@pytest.fixture
def sample_atomic_modern_report() -> Dict[str, Any]:
    """Return sample Atomic Red Team modern format report."""
    return {
        "host": "test-host",
        "generated_at": "2024-10-27T18:00:00Z",
        "mode": "run",
        "atomics_path": "/path/to/atomics",
        "summary": {
            "passed": 3,
            "failed": 1,
            "skipped": 1,
            "error": 0,
            "unknown": 0,
            "total": 5
        },
        "scenarios": [
            {
                "id": "linux_system_discovery",
                "name": "Linux system discovery",
                "technique": "T1082",
                "technique_name": "System Information Discovery",
                "status": "passed",
                "tests": [
                    {
                        "guid": "test-guid-1",
                        "number": 1,
                        "name": "Test 1",
                        "executor": "sh",
                        "supported_platforms": ["linux"],
                        "status": "passed",
                        "return_code": 0
                    },
                    {
                        "guid": "test-guid-2",
                        "number": 2,
                        "name": "Test 2",
                        "executor": "bash",
                        "supported_platforms": ["linux"],
                        "status": "failed",
                        "return_code": 1
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_atomic_legacy_report() -> Dict[str, Any]:
    """Return sample Atomic Red Team legacy format report."""
    return {
        "tests": [
            {"id": "T1082", "passed": True},
            {"id": "T1049", "passed": False},
            {"id": "T1119", "passed": True}
        ]
    }


@pytest.fixture
def sample_openscap_arf(tmp_path: Path) -> Path:
    """Create sample OpenSCAP ARF XML file."""
    arf_content = """<?xml version="1.0" encoding="UTF-8"?>
<arf:asset-report-collection xmlns:arf="http://scap.nist.gov/schema/arf/1.1"
                             xmlns:xccdf="http://checklists.nist.gov/xccdf/1.2">
    <xccdf:TestResult>
        <xccdf:rule-result>
            <xccdf:result>pass</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>pass</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>fail</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>fail</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>fail</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>error</xccdf:result>
        </xccdf:rule-result>
        <xccdf:rule-result>
            <xccdf:result>unknown</xccdf:result>
        </xccdf:rule-result>
    </xccdf:TestResult>
</arf:asset-report-collection>
"""
    arf_file = tmp_path / "test-report.arf"
    arf_file.write_text(arf_content)
    return arf_file


@pytest.fixture
def temp_report_file(tmp_path: Path) -> Path:
    """Create temporary directory for test reports."""
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    return report_dir


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    test_env = {
        "HARDENING_RESULTS_DIR": "/tmp/test-results",
        "HARDENING_ART_STORAGE": "/tmp/art-storage",
        "ATOMIC_DRY_RUN": "true",
        "ATOMIC_TIMEOUT": "60"
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture(scope="session")
def docker_compose_file(tmp_path_factory):
    """Provide path to docker-compose file for integration tests."""
    return PROJECT_ROOT / "docker-compose.yml"


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing command-line scripts."""
    from click.testing import CliRunner
    return CliRunner()
