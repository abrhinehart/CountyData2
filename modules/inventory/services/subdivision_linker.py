"""Link parcels to subdivisions via PostGIS ST_Contains (centroid point-in-polygon)."""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def link_parcels_to_subdivisions(county_id: int, db: Session) -> int:
    """Assign subdivision_id to parcels whose centroid falls within a subdivision polygon.

    Only updates parcels that have no subdivision_id yet and have a centroid.
    Returns the number of parcels updated.
    """
    result = db.execute(
        text("""
            UPDATE parcels
            SET subdivision_id = s.id
            FROM subdivisions s
            WHERE parcels.county_id = :county_id
              AND s.county_id = :county_id
              AND parcels.subdivision_id IS NULL
              AND parcels.centroid IS NOT NULL
              AND s.geom IS NOT NULL
              AND ST_Contains(s.geom, parcels.centroid)
        """),
        {"county_id": county_id},
    )
    count = result.rowcount
    db.commit()
    logger.info(f"Linked {count} parcels to subdivisions in county {county_id}")
    return count


def link_all_counties(db: Session) -> dict[int, int]:
    """Run subdivision linker for all counties that have parcels and subdivisions."""
    from modules.inventory.models import County, Parcel
    from sqlalchemy import func

    # Find counties with unlinked parcels
    counties = db.query(County.id, County.name).join(Parcel).filter(Parcel.subdivision_id == None).distinct().all()

    results = {}
    for cid, name in counties:
        count = link_parcels_to_subdivisions(cid, db)
        results[cid] = count

    return results
