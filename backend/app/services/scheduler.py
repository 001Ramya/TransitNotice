import logging
from threading import Lock

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.database import SessionLocal
from app.services.collectors import refresh_enabled_sources

logger = logging.getLogger("transitnotice.scheduler")
refresh_lock = Lock()
scheduler = BackgroundScheduler(timezone="UTC")


def scheduled_refresh() -> None:
    if settings.demo_mode:
        return
    if not refresh_lock.acquire(blocking=False):
        logger.info("Refresh skipped because another source check is still running")
        return
    try:
        with SessionLocal() as session:
            refresh_enabled_sources(session)
    finally:
        refresh_lock.release()


def start_scheduler() -> None:
    if settings.scheduler_enabled and not scheduler.running:
        scheduler.add_job(
            scheduled_refresh,
            "interval",
            minutes=max(5, settings.refresh_interval_minutes),
            id="source-refresh",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
