from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import BiCountyConfig, BiSnapshot, County
from modules.inventory.schemas.county import CountyOut

router = APIRouter(prefix="/counties", tags=["counties"])


@router.get("", response_model=list[CountyOut])
def list_counties(db: Session = Depends(get_db)):
    # Subquery: most recent completed snapshot per county
    latest = (
        db.query(
            BiSnapshot.county_id,
            func.max(BiSnapshot.completed_at).label("last_snapshot_at"),
        )
        .filter(BiSnapshot.status == "completed")
        .group_by(BiSnapshot.county_id)
        .subquery()
    )

    # Join to get parcel count from that snapshot
    latest_detail = (
        db.query(
            BiSnapshot.county_id,
            BiSnapshot.completed_at.label("last_snapshot_at"),
            BiSnapshot.total_parcels_queried.label("last_snapshot_parcels"),
        )
        .join(latest, (BiSnapshot.county_id == latest.c.county_id)
              & (BiSnapshot.completed_at == latest.c.last_snapshot_at))
        .subquery()
    )

    rows = (
        db.query(
            County,
            latest_detail.c.last_snapshot_at,
            latest_detail.c.last_snapshot_parcels,
            BiCountyConfig.gis_endpoint,
        )
        .outerjoin(latest_detail, County.id == latest_detail.c.county_id)
        .outerjoin(BiCountyConfig, BiCountyConfig.county_id == County.id)
        .order_by(County.name)
        .all()
    )

    return [
        CountyOut(
            id=c.id,
            name=c.name,
            state=c.state,
            dor_county_no=c.dor_county_no,
            is_active=c.is_active,
            has_endpoint=gis_endpoint is not None,
            last_snapshot_at=snap_at,
            last_snapshot_parcels=snap_parcels,
        )
        for c, snap_at, snap_parcels, gis_endpoint in rows
    ]
