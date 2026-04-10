import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import Builder, County, Parcel, Subdivision
from modules.inventory.schemas.parcel import ParcelOut, ParcelPage

router = APIRouter(prefix="/parcels", tags=["parcels"])

VALID_PARCEL_CLASSES = {"lot", "common_area", "tract", "other"}
VALID_ENTITY_TYPES = {"builder", "developer", "land_banker", "btr"}


def _build_parcel_query(
    db: Session,
    county_id: int | None = None,
    entity_type: list[str] | None = None,
    parcel_class: list[str] | None = None,
    subdivision_id: int | None = None,
    builder_id: int | None = None,
    search: str | None = None,
    sort: str = "last_changed",
    order: str = "desc",
):
    """Build a fully filtered/sorted parcel query (no pagination)."""
    q = (
        db.query(
            Parcel.id,
            Parcel.parcel_number,
            County.name.label("county"),
            Builder.canonical_name.label("entity"),
            Subdivision.name.label("subdivision"),
            Parcel.owner_name,
            Parcel.site_address,
            Parcel.use_type,
            Parcel.acreage,
            Parcel.lot_width_ft,
            Parcel.lot_depth_ft,
            Parcel.lot_area_sqft,
            Parcel.building_value,
            Parcel.appraised_value,
            Parcel.deed_date,
            Parcel.previous_owner,
            Parcel.parcel_class,
            Parcel.is_active,
            Parcel.first_seen,
            Parcel.last_seen,
            Parcel.last_changed,
        )
        .join(County, County.id == Parcel.county_id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .outerjoin(Subdivision, Subdivision.id == Parcel.subdivision_id)
        .filter(Parcel.is_active == True)
    )

    if county_id is not None:
        q = q.filter(Parcel.county_id == county_id)

    classes = [c for c in (parcel_class or []) if c in VALID_PARCEL_CLASSES]
    if classes:
        q = q.filter(Parcel.parcel_class.in_(classes))

    types = [t for t in (entity_type or []) if t in VALID_ENTITY_TYPES]
    if types:
        q = q.filter(Builder.type.in_(types))

    if subdivision_id is not None:
        q = q.filter(Parcel.subdivision_id == subdivision_id)

    if builder_id is not None:
        q = q.filter(Parcel.builder_id == builder_id)

    if search:
        pattern = f"%{search}%"
        q = q.filter(
            Parcel.parcel_number.ilike(pattern)
            | Parcel.owner_name.ilike(pattern)
            | Parcel.site_address.ilike(pattern)
        )

    # Sorting
    sort_cols = {
        "parcel_number": Parcel.parcel_number,
        "owner_name": Parcel.owner_name,
        "site_address": Parcel.site_address,
        "acreage": Parcel.acreage,
        "building_value": Parcel.building_value,
        "appraised_value": Parcel.appraised_value,
        "deed_date": Parcel.deed_date,
        "first_seen": Parcel.first_seen,
        "last_changed": Parcel.last_changed,
    }
    sort_col = sort_cols.get(sort, Parcel.last_changed)
    q = q.order_by(sort_col.desc() if order == "desc" else sort_col.asc())

    return q


@router.get("", response_model=ParcelPage)
def list_parcels(
    county_id: int | None = None,
    entity_type: list[str] = Query(default=[]),
    parcel_class: list[str] = Query(default=[]),
    subdivision_id: int | None = None,
    builder_id: int | None = None,
    search: str | None = None,
    sort: str = "last_changed",
    order: str = "desc",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = _build_parcel_query(
        db, county_id, entity_type, parcel_class,
        subdivision_id, builder_id, search, sort, order,
    )

    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        ParcelOut(
            id=r.id,
            parcel_number=r.parcel_number,
            county=r.county,
            entity=r.entity,
            subdivision=r.subdivision,
            owner_name=r.owner_name,
            site_address=r.site_address,
            use_type=r.use_type,
            acreage=float(r.acreage) if r.acreage is not None else None,
            lot_width_ft=float(r.lot_width_ft) if r.lot_width_ft is not None else None,
            lot_depth_ft=float(r.lot_depth_ft) if r.lot_depth_ft is not None else None,
            lot_area_sqft=float(r.lot_area_sqft) if r.lot_area_sqft is not None else None,
            building_value=float(r.building_value) if r.building_value is not None else None,
            appraised_value=float(r.appraised_value) if r.appraised_value is not None else None,
            deed_date=r.deed_date,
            previous_owner=r.previous_owner,
            parcel_class=r.parcel_class,
            is_active=r.is_active,
            first_seen=r.first_seen,
            last_seen=r.last_seen,
            last_changed=r.last_changed,
        )
        for r in rows
    ]

    return ParcelPage(items=items, total=total, page=page, page_size=page_size)


CSV_COLUMNS = [
    "parcel_number", "county", "entity", "subdivision", "owner_name",
    "site_address", "use_type", "acreage", "lot_width_ft", "lot_depth_ft",
    "lot_area_sqft", "building_value", "appraised_value", "deed_date",
    "previous_owner", "parcel_class", "first_seen", "last_seen", "last_changed",
]

DECIMAL_FIELDS = {"acreage", "lot_width_ft", "lot_depth_ft", "lot_area_sqft",
                  "building_value", "appraised_value"}
DATETIME_FIELDS = {"deed_date", "first_seen", "last_seen", "last_changed"}


@router.get("/export")
def export_parcels(
    county_id: int | None = None,
    entity_type: list[str] = Query(default=[]),
    parcel_class: list[str] = Query(default=[]),
    subdivision_id: int | None = None,
    builder_id: int | None = None,
    search: str | None = None,
    sort: str = "last_changed",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    q = _build_parcel_query(
        db, county_id, entity_type, parcel_class,
        subdivision_id, builder_id, search, sort, order,
    )

    def _generate():
        buf = io.StringIO()
        writer = csv.writer(buf)

        # Header row
        writer.writerow(CSV_COLUMNS)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)

        for row in q.yield_per(500):
            vals = []
            for col in CSV_COLUMNS:
                v = getattr(row, col)
                if v is None:
                    vals.append("")
                elif col in DECIMAL_FIELDS:
                    vals.append(float(v))
                elif col in DATETIME_FIELDS:
                    vals.append(v.isoformat())
                else:
                    vals.append(v)
            writer.writerow(vals)
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="parcels.csv"'},
    )
