import subprocess

SAMPLE_ARF = """<?xml version="1.0"?>
<arf:arf xmlns:arf="http://scap.nist.gov/schema/arf/1.1" xmlns:xccdf="http://checklists.nist.gov/xccdf/1.2">
  <xccdf:rule-result>
    <xccdf:result>pass</xccdf:result>
  </xccdf:rule-result>
  <xccdf:rule-result>
    <xccdf:result>fail</xccdf:result>
  </xccdf:rule-result>
</arf:arf>
"""


def test_parse_openscap_writes_metrics(tmp_path):
    arf = tmp_path / "test.arf"
    arf.write_text(SAMPLE_ARF)

    # Run parser
    res = subprocess.run(["python3", "scripts/parsing/parse_openscap_report.py", str(arf)], check=False)
    assert res.returncode == 0

    metrics = arf.with_name("test_metrics.prom")
    assert metrics.exists()
    txt = metrics.read_text()
    assert "openscap_score" in txt
    assert "openscap_pass_count" in txt
    assert "openscap_fail_count" in txt
