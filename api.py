"""
api.py - Unified Real Estate Intelligence Platform.

FastAPI application factory. Each module registers its own router.

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 1460
"""

import os
from pathlib import Path

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

app.include_router(sales_router)
app.include_router(inventory_router)
app.include_router(permits_router)
app.include_router(commission_router)


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
    """Per-county subdivision geometry coverage stats."""
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.name                                          AS county,
                       COUNT(*)                                        AS total,
                       COUNT(*) FILTER (WHERE s.geom IS NOT NULL)      AS with_geom,
                       COUNT(*) FILTER (WHERE s.geom IS NULL)          AS without_geom
                  FROM subdivisions s
                  JOIN counties c ON c.id = s.county_id
                 WHERE s.is_active = true
                 GROUP BY c.name
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
# Static file serving (production: serve built React app)
# ---------------------------------------------------------------------------

_ui_dist = Path(__file__).parent / "ui" / "dist"
if _ui_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True))
