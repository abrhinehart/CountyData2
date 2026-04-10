"""Raw land acreage view -- aggregates tract parcels by entity."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import Builder, County, Parcel

router = APIRouter(prefix="/raw-land", tags=["raw-land"])

VALID_ENTITY_TYPES = {"builder", "developer", "land_banker", "btr"}


class CountyAcreage(BaseModel):
    county_id: int
    county: str
    acreage: float
    parcel_count: int
    model_config = ConfigDict(from_attributes=True)


class EntityRawLand(BaseModel):
    builder_id: int
    entity: str
    entity_type: str
    total_acreage: float
    parcel_count: int
    counties: list[CountyAcreage]
    model_config = ConfigDict(from_attributes=True)


class RawLandSummary(BaseModel):
    items: list[EntityRawLand]
    total_acreage: float
    total_parcels: int


@router.get("", response_model=RawLandSummary)
def raw_land_summary(
    entity_type: list[str] = Query(default=[]),
    county_id: int | None = None,
    search: str | None = None,
    sort: str = "acreage",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    """Return raw land (tract) acreage aggregated by entity."""

    base = (
        db.query(
            Parcel.builder_id,
            Parcel.county_id,
            Builder.canonical_name.label("entity"),
            Builder.type.label("entity_type"),
            County.name.label("county"),
            func.sum(Parcel.acreage).label("acreage"),
            func.count(Parcel.id).label("parcel_count"),
        )
        .join(Builder, Builder.id == Parcel.builder_id)
        .join(County, County.id == Parcel.county_id)
        .filter(Parcel.is_active == True)
        .filter(Parcel.parcel_class == "tract")
        .filter(Parcel.acreage.isnot(None))
    )

    types = [t for t in entity_type if t in VALID_ENTITY_TYPES]
    if types:
        base = base.filter(Builder.type.in_(types))

    if county_id is not None:
        base = base.filter(Parcel.county_id == county_id)

    if search:
        pattern = f"%{search}%"
        base = base.filter(Builder.canonical_name.ilike(pattern))

    # Group by entity + county for county-level breakdown
    county_rows = (
        base.group_by(
            Parcel.builder_id,
            Parcel.county_id,
            Builder.canonical_name,
            Builder.type,
            County.name,
        )
        .all()
    )

    # Aggregate into entity-level summaries
    entity_map: dict[int, EntityRawLand] = {}
    for row in county_rows:
        if row.builder_id not in entity_map:
            entity_map[row.builder_id] = EntityRawLand(
                builder_id=row.builder_id,
                entity=row.entity,
                entity_type=row.entity_type,
                total_acreage=0,
                parcel_count=0,
                counties=[],
            )
        ent = entity_map[row.builder_id]
        ent.total_acreage += float(row.acreage)
        ent.parcel_count += row.parcel_count
        ent.counties.append(
            CountyAcreage(
                county_id=row.county_id,
                county=row.county,
                acreage=float(row.acreage),
                parcel_count=row.parcel_count,
            )
        )

    items = list(entity_map.values())

    # Sort counties within each entity by acreage desc
    for item in items:
        item.counties.sort(key=lambda c: c.acreage, reverse=True)
        item.total_acreage = round(item.total_acreage, 2)

    # Sort entities
    if sort == "parcels":
        items.sort(key=lambda e: e.parcel_count, reverse=(order == "desc"))
    elif sort == "name":
        items.sort(key=lambda e: e.entity.lower(), reverse=(order == "desc"))
    else:  # default: acreage
        items.sort(key=lambda e: e.total_acreage, reverse=(order == "desc"))

    total_acreage = round(sum(e.total_acreage for e in items), 2)
    total_parcels = sum(e.parcel_count for e in items)

    return RawLandSummary(
        items=items,
        total_acreage=total_acreage,
        total_parcels=total_parcels,
    )
