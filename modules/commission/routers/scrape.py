"""Scraping router — fetch and process documents from government websites."""

import json
import os
import time

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from shared.sa_database import get_db, SessionLocal
from modules.commission.models import (
    CrJurisdictionConfig,
    CrSourceDocument as SourceDocument,
    Jurisdiction,
    SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
)

from modules.commission.routers.helpers import (
    _document_storage_slug,
    _json_error,
    _send,
    PDF_STORAGE_DIR,
)
from modules.commission.routers.process import process_document

# TODO: verify schema — these supporting modules have not yet been ported
# from commission_radar to modules.commission. The router imports them
# defensively so the module can still be loaded during the migration.
try:
    from modules.commission.collection_review import (
        flag_source_document_for_review,
        inspect_listing_for_collection_review,
        inspect_primary_document_for_collection_review,
        should_queue_collection_review,
        source_document_status_label,
    )
except ImportError:  # pragma: no cover
    flag_source_document_for_review = None  # type: ignore
    inspect_listing_for_collection_review = None  # type: ignore
    inspect_primary_document_for_collection_review = None  # type: ignore

    def should_queue_collection_review(*args, **kwargs):  # type: ignore
        return False

    def source_document_status_label(*args, **kwargs):  # type: ignore
        return "unknown"

try:
    from modules.commission.config import SCRAPE_DELAY_SECONDS
except ImportError:  # pragma: no cover
    SCRAPE_DELAY_SECONDS = 0

try:
    from modules.commission.intake import (
        IntakeValidationError,
        build_scrape_config,
        find_listing_duplicate,
        get_scrapable_jurisdictions,
        normalize_external_document_id,
        validate_document_file,
        validate_scrape_date_range,
    )
except ImportError:  # pragma: no cover
    class IntakeValidationError(Exception):  # type: ignore
        pass

    build_scrape_config = None  # type: ignore
    find_listing_duplicate = None  # type: ignore
    get_scrapable_jurisdictions = None  # type: ignore
    normalize_external_document_id = None  # type: ignore
    validate_document_file = None  # type: ignore
    validate_scrape_date_range = None  # type: ignore

from modules.commission.scrapers import PlatformScraper


router = APIRouter(prefix="/scrape")


@router.get("/jurisdictions")
def scrape_jurisdictions(db: Session = Depends(get_db)):
    """List jurisdictions that can be scraped.

    ``get_scrapable_jurisdictions`` normally applies the commission's scraper
    config criteria. If that helper has not yet been ported we fall back to
    a direct query against ``CrJurisdictionConfig``.
    """
    if get_scrapable_jurisdictions is not None:
        rows = get_scrapable_jurisdictions(db)
        return [{"slug": r.slug, "name": r.name} for r in rows]

    rows = (
        db.query(Jurisdiction)
        .join(
            CrJurisdictionConfig,
            CrJurisdictionConfig.jurisdiction_id == Jurisdiction.id,
        )
        .filter(CrJurisdictionConfig.is_active == True)  # noqa: E712
        .filter(CrJurisdictionConfig.agenda_platform.isnot(None))
        .filter(CrJurisdictionConfig.agenda_platform != "manual")
        .order_by(Jurisdiction.name)
        .all()
    )
    return [{"slug": r.slug, "name": r.name} for r in rows]


@router.post("/listings")
def scrape_listings(
    jurisdiction: str | None = Form(None),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    db: Session = Depends(get_db),
):
    jurisdiction_slug = jurisdiction or None

    try:
        start_date_v, end_date_v = validate_scrape_date_range(start_date, end_date)
        juris_list = get_scrapable_jurisdictions(db, jurisdiction_slug)
        if not juris_list:
            return _json_error("No scrapable jurisdictions found.")

        all_listings = []
        for juris in juris_list:
            try:
                scraper = PlatformScraper.for_platform(juris.agenda_platform)
            except ValueError:
                continue

            scrape_config = build_scrape_config(juris)
            listings = scraper.fetch_listings(scrape_config, start_date_v, end_date_v)

            for listing in listings:
                external_document_id = normalize_external_document_id(
                    juris.agenda_platform,
                    listing.document_type,
                    listing.document_id,
                )
                duplicate = find_listing_duplicate(
                    db,
                    jurisdiction_id=juris.id,
                    platform=juris.agenda_platform,
                    document_type=listing.document_type,
                    document_id=listing.document_id,
                    source_url=listing.url,
                    filename=listing.filename,
                )
                listing_review = inspect_listing_for_collection_review(
                    listing.document_type,
                    filename=listing.filename,
                    listing_title=listing.title,
                )
                if duplicate:
                    status = source_document_status_label(
                        duplicate.existing_status,
                        duplicate_reason=duplicate.reason,
                    )
                    review_reason = duplicate.existing_failure_reason
                elif should_queue_collection_review(listing_review):
                    status = source_document_status_label(
                        SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW
                    )
                    review_reason = listing_review.review_reason
                else:
                    status = "new"
                    review_reason = None
                all_listings.append(
                    {
                        "jurisdiction": juris.name,
                        "jurisdiction_slug": juris.slug,
                        "title": listing.title,
                        "date": listing.date_str,
                        "filename": listing.filename,
                        "document_type": listing.document_type,
                        "source_url": listing.url,
                        "external_document_id": external_document_id,
                        "already_processed": duplicate is not None,
                        "duplicate_reason": duplicate.reason if duplicate else None,
                        "status": status,
                        "review_reason": review_reason,
                    }
                )

        return all_listings
    except IntakeValidationError as exc:
        return _json_error(str(exc))


@router.post("/run")
def scrape_run(
    jurisdiction: str | None = Form(None),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    skip_filter: str | None = Form(None),
    download_only: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        jurisdiction_slug = jurisdiction or None
        start_date_v, end_date_v = validate_scrape_date_range(start_date, end_date)
        skip_filter_v = skip_filter == "on"
        download_only_v = download_only == "on"
    except IntakeValidationError as exc:
        return _json_error(str(exc))

    # Upfront validation against the request-scoped session.
    try:
        if not get_scrapable_jurisdictions(db, jurisdiction_slug):
            return _json_error("No scrapable jurisdictions found.")
    except IntakeValidationError as exc:
        return _json_error(str(exc))

    def generate():
        # Streamed responses need their own session scope.
        session = SessionLocal()
        try:
            juris_list = get_scrapable_jurisdictions(session, jurisdiction_slug)
            if not juris_list:
                yield _send({"error": "No scrapable jurisdictions found."})
                return

            # Gather all listings
            all_work = []
            for juris in juris_list:
                try:
                    scraper = PlatformScraper.for_platform(juris.agenda_platform)
                except ValueError:
                    continue
                scrape_config = build_scrape_config(juris)
                listings = scraper.fetch_listings(
                    scrape_config, start_date_v, end_date_v
                )
                for listing in listings:
                    all_work.append((juris, listing, scraper))

            total = len(all_work)
            if total == 0:
                yield _send(
                    {
                        "done": True,
                        "summary": {
                            "found": 0,
                            "downloaded": 0,
                            "skipped": 0,
                            "flagged": 0,
                            "processed": 0,
                            "errors": 0,
                        },
                    }
                )
                return

            yield _send(
                {
                    "phase": "init",
                    "total": total,
                    "message": f"Found {total} documents across {len(juris_list)} jurisdiction(s)",
                }
            )

            counts = {
                "found": total,
                "downloaded": 0,
                "skipped": 0,
                "flagged": 0,
                "processed": 0,
                "errors": 0,
            }

            for idx, (juris, listing, scraper) in enumerate(all_work, 1):
                external_document_id = normalize_external_document_id(
                    juris.agenda_platform,
                    listing.document_type,
                    listing.document_id,
                )
                duplicate = find_listing_duplicate(
                    session,
                    jurisdiction_id=juris.id,
                    platform=juris.agenda_platform,
                    document_type=listing.document_type,
                    document_id=listing.document_id,
                    source_url=listing.url,
                    filename=listing.filename,
                )
                if duplicate:
                    counts["skipped"] += 1
                    status = source_document_status_label(
                        duplicate.existing_status,
                        duplicate_reason=duplicate.reason,
                    )
                    yield _send(
                        {
                            "phase": "skip",
                            "current": idx,
                            "total": total,
                            "filename": listing.filename,
                            "reason": f"already collected ({status})",
                            "duplicate_reason": duplicate.reason,
                            "external_document_id": external_document_id,
                            "source_url": listing.url,
                        }
                    )
                    continue

                # Download
                yield _send(
                    {
                        "phase": "download",
                        "current": idx,
                        "total": total,
                        "filename": listing.filename,
                        "jurisdiction": juris.name,
                    }
                )
                slug = _document_storage_slug(juris)
                output_dir = os.path.join(PDF_STORAGE_DIR, slug)
                try:
                    filepath = scraper.download_document(listing, output_dir)
                    counts["downloaded"] += 1
                except Exception as e:
                    counts["errors"] += 1
                    yield _send(
                        {
                            "phase": "error",
                            "current": idx,
                            "total": total,
                            "filename": listing.filename,
                            "error": f"Download failed: {e}",
                        }
                    )
                    continue

                try:
                    file_format = validate_document_file(filepath, listing.filename)
                except IntakeValidationError as exc:
                    counts["errors"] += 1
                    yield _send(
                        {
                            "phase": "error",
                            "current": idx,
                            "total": total,
                            "filename": listing.filename,
                            "error": str(exc),
                        }
                    )
                    continue

                inspection = inspect_primary_document_for_collection_review(
                    filepath,
                    file_format,
                    listing.document_type,
                    filename=listing.filename,
                    listing_title=listing.title,
                )
                if should_queue_collection_review(inspection):
                    flagged_doc = flag_source_document_for_review(
                        session,
                        jurisdiction_id=juris.id,
                        file_path=filepath,
                        filename=listing.filename,
                        file_format=file_format,
                        doc_type=listing.document_type,
                        meeting_date=listing.date_str,
                        source_url=listing.url,
                        external_document_id=external_document_id,
                        inspection=inspection,
                    )
                    session.commit()
                    counts["flagged"] += 1
                    yield _send(
                        {
                            "phase": "flagged",
                            "current": idx,
                            "total": total,
                            "filename": listing.filename,
                            "reason": inspection.review_reason,
                            "review_id": flagged_doc.id,
                        }
                    )
                    continue

                if not download_only_v:
                    yield _send(
                        {
                            "phase": "process",
                            "current": idx,
                            "total": total,
                            "filename": listing.filename,
                        }
                    )

                    error_occurred = False
                    for event in process_document(
                        session,
                        filepath,
                        listing.filename,
                        file_format,
                        juris.slug,
                        listing.document_type,
                        skip_filter_v,
                        False,
                        override_date=listing.date_str,
                        label_prefix=f"[{idx}/{total}] ",
                        source_url=listing.url,
                        external_document_id=external_document_id,
                        collection_review_note=inspection.audit_note,
                    ):
                        yield event
                        try:
                            parsed = json.loads(
                                event.removeprefix("data: ").strip()
                            )
                            if "error" in parsed:
                                error_occurred = True
                        except (json.JSONDecodeError, AttributeError):
                            pass

                    if error_occurred:
                        counts["errors"] += 1
                    else:
                        counts["processed"] += 1
                        # Persist structured event items if the listing carries them
                        if listing.structured_items:
                            try:
                                source_doc = (
                                    session.query(SourceDocument)
                                    .filter_by(
                                        jurisdiction_id=juris.id,
                                        external_document_id=external_document_id,
                                    )
                                    .order_by(SourceDocument.id.desc())
                                    .first()
                                )
                                if source_doc is not None:
                                    source_doc.structured_event_items = listing.structured_items
                                    session.commit()
                            except Exception:
                                session.rollback()

                if SCRAPE_DELAY_SECONDS > 0:
                    time.sleep(SCRAPE_DELAY_SECONDS)

            yield _send({"done": True, "summary": counts})

        except Exception as e:
            session.rollback()
            yield _send({"error": f"Unexpected error: {e}"})
        finally:
            session.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
