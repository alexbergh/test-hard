"""Regenerate all Trivy .prom metric files to match the format Telegraf expects.

The correct format uses separate metrics per severity:
  trivy_vulnerabilities_critical{image="..."} N
  trivy_vulnerabilities_high{image="..."} N
  trivy_vulnerabilities_total{image="..."} N

Telegraf with name_override="trivy" turns these into:
  trivy_trivy_vulnerabilities_critical{image="..."} N
"""

import glob
import json
import os

REPORTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports", "trivy")


def main():
    json_files = glob.glob(os.path.join(REPORTS_DIR, "*.vuln.json"))
    print(f"Found {len(json_files)} JSON reports in {REPORTS_DIR}")

    for json_file in sorted(json_files):
        base = os.path.basename(json_file).replace(".vuln.json", "")
        prom_file = os.path.join(REPORTS_DIR, f"{base}_metrics.prom")

        with open(json_file) as f:
            data = json.load(f)

        image = data.get("ArtifactName", base)

        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        total_packages = 0
        for result in data.get("Results", []):
            total_packages += len(result.get("Packages") or [])
            for v in result.get("Vulnerabilities") or []:
                sev = v.get("Severity", "UNKNOWN").upper()
                if sev in counts:
                    counts[sev] += 1
        total = sum(counts.values())

        safe_image = image.replace('"', '\\"')
        lines = [
            "# HELP trivy_vulnerabilities_total Total vulnerabilities",
            "# TYPE trivy_vulnerabilities_total gauge",
            f'trivy_vulnerabilities_total{{image="{safe_image}"}} {total}',
            "# HELP trivy_vulnerabilities_critical Critical vulnerabilities",
            "# TYPE trivy_vulnerabilities_critical gauge",
            f'trivy_vulnerabilities_critical{{image="{safe_image}"}} {counts["CRITICAL"]}',
            "# HELP trivy_vulnerabilities_high High vulnerabilities",
            "# TYPE trivy_vulnerabilities_high gauge",
            f'trivy_vulnerabilities_high{{image="{safe_image}"}} {counts["HIGH"]}',
            "# HELP trivy_vulnerabilities_medium Medium vulnerabilities",
            "# TYPE trivy_vulnerabilities_medium gauge",
            f'trivy_vulnerabilities_medium{{image="{safe_image}"}} {counts["MEDIUM"]}',
            "# HELP trivy_vulnerabilities_low Low vulnerabilities",
            "# TYPE trivy_vulnerabilities_low gauge",
            f'trivy_vulnerabilities_low{{image="{safe_image}"}} {counts["LOW"]}',
            "# HELP trivy_packages_total Total packages",
            "# TYPE trivy_packages_total gauge",
            f'trivy_packages_total{{image="{safe_image}"}} {total_packages}',
        ]

        with open(prom_file, "wb") as f:
            f.write(("\n".join(lines) + "\n").encode())

        print(
            f"  {image}: C={counts['CRITICAL']} H={counts['HIGH']} M={counts['MEDIUM']} L={counts['LOW']} total={total}"
        )

    print(f"\nDone. Regenerated {len(json_files)} .prom files.")
    print("Telegraf will pick up on next interval (60s).")


if __name__ == "__main__":
    main()
