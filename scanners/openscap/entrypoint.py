#!/usr/bin/env python3
import os
import pathlib
import subprocess
import sys

PROFILE = "xccdf_org.ssgproject.content_profile_standard"
DATASTREAMS = {
    "target-fedora": "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml",
    "target-debian": "/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml",
    "target-centos": "/usr/share/xml/scap/ssg/content/ssg-centos9-ds.xml",
    "target-ubuntu": "/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml",
}


def collect_targets() -> list[str]:
    targets_str = os.environ.get("TARGET_CONTAINERS", "").strip()
    if not targets_str:
        print("No target containers provided via TARGET_CONTAINERS", file=sys.stderr)
        return []

    targets = [item for item in targets_str.split() if item]
    if not targets:
        print("No target containers provided via TARGET_CONTAINERS", file=sys.stderr)
        return []

    return targets


def ensure_reports_dir() -> pathlib.Path:
    reports_dir = pathlib.Path("/reports/openscap")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def scan_target(name: str, reports_dir: pathlib.Path) -> bool:
    datastream = DATASTREAMS.get(name)
    if datastream is None:
        print(f"No datastream known for {name}, skipping", file=sys.stderr)
        return False

    if not pathlib.Path(datastream).exists():
        print(f"Datastream {datastream} not found for {name}, skipping", file=sys.stderr)
        return False

    result_path = reports_dir / f"{name}.xml"
    report_path = reports_dir / f"{name}.html"

    print(f"[OpenSCAP] Scanning {name} using {datastream}", file=sys.stderr)

    cmd = [
        "oscap-docker",
        "container",
        name,
        "xccdf",
        "eval",
        "--profile",
        PROFILE,
        "--fetch-remote-resources",
        "--results",
        str(result_path),
        "--report",
        str(report_path),
        datastream,
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print(f"OpenSCAP scan failed for {name}", file=sys.stderr)
        return False

    return True


def main() -> int:
    targets = collect_targets()
    if not targets:
        return 1

    reports_dir = ensure_reports_dir()

    status = 0
    for name in targets:
        if not scan_target(name, reports_dir):
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
