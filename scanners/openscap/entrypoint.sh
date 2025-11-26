set -euo pipefail
exec /usr/bin/env python3 - "$@" <<'PY'
import pathlib
import sys
PROFILE = "xccdf_org.ssgproject.content_profile_standard"
    "target-fedora": "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml",
    "target-centos": "/usr/share/xml/scap/ssg/content/ssg-centos9-ds.xml",
}

    targets_str = os.environ.get("TARGET_CONTAINERS", "").strip()
        print("No target containers provided via TARGET_CONTAINERS", file=sys.stderr)

    if not targets:
        return 1
    reports_dir = pathlib.Path("/reports/openscap")


        datastream = DATASTREAMS.get(name)
            print(f"No datastream known for {name}, skipping", file=sys.stderr)
            continue
        if not pathlib.Path(datastream).exists():
            status = 1

        report_path = reports_dir / f"{name}.html"
        print(f"[OpenSCAP] Scanning {name} using {datastream}", file=sys.stderr)
        cmd = [
            "container",
            "xccdf",
            "--profile",
            "--fetch-remote-resources",
            str(result_path),
            str(report_path),
        ]
        try:
        except subprocess.CalledProcessError:
            status = 1
    return status

    sys.exit(main())
