from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import Builder, County, Parcel, BiSnapshot, Subdivision
from modules.inventory.schemas.inventory import (
    BuilderCount,
    CountyDetail,
    CountyInventory,
    MapMarker,
    SubdivisionInventory,
    TrendPoint,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])

VALID_PARCEL_CLASSES = {"lot", "common_area", "tract", "other"}


VALID_ENTITY_TYPES = {"builder", "developer", "land_banker", "btr"}


@router.get("", response_model=list[CountyInventory])
def get_inventory(
    parcel_class: list[str] = Query(default=["lot"]),
    entity_type: list[str] = Query(default=["builder"]),
    builder_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Inventory counts by county. Filter by parcel_class, entity_type, and builder_id."""
    q = (
        db.query(
            County.id,
            County.name,
            Builder.id,
            Builder.canonical_name,
            func.count(Parcel.id),
            func.coalesce(func.sum(Parcel.acreage), 0.0),
        )
        .join(Parcel, Parcel.county_id == County.id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(Parcel.is_active == True)
    )

    classes = [c for c in parcel_class if c in VALID_PARCEL_CLASSES]
    if classes:
        q = q.filter(Parcel.parcel_class.in_(classes))

    types = [t for t in entity_type if t in VALID_ENTITY_TYPES]
    if types:
        q = q.filter(Builder.type.in_(types))

    if builder_id is not None:
        q = q.filter(Parcel.builder_id == builder_id)

    rows = (
        q.group_by(County.id, County.name, Builder.id, Builder.canonical_name)
        .order_by(County.name, Builder.canonical_name)
        .all()
    )

    counties: dict[int, CountyInventory] = {}
    for county_id, county_name, bid, builder_name, count, acreage in rows:
        if county_id not in counties:
            counties[county_id] = CountyInventory(
                county_id=county_id, county=county_name, total=0, builders=[]
            )
        counties[county_id].builders.append(
            BuilderCount(builder_id=bid, builder_name=builder_name, count=count, acreage=float(acreage))
        )
        counties[county_id].total += count

    return list(counties.values())


@router.get("/trends", response_model=list[TrendPoint])
def get_trends(
    county_id: int | None = None,
    days: int = Query(default=90, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Inventory trend data from snapshot history. Returns one point per county per completed snapshot."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    q = (
        db.query(
            BiSnapshot.completed_at,
            BiSnapshot.county_id,
            County.name,
            BiSnapshot.total_parcels_queried,
            BiSnapshot.new_count,
            BiSnapshot.removed_count,
            BiSnapshot.changed_count,
        )
        .join(County, County.id == BiSnapshot.county_id)
        .filter(BiSnapshot.status == "completed")
        .filter(BiSnapshot.completed_at >= cutoff)
    )

    if county_id is not None:
        q = q.filter(BiSnapshot.county_id == county_id)

    rows = q.order_by(BiSnapshot.completed_at).all()

    return [
        TrendPoint(
            date=row[0],
            county_id=row[1],
            county=row[2],
            total_parcels=row[3],
            new_count=row[4],
            removed_count=row[5],
            changed_count=row[6],
        )
        for row in rows
    ]


@router.get("/map", response_model=list[MapMarker])
def get_map_markers(
    county_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Map markers: one per (subdivision, builder) with averaged parcel centroids."""
    q = (
        db.query(
            Subdivision.id.label("subdivision_id"),
            Subdivision.name.label("subdivision_name"),
            County.id.label("county_id"),
            County.name.label("county_name"),
            Builder.id.label("builder_id"),
            Builder.canonical_name.label("builder_name"),
            func.count(Parcel.id).label("lot_count"),
            func.avg(func.ST_Y(Parcel.centroid)).label("lat"),
            func.avg(func.ST_X(Parcel.centroid)).label("lng"),
        )
        .join(Subdivision, Subdivision.id == Parcel.subdivision_id)
        .join(County, County.id == Parcel.county_id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(
            Parcel.is_active == True,
            Parcel.parcel_class == "lot",
            Parcel.subdivision_id.isnot(None),
        )
    )

    if county_id is not None:
        q = q.filter(Parcel.county_id == county_id)

    rows = (
        q.group_by(
            Subdivision.id, Subdivision.name,
            County.id, County.name,
            Builder.id, Builder.canonical_name,
        )
        .order_by(County.name, Subdivision.name)
        .all()
    )

    return [
        MapMarker(
            subdivision_id=r.subdivision_id,
            subdivision_name=r.subdivision_name,
            county_id=r.county_id,
            county_name=r.county_name,
            builder_id=r.builder_id,
            builder_name=r.builder_name,
            lot_count=r.lot_count,
            lat=float(r.lat) if r.lat is not None else None,
            lng=float(r.lng) if r.lng is not None else None,
        )
        for r in rows
    ]


@router.get("/{county_id}", response_model=CountyDetail)
def get_county_inventory(
    county_id: int,
    parcel_class: list[str] = Query(default=["lot"]),
    entity_type: list[str] = Query(default=["builder"]),
    builder_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Inventory counts by subdivision within a county. Filter by parcel_class, entity_type, and builder_id."""
    county = db.get(County, county_id)
    if not county:
        from fastapi import HTTPException
        raise HTTPException(404, "County not found")

    q = (
        db.query(
            Subdivision.id,
            Subdivision.name,
            Builder.id,
            Builder.canonical_name,
            func.count(Parcel.id),
        )
        .select_from(Parcel)
        .outerjoin(Subdivision, Subdivision.id == Parcel.subdivision_id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(Parcel.county_id == county_id, Parcel.is_active == True)
    )

    classes = [c for c in parcel_class if c in VALID_PARCEL_CLASSES]
    if classes:
        q = q.filter(Parcel.parcel_class.in_(classes))

    types = [t for t in entity_type if t in VALID_ENTITY_TYPES]
    if types:
        q = q.filter(Builder.type.in_(types))

    if builder_id is not None:
        q = q.filter(Parcel.builder_id == builder_id)

    rows = (
        q.group_by(Subdivision.id, Subdivision.name, Builder.id, Builder.canonical_name)
        .order_by(Subdivision.name, Builder.canonical_name)
        .all()
    )

    subdivisions: dict[int | None, SubdivisionInventory] = {}
    for sub_id, sub_name, bid, builder_name, count in rows:
        key = sub_id
        if key not in subdivisions:
            subdivisions[key] = SubdivisionInventory(
                subdivision_id=sub_id,
                subdivision=sub_name or "Unlinked",
                total=0,
                builders=[],
            )
        subdivisions[key].builders.append(BuilderCount(builder_id=bid, builder_name=builder_name, count=count))
        subdivisions[key].total += count

    total = sum(s.total for s in subdivisions.values())
    return CountyDetail(
        county_id=county_id,
        county=county.name,
        total=total,
        subdivisions=list(subdivisions.values()),
    )
