"""Post-extraction acreage enrichment pipeline.

Three strategies, applied in order of cost:
1. Cross-action propagation — copy acreage from sibling actions on the same project (free).
2. Agenda HTML parsing — extract acreage from CivicPlus agenda description fields (free).
3. Backup PDF extraction — download per-item PDF, convert the first 3 pages to
   text, and extract acreage/lot count via a focused Claude prompt (API cost,
   but much cheaper than full extraction).

Ported from commission_radar.acreage_enricher. Schema notes for CountyData2:
- The old Project model is aliased to Subdivision in modules.commission.models.
- Subdivision has ``platted_acreage`` (not ``acreage``) and has NO ``lot_count``
  column; lot_count lives on ``CrEntitlementAction`` and ``Phase`` only.
- Subdivision has no ``jurisdiction_id`` — the authoritative jurisdiction link
  is via ``CrSourceDocument.jurisdiction_id``.
- ``_resolve_jurisdiction`` now returns a ``JurisdictionView`` so downstream
  ``packet_fetcher`` helpers see ``agenda_platform`` / ``agenda_source_url`` /
  ``config`` attributes that used to live directly on ``Jurisdiction``.
"""

import json
import logging
import os
import tempfile
import time

import anthropic

from modules.commission.config import CLAUDE_MODEL, require_anthropic_api_key
from modules.commission.constants import PACKET_ENRICHMENT_MAX_PAGES
from modules.commission.models import EntitlementAction, Jurisdiction, Phase, Project, SourceDocument
from modules.commission.intake import _wrap_jurisdiction

logger = logging.getLogger("commission_radar.acreage_enricher")

ACREAGE_EXTRACTION_PROMPT = """Extract the acreage and lot count from this development application document.

Look for:
- Total acreage / site size (e.g., "10.5 acres", "approximately 25 acres", "+/- 15 acres")
- Number of lots or units (e.g., "150 lots", "200 dwelling units", "300 units")

Return ONLY a JSON object: {{"acreage": number_or_null, "lot_count": number_or_null}}

If no acreage or lot count is mentioned, return {{"acreage": null, "lot_count": null}}.

--- DOCUMENT TEXT (first pages of agenda packet) ---
{text}"""

API_MAX_RETRIES = 3
API_RETRY_BASE_DELAY = 5


# ── Shared helpers ────────────────────────────────────────────────────────


def _actions_missing_packet_data(session, jurisdiction_id=None):
    """Return actions whose project is still missing acreage or lot count."""
    query = (
        session.query(EntitlementAction)
        .join(Project, EntitlementAction.subdivision_id == Project.id)
        .filter(EntitlementAction.subdivision_id.isnot(None))
        .filter(
            (
                EntitlementAction.acreage.is_(None)
                & Project.platted_acreage.is_(None)
            )
            | EntitlementAction.lot_count.is_(None)
        )
    )
    if jurisdiction_id:
        query = (
            query.join(
                SourceDocument,
                EntitlementAction.source_document_id == SourceDocument.id,
            )
            .filter(SourceDocument.jurisdiction_id == jurisdiction_id)
        )
    return query.all()


def _resolve_jurisdiction(session, action):
    """Resolve the JurisdictionView for an action via its source document.

    In the unified schema Subdivision no longer carries a jurisdiction_id;
    the authoritative link is CrSourceDocument.jurisdiction_id. We also
    wrap the result in a JurisdictionView so callers (packet_fetcher) see
    the agenda_platform/agenda_source_url/config attributes that used to
    live directly on Jurisdiction.
    """
    if not action.source_document_id:
        return None
    source_doc = session.get(SourceDocument, action.source_document_id)
    if source_doc is None or source_doc.jurisdiction_id is None:
        return None
    jurisdiction = session.get(Jurisdiction, source_doc.jurisdiction_id)
    if jurisdiction is None:
        return None
    return _wrap_jurisdiction(session, jurisdiction)


def _apply_acreage(session, project_id, acreage, lot_count, dry_run=False):
    """Apply acreage/lot_count to a project and all actions missing either field.

    Returns (actions_updated, projects_updated) counts.
    """
    project = session.get(Project, project_id)
    actions_updated = 0
    projects_updated = 0

    project_changed = False
    if project:
        if acreage is not None and project.platted_acreage is None:
            if not dry_run:
                project.platted_acreage = acreage
            project_changed = True
        # Subdivision has no lot_count column in CD2 — lot_count lives on
        # CrEntitlementAction and Phase. The action loop below still writes it.
    if project_changed:
        projects_updated = 1

    project_actions = (
        session.query(EntitlementAction)
        .filter(
            EntitlementAction.subdivision_id == project_id,
            (EntitlementAction.acreage.is_(None)) | (EntitlementAction.lot_count.is_(None)),
        )
        .all()
    )
    for pa in project_actions:
        action_changed = False
        if not dry_run:
            if acreage is not None and pa.acreage is None:
                pa.acreage = acreage
                action_changed = True
            if lot_count is not None and pa.lot_count is None:
                pa.lot_count = lot_count
                action_changed = True
        else:
            action_changed = (
                (acreage is not None and pa.acreage is None)
                or (lot_count is not None and pa.lot_count is None)
            )
        if action_changed:
            actions_updated += 1

    return actions_updated, projects_updated


# ── Stage 1: Sibling propagation (free) ──────────────────────────────────


def propagate_acreage_from_siblings(session, jurisdiction_id=None, dry_run=False):
    """Copy acreage from sibling actions on the same project.

    Returns:
        dict with counts: actions_updated, phases_updated, projects_updated
    """
    counts = {"actions_updated": 0, "phases_updated": 0, "projects_updated": 0}

    query = (
        session.query(EntitlementAction)
        .join(Project, EntitlementAction.subdivision_id == Project.id)
        .filter(EntitlementAction.subdivision_id.isnot(None))
        .filter(
            (
                EntitlementAction.acreage.is_(None)
                & Project.platted_acreage.is_(None)
            )
            | EntitlementAction.lot_count.is_(None)
        )
    )
    if jurisdiction_id:
        query = (
            query.join(
                SourceDocument,
                EntitlementAction.source_document_id == SourceDocument.id,
            )
            .filter(SourceDocument.jurisdiction_id == jurisdiction_id)
        )

    actions_missing = query.all()
    if not actions_missing:
        return counts

    by_project = {}
    for action in actions_missing:
        by_project.setdefault(action.subdivision_id, []).append(action)

    for project_id, actions in by_project.items():
        sibling = (
            session.query(EntitlementAction)
            .filter(
                EntitlementAction.subdivision_id == project_id,
                (EntitlementAction.acreage.isnot(None)) | (EntitlementAction.lot_count.isnot(None)),
            )
            .first()
        )
        if not sibling:
            continue

        project = session.get(Project, project_id)

        for action in actions:
            action_changed = False
            if not dry_run:
                if sibling.acreage is not None and action.acreage is None:
                    action.acreage = sibling.acreage
                    action_changed = True
                if sibling.lot_count is not None and action.lot_count is None:
                    action.lot_count = sibling.lot_count
                    action_changed = True
            else:
                action_changed = (
                    (sibling.acreage is not None and action.acreage is None)
                    or (sibling.lot_count is not None and action.lot_count is None)
                )
            if action_changed:
                counts["actions_updated"] += 1

        project_changed = False
        if project:
            if sibling.acreage is not None and project.platted_acreage is None:
                if not dry_run:
                    project.platted_acreage = sibling.acreage
                project_changed = True
            # Subdivision has no lot_count column in CD2 — lot_count lives on
            # CrEntitlementAction and Phase. The sibling's lot_count is still
            # propagated to the actions/phases below.
        if project_changed:
            counts["projects_updated"] += 1

        for action in actions:
            if action.phase_id:
                phase = session.get(Phase, action.phase_id)
                phase_changed = False
                if phase:
                    if sibling.acreage is not None and phase.acreage is None:
                        if not dry_run:
                            phase.acreage = sibling.acreage
                        phase_changed = True
                    if sibling.lot_count is not None and phase.lot_count is None:
                        if not dry_run:
                            phase.lot_count = sibling.lot_count
                        phase_changed = True
                if phase_changed:
                    counts["phases_updated"] += 1

    return counts


# ── Stage 2: Agenda HTML description parsing (free) ──────────────────────


def enrich_from_html(session, jurisdiction_id=None, dry_run=False):
    """Parse acreage from CivicPlus agenda HTML description fields.

    Planning board agendas embed structured fields (Acreage, Lot Count) in
    the item description.  No PDF download or API call needed.

    Returns:
        dict with counts.
    """
    from modules.commission.packet_fetcher import parse_item_fields_from_html

    counts = {
        "actions_checked": 0,
        "items_matched": 0,
        "actions_updated": 0,
        "projects_updated": 0,
    }

    actions = _actions_missing_packet_data(session, jurisdiction_id)
    if not actions:
        return counts

    seen_projects = set()
    html_cache = {}

    for action in actions:
        counts["actions_checked"] += 1
        if action.subdivision_id in seen_projects:
            continue

        source_doc = (
            session.get(SourceDocument, action.source_document_id)
            if action.source_document_id else None
        )
        jurisdiction = _resolve_jurisdiction(session, action)

        fields = parse_item_fields_from_html(
            action, source_doc, jurisdiction, cache=html_cache
        )
        acreage = fields.get("acreage")
        lot_count = fields.get("lot_count")
        if acreage is None and lot_count is None:
            continue

        seen_projects.add(action.subdivision_id)
        counts["items_matched"] += 1

        if dry_run:
            project = session.get(Project, action.subdivision_id)
            logger.info(
                f"[DRY RUN] HTML acreage={acreage}, lots={lot_count} "
                f"for project={project.name if project else '?'}"
            )
            continue

        au, pu = _apply_acreage(session, action.subdivision_id, acreage, lot_count)
        counts["actions_updated"] += au
        counts["projects_updated"] += pu

    return counts


# ── Stage 3: Backup PDF extraction (API cost) ────────────────────────────


def extract_acreage_from_text(text):
    """Call Claude with a focused prompt to extract acreage and lot_count.

    Returns:
        Tuple of (acreage: float|None, lot_count: int|None).
    """
    prompt = ACREAGE_EXTRACTION_PROMPT.format(text=text)
    client = anthropic.Anthropic(api_key=require_anthropic_api_key())

    last_error = None
    for attempt in range(API_MAX_RETRIES):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            break
        except (anthropic.RateLimitError, anthropic.APIConnectionError) as e:
            last_error = e
            delay = API_RETRY_BASE_DELAY * (2 ** attempt)
            logger.warning("API error (attempt %s): %s. Retrying in %ss...", attempt + 1, e, delay)
            time.sleep(delay)
    else:
        raise last_error

    response_text = ""
    for block in (message.content or []):
        if hasattr(block, "text"):
            response_text += block.text

    response_text = response_text.strip()
    if response_text.startswith("```"):
        import re
        fence_match = re.match(r"^```(?:json)?\s*\n(.*)\n```\s*$", response_text, re.DOTALL)
        if fence_match:
            response_text = fence_match.group(1).strip()

    try:
        data = json.loads(response_text)
    except json.JSONDecodeError:
        logger.warning("Could not parse acreage response: %s", response_text[:200])
        return None, None

    acreage = data.get("acreage")
    lot_count = data.get("lot_count")

    if acreage is not None:
        try:
            acreage = float(acreage)
        except (TypeError, ValueError):
            acreage = None
    if lot_count is not None:
        try:
            lot_count = int(lot_count)
        except (TypeError, ValueError):
            lot_count = None

    return acreage, lot_count


def enrich_from_packets(session, jurisdiction_id=None, dry_run=False):
    """Download backup PDFs for actions missing acreage or lot count and extract via Claude.

    Only processes actions where the action and project are still missing acreage
    or lot_count after the cheaper enrichment stages.

    Returns:
        dict with counts.
    """
    from modules.commission.packet_fetcher import resolve_packet_url
    from modules.commission.converters.pdf_converter import PdfConverter
    import requests

    counts = {
        "actions_checked": 0,
        "packets_found": 0,
        "packets_fetched": 0,
        "actions_updated": 0,
        "projects_updated": 0,
    }

    actions = _actions_missing_packet_data(session, jurisdiction_id)
    if not actions:
        return counts

    seen_projects = set()
    html_cache = {}
    converter = PdfConverter()

    for action in actions:
        counts["actions_checked"] += 1
        if action.subdivision_id in seen_projects:
            continue
        seen_projects.add(action.subdivision_id)

        source_doc = (
            session.get(SourceDocument, action.source_document_id)
            if action.source_document_id else None
        )
        jurisdiction = _resolve_jurisdiction(session, action)

        packet_url = resolve_packet_url(action, source_doc, jurisdiction, cache=html_cache)
        if not packet_url:
            continue
        counts["packets_found"] += 1

        if dry_run:
            logger.info("[DRY RUN] Would fetch packet: %s", packet_url)
            continue

        try:
            resp = requests.get(packet_url, timeout=30)
            resp.raise_for_status()
        except Exception as e:
            logger.warning("Failed to download packet %s: %s", packet_url, e)
            continue
        counts["packets_fetched"] += 1

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            conv_result = converter.convert(tmp_path, max_pages=PACKET_ENRICHMENT_MAX_PAGES)
            text = conv_result.text
            if not text or len(text.strip()) < 20:
                continue

            acreage, lot_count = extract_acreage_from_text(text)
            if acreage is None and lot_count is None:
                continue

            au, pu = _apply_acreage(session, action.subdivision_id, acreage, lot_count)
            counts["actions_updated"] += au
            counts["projects_updated"] += pu
        finally:
            os.unlink(tmp_path)

    return counts
