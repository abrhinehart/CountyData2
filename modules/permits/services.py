from __future__ import annotations

import json
import psycopg2
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from modules.permits import geocoding, parcels
from modules.permits.normalization import (
    canonicalize_builder_name,
    names_match,
    normalize_permit_status,
    normalize_text,
)
from modules.permits.reference_data import (
    reference_jurisdiction_by_name,
    reference_jurisdictions,
    reference_subdivisions,
)
from modules.permits.scrapers.registry import ADAPTERS
from modules.permits.subdivision_geo import SubdivisionGeometryLookup
from shared.database import get_conn, put_conn


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "modules" / "permits" / "data"


class ConflictError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


SCRAPE_JOB_ACTIVE_STATUSES = {"pending", "running"}
SCRAPE_JOB_TERMINAL_STATUSES = {"succeeded", "failed"}
SCRAPE_JOB_LEASE_SECONDS = 30 * 60


def seed_reference_data(conn) -> None:
    """Deprecated: PT reference data is now seeded via seed_pt_jurisdiction_config.py.

    Left as a no-op so any legacy callers don't break.
    """
    return None


def seed_demo_data(conn, force: bool = False) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pt_permits")
    existing = cur.fetchone()[0]
    if existing and not force:
        cur.close()
        return

    if force:
        cur.execute("DELETE FROM pt_scrape_jobs")
        cur.execute("DELETE FROM pt_scrape_runs")
        cur.execute("DELETE FROM pt_permits")
        cur.execute("DELETE FROM builders")
        conn.commit()

    fixture_records = json.loads((DATA_DIR / "demo_permits.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for record in fixture_records:
        grouped[record["jurisdiction"]].append(record)

    base_run_date = date.today() - timedelta(days=21)
    for offset, (jurisdiction, records) in enumerate(grouped.items()):
        run_at = datetime.combine(base_run_date + timedelta(days=offset * 7), datetime.min.time()).isoformat()
        ingest_permits(conn, jurisdiction, records, run_at=run_at)

    cur.close()


def ingest_permits(
    conn,
    jurisdiction_name: str,
    permits: list[dict],
    run_at: str | None = None,
    status: str = "success",
    error_log: str | None = None,
    source_start_date: str | None = None,
    source_end_date: str | None = None,
) -> dict:
    cur = conn.cursor()
    run_at = run_at or datetime.now(UTC).isoformat()
    cur.execute(
        "SELECT id, name FROM jurisdictions WHERE name = %s",
        (jurisdiction_name,),
    )
    jurisdiction = cur.fetchone()
    if jurisdiction is None:
        cur.close()
        raise ValueError(f"Unknown jurisdiction: {jurisdiction_name}")
    jurisdiction_id = jurisdiction[0]
    jurisdiction_db_name = jurisdiction[1]

    permits_found = len(permits)
    permits_new = 0
    permits_updated = 0

    for permit in permits:
        subdivision_id = _resolve_subdivision_id(
            conn,
            jurisdiction_id,
            jurisdiction_db_name,
            permit.get("raw_subdivision_name"),
            permit.get("address"),
            permit.get("latitude"),
            permit.get("longitude"),
        )
        builder_id = _ensure_builder_id(conn, permit.get("raw_contractor_name"))
        payload = {
            "subdivision_id": subdivision_id,
            "builder_id": builder_id,
            "address": permit["address"],
            "parcel_id": permit.get("parcel_id"),
            "issue_date": permit["issue_date"],
            "status": normalize_permit_status(permit.get("status")),
            "permit_type": permit["permit_type"],
            "valuation": permit.get("valuation"),
            "raw_subdivision_name": permit.get("raw_subdivision_name"),
            "raw_contractor_name": permit.get("raw_contractor_name"),
            "raw_applicant_name": permit.get("raw_applicant_name"),
            "raw_licensed_professional_name": permit.get("raw_licensed_professional_name"),
            "latitude": permit.get("latitude"),
            "longitude": permit.get("longitude"),
        }

        cur.execute(
            """
            SELECT id, subdivision_id, builder_id, address, parcel_id,
                   issue_date, status, permit_type, valuation,
                   raw_subdivision_name, raw_contractor_name, raw_applicant_name,
                   raw_licensed_professional_name, latitude, longitude
            FROM pt_permits
            WHERE jurisdiction_id = %s AND permit_number = %s
            """,
            (jurisdiction_id, permit["permit_number"]),
        )
        existing = cur.fetchone()

        if existing is None:
            cur.execute(
                """
                INSERT INTO pt_permits (
                    permit_number, jurisdiction_id, subdivision_id, builder_id, address,
                    parcel_id, issue_date, status, permit_type, valuation,
                    raw_subdivision_name, raw_contractor_name, raw_applicant_name,
                    raw_licensed_professional_name, latitude, longitude,
                    first_seen_at, last_updated_at, last_seen_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    permit["permit_number"],
                    jurisdiction_id,
                    payload["subdivision_id"],
                    payload["builder_id"],
                    payload["address"],
                    payload["parcel_id"],
                    payload["issue_date"],
                    payload["status"],
                    payload["permit_type"],
                    payload["valuation"],
                    payload["raw_subdivision_name"],
                    payload["raw_contractor_name"],
                    payload["raw_applicant_name"],
                    payload["raw_licensed_professional_name"],
                    payload["latitude"],
                    payload["longitude"],
                    run_at,
                    run_at,
                    run_at,
                ),
            )
            permits_new += 1
            continue

        # existing columns: id, subdivision_id, builder_id, address, parcel_id,
        #   issue_date, status, permit_type, valuation,
        #   raw_subdivision_name, raw_contractor_name, raw_applicant_name,
        #   raw_licensed_professional_name, latitude, longitude
        existing_id = existing[0]
        existing_dict = {
            "subdivision_id": existing[1],
            "builder_id": existing[2],
            "address": existing[3],
            "parcel_id": existing[4],
            "issue_date": existing[5],
            "status": existing[6],
            "permit_type": existing[7],
            "valuation": existing[8],
            "raw_subdivision_name": existing[9],
            "raw_contractor_name": existing[10],
            "raw_applicant_name": existing[11],
            "raw_licensed_professional_name": existing[12],
            "latitude": existing[13],
            "longitude": existing[14],
        }

        # Normalize issue_date for comparison: existing may be a date object
        existing_issue_date = existing_dict["issue_date"]
        if isinstance(existing_issue_date, date) and not isinstance(existing_issue_date, datetime):
            existing_issue_date = existing_issue_date.isoformat()
        existing_dict["issue_date"] = existing_issue_date

        # Normalize valuation for comparison: existing may be Decimal
        existing_val = existing_dict["valuation"]
        payload_val = payload["valuation"]
        if existing_val is not None and payload_val is not None:
            existing_dict["valuation"] = float(existing_val)
            payload["valuation"] = float(payload_val)

        changed = any(
            existing_dict[key] != payload[key]
            for key in (
                "subdivision_id",
                "builder_id",
                "address",
                "parcel_id",
                "issue_date",
                "status",
                "permit_type",
                "valuation",
                "raw_subdivision_name",
                "raw_contractor_name",
                "raw_applicant_name",
                "raw_licensed_professional_name",
                "latitude",
                "longitude",
            )
        )
        if not changed:
            cur.execute(
                "UPDATE pt_permits SET last_seen_at = %s WHERE id = %s",
                (run_at, existing_id),
            )
            continue

        cur.execute(
            """
            UPDATE pt_permits
            SET subdivision_id = %s, builder_id = %s, address = %s, parcel_id = %s,
                issue_date = %s, status = %s, permit_type = %s, valuation = %s,
                raw_subdivision_name = %s, raw_contractor_name = %s, raw_applicant_name = %s,
                raw_licensed_professional_name = %s, latitude = %s, longitude = %s,
                last_updated_at = %s, last_seen_at = %s
            WHERE id = %s
            """,
            (
                payload["subdivision_id"],
                payload["builder_id"],
                payload["address"],
                payload["parcel_id"],
                payload["issue_date"],
                payload["status"],
                payload["permit_type"],
                payload["valuation"],
                payload["raw_subdivision_name"],
                payload["raw_contractor_name"],
                payload["raw_applicant_name"],
                payload["raw_licensed_professional_name"],
                payload["latitude"],
                payload["longitude"],
                run_at,
                run_at,
                existing_id,
            ),
        )
        permits_updated += 1

    cur.execute(
        """
        INSERT INTO pt_scrape_runs (
            jurisdiction_id, run_at, status, permits_found, permits_new, permits_updated, error_log
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            jurisdiction_id,
            run_at,
            status,
            permits_found,
            permits_new,
            permits_updated,
            error_log,
        ),
    )
    scrape_run_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO pt_scrape_payload_archives (
            jurisdiction_id, run_at, status, permits_count, source_start_date, source_end_date, payload_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            jurisdiction_id,
            run_at,
            status,
            permits_found,
            source_start_date,
            source_end_date,
            json.dumps(permits, sort_keys=True),
        ),
    )
    conn.commit()
    cur.close()

    return {
        "jurisdiction": jurisdiction_name,
        "status": status,
        "scrape_run_id": scrape_run_id,
        "permits_found": permits_found,
        "permits_new": permits_new,
        "permits_updated": permits_updated,
        "error_log": error_log,
        "run_at": run_at,
    }


def run_adapter_scrape(
    conn,
    jurisdiction_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    scrape_mode: str | None = None,
    scrape_job_id: int | None = None,
) -> dict:
    start, end = _validated_scrape_request(
        jurisdiction_name=jurisdiction_name,
        start_date=start_date,
        end_date=end_date,
        scrape_mode=scrape_mode,
        validate_only=True,
    )

    if jurisdiction_name:
        adapter = ADAPTERS.get(jurisdiction_name)
        return _run_single_adapter(conn, adapter, start, end, scrape_mode=scrape_mode, scrape_job_id=scrape_job_id)

    results = []
    for adapter in _runnable_adapters():
        results.append(_run_single_adapter(conn, adapter, start, end, scrape_mode=scrape_mode, scrape_job_id=scrape_job_id))
    return {"results": results}


def run_all_scrapes(conn) -> dict:
    return run_adapter_scrape(conn)


def enqueue_scrape_job(
    conn,
    jurisdiction_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    scrape_mode: str | None = None,
    *,
    trigger_type: str = "manual",
    retry_of_job_id: int | None = None,
) -> dict:
    start, end = _validated_scrape_request(
        jurisdiction_name=jurisdiction_name,
        start_date=start_date,
        end_date=end_date,
        scrape_mode=scrape_mode,
        validate_only=True,
    )
    existing = _find_active_scrape_job(conn, jurisdiction_name)
    if existing is not None:
        return {
            "job": _serialize_scrape_job(existing),
            "duplicate": True,
        }

    payload = {
        "jurisdiction": jurisdiction_name,
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "scrape_mode": scrape_mode or "daily",
    }
    queued_at = datetime.now(UTC).isoformat()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pt_scrape_jobs (
            jurisdiction_name,
            status,
            trigger_type,
            request_payload_json,
            attempt_count,
            max_attempts,
            retry_of_job_id,
            queued_at
        )
        VALUES (%s, 'pending', %s, %s, 0, 2, %s, %s)
        RETURNING id
        """,
        (
            jurisdiction_name,
            trigger_type,
            json.dumps(payload, sort_keys=True),
            retry_of_job_id,
            queued_at,
        ),
    )
    job_id = cur.fetchone()[0]
    conn.commit()
    job = _fetch_scrape_job_row(conn, job_id)
    cur.close()
    return {
        "job": _serialize_scrape_job(job),
        "duplicate": False,
    }


def list_scrape_jobs_payload(
    conn,
    *,
    limit: int = 20,
    status: str | None = None,
    jurisdiction_name: str | None = None,
) -> dict:
    safe_limit = max(1, min(limit, 100))
    clauses: list[str] = []
    params: list = []
    if status:
        clauses.append("status = %s")
        params.append(status)
    if jurisdiction_name:
        clauses.append("jurisdiction_name = %s")
        params.append(jurisdiction_name)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT *
        FROM pt_scrape_jobs
        {where_sql}
        ORDER BY queued_at DESC, id DESC
        LIMIT %s
        """,
        params + [safe_limit],
    )
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.execute(
        """
        SELECT COUNT(*) AS total
        FROM pt_scrape_jobs
        WHERE status IN ('pending', 'running')
        """
    )
    active_count = cur.fetchone()[0]
    cur.close()
    return {
        "jobs": [_serialize_scrape_job(row) for row in rows],
        "active_count": active_count,
    }


def get_scrape_job_payload(conn, job_id: int) -> dict:
    row = _fetch_scrape_job_row(conn, job_id)
    if row is None:
        raise NotFoundError("Scrape job not found.")
    return _serialize_scrape_job(row)


def list_scraper_artifacts_payload(
    conn,
    *,
    limit: int = 20,
    adapter_slug: str | None = None,
    jurisdiction_name: str | None = None,
    scrape_job_id: int | None = None,
) -> dict:
    safe_limit = max(1, min(limit, 100))
    clauses: list[str] = []
    params: list = []
    if adapter_slug:
        clauses.append("sa.adapter_slug = %s")
        params.append(adapter_slug)
    if jurisdiction_name:
        clauses.append("j.name = %s")
        params.append(jurisdiction_name)
    if scrape_job_id is not None:
        clauses.append("sa.scrape_job_id = %s")
        params.append(scrape_job_id)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT sa.*, j.name AS jurisdiction_name
        FROM pt_scraper_artifacts sa
        LEFT JOIN jurisdictions j ON j.id = sa.jurisdiction_id
        {where_sql}
        ORDER BY sa.created_at DESC, sa.id DESC
        LIMIT %s
        """,
        params + [safe_limit],
    )
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, row)) for row in cur.fetchall()]
    cur.close()
    return {"artifacts": [_serialize_scraper_artifact(row) for row in rows]}


def get_scraper_artifact_payload(conn, artifact_id: int) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sa.*, j.name AS jurisdiction_name
        FROM pt_scraper_artifacts sa
        LEFT JOIN jurisdictions j ON j.id = sa.jurisdiction_id
        WHERE sa.id = %s
        """,
        (artifact_id,),
    )
    columns = [desc[0] for desc in cur.description]
    row_tuple = cur.fetchone()
    cur.close()
    if row_tuple is None:
        raise NotFoundError("Scraper artifact not found.")
    row = dict(zip(columns, row_tuple))
    return _serialize_scraper_artifact(row)


def retry_scrape_job(conn, job_id: int) -> dict:
    row = _fetch_scrape_job_row(conn, job_id)
    if row is None:
        raise NotFoundError("Scrape job not found.")
    if row["status"] not in SCRAPE_JOB_TERMINAL_STATUSES:
        raise ValueError("Only finished scrape jobs can be retried.")
    payload = json.loads(row["request_payload_json"])
    return enqueue_scrape_job(
        conn,
        jurisdiction_name=payload.get("jurisdiction"),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        scrape_mode=payload.get("scrape_mode"),
        trigger_type="retry",
        retry_of_job_id=job_id,
    )


def recover_stale_scrape_jobs(conn) -> dict:
    cur = conn.cursor()
    now = datetime.now(UTC)
    cur.execute(
        """
        SELECT id, attempt_count, max_attempts
        FROM pt_scrape_jobs
        WHERE status = 'running'
          AND lease_expires_at IS NOT NULL
          AND lease_expires_at < %s
        ORDER BY id
        """,
        (now.isoformat(),),
    )
    columns = [desc[0] for desc in cur.description]
    stale_rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    requeued = 0
    failed = 0
    for row in stale_rows:
        message = "Previous worker lease expired before the scrape job finished."
        if row["attempt_count"] >= row["max_attempts"]:
            cur.execute(
                """
                UPDATE pt_scrape_jobs
                SET status = 'failed',
                    finished_at = %s,
                    lease_expires_at = NULL,
                    last_error = %s
                WHERE id = %s
                """,
                (now.isoformat(), message, row["id"]),
            )
            failed += 1
            continue
        cur.execute(
            """
            UPDATE pt_scrape_jobs
            SET status = 'pending',
                started_at = NULL,
                lease_expires_at = NULL,
                last_error = %s
            WHERE id = %s
            """,
            (message, row["id"]),
        )
        requeued += 1
    conn.commit()
    cur.close()
    return {"requeued": requeued, "failed": failed}


def run_pending_scrape_jobs(conn, limit: int = 1) -> dict:
    processed: list[dict] = []
    recover_stale_scrape_jobs(conn)
    for _ in range(max(1, limit)):
        job = _claim_next_scrape_job(conn)
        if job is None:
            break
        processed.append(_execute_scrape_job(conn, job))
    return {"processed": len(processed), "jobs": processed}


def geocode_missing_permits(
    conn,
    jurisdiction_name: str | None = None,
    addresses: list[str] | None = None,
    limit: int | None = None,
) -> dict:
    cur = conn.cursor()
    clauses = ["(p.latitude IS NULL OR p.longitude IS NULL)"]
    params: list = []

    if jurisdiction_name:
        clauses.append("j.name = %s")
        params.append(jurisdiction_name)

    if addresses:
        deduped_addresses = list(dict.fromkeys(address for address in addresses if address))
        placeholders = ", ".join("%s" for _ in deduped_addresses)
        clauses.append(f"p.address IN ({placeholders})")
        params.extend(deduped_addresses)

    sql = f"""
        SELECT DISTINCT p.address, j.name AS jurisdiction
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE {' AND '.join(clauses)}
        ORDER BY p.address
    """
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    cur.execute(sql, params)
    columns = [desc[0] for desc in cur.description]
    target_rows = [dict(zip(columns, r)) for r in cur.fetchall() if r[0]]
    cur.close()
    if not target_rows:
        return {
            "jurisdiction": jurisdiction_name,
            "addresses_considered": 0,
            "cache_hits": 0,
            "queried": 0,
            "matched": 0,
            "updated": 0,
        }

    target_addresses = [row["address"] for row in target_rows]
    jurisdiction_name_by_address = {
        row["address"]: row["jurisdiction"]
        for row in target_rows
    }

    cache_rows = _lookup_geocode_cache(conn, target_addresses)
    cache_hits = sum(
        1
        for row in cache_rows.values()
        if row["latitude"] is not None and row["longitude"] is not None
    )
    updated = _apply_cached_geocodes(conn, cache_rows, jurisdiction_name)

    addresses_to_query = [
        address
        for address in target_addresses
        if _should_query_geocode(
            address,
            jurisdiction_name_by_address.get(address),
            cache_rows.get(address),
        )
    ]
    queried = len(addresses_to_query)
    matched = 0
    if addresses_to_query:
        query_jurisdiction_by_address = {
            address: jurisdiction_name_by_address[address]
            for address in addresses_to_query
        }
        for result in geocoding.batch_geocode_addresses(
            addresses_to_query,
            jurisdiction_name_by_address=query_jurisdiction_by_address,
        ):
            _store_geocode_result(conn, result)
            if result["matched"]:
                matched += 1
                updated += _apply_single_geocode(
                    conn,
                    result["address"],
                    result["latitude"],
                    result["longitude"],
                    jurisdiction_name,
                )

    subdivision_matches = backfill_subdivision_matches(
        conn,
        jurisdiction_name=jurisdiction_name,
        addresses=target_addresses,
    )["matched"]
    conn.commit()
    return {
        "jurisdiction": jurisdiction_name,
        "addresses_considered": len(target_addresses),
        "cache_hits": cache_hits,
        "queried": queried,
        "matched": matched,
        "updated": updated,
        "subdivision_matches": subdivision_matches,
    }


def backfill_subdivision_matches(
    conn,
    jurisdiction_name: str | None = None,
    addresses: list[str] | None = None,
    limit: int | None = None,
) -> dict:
    cur = conn.cursor()
    clauses = [
        "p.subdivision_id IS NULL",
        "p.latitude IS NOT NULL",
        "p.longitude IS NOT NULL",
    ]
    params: list = []

    if jurisdiction_name:
        clauses.append("j.name = %s")
        params.append(jurisdiction_name)

    if addresses:
        deduped_addresses = list(dict.fromkeys(address for address in addresses if address))
        if deduped_addresses:
            placeholders = ", ".join("%s" for _ in deduped_addresses)
            clauses.append(f"p.address IN ({placeholders})")
            params.extend(deduped_addresses)

    sql = f"""
        SELECT
            p.id,
            p.address,
            p.raw_subdivision_name,
            p.latitude,
            p.longitude,
            j.id AS jurisdiction_id,
            j.name AS jurisdiction
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE {' AND '.join(clauses)}
        ORDER BY p.issue_date DESC, p.id DESC
    """
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    cur.execute(sql, params)
    columns = [desc[0] for desc in cur.description]
    permits = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    if not permits:
        return {
            "jurisdiction": jurisdiction_name,
            "permits_considered": 0,
            "matched": 0,
        }

    matched = 0
    with SubdivisionGeometryLookup(conn) as lookup:
        for permit in permits:
            subdivision_id = _resolve_subdivision_id(
                conn,
                permit["jurisdiction_id"],
                permit["jurisdiction"],
                permit["raw_subdivision_name"],
                permit["address"],
                permit["latitude"],
                permit["longitude"],
                lookup=lookup,
            )
            if subdivision_id is None:
                continue
            cur2 = conn.cursor()
            cur2.execute(
                "UPDATE pt_permits SET subdivision_id = %s WHERE id = %s",
                (subdivision_id, permit["id"]),
            )
            cur2.close()
            matched += 1
    conn.commit()

    return {
        "jurisdiction": jurisdiction_name,
        "permits_considered": len(permits),
        "matched": matched,
    }


def backfill_bay_county_parcel_ids(
    conn,
    jurisdiction_name: str | None = None,
    addresses: list[str] | None = None,
    limit: int | None = None,
) -> dict:
    if jurisdiction_name and jurisdiction_name != "Bay County":
        raise ValueError("Parcel ID backfill is currently available for Bay County only.")

    effective_jurisdiction = "Bay County"
    clauses = ["j.name = %s", "(p.parcel_id IS NULL OR TRIM(p.parcel_id) = '')"]
    params: list = [effective_jurisdiction]

    if addresses:
        deduped_addresses = list(dict.fromkeys(address for address in addresses if address))
        placeholders = ", ".join("%s" for _ in deduped_addresses)
        clauses.append(f"p.address IN ({placeholders})")
        params.extend(deduped_addresses)

    sql = f"""
        SELECT DISTINCT p.address
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE {' AND '.join(clauses)}
        ORDER BY p.address
    """
    if limit:
        sql += " LIMIT %s"
        params.append(limit)

    cur = conn.cursor()
    cur.execute(sql, params)
    target_addresses = [row[0] for row in cur.fetchall() if row[0]]
    cur.close()
    if not target_addresses:
        return {
            "jurisdiction": effective_jurisdiction,
            "addresses_considered": 0,
            "cache_hits": 0,
            "queried": 0,
            "matched": 0,
            "updated": 0,
        }

    cache_rows = _lookup_parcel_cache(conn, target_addresses)
    cache_hits = sum(1 for row in cache_rows.values() if row["parcel_id"])
    updated = _apply_cached_parcels(conn, cache_rows, effective_jurisdiction)

    addresses_to_query = [
        address
        for address in target_addresses
        if _should_query_parcel(cache_rows.get(address))
    ]
    queried = len(addresses_to_query)
    matched = 0
    if addresses_to_query:
        for result in parcels.batch_lookup_bay_county_parcels(addresses_to_query):
            _store_parcel_result(conn, result)
            if result["matched"]:
                matched += 1
                updated += _apply_single_parcel_id(
                    conn,
                    result["address"],
                    result["parcel_id"],
                    effective_jurisdiction,
                )

    conn.commit()
    return {
        "jurisdiction": effective_jurisdiction,
        "addresses_considered": len(target_addresses),
        "cache_hits": cache_hits,
        "queried": queried,
        "matched": matched,
        "updated": updated,
    }


def get_bootstrap_payload(conn) -> dict:
    research = _load_research_index()
    cur = conn.cursor()
    cur.execute("""
        SELECT j.id, j.name,
               pc.portal_type, pc.portal_url,
               j.is_active AS active
        FROM jurisdictions j
        LEFT JOIN pt_jurisdiction_config pc ON pc.jurisdiction_id = j.id
        WHERE pc.id IS NOT NULL
        ORDER BY j.name
    """)
    columns = [desc[0] for desc in cur.description]
    jurisdictions = [dict(zip(columns, r)) for r in cur.fetchall()]
    jurisdictions = [_enrich_jurisdiction_runtime(row, research) for row in jurisdictions]

    cur.execute(
        """
        SELECT DISTINCT b.id, b.canonical_name AS name
        FROM builders b
        JOIN pt_permits p ON p.builder_id = b.id
        ORDER BY b.canonical_name
        """
    )
    builders_columns = [desc[0] for desc in cur.description]
    builders = [dict(zip(builders_columns, r)) for r in cur.fetchall()]

    cur.execute("SELECT DISTINCT status FROM pt_permits ORDER BY status")
    statuses = [row[0] for row in cur.fetchall()]
    cur.close()
    return {
        "jurisdictions": jurisdictions,
        "runnable_jurisdictions": [row for row in jurisdictions if row["runnable"]],
        "builders": builders,
        "subdivisions": list_subdivisions_payload(conn)["subdivisions"],
        "research": _enrich_research_runtime(research),
        "statuses": statuses,
    }


def get_dashboard_payload(conn, filters: dict) -> dict:
    cur = conn.cursor()
    base_sql, params = _base_query(filters)
    today = date.today()
    month_start = today.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    last_month_end = month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    cur.execute(
        f"SELECT COUNT(*) AS total {base_sql} AND p.issue_date >= %s AND p.issue_date < %s",
        params + [month_start.isoformat(), next_month.isoformat()],
    )
    current_month = cur.fetchone()[0]
    cur.execute(
        f"SELECT COUNT(*) AS total {base_sql} AND p.issue_date >= %s AND p.issue_date < %s",
        params + [last_month_start.isoformat(), month_start.isoformat()],
    )
    last_month = cur.fetchone()[0]
    cur.execute(
        f"SELECT COUNT(*) AS total {base_sql}",
        params,
    )
    total_permits = cur.fetchone()[0]

    cur.execute(
        f"SELECT p.issue_date {base_sql} ORDER BY p.issue_date",
        params,
    )
    trend_rows = cur.fetchall()
    trend = _build_trend([row[0] for row in trend_rows], filters.get("grain", "month"))

    cur.execute(
        f"""
        SELECT COALESCE(s.canonical_name, 'Unmatched') AS name, COUNT(*) AS total
        {base_sql}
        GROUP BY COALESCE(s.canonical_name, 'Unmatched')
        ORDER BY total DESC, name
        LIMIT 8
        """,
        params,
    )
    top_subdivisions = [{"name": r[0], "total": r[1]} for r in cur.fetchall()]

    cur.execute(
        f"""
        SELECT COALESCE(b.canonical_name, 'Unknown Builder') AS builder_name, COUNT(*) AS total
        {base_sql}
        GROUP BY COALESCE(b.canonical_name, 'Unknown Builder')
        ORDER BY total DESC, builder_name
        LIMIT 8
        """,
        params,
    )
    top_builders = [{"name": r[0], "total": r[1]} for r in cur.fetchall()]

    cur.execute(
        f"""
        SELECT
            p.permit_number,
            p.address,
            p.issue_date,
            p.status,
            p.latitude,
            p.longitude,
            j.name AS jurisdiction,
            COALESCE(s.canonical_name, 'Unmatched') AS subdivision,
            COALESCE(b.canonical_name, 'Unknown Builder') AS builder
        {base_sql}
        AND p.latitude IS NOT NULL
        AND p.longitude IS NOT NULL
        ORDER BY p.issue_date DESC
        LIMIT 2000
        """,
        params,
    )
    map_columns = [desc[0] for desc in cur.description]
    map_points = [dict(zip(map_columns, r)) for r in cur.fetchall()]
    for point in map_points:
        point["status_group"] = _status_group(point["status"])
        # Normalize issue_date to string for JSON serialization
        if isinstance(point["issue_date"], date):
            point["issue_date"] = point["issue_date"].isoformat()
    map_meta = {
        "count": len(map_points),
        "date_start": min((point["issue_date"] for point in map_points), default=None),
        "date_end": max((point["issue_date"] for point in map_points), default=None),
        "open_count": sum(1 for point in map_points if point["status_group"] == "open"),
        "closed_count": sum(1 for point in map_points if point["status_group"] == "closed"),
    }

    cur.execute(
        """
        SELECT
            j.name,
            pc.portal_type,
            MAX(CASE WHEN sr.status = 'success' THEN sr.run_at END) AS last_success,
            MAX(sr.run_at) AS last_attempt
        FROM jurisdictions j
        LEFT JOIN pt_jurisdiction_config pc ON pc.jurisdiction_id = j.id
        LEFT JOIN pt_scrape_runs sr ON sr.jurisdiction_id = j.id
        WHERE pc.id IS NOT NULL
        GROUP BY j.id, j.name, pc.portal_type
        ORDER BY j.name
        """
    )
    last_runs_columns = [desc[0] for desc in cur.description]
    last_runs = [dict(zip(last_runs_columns, r)) for r in cur.fetchall()]
    for run in last_runs:
        # Normalize datetime to string for freshness check
        ls = run.get("last_success")
        if isinstance(ls, datetime):
            run["last_success"] = ls.isoformat()
        run["freshness"] = _freshness_label(run["last_success"])

    cur.execute(
        "SELECT COUNT(*) AS total FROM subdivisions WHERE watched = %s",
        (True,),
    )
    watch_count = cur.fetchone()[0]
    cur.close()

    return {
        "summary": {
            "current_month": current_month,
            "last_month": last_month,
            "month_delta": current_month - last_month,
            "total_permits": total_permits,
            "watchlist_count": watch_count,
        },
        "trend": trend,
        "top_subdivisions": top_subdivisions,
        "top_builders": top_builders,
        "map_points": map_points,
        "map_meta": map_meta,
        "last_runs": last_runs,
    }


def get_permits_payload(conn, filters: dict) -> dict:
    cur = conn.cursor()
    base_sql, params = _base_query(filters)
    page_size = _bounded_positive_int(filters.get("page_size"), default=50, minimum=1, maximum=250)
    requested_page = _bounded_positive_int(filters.get("page"), default=1, minimum=1)
    sort_map = {
        "issue_date_desc": "p.issue_date DESC, p.permit_number DESC",
        "issue_date_asc": "p.issue_date ASC, p.permit_number ASC",
        "builder": "COALESCE(b.canonical_name, 'Unknown Builder') ASC, p.issue_date DESC",
        "subdivision": "COALESCE(s.canonical_name, 'Unmatched') ASC, p.issue_date DESC",
        "status": "p.status ASC, p.issue_date DESC",
    }
    sort_sql = sort_map.get(filters.get("sort"), sort_map["issue_date_desc"])
    cur.execute(
        f"SELECT COUNT(*) AS total {base_sql}",
        params,
    )
    total_count = cur.fetchone()[0]
    total_pages = (total_count + page_size - 1) // page_size if total_count else 0
    page = min(requested_page, total_pages) if total_pages else 1
    offset = (page - 1) * page_size
    cur.execute(
        f"""
        SELECT
            p.id,
            p.permit_number,
            p.address,
            p.issue_date,
            p.status,
            p.permit_type,
            p.valuation,
            p.parcel_id,
            p.first_seen_at,
            p.last_updated_at,
            j.name AS jurisdiction,
            COALESCE(s.canonical_name, 'Unmatched') AS subdivision,
            COALESCE(b.canonical_name, 'Unknown Builder') AS builder,
            p.raw_subdivision_name,
            p.raw_contractor_name,
            p.raw_applicant_name,
            p.raw_licensed_professional_name
        {base_sql}
        ORDER BY {sort_sql}
        LIMIT %s OFFSET %s
        """,
        params + [page_size, offset],
    )
    columns = [desc[0] for desc in cur.description]
    permits = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    count = len(permits)
    start_index = offset + 1 if count else 0
    end_index = offset + count if count else 0
    return {
        "permits": permits,
        "count": count,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "start_index": start_index,
        "end_index": end_index,
    }


def list_subdivisions_payload(conn) -> dict:
    """List subdivisions relevant to PT: watched + those with permits.

    Joined through the county to PT's managed jurisdictions. A subdivision
    in a county with multiple PT jurisdictions shows the county-level one
    as its representative jurisdiction.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            s.id,
            s.canonical_name AS name,
            s.watched,
            s.notes,
            j.id AS jurisdiction_id,
            j.name AS jurisdiction,
            (SELECT COUNT(*) FROM pt_permits p WHERE p.subdivision_id = s.id) AS permit_count
        FROM subdivisions s
        JOIN LATERAL (
            SELECT j2.id, j2.name
            FROM jurisdictions j2
            JOIN pt_jurisdiction_config pc ON pc.jurisdiction_id = j2.id
            WHERE j2.county_id = s.county_id
            ORDER BY CASE WHEN j2.jurisdiction_type = 'county' THEN 0 ELSE 1 END, j2.name
            LIMIT 1
        ) j ON TRUE
        WHERE s.watched = TRUE
           OR EXISTS (SELECT 1 FROM pt_permits p WHERE p.subdivision_id = s.id)
        ORDER BY s.watched DESC, s.canonical_name
        """
    )
    columns = [desc[0] for desc in cur.description]
    subdivisions = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    return {"subdivisions": subdivisions}


def list_unmatched_permits_payload(conn, limit: int = 25) -> dict:
    safe_limit = max(1, min(limit, 100))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT
            p.id,
            p.permit_number,
            p.address,
            p.issue_date,
            p.status,
            p.raw_subdivision_name,
            j.id AS jurisdiction_id,
            j.name AS jurisdiction,
            COALESCE(b.canonical_name, 'Unknown Builder') AS builder
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        LEFT JOIN builders b ON b.id = p.builder_id
        WHERE p.subdivision_id IS NULL
        ORDER BY p.issue_date DESC, p.id DESC
        LIMIT %s
        """,
        (safe_limit,),
    )
    columns = [desc[0] for desc in cur.description]
    permits = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    return {"permits": permits, "count": len(permits)}


def assign_permit_subdivision(conn, permit_id: int, subdivision_id: int | None) -> dict:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.id, j.county_id
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE p.id = %s
        """,
        (permit_id,),
    )
    permit = cur.fetchone()
    if permit is None:
        cur.close()
        raise NotFoundError("Permit not found.")
    permit_county_id = permit[1]

    subdivision_name = None
    if subdivision_id is not None:
        cur.execute(
            """
            SELECT id, county_id, canonical_name
            FROM subdivisions
            WHERE id = %s
            """,
            (subdivision_id,),
        )
        subdivision = cur.fetchone()
        if subdivision is None:
            cur.close()
            raise NotFoundError("Subdivision not found.")
        if subdivision[1] != permit_county_id:
            cur.close()
            raise ValueError("Subdivision must belong to the same county as the permit's jurisdiction.")
        subdivision_name = subdivision[2]

    cur.execute(
        "UPDATE pt_permits SET subdivision_id = %s WHERE id = %s",
        (subdivision_id, permit_id),
    )
    conn.commit()
    cur.close()
    return {
        "permit_id": permit_id,
        "subdivision_id": subdivision_id,
        "subdivision": subdivision_name,
    }


def create_subdivision(conn, payload: dict) -> dict:
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("Subdivision name is required.")

    jurisdiction_id_raw = payload.get("jurisdiction_id")
    try:
        jurisdiction_id = int(jurisdiction_id_raw)
    except (TypeError, ValueError):
        raise ValueError("A valid jurisdiction is required.") from None

    cur = conn.cursor()
    cur.execute(
        "SELECT id, county_id FROM jurisdictions WHERE id = %s",
        (jurisdiction_id,),
    )
    jurisdiction = cur.fetchone()
    if jurisdiction is None:
        cur.close()
        raise ValueError("The selected jurisdiction does not exist.")
    county_id = jurisdiction[1]

    cur.execute(
        """
        SELECT id
        FROM subdivisions
        WHERE county_id = %s
          AND lower(canonical_name) = lower(%s)
        """,
        (county_id, name),
    )
    existing = cur.fetchone()
    if existing is not None:
        cur.close()
        raise ConflictError(f"{name} already exists for this county.")

    notes = payload.get("notes")
    if notes is not None:
        notes = str(notes).strip() or None

    try:
        cur.execute(
            """
            INSERT INTO subdivisions (canonical_name, county, county_id, watched, notes)
            VALUES (%s, (SELECT name FROM counties WHERE id = %s), %s, %s, %s)
            """,
            (
                name,
                county_id,
                county_id,
                True if payload.get("watched") else False,
                notes,
            ),
        )
    except psycopg2.IntegrityError as exc:
        conn.rollback()
        cur.close()
        raise ConflictError(
            "That subdivision could not be saved because it conflicts with existing data."
        ) from exc
    conn.commit()
    cur.close()
    return list_subdivisions_payload(conn)


def set_watchlist_state(conn, subdivision_id: int, watched: bool) -> dict:
    cur = conn.cursor()
    cur.execute(
        "UPDATE subdivisions SET watched = %s WHERE id = %s",
        (watched, subdivision_id),
    )
    if cur.rowcount == 0:
        cur.close()
        raise NotFoundError("Subdivision not found.")
    conn.commit()
    cur.execute(
        """
        SELECT s.id, s.canonical_name AS name, s.watched,
               (SELECT j.name FROM jurisdictions j WHERE j.county_id = s.county_id
                ORDER BY CASE WHEN j.jurisdiction_type = 'county' THEN 0 ELSE 1 END LIMIT 1) AS jurisdiction
        FROM subdivisions s
        WHERE s.id = %s
        """,
        (subdivision_id,),
    )
    columns = [desc[0] for desc in cur.description]
    row = dict(zip(columns, cur.fetchone()))
    cur.close()
    return row


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _base_query(filters: dict) -> tuple[str, list]:
    clauses = ["WHERE 1 = 1"]
    params: list = []
    if filters.get("watch_only"):
        clauses.append("AND COALESCE(s.watched, FALSE) = TRUE")
    if filters.get("jurisdiction_id"):
        clauses.append("AND p.jurisdiction_id = %s")
        params.append(filters["jurisdiction_id"])
    if filters.get("subdivision_id"):
        clauses.append("AND p.subdivision_id = %s")
        params.append(filters["subdivision_id"])
    if filters.get("builder_id"):
        clauses.append("AND p.builder_id = %s")
        params.append(filters["builder_id"])
    if filters.get("status"):
        clauses.append("AND p.status = %s")
        params.append(filters["status"])
    if filters.get("start_date"):
        clauses.append("AND p.issue_date >= %s")
        params.append(filters["start_date"])
    if filters.get("end_date"):
        clauses.append("AND p.issue_date <= %s")
        params.append(filters["end_date"])

    base_sql = f"""
    FROM pt_permits p
    JOIN jurisdictions j ON j.id = p.jurisdiction_id
    LEFT JOIN subdivisions s ON s.id = p.subdivision_id
    LEFT JOIN builders b ON b.id = p.builder_id
    {' '.join(clauses)}
    """
    return base_sql, params


def _resolve_subdivision_id(
    conn,
    jurisdiction_id: int,
    jurisdiction_name: str,
    raw_subdivision_name: str | None,
    address: str | None,
    latitude: float | None = None,
    longitude: float | None = None,
    lookup: SubdivisionGeometryLookup | None = None,
) -> int | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.id, s.canonical_name
        FROM subdivisions s
        JOIN jurisdictions j ON j.county_id = s.county_id
        WHERE j.id = %s
        """,
        (jurisdiction_id,),
    )
    subdivisions = cur.fetchall()
    cur.close()
    candidate = raw_subdivision_name or ""
    for subdivision in subdivisions:
        if names_match(subdivision[1], candidate):
            return subdivision[0]

    address_normalized = normalize_text(address)
    for subdivision in subdivisions:
        name_normalized = normalize_text(subdivision[1])
        if name_normalized and name_normalized in address_normalized:
            return subdivision[0]

    geo_match = None
    if lookup is not None:
        geo_match = lookup.lookup(
            latitude=latitude,
            longitude=longitude,
            jurisdiction_name=jurisdiction_name,
        )
    elif latitude is not None and longitude is not None:
        try:
            with SubdivisionGeometryLookup(conn) as geometry_lookup:
                geo_match = geometry_lookup.lookup(
                    latitude=latitude,
                    longitude=longitude,
                    jurisdiction_name=jurisdiction_name,
                )
        except Exception:
            geo_match = None

    if geo_match:
        return _ensure_subdivision_id(
            conn,
            jurisdiction_id,
            geo_match["name"],
            notes=f"Imported from CountyData2 {geo_match['county']} geometry.",
        )
    return None


def _ensure_subdivision_id(
    conn,
    jurisdiction_id: int,
    name: str,
    notes: str | None = None,
) -> int:
    cur = conn.cursor()
    # Resolve the county for this jurisdiction
    cur.execute("SELECT county_id FROM jurisdictions WHERE id = %s", (jurisdiction_id,))
    row = cur.fetchone()
    if row is None:
        cur.close()
        raise ValueError(f"Jurisdiction {jurisdiction_id} not found")
    county_id = row[0]

    cur.execute(
        """
        SELECT id
        FROM subdivisions
        WHERE county_id = %s
          AND lower(canonical_name) = lower(%s)
        """,
        (county_id, name),
    )
    existing = cur.fetchone()
    if existing is not None:
        cur.close()
        return existing[0]

    cur.execute(
        """
        INSERT INTO subdivisions (canonical_name, county, county_id, watched, notes)
        VALUES (%s, (SELECT name FROM counties WHERE id = %s), %s, FALSE, %s)
        RETURNING id
        """,
        (name, county_id, county_id, notes),
    )
    new_id = cur.fetchone()[0]
    cur.close()
    return new_id


def _ensure_builder_id(conn, raw_contractor_name: str | None) -> int:
    canonical_name = canonicalize_builder_name(raw_contractor_name)
    cur = conn.cursor()
    # Primary: exact LOWER(TRIM) match against builders.canonical_name OR builder_aliases.alias.
    # This closes the gap where builder_aliases already contains the correct variant but the
    # legacy names_match fuzzy scan never consulted it (see post-merge-quirks.md Entry 5).
    cur.execute(
        """
        SELECT b.id
        FROM builders b
        LEFT JOIN builder_aliases ba ON ba.builder_id = b.id
        WHERE LOWER(TRIM(b.canonical_name)) = LOWER(TRIM(%s))
           OR LOWER(TRIM(ba.alias)) = LOWER(TRIM(%s))
        LIMIT 1
        """,
        (canonical_name, canonical_name),
    )
    row = cur.fetchone()
    if row is not None:
        cur.close()
        return row[0]
    # Fallback: existing SequenceMatcher fuzzy scan for names that canonicalize close-but-not-equal
    # to an existing canonical_name (and have no matching alias row yet).
    cur.execute("SELECT id, canonical_name FROM builders ORDER BY canonical_name")
    existing = cur.fetchall()
    for builder in existing:
        if names_match(builder[1], canonical_name):
            cur.close()
            return builder[0]
    cur.execute(
        "INSERT INTO builders (canonical_name, type, scope) VALUES (%s, 'builder', 'national') RETURNING id",
        (canonical_name,),
    )
    new_id = cur.fetchone()[0]
    cur.close()
    return new_id


def _build_trend(issue_dates: list, grain: str) -> list[dict]:
    counts: defaultdict[str, int] = defaultdict(int)
    for value in issue_dates:
        if isinstance(value, date):
            current = value
        else:
            current = date.fromisoformat(str(value))
        if grain == "week":
            bucket = current - timedelta(days=current.weekday())
            label = bucket.isoformat()
        elif grain == "quarter":
            quarter = ((current.month - 1) // 3) + 1
            label = f"{current.year} Q{quarter}"
        else:
            label = current.strftime("%Y-%m")
        counts[label] += 1

    return [{"label": label, "count": counts[label]} for label in sorted(counts)]


def _freshness_label(value: str | None) -> str:
    if not value:
        return "missing"
    current = datetime.fromisoformat(value)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    age = datetime.now(UTC) - current
    if age.days > 14:
        return "stale"
    if age.days > 7:
        return "warning"
    return "fresh"


def _rows_to_dicts(cur_description, rows) -> list[dict]:
    columns = [desc[0] for desc in cur_description]
    return [dict(zip(columns, row)) for row in rows]


def _bounded_positive_int(
    value,
    *,
    default: int,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if parsed < minimum:
        return minimum
    if maximum is not None and parsed > maximum:
        return maximum
    return parsed


def _status_group(status: str | None) -> str:
    if normalize_permit_status(status) in {
        "Closed",
        "Expired",
        "Finaled",
        "Revoked",
        "Withdrawn",
    }:
        return "closed"
    return "open"


def _runnable_adapters() -> list:
    return [adapter for adapter in ADAPTERS.values() if _is_runnable_adapter(adapter)]


def _is_runnable_adapter(adapter) -> bool:
    return getattr(adapter, "mode", None) == "live"


def _load_research_index() -> dict:
    return json.loads((DATA_DIR / "source_research.json").read_text(encoding="utf-8"))


def _enrich_jurisdiction_runtime(jurisdiction: dict, research_index: dict) -> dict:
    adapter = ADAPTERS.get(jurisdiction["name"])
    config = reference_jurisdiction_by_name().get(jurisdiction["name"])
    research_entry = next(
        (
            entry
            for entry in research_index.values()
            if entry["jurisdiction"] == jurisdiction["name"]
        ),
        None,
    )
    return {
        **jurisdiction,
        **_runtime_metadata_for_adapter(adapter, research_entry, jurisdiction_config=config),
    }


def _enrich_research_runtime(research_index: dict) -> dict:
    adapters_by_slug = {adapter.slug: adapter for adapter in ADAPTERS.values()}
    config_by_name = reference_jurisdiction_by_name()
    return {
        slug: {
            **entry,
            **_runtime_metadata_for_adapter(
                adapters_by_slug.get(slug),
                entry,
                jurisdiction_config=config_by_name.get(entry["jurisdiction"]),
            ),
        }
        for slug, entry in research_index.items()
    }


def _runtime_metadata_for_adapter(
    adapter,
    research_entry: dict | None,
    *,
    jurisdiction_config: dict | None = None,
) -> dict:
    adapter_mode = getattr(adapter, "mode", None) or "unavailable"
    runnable = _is_runnable_adapter(adapter)
    jurisdiction_name = (
        research_entry.get("jurisdiction")
        if research_entry is not None
        else getattr(adapter, "display_name", None)
    )
    fragile_note = (jurisdiction_config or {}).get("fragile_note")

    operator_status = "Research only"
    operator_note = "Visible for source research, but not runnable from scrape controls yet."
    if runnable:
        operator_status = "Live"
        operator_note = "Runnable from the dashboard scrape controls."
    if fragile_note:
        operator_status = "Live (fragile)"
        operator_note = fragile_note

    return {
        "adapter_slug": getattr(adapter, "slug", None),
        "adapter_mode": adapter_mode,
        "runnable": runnable,
        "operator_status": operator_status,
        "operator_note": operator_note,
    }


def _run_single_adapter(
    conn,
    adapter,
    start: date | None,
    end: date | None,
    scrape_mode: str | None = None,
    scrape_job_id: int | None = None,
) -> dict:
    start, end = _resolve_adapter_window(conn, adapter, start, end)
    if hasattr(adapter, "reset_run_state"):
        adapter.reset_run_state()
    if hasattr(adapter, "configure_scrape_mode"):
        adapter.configure_scrape_mode(scrape_mode)
    try:
        permits = adapter.fetch_permits(start, end)
        fetch_result = getattr(adapter, "last_fetch_stats", None)
        result = ingest_permits(
            conn,
            adapter.display_name,
            permits,
            source_start_date=start.isoformat() if start else None,
            source_end_date=end.isoformat() if end else None,
        )
        missing_coordinate_addresses = [
            permit["address"]
            for permit in permits
            if permit.get("address") and (permit.get("latitude") is None or permit.get("longitude") is None)
        ]
        geocode_result = geocode_missing_permits(
            conn,
            adapter.display_name,
            addresses=missing_coordinate_addresses,
        )
        subdivision_result = backfill_subdivision_matches(conn, adapter.display_name)
    except Exception as exc:
        result = ingest_permits(
            conn,
            adapter.display_name,
            [],
            status="failed",
            error_log=str(exc),
            source_start_date=start.isoformat() if start else None,
            source_end_date=end.isoformat() if end else None,
        )
        fetch_result = getattr(adapter, "last_fetch_stats", None)
        geocode_result = None
        subdivision_result = None
    artifacts_captured = _persist_adapter_trace_artifacts(
        conn,
        adapter,
        scrape_job_id=scrape_job_id,
        scrape_run_id=result.get("scrape_run_id"),
    )
    if artifacts_captured:
        fetch_result = {
            **(fetch_result or {}),
            "artifacts_captured": artifacts_captured,
        }
    result["records_processed"] = result["permits_found"]
    window_metrics = _window_metrics_for_jurisdiction(
        conn,
        adapter.display_name,
        start=start,
        end=end,
    )
    return {
        "jurisdiction": adapter.display_name,
        "mode": adapter.mode,
        "scrape_mode": scrape_mode or "daily",
        "research": asdict(adapter.research()),
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "fetch": fetch_result,
        "result": result,
        "window_metrics": window_metrics,
        "geocode": geocode_result,
        "subdivision": subdivision_result,
    }


def _validated_scrape_request(
    *,
    jurisdiction_name: str | None,
    start_date: str | None,
    end_date: str | None,
    scrape_mode: str | None,
    validate_only: bool = False,
) -> tuple[date | None, date | None]:
    start = _parse_iso_date(start_date)
    end = _parse_iso_date(end_date)
    if start and end and start > end:
        raise ValueError("Start date must be on or before end date.")
    if scrape_mode not in {None, "daily", "weekly"}:
        raise ValueError("Scrape mode must be 'daily' or 'weekly'.")
    if not jurisdiction_name:
        return start, end

    adapter = ADAPTERS.get(jurisdiction_name)
    if adapter is None:
        raise ValueError(
            f"Unknown jurisdiction: {jurisdiction_name}. "
            f"Choose one of: {', '.join(sorted(ADAPTERS))}."
        )
    if not _is_runnable_adapter(adapter):
        raise ValueError(
            f"{jurisdiction_name} is research-only in Permit Tracker and cannot be run yet."
        )
    return start, end


def _parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def _resolve_adapter_window(
    conn,
    adapter,
    start: date | None,
    end: date | None,
) -> tuple[date | None, date | None]:
    if start is not None or end is not None:
        return start, end
    return adapter.resolve_default_window(
        has_existing_permits=_jurisdiction_has_permits(conn, adapter.display_name),
        last_success_at=_last_successful_scrape(conn, adapter.display_name),
    )


def _jurisdiction_has_permits(conn, jurisdiction_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) AS total
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE j.name = %s
        """,
        (jurisdiction_name,),
    )
    total = cur.fetchone()[0]
    cur.close()
    return bool(total)


def _last_successful_scrape(conn, jurisdiction_name: str) -> datetime | None:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sr.run_at
        FROM pt_scrape_runs sr
        JOIN jurisdictions j ON j.id = sr.jurisdiction_id
        WHERE j.name = %s AND sr.status = 'success'
        ORDER BY sr.run_at DESC
        LIMIT 1
        """,
        (jurisdiction_name,),
    )
    row = cur.fetchone()
    cur.close()
    if row is None or not row[0]:
        return None
    val = row[0]
    if isinstance(val, datetime):
        return val
    return datetime.fromisoformat(str(val))


def _window_metrics_for_jurisdiction(
    conn,
    jurisdiction_name: str,
    *,
    start: date | None,
    end: date | None,
) -> dict:
    cur = conn.cursor()
    clauses = ["j.name = %s"]
    params: list = [jurisdiction_name]
    if start is not None:
        clauses.append("p.issue_date >= %s")
        params.append(start.isoformat())
    if end is not None:
        clauses.append("p.issue_date <= %s")
        params.append(end.isoformat())

    cur.execute(
        f"""
        SELECT COUNT(*) AS permits_in_window
        FROM pt_permits p
        JOIN jurisdictions j ON j.id = p.jurisdiction_id
        WHERE {' AND '.join(clauses)}
        """,
        params,
    )
    row = cur.fetchone()
    cur.close()
    return {"permits_in_window": row[0] if row else 0}


def _find_active_scrape_job(conn, jurisdiction_name: str | None):
    cur = conn.cursor()
    if jurisdiction_name is None:
        cur.execute(
            """
            SELECT *
            FROM pt_scrape_jobs
            WHERE status IN ('pending', 'running')
            ORDER BY queued_at ASC, id ASC
            LIMIT 1
            """
        )
    else:
        cur.execute(
            """
            SELECT *
            FROM pt_scrape_jobs
            WHERE status IN ('pending', 'running')
              AND (jurisdiction_name IS NULL OR jurisdiction_name = %s)
            ORDER BY queued_at ASC, id ASC
            LIMIT 1
            """,
            (jurisdiction_name,),
        )
    row_tuple = cur.fetchone()
    if row_tuple is None:
        cur.close()
        return None
    columns = [desc[0] for desc in cur.description]
    cur.close()
    return dict(zip(columns, row_tuple))


def _claim_next_scrape_job(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id
        FROM pt_scrape_jobs
        WHERE status = 'pending'
        ORDER BY queued_at ASC, id ASC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    if row is None:
        cur.close()
        return None
    job_id = row[0]
    now = datetime.now(UTC)
    cur.execute(
        """
        UPDATE pt_scrape_jobs
        SET status = 'running',
            started_at = COALESCE(started_at, %s),
            lease_expires_at = %s,
            attempt_count = attempt_count + 1
        WHERE id = %s
          AND status = 'pending'
        """,
        (
            now.isoformat(),
            (now + timedelta(seconds=SCRAPE_JOB_LEASE_SECONDS)).isoformat(),
            job_id,
        ),
    )
    updated = cur.rowcount
    conn.commit()
    if not updated:
        cur.close()
        return None
    result = _fetch_scrape_job_row(conn, job_id)
    cur.close()
    return result


def _execute_scrape_job(conn, job_row) -> dict:
    payload = json.loads(job_row["request_payload_json"])
    result = run_adapter_scrape(
        conn,
        jurisdiction_name=payload.get("jurisdiction"),
        start_date=payload.get("start_date"),
        end_date=payload.get("end_date"),
        scrape_mode=payload.get("scrape_mode"),
        scrape_job_id=job_row["id"],
    )
    job_status, last_error, scrape_run_id, summary = _job_outcome_from_result(result)
    return _finalize_scrape_job(
        conn,
        job_id=job_row["id"],
        status=job_status,
        summary=summary,
        last_error=last_error,
        scrape_run_id=scrape_run_id,
    )


def _job_outcome_from_result(result: dict) -> tuple[str, str | None, int | None, dict]:
    if "results" in result:
        failures = [entry for entry in result["results"] if entry["result"]["status"] != "success"]
        summary = {
            "kind": "multi",
            "jurisdictions": len(result["results"]),
            "permits_found": sum(entry["result"]["permits_found"] for entry in result["results"]),
            "permits_new": sum(entry["result"]["permits_new"] for entry in result["results"]),
            "permits_updated": sum(entry["result"]["permits_updated"] for entry in result["results"]),
            "failures": len(failures),
        }
        if failures:
            error_parts = [
                f"{entry['jurisdiction']}: {entry['result'].get('error_log') or 'failed'}"
                for entry in failures
            ]
            return "failed", " | ".join(error_parts), None, summary
        return "succeeded", None, None, summary

    single_result = result["result"]
    summary = {
        "kind": "single",
        "jurisdiction": result["jurisdiction"],
        "permits_found": single_result["permits_found"],
        "permits_new": single_result["permits_new"],
        "permits_updated": single_result["permits_updated"],
        "window_metrics": result.get("window_metrics"),
    }
    if single_result["status"] != "success":
        return "failed", single_result.get("error_log") or "Scrape failed.", single_result.get("scrape_run_id"), summary
    return "succeeded", None, single_result.get("scrape_run_id"), summary


def _finalize_scrape_job(
    conn,
    *,
    job_id: int,
    status: str,
    summary: dict,
    last_error: str | None,
    scrape_run_id: int | None,
) -> dict:
    cur = conn.cursor()
    finished_at = datetime.now(UTC).isoformat()
    cur.execute(
        """
        UPDATE pt_scrape_jobs
        SET status = %s,
            finished_at = %s,
            lease_expires_at = NULL,
            last_error = %s,
            result_summary_json = %s,
            scrape_run_id = %s
        WHERE id = %s
        """,
        (
            status,
            finished_at,
            last_error,
            json.dumps(summary, sort_keys=True),
            scrape_run_id,
            job_id,
        ),
    )
    conn.commit()
    row = _fetch_scrape_job_row(conn, job_id)
    cur.close()
    return _serialize_scrape_job(row)


def _fetch_scrape_job_row(conn, job_id: int) -> dict | None:
    """Fetch a single scrape job row as a dict (or None)."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM pt_scrape_jobs WHERE id = %s", (job_id,))
    row_tuple = cur.fetchone()
    if row_tuple is None:
        cur.close()
        return None
    columns = [desc[0] for desc in cur.description]
    cur.close()
    return dict(zip(columns, row_tuple))


def _serialize_scrape_job(row) -> dict:
    payload = json.loads(row["request_payload_json"])
    summary = json.loads(row["result_summary_json"]) if row["result_summary_json"] else None
    return {
        "id": row["id"],
        "jurisdiction": row["jurisdiction_name"],
        "scope_label": row["jurisdiction_name"] or "All runnable jurisdictions",
        "status": row["status"],
        "trigger_type": row["trigger_type"],
        "queued_at": row["queued_at"],
        "started_at": row["started_at"],
        "lease_expires_at": row["lease_expires_at"],
        "finished_at": row["finished_at"],
        "attempt_count": row["attempt_count"],
        "max_attempts": row["max_attempts"],
        "retry_of_job_id": row["retry_of_job_id"],
        "scrape_run_id": row["scrape_run_id"],
        "last_error": row["last_error"],
        "payload": payload,
        "summary": summary,
        "can_retry": row["status"] in SCRAPE_JOB_TERMINAL_STATUSES,
    }


def _serialize_scraper_artifact(row) -> dict:
    metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
    return {
        "id": row["id"],
        "jurisdiction": row["jurisdiction_name"],
        "adapter_slug": row["adapter_slug"],
        "scrape_job_id": row["scrape_job_id"],
        "scrape_run_id": row["scrape_run_id"],
        "artifact_type": row["artifact_type"],
        "method": row["method"],
        "url": row["url"],
        "status_code": row["status_code"],
        "content_type": row["content_type"],
        "excerpt_text": row["excerpt_text"],
        "metadata": metadata,
        "created_at": row["created_at"],
    }


def _persist_adapter_trace_artifacts(
    conn,
    adapter,
    *,
    scrape_job_id: int | None = None,
    scrape_run_id: int | None = None,
) -> int:
    if not hasattr(adapter, "consume_trace_artifacts"):
        return 0
    artifacts = adapter.consume_trace_artifacts()
    if not artifacts:
        return 0

    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM jurisdictions WHERE name = %s",
        (adapter.display_name,),
    )
    jurisdiction_row = cur.fetchone()
    jurisdiction_id = jurisdiction_row[0] if jurisdiction_row is not None else None

    for artifact in artifacts:
        cur.execute(
            """
            INSERT INTO pt_scraper_artifacts (
                jurisdiction_id,
                adapter_slug,
                scrape_job_id,
                scrape_run_id,
                artifact_type,
                method,
                url,
                status_code,
                content_type,
                excerpt_text,
                metadata_json,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                jurisdiction_id,
                adapter.slug,
                scrape_job_id,
                scrape_run_id,
                artifact.get("artifact_type"),
                artifact.get("method"),
                artifact.get("url"),
                artifact.get("status_code"),
                artifact.get("content_type"),
                artifact.get("excerpt"),
                json.dumps(artifact.get("metadata") or {}, sort_keys=True, default=str),
                artifact.get("created_at") or datetime.now(UTC).isoformat(),
            ),
        )
    conn.commit()
    cur.close()
    return len(artifacts)


def _lookup_geocode_cache(conn, addresses: list[str]) -> dict[str, dict]:
    if not addresses:
        return {}
    cur = conn.cursor()
    placeholders = ", ".join("%s" for _ in addresses)
    cur.execute(
        f"""
        SELECT address, latitude, longitude, matched_address, match_type, match_status
        FROM pt_geocode_cache
        WHERE address IN ({placeholders})
        """,
        addresses,
    )
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    return {row["address"]: row for row in rows}


def _lookup_parcel_cache(conn, addresses: list[str]) -> dict[str, dict]:
    if not addresses:
        return {}
    cur = conn.cursor()
    placeholders = ", ".join("%s" for _ in addresses)
    cur.execute(
        f"""
        SELECT address, parcel_id, matched_address, site_address, owner_name, match_type, match_status
        FROM pt_parcel_lookup_cache
        WHERE address IN ({placeholders})
        """,
        addresses,
    )
    columns = [desc[0] for desc in cur.description]
    rows = [dict(zip(columns, r)) for r in cur.fetchall()]
    cur.close()
    return {row["address"]: row for row in rows}


def _should_query_geocode(
    address: str,
    jurisdiction_name: str | None,
    cache_row: dict | None,
) -> bool:
    if cache_row is None:
        return True
    if cache_row["latitude"] is not None and cache_row["longitude"] is not None:
        return False

    prepared = geocoding.prepare_address_for_geocoding(address, jurisdiction_name)
    if cache_row.get("match_type") == "unparseable":
        return True
    return geocoding.normalize_query_address(prepared) != geocoding.normalize_query_address(address)


def _should_query_parcel(cache_row: dict | None) -> bool:
    return cache_row is None or not cache_row.get("parcel_id")


def _apply_cached_geocodes(conn, cache_rows: dict[str, dict], jurisdiction_name: str | None) -> int:
    updated = 0
    for address, row in cache_rows.items():
        if row["latitude"] is None or row["longitude"] is None:
            continue
        updated += _apply_single_geocode(
            conn,
            address,
            row["latitude"],
            row["longitude"],
            jurisdiction_name,
        )
    return updated


def _apply_cached_parcels(conn, cache_rows: dict[str, dict], jurisdiction_name: str | None) -> int:
    updated = 0
    for address, row in cache_rows.items():
        if not row.get("parcel_id"):
            continue
        updated += _apply_single_parcel_id(
            conn,
            address,
            row["parcel_id"],
            jurisdiction_name,
        )
    return updated


def _apply_single_geocode(
    conn,
    address: str,
    latitude: float | None,
    longitude: float | None,
    jurisdiction_name: str | None,
) -> int:
    if latitude is None or longitude is None:
        return 0
    cur = conn.cursor()
    params: list = [latitude, longitude, address]
    sql = """
        UPDATE pt_permits
        SET latitude = %s, longitude = %s
        WHERE address = %s
          AND (latitude IS NULL OR longitude IS NULL)
    """
    if jurisdiction_name:
        sql += " AND jurisdiction_id = (SELECT id FROM jurisdictions WHERE name = %s)"
        params.append(jurisdiction_name)
    cur.execute(sql, params)
    count = cur.rowcount
    cur.close()
    return count


def _apply_single_parcel_id(
    conn,
    address: str,
    parcel_id: str | None,
    jurisdiction_name: str | None,
) -> int:
    if not parcel_id:
        return 0
    cur = conn.cursor()
    params: list = [parcel_id, address]
    sql = """
        UPDATE pt_permits
        SET parcel_id = %s
        WHERE address = %s
          AND (parcel_id IS NULL OR TRIM(parcel_id) = '')
    """
    if jurisdiction_name:
        sql += " AND jurisdiction_id = (SELECT id FROM jurisdictions WHERE name = %s)"
        params.append(jurisdiction_name)
    cur.execute(sql, params)
    count = cur.rowcount
    cur.close()
    return count


def _store_geocode_result(conn, result: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pt_geocode_cache (
            address, latitude, longitude, matched_address, match_type, match_status, geocoded_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(address) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude,
            matched_address = excluded.matched_address,
            match_type = excluded.match_type,
            match_status = excluded.match_status,
            geocoded_at = excluded.geocoded_at
        """,
        (
            result["address"],
            result["latitude"],
            result["longitude"],
            result.get("matched_address"),
            result.get("match_type"),
            result["match_status"],
            datetime.now(UTC).isoformat(),
        ),
    )
    cur.close()


def _store_parcel_result(conn, result: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO pt_parcel_lookup_cache (
            address, parcel_id, matched_address, site_address, owner_name, match_type, match_status, looked_up_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(address) DO UPDATE SET
            parcel_id = excluded.parcel_id,
            matched_address = excluded.matched_address,
            site_address = excluded.site_address,
            owner_name = excluded.owner_name,
            match_type = excluded.match_type,
            match_status = excluded.match_status,
            looked_up_at = excluded.looked_up_at
        """,
        (
            result["address"],
            result.get("parcel_id"),
            result.get("matched_address"),
            result.get("site_address"),
            result.get("owner_name"),
            result.get("match_type"),
            result["match_status"],
            datetime.now(UTC).isoformat(),
        ),
    )
    cur.close()
