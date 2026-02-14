"""Run Lynis scans on all eligible hosts and store results directly in the DB."""

import asyncio
import re
import time
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_session_context
from app.models import Host, Scan
from app.models.scan import ScanResult
from sqlalchemy import select

import docker as docker_lib

settings = get_settings()


def run_lynis_on_container(container_name: str) -> tuple[str, float]:
    """Run lynis on a container, return (output, elapsed_seconds)."""
    docker_host = settings.docker_host
    if docker_host.startswith("tcp://"):
        client = docker_lib.DockerClient(base_url=docker_host)
    else:
        client = docker_lib.from_env()

    container = client.containers.get(container_name)
    print(f"  Running lynis on {container_name}...")
    start = time.time()
    result = container.exec_run(
        cmd=["lynis", "audit", "system", "--no-colors", "--quick"],
        demux=True,
    )
    elapsed = time.time() - start
    stdout = (result.output[0] or b"").decode("utf-8", errors="replace")
    client.close()
    print(f"  Done in {elapsed:.1f}s, output={len(stdout)} bytes")
    return stdout, elapsed


def parse_lynis(output: str) -> dict:
    """Parse lynis output into score, counts, and findings."""
    score = 0
    findings = []
    warning_count = 0
    suggestion_count = 0

    # Extract hardening index
    m = re.search(r"Hardening index\s*:\s*\[(\d+)\]", output)
    if not m:
        m = re.search(r"Hardening index\s*:\s*(\d+)", output)
    if m:
        score = int(m.group(1))

    # Extract warnings count
    m = re.search(r"Warnings\s*\((\d+)\)", output)
    if m:
        warning_count = int(m.group(1))

    # Extract suggestions count
    m = re.search(r"Suggestions\s*\((\d+)\)", output)
    if m:
        suggestion_count = int(m.group(1))

    # Parse [WARNING] lines
    for line in output.splitlines():
        stripped = line.strip()

        if "[WARNING]" in line:
            title = re.sub(r"\[WARNING\]", "", line).strip().strip("-").strip()
            if title and len(title) > 5:
                findings.append(
                    {
                        "rule_id": f"LYNIS-W-{len(findings)+1:04d}",
                        "title": title[:500],
                        "severity": "high",
                        "status": "fail",
                        "category": "security",
                    }
                )

    # Parse "! text" warning lines in the Warnings section
    in_warnings = False
    in_suggestions = False
    for line in output.splitlines():
        stripped = line.strip()

        if "Warnings" in line and ":" in line:
            in_warnings = True
            in_suggestions = False
            continue
        if "Suggestions" in line and ":" in line:
            in_warnings = False
            in_suggestions = True
            continue
        if stripped.startswith("====") or stripped.startswith("Follow-up"):
            in_warnings = False
            in_suggestions = False
            continue

        if in_warnings and stripped.startswith("! "):
            title = stripped[2:].strip()
            if title and len(title) > 5:
                findings.append(
                    {
                        "rule_id": f"LYNIS-WARN-{len(findings)+1:04d}",
                        "title": title[:500],
                        "severity": "high",
                        "status": "fail",
                        "category": "hardening",
                    }
                )

        if in_suggestions and stripped.startswith("* "):
            title = stripped[2:].strip()
            if title and len(title) > 10:
                sev = "medium"
                tl = title.lower()
                if any(w in tl for w in ["password", "auth", "root", "permission", "firewall", "encrypt", "ssh"]):
                    sev = "high"
                elif any(w in tl for w in ["log", "banner", "update", "version", "ntp"]):
                    sev = "low"
                findings.append(
                    {
                        "rule_id": f"LYNIS-SUGG-{len(findings)+1:04d}",
                        "title": title[:500],
                        "severity": sev,
                        "status": "fail",
                        "category": "hardening",
                    }
                )

    return {
        "score": score,
        "warnings": warning_count,
        "suggestions": suggestion_count,
        "findings": findings,
        "passed": suggestion_count + warning_count,
        "failed": len(findings),
    }


async def main():
    async with get_session_context() as session:
        result = await session.execute(select(Host).where(Host.is_active is True))
        hosts = result.scalars().all()

        for host in hosts:
            if host.os_family not in ("debian", "ubuntu", "fedora", "centos"):
                print(f"Skipping {host.name} (os={host.os_family}) - no lynis")
                continue

            print(f"\n=== Scanning {host.name} (os={host.os_family}) ===")

            # Create scan record
            scan = Scan(
                host_id=host.id,
                user_id=1,
                scanner="lynis",
                status="running",
                started_at=datetime.now(timezone.utc),
            )
            session.add(scan)
            await session.flush()
            await session.refresh(scan)
            scan_id = scan.id
            print(f"  Created scan {scan_id}")

            try:
                output, elapsed = run_lynis_on_container(host.name)
                parsed = parse_lynis(output)

                scan.status = "completed"
                scan.completed_at = datetime.now(timezone.utc)
                scan.duration_seconds = int(elapsed)
                scan.score = parsed["score"]
                scan.passed = parsed["passed"]
                scan.failed = parsed["failed"]
                scan.warnings = parsed["warnings"]

                # Save findings
                for f in parsed["findings"]:
                    sr = ScanResult(
                        scan_id=scan_id,
                        rule_id=f["rule_id"],
                        title=f["title"],
                        severity=f["severity"],
                        status=f["status"],
                        category=f.get("category"),
                    )
                    session.add(sr)

                # Update host score
                host.last_scan_id = scan_id
                host.last_scan_score = parsed["score"]

                await session.commit()
                print(
                    f"  Result: score={parsed['score']} warnings={parsed['warnings']} suggestions={parsed['suggestions']} findings={len(parsed['findings'])}"
                )

            except Exception as e:
                scan.status = "failed"
                scan.error_message = str(e)
                scan.completed_at = datetime.now(timezone.utc)
                host.status = "online"
                await session.commit()
                print(f"  FAILED: {e}")

        print("\nAll scans complete!")


if __name__ == "__main__":
    asyncio.run(main())
