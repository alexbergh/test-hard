"""Unit tests for parse_atomic_red_team_result.py"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from parse_atomic_red_team_result import main, emit_modern_format, emit_legacy_format, render_metric


class TestParseAtomicRedTeam:
    """Test suite for Atomic Red Team result parser."""

    def test_parse_modern_format(self, sample_atomic_modern_report, tmp_path, capsys):
        """Test parsing modern format Atomic Red Team results."""
        result_file = tmp_path / "atomic-results.json"
        with result_file.open('w') as f:
            json.dump(sample_atomic_modern_report, f)

        main(str(result_file))
        captured = capsys.readouterr()
        output = captured.out

        # Check test result metrics
        assert 'art_test_result{' in output
        assert 'host="test-host"' in output
        assert 'technique="T1082"' in output
        assert 'status="passed"' in output or 'status="failed"' in output

        # Check scenario status
        assert 'art_scenario_status{' in output

        # Check summary metrics
        assert 'art_summary_total{' in output

    def test_parse_legacy_format(self, sample_atomic_legacy_report, tmp_path, capsys):
        """Test parsing legacy format Atomic Red Team results."""
        result_file = tmp_path / "legacy-results.json"
        with result_file.open('w') as f:
            json.dump(sample_atomic_legacy_report, f)

        main(str(result_file))
        captured = capsys.readouterr()
        output = captured.out

        assert 'art_test_result{' in output
        assert 'technique="T1082"' in output

    def test_missing_file(self, tmp_path, capsys):
        """Test handling of missing result file."""
        main(str(tmp_path / "nonexistent.json"))
        captured = capsys.readouterr()

        # Should log warning but not crash
        assert captured.err == ""  # No stderr output expected

    def test_invalid_json(self, tmp_path, capsys):
        """Test handling of invalid JSON."""
        result_file = tmp_path / "invalid.json"
        result_file.write_text("{ invalid json")

        main(str(result_file))
        # Should not crash, but won't produce metrics

    def test_unsupported_schema(self, tmp_path):
        """Test handling of unsupported result schema."""
        result_file = tmp_path / "unsupported.json"
        with result_file.open('w') as f:
            json.dump({"unknown": "schema"}, f)

        with pytest.raises(ValueError, match="Unsupported"):
            main(str(result_file))

    def test_render_metric(self):
        """Test metric rendering with proper escaping."""
        labels = {
            "host": "test-host",
            "scenario": "test scenario",
            "status": "passed"
        }
        result = render_metric("test_metric", labels, 0)

        assert "test_metric{" in result
        assert 'host="test-host"' in result
        assert 'scenario="test scenario"' in result
        assert '} 0' in result

    def test_render_metric_escaping(self):
        """Test label value escaping in metrics."""
        labels = {
            "host": "test\"host",  # Contains quote
            "path": "C:\\test\\path"  # Contains backslash
        }
        result = render_metric("test_metric", labels, 1)

        # Quotes should be escaped
        assert 'test\\"host' in result or '\\\\"' in result

    def test_emit_modern_format_direct(self, sample_atomic_modern_report, capsys):
        """Test direct call to emit_modern_format."""
        emit_modern_format("test-host", sample_atomic_modern_report)
        captured = capsys.readouterr()
        output = captured.out

        # Verify all metric types are present
        assert 'art_test_result' in output
        assert 'art_scenario_status' in output
        assert 'art_summary_total' in output

    def test_emit_legacy_format_direct(self, sample_atomic_legacy_report, capsys):
        """Test direct call to emit_legacy_format."""
        emit_legacy_format("test-host", sample_atomic_legacy_report)
        captured = capsys.readouterr()
        output = captured.out

        assert 'art_test_result' in output
        assert 'scenario="legacy"' in output


@pytest.mark.parametrize("status,expected_value", [
    ("passed", 0),
    ("failed", 1),
    ("skipped", 2),
    ("error", 3),
    ("unknown", 4),
])
def test_status_values(status, expected_value):
    """Test that status values are correctly mapped."""
    from parse_atomic_red_team_result import STATUS_TO_VALUE
    assert STATUS_TO_VALUE.get(status) == expected_value


def test_summary_metrics(sample_atomic_modern_report, tmp_path, capsys):
    """Test summary metric generation."""
    result_file = tmp_path / "summary-test.json"
    with result_file.open('w') as f:
        json.dump(sample_atomic_modern_report, f)

    main(str(result_file))
    captured = capsys.readouterr()
    output = captured.out

    # Check summary counts
    assert 'art_summary_total{host="test-host",bucket="passed"} 3' in output
    assert 'art_summary_total{host="test-host",bucket="failed"} 1' in output
    assert 'art_summary_total{host="test-host",bucket="total"} 5' in output
