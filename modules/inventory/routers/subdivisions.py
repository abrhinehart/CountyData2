"""Subdivision management -- list, import GeoJSON polygons, trigger parcel relinking."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import from_shape
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.validation import make_valid
from sqlalchemy import func
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import County, Parcel, Subdivision
from modules.inventory.schemas.subdivision import (
    GeoJSONImportRequest,
    SubdivisionGeometryUpdate,
    SubdivisionImportResult,
    SubdivisionOut,
)
from modules.inventory.services.subdivision_linker import link_parcels_to_subdivisions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subdivisions", tags=["subdivisions"])


def _to_multipolygon(geojson_geom: dict) -> MultiPolygon | None:
    """Convert a GeoJSON geometry dict to a valid Shapely MultiPolygon."""
    try:
        geom = shape(geojson_geom)
    except Exception:
        return None

    if not geom.is_valid:
        geom = make_valid(geom)

    if geom.is_empty:
        return None

    if geom.geom_type == "Polygon":
        return MultiPolygon([geom])
    if geom.geom_type == "MultiPolygon":
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        flat = []
        for p in polys:
            if p.geom_type == "MultiPolygon":
                flat.extend(p.geoms)
            else:
                flat.append(p)
        return MultiPolygon(flat) if flat else None

    return None


@router.get("", response_model=list[SubdivisionOut])
def list_subdivisions(
    county_id: int | None = None,
    has_geometry: bool | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    """List subdivisions with geometry status and parcel count."""
    parcel_count = func.count(Parcel.id).label("parcel_count")

    q = (
        db.query(
            Subdivision.id,
            Subdivision.name,
            Subdivision.county_id,
            County.name.label("county_name"),
            (Subdivision.geom.isnot(None)).label("has_geometry"),
            parcel_count,
            Subdivision.created_at,
            Subdivision.updated_at,
        )
        .join(County, County.id == Subdivision.county_id)
        .outerjoin(Parcel, (Parcel.subdivision_id == Subdivision.id) & (Parcel.is_active == True))
        .group_by(Subdivision.id, County.name)
    )

    if county_id is not None:
        q = q.filter(Subdivision.county_id == county_id)

    if has_geometry is True:
        q = q.filter(Subdivision.geom.isnot(None))
    elif has_geometry is False:
        q = q.filter(Subdivision.geom.is_(None))

    if search:
        q = q.filter(Subdivision.name.ilike(f"%{search}%"))

    q = q.order_by(Subdivision.name)

    return [
        SubdivisionOut(
            id=row.id,
            name=row.name,
            county_id=row.county_id,
            county_name=row.county_name,
            has_geometry=bool(row.has_geometry),
            parcel_count=row.parcel_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in q.all()
    ]


@router.post("/import/geojson", response_model=SubdivisionImportResult)
def import_geojson(data: GeoJSONImportRequest, db: Session = Depends(get_db)):
    """Import subdivision polygons from a GeoJSON FeatureCollection.

    Each feature must have a `name` property. The geometry is normalized to
    MultiPolygon and upserted by (name, county_id). After import, runs the
    subdivision linker to assign unlinked parcels.
    """
    county = db.get(County, data.county_id)
    if not county:
        raise HTTPException(404, f"County {data.county_id} not found")

    created = 0
    updated = 0
    skipped = 0
    errors: list[str] = []

    for i, feature in enumerate(data.features):
        name = feature.properties.get("name") or feature.properties.get("NAME")
        if not name or not str(name).strip():
            skipped += 1
            continue
        name = str(name).strip()

        mp = _to_multipolygon(feature.geometry)
        if mp is None:
            errors.append(f"Feature {i} ({name}): invalid or empty geometry")
            continue

        geom_wkb = from_shape(mp, srid=4326)

        existing = (
            db.query(Subdivision)
            .filter(
                func.upper(Subdivision.name) == name.upper(),
                Subdivision.county_id == data.county_id,
            )
            .first()
        )

        if existing:
            existing.geom = geom_wkb
            updated += 1
        else:
            db.add(Subdivision(name=name, county_id=data.county_id, geom=geom_wkb))
            created += 1

    db.commit()

    # Run linker to assign unlinked parcels
    parcels_linked = 0
    try:
        parcels_linked = link_parcels_to_subdivisions(data.county_id, db)
    except Exception as e:
        logger.warning(f"Subdivision linker failed for county {data.county_id}: {e}")

    return SubdivisionImportResult(
        created=created,
        updated=updated,
        skipped=skipped,
        errors=errors,
        parcels_linked=parcels_linked,
    )


@router.put("/{subdivision_id}/geometry", response_model=SubdivisionImportResult)
def update_geometry(
    subdivision_id: int,
    data: SubdivisionGeometryUpdate,
    db: Session = Depends(get_db),
):
    """Update the polygon geometry for a single subdivision."""
    sub = db.get(Subdivision, subdivision_id)
    if not sub:
        raise HTTPException(404, "Subdivision not found")

    mp = _to_multipolygon(data.geometry)
    if mp is None:
        raise HTTPException(422, "Invalid or empty geometry")

    sub.geom = from_shape(mp, srid=4326)
    db.commit()

    parcels_linked = 0
    try:
        parcels_linked = link_parcels_to_subdivisions(sub.county_id, db)
    except Exception as e:
        logger.warning(f"Subdivision linker failed: {e}")

    return SubdivisionImportResult(
        created=0, updated=1, skipped=0, errors=[], parcels_linked=parcels_linked,
    )


@router.delete("/{subdivision_id}/geometry", status_code=204)
def clear_geometry(subdivision_id: int, db: Session = Depends(get_db)):
    """Remove the polygon geometry from a subdivision (keeps the name record)."""
    sub = db.get(Subdivision, subdivision_id)
    if not sub:
        raise HTTPException(404, "Subdivision not found")
    sub.geom = None
    db.commit()


@router.post("/relink/{county_id}")
def relink_county(county_id: int, db: Session = Depends(get_db)):
    """Trigger the subdivision linker for a county to assign unlinked parcels."""
    county = db.get(County, county_id)
    if not county:
        raise HTTPException(404, "County not found")

    linked = link_parcels_to_subdivisions(county_id, db)
    return {"county": county.name, "parcels_linked": linked}
