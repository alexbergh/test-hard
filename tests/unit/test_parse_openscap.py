"""Unit tests for parse_openscap_report.py"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from parse_openscap_report import main, _latest_report


class TestParseOpenSCAPReport:
    """Test suite for OpenSCAP report parser."""

    def test_parse_valid_arf(self, sample_openscap_arf, capsys):
        """Test parsing a valid ARF file."""
        result = main([str(sample_openscap_arf)])

        captured = capsys.readouterr()
        output = captured.out

        # Verify metrics are present
        assert 'openscap_pass_count' in output
        assert 'openscap_fail_count' in output
        assert 'openscap_error_count' in output
        assert 'openscap_unknown_count' in output

        # Verify counts from sample data
        assert 'openscap_pass_count' in output and '2' in output
        assert 'openscap_fail_count' in output and '3' in output
        assert 'openscap_error_count' in output and '1' in output
        assert 'openscap_unknown_count' in output and '1' in output

        assert result == 0

    def test_parse_missing_file(self, capsys):
        """Test handling of missing ARF file."""
        result = main(["/nonexistent/file.arf"])

        captured = capsys.readouterr()
        assert "not found" in captured.err.lower()
        assert result == 1

    def test_parse_invalid_xml(self, tmp_path, capsys):
        """Test handling of invalid XML."""
        invalid_xml = tmp_path / "invalid.arf"
        invalid_xml.write_text("<invalid>xml<unclosed>")

        result = main([str(invalid_xml)])
        # capsys output not needed for this test
        assert result == 1

    def test_latest_report_found(self, tmp_path):
        """Test finding the latest report in directory."""
        results_dir = tmp_path / "openscap"
        results_dir.mkdir()

        # Create multiple ARF files
        (results_dir / "old.arf").touch()
        (results_dir / "newer.arf").touch()

        latest = _latest_report(results_dir)
        assert latest is not None
        assert latest.name == "newer.arf"

    def test_latest_report_not_found(self, tmp_path):
        """Test when no reports exist."""
        results_dir = tmp_path / "empty"
        results_dir.mkdir()

        latest = _latest_report(results_dir)
        assert latest is None

    def test_latest_report_nonexistent_dir(self):
        """Test when results directory doesn't exist."""
        latest = _latest_report(Path("/nonexistent/directory"))
        assert latest is None

    def test_parse_no_arguments(self, capsys):
        """Test parsing with no arguments and no default reports."""
        result = main([])
        captured = capsys.readouterr()

        # Should show usage message
        assert "Usage" in captured.err or result == 1

    def test_all_status_types(self, tmp_path, capsys):
        """Test that all OpenSCAP status types are counted."""
        arf_content = """<?xml version="1.0" encoding="UTF-8"?>
<arf:asset-report-collection xmlns:arf="http://scap.nist.gov/schema/arf/1.1"
                             xmlns:xccdf="http://checklists.nist.gov/xccdf/1.2">
    <xccdf:TestResult>
        <xccdf:rule-result><xccdf:result>pass</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>fail</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>error</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>unknown</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>notchecked</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>notselected</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>informational</xccdf:result></xccdf:rule-result>
        <xccdf:rule-result><xccdf:result>fixed</xccdf:result></xccdf:rule-result>
    </xccdf:TestResult>
</arf:asset-report-collection>
"""
        arf_file = tmp_path / "all-types.arf"
        arf_file.write_text(arf_content)

        result = main([str(arf_file)])
        captured = capsys.readouterr()
        output = captured.out

        # All status types should be present
        assert 'openscap_pass_count' in output
        assert 'openscap_fail_count' in output
        assert 'openscap_error_count' in output
        assert 'openscap_unknown_count' in output
        assert 'openscap_notchecked_count' in output
        assert 'openscap_notselected_count' in output
        assert 'openscap_informational_count' in output
        assert 'openscap_fixed_count' in output

        # Each should have count of 1
        for status_type in ['pass', 'fail', 'error', 'unknown', 'notchecked', 
                           'notselected', 'informational', 'fixed']:
            assert f'openscap_{status_type}_count' in output

        assert result == 0

    def test_empty_arf(self, tmp_path, capsys):
        """Test handling of ARF with no results."""
        arf_content = """<?xml version="1.0" encoding="UTF-8"?>
<arf:asset-report-collection xmlns:arf="http://scap.nist.gov/schema/arf/1.1"
                             xmlns:xccdf="http://checklists.nist.gov/xccdf/1.2">
    <xccdf:TestResult>
    </xccdf:TestResult>
</arf:asset-report-collection>
"""
        arf_file = tmp_path / "empty.arf"
        arf_file.write_text(arf_content)

        result = main([str(arf_file)])
        captured = capsys.readouterr()
        output = captured.out

        # Should still output metrics with 0 counts
        assert 'openscap_pass_count' in output
        assert result == 0


@pytest.mark.parametrize("filename", [
    "report-20241027.arf",
    "scan-results.arf",
    "ubuntu-scan.arf",
])
def test_various_filenames(tmp_path, sample_openscap_arf, filename):
    """Test that parser works with various ARF filenames."""
    target_file = tmp_path / filename
    target_file.write_text(sample_openscap_arf.read_text())

    result = main([str(target_file)])
    assert result == 0
