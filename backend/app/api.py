from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, nulls_last, select
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.models import Agency, AlertDelivery, CollectorRun, Notice, NoticeRevision, utc_now
from app.schemas import DeliveryOut, NoticeOut, RevisionOut, SettingsOut, SourceOut
from app.services.collectors import refresh_enabled_sources
from app.services.processing import current_status
from app.services.scheduler import refresh_lock

router = APIRouter()
manual_lock = Lock()
SOURCE_INFO = {
    "mtc_chennai": ("MTC Chennai", "https://mtcbus.tn.gov.in/Home/news"),
    "cmrl": ("Chennai Metro Rail", "https://chennaimetrorail.org/press-release/"),
}


def _source_last_runs(session: Session) -> dict[str, CollectorRun]:
    latest = {}
    rows = session.scalars(select(CollectorRun).order_by(CollectorRun.started_at.desc())).all()
    for run in rows:
        latest.setdefault(run.source_key, run)
    return latest


def _last_success(session: Session, source_key: str) -> datetime | None:
    return session.scalar(
        select(func.max(CollectorRun.finished_at)).where(
            CollectorRun.source_key == source_key,
            CollectorRun.state == "success",
        )
    )


def _is_stale(agency_key: str, session: Session) -> bool:
    if settings.demo_mode or agency_key == "demo":
        return False
    last_success = _last_success(session, agency_key)
    return not last_success or utc_now() - last_success > timedelta(minutes=settings.stale_after_minutes)


def _notice_out(notice: Notice, session: Session) -> NoticeOut:
    return NoticeOut(
        id=notice.id,
        agency=notice.agency.name,
        route_ids=notice.route_ids or [],
        area=notice.area,
        source_url=notice.source_url,
        advisory_type=notice.advisory_type,
        summary=notice.summary,
        content_text=notice.content_text,
        published_at=notice.published_at,
        valid_from=notice.valid_from,
        valid_to=notice.valid_to,
        status=current_status(notice),
        last_observed_at=notice.last_observed_at,
        last_confirmed_at=notice.last_confirmed_at,
        revision_number=notice.revision_number,
        change_summary=notice.change_summary,
        is_demo=notice.is_demo,
        is_stale=_is_stale(notice.agency.key, session),
    )


@router.get("/health")
def health():
    return {"status": "ok", "service": "TransitNotice API"}


@router.get("/notices", response_model=list[NoticeOut])
def list_notices(
    search: str | None = None,
    agency: str | None = None,
    area: str | None = None,
    advisory_type: str | None = None,
    status: str | None = None,
    service_date: str | None = None,
    limit: int = Query(default=250, ge=1, le=500),
    session: Session = Depends(get_db),
):
    query = select(Notice).options(joinedload(Notice.agency))
    if not settings.demo_mode:
        query = query.where(Notice.is_demo.is_(False))
    query = query.order_by(nulls_last(Notice.published_at.desc()), Notice.last_observed_at.desc()).limit(limit)
    rows = session.scalars(query).unique().all()
    results = []
    target_date = None
    if service_date:
        try:
            target_date = datetime.fromisoformat(service_date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="service_date must use YYYY-MM-DD")
    for row in rows:
        item = _notice_out(row, session)
        if search and search.lower() not in (
            item.summary + " " + item.content_text + " " + " ".join(item.route_ids) + " " + item.area
        ).lower():
            continue
        if agency and item.agency.lower() != agency.lower():
            continue
        if area and area.lower() not in item.area.lower():
            continue
        if advisory_type and item.advisory_type != advisory_type:
            continue
        if status and item.status != status:
            continue
        if target_date:
            starts = item.valid_from.date() if item.valid_from else None
            ends = item.valid_to.date() if item.valid_to else None
            if starts and target_date < starts:
                continue
            if ends and target_date > ends:
                continue
        results.append(item)
    return results


@router.get("/notices/{notice_id}", response_model=NoticeOut)
def notice_detail(notice_id: str, session: Session = Depends(get_db)):
    notice = session.scalar(
        select(Notice).options(joinedload(Notice.agency)).where(Notice.id == notice_id)
    )
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return _notice_out(notice, session)


@router.get("/notices/{notice_id}/revisions", response_model=list[RevisionOut])
def notice_revisions(notice_id: str, session: Session = Depends(get_db)):
    if not session.scalar(select(Notice.id).where(Notice.id == notice_id)):
        raise HTTPException(status_code=404, detail="Notice not found")
    rows = session.scalars(
        select(NoticeRevision).where(NoticeRevision.notice_id == notice_id).order_by(NoticeRevision.revision_number.desc())
    ).all()
    return rows


@router.get("/history")
def history(session: Session = Depends(get_db)):
    revisions = session.execute(
        select(NoticeRevision, Notice, Agency)
        .join(Notice, NoticeRevision.notice_id == Notice.id)
        .join(Agency, Notice.agency_id == Agency.id)
        .order_by(NoticeRevision.observed_at.desc())
        .limit(250)
    ).all()
    return [
        {
            "id": revision.id,
            "notice_id": notice.id,
            "revision_number": revision.revision_number,
            "change_summary": revision.change_summary,
            "observed_at": revision.observed_at,
            "summary": notice.summary,
            "agency": agency.name,
            "route_ids": notice.route_ids or [],
            "is_demo": notice.is_demo,
        }
        for revision, notice, agency in revisions
    ]


@router.get("/alerts", response_model=list[DeliveryOut])
def alerts(session: Session = Depends(get_db)):
    return session.scalars(
        select(AlertDelivery).order_by(AlertDelivery.created_at.desc()).limit(250)
    ).all()


@router.get("/sources", response_model=list[SourceOut])
def sources(session: Session = Depends(get_db)):
    latest = _source_last_runs(session)
    result = []
    for key in ("mtc_chennai", "cmrl"):
        agency_name, source_url = SOURCE_INFO[key]
        run = latest.get(key)
        success_at = _last_success(session, key)
        if settings.demo_mode:
            enabled = False
            state = "demo"
            message = "Demo mode is on; no live source is contacted"
        elif key == "mtc_chennai":
            enabled = settings.mtc_enabled
            state = (run.state if run else "waiting") if enabled else "disabled"
            if run and run.state == "error":
                message = run.error_message or "The latest source check failed"
            elif not run:
                message = "Waiting for the first scheduled check"
            else:
                message = "Official MTC Chennai announcements are being monitored"
        else:
            enabled = settings.cmrl_enabled
            state = (run.state if run else "waiting") if enabled else "locked"
            if run and run.state == "error":
                message = run.error_message or "The latest source check failed"
            elif enabled and not run:
                message = "Waiting for the first scheduled check"
            elif not enabled:
                message = "CMRL collection is disabled in settings"
            else:
                message = "Official Chennai Metro announcements are being monitored"
        result.append(
            SourceOut(
                key=key,
                agency=agency_name,
                source_url=source_url,
                enabled=enabled,
                state=state,
                last_checked_at=run.finished_at if run else None,
                last_success_at=success_at,
                last_notice_count=run.notice_count if run and run.state == "success" else 0,
                message=message,
                is_demo=False,
            )
        )
    demo_run = latest.get("demo")
    result.append(
        SourceOut(
            key="demo",
            agency="HarborLink Demo Network",
            source_url="",
            enabled=settings.demo_mode,
            state="demo",
            last_checked_at=demo_run.finished_at if demo_run else None,
            last_success_at=None,
            last_notice_count=demo_run.notice_count if demo_run else 0,
            message="Fictional sample records for demonstrations; not a live source",
            is_demo=True,
        )
    )
    return result


@router.get("/settings", response_model=SettingsOut)
def app_settings():
    return SettingsOut(
        demo_mode=settings.demo_mode,
        scheduler_enabled=settings.scheduler_enabled,
        refresh_interval_minutes=settings.refresh_interval_minutes,
        stale_after_minutes=settings.stale_after_minutes,
        alert_mode=settings.alert_mode,
        smtp_configured=settings.smtp_ready,
        # Legacy response fields are retained for frontend compatibility.
        mbta_enabled=settings.mtc_enabled,
        mbta_key_configured=False,
        cta_terms_accepted=settings.cmrl_enabled,
    )


@router.get("/dashboard")
def dashboard(session: Session = Depends(get_db)):
    dashboard_query = select(Notice).options(joinedload(Notice.agency))
    if not settings.demo_mode:
        dashboard_query = dashboard_query.where(Notice.is_demo.is_(False))
    rows = session.scalars(dashboard_query).unique().all()
    counts = {"active": 0, "upcoming": 0, "expired": 0, "withdrawn": 0, "updated": 0, "stale": 0, "demo": 0}
    for row in rows:
        counts[current_status(row)] += 1
        if row.revision_number > 1:
            counts["updated"] += 1
        if _is_stale(row.agency.key, session):
            counts["stale"] += 1
        if row.is_demo:
            counts["demo"] += 1
    now = utc_now()
    start_day = (now - timedelta(days=6)).date()
    chart = []
    for offset in range(7):
        day = start_day + timedelta(days=offset)
        start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        created_count = session.scalar(
            select(func.count(NoticeRevision.id)).where(
                NoticeRevision.observed_at >= start,
                NoticeRevision.observed_at < end,
                NoticeRevision.revision_number == 1,
            )
        ) or 0
        changed_count = session.scalar(
            select(func.count(NoticeRevision.id)).where(
                NoticeRevision.observed_at >= start,
                NoticeRevision.observed_at < end,
                NoticeRevision.revision_number > 1,
            )
        ) or 0
        chart.append({"day": day.isoformat(), "new": created_count, "updated": changed_count})
    enabled_keys = []
    if not settings.demo_mode and settings.mtc_enabled:
        enabled_keys.append("mtc_chennai")
    if not settings.demo_mode and settings.cmrl_enabled:
        enabled_keys.append("cmrl")
    successful_checks = [_last_success(session, key) for key in enabled_keys]
    successful_checks = [value for value in successful_checks if value]
    newest_check = max(successful_checks, default=None)
    active_deliveries = session.scalar(
        select(func.count(AlertDelivery.id)).where(AlertDelivery.created_at >= now - timedelta(days=7))
    ) or 0
    recent_query = select(Notice).options(joinedload(Notice.agency))
    if not settings.demo_mode:
        recent_query = recent_query.where(Notice.is_demo.is_(False))
    recent = session.scalars(
        recent_query.order_by(nulls_last(Notice.published_at.desc()), Notice.last_observed_at.desc()).limit(5)
    ).unique().all()
    return {
        **counts,
        "total": len(rows),
        "alerts_last_7_days": active_deliveries,
        "last_checked_at": newest_check,
        "freshness_state": "demo" if settings.demo_mode else (
            "stale" if not newest_check or now - newest_check > timedelta(minutes=settings.stale_after_minutes) else "fresh"
        ),
        "notice_trend": chart,
        "recent_notices": [_notice_out(row, session) for row in recent],
        "demo_mode": settings.demo_mode,
    }


@router.post("/refresh")
def refresh(session: Session = Depends(get_db)):
    if settings.demo_mode:
        raise HTTPException(status_code=409, detail="Demo mode is on. No external source was contacted.")
    if not manual_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A refresh is already in progress.")
    if not refresh_lock.acquire(blocking=False):
        manual_lock.release()
        raise HTTPException(status_code=409, detail="A scheduled refresh is already in progress.")
    try:
        results = refresh_enabled_sources(session)
        return {
            "message": "Source checks completed. Review each source result and freshness label.",
            "started_at": datetime.now(timezone.utc),
            "results": results,
        }
    finally:
        refresh_lock.release()
        manual_lock.release()
