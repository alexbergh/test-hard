"""Unit tests for parse_lynis_report.py"""
import json
import sys
from pathlib import Path

import pytest

# Import the module to test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from parse_lynis_report import parse_lynis_report  # noqa: E402


class TestParseLynisReport:
    """Test suite for Lynis report parser."""

    def test_parse_valid_report(self, sample_lynis_report, tmp_path, capsys):
        """Test parsing a valid Lynis report."""
        # Create temporary report file
        report_file = tmp_path / "lynis-report.json"
        with report_file.open('w') as f:
            json.dump(sample_lynis_report, f)

        # Parse the report
        parse_lynis_report(str(report_file))

        # Capture output
        captured = capsys.readouterr()
        output = captured.out

        # Verify metrics are present
        assert 'lynis_score{host="test-host"} 75' in output
        assert 'lynis_warnings_count{host="test-host"} 2' in output
        assert 'lynis_suggestions_count{host="test-host"} 3' in output
        assert 'lynis_tests_performed{host="test-host"} 3' in output
        assert 'lynis_plugins_count{host="test-host"} 2' in output

    def test_parse_missing_file(self, capsys):
        """Test handling of missing report file."""
        with pytest.raises(SystemExit) as exc_info:
            parse_lynis_report("/nonexistent/path/report.json")
        assert exc_info.value.code == 1

    def test_parse_invalid_json(self, tmp_path):
        """Test handling of invalid JSON."""
        report_file = tmp_path / "invalid.json"
        report_file.write_text("{ invalid json }")

        with pytest.raises(SystemExit) as exc_info:
            parse_lynis_report(str(report_file))
        assert exc_info.value.code == 1

    def test_parse_minimal_report(self, tmp_path, capsys):
        """Test parsing report with minimal data."""
        minimal_report = {
            "general": {
                "hostname": "minimal-host"
            }
        }

        report_file = tmp_path / "minimal.json"
        with report_file.open('w') as f:
            json.dump(minimal_report, f)

        parse_lynis_report(str(report_file))
        captured = capsys.readouterr()

        # Should handle missing fields gracefully
        assert captured.out != ""

    def test_parse_invalid_hardening_index(self, tmp_path, capsys):
        """Test handling of invalid hardening_index value."""
        report = {
            "general": {
                "hostname": "test-host",
                "hardening_index": "invalid"  # Should be int
            }
        }

        report_file = tmp_path / "invalid-index.json"
        with report_file.open('w') as f:
            json.dump(report, f)

        parse_lynis_report(str(report_file))
        captured = capsys.readouterr()

        # Should not include lynis_score if invalid
        assert 'lynis_score' not in captured.out

    def test_default_hostname(self, tmp_path, capsys):
        """Test default hostname when not provided."""
        report = {
            "general": {},
            "warnings": []
        }

        report_file = tmp_path / "no-hostname.json"
        with report_file.open('w') as f:
            json.dump(report, f)

        parse_lynis_report(str(report_file))
        captured = capsys.readouterr()

        # Should use 'unknown' as default hostname
        assert 'host="unknown"' in captured.out


@pytest.mark.parametrize("field,expected_count", [
    ("warnings", 2),
    ("suggestions", 3),
    ("tests", 3),
    ("plugins", 2),
])
def test_count_fields(sample_lynis_report, tmp_path, capsys, field, expected_count):
    """Test counting of various report fields."""
    report_file = tmp_path / f"test-{field}.json"
    with report_file.open('w') as f:
        json.dump(sample_lynis_report, f)

    parse_lynis_report(str(report_file))
    captured = capsys.readouterr()

    metric_name = f"lynis_{field}_count"
    assert f'{metric_name}{{host="test-host"}} {expected_count}' in captured.out
