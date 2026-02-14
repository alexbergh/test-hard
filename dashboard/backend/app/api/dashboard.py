"""Dashboard aggregation endpoints."""

import socket
from datetime import datetime, timedelta, timezone

from app.api.deps import CurrentUser, DbSession
from app.models import Host, Scan, ScanSchedule
from app.models.scan import ScanResult
from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    session: DbSession,
    current_user: CurrentUser,
    days: float = 30,
    hours: int | None = None,
) -> dict:
    """Get aggregated dashboard statistics."""

    # --- Host stats ---
    host_query = select(Host).where(Host.is_active == True)  # noqa: E712
    host_result = await session.execute(host_query)
    hosts = host_result.scalars().all()

    total_hosts = len(hosts)
    online_hosts = sum(1 for h in hosts if h.status == "online")
    offline_hosts = sum(1 for h in hosts if h.status == "offline")
    scanning_hosts = sum(1 for h in hosts if h.status == "scanning")

    # Host scores for compliance overview
    host_scores = []
    for h in hosts:
        host_scores.append(
            {
                "id": h.id,
                "name": h.display_name or h.name,
                "status": h.status,
                "os_family": h.os_family,
                "host_type": h.host_type,
                "score": h.last_scan_score,
                "tags": h.tags or [],
            }
        )

    # Score distribution buckets
    scores = [h.last_scan_score for h in hosts if h.last_scan_score is not None]
    score_distribution = {
        "critical": sum(1 for s in scores if s < 40),
        "low": sum(1 for s in scores if 40 <= s < 60),
        "medium": sum(1 for s in scores if 60 <= s < 80),
        "good": sum(1 for s in scores if 80 <= s < 95),
        "excellent": sum(1 for s in scores if s >= 95),
    }

    avg_score = round(sum(scores) / len(scores)) if scores else 0

    # --- Scan stats ---
    if hours is not None:
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=days)

    scan_count_query = select(func.count(Scan.id)).where(Scan.created_at >= since)
    scan_count_result = await session.execute(scan_count_query)
    total_scans = scan_count_result.scalar() or 0

    # Scans by status
    scan_status_query = select(Scan.status, func.count(Scan.id)).where(Scan.created_at >= since).group_by(Scan.status)
    scan_status_result = await session.execute(scan_status_query)
    scans_by_status = dict(scan_status_result.all())

    # Scans by scanner
    scan_scanner_query = (
        select(Scan.scanner, func.count(Scan.id)).where(Scan.created_at >= since).group_by(Scan.scanner)
    )
    scan_scanner_result = await session.execute(scan_scanner_query)
    scans_by_scanner = dict(scan_scanner_result.all())

    # Average scan duration
    avg_duration_query = select(func.avg(Scan.duration_seconds)).where(
        Scan.created_at >= since, Scan.duration_seconds.isnot(None)
    )
    avg_duration_result = await session.execute(avg_duration_query)
    avg_duration = avg_duration_result.scalar()
    avg_duration = round(avg_duration) if avg_duration else 0

    # --- Score trend (daily average over period) ---
    score_trend_query = (
        select(
            func.date(Scan.completed_at).label("date"),
            func.avg(Scan.score).label("avg_score"),
            func.count(Scan.id).label("scan_count"),
        )
        .where(
            Scan.completed_at >= since,
            Scan.score.isnot(None),
            Scan.status == "completed",
        )
        .group_by(func.date(Scan.completed_at))
        .order_by(func.date(Scan.completed_at))
    )
    score_trend_result = await session.execute(score_trend_query)
    score_trend = [
        {
            "date": str(row.date),
            "avg_score": round(row.avg_score) if row.avg_score else 0,
            "scan_count": row.scan_count,
        }
        for row in score_trend_result.all()
    ]

    # --- Scanner comparison (avg score per scanner) ---
    scanner_comparison_query = (
        select(
            Scan.scanner,
            func.avg(Scan.score).label("avg_score"),
            func.sum(Scan.passed).label("total_passed"),
            func.sum(Scan.failed).label("total_failed"),
            func.sum(Scan.warnings).label("total_warnings"),
            func.count(Scan.id).label("total_scans"),
        )
        .where(Scan.created_at >= since, Scan.status == "completed")
        .group_by(Scan.scanner)
    )
    scanner_comparison_result = await session.execute(scanner_comparison_query)
    scanner_comparison = [
        {
            "scanner": row.scanner,
            "avg_score": round(row.avg_score) if row.avg_score else 0,
            "total_passed": row.total_passed or 0,
            "total_failed": row.total_failed or 0,
            "total_warnings": row.total_warnings or 0,
            "total_scans": row.total_scans,
        }
        for row in scanner_comparison_result.all()
    ]

    # --- Severity breakdown from ScanResults ---
    severity_query = (
        select(ScanResult.severity, ScanResult.status, func.count(ScanResult.id))
        .join(Scan, ScanResult.scan_id == Scan.id)
        .where(Scan.created_at >= since, Scan.status == "completed")
        .group_by(ScanResult.severity, ScanResult.status)
    )
    severity_result = await session.execute(severity_query)

    findings_by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    findings_by_status = {"pass": 0, "fail": 0, "error": 0, "notapplicable": 0}
    for sev, st, cnt in severity_result.all():
        sev_lower = (sev or "info").lower()
        st_lower = (st or "error").lower()
        if sev_lower in findings_by_severity:
            findings_by_severity[sev_lower] += cnt
        if st_lower in findings_by_status:
            findings_by_status[st_lower] += cnt

    total_findings = sum(findings_by_status.values())
    failed_findings = findings_by_status.get("fail", 0)

    # --- Top failing rules ---
    top_rules_query = (
        select(
            ScanResult.rule_id,
            ScanResult.title,
            ScanResult.severity,
            ScanResult.category,
            Scan.scanner,
            func.count(ScanResult.id).label("occurrence_count"),
        )
        .join(Scan, ScanResult.scan_id == Scan.id)
        .where(
            Scan.created_at >= since,
            Scan.status == "completed",
            ScanResult.status == "fail",
        )
        .group_by(ScanResult.rule_id, ScanResult.title, ScanResult.severity, ScanResult.category, Scan.scanner)
        .order_by(func.count(ScanResult.id).desc())
        .limit(20)
    )
    top_rules_result = await session.execute(top_rules_query)
    top_failing_rules = [
        {
            "rule_id": row.rule_id,
            "title": row.title,
            "severity": row.severity,
            "category": row.category,
            "scanner": row.scanner,
            "count": row.occurrence_count,
        }
        for row in top_rules_result.all()
    ]

    # --- Recent scans ---
    recent_scans_query = select(Scan).options(selectinload(Scan.host)).order_by(Scan.created_at.desc()).limit(10)
    recent_scans_result = await session.execute(recent_scans_query)
    recent_scans = [
        {
            "id": s.id,
            "host_name": s.host.name if s.host else "Unknown",
            "scanner": s.scanner,
            "status": s.status,
            "score": s.score,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "duration_seconds": s.duration_seconds,
            "passed": s.passed,
            "failed": s.failed,
            "warnings": s.warnings,
        }
        for s in recent_scans_result.scalars().all()
    ]

    # --- Schedules overview ---
    schedule_query = select(ScanSchedule).options(selectinload(ScanSchedule.host))
    schedule_result = await session.execute(schedule_query)
    schedules = schedule_result.scalars().all()

    active_schedules = sum(1 for s in schedules if s.is_active)
    upcoming_scans = []
    for s in sorted(schedules, key=lambda x: x.next_run_at or datetime.max.replace(tzinfo=timezone.utc)):
        if s.is_active and s.next_run_at:
            upcoming_scans.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "host_name": s.host.name if s.host else "Unknown",
                    "scanner": s.scanner,
                    "next_run_at": s.next_run_at.isoformat(),
                    "cron_expression": s.cron_expression,
                    "run_count": s.run_count,
                }
            )
    upcoming_scans = upcoming_scans[:5]

    # --- Scan activity heatmap (scans per day, last 30 days) ---
    activity_query = (
        select(
            func.date(Scan.created_at).label("date"),
            func.count(Scan.id).label("count"),
        )
        .where(Scan.created_at >= since)
        .group_by(func.date(Scan.created_at))
        .order_by(func.date(Scan.created_at))
    )
    activity_result = await session.execute(activity_query)
    scan_activity = [{"date": str(row.date), "count": row.count} for row in activity_result.all()]

    return {
        "hostname": socket.gethostname(),
        "summary": {
            "total_hosts": total_hosts,
            "online_hosts": online_hosts,
            "offline_hosts": offline_hosts,
            "scanning_hosts": scanning_hosts,
            "total_scans": total_scans,
            "avg_score": avg_score,
            "avg_duration": avg_duration,
            "active_schedules": active_schedules,
            "total_findings": total_findings,
            "failed_findings": failed_findings,
        },
        "score_distribution": score_distribution,
        "scans_by_status": scans_by_status,
        "scans_by_scanner": scans_by_scanner,
        "score_trend": score_trend,
        "scanner_comparison": scanner_comparison,
        "findings_by_severity": findings_by_severity,
        "findings_by_status": findings_by_status,
        "top_failing_rules": top_failing_rules,
        "host_scores": host_scores,
        "recent_scans": recent_scans,
        "upcoming_scans": upcoming_scans,
        "scan_activity": scan_activity,
    }
