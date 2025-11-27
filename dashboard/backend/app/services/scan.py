"""Scan execution service."""

import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models import Host, Scan, ScanResult
from app.schemas import ScanCreate

settings = get_settings()


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

        # Run scan in background
        asyncio.create_task(self._execute_scan(scan_id))
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

        async with get_session_context() as session:
            scan = await session.get(Scan, scan_id)
            if not scan:
                return

            host = await session.get(Host, scan.host_id)
            if not host:
                scan.status = "failed"
                scan.error_message = "Host not found"
                scan.completed_at = datetime.now(timezone.utc)
                await session.commit()
                return

            try:
                # Update host status
                host.status = "scanning"
                await session.commit()

                # Execute scanner
                if scan.scanner == "lynis":
                    result = await self._run_lynis_scan(host, scan)
                elif scan.scanner == "openscap":
                    result = await self._run_openscap_scan(host, scan)
                else:
                    result = {"success": False, "error": f"Unknown scanner: {scan.scanner}"}

                # Update scan with results
                scan.completed_at = datetime.now(timezone.utc)
                if scan.started_at:
                    scan.duration_seconds = int(
                        (scan.completed_at - scan.started_at).total_seconds()
                    )

                if result.get("success"):
                    scan.status = "completed"
                    scan.score = result.get("score", 0)
                    scan.passed = result.get("passed", 0)
                    scan.failed = result.get("failed", 0)
                    scan.warnings = result.get("warnings", 0)
                    scan.report_path = result.get("report_path")
                    scan.html_report_path = result.get("html_report_path")

                    # Update host last scan info
                    host.last_scan_id = scan.id
                    host.last_scan_score = scan.score
                else:
                    scan.status = "failed"
                    scan.error_message = result.get("error", "Unknown error")

                host.status = "online"
                await session.commit()

            except Exception as e:
                scan.status = "failed"
                scan.error_message = str(e)
                scan.completed_at = datetime.now(timezone.utc)
                host.status = "online"
                await session.commit()

    async def _run_lynis_scan(self, host: Host, scan: Scan) -> dict:
        """Run Lynis scan on host."""
        reports_dir = Path(settings.reports_dir) / "lynis"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = reports_dir / f"{host.name}_{scan.id}.log"

        try:
            if host.host_type == "container":
                # Run Lynis inside container
                cmd = [
                    "docker",
                    "exec",
                    host.name,
                    "lynis",
                    "audit",
                    "system",
                    "--quiet",
                    "--logfile",
                    "/tmp/lynis.log",
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(process.wait(), timeout=settings.scan_timeout)

                # Copy report from container
                copy_cmd = ["docker", "cp", f"{host.name}:/tmp/lynis.log", str(report_path)]
                await asyncio.create_subprocess_exec(*copy_cmd)

            # Parse results
            score, warnings, suggestions = self._parse_lynis_report(report_path)

            return {
                "success": True,
                "score": score,
                "passed": 0,
                "failed": 0,
                "warnings": warnings,
                "report_path": str(report_path),
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Scan timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _run_openscap_scan(self, host: Host, scan: Scan) -> dict:
        """Run OpenSCAP scan on host."""
        reports_dir = Path(settings.reports_dir) / "openscap"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_path = reports_dir / f"{host.name}_{scan.id}.xml"
        html_report_path = reports_dir / f"{host.name}_{scan.id}.html"

        try:
            # Determine datastream based on OS
            datastream = self._get_openscap_datastream(host.os_family)
            if not datastream:
                return {"success": False, "error": f"No datastream for OS: {host.os_family}"}

            if host.host_type == "container":
                cmd = [
                    "oscap-docker",
                    "container",
                    host.name,
                    "xccdf",
                    "eval",
                    "--profile",
                    scan.profile or "xccdf_org.ssgproject.content_profile_standard",
                    "--results",
                    str(report_path),
                    "--report",
                    str(html_report_path),
                    datastream,
                ]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(process.wait(), timeout=settings.scan_timeout)

            # Parse results
            passed, failed = self._parse_openscap_report(report_path)
            score = int((passed / (passed + failed)) * 100) if (passed + failed) > 0 else 0

            return {
                "success": True,
                "score": score,
                "passed": passed,
                "failed": failed,
                "warnings": 0,
                "report_path": str(report_path),
                "html_report_path": str(html_report_path),
            }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Scan timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def _get_openscap_datastream(os_family: str | None) -> str | None:
        """Get OpenSCAP datastream path for OS family."""
        datastreams = {
            "fedora": "/usr/share/xml/scap/ssg/content/ssg-fedora-ds.xml",
            "debian": "/usr/share/xml/scap/ssg/content/ssg-debian12-ds.xml",
            "centos": "/usr/share/xml/scap/ssg/content/ssg-centos9-ds.xml",
            "ubuntu": "/usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml",
        }
        return datastreams.get(os_family or "")

    @staticmethod
    def _parse_lynis_report(report_path: Path) -> tuple[int, int, int]:
        """Parse Lynis report and extract metrics."""
        score = 0
        warnings = 0
        suggestions = 0

        if not report_path.exists():
            return score, warnings, suggestions

        try:
            content = report_path.read_text()
            for line in content.splitlines():
                if "hardening index" in line.lower():
                    import re

                    match = re.search(r"\[(\d+)\]", line)
                    if match:
                        score = int(match.group(1))
                elif line.startswith("Warning:"):
                    warnings += 1
                elif line.startswith("Suggestion:"):
                    suggestions += 1
        except Exception:
            pass

        return score, warnings, suggestions

    @staticmethod
    def _parse_openscap_report(report_path: Path) -> tuple[int, int]:
        """Parse OpenSCAP XML report and count pass/fail."""
        passed = 0
        failed = 0

        if not report_path.exists():
            return passed, failed

        try:
            import xml.etree.ElementTree as ET

            tree = ET.parse(report_path)
            root = tree.getroot()

            ns = {"xccdf": "http://checklists.nist.gov/xccdf/1.2"}
            for result in root.findall(".//xccdf:rule-result", ns):
                status = result.findtext("xccdf:result", namespaces=ns)
                if status == "pass":
                    passed += 1
                elif status == "fail":
                    failed += 1
        except Exception:
            pass

        return passed, failed
