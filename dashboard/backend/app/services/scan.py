"""Scan execution service."""

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from app.config import get_settings
from app.models import Host, Scan
from app.models.scan import ScanResult
from app.schemas import ScanCreate
from app.services.notifications import send_scan_notification
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

settings = get_settings()
logger = logging.getLogger(__name__)

# Store background task references to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


def _task_done_callback(task: asyncio.Task) -> None:
    """Remove completed task from set and log errors."""
    _background_tasks.discard(task)
    if task.cancelled():
        logger.warning("Scan task was cancelled")
    elif task.exception():
        logger.error(f"Scan task failed with error: {task.exception()}")
    else:
        logger.info("Scan task completed successfully")


class ScanService:
    """Service for scan operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_scans(
        self,
        host_id: int | None = None,
        scanner: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Scan]:
        """Get all scans with optional filters."""
        query = select(Scan).options(selectinload(Scan.host))

        if host_id:
            query = query.where(Scan.host_id == host_id)
        if scanner:
            query = query.where(Scan.scanner == scanner)
        if status:
            query = query.where(Scan.status == status)

        query = query.order_by(Scan.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_scan_by_id(self, scan_id: int, include_results: bool = False) -> Scan | None:
        """Get scan by ID."""
        query = select(Scan).where(Scan.id == scan_id)
        if include_results:
            query = query.options(selectinload(Scan.results))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create_scan(self, scan_data: ScanCreate, user_id: int | None = None) -> Scan:
        """Create a new scan job."""
        scan = Scan(
            host_id=scan_data.host_id,
            user_id=user_id,
            scanner=scan_data.scanner,
            profile=scan_data.profile,
            status="pending",
        )
        self.session.add(scan)
        await self.session.flush()
        await self.session.refresh(scan)
        return scan

    async def start_scan(self, scan_id: int) -> Scan | None:
        """Start a pending scan."""
        scan = await self.get_scan_by_id(scan_id)
        if not scan or scan.status != "pending":
            return None

        scan.status = "running"
        scan.started_at = datetime.now(timezone.utc)
        await self.session.flush()

        # Run scan in background (store ref to prevent GC)
        task = asyncio.create_task(self._execute_scan(scan_id))
        _background_tasks.add(task)
        task.add_done_callback(_task_done_callback)
        return scan

    async def cancel_scan(self, scan_id: int) -> Scan | None:
        """Cancel a running scan."""
        scan = await self.get_scan_by_id(scan_id)
        if not scan or scan.status not in ("pending", "running"):
            return None

        scan.status = "cancelled"
        scan.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return scan

    async def _execute_scan(self, scan_id: int) -> None:
        """Execute scan in background."""
        from app.database import get_session_context

        logger.info(f"Background scan task started for scan_id={scan_id}")

        async with get_session_context() as session:
            scan = await session.get(Scan, scan_id)
            if not scan:
                logger.error(f"Scan {scan_id} not found in DB")
                return

            host = await session.get(Host, scan.host_id)
            if not host:
                scan.status = "failed"
                scan.error_message = "Host not found"
                scan.completed_at = datetime.now(timezone.utc)
                await session.commit()
                logger.error(f"Host not found for scan {scan_id}")
                return

            try:
                # Update host status
                host.status = "scanning"
                await session.commit()

                logger.info(f"Executing {scan.scanner} scan on {host.name} (scan_id={scan_id})")

                # Execute scanner
                if scan.scanner == "lynis":
                    result = await self._run_lynis_scan(host, scan)
                elif scan.scanner == "openscap":
                    result = await self._run_openscap_scan(host, scan)
                elif scan.scanner == "trivy":
                    result = await self._run_trivy_scan(host, scan)
                elif scan.scanner == "atomic":
                    result = await self._run_atomic_scan(host, scan)
                else:
                    result = {"success": False, "error": f"Unknown scanner: {scan.scanner}"}

                # Update scan with results
                now = datetime.now(timezone.utc)
                scan.completed_at = now
                if scan.started_at:
                    started = scan.started_at
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    scan.duration_seconds = int((now - started).total_seconds())

                if result.get("success"):
                    scan.status = "completed"
                    scan.score = result.get("score", 0)
                    scan.passed = result.get("passed", 0)
                    scan.failed = result.get("failed", 0)
                    scan.warnings = result.get("warnings", 0)
                    scan.report_path = result.get("report_path")
                    scan.html_report_path = result.get("html_report_path")

                    # Save individual findings as ScanResult entries
                    findings = result.get("findings", [])
                    for f in findings:
                        sr = ScanResult(
                            scan_id=scan.id,
                            rule_id=f.get("rule_id", "UNKNOWN"),
                            title=f.get("title", "Unknown finding"),
                            severity=f.get("severity", "medium"),
                            status=f.get("status", "fail"),
                            category=f.get("category"),
                        )
                        session.add(sr)

                    # Update host last scan info
                    host.last_scan_id = scan.id
                    host.last_scan_score = scan.score

                    # Send success notification
                    await asyncio.to_thread(
                        send_scan_notification,
                        host.name,
                        scan.scanner,
                        "completed",
                        scan.score,
                        scan.passed,
                        scan.failed,
                    )
                else:
                    scan.status = "failed"
                    scan.error_message = result.get("error", "Unknown error")

                    # Send failure notification
                    await asyncio.to_thread(
                        send_scan_notification,
                        host.name,
                        scan.scanner,
                        "failed",
                        error_message=scan.error_message,
                    )

                host.status = "online"
                await session.commit()

            except Exception as e:
                scan.status = "failed"
                scan.error_message = str(e)
                scan.completed_at = datetime.now(timezone.utc)
                host.status = "online"
                await session.commit()

    async def _run_lynis_scan(self, host: Host, scan: Scan) -> dict:
        """Run Lynis scan on host via Docker Python SDK (non-blocking)."""
        if host.host_type != "container":
            return {"success": False, "error": "Only container scans are supported"}

        # Run the blocking Docker SDK call in a thread
        return await asyncio.to_thread(self._run_lynis_scan_sync, host.name, scan.id)

    @staticmethod
    def _run_lynis_scan_sync(host_name: str, scan_id: int) -> dict:
        """Synchronous Lynis scan execution via Docker SDK (runs in thread)."""
        import logging

        import docker as docker_lib

        logger = logging.getLogger(__name__)
        reports_dir = Path(settings.reports_dir) / "lynis"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = reports_dir / f"{host_name}_{scan_id}.log"

        try:
            docker_host = settings.docker_host
            if docker_host.startswith("tcp://"):
                client = docker_lib.DockerClient(base_url=docker_host)
            else:
                client = docker_lib.from_env()

            container = client.containers.get(host_name)

            logger.info(f"Starting Lynis scan on {host_name}")
            exec_result = container.exec_run(
                cmd=["lynis", "audit", "system", "--no-colors", "--quick"],
                demux=True,
            )

            stdout_data = exec_result.output[0] or b""
            output = stdout_data.decode("utf-8", errors="replace")

            report_path.write_text(output, encoding="utf-8")
            logger.info(f"Lynis scan on {host_name} completed, output_len={len(output)}")

            client.close()

            score, warnings, suggestions, findings = ScanService._parse_lynis_output(output)
            passed = max(0, suggestions + warnings)
            failed = warnings + suggestions

            return {
                "success": True,
                "score": score,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "report_path": str(report_path),
                "findings": findings,
            }
        except Exception as e:
            logger.error(f"Lynis scan failed on {host_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _run_openscap_scan(self, host: Host, scan: Scan) -> dict:
        """Run OpenSCAP scan on host via Docker Python SDK."""
        if host.host_type != "container":
            return {"success": False, "error": "Only container scans are supported"}
        return await asyncio.to_thread(self._run_openscap_scan_sync, host.name, host.os_family, scan.id, scan.profile)

    @staticmethod
    def _run_openscap_scan_sync(host_name: str, os_family: str | None, scan_id: int, profile: str | None) -> dict:
        """Synchronous OpenSCAP scan via Docker SDK."""
        import re
        import xml.etree.ElementTree as ET

        import docker as docker_lib

        reports_dir = Path(settings.reports_dir) / "openscap"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{host_name}_{scan_id}.xml"

        try:
            docker_host = settings.docker_host
            if docker_host.startswith("tcp://"):
                client = docker_lib.DockerClient(base_url=docker_host)
            else:
                client = docker_lib.from_env()

            container = client.containers.get(host_name)

            # Check if oscap is available
            check = container.exec_run(cmd=["sh", "-c", "command -v oscap"], demux=True)
            if check.exit_code != 0:
                client.close()
                return {
                    "success": False,
                    "error": f"oscap not installed in {host_name}. Install openscap-scanner package.",
                }

            # Determine datastream
            datastreams = {
                "fedora": "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml",
                "debian": "/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml",
                "centos": "/usr/share/xml/scap/ssg/content/ssg-cs9-ds.xml",
                "ubuntu": "/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml",
            }
            datastream = datastreams.get(os_family or "")
            if not datastream:
                client.close()
                return {"success": False, "error": f"No SCAP datastream for OS: {os_family}"}

            oscap_profile = profile or "xccdf_org.ssgproject.content_profile_standard"

            logger.info(f"Starting OpenSCAP scan on {host_name} with profile {oscap_profile}")
            exec_result = container.exec_run(
                cmd=[
                    "oscap",
                    "xccdf",
                    "eval",
                    "--profile",
                    oscap_profile,
                    "--results",
                    "/tmp/oscap-results.xml",
                    datastream,
                ],
                demux=True,
            )

            stdout_data = (exec_result.output[0] or b"").decode("utf-8", errors="replace")

            # Get XML results
            xml_result = container.exec_run(cmd=["cat", "/tmp/oscap-results.xml"], demux=True)
            xml_data = (xml_result.output[0] or b"").decode("utf-8", errors="replace")

            if xml_data.strip():
                report_path.write_text(xml_data, encoding="utf-8")

            client.close()

            # Parse results
            passed = 0
            failed = 0
            findings: list[dict] = []
            not_applicable = 0

            if xml_data.strip():
                try:
                    root = ET.fromstring(xml_data)
                    ns = {"xccdf": "http://checklists.nist.gov/xccdf/1.2"}
                    for rule_result in root.findall(".//xccdf:rule-result", ns):
                        result_el = rule_result.find("xccdf:result", ns)
                        status_text = result_el.text if result_el is not None else "error"
                        rule_id = rule_result.get("idref", "unknown")

                        if status_text == "pass":
                            passed += 1
                        elif status_text == "fail":
                            failed += 1
                            title = rule_id.replace("xccdf_org.ssgproject.content_rule_", "").replace("_", " ").title()
                            findings.append(
                                {
                                    "rule_id": rule_id[:200],
                                    "title": title[:500],
                                    "severity": "high",
                                    "status": "fail",
                                    "category": "compliance",
                                }
                            )
                        elif status_text == "notapplicable":
                            not_applicable += 1
                except ET.ParseError:
                    pass

            # Also parse stdout for pass/fail counts
            if passed == 0 and failed == 0:
                for line in stdout_data.splitlines():
                    m = re.match(r"Title\s+(.+)", line.strip())
                    if m:
                        pass  # title lines
                    if "Result" in line and "pass" in line.lower():
                        passed += 1
                    elif "Result" in line and "fail" in line.lower():
                        failed += 1

            total = passed + failed
            score = int((passed / total) * 100) if total > 0 else 0

            logger.info(f"OpenSCAP scan on {host_name} completed: score={score} passed={passed} failed={failed}")

            return {
                "success": True,
                "score": score,
                "passed": passed,
                "failed": failed,
                "warnings": not_applicable,
                "report_path": str(report_path),
                "findings": findings,
            }
        except Exception as e:
            logger.error(f"OpenSCAP scan failed on {host_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _run_trivy_scan(self, host: Host, scan: Scan) -> dict:
        """Run Trivy vulnerability scan on container image via Docker SDK."""
        if host.host_type != "container":
            return {"success": False, "error": "Only container scans are supported"}
        return await asyncio.to_thread(self._run_trivy_scan_sync, host.name, scan.id)

    @staticmethod
    def _run_trivy_scan_sync(host_name: str, scan_id: int) -> dict:
        """Synchronous Trivy scan via Docker SDK - runs trivy container."""
        import json

        import docker as docker_lib

        reports_dir = Path(settings.reports_dir) / "trivy"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{host_name}_{scan_id}.json"

        try:
            docker_host = settings.docker_host
            if docker_host.startswith("tcp://"):
                client = docker_lib.DockerClient(base_url=docker_host)
            else:
                client = docker_lib.from_env()

            # Get the target container's image name
            target = client.containers.get(host_name)
            image_name = target.attrs.get("Config", {}).get("Image", "")
            if not image_name:
                client.close()
                return {"success": False, "error": f"Cannot determine image for container {host_name}"}

            logger.info(f"Starting Trivy scan on {host_name} (image={image_name})")

            # Run trivy container to scan the image
            trivy_output = client.containers.run(
                image="aquasec/trivy:0.58.0",
                command=f"image --no-progress --format json --scanners vuln {image_name}",
                volumes={"/var/run/docker.sock": {"bind": "/var/run/docker.sock", "mode": "ro"}},
                remove=True,
                detach=False,
            )

            output = (
                trivy_output.decode("utf-8", errors="replace") if isinstance(trivy_output, bytes) else str(trivy_output)
            )
            report_path.write_text(output, encoding="utf-8")

            client.close()

            # Parse JSON results
            findings: list[dict] = []
            total_vulns = 0
            critical = 0
            high = 0
            medium = 0
            low = 0

            try:
                data = json.loads(output)
                results = data.get("Results", [])
                for result_item in results:
                    vulns = result_item.get("Vulnerabilities") or []
                    for vuln in vulns:
                        total_vulns += 1
                        sev = (vuln.get("Severity") or "UNKNOWN").lower()
                        if sev == "critical":
                            critical += 1
                        elif sev == "high":
                            high += 1
                        elif sev == "medium":
                            medium += 1
                        elif sev == "low":
                            low += 1

                        if total_vulns <= 100:
                            findings.append(
                                {
                                    "rule_id": vuln.get("VulnerabilityID", "CVE-UNKNOWN"),
                                    "title": f"{vuln.get('PkgName', '?')} {vuln.get('InstalledVersion', '')} - {vuln.get('Title', vuln.get('VulnerabilityID', ''))}",
                                    "severity": sev if sev in ("critical", "high", "medium", "low") else "info",
                                    "status": "fail",
                                    "category": "vulnerability",
                                }
                            )
            except json.JSONDecodeError:
                pass

            failed_count = critical + high
            passed_count = medium + low
            score = max(0, 100 - (critical * 10 + high * 5 + medium * 2 + low * 1))
            score = max(0, min(100, score))

            logger.info(
                f"Trivy scan on {host_name} completed: vulns={total_vulns} C={critical} H={high} M={medium} L={low}"
            )

            return {
                "success": True,
                "score": score,
                "passed": passed_count,
                "failed": failed_count,
                "warnings": medium + low,
                "report_path": str(report_path),
                "findings": findings,
            }
        except Exception as e:
            logger.error(f"Trivy scan failed on {host_name}: {e}")
            return {"success": False, "error": str(e)}

    async def _run_atomic_scan(self, host: Host, scan: Scan) -> dict:
        """Run Atomic Red Team style security tests on container."""
        if host.host_type != "container":
            return {"success": False, "error": "Only container scans are supported"}
        return await asyncio.to_thread(self._run_atomic_scan_sync, host.name, scan.id)

    @staticmethod
    def _run_atomic_scan_sync(host_name: str, scan_id: int) -> dict:
        """Synchronous Atomic Red Team security tests via Docker SDK."""
        import docker as docker_lib

        reports_dir = Path(settings.reports_dir) / "atomic"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"{host_name}_{scan_id}.log"

        # Security test definitions (MITRE ATT&CK inspired)
        tests = [
            {
                "id": "T1003.008",
                "name": "Credential Access: /etc/shadow readable",
                "cmd": "test -r /etc/shadow && echo FAIL || echo PASS",
                "expect": "PASS",
                "severity": "critical",
                "category": "credential-access",
            },
            {
                "id": "T1053.003",
                "name": "Persistence: cron jobs present",
                "cmd": "ls /etc/cron.d/ /var/spool/cron/ 2>/dev/null | head -5; echo CHECK",
                "expect": None,
                "severity": "medium",
                "category": "persistence",
            },
            {
                "id": "T1548.001",
                "name": "Privilege Escalation: SUID binaries",
                "cmd": "find / -perm -4000 -type f 2>/dev/null | head -20; echo DONE",
                "expect": None,
                "severity": "high",
                "category": "privilege-escalation",
            },
            {
                "id": "T1222.002",
                "name": "Defense Evasion: World-writable dirs",
                "cmd": "find / -maxdepth 3 -type d -perm -0002 ! -path '/proc/*' ! -path '/sys/*' 2>/dev/null | head -10; echo DONE",
                "expect": None,
                "severity": "medium",
                "category": "defense-evasion",
            },
            {
                "id": "T1552.001",
                "name": "Credential Access: Credentials in files",
                "cmd": "grep -rl 'password\\|secret\\|api_key' /etc/ 2>/dev/null | head -5; echo DONE",
                "expect": None,
                "severity": "high",
                "category": "credential-access",
            },
            {
                "id": "T1018",
                "name": "Discovery: Network configuration exposed",
                "cmd": "cat /etc/hosts 2>/dev/null | wc -l; echo DONE",
                "expect": None,
                "severity": "low",
                "category": "discovery",
            },
            {
                "id": "T1057",
                "name": "Discovery: Process listing available",
                "cmd": "ls /proc/*/cmdline 2>/dev/null | wc -l; echo DONE",
                "expect": None,
                "severity": "low",
                "category": "discovery",
            },
            {
                "id": "T1070.003",
                "name": "Defense Evasion: Bash history exists",
                "cmd": "test -f /root/.bash_history && echo FAIL || echo PASS",
                "expect": "PASS",
                "severity": "medium",
                "category": "defense-evasion",
            },
            {
                "id": "T1136.001",
                "name": "Persistence: Users with shells",
                "cmd": "grep -c '/bin/bash\\|/bin/sh' /etc/passwd; echo DONE",
                "expect": None,
                "severity": "medium",
                "category": "persistence",
            },
            {
                "id": "T1082",
                "name": "Discovery: System info disclosure",
                "cmd": "cat /etc/os-release 2>/dev/null | head -3; echo DONE",
                "expect": None,
                "severity": "low",
                "category": "discovery",
            },
            {
                "id": "T1049",
                "name": "Discovery: Network connections",
                "cmd": "cat /proc/net/tcp 2>/dev/null | wc -l; echo DONE",
                "expect": None,
                "severity": "medium",
                "category": "discovery",
            },
            {
                "id": "T1083",
                "name": "Discovery: Sensitive file access",
                "cmd": "test -r /etc/passwd && echo READABLE || echo PROTECTED",
                "expect": None,
                "severity": "low",
                "category": "discovery",
            },
            {
                "id": "T1543.002",
                "name": "Persistence: Systemd services",
                "cmd": "ls /etc/systemd/system/*.service 2>/dev/null | wc -l; echo DONE",
                "expect": None,
                "severity": "medium",
                "category": "persistence",
            },
            {
                "id": "T1059.004",
                "name": "Execution: Shell available",
                "cmd": "test -x /bin/sh && echo AVAILABLE || echo MISSING; echo DONE",
                "expect": None,
                "severity": "low",
                "category": "execution",
            },
            {
                "id": "T1574.006",
                "name": "Privilege Escalation: LD_PRELOAD hijack",
                "cmd": "test -f /etc/ld.so.preload && echo FAIL || echo PASS",
                "expect": "PASS",
                "severity": "critical",
                "category": "privilege-escalation",
            },
            {
                "id": "T1027",
                "name": "Defense Evasion: Compiled binaries in /tmp",
                "cmd": "find /tmp -type f -executable 2>/dev/null | wc -l; echo DONE",
                "expect": None,
                "severity": "high",
                "category": "defense-evasion",
            },
        ]

        try:
            docker_host = settings.docker_host
            if docker_host.startswith("tcp://"):
                client = docker_lib.DockerClient(base_url=docker_host)
            else:
                client = docker_lib.from_env()

            container = client.containers.get(host_name)
            logger.info(f"Starting Atomic Red Team tests on {host_name} ({len(tests)} tests)")

            findings: list[dict] = []
            passed = 0
            failed = 0
            report_lines: list[str] = []
            report_lines.append(f"Atomic Red Team Security Tests - {host_name}")
            report_lines.append("=" * 60)

            for test in tests:
                try:
                    exec_result = container.exec_run(
                        cmd=["sh", "-c", test["cmd"]],
                        demux=True,
                    )
                    stdout = (exec_result.output[0] or b"").decode("utf-8", errors="replace").strip()
                    output_lines = stdout.splitlines()

                    # Determine pass/fail
                    test_passed = True
                    if test["expect"] == "PASS":
                        test_passed = any("PASS" in line for line in output_lines)
                    elif test["expect"] == "FAIL":
                        test_passed = any("FAIL" in line for line in output_lines)
                    else:
                        # Count-based: if output has numbers > 0, it means something was found
                        for line in output_lines:
                            if line.strip().isdigit() and int(line.strip()) > 0:
                                test_passed = False
                                break

                    status = "pass" if test_passed else "fail"
                    if test_passed:
                        passed += 1
                    else:
                        failed += 1

                    report_lines.append(f"\n[{test['id']}] {test['name']}")
                    report_lines.append(f"  Status: {status.upper()}")
                    report_lines.append(f"  Output: {stdout[:200]}")

                    if not test_passed:
                        findings.append(
                            {
                                "rule_id": test["id"],
                                "title": test["name"],
                                "severity": test["severity"],
                                "status": "fail",
                                "category": test["category"],
                            }
                        )

                except Exception as e:
                    report_lines.append(f"\n[{test['id']}] {test['name']} - ERROR: {e}")
                    failed += 1
                    findings.append(
                        {
                            "rule_id": test["id"],
                            "title": f"{test['name']} (error)",
                            "severity": test["severity"],
                            "status": "fail",
                            "category": test["category"],
                        }
                    )

            client.close()

            report_content = "\n".join(report_lines)
            report_path.write_text(report_content, encoding="utf-8")

            total = passed + failed
            score = int((passed / total) * 100) if total > 0 else 0

            logger.info(
                f"Atomic Red Team tests on {host_name} completed: passed={passed} failed={failed} score={score}"
            )

            return {
                "success": True,
                "score": score,
                "passed": passed,
                "failed": failed,
                "warnings": 0,
                "report_path": str(report_path),
                "findings": findings,
            }
        except Exception as e:
            logger.error(f"Atomic Red Team scan failed on {host_name}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _parse_lynis_output(output: str) -> tuple[int, int, int, list[dict]]:
        """Parse Lynis stdout output and extract score, warnings, suggestions, and findings."""
        import re

        score = 0
        warnings = 0
        suggestions = 0
        findings: list[dict] = []

        lines = output.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]

            # Extract hardening index score
            if "hardening index" in line.lower() or "hardening_index" in line.lower():
                match = re.search(r"(\d+)", line)
                if match:
                    score = int(match.group(1))

            # Parse warnings
            elif line.strip().startswith("! ") or "warning" in line.lower() and "[" in line:
                warnings += 1
                # Try to extract finding details
                title = line.strip().lstrip("! ").strip()
                if title:
                    findings.append(
                        {
                            "rule_id": f"LYNIS-WARN-{warnings:04d}",
                            "title": title[:500],
                            "severity": "high",
                            "status": "fail",
                            "category": "hardening",
                        }
                    )

            # Parse suggestions
            elif (
                line.strip().startswith("- ")
                and i > 0
                and (
                    "suggestion" in lines[max(0, i - 5) : i + 1].__repr__().lower()
                    or any(
                        c in line
                        for c in ["Consider", "Enable", "Disable", "Configure", "Install", "Set ", "Add ", "Remove"]
                    )
                )
            ):
                suggestions += 1
                title = line.strip().lstrip("- ").strip()
                if title and len(title) > 10:
                    # Determine severity from context
                    sev = "medium"
                    title_lower = title.lower()
                    if any(w in title_lower for w in ["password", "auth", "root", "permission", "firewall", "encrypt"]):
                        sev = "high"
                    elif any(w in title_lower for w in ["log", "banner", "update", "version"]):
                        sev = "low"

                    findings.append(
                        {
                            "rule_id": f"LYNIS-SUGG-{suggestions:04d}",
                            "title": title[:500],
                            "severity": sev,
                            "status": "fail",
                            "category": "hardening",
                        }
                    )

            # Parse test results like [WARNING], [OK], [FOUND], etc.
            if "[WARNING]" in line:
                warnings += 1
                title = re.sub(r"\[WARNING\]", "", line).strip().strip("-").strip()
                if title and len(title) > 5 and not any(f["title"] == title[:500] for f in findings):
                    findings.append(
                        {
                            "rule_id": f"LYNIS-W-{warnings:04d}",
                            "title": title[:500],
                            "severity": "high",
                            "status": "fail",
                            "category": "security",
                        }
                    )

            i += 1

        # If score is still 0 but we have output, try harder
        if score == 0 and output:
            match = re.search(r"Hardening index\s*:\s*(\d+)", output, re.IGNORECASE)
            if match:
                score = int(match.group(1))
            else:
                # Try to find any number near "index" or "score"
                match = re.search(
                    r"(\d{1,3})\s*$", output[output.lower().rfind("harden") :] if "harden" in output.lower() else ""
                )
                if match:
                    score = int(match.group(1))

        return score, warnings, suggestions, findings
