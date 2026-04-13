import logging
from threading import Thread

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import (
    BiCountyConfig,
    BiParcelSnapshot,
    BiSnapshot,
    Builder,
    County,
    Parcel,
    Subdivision,
)
from modules.inventory.schemas.snapshot import (
    BuilderChangeSummary,
    ParcelChangeOut,
    SnapshotChangesOut,
    SnapshotOut,
    SnapshotRunRequest,
    SnapshotRunResponse,
)
from modules.inventory.services.discovery_scan import run_discovery_scan
from modules.inventory.services.snapshot_parallel import run_parallel_counties, run_single_county

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotOut])
def list_snapshots(county_id: int | None = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(BiSnapshot)
    if county_id:
        q = q.filter_by(county_id=county_id)
    return q.order_by(BiSnapshot.started_at.desc()).limit(limit).all()


@router.get("/active", response_model=list[SnapshotOut])
def list_active_snapshots(db: Session = Depends(get_db)):
    """Return all currently running snapshots with progress info."""
    return (
        db.query(BiSnapshot)
        .filter(BiSnapshot.status == "running")
        .order_by(BiSnapshot.started_at.desc())
        .all()
    )


@router.get("/{snapshot_id}/changes", response_model=SnapshotChangesOut)
def get_snapshot_changes(snapshot_id: int, db: Session = Depends(get_db)):
    """Return per-builder breakdown of parcel changes for a snapshot."""
    snapshot = db.get(BiSnapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(404, "Snapshot not found")

    county = db.get(County, snapshot.county_id)

    rows = (
        db.query(
            BiParcelSnapshot.id,
            BiParcelSnapshot.change_type,
            BiParcelSnapshot.old_values,
            BiParcelSnapshot.new_values,
            Parcel.id.label("parcel_id"),
            Parcel.parcel_number,
            Parcel.site_address,
            Parcel.owner_name,
            Builder.canonical_name.label("builder_name"),
            Subdivision.name.label("subdivision"),
        )
        .join(Parcel, Parcel.id == BiParcelSnapshot.parcel_id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .outerjoin(Subdivision, Subdivision.id == Parcel.subdivision_id)
        .filter(BiParcelSnapshot.snapshot_id == snapshot_id)
        .order_by(Builder.canonical_name, BiParcelSnapshot.change_type)
        .all()
    )

    # Group by builder
    builder_map: dict[str, BuilderChangeSummary] = {}
    for row in rows:
        name = row.builder_name
        if name not in builder_map:
            builder_map[name] = BuilderChangeSummary(
                builder_name=name,
                new_count=0,
                removed_count=0,
                changed_count=0,
                parcels=[],
            )
        bs = builder_map[name]

        if row.change_type == "new":
            bs.new_count += 1
        elif row.change_type == "removed":
            bs.removed_count += 1
        elif row.change_type == "changed":
            bs.changed_count += 1

        bs.parcels.append(ParcelChangeOut(
            parcel_id=row.parcel_id,
            parcel_number=row.parcel_number,
            site_address=row.site_address,
            subdivision=row.subdivision,
            owner_name=row.owner_name,
            change_type=row.change_type,
            old_values=row.old_values,
            new_values=row.new_values,
        ))

    # Sort builders by total activity
    builders = sorted(
        builder_map.values(),
        key=lambda b: b.new_count + b.removed_count + b.changed_count,
        reverse=True,
    )

    return SnapshotChangesOut(
        snapshot_id=snapshot.id,
        county_id=snapshot.county_id,
        county=county.name if county else "Unknown",
        summary_text=snapshot.summary_text,
        builders=builders,
    )


@router.post("/run", response_model=SnapshotRunResponse)
def trigger_snapshot(data: SnapshotRunRequest, db: Session = Depends(get_db)):
    """Trigger a scoped snapshot run in the background.

    - Single county: runs in a background thread.
    - All counties: runs in parallel with bounded concurrency.
    """
    if data.county_id:
        counties = [db.get(County, data.county_id)]
        if not counties[0]:
            raise HTTPException(404, "County not found")
        county_ids = [counties[0].id]
    else:
        # Find counties that have a BiCountyConfig with a gis_endpoint
        county_ids = [
            row.county_id
            for row in db.query(BiCountyConfig.county_id)
            .join(County, County.id == BiCountyConfig.county_id)
            .filter(County.is_active == True, BiCountyConfig.gis_endpoint.isnot(None))
            .all()
        ]

    if len(county_ids) == 1:
        thread = Thread(target=run_single_county, args=(county_ids[0],), daemon=True)
        thread.start()
    else:
        thread = Thread(target=run_parallel_counties, args=(county_ids,), daemon=True)
        thread.start()

    return SnapshotRunResponse(
        message=f"Snapshot triggered for {len(county_ids)} county(ies)",
        snapshot_ids=[],
    )


@router.post("/discover", response_model=SnapshotRunResponse)
def trigger_discovery(db: Session = Depends(get_db)):
    """Run a lightweight discovery scan to find which entities are active in which counties.

    Queries all entities against all counties but only records builder-county
    assignments -- no parcel inserts, no snapshot records.
    """
    thread = Thread(target=run_discovery_scan, daemon=True)
    thread.start()

    county_count = (
        db.query(BiCountyConfig.county_id)
        .join(County, County.id == BiCountyConfig.county_id)
        .filter(County.is_active == True, BiCountyConfig.gis_endpoint.isnot(None))
        .count()
    )
    return SnapshotRunResponse(
        message=f"Discovery scan started across {county_count} counties",
        snapshot_ids=[],
    )
