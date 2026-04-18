"""
api.py - Unified Real Estate Intelligence Platform.

FastAPI application factory. Each module registers its own router.

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 1460
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.database import pool


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(title="Real Estate Intelligence Platform")

_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:1560,http://localhost:1460").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Module routers
# ---------------------------------------------------------------------------

from modules.sales.router import router as sales_router  # noqa: E402
from modules.inventory.router import router as inventory_router  # noqa: E402
from modules.permits.router import router as permits_router  # noqa: E402
from modules.commission.router import router as commission_router  # noqa: E402
from modules.estoppels.router import router as estoppels_router  # noqa: E402

app.include_router(sales_router)
app.include_router(inventory_router)
app.include_router(permits_router)
app.include_router(commission_router)
app.include_router(estoppels_router)


# ---------------------------------------------------------------------------
# Platform-level endpoints
# ---------------------------------------------------------------------------

@app.get("/api/platform/health")
def health_check():
    """Verify database connectivity and return module status."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    finally:
        pool.putconn(conn)

    return {
        "status": "ok",
        "modules": {
            "sales": "active",
            "inventory": "active",
            "permits": "active",
            "commission": "active",
        },
    }


@app.get("/api/platform/modules")
def list_modules():
    """List all registered modules and their route prefixes."""
    modules = []
    for route in app.routes:
        if hasattr(route, "tags") and route.tags:
            tag = route.tags[0]
            if tag not in [m["name"] for m in modules]:
                modules.append({"name": tag, "status": "active"})
    return {"modules": modules}


@app.get("/api/platform/geometry-coverage")
def geometry_coverage():
    """Per-county subdivision and parcel geometry coverage stats."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                WITH sub_cov AS (
                    SELECT s.county_id,
                           COUNT(*)                                        AS total,
                           COUNT(*) FILTER (WHERE s.geom IS NOT NULL)      AS with_geom,
                           COUNT(*) FILTER (WHERE s.geom IS NULL)          AS without_geom
                      FROM subdivisions s
                     WHERE s.is_active = true
                     GROUP BY s.county_id
                ),
                parcel_cov AS (
                    SELECT p.county_id,
                           COUNT(*)                                        AS parcel_total,
                           COUNT(*) FILTER (WHERE p.geom IS NOT NULL)      AS parcel_with_geom,
                           COUNT(*) FILTER (WHERE p.geom IS NULL)          AS parcel_without_geom
                      FROM parcels p
                     WHERE p.is_active = true
                     GROUP BY p.county_id
                )
                SELECT c.name                               AS county,
                       COALESCE(s.total, 0)                 AS total,
                       COALESCE(s.with_geom, 0)             AS with_geom,
                       COALESCE(s.without_geom, 0)          AS without_geom,
                       COALESCE(p.parcel_total, 0)          AS parcel_total,
                       COALESCE(p.parcel_with_geom, 0)      AS parcel_with_geom,
                       COALESCE(p.parcel_without_geom, 0)   AS parcel_without_geom
                  FROM counties c
             LEFT JOIN sub_cov s    ON s.county_id = c.id
             LEFT JOIN parcel_cov p ON p.county_id = c.id
                 WHERE COALESCE(s.total, 0) > 0 OR COALESCE(p.parcel_total, 0) > 0
                 ORDER BY c.name
            """)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)
    return {"rows": rows}


@app.get("/api/platform/bi-snapshot-health")
def bi_snapshot_health():
    """Latest BI snapshot per county."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT ON (c.name)
                       c.name                       AS county,
                       s.started_at,
                       s.completed_at,
                       s.status,
                       s.total_parcels_queried,
                       s.new_count,
                       s.changed_count,
                       s.error_message
                  FROM bi_snapshots s
                  JOIN counties c ON c.id = s.county_id
                 ORDER BY c.name, s.started_at DESC
            """)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)
    return {"rows": rows}


@app.get("/api/platform/pt-scrape-health")
def pt_scrape_health():
    """Recent PT scrape jobs."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id,
                       jurisdiction_name,
                       status,
                       trigger_type,
                       queued_at,
                       started_at,
                       finished_at,
                       last_error,
                       attempt_count,
                       max_attempts
                  FROM pt_scrape_jobs
                 ORDER BY queued_at DESC
                 LIMIT 50
            """)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)
    return {"rows": rows}


@app.get("/api/platform/cr-document-health")
def cr_document_health():
    """CR source document stats grouped by jurisdiction."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT j.name                                                        AS jurisdiction,
                       COUNT(*)                                                      AS total_documents,
                       COUNT(*) FILTER (WHERE d.extraction_successful = true)        AS extracted_ok,
                       COUNT(*) FILTER (WHERE d.extraction_successful = false)       AS extracted_fail,
                       COUNT(*) FILTER (WHERE d.extraction_attempted = false)        AS not_attempted,
                       MAX(d.meeting_date)                                           AS latest_meeting
                  FROM cr_source_documents d
                  JOIN jurisdictions j ON j.id = d.jurisdiction_id
                 GROUP BY j.name
                 ORDER BY j.name
            """)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)
    return {"rows": rows}


# ---------------------------------------------------------------------------
# Status Matrix — jurisdiction × status dashboard
# ---------------------------------------------------------------------------

# Platform buckets per module (for api-map discovery in docs/api-maps/)
_MAP_PLATFORMS = {
    "cd2": ("landmark", "oncore", "acclaimweb", "tyler-selfservice", "records-portal", "clerk"),
    "bi":  ("arcgis",),
    "pt":  ("cityview", "iworq", "accela", "mgo-connect", "tyler-energov", "permittrax", "bitco"),
    "cr":  ("civicplus", "civicclerk", "legistar", "novusagenda", "escribe", "granicus",
            "granicus-viewpublisher", "civicweb", "icompass"),
}

_API_MAPS_DIR = Path(__file__).parent / "docs" / "api-maps"
_REGISTRY_PATH = Path(__file__).parent / "county-registry.yaml"


def _slug(name: str, juris_type: str | None) -> str:
    """Return the api-map filename slug for a jurisdiction.

    County rows use `<name>-county`, city rows use `<name>` (hyphen-lowered).
    Matches the existing convention in docs/api-maps/.
    """
    base = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    if juris_type == "county":
        return f"{base}-county" if not base.endswith("-county") else base
    return base


def _scan_api_maps() -> dict[str, dict[str, tuple[str, float]]]:
    """Return {slug: {platform_bucket: (filename, mtime_epoch)}} — freshest per bucket."""
    result: dict[str, dict[str, tuple[str, float]]] = {}
    if not _API_MAPS_DIR.exists():
        return result
    for path in _API_MAPS_DIR.glob("*.md"):
        stem = path.stem
        mtime = path.stat().st_mtime
        # Match longest platform token suffix
        for bucket, tokens in _MAP_PLATFORMS.items():
            for tok in tokens:
                suffix = f"-{tok}"
                if stem.endswith(suffix):
                    slug = stem[: -len(suffix)]
                    entry = result.setdefault(slug, {})
                    existing = entry.get(bucket)
                    if existing is None or mtime > existing[1]:
                        entry[bucket] = (path.name, mtime)
                    break
    return result


def _load_registry_slugs() -> dict[str, set[str]]:
    """Return {slug: set_of_documented_projects} from county-registry.yaml.

    A county counts as having a project documented when its `projects.<mod>` block
    is a dict with at least a `status` or `portal` key (not empty / not a stub).
    """
    result: dict[str, set[str]] = {}
    if not _REGISTRY_PATH.exists():
        return result
    try:
        data = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return result
    for slug, entry in (data.get("counties") or {}).items():
        if not isinstance(entry, dict):
            continue
        projects = entry.get("projects") or {}
        docs = set()
        for proj_key, proj_val in projects.items():
            if isinstance(proj_val, dict) and (proj_val.get("status") or proj_val.get("portal") or proj_val.get("platform")):
                docs.add(proj_key)
        if docs:
            result[slug] = docs
    return result


def _age_days(ts) -> float | None:
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        delta = datetime.now(timezone.utc).timestamp() - ts
        return delta / 86400.0
    # Promote date -> datetime if needed
    if not hasattr(ts, "tzinfo"):
        from datetime import datetime as _dt
        ts = _dt.combine(ts, _dt.min.time()).replace(tzinfo=timezone.utc)
    elif ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - ts).total_seconds() / 86400.0


@app.get("/api/platform/status-matrix")
def status_matrix():
    """Counties × jurisdictions status dashboard.

    Returns a nested structure grouped by state → county → jurisdictions. Each
    row carries precomputed cell values for the HealthPage matrix:
      - doc              binary   (county-registry.yaml has real projects block)
      - cd2/bi/pt/cr     "green" | "yellow" | "red" | "na"
      - cd2_map/bi_map/pt_map/cr_map  {age_days, filename} | null
      - sub_pct          float 0-1 | null
      - parcel_pct       float 0-1 | null
      - roster           "yes" | "no" | "na"
      - last_run_days    int | null  (newest of PT / BI / CR activity)
    """
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.name, c.state, c.is_active,
                       (SELECT COUNT(*) FROM transactions t
                         WHERE UPPER(t.county) = UPPER(c.name))                           AS cd2_count,
                       (SELECT MAX(t.date) FROM transactions t
                         WHERE UPPER(t.county) = UPPER(c.name))                           AS cd2_last_date,
                       EXISTS(SELECT 1 FROM bi_county_config bc
                                WHERE bc.county_id = c.id AND bc.gis_endpoint IS NOT NULL) AS bi_has_config,
                       (SELECT MAX(s.completed_at) FROM bi_snapshots s
                         WHERE s.county_id = c.id AND s.status = 'completed')             AS bi_last_completed,
                       (SELECT COUNT(*) FROM subdivisions s
                         WHERE s.county_id = c.id AND s.is_active)                        AS sub_total,
                       (SELECT COUNT(*) FROM subdivisions s
                         WHERE s.county_id = c.id AND s.is_active AND s.geom IS NOT NULL) AS sub_with_geom,
                       (SELECT COUNT(*) FROM parcels p
                         WHERE p.county_id = c.id AND p.is_active)                        AS parcel_total,
                       (SELECT COUNT(*) FROM parcels p
                         WHERE p.county_id = c.id AND p.is_active AND p.geom IS NOT NULL) AS parcel_with_geom
                  FROM counties c
              ORDER BY COALESCE(c.state, 'ZZ'), c.name
            """)
            county_cols = [d[0] for d in cur.description]
            county_rows = [dict(zip(county_cols, r)) for r in cur.fetchall()]

            cur.execute("""
                SELECT j.id, j.name, j.county_id, j.jurisdiction_type, j.is_active,
                       EXISTS(SELECT 1 FROM pt_jurisdiction_config pc
                                WHERE pc.jurisdiction_id = j.id
                                  AND pc.scrape_mode = 'live')                             AS pt_live,
                       EXISTS(SELECT 1 FROM pt_jurisdiction_config pc
                                WHERE pc.jurisdiction_id = j.id)                           AS pt_has_config,
                       (SELECT MAX(r.run_at) FROM pt_scrape_runs r
                         WHERE r.jurisdiction_id = j.id AND r.status = 'completed')        AS pt_last_run,
                       EXISTS(SELECT 1 FROM cr_jurisdiction_config cc
                                WHERE cc.jurisdiction_id = j.id)                           AS cr_has_config,
                       (SELECT MAX(d.created_at) FROM cr_source_documents d
                         WHERE d.jurisdiction_id = j.id AND d.extraction_successful)       AS cr_last_success,
                       (SELECT COUNT(*) FROM cr_commissioners cm
                         WHERE cm.jurisdiction_id = j.id AND cm.active)                    AS roster_count,
                       (SELECT MIN(cm.commission_type) FROM cr_jurisdiction_config cm
                         WHERE cm.jurisdiction_id = j.id)                                  AS commission_type
                  FROM jurisdictions j
                 WHERE j.is_active = true
              ORDER BY j.county_id, j.name
            """)
            juris_cols = [d[0] for d in cur.description]
            juris_rows = [dict(zip(juris_cols, r)) for r in cur.fetchall()]
    finally:
        pool.putconn(conn)

    maps = _scan_api_maps()
    registry = _load_registry_slugs()
    jur_by_county: dict[int, list[dict]] = {}
    for j in juris_rows:
        jur_by_county.setdefault(j["county_id"], []).append(j)

    def _pct(num, den):
        return (num / den) if den else None

    def _module_status(has_config: bool, last_activity_days: float | None,
                       green_days: int = 60, yellow_days: int = 180) -> str:
        if not has_config:
            return "red"
        if last_activity_days is None:
            return "yellow"
        if last_activity_days <= green_days:
            return "green"
        if last_activity_days <= yellow_days:
            return "yellow"
        return "red"

    def _map_cell(slug: str, bucket: str) -> dict | None:
        entry = maps.get(slug, {}).get(bucket)
        if not entry:
            return None
        filename, mtime = entry
        return {"filename": filename, "age_days": _age_days(mtime)}

    states: dict[str, dict] = {}
    for c in county_rows:
        state = c["state"] or "??"
        slug = _slug(c["name"], "county")
        registry_has = slug.replace("-county", "") in registry or slug in registry
        # Try both with and without -county suffix for registry lookup
        base_slug = slug.replace("-county", "")
        reg_entry = registry.get(slug) or registry.get(base_slug) or registry.get(f"{base_slug}-{state.lower()}")

        cd2_days = _age_days(c["cd2_last_date"])
        cd2_status = _module_status(
            has_config=bool(c["cd2_count"] and c["cd2_count"] > 0),
            last_activity_days=cd2_days if c["cd2_count"] else None,
            green_days=365, yellow_days=1095,
        )
        bi_days = _age_days(c["bi_last_completed"])
        bi_status = _module_status(bool(c["bi_has_config"]), bi_days)

        sub_pct = _pct(c["sub_with_geom"] or 0, c["sub_total"] or 0)
        parcel_pct = _pct(c["parcel_with_geom"] or 0, c["parcel_total"] or 0)

        # Build jurisdiction list (PT/CR attach here). Split county bodies vs cities
        # so the UI can render cities in a separate sub-table under the county row.
        county_bodies_out: list[dict] = []
        cities_out: list[dict] = []
        newest_activity_days = cd2_days if cd2_days is not None else None
        if bi_days is not None and (newest_activity_days is None or bi_days < newest_activity_days):
            newest_activity_days = bi_days

        # Dedupe pass: if a jurisdiction's name matches its parent county exactly
        # AND it's type='county', it's the vestigial county-owning placeholder
        # (often holds a county-wide PT config). Merge its PT/CR/maps onto the
        # county row so there's one county-level row instead of a "Bay County"
        # + "Bay County BCC" duplicate.
        county_generic_pt = "na"
        county_generic_cr = "na"
        county_generic_pt_map = None
        county_generic_pt_last_days: float | None = None
        county_generic_cr_last_days: float | None = None
        county_name_variants = {
            c["name"].strip().lower(),
            f"{c['name'].strip().lower()} county",
        }
        for j in jur_by_county.get(c["id"], []):
            if j["jurisdiction_type"] == "county" and j["name"].strip().lower() in county_name_variants:
                if j["pt_has_config"]:
                    pt_days_gen = _age_days(j["pt_last_run"])
                    s = _module_status(True, pt_days_gen)
                    if not j["pt_live"] and s == "green":
                        s = "yellow"
                    county_generic_pt = s
                    county_generic_pt_last_days = pt_days_gen
                    county_generic_pt_map = _map_cell(_slug(j["name"], "county"), "pt")
                if j["cr_has_config"]:
                    cr_days_gen = _age_days(j["cr_last_success"])
                    county_generic_cr = _module_status(True, cr_days_gen, green_days=90, yellow_days=270)
                    county_generic_cr_last_days = cr_days_gen
                break

        for j in jur_by_county.get(c["id"], []):
            # Skip the generic county-matching jurisdiction — its modules were
            # merged onto the county row above.
            if j["jurisdiction_type"] == "county" and j["name"].strip().lower() in county_name_variants:
                continue
            # Skip truly vacuous rows (no PT and no CR config at all).
            if not j["pt_has_config"] and not j["cr_has_config"]:
                continue
            pt_days = _age_days(j["pt_last_run"])
            pt_status = _module_status(bool(j["pt_has_config"]), pt_days)
            if not j["pt_live"] and pt_status == "green":
                pt_status = "yellow"
            cr_days = _age_days(j["cr_last_success"])
            cr_status = _module_status(bool(j["cr_has_config"]), cr_days, green_days=90, yellow_days=270)
            juris_slug = _slug(j["name"], j["jurisdiction_type"])

            juris_newest = None
            for d in (pt_days, cr_days):
                if d is not None and (juris_newest is None or d < juris_newest):
                    juris_newest = d
            if juris_newest is not None and (newest_activity_days is None or juris_newest < newest_activity_days):
                newest_activity_days = juris_newest

            # Commissioner roster only meaningful for commission-style jurisdictions
            roster_applicable = bool(j["cr_has_config"]) and (
                not j["commission_type"] or
                j["commission_type"] in ("city_commission", "bcc", "planning_board", "planning_commission")
            )
            roster = (
                "yes" if (j["roster_count"] or 0) > 0 else ("no" if roster_applicable else "na")
            )

            j_row = {
                "id": j["id"],
                "name": j["name"],
                "type": j["jurisdiction_type"],
                "slug": juris_slug,
                "is_county_row": False,
                "doc": registry_has,
                "cd2": "na",
                "bi":  "na",
                "pt":  pt_status,
                "cr":  cr_status,
                "cd2_map": None,
                "bi_map":  None,
                "pt_map":  _map_cell(juris_slug, "pt"),
                "cr_map":  _map_cell(juris_slug, "cr"),
                "sub_pct": None,
                "parcel_pct": None,
                "roster": roster,
                "last_run_days": juris_newest,
            }
            if j["jurisdiction_type"] == "city":
                cities_out.append(j_row)
            else:
                county_bodies_out.append(j_row)

        # Roll generic PT/CR freshness into the county's newest_activity.
        for d in (county_generic_pt_last_days, county_generic_cr_last_days):
            if d is not None and (newest_activity_days is None or d < newest_activity_days):
                newest_activity_days = d

        county_row = {
            "id": c["id"],
            "name": c["name"],
            "type": "county",
            "slug": slug,
            "is_county_row": True,
            "doc": bool(reg_entry),
            "cd2": cd2_status,
            "bi":  bi_status,
            "pt":  county_generic_pt,
            "cr":  county_generic_cr,
            "cd2_map":  _map_cell(slug, "cd2"),
            "bi_map":   _map_cell(slug, "bi"),
            "pt_map":   county_generic_pt_map,
            "cr_map":   _map_cell(slug, "cr"),
            "sub_pct":  sub_pct,
            "parcel_pct": parcel_pct,
            "roster":   "na",
            "last_run_days": newest_activity_days,
        }

        st = states.setdefault(state, {"state": state, "counties": []})
        st["counties"].append({
            "county": c["name"],
            "row": county_row,
            "jurisdictions": county_bodies_out,
            "cities": cities_out,
        })

    return {
        "states": [states[k] for k in sorted(states.keys())],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Static file serving (production: serve built React app)
# ---------------------------------------------------------------------------

_ui_dist = Path(__file__).parent / "ui" / "dist"
if _ui_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True))
