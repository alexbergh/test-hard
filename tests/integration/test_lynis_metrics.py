import subprocess


def test_generate_lynis_metrics(tmp_path):
    report = tmp_path / "host-1.txt"
    report.write_text("Hardening index: 80\nWarnings: 3\nSuggestion: x\n")

    res = subprocess.run(["python3", "scripts/parsing/generate_lynis_metrics.py", str(report)], check=False)
    assert res.returncode == 0
    m = report.with_name("host-1_metrics.prom")
    assert m.exists()
    txt = m.read_text()
    assert "lynis_score" in txt
