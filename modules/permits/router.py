from __future__ import annotations

import threading
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.database import get_conn, put_conn

from modules.permits.services import (
    ConflictError,
    NotFoundError,
    assign_permit_subdivision,
    backfill_bay_county_parcel_ids,
    backfill_subdivision_matches,
    create_subdivision,
    enqueue_scrape_job,
    geocode_missing_permits,
    get_bootstrap_payload,
    get_dashboard_payload,
    get_permits_payload,
    get_scraper_artifact_payload,
    get_scrape_job_payload,
    list_scrape_jobs_payload,
    list_scraper_artifacts_payload,
    list_unmatched_permits_payload,
    list_subdivisions_payload,
    retry_scrape_job,
    set_watchlist_state,
)

router = APIRouter(prefix="/api/permits", tags=["permits"])

_job_runner_wake = threading.Event()

# ---------------------------------------------------------------------------
# Pydantic request bodies
# ---------------------------------------------------------------------------

class SubdivisionCreate(BaseModel):
    name: Optional[str] = None
    jurisdiction_id: Optional[int] = None
    model_config = {"extra": "allow"}


class SubdivisionUpdate(BaseModel):
    watched: bool = False


class BackfillRequest(BaseModel):
    jurisdiction: Optional[str] = None
    limit: Optional[int] = None


class PermitSubdivisionUpdate(BaseModel):
    subdivision_id: Optional[Any] = None


class ScrapeRunRequest(BaseModel):
    jurisdiction: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    scrape_mode: Optional[str] = None


class GeocodeRunRequest(BaseModel):
    jurisdiction: Optional[str] = None
    limit: Optional[int] = None


class ParcelRunRequest(BaseModel):
    jurisdiction: Optional[str] = None
    limit: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filters_from_query(
    watch_only: Optional[str] = None,
    jurisdiction_id: Optional[int] = None,
    subdivision_id: Optional[int] = None,
    builder_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    grain: str = "month",
    sort: str = "issue_date_desc",
    page: Optional[str] = None,
    page_size: Optional[str] = None,
) -> dict:
    def as_bool(value: str | None) -> bool:
        return str(value).lower() in {"1", "true", "yes", "on"} if value else False

    return {
        "watch_only": as_bool(watch_only),
        "jurisdiction_id": jurisdiction_id,
        "subdivision_id": subdivision_id,
        "builder_id": builder_id,
        "status": status or None,
        "start_date": start_date or None,
        "end_date": end_date or None,
        "grain": grain or "month",
        "sort": sort or "issue_date_desc",
        "page": page or None,
        "page_size": page_size or None,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/bootstrap")
def bootstrap():
    conn = get_conn()
    try:
        return get_bootstrap_payload(conn)
    finally:
        put_conn(conn)


@router.get("/dashboard")
def dashboard(
    watch_only: Optional[str] = Query(None),
    jurisdiction_id: Optional[int] = Query(None),
    subdivision_id: Optional[int] = Query(None),
    builder_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    grain: str = Query("month"),
    sort: str = Query("issue_date_desc"),
    page: Optional[str] = Query(None),
    page_size: Optional[str] = Query(None),
):
    filters = _filters_from_query(
        watch_only=watch_only,
        jurisdiction_id=jurisdiction_id,
        subdivision_id=subdivision_id,
        builder_id=builder_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        grain=grain,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    conn = get_conn()
    try:
        return get_dashboard_payload(conn, filters)
    finally:
        put_conn(conn)


@router.get("/permits")
def permits(
    watch_only: Optional[str] = Query(None),
    jurisdiction_id: Optional[int] = Query(None),
    subdivision_id: Optional[int] = Query(None),
    builder_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    grain: str = Query("month"),
    sort: str = Query("issue_date_desc"),
    page: Optional[str] = Query(None),
    page_size: Optional[str] = Query(None),
):
    filters = _filters_from_query(
        watch_only=watch_only,
        jurisdiction_id=jurisdiction_id,
        subdivision_id=subdivision_id,
        builder_id=builder_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        grain=grain,
        sort=sort,
        page=page,
        page_size=page_size,
    )
    conn = get_conn()
    try:
        return get_permits_payload(conn, filters)
    finally:
        put_conn(conn)


@router.get("/subdivisions")
def subdivisions():
    conn = get_conn()
    try:
        return list_subdivisions_payload(conn)
    finally:
        put_conn(conn)


@router.get("/unmatched-permits")
def unmatched_permits(limit: int = Query(25)):
    conn = get_conn()
    try:
        return list_unmatched_permits_payload(conn, limit=limit)
    finally:
        put_conn(conn)


@router.post("/subdivisions", status_code=201)
def subdivision_create(body: SubdivisionCreate):
    payload = body.model_dump()
    conn = get_conn()
    try:
        return create_subdivision(conn, payload)
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)


@router.patch("/subdivisions/{subdivision_id}")
def subdivision_update(subdivision_id: int, body: SubdivisionUpdate):
    conn = get_conn()
    try:
        return set_watchlist_state(conn, subdivision_id, body.watched)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        put_conn(conn)


@router.post("/subdivisions/backfill")
def subdivision_backfill_run(body: BackfillRequest):
    conn = get_conn()
    try:
        return backfill_subdivision_matches(
            conn,
            jurisdiction_name=body.jurisdiction,
            limit=body.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)


@router.patch("/permits/{permit_id}/subdivision")
def permit_subdivision_update(permit_id: int, body: PermitSubdivisionUpdate):
    raw = body.subdivision_id
    try:
        subdivision_id = None if raw in (None, "", 0, "0") else int(raw)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="A valid subdivision is required.")
    conn = get_conn()
    try:
        return assign_permit_subdivision(conn, permit_id, subdivision_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)


@router.post("/scrape/run", status_code=202)
def scrape_run(body: ScrapeRunRequest):
    conn = get_conn()
    try:
        result = enqueue_scrape_job(
            conn,
            jurisdiction_name=body.jurisdiction,
            start_date=body.start_date,
            end_date=body.end_date,
            scrape_mode=body.scrape_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)
    _job_runner_wake.set()
    return result


@router.get("/scrape/jobs")
def scrape_jobs(
    limit: int = Query(20),
    status: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
):
    conn = get_conn()
    try:
        return list_scrape_jobs_payload(
            conn,
            limit=limit,
            status=status or None,
            jurisdiction_name=jurisdiction or None,
        )
    finally:
        put_conn(conn)


@router.get("/scrape/jobs/{job_id}")
def scrape_job(job_id: int):
    conn = get_conn()
    try:
        return get_scrape_job_payload(conn, job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        put_conn(conn)


@router.get("/scrape/artifacts")
def scrape_artifacts(
    limit: int = Query(20),
    adapter_slug: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    scrape_job_id: Optional[int] = Query(None),
):
    conn = get_conn()
    try:
        return list_scraper_artifacts_payload(
            conn,
            limit=limit,
            adapter_slug=adapter_slug or None,
            jurisdiction_name=jurisdiction or None,
            scrape_job_id=scrape_job_id,
        )
    finally:
        put_conn(conn)


@router.get("/scrape/artifacts/{artifact_id}")
def scrape_artifact(artifact_id: int):
    conn = get_conn()
    try:
        return get_scraper_artifact_payload(conn, artifact_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    finally:
        put_conn(conn)


@router.post("/scrape/jobs/{job_id}/retry", status_code=202)
def scrape_job_retry(job_id: int):
    conn = get_conn()
    try:
        result = retry_scrape_job(conn, job_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)
    _job_runner_wake.set()
    return result


@router.post("/geocode/run")
def geocode_run(body: GeocodeRunRequest):
    conn = get_conn()
    try:
        return geocode_missing_permits(
            conn,
            jurisdiction_name=body.jurisdiction,
            limit=body.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)


@router.post("/parcels/run")
def parcel_backfill_run(body: ParcelRunRequest):
    conn = get_conn()
    try:
        return backfill_bay_county_parcel_ids(
            conn,
            jurisdiction_name=body.jurisdiction,
            limit=body.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        put_conn(conn)
