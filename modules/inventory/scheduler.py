"""APScheduler configuration with Postgres-backed job store."""

import logging

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from modules.inventory.services.snapshot_parallel import run_all_active_counties

logger = logging.getLogger(__name__)

SNAPSHOT_JOB_ID = "snapshot_job"


def run_all_county_snapshots():
    """Job function: run snapshot for all active counties in parallel."""
    results = run_all_active_counties()
    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    logger.info(f"Scheduled snapshot batch done: {completed} completed, {failed} failed")


def create_scheduler(db_url: str | None = None) -> BackgroundScheduler:
    if db_url is None:
        from config import DATABASE_URL
        db_url = DATABASE_URL
    jobstores = {"default": SQLAlchemyJobStore(url=db_url)}
    executors = {"default": ThreadPoolExecutor(max_workers=4)}
    scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors)
    return scheduler


def setup_snapshot_job(scheduler: BackgroundScheduler, interval_minutes: int):
    """Add or replace the snapshot interval job."""
    scheduler.add_job(
        run_all_county_snapshots,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id=SNAPSHOT_JOB_ID,
        replace_existing=True,
        coalesce=True,
        misfire_grace_time=3600,
    )
    logger.info(f"Snapshot job scheduled every {interval_minutes} minutes")


def remove_snapshot_job(scheduler: BackgroundScheduler):
    """Remove the snapshot job if it exists."""
    try:
        scheduler.remove_job(SNAPSHOT_JOB_ID)
        logger.info("Snapshot job removed")
    except Exception:
        pass
