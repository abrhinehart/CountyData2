"""
api.py - FastAPI backend for the CountyData2 web UI.

Wraps existing ETL, export, and query functions with REST endpoints.

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from psycopg2.pool import SimpleConnectionPool

from config import DATABASE_URL, OUTPUT_DIR
from etl import load_config, process_county, resolve_county_names, apply_input_root
from export import build_query as build_export_query
from review_export import (
    build_query as build_review_query,
    flatten_review_row,
)
from utils.lookup import BuilderMatcher, LandBankerMatcher, SubdivisionMatcher


app = FastAPI(title="CountyData2 API")

_allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_methods=["*"],
    allow_headers=["*"],
)

pool = SimpleConnectionPool(1, 5, DATABASE_URL)

_etl_lock = asyncio.Lock()
_SAFE_FILENAME = re.compile(r"^[a-zA-Z0-9_\-]+\.xlsx$")


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")


def _coerce(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, pd.Timestamp):
        return None if pd.isna(v) else v.isoformat()
    return v


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    return [{k: _coerce(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


# ---------------------------------------------------------------------------
# ETL state (in-memory)
# ---------------------------------------------------------------------------

class ETLStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ETLState:
    status: ETLStatus = ETLStatus.IDLE
    started_at: str | None = None
    completed_at: str | None = None
    counties: list[str] = field(default_factory=list)
    results: dict = field(default_factory=dict)
    error: str | None = None


_etl_state = ETLState()


# ---------------------------------------------------------------------------
# Data endpoints
# ---------------------------------------------------------------------------

@app.get("/api/counties")
def get_counties():
    config = load_config()
    return list(config.keys())


@app.get("/api/subdivisions")
def get_subdivisions(county: str | None = None):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            if county:
                cur.execute(
                    "SELECT id, canonical_name, county FROM subdivisions "
                    "WHERE REPLACE(UPPER(county), ' ', '') = REPLACE(UPPER(%s), ' ', '') "
                    "ORDER BY canonical_name",
                    [county],
                )
            else:
                cur.execute(
                    "SELECT id, canonical_name, county FROM subdivisions ORDER BY canonical_name"
                )
            rows = cur.fetchall()
    finally:
        pool.putconn(conn)

    return [{"id": r[0], "canonical_name": r[1], "county": r[2]} for r in rows]


@app.get("/api/stats")
def get_stats():
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transactions")
            total = cur.fetchone()[0]

            cur.execute(
                "SELECT county, COUNT(*) FROM transactions GROUP BY county ORDER BY county"
            )
            by_county = [{"county": r[0], "count": r[1]} for r in cur.fetchall()]

            cur.execute(
                "SELECT type, COUNT(*) FROM transactions WHERE type IS NOT NULL "
                "GROUP BY type ORDER BY COUNT(*) DESC"
            )
            by_type = [{"type": r[0], "count": r[1]} for r in cur.fetchall()]

            cur.execute("SELECT MIN(date), MAX(date) FROM transactions")
            date_row = cur.fetchone()

            cur.execute("SELECT COUNT(*) FROM transactions WHERE review_flag = TRUE")
            flagged = cur.fetchone()[0]
    finally:
        pool.putconn(conn)

    return {
        "total_transactions": total,
        "flagged_for_review": flagged,
        "date_range": {
            "min": date_row[0].isoformat() if date_row and date_row[0] else None,
            "max": date_row[1].isoformat() if date_row and date_row[1] else None,
        },
        "by_county": by_county,
        "by_type": by_type,
    }


@app.get("/api/transactions/{transaction_id}")
def get_transaction(transaction_id: int):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id, grantor, grantee, type, instrument, date,
                    export_legal_desc, export_legal_raw,
                    deed_legal_desc, deed_legal_parsed, deed_locator,
                    subdivision, subdivision_id, phase, inventory_category,
                    lots, price, price_per_lot, acres, acres_source, price_per_acre,
                    parsed_data, county, notes, review_flag,
                    source_file, inserted_at, updated_at
                FROM transactions
                WHERE id = %s
                """,
                [transaction_id],
            )
            row = cur.fetchone()
            if not row:
                return JSONResponse(status_code=404, content={"error": "Transaction not found"})
            columns = [desc[0] for desc in cur.description]
    finally:
        pool.putconn(conn)

    record = {k: _coerce(v) for k, v in zip(columns, row)}
    return JSONResponse(content=record)


@app.patch("/api/transactions/{transaction_id}/resolve")
def resolve_transaction(transaction_id: int, body: dict | None = None):
    note = (body or {}).get("note", "").strip()
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE transactions
                SET review_flag = FALSE,
                    notes = CASE
                        WHEN %s = '' THEN notes
                        WHEN notes IS NULL OR notes = '' THEN %s
                        ELSE notes || E'\\n' || %s
                    END,
                    updated_at = NOW()
                WHERE id = %s AND review_flag = TRUE
                RETURNING id
                """,
                [note, note, note, transaction_id],
            )
            result = cur.fetchone()
            conn.commit()
    finally:
        pool.putconn(conn)

    if not result:
        return JSONResponse(status_code=404, content={"error": "Transaction not found or already resolved"})
    return {"id": transaction_id, "resolved": True}


@app.get("/api/transactions")
def get_transactions(
    county: str | None = None,
    subdivision: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    inventory_category: str | None = None,
    unmatched_only: bool = False,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = "date",
    sort_dir: str = "desc",
):
    try:
        d_from = date.fromisoformat(date_from) if date_from else None
        d_to = date.fromisoformat(date_to) if date_to else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    inv_cats = [inventory_category] if inventory_category else None

    sql, params, col_map = build_export_query(
        county, subdivision, d_from, d_to,
        unmatched_only=unmatched_only,
        inventory_categories=inv_cats,
    )

    # Inject id column so the UI can link to detail view
    if sql.upper().startswith("SELECT "):
        sql = "SELECT id, " + sql[7:]

    # Strip the existing ORDER BY so we can replace it
    order_idx = sql.upper().rfind("ORDER BY")
    base_sql = sql[:order_idx].rstrip() if order_idx != -1 else sql

    # Add search filter
    if search:
        like = f"%{search}%"
        base_sql += (
            " AND (grantor ILIKE %s OR grantee ILIKE %s"
            " OR subdivision ILIKE %s OR export_legal_desc ILIKE %s)"
        )
        params.extend([like, like, like, like])

    # Count
    count_sql = f"SELECT COUNT(*) FROM ({base_sql}) _c"
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            # Sort — map user input to known-safe column names
            _SORT_COLUMNS = {
                "date": "date", "county": "county", "grantor": "grantor",
                "grantee": "grantee", "subdivision": "subdivision",
                "price": "price", "lots": "lots", "type": "type",
                "instrument": "instrument", "price_per_lot": "price_per_lot",
                "acres": "acres", "price_per_acre": "price_per_acre",
                "inventory_category": "inventory_category",
            }
            sb = _SORT_COLUMNS.get(sort_by, "date")
            sd = "ASC" if sort_dir.lower() == "asc" else "DESC"
            paginated_sql = f"{base_sql} ORDER BY {sb} {sd} NULLS LAST LIMIT %s OFFSET %s"
            params.extend([page_size, (page - 1) * page_size])

            cur.execute(paginated_sql, params)
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    finally:
        pool.putconn(conn)

    df = pd.DataFrame(rows, columns=columns)
    df.rename(columns=col_map, inplace=True)

    return JSONResponse(
        content={
            "items": _df_to_records(df),
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        media_type="application/json",
    )


@app.get("/api/review-queue")
def get_review_queue(
    county: str | None = None,
    reason: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    reasons = [reason] if reason else None
    sql, params = build_review_query(county, reasons)

    # Count
    order_idx = sql.upper().rfind("ORDER BY")
    base_sql = sql[:order_idx].rstrip() if order_idx != -1 else sql

    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM ({base_sql}) _c", params)
            total = cur.fetchone()[0]

            paginated_sql = f"{sql} LIMIT %s OFFSET %s"
            cur.execute(paginated_sql, params + [page_size, (page - 1) * page_size])
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
    finally:
        pool.putconn(conn)

    raw_df = pd.DataFrame(rows, columns=columns)
    flat_rows = [flatten_review_row(r) for r in raw_df.to_dict(orient="records")]

    return JSONResponse(
        content={
            "items": flat_rows,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        media_type="application/json",
    )


# ---------------------------------------------------------------------------
# Pipeline endpoints
# ---------------------------------------------------------------------------

_ETL_COOLDOWN_SECONDS = int(os.getenv("ETL_COOLDOWN_SECONDS", "60"))


@app.post("/api/etl/run")
async def run_etl(body: dict | None = None):
    global _etl_state

    async with _etl_lock:
        if _etl_state.status == ETLStatus.RUNNING:
            return JSONResponse(
                status_code=409,
                content={"error": "ETL is already running"},
            )

        if _etl_state.completed_at and _ETL_COOLDOWN_SECONDS > 0:
            elapsed = (datetime.now() - datetime.fromisoformat(_etl_state.completed_at)).total_seconds()
            if elapsed < _ETL_COOLDOWN_SECONDS:
                return JSONResponse(
                    status_code=429,
                    content={"error": f"ETL cooldown: wait {int(_ETL_COOLDOWN_SECONDS - elapsed)}s"},
                )

        requested = (body or {}).get("counties", [])

        _etl_state = ETLState(
            status=ETLStatus.RUNNING,
            started_at=datetime.now().isoformat(),
            counties=requested or ["all"],
        )

    async def _run():
        global _etl_state
        try:
            results = await asyncio.to_thread(_run_etl_sync, requested)
            async with _etl_lock:
                _etl_state.status = ETLStatus.COMPLETED
                _etl_state.completed_at = datetime.now().isoformat()
                _etl_state.results = results
        except Exception as e:
            async with _etl_lock:
                _etl_state.status = ETLStatus.FAILED
                _etl_state.completed_at = datetime.now().isoformat()
                _etl_state.error = str(e)

    asyncio.create_task(_run())
    return {"status": "started", "counties": _etl_state.counties}


def _run_etl_sync(requested_counties: list[str]) -> dict:
    counties_config = load_config()

    if requested_counties:
        to_run, unknown = resolve_county_names(requested_counties, counties_config)
        if unknown:
            raise ValueError(f"Unknown counties: {', '.join(unknown)}")
    else:
        to_run = counties_config

    conn = psycopg2.connect(DATABASE_URL)
    results = {}
    try:
        sub_matcher = SubdivisionMatcher(conn)
        builder_matcher = BuilderMatcher(conn)
        land_banker_matcher = LandBankerMatcher(conn)

        for county, cfg in to_run.items():
            results[county] = process_county(
                county, cfg, conn,
                sub_matcher, builder_matcher, land_banker_matcher,
            )
    finally:
        conn.close()

    return results


@app.get("/api/etl/status")
def get_etl_status():
    return JSONResponse(
        content={
            "status": _etl_state.status.value,
            "started_at": _etl_state.started_at,
            "completed_at": _etl_state.completed_at,
            "counties": _etl_state.counties,
            "results": _etl_state.results,
            "error": _etl_state.error,
        },
    )


# ---------------------------------------------------------------------------
# Export endpoints
# ---------------------------------------------------------------------------

@app.post("/api/export/transactions")
def export_transactions(body: dict | None = None):
    params = body or {}
    d_from = date.fromisoformat(params["date_from"]) if params.get("date_from") else None
    d_to = date.fromisoformat(params["date_to"]) if params.get("date_to") else None
    inv_cats = [params["inventory_category"]] if params.get("inventory_category") else None

    sql, query_params, col_map = build_export_query(
        params.get("county"), params.get("subdivision"), d_from, d_to,
        unmatched_only=params.get("unmatched_only", False),
        inventory_categories=inv_cats,
    )

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, query_params)
            columns = [desc[0] for desc in cur.description]
            df = pd.DataFrame(cur.fetchall(), columns=columns)
    finally:
        conn.close()

    df.rename(columns=col_map, inplace=True)

    if df.empty:
        return JSONResponse(status_code=404, content={"error": "No records matched"})

    filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    out_path = OUTPUT_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(out_path, engine="openpyxl", datetime_format="m/d/yyyy") as writer:
        df.to_excel(writer, index=False)

    return {"filename": filename, "records": len(df)}


@app.post("/api/export/review-queue")
def export_review_queue_endpoint(body: dict | None = None):
    from review_export import export_review_queue

    params = body or {}
    reasons = params.get("reasons")
    sql, query_params = build_review_query(params.get("county"), reasons)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, query_params)
            columns = [desc[0] for desc in cur.description]
            raw_df = pd.DataFrame(cur.fetchall(), columns=columns)
    finally:
        conn.close()

    flat_rows = [flatten_review_row(r) for r in raw_df.to_dict(orient="records")]
    from review_export import _DETAIL_COLUMNS
    detail_df = pd.DataFrame(flat_rows, columns=_DETAIL_COLUMNS)

    if detail_df.empty:
        return JSONResponse(status_code=404, content={"error": "No review rows matched"})

    filename = f"review_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    out_path = OUTPUT_DIR / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    export_review_queue(detail_df, out_path)
    return {"filename": filename, "records": len(detail_df)}


@app.get("/api/export/download/{filename}")
def download_export(filename: str):
    if not _SAFE_FILENAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = (OUTPUT_DIR / filename).resolve()
    if not path.is_relative_to(OUTPUT_DIR.resolve()):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# Static file serving (production: serve built React app)
# ---------------------------------------------------------------------------

_ui_dist = Path(__file__).parent / "ui" / "dist"
if _ui_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_ui_dist), html=True))
