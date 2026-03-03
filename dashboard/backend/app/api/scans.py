"""Scan management endpoints."""

import csv
import io
import json

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse

from app.api.deps import CurrentUser, DbSession, OperatorUser
from app.schemas import ScanCreate, ScanResponse, ScanSummary
from app.services.scan import ScanService

router = APIRouter()


@router.get("", response_model=list[ScanSummary])
async def list_scans(
    session: DbSession,
    current_user: CurrentUser,
    host_id: int | None = None,
    scanner: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ScanSummary]:
    """List all scans with optional filters."""
    scan_service = ScanService(session)
    scans = await scan_service.get_all_scans(
        host_id=host_id,
        scanner=scanner,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    result = []
    for scan in scans:
        summary = ScanSummary(
            id=scan.id,
            host_id=scan.host_id,
            host_name=scan.host.name if scan.host else None,
            scanner=scan.scanner,
            status=scan.status,
            score=scan.score,
            passed=scan.passed,
            failed=scan.failed,
            warnings=scan.warnings,
            started_at=scan.started_at,
            completed_at=scan.completed_at,
            duration_seconds=scan.duration_seconds,
        )
        result.append(summary)

    return result


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    session: DbSession,
    current_user: CurrentUser,
    include_results: bool = False,
) -> ScanResponse:
    """Get scan by ID with optional detailed results."""
    scan_service = ScanService(session)
    scan = await scan_service.get_scan_by_id(scan_id, include_results=True)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    return ScanResponse.model_validate(scan)


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanResponse:
    """Create and start a new scan."""
    scan_service = ScanService(session)

    # Create scan and commit so background task can see it
    scan = await scan_service.create_scan(scan_data, user_id=current_user.id)
    await session.commit()

    from app.services.audit import log_action

    await log_action(
        session,
        "scan_started",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="scan",
        resource_id=str(scan.id),
        detail=f"scanner={scan_data.scanner} host_id={scan_data.host_id}",
    )

    # Start scan immediately
    await scan_service.start_scan(scan.id)
    await session.commit()

    # Refresh to get updated status with results eagerly loaded
    scan = await scan_service.get_scan_by_id(scan.id, include_results=True)
    return ScanResponse.model_validate(scan)


@router.post("/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanResponse:
    """Start a pending scan."""
    scan_service = ScanService(session)
    scan = await scan_service.start_scan(scan_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan not found or not in pending status",
        )

    scan = await scan_service.get_scan_by_id(scan_id, include_results=True)
    return ScanResponse.model_validate(scan)


@router.post("/{scan_id}/cancel", response_model=ScanResponse)
async def cancel_scan(
    scan_id: int,
    session: DbSession,
    current_user: OperatorUser,
) -> ScanResponse:
    """Cancel a running or pending scan."""
    scan_service = ScanService(session)
    scan = await scan_service.cancel_scan(scan_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scan not found or cannot be cancelled",
        )

    scan = await scan_service.get_scan_by_id(scan_id, include_results=True)
    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}/report")
async def get_scan_report(
    scan_id: int,
    session: DbSession,
    current_user: CurrentUser,
    format: str = "html",
) -> FileResponse:
    """Download scan report."""
    scan_service = ScanService(session)
    scan = await scan_service.get_scan_by_id(scan_id)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    if format == "html" and scan.html_report_path:
        return FileResponse(
            scan.html_report_path,
            media_type="text/html",
            filename=f"scan_{scan_id}_report.html",
        )
    elif scan.report_path:
        return FileResponse(
            scan.report_path,
            media_type="application/xml",
            filename=f"scan_{scan_id}_report.xml",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not available",
        )


@router.get("/{scan_id}/export")
async def export_scan_results(
    scan_id: int,
    session: DbSession,
    current_user: CurrentUser,
    format: str = "csv",
):
    """Export scan results as CSV or JSON."""
    scan_service = ScanService(session)
    scan = await scan_service.get_scan_by_id(scan_id, include_results=True)

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    results_data = []
    for r in scan.results or []:
        results_data.append(
            {
                "rule_id": r.rule_id,
                "title": r.title,
                "severity": r.severity,
                "status": r.status,
                "category": r.category or "",
            }
        )

    if format == "json":
        export = {
            "scan_id": scan.id,
            "scanner": scan.scanner,
            "status": scan.status,
            "score": scan.score,
            "passed": scan.passed,
            "failed": scan.failed,
            "started_at": scan.started_at.isoformat() if scan.started_at else None,
            "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
            "results": results_data,
        }
        content = json.dumps(export, indent=2, ensure_ascii=False)
        return StreamingResponse(
            io.BytesIO(content.encode("utf-8")),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_results.json"},
        )

    # Default: CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["rule_id", "title", "severity", "status", "category"])
    writer.writeheader()
    writer.writerows(results_data)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=scan_{scan_id}_results.csv"},
    )
