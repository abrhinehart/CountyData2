"""Orchestrates a full snapshot run for a county: query GIS, detect changes, store results."""

import json
import logging
import time
from datetime import datetime, timezone

from geoalchemy2.shape import from_shape
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, shape
from shapely.validation import make_valid
from sqlalchemy.orm import Session

from modules.inventory.models import (
    BiCountyConfig,
    BiParcelSnapshot,
    BiSnapshot,
    Builder,
    BuilderAlias,
    BuilderCounty,
    County,
    Parcel,
    Subdivision,
)
from modules.inventory.services.change_detect import compare_parcel
from modules.inventory.services.gis_query import AdaptiveDelay, ParsedParcel, build_engine_for_county
from modules.inventory.services.lot_dimensions import compute_lot_dimensions
from modules.inventory.services.parcel_classifier import classify_parcel
from modules.inventory.services.subdivision_linker import link_parcels_to_subdivisions

logger = logging.getLogger(__name__)


def _geojson_to_wkb(geojson_dict: dict | None):
    """Convert GeoJSON dict to WKB element for PostGIS storage."""
    if not geojson_dict:
        return None, None
    try:
        geom = shape(geojson_dict)
        # Heal invalid source geometry (ring self-intersections, etc.) before
        # handing WKB to PostGIS. County GIS layers occasionally serve invalid
        # polygons at a low rate; without this, ST_IsValid fails downstream
        # and spatial joins misbehave (post-merge-quirks.md Entry 3).
        if not geom.is_valid:
            geom = make_valid(geom)
        # make_valid can return a GeometryCollection containing degenerate
        # LineString/Point parts alongside the real Polygon(s). Keep only the
        # areal parts so the normalized MultiPolygon below stays well-formed
        # and matches the parcels.geom MULTIPOLYGON column constraint.
        if isinstance(geom, GeometryCollection):
            polys = [g for g in geom.geoms if isinstance(g, (Polygon, MultiPolygon))]
            if not polys:
                logger.warning("Geometry healed to non-areal parts only; dropping")
                return None, None
            geom = MultiPolygon(
                [p for g in polys for p in (g.geoms if isinstance(g, MultiPolygon) else [g])]
            )
        # Normalize to MultiPolygon for consistent storage
        if isinstance(geom, Polygon):
            geom = MultiPolygon([geom])
        centroid = geom.centroid
        return from_shape(geom, srid=4326), from_shape(centroid, srid=4326)
    except Exception as e:
        logger.warning(f"Failed to parse geometry: {e}")
        return None, None


ALIAS_DELAY_BASE = 0.3  # seconds — adaptive delay starts here


MAX_ALIAS_RETRIES = 3
ALIAS_RETRY_BACKOFF = 5.0  # seconds multiplier


def _run_alias_query_with_retries(query_fn, label: str, alias_delay: AdaptiveDelay):
    """Run a GIS alias query with bounded retries. Returns None after final failure."""
    for attempt in range(MAX_ALIAS_RETRIES):
        try:
            t0 = time.monotonic()
            results = query_fn()
            elapsed = time.monotonic() - t0
            alias_delay.record_success(elapsed)
            return results
        except Exception as e:
            logger.warning(f"GIS batch attempt {attempt+1}/{MAX_ALIAS_RETRIES} failed for '{label}': {e}")
            alias_delay.record_error()
            if attempt < MAX_ALIAS_RETRIES - 1:
                sleep_time = ALIAS_RETRY_BACKOFF * (attempt + 1)
                logger.info(f"Retrying batch '{label}' in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"GIS batch permanently failed for '{label}' after {MAX_ALIAS_RETRIES} attempts.")
    return None


def _query_builder_batch_with_fallback(
    engine,
    aliases: list[str],
    alias_delay: AdaptiveDelay,
) -> list[ParsedParcel]:
    """Query a builder's alias set, falling back to single-alias queries on batch failure."""
    batch_label = aliases[0] if len(aliases) == 1 else f"{aliases[0]}+{len(aliases)-1}"
    results = _run_alias_query_with_retries(
        lambda: engine.query_by_owner_batch(aliases),
        batch_label,
        alias_delay,
    )
    if results is not None:
        return results

    if len(aliases) <= 1:
        return []

    logger.warning(f"Falling back to single-alias queries for '{batch_label}'")
    deduped: dict[str, ParsedParcel] = {}
    for idx, alias in enumerate(aliases):
        alias_results = _run_alias_query_with_retries(
            lambda alias=alias: engine.query_by_owner(alias),
            alias,
            alias_delay,
        )
        if alias_results:
            for parcel in alias_results:
                deduped.setdefault(parcel.parcel_number, parcel)
        if idx < len(aliases) - 1:
            alias_delay.wait()

    logger.info(
        f"Fallback for '{batch_label}' recovered {len(deduped)} parcels across {len(aliases)} aliases"
    )
    return list(deduped.values())


def _parse_deed_date(raw: str | None):
    """Convert a deed date (epoch ms string or ISO) to a datetime."""
    if not raw:
        return None
    try:
        # ArcGIS returns dates as epoch milliseconds
        epoch_ms = float(raw)
        return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        pass
    return None


def _compute_dimensions(geojson_dict: dict | None):
    """Compute lot width/depth/area from GeoJSON. Returns (width, depth, area) or (None, None, None)."""
    if not geojson_dict:
        return None, None, None
    try:
        geom = shape(geojson_dict)
        dims = compute_lot_dimensions(geom)
        if dims:
            return dims.width_ft, dims.depth_ft, dims.area_sqft
    except Exception as e:
        logger.warning(f"Failed to compute lot dimensions: {e}")
    return None, None, None


def _resolve_subdivision(
    name: str, county_id: int, county_name: str, db: Session, cache: dict
) -> int | None:
    """Look up or auto-create a subdivision record. Returns subdivision_id.

    ``county_name`` is the legacy ``subdivisions.county`` TEXT NOT NULL column
    that the shared spine still requires (see post-merge-quirks.md Entry 1).
    """
    key = (name, county_id)
    if key in cache:
        return cache[key]
    sub = db.query(Subdivision).filter_by(name=name, county_id=county_id).first()
    if not sub:
        sub = Subdivision(
            name=name, county_id=county_id, county=county_name,
            classification="scattered",
        )
        db.add(sub)
        db.flush()
        logger.info(f"Auto-created subdivision '{name}' (scattered) for county {county_id}")
    cache[key] = sub.id
    return sub.id

def _build_summary_text(county_name: str, snapshot_id: int, db: Session) -> str:
    """Build a one-line human-readable change summary for a snapshot.

    Example: "Bay: +12 DR Horton, -3 Adams Homes, 2 changed Lennar"
    """
    from sqlalchemy import func

    # Flush pending INSERTs so the re-query below sees every BiParcelSnapshot
    # row this transaction just wrote. Without this, SQLAlchemy's identity map
    # can hold unflushed rows and the aggregate undercounts by 1+ per builder
    # (post-merge-quirks.md Entry 2).
    db.flush()

    rows = (
        db.query(
            Builder.canonical_name,
            BiParcelSnapshot.change_type,
            func.count(BiParcelSnapshot.id).label("cnt"),
        )
        .join(Parcel, Parcel.id == BiParcelSnapshot.parcel_id)
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(BiParcelSnapshot.snapshot_id == snapshot_id)
        .group_by(Builder.canonical_name, BiParcelSnapshot.change_type)
        .all()
    )

    if not rows:
        return f"{county_name}: no changes"

    # Aggregate per builder
    builder_stats: dict[str, dict[str, int]] = {}
    for name, change_type, cnt in rows:
        if name not in builder_stats:
            builder_stats[name] = {"new": 0, "removed": 0, "changed": 0}
        builder_stats[name][change_type] = cnt

    # Sort by total activity descending
    ranked = sorted(
        builder_stats.items(),
        key=lambda x: sum(x[1].values()),
        reverse=True,
    )

    parts = []
    for name, stats in ranked[:5]:  # top 5 movers
        pieces = []
        if stats["new"]:
            pieces.append(f"+{stats['new']}")
        if stats["removed"]:
            pieces.append(f"-{stats['removed']}")
        if stats["changed"]:
            pieces.append(f"{stats['changed']} chg")
        if pieces:
            parts.append(f"{'/'.join(pieces)} {name}")

    text = f"{county_name}: {', '.join(parts)}"
    if len(ranked) > 5:
        text += f" (+{len(ranked) - 5} more)"
    return text


def run_snapshot(county_id: int, db: Session) -> dict:
    """Run a full snapshot for one county. Returns summary dict."""
    now = datetime.now(timezone.utc)

    county = db.get(County, county_id)
    if not county:
        raise ValueError(f"County {county_id} not found")

    # Load the BI-specific GIS config for this county
    bi_config = db.query(BiCountyConfig).filter_by(county_id=county_id).first()
    engine = build_engine_for_county(county, bi_config)
    if not engine:
        raise ValueError(f"County '{county.name}' has no GIS endpoint configured")

    # Create snapshot row
    snapshot = BiSnapshot(county_id=county_id, started_at=now, status="running")
    db.add(snapshot)
    db.flush()

    try:
        # Load aliases scoped to this county
        # National builders: always included
        national = (
            db.query(BuilderAlias.alias, BuilderAlias.builder_id)
            .join(BuilderAlias.builder)
            .filter(Builder.is_active == True, Builder.scope == "national")
            .all()
        )
        # Regional/local builders: only if this county is in their list
        scoped = (
            db.query(BuilderAlias.alias, BuilderAlias.builder_id)
            .join(BuilderAlias.builder)
            .filter(
                Builder.is_active == True,
                Builder.scope != "national",
                Builder.id.in_(
                    db.query(BuilderCounty.builder_id)
                    .filter(BuilderCounty.county_id == county_id)
                ),
            )
            .all()
        )
        aliases = national + scoped

        logger.info(f"Snapshot for {county.name}: {len(aliases)} aliases")

        # Group aliases by builder for batched OR queries
        builder_aliases: dict[int, list[str]] = {}
        for alias_str, bid in aliases:
            builder_aliases.setdefault(bid, []).append(alias_str)

        builder_ids = list(builder_aliases.keys())
        logger.info(f"Snapshot for {county.name}: {len(aliases)} aliases across {len(builder_ids)} builders (batched)")

        # Set progress total for UI tracking
        snapshot.progress_total = len(builder_ids)
        db.commit()

        # Query GIS per builder (batched aliases), dedup by parcel_number
        gis_parcels: dict[str, tuple[ParsedParcel, int]] = {}
        alias_delay = AdaptiveDelay(base=ALIAS_DELAY_BASE)
        for i, bid in enumerate(builder_ids):
            batch = builder_aliases[bid]
            results = _query_builder_batch_with_fallback(engine, batch, alias_delay)

            if results:
                for p in results:
                    if p.parcel_number not in gis_parcels:
                        gis_parcels[p.parcel_number] = (p, bid)

            snapshot.progress_current = i + 1
            db.commit()

            # Adaptive rate limit: pause between builders (not after the last one)
            if i < len(builder_ids) - 1:
                alias_delay.wait()

        # Load existing parcels for this county
        db_parcels_list = db.query(Parcel).filter_by(county_id=county_id).all()
        db_parcels = {p.parcel_number: p for p in db_parcels_list}

        gis_keys = set(gis_parcels.keys())
        db_keys = set(db_parcels.keys())

        new_keys = gis_keys - db_keys
        removed_keys = {k for k in (db_keys - gis_keys) if db_parcels[k].is_active}
        existing_keys = gis_keys & db_keys

        new_count = 0
        removed_count = 0
        changed_count = 0
        unchanged_count = 0
        subdivision_cache: dict[tuple[str, int], int] = {}

        # Process NEW parcels
        for key in new_keys:
            parsed, builder_id = gis_parcels[key]
            geom_wkb, centroid_wkb = _geojson_to_wkb(parsed.geometry)
            lot_w, lot_d, lot_a = _compute_dimensions(parsed.geometry)

            sub_id = None
            if parsed.subdivision_name:
                sub_id = _resolve_subdivision(
                    parsed.subdivision_name, county_id, county.name, db, subdivision_cache
                )

            parcel = Parcel(
                parcel_number=parsed.parcel_number,
                county_id=county_id,
                builder_id=builder_id,
                subdivision_id=sub_id,
                owner_name=parsed.owner_name,
                site_address=parsed.site_address,
                use_type=parsed.use_type,
                acreage=parsed.acreage,
                parcel_class=classify_parcel(parsed.use_type, parsed.acreage),
                lot_width_ft=lot_w,
                lot_depth_ft=lot_d,
                lot_area_sqft=lot_a,
                building_value=parsed.building_value,
                appraised_value=parsed.appraised_value,
                deed_date=_parse_deed_date(parsed.deed_date),
                previous_owner=parsed.previous_owner,
                geom=geom_wkb,
                centroid=centroid_wkb,
                is_active=True,
                first_seen=now,
                last_seen=now,
                last_changed=now,
            )
            db.add(parcel)
            db.flush()

            db.add(BiParcelSnapshot(
                parcel_id=parcel.id,
                snapshot_id=snapshot.id,
                change_type="new",
                new_values={
                    "owner_name": parsed.owner_name,
                    "site_address": parsed.site_address,
                    "use_type": parsed.use_type,
                    "acreage": str(parsed.acreage) if parsed.acreage else None,
                },
            ))
            new_count += 1

        # Process REMOVED parcels
        for key in removed_keys:
            parcel = db_parcels[key]
            parcel.is_active = False

            db.add(BiParcelSnapshot(
                parcel_id=parcel.id,
                snapshot_id=snapshot.id,
                change_type="removed",
                old_values={
                    "owner_name": parcel.owner_name,
                    "site_address": parcel.site_address,
                    "use_type": parcel.use_type,
                    "acreage": str(parcel.acreage) if parcel.acreage else None,
                },
            ))
            removed_count += 1

        # Process EXISTING parcels
        for key in existing_keys:
            parsed, builder_id = gis_parcels[key]
            parcel = db_parcels[key]

            # Always update last_seen
            parcel.last_seen = now

            # Always update geometry and lot dimensions
            geom_wkb, centroid_wkb = _geojson_to_wkb(parsed.geometry)
            if geom_wkb:
                parcel.geom = geom_wkb
                parcel.centroid = centroid_wkb
            lot_w, lot_d, lot_a = _compute_dimensions(parsed.geometry)
            if lot_w is not None:
                parcel.lot_width_ft = lot_w
                parcel.lot_depth_ft = lot_d
                parcel.lot_area_sqft = lot_a

            # Always update subdivision from GIS field if available
            if parsed.subdivision_name and not parcel.subdivision_id:
                parcel.subdivision_id = _resolve_subdivision(
                    parsed.subdivision_name, county_id, county.name, db, subdivision_cache
                )

            # Always update value/deed fields (these change over time)
            parcel.building_value = parsed.building_value
            parcel.appraised_value = parsed.appraised_value
            if parsed.deed_date:
                parcel.deed_date = _parse_deed_date(parsed.deed_date)
            if parsed.previous_owner:
                parcel.previous_owner = parsed.previous_owner

            # Reactivate if previously removed
            if not parcel.is_active:
                parcel.is_active = True
                parcel.owner_name = parsed.owner_name
                parcel.site_address = parsed.site_address
                parcel.use_type = parsed.use_type
                parcel.acreage = parsed.acreage
                parcel.parcel_class = classify_parcel(parsed.use_type, parsed.acreage)
                parcel.builder_id = builder_id
                parcel.last_changed = now

                db.add(BiParcelSnapshot(
                    parcel_id=parcel.id,
                    snapshot_id=snapshot.id,
                    change_type="new",
                    new_values={
                        "owner_name": parsed.owner_name,
                        "site_address": parsed.site_address,
                        "use_type": parsed.use_type,
                        "acreage": str(parsed.acreage) if parsed.acreage else None,
                    },
                ))
                new_count += 1
                continue

            # Check for field changes
            diff = compare_parcel(parcel, parsed, builder_id)
            if diff:
                parcel.owner_name = parsed.owner_name
                parcel.site_address = parsed.site_address
                parcel.use_type = parsed.use_type
                parcel.acreage = parsed.acreage
                parcel.parcel_class = classify_parcel(parsed.use_type, parsed.acreage)
                parcel.builder_id = builder_id
                parcel.last_changed = now

                db.add(BiParcelSnapshot(
                    parcel_id=parcel.id,
                    snapshot_id=snapshot.id,
                    change_type="changed",
                    old_values=diff["old_values"],
                    new_values=diff["new_values"],
                ))
                changed_count += 1
            else:
                unchanged_count += 1

        # Update snapshot
        snapshot.status = "completed"
        snapshot.completed_at = datetime.now(timezone.utc)
        snapshot.total_parcels_queried = len(gis_parcels)
        snapshot.new_count = new_count
        snapshot.removed_count = removed_count
        snapshot.changed_count = changed_count
        snapshot.unchanged_count = unchanged_count

        # Generate human-readable summary text
        snapshot.summary_text = _build_summary_text(
            county.name, snapshot.id, db,
        )

        db.commit()

        # Link new parcels to subdivisions via point-in-polygon
        try:
            linked = link_parcels_to_subdivisions(county_id, db)
            if linked:
                logger.info(f"Linked {linked} parcels to subdivisions for {county.name}")
        except Exception as e:
            logger.warning(f"Subdivision linkage failed for {county.name}: {e}")

        summary = {
            "snapshot_id": snapshot.id,
            "county": county.name,
            "status": "completed",
            "total_queried": len(gis_parcels),
            "new": new_count,
            "removed": removed_count,
            "changed": changed_count,
            "unchanged": unchanged_count,
        }
        logger.info(f"Snapshot complete for {county.name}: {summary}")
        return summary

    except Exception as e:
        snapshot.status = "failed"
        snapshot.error_message = str(e)
        snapshot.completed_at = datetime.now(timezone.utc)
        db.commit()
        logger.error(f"Snapshot failed for {county.name}: {e}")
        raise
