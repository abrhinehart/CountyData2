"""Parallel snapshot execution — shared by the API router and the scheduler."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from shared.sa_database import SessionLocal
from modules.inventory.models import BiCountyConfig, County
from modules.inventory.services.snapshot_runner import run_snapshot

logger = logging.getLogger(__name__)

MAX_PARALLEL_COUNTIES = 6


def run_single_county(county_id: int) -> dict:
    """Run snapshot for one county with its own DB session."""
    db = SessionLocal()
    try:
        return run_snapshot(county_id, db)
    except Exception as e:
        logger.error(f"Snapshot failed for county {county_id}: {e}")
        return {"county_id": county_id, "status": "failed", "error": str(e)}
    finally:
        db.close()


def run_parallel_counties(county_ids: list[int]) -> list[dict]:
    """Run snapshots for multiple counties in parallel with bounded concurrency.

    Returns list of result dicts.
    """
    results = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_COUNTIES) as pool:
        futures = {
            pool.submit(run_single_county, cid): cid
            for cid in county_ids
        }
        for future in as_completed(futures):
            cid = futures[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"County {cid} completed: {result.get('status', 'unknown')}")
            except Exception as e:
                logger.error(f"County {cid} raised: {e}")
                results.append({"county_id": cid, "status": "failed", "error": str(e)})

    completed = sum(1 for r in results if r.get("status") == "completed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    logger.info(f"Parallel snapshot done: {completed} completed, {failed} failed out of {len(county_ids)}")
    return results


def run_all_active_counties() -> list[dict]:
    """Query all active counties that have BI GIS config and run snapshots in parallel."""
    db = SessionLocal()
    try:
        # Find counties that have a BiCountyConfig with a gis_endpoint
        county_ids = [
            row.county_id
            for row in db.query(BiCountyConfig.county_id)
            .join(County, County.id == BiCountyConfig.county_id)
            .filter(County.is_active == True, BiCountyConfig.gis_endpoint.isnot(None))
            .all()
        ]
    finally:
        db.close()

    if not county_ids:
        logger.info("No active counties to scan")
        return []

    logger.info(f"Scheduled scan: {len(county_ids)} counties")
    return run_parallel_counties(county_ids)
