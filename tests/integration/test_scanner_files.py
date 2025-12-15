from pathlib import Path


def test_openscap_entrypoint_exists():
    p = Path("scanners/openscap/entrypoint-new.sh")
    assert p.exists() and p.is_file()
    content = p.read_text()
    assert "oscap" in content


def test_parse_script_exists():
    p = Path("scripts/parsing/parse_openscap_report.py")
    assert p.exists() and p.is_file()


def test_run_openscap_invokes_parser():
    p = Path("scripts/scanning/run_openscap.sh")
    assert p.exists()
    content = p.read_text()
    assert "../parsing/parse_openscap_report.py" in content


def test_run_lynis_profile_or_usecwd():
    p = Path("scripts/scanning/run_lynis.sh")
    assert p.exists()
    content = p.read_text()
    assert "--profile" in content or "--usecwd" in content


def test_lynis_metrics_generator_exists_and_invoked():
    p = Path("scripts/parsing/generate_lynis_metrics.py")
    assert p.exists() and p.is_file()
    content = Path("scripts/scanning/run_lynis.sh").read_text()
    assert "generate_lynis_metrics.py" in content


def test_dockerfile_contains_lynis_default_profile():
    p = Path("Dockerfile")
    assert p.exists()
    txt = p.read_text()
    assert "/etc/lynis/default.prf" in txt
