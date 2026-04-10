"""Lightweight discovery scan: find which entities are active in which counties.

Queries all active entities against all active counties, records hits in
builder_counties junction table. No parcel inserts, no snapshot records.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from shared.sa_database import SessionLocal
from modules.inventory.models import BiCountyConfig, Builder, BuilderAlias, BuilderCounty, County
from modules.inventory.services.gis_query import build_engine_for_county

logger = logging.getLogger(__name__)

ALIAS_DELAY = 1.0  # seconds between alias queries per county
MAX_PARALLEL = 6


def _scan_county(county_id: int, aliases: list[tuple[str, int]]) -> dict:
    """Check which entities have parcels in this county. Returns {builder_id: hit_count}."""
    db = SessionLocal()
    try:
        county = db.get(County, county_id)
        bi_config = db.query(BiCountyConfig).filter_by(county_id=county_id).first()
        engine = build_engine_for_county(county, bi_config)
        if not engine:
            return {"county_id": county_id, "county": county.name, "hits": {}, "error": "no endpoint"}

        hits: dict[int, int] = {}
        for i, (alias_str, builder_id) in enumerate(aliases):
            try:
                results = engine.query_by_owner(alias_str)
                if results:
                    hits[builder_id] = hits.get(builder_id, 0) + len(results)
            except Exception as e:
                logger.warning(f"Discovery query failed for '{alias_str}' in {county.name}: {e}")
            if i < len(aliases) - 1:
                time.sleep(ALIAS_DELAY)

        logger.info(f"Discovery scan {county.name}: {len(hits)} entities found")
        return {"county_id": county_id, "county": county.name, "hits": hits}
    except Exception as e:
        logger.error(f"Discovery scan failed for county {county_id}: {e}")
        return {"county_id": county_id, "hits": {}, "error": str(e)}
    finally:
        db.close()


def run_discovery_scan() -> list[dict]:
    """Run discovery across all active counties in parallel. Updates builder_counties table."""
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

        # Load all active aliases
        aliases = (
            db.query(BuilderAlias.alias, BuilderAlias.builder_id)
            .join(BuilderAlias.builder)
            .filter(Builder.is_active == True)
            .all()
        )
        alias_list = [(a.alias, a.builder_id) for a in aliases]

        logger.info(f"Discovery scan: {len(county_ids)} counties, {len(alias_list)} aliases")
    finally:
        db.close()

    # Run counties in parallel
    results = []
    with ThreadPoolExecutor(max_workers=MAX_PARALLEL) as pool:
        futures = {
            pool.submit(_scan_county, cid, alias_list): cid
            for cid in county_ids
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Update builder_counties junction table with discoveries
    db = SessionLocal()
    try:
        new_assignments = 0
        for result in results:
            county_id = result["county_id"]
            for builder_id in result.get("hits", {}):
                existing = (
                    db.query(BuilderCounty)
                    .filter_by(builder_id=builder_id, county_id=county_id)
                    .first()
                )
                if not existing:
                    db.add(BuilderCounty(builder_id=builder_id, county_id=county_id))
                    new_assignments += 1
        db.commit()
        logger.info(f"Discovery scan complete: {new_assignments} new builder-county assignments")
    finally:
        db.close()

    # Build summary
    summary = []
    for r in sorted(results, key=lambda x: x.get("county", "")):
        if r.get("hits"):
            summary.append({
                "county": r["county"],
                "entities_found": len(r["hits"]),
                "total_parcels": sum(r["hits"].values()),
            })
    return summary
