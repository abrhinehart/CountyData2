"""Persist extracted commission items into the unified schema.

Ported from Commission Radar's ``record_inserter``. The original module
wrote ``Project`` / ``ProjectAlias`` / ``Phase`` / ``EntitlementAction`` /
``Commissioner`` / ``CommissionerVote`` rows. In the unified CountyData2
schema the ``projects`` table was collapsed into the shared
``subdivisions`` table. The important schema differences are:

* ``Subdivision`` identifies by ``(canonical_name, county_id)`` rather than
  ``(name, jurisdiction_id)``. CR only ever knows the jurisdiction, so we
  resolve ``county_id`` (and the legacy ``county`` text column) by joining
  through ``jurisdictions``.
* ``Subdivision`` has **no** ``acreage``/``lot_count`` columns. ``acreage``
  rolls up into ``platted_acreage``; ``lot_count`` is only stored on the
  ``phases`` table and on each ``CrEntitlementAction`` row.
* ``Phase`` now FKs ``subdivision_id`` directly and carries no
  ``jurisdiction_id``. Uniqueness is ``(subdivision_id, name)``.
* ``SubdivisionAlias`` replaces ``ProjectAlias``. It FKs ``subdivision_id``
  and keeps the ``source`` column (CR entries are written with
  ``source='extracted'``).
* ``CrEntitlementAction`` uses ``subdivision_id`` (not ``project_id``) and
  is otherwise field-compatible with CR's ``EntitlementAction``.

The caller still passes a ``jurisdiction_id``; the function resolves the
owning county internally. A missing jurisdiction or missing county row is
treated as a hard error — ``insert_records`` runs inside the extraction
pipeline, not at user-facing request time, so noisy failures are preferred
over silently writing orphan subdivisions.
"""

import json
from datetime import date

from sqlalchemy import func

from modules.commission.constants import LAND_USE_LARGE_SCALE_ACRES
from modules.commission.models import (
    Commissioner,
    CommissionerVote,
    EntitlementAction,
    Jurisdiction,
    Phase,
    Project,  # alias for Subdivision
)
from modules.commission.normalization import normalize_approval_type, normalize_text
from shared.models import County, SubdivisionAlias


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date(date_str):
    """Parse a YYYY-MM-DD string to a date object, or return None."""
    if date_str is None or date_str == "":
        return None
    if isinstance(date_str, date):
        return date_str
    if not isinstance(date_str, str):
        raise ValueError(f"Expected YYYY-MM-DD date string, got {type(date_str).__name__}")
    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise ValueError(f"Invalid YYYY-MM-DD date: {date_str}") from exc


def _normalize_parcel_ids(parcel_ids):
    if not parcel_ids:
        return None
    normalized = sorted(
        normalized_id
        for normalized_id in (normalize_text(parcel_id) for parcel_id in parcel_ids)
        if normalized_id
    )
    if not normalized:
        return None
    return tuple(normalized)


def _identity_keys(item, project_name=None):
    keys = []
    name_value = project_name if project_name is not None else item.get("project_name")
    normalized_name = normalize_text(name_value)
    if normalized_name:
        keys.append(("project_name", normalized_name))

    normalized_case = normalize_text(item.get("case_number"))
    if normalized_case:
        keys.append(("case_number", normalized_case))

    normalized_ordinance = normalize_text(item.get("ordinance_number"))
    if normalized_ordinance:
        keys.append(("ordinance_number", normalized_ordinance))

    normalized_parcel_ids = _normalize_parcel_ids(item.get("parcel_ids"))
    if normalized_parcel_ids:
        keys.append(("parcel_ids", normalized_parcel_ids))

    normalized_address = normalize_text(item.get("address"))
    if normalized_address:
        keys.append(("address", normalized_address))

    normalized_applicant = normalize_text(item.get("applicant_name"))
    if normalized_applicant:
        keys.append(("applicant_name", normalized_applicant))

    return keys


def _find_existing_project(project_cache, item):
    for field_name in ("project_name", "case_number", "ordinance_number", "parcel_ids", "address", "applicant_name"):
        for key in _identity_keys(item):
            if key[0] == field_name and key in project_cache:
                return project_cache[key]
    return None


def _resolve_jurisdiction_county(session, jurisdiction_id: int) -> tuple[int, str]:
    """Return ``(county_id, county_text_name)`` for a jurisdiction.

    CR only stores ``jurisdiction_id`` on extracted items, but the shared
    ``subdivisions`` table is keyed by county. This lookup is cached at the
    call site (``insert_records`` resolves it once per batch).
    """
    row = (
        session.query(County.id, County.name)
        .join(Jurisdiction, Jurisdiction.county_id == County.id)
        .filter(Jurisdiction.id == jurisdiction_id)
        .first()
    )
    if row is None:
        raise ValueError(
            f"Cannot locate county for jurisdiction_id={jurisdiction_id}; "
            "seed jurisdictions before extracting."
        )
    return int(row[0]), str(row[1])


def _find_subdivision_in_db(session, county_id: int, project_name: str):
    """Find an existing Subdivision in a county by canonical name or alias."""
    normalized = normalize_text(project_name)
    if not normalized:
        return None

    # Direct canonical_name match (case-insensitive).
    subdivision = (
        session.query(Project)
        .filter(
            Project.county_id == county_id,
            func.lower(Project.canonical_name) == normalized,
        )
        .first()
    )
    if subdivision:
        return subdivision

    # Alias match, scoped to subdivisions in the same county.
    alias_row = (
        session.query(SubdivisionAlias)
        .join(Project, Project.id == SubdivisionAlias.subdivision_id)
        .filter(
            Project.county_id == county_id,
            func.lower(SubdivisionAlias.alias) == normalized,
        )
        .first()
    )
    if alias_row:
        return (
            session.query(Project)
            .filter(Project.id == alias_row.subdivision_id)
            .first()
        )
    return None


def _maybe_create_alias(session, subdivision, extracted_name):
    """Record extracted names that differ from ``subdivision.canonical_name``."""
    if not extracted_name:
        return
    normalized_extracted = normalize_text(extracted_name)
    normalized_stored = normalize_text(subdivision.canonical_name)
    if not normalized_extracted or normalized_extracted == normalized_stored:
        return
    existing = (
        session.query(SubdivisionAlias)
        .filter(
            SubdivisionAlias.subdivision_id == subdivision.id,
            func.lower(SubdivisionAlias.alias) == normalized_extracted,
        )
        .first()
    )
    if not existing:
        session.add(
            SubdivisionAlias(
                subdivision_id=subdivision.id,
                alias=extracted_name.strip(),
                source="extracted",
            )
        )


def _infer_land_use_scale(item):
    """Infer land_use_scale from acreage when not explicitly extracted."""
    if item.get("land_use_scale"):
        return item["land_use_scale"]
    approval_type = item.get("normalized_approval_type") or item.get("approval_type", "")
    if normalize_approval_type(approval_type) != "land_use":
        return None
    acreage = item.get("acreage")
    if acreage is not None:
        return "large_scale" if acreage >= LAND_USE_LARGE_SCALE_ACRES else "small_scale"
    return None


def _register_project(project_cache, subdivision, item, project_name=None):
    for key in _identity_keys(
        item, project_name=project_name or subdivision.canonical_name
    ):
        project_cache[key] = subdivision


def _enrich_subdivision(subdivision, item):
    """Opportunistically fill in Subdivision-level fields from an extracted item.

    Subdivisions own ``platted_acreage``, ``proposed_land_use``,
    ``proposed_zoning``, ``location_description`` and ``notes``. They do not
    own ``lot_count`` — any per-phase lot counts live on the ``phases`` table
    (and the extracted value is still captured on the entitlement action).
    """
    if not subdivision.location_description and item.get("address"):
        subdivision.location_description = item.get("address")

    new_acreage = item.get("acreage")
    if new_acreage is not None:
        if subdivision.platted_acreage is None:
            subdivision.platted_acreage = new_acreage
        elif subdivision.platted_acreage != new_acreage:
            note = (
                f"Acreage changed: {subdivision.platted_acreage} -> {new_acreage}. "
            )
            subdivision.notes = (subdivision.notes or "") + note
            subdivision.platted_acreage = new_acreage

    if subdivision.proposed_land_use is None and item.get("proposed_land_use"):
        subdivision.proposed_land_use = item["proposed_land_use"]
    if subdivision.proposed_zoning is None and item.get("proposed_zoning"):
        subdivision.proposed_zoning = item["proposed_zoning"]


def _find_or_create_phase(session, phase_cache, subdivision, phase_name, item, counts):
    """Find or create a Phase for the given subdivision and phase_name.

    Returns the Phase, or None if phase_name is empty.
    Increments counts["phases"] when a new Phase is created.
    """
    if not phase_name:
        return None

    normalized = normalize_text(phase_name)
    if not normalized:
        return None

    cache_key = (subdivision.id, normalized)
    if cache_key in phase_cache:
        phase = phase_cache[cache_key]
        _enrich_phase(phase, item)
        return phase

    phase = (
        session.query(Phase)
        .filter(
            Phase.subdivision_id == subdivision.id,
            func.lower(Phase.name) == normalized,
        )
        .first()
    )

    if phase is None:
        phase = Phase(
            subdivision_id=subdivision.id,
            name=phase_name,
            entitlement_status="in_progress",
            acreage=item.get("acreage"),
            lot_count=item.get("lot_count"),
            proposed_land_use=item.get("proposed_land_use"),
            proposed_zoning=item.get("proposed_zoning"),
        )
        session.add(phase)
        session.flush()
        counts["phases"] += 1

    _enrich_phase(phase, item)
    phase_cache[cache_key] = phase
    return phase


def _enrich_phase(phase, item):
    if phase.acreage is None and item.get("acreage") is not None:
        phase.acreage = item.get("acreage")
    if phase.lot_count is None and item.get("lot_count") is not None:
        phase.lot_count = item.get("lot_count")
    if phase.proposed_land_use is None and item.get("proposed_land_use"):
        phase.proposed_land_use = item["proposed_land_use"]
    if phase.proposed_zoning is None and item.get("proposed_zoning"):
        phase.proposed_zoning = item["proposed_zoning"]


def _get_or_create_commissioner(session, commissioner_cache, jurisdiction_id, name, title):
    """Look up or create a Commissioner by (jurisdiction_id, name).

    Uses an in-memory cache to avoid repeated DB queries within a batch.
    Updates title if previously null and now provided.
    """
    cache_key = (jurisdiction_id, name.strip().lower())
    if cache_key in commissioner_cache:
        commissioner = commissioner_cache[cache_key]
        if commissioner.title is None and title:
            commissioner.title = title
        return commissioner

    commissioner = (
        session.query(Commissioner)
        .filter(
            Commissioner.jurisdiction_id == jurisdiction_id,
            func.lower(Commissioner.name) == name.strip().lower(),
        )
        .first()
    )

    if commissioner is None:
        commissioner = Commissioner(
            jurisdiction_id=jurisdiction_id,
            name=name.strip(),
            title=title,
        )
        session.add(commissioner)
        session.flush()
    elif commissioner.title is None and title:
        commissioner.title = title

    commissioner_cache[cache_key] = commissioner
    return commissioner


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def insert_records(
    session,
    items: list[dict],
    source_document_id: int,
    jurisdiction_id: int,
    meeting_date: str | None,
) -> dict[str, int]:
    """Insert extracted items as database records in the unified schema."""
    counts = {"projects": 0, "phases": 0, "entitlement_actions": 0, "commissioner_votes": 0}
    meeting_date_obj = _parse_date(meeting_date)

    # Resolve (county_id, county_text) once per batch. All subdivisions
    # created below land in this county.
    county_id, county_text = _resolve_jurisdiction_county(session, jurisdiction_id)

    project_cache: dict = {}
    phase_cache: dict = {}
    commissioner_cache: dict = {}
    all_pending_votes: list = []

    for item in items:
        subdivision = _find_existing_project(project_cache, item)
        normalized_approval_type = normalize_approval_type(
            item.get("normalized_approval_type") or item.get("approval_type", "")
        )
        project_name = item.get("project_name")

        if subdivision is None and project_name and normalized_approval_type != "text_amendment":
            subdivision = _find_subdivision_in_db(session, county_id, project_name)

            if subdivision is None:
                subdivision = Project(
                    canonical_name=project_name,
                    county=county_text,
                    county_id=county_id,
                    entitlement_status="in_progress",
                    location_description=item.get("address"),
                    platted_acreage=item.get("acreage"),
                    source="commission",
                )
                session.add(subdivision)
                session.flush()
                counts["projects"] += 1

        if subdivision is not None:
            _enrich_subdivision(subdivision, item)
            _register_project(
                project_cache,
                subdivision,
                item,
                project_name=subdivision.canonical_name,
            )

        # Find or create Phase if phase_name is present
        phase = None
        phase_name = item.get("phase_name")
        if subdivision is not None and phase_name:
            phase = _find_or_create_phase(
                session, phase_cache, subdivision, phase_name, item, counts,
            )

        parcel_ids = item.get("parcel_ids")
        parcel_ids_text = json.dumps(parcel_ids) if parcel_ids else None

        # Create alias if extracted name differs from stored canonical name.
        if subdivision is not None:
            _maybe_create_alias(session, subdivision, project_name)

        action = EntitlementAction(
            source_document_id=source_document_id,
            subdivision_id=subdivision.id if subdivision is not None else None,
            phase_id=phase.id if phase is not None else None,
            case_number=item.get("case_number"),
            ordinance_number=item.get("ordinance_number"),
            parcel_ids=parcel_ids_text,
            address=item.get("address"),
            approval_type=normalized_approval_type,
            outcome=item.get("outcome"),
            vote_detail=item.get("vote_detail"),
            conditions=item.get("conditions"),
            reading_number=item.get("reading_number"),
            scheduled_first_reading_date=_parse_date(item.get("scheduled_first_reading_date")),
            scheduled_final_reading_date=_parse_date(item.get("scheduled_final_reading_date")),
            action_summary=item.get("action_summary"),
            applicant_name=item.get("applicant_name"),
            current_land_use=item.get("current_land_use"),
            proposed_land_use=item.get("proposed_land_use"),
            current_zoning=item.get("current_zoning"),
            proposed_zoning=item.get("proposed_zoning"),
            acreage=item.get("acreage"),
            lot_count=item.get("lot_count"),
            project_name=project_name,
            phase_name=phase_name,
            land_use_scale=_infer_land_use_scale(item),
            action_requested=item.get("action_requested"),
            meeting_date=meeting_date_obj,
            agenda_section=item.get("agenda_section"),
            multi_project_flag=item.get("multi_project_flag", False),
            backup_doc_filename=item.get("backup_doc_filename"),
            needs_review=item.get("needs_review", False),
            review_notes=item.get("review_notes"),
        )
        session.add(action)
        counts["entitlement_actions"] += 1

        # Collect commissioner votes for deferred creation after flush.
        pending_votes = []
        for v in item.get("commissioner_votes", []):
            commissioner = _get_or_create_commissioner(
                session, commissioner_cache, jurisdiction_id,
                v["name"], v.get("title"),
            )
            pending_votes.append((action, commissioner, v))
            counts["commissioner_votes"] += 1
        all_pending_votes.extend(pending_votes)

    # Single flush assigns IDs to all actions and new subdivisions/phases.
    session.flush()

    # Now create commissioner votes — action.id and commissioner.id are available.
    for action, commissioner, v in all_pending_votes:
        action.commissioner_votes.append(
            CommissionerVote(
                commissioner_id=commissioner.id,
                vote=v["vote"],
                made_motion=v.get("made_motion", False),
                seconded_motion=v.get("seconded_motion", False),
            )
        )

    session.flush()

    # Update lifecycle stage for all affected subdivisions.
    from modules.commission.lifecycle import update_project_lifecycle

    updated_subdivision_ids: set[int] = set()
    for item in items:
        subdivision = _find_existing_project(project_cache, item)
        if subdivision and subdivision.id not in updated_subdivision_ids:
            update_project_lifecycle(session, subdivision)
            updated_subdivision_ids.add(subdivision.id)
    session.flush()

    # Backfill acreage from subdivision.platted_acreage onto sibling actions
    # that didn't capture it directly. ``lot_count`` is no longer stored on
    # the subdivision, so it can't be backfilled from this level.
    for subdivision_id in updated_subdivision_ids:
        subdivision = session.get(Project, subdivision_id)
        if subdivision is None or subdivision.platted_acreage is None:
            continue
        siblings = (
            session.query(EntitlementAction)
            .filter(EntitlementAction.subdivision_id == subdivision_id)
            .all()
        )
        for sibling in siblings:
            if sibling.acreage is None:
                sibling.acreage = subdivision.platted_acreage
    session.flush()

    return counts
