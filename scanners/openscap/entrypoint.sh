#!/usr/bin/env bash
set -euo pipefail

exec /usr/bin/env python3 - "$@" <<'PY'
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


def main() -> int:
    targets_str = os.environ.get("TARGET_CONTAINERS", "").strip()
    if not targets_str:
        print("No target containers provided via TARGET_CONTAINERS", file=sys.stderr)
        return 1

    targets = targets_str.split()
    if not targets:
        print("No target containers provided via TARGET_CONTAINERS", file=sys.stderr)
        return 1

    reports_dir = pathlib.Path("/reports/openscap")
    reports_dir.mkdir(parents=True, exist_ok=True)

    status = 0

    for name in targets:
        datastream = DATASTREAMS.get(name)
        if datastream is None:
            print(f"No datastream known for {name}, skipping", file=sys.stderr)
            status = 1
            continue

        if not pathlib.Path(datastream).exists():
            print(f"Datastream {datastream} not found for {name}, skipping", file=sys.stderr)
            status = 1
            continue

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
            status = 1

    return status


if __name__ == "__main__":
    sys.exit(main())
PY
