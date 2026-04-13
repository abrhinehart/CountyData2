from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import (
    Builder,
    BuilderAlias,
    BuilderCounty,
    County,
    Parcel,
    BiParcelSnapshot,
    BiSnapshot,
    Subdivision,
)
from modules.inventory.schemas.builder import (
    BuilderCreate,
    BuilderInfo,
    BuilderOut,
    BuilderPortfolio,
    BuilderUpdate,
    PortfolioChange,
    PortfolioCounty,
    PortfolioSubdivision,
)

router = APIRouter(prefix="/builders", tags=["builders"])


@router.get("", response_model=list[BuilderOut])
def list_builders(
    type: list[str] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(Builder)
        .filter(Builder.is_active == True)  # noqa: E712
        .filter(Builder.aliases.any())  # Only builders with curated aliases (excludes permit auto-inserts)
    )
    if type:
        q = q.filter(Builder.type.in_(type))
    return q.order_by(Builder.canonical_name).all()


@router.post("", response_model=BuilderOut, status_code=201)
def create_builder(data: BuilderCreate, db: Session = Depends(get_db)):
    existing = db.query(Builder).filter_by(canonical_name=data.canonical_name).first()
    if existing:
        raise HTTPException(409, "Builder already exists")

    builder = Builder(canonical_name=data.canonical_name, type=data.type, scope=data.scope)
    db.add(builder)
    db.flush()

    for alias_str in data.aliases:
        db.add(BuilderAlias(builder_id=builder.id, alias=alias_str))

    for county_id in data.county_ids:
        db.add(BuilderCounty(builder_id=builder.id, county_id=county_id))

    db.commit()
    db.refresh(builder)
    return builder


@router.put("/{builder_id}", response_model=BuilderOut)
def update_builder(builder_id: int, data: BuilderUpdate, db: Session = Depends(get_db)):
    builder = db.get(Builder, builder_id)
    if not builder:
        raise HTTPException(404, "Builder not found")

    if data.canonical_name is not None:
        builder.canonical_name = data.canonical_name
    if data.type is not None:
        builder.type = data.type
    if data.is_active is not None:
        builder.is_active = data.is_active
    if data.scope is not None:
        builder.scope = data.scope

    if data.aliases is not None:
        db.query(BuilderAlias).filter_by(builder_id=builder.id).delete()
        for alias_str in data.aliases:
            db.add(BuilderAlias(builder_id=builder.id, alias=alias_str))

    if data.county_ids is not None:
        db.query(BuilderCounty).filter_by(builder_id=builder.id).delete()
        for county_id in data.county_ids:
            db.add(BuilderCounty(builder_id=builder.id, county_id=county_id))

    db.commit()
    db.refresh(builder)
    return builder


@router.delete("/{builder_id}", status_code=204)
def delete_builder(builder_id: int, db: Session = Depends(get_db)):
    builder = db.get(Builder, builder_id)
    if not builder:
        raise HTTPException(404, "Builder not found")
    db.delete(builder)
    db.commit()


@router.get("/{builder_id}/portfolio", response_model=BuilderPortfolio)
def get_builder_portfolio(builder_id: int, db: Session = Depends(get_db)):
    """Comprehensive portfolio view for a single builder."""
    builder = db.get(Builder, builder_id)
    if not builder:
        raise HTTPException(404, "Builder not found")

    alias_count = db.query(BuilderAlias).filter_by(builder_id=builder_id).count()

    # County breakdown
    county_rows = (
        db.query(
            County.id,
            County.name,
            func.count(Parcel.id).label("lot_count"),
            func.coalesce(func.sum(Parcel.acreage), 0).label("acreage"),
        )
        .join(Parcel, Parcel.county_id == County.id)
        .filter(
            Parcel.builder_id == builder_id,
            Parcel.is_active == True,
            Parcel.parcel_class == "lot",
        )
        .group_by(County.id, County.name)
        .order_by(func.count(Parcel.id).desc())
        .all()
    )

    counties = [
        PortfolioCounty(
            county_id=r[0], county_name=r[1],
            lot_count=r[2], acreage=round(float(r[3]), 2),
        )
        for r in county_rows
    ]

    total_lots = sum(c.lot_count for c in counties)
    total_acreage = round(sum(c.acreage for c in counties), 2)

    # Top subdivisions
    sub_rows = (
        db.query(
            Subdivision.id,
            Subdivision.name,
            County.name.label("county_name"),
            func.count(Parcel.id).label("lot_count"),
        )
        .join(Parcel, Parcel.subdivision_id == Subdivision.id)
        .join(County, County.id == Parcel.county_id)
        .filter(
            Parcel.builder_id == builder_id,
            Parcel.is_active == True,
            Parcel.parcel_class == "lot",
        )
        .group_by(Subdivision.id, Subdivision.name, County.name)
        .order_by(func.count(Parcel.id).desc())
        .limit(25)
        .all()
    )

    top_subdivisions = [
        PortfolioSubdivision(
            subdivision_id=r[0], subdivision_name=r[1],
            county_name=r[2], lot_count=r[3],
        )
        for r in sub_rows
    ]

    # Recent changes
    change_rows = (
        db.query(
            Parcel.id.label("parcel_id"),
            Parcel.parcel_number,
            Parcel.site_address,
            County.name.label("county_name"),
            Subdivision.name.label("subdivision_name"),
            BiParcelSnapshot.change_type,
            BiSnapshot.completed_at,
        )
        .join(BiParcelSnapshot, BiParcelSnapshot.parcel_id == Parcel.id)
        .join(BiSnapshot, BiSnapshot.id == BiParcelSnapshot.snapshot_id)
        .join(County, County.id == Parcel.county_id)
        .outerjoin(Subdivision, Subdivision.id == Parcel.subdivision_id)
        .filter(Parcel.builder_id == builder_id)
        .order_by(BiSnapshot.completed_at.desc())
        .limit(50)
        .all()
    )

    recent_changes = [
        PortfolioChange(
            parcel_id=r.parcel_id,
            parcel_number=r.parcel_number,
            site_address=r.site_address,
            county_name=r.county_name,
            subdivision_name=r.subdivision_name,
            change_type=r.change_type,
            snapshot_date=r.completed_at.isoformat() if r.completed_at else None,
        )
        for r in change_rows
    ]

    return BuilderPortfolio(
        builder=BuilderInfo(
            id=builder.id,
            canonical_name=builder.canonical_name,
            type=builder.type,
            scope=builder.scope,
            alias_count=alias_count,
        ),
        total_lots=total_lots,
        total_acreage=total_acreage,
        counties=counties,
        top_subdivisions=top_subdivisions,
        recent_changes=recent_changes,
    )
