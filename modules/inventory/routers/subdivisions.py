"""Subdivision management -- list, import GeoJSON polygons, trigger parcel relinking."""

import collections
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import MultiPolygon, Polygon, mapping, shape
from shapely.validation import make_valid
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import Builder, County, Parcel, Subdivision
from modules.inventory.schemas.subdivision import (
    GeoJSONImportRequest,
    SubdivisionBuilderSummary,
    SubdivisionGeoFeature,
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
    relevant_only: bool = False,
    builder_active_only: bool = True,
    db: Session = Depends(get_db),
):
    """List subdivisions with geometry status and parcel count.

    builder_active_only (default True): only return subdivisions where a builder
    has owned at least one lot — either currently active, or last seen within the
    past 5 years.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=5 * 365)

    # Pre-compute set of builder-active subdivision IDs (fast index scan)
    if builder_active_only:
        ba_q = (
            db.query(Parcel.subdivision_id)
            .filter(
                Parcel.subdivision_id.isnot(None),
                Parcel.builder_id.isnot(None),
                or_(
                    Parcel.is_active == True,  # noqa: E712
                    Parcel.last_seen >= cutoff,
                ),
            )
            .distinct()
        )
        if county_id is not None:
            ba_q = ba_q.filter(Parcel.county_id == county_id)
        builder_active_ids = {row[0] for row in ba_q.all()}
    else:
        builder_active_ids = None

    # Count ALL active parcels (total)
    parcel_count = func.count(Parcel.id).label("parcel_count")
    # Count only builder-owned active parcels
    builder_lot_count = func.count(
        case((Parcel.builder_id.isnot(None), Parcel.id))
    ).label("builder_lot_count")
    # Count distinct builders with active parcels
    distinct_builder_count = func.count(
        func.distinct(case((Parcel.builder_id.isnot(None), Parcel.builder_id)))
    ).label("distinct_builder_count")

    q = (
        db.query(
            Subdivision.id,
            Subdivision.name,
            Subdivision.county_id,
            County.name.label("county_name"),
            (Subdivision.geom.isnot(None)).label("has_geometry"),
            parcel_count,
            builder_lot_count,
            distinct_builder_count,
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

    if relevant_only:
        q = q.filter(Subdivision.is_relevant == True)  # noqa: E712

    if builder_active_ids is not None:
        if not builder_active_ids:
            return []
        q = q.filter(Subdivision.id.in_(builder_active_ids))

    q = q.order_by(builder_lot_count.desc(), Subdivision.name)

    return [
        SubdivisionOut(
            id=row.id,
            name=row.name,
            county_id=row.county_id,
            county_name=row.county_name,
            has_geometry=bool(row.has_geometry),
            parcel_count=row.parcel_count,
            builder_lot_count=row.builder_lot_count,
            distinct_builder_count=row.distinct_builder_count,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in q.all()
    ]


@router.get("/geojson", response_model=list[SubdivisionGeoFeature])
def get_subdivisions_geojson(
    county_id: int | None = None,
    builder_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Return all builder-active subdivisions with geometry and per-builder lot breakdowns.

    Designed for the map page so it can load all polygons in a single request
    instead of making 300+ individual fetches.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=5 * 365)

    # Pre-compute builder-active subdivision IDs (same logic as list_subdivisions)
    ba_q = (
        db.query(Parcel.subdivision_id)
        .filter(
            Parcel.subdivision_id.isnot(None),
            Parcel.builder_id.isnot(None),
            or_(
                Parcel.is_active == True,  # noqa: E712
                Parcel.last_seen >= cutoff,
            ),
        )
        .distinct()
    )
    if county_id is not None:
        ba_q = ba_q.filter(Parcel.county_id == county_id)
    if builder_id is not None:
        ba_q = ba_q.filter(Parcel.builder_id == builder_id)
    builder_active_ids = {row[0] for row in ba_q.all()}

    if not builder_active_ids:
        return []

    # Fetch subdivisions that have geometry AND are builder-active
    subs_q = (
        db.query(
            Subdivision.id,
            Subdivision.name,
            Subdivision.county_id,
            County.name.label("county_name"),
            Subdivision.geom,
        )
        .join(County, County.id == Subdivision.county_id)
        .filter(
            Subdivision.id.in_(builder_active_ids),
            Subdivision.geom.isnot(None),
        )
    )
    if county_id is not None:
        subs_q = subs_q.filter(Subdivision.county_id == county_id)

    subdivisions = subs_q.all()
    if not subdivisions:
        return []

    sub_ids = [row.id for row in subdivisions]

    # Query per-builder lot counts grouped by subdivision
    builder_counts_q = (
        db.query(
            Parcel.subdivision_id,
            Parcel.builder_id,
            Builder.canonical_name.label("builder_name"),
            func.count(Parcel.id).label("lot_count"),
        )
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(
            Parcel.subdivision_id.in_(sub_ids),
            Parcel.builder_id.isnot(None),
            or_(
                Parcel.is_active == True,  # noqa: E712
                Parcel.last_seen >= cutoff,
            ),
        )
        .group_by(Parcel.subdivision_id, Parcel.builder_id, Builder.canonical_name)
    )
    if builder_id is not None:
        builder_counts_q = builder_counts_q.filter(Parcel.builder_id == builder_id)

    # Group builder data by subdivision_id
    builders_by_sub: dict[int, list[SubdivisionBuilderSummary]] = collections.defaultdict(list)
    for row in builder_counts_q.all():
        builders_by_sub[row.subdivision_id].append(
            SubdivisionBuilderSummary(
                builder_id=row.builder_id,
                builder_name=row.builder_name,
                lot_count=row.lot_count,
            )
        )

    # Build response features
    features: list[SubdivisionGeoFeature] = []
    for row in subdivisions:
        builders = builders_by_sub.get(row.id, [])
        builder_lot_count = sum(b.lot_count for b in builders)
        distinct_builder_count = len(builders)

        try:
            geojson_geom = mapping(to_shape(row.geom))
        except Exception:
            continue  # skip subdivisions whose geometry can't be converted

        features.append(
            SubdivisionGeoFeature(
                id=row.id,
                name=row.name,
                county_id=row.county_id,
                county_name=row.county_name,
                builder_lot_count=builder_lot_count,
                distinct_builder_count=distinct_builder_count,
                builders=builders,
                geojson=dict(geojson_geom),
            )
        )

    return features


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
            db.add(Subdivision(
                name=name,
                county_id=data.county_id,
                county=county.name,
                geom=geom_wkb,
            ))
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
