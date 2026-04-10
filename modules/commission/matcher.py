import json
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

from modules.commission.models import EntitlementAction, SourceDocument

logger = logging.getLogger("commission_radar.matcher")

# Maximum days between an agenda and its corresponding minutes
MATCH_WINDOW_DAYS = 90
CLOSE_MATCH_DAYS = 7
MIN_SCORE_GAP = 5

from modules.commission.normalization import normalize_approval_type, normalize_text

SCORE_EXACT_CASE_NUMBER = 100
SCORE_EXACT_ORDINANCE_NUMBER = 80
SCORE_PROJECT_NAME_AND_TYPE = 50
SCORE_PHASE_NAME_MATCH = 20
SCORE_PARCEL_OVERLAP = 12
SCORE_EXACT_ADDRESS = 8
SCORE_APPLICANT_MATCH = 6
SCORE_EXACT_MEETING_DATE = 10
SCORE_NEAR_MEETING_DATE = 5
SCORE_CASE_FAMILY = 4
SCORE_ORDINANCE_FAMILY = 3


@dataclass
class MatchCandidate:
    agenda_action: EntitlementAction
    score: int
    reasons: list[str]
    exact_case_match: bool = False
    exact_ordinance_match: bool = False
    project_type_match: bool = False
    support_signals: int = 0
    date_distance: int = MATCH_WINDOW_DAYS + CLOSE_MATCH_DAYS + 1

    @property
    def reason(self):
        return "; ".join(self.reasons)


def match_agenda_to_minutes(session, jurisdiction_id: int) -> int:
    """Link unlinked minutes actions to their corresponding agenda actions.

    Matching strategy:
    1. Normalize identifiers and score all viable agenda candidates.
    2. Require one-to-one matching within a run.
    3. Skip ambiguous matches instead of guessing.

    Returns:
        Number of links created.
    """
    minutes_actions = (
        session.query(EntitlementAction)
        .join(SourceDocument, EntitlementAction.source_document_id == SourceDocument.id)
        .filter(
            SourceDocument.jurisdiction_id == jurisdiction_id,
            SourceDocument.document_type == "minutes",
            EntitlementAction.linked_action_id.is_(None),
        )
        .all()
    )

    if not minutes_actions:
        logger.info("No unlinked minutes actions found.")
        return 0

    agenda_actions = (
        session.query(EntitlementAction)
        .join(SourceDocument, EntitlementAction.source_document_id == SourceDocument.id)
        .filter(
            SourceDocument.jurisdiction_id == jurisdiction_id,
            SourceDocument.document_type == "agenda",
        )
        .all()
    )

    if not agenda_actions:
        logger.info("No agenda actions to match against.")
        return 0

    used_agenda_ids = {
        linked_action_id
        for (linked_action_id,) in (
            session.query(EntitlementAction.linked_action_id)
            .join(SourceDocument, EntitlementAction.source_document_id == SourceDocument.id)
            .filter(
                SourceDocument.jurisdiction_id == jurisdiction_id,
                SourceDocument.document_type == "minutes",
                EntitlementAction.linked_action_id.is_not(None),
            )
            .all()
        )
    }

    available_agenda = [
        agenda_action
        for agenda_action in agenda_actions
        if agenda_action.id not in used_agenda_ids
    ]
    links_created = 0

    # Precompute all unambiguous (minutes, candidate) proposals in one pass,
    # then sort globally by score so the greedy assignment picks the best first.
    proposals = []
    ambiguous_reasons = {}
    for minutes_action in sorted(minutes_actions, key=_minutes_sort_key):
        decision = _select_candidate(minutes_action, available_agenda)
        if decision["status"] == "matched":
            proposals.append((minutes_action, decision["candidate"]))
        elif decision["status"] == "ambiguous":
            ambiguous_reasons[minutes_action.id] = decision["reason"]

    # Sort: highest score first, then closest date, then deterministic tie-breaking.
    proposals.sort(
        key=lambda proposal: (
            -proposal[1].score,
            proposal[1].date_distance,
            proposal[0].id,
            proposal[1].agenda_action.id,
        ),
    )

    # Greedy one-to-one assignment: first-come in sorted order claims the agenda action.
    claimed_agenda_ids = set(used_agenda_ids)
    claimed_minutes_ids = set()
    for minutes_action, candidate in proposals:
        if minutes_action.id in claimed_minutes_ids:
            continue
        if candidate.agenda_action.id in claimed_agenda_ids:
            continue

        minutes_action.linked_action_id = candidate.agenda_action.id
        claimed_agenda_ids.add(candidate.agenda_action.id)
        claimed_minutes_ids.add(minutes_action.id)
        links_created += 1
        logger.debug(
            "Linked minutes action %s -> agenda action %s (%s)",
            minutes_action.id,
            candidate.agenda_action.id,
            candidate.reason,
        )

    # Log why unmatched minutes were skipped.
    for minutes_action in sorted(minutes_actions, key=_minutes_sort_key):
        if minutes_action.id in claimed_minutes_ids:
            continue
        if minutes_action.id in ambiguous_reasons:
            logger.debug(
                "Skipped linking minutes action %s because the best candidates were too close: %s",
                minutes_action.id,
                ambiguous_reasons[minutes_action.id],
            )
        else:
            logger.debug(
                "Skipped linking minutes action %s because no unambiguous candidate was found.",
                minutes_action.id,
            )

    if links_created > 0:
        session.flush()
        logger.info("Created %s agenda-minutes links.", links_created)

    return links_created


def _minutes_sort_key(minutes_action):
    return (
        not bool(_normalize_identifier(minutes_action.case_number)),
        not bool(_normalize_identifier(minutes_action.ordinance_number)),
        not bool(normalize_text(minutes_action.project_name)),
        not bool(_normalize_approval_type(minutes_action.approval_type)),
        minutes_action.meeting_date or date.min,
        minutes_action.id,
    )


def _select_candidate(minutes_action, agenda_actions):
    candidates = _rank_candidates(minutes_action, agenda_actions)
    if not candidates:
        return {"status": "no_match", "candidate": None, "reason": "no viable candidates"}

    best = candidates[0]
    runner_up = candidates[1] if len(candidates) > 1 else None

    if runner_up and best.score - runner_up.score < MIN_SCORE_GAP:
        return {
            "status": "ambiguous",
            "candidate": None,
            "reason": f"{best.agenda_action.id} ({best.reason}) vs {runner_up.agenda_action.id} ({runner_up.reason})",
        }

    return {"status": "matched", "candidate": best, "reason": best.reason}


def _rank_candidates(minutes_action, agenda_actions):
    candidates = []
    for agenda_action in _filter_by_date_window(minutes_action, agenda_actions):
        candidate = _build_candidate(minutes_action, agenda_action)
        if candidate:
            candidates.append(candidate)

    return sorted(
        candidates,
        key=lambda candidate: (-candidate.score, candidate.date_distance, candidate.agenda_action.id),
    )


def _build_candidate(minutes_action, agenda_action):
    reasons = []
    score = 0
    support_signals = 0

    minutes_case = _normalize_identifier(minutes_action.case_number)
    agenda_case = _normalize_identifier(agenda_action.case_number)
    exact_case_match = bool(minutes_case and agenda_case and minutes_case == agenda_case)
    if exact_case_match:
        score += SCORE_EXACT_CASE_NUMBER
        reasons.append("exact normalized case number match")

    minutes_ordinance = _normalize_identifier(minutes_action.ordinance_number)
    agenda_ordinance = _normalize_identifier(agenda_action.ordinance_number)
    exact_ordinance_match = bool(
        minutes_ordinance and agenda_ordinance and minutes_ordinance == agenda_ordinance
    )
    if exact_ordinance_match:
        score += SCORE_EXACT_ORDINANCE_NUMBER
        reasons.append("exact normalized ordinance number match")

    project_name_match = normalize_text(minutes_action.project_name) == normalize_text(
        agenda_action.project_name
    )
    approval_type_match = _normalize_approval_type(minutes_action.approval_type) == _normalize_approval_type(
        agenda_action.approval_type
    )
    project_type_match = bool(
        normalize_text(minutes_action.project_name)
        and normalize_text(agenda_action.project_name)
        and project_name_match
        and approval_type_match
    )
    if project_type_match:
        score += SCORE_PROJECT_NAME_AND_TYPE
        reasons.append("normalized project name and approval type match")

    minutes_phase = normalize_text(minutes_action.phase_name)
    agenda_phase = normalize_text(agenda_action.phase_name)
    if minutes_phase and agenda_phase:
        if minutes_phase == agenda_phase:
            score += SCORE_PHASE_NAME_MATCH
            support_signals += 1
            reasons.append("phase name match")
        elif project_type_match:
            # Both have phase names but they differ — not the same entitlement
            return None

    date_distance = _date_distance(minutes_action, agenda_action)
    if minutes_action.meeting_date and agenda_action.meeting_date:
        if date_distance == 0:
            support_signals += 1
            score += SCORE_EXACT_MEETING_DATE
            reasons.append("same meeting date")
        elif date_distance <= CLOSE_MATCH_DAYS:
            support_signals += 1
            score += SCORE_NEAR_MEETING_DATE
            reasons.append(f"meeting dates within {CLOSE_MATCH_DAYS} days")

    minutes_parcels = _normalize_parcel_ids(minutes_action.parcel_ids)
    agenda_parcels = _normalize_parcel_ids(agenda_action.parcel_ids)
    if minutes_parcels and agenda_parcels and minutes_parcels.intersection(agenda_parcels):
        support_signals += 1
        score += SCORE_PARCEL_OVERLAP
        reasons.append("overlapping parcel IDs")

    minutes_address = normalize_text(minutes_action.address)
    agenda_address = normalize_text(agenda_action.address)
    if minutes_address and agenda_address and minutes_address == agenda_address:
        support_signals += 1
        score += SCORE_EXACT_ADDRESS
        reasons.append("normalized address match")

    minutes_applicant = normalize_text(minutes_action.applicant_name)
    agenda_applicant = normalize_text(agenda_action.applicant_name)
    if minutes_applicant and agenda_applicant and minutes_applicant == agenda_applicant:
        support_signals += 1
        score += SCORE_APPLICANT_MATCH
        reasons.append("applicant name match")

    minutes_case_family = _identifier_family(minutes_action.case_number)
    agenda_case_family = _identifier_family(agenda_action.case_number)
    if (
        project_type_match
        and not exact_case_match
        and minutes_case_family
        and agenda_case_family
        and minutes_case_family == agenda_case_family
    ):
        support_signals += 1
        score += SCORE_CASE_FAMILY
        reasons.append("same case-number family")

    minutes_ordinance_family = _identifier_family(minutes_action.ordinance_number)
    agenda_ordinance_family = _identifier_family(agenda_action.ordinance_number)
    if (
        project_type_match
        and not exact_ordinance_match
        and minutes_ordinance_family
        and agenda_ordinance_family
        and minutes_ordinance_family == agenda_ordinance_family
    ):
        support_signals += 1
        score += SCORE_ORDINANCE_FAMILY
        reasons.append("same ordinance-number family")

    if not exact_case_match and not exact_ordinance_match:
        if not project_type_match:
            return None
        if support_signals == 0:
            return None

    if score == 0:
        return None

    return MatchCandidate(
        agenda_action=agenda_action,
        score=score,
        reasons=reasons,
        exact_case_match=exact_case_match,
        exact_ordinance_match=exact_ordinance_match,
        project_type_match=project_type_match,
        support_signals=support_signals,
        date_distance=date_distance,
    )


def _filter_by_date_window(minutes_action, agenda_actions):
    """Filter agenda actions to those within the date window of a minutes action."""
    if not minutes_action.meeting_date:
        return agenda_actions

    window_start = minutes_action.meeting_date - timedelta(days=MATCH_WINDOW_DAYS)
    window_end = minutes_action.meeting_date + timedelta(days=7)

    return [
        agenda_action
        for agenda_action in agenda_actions
        if agenda_action.meeting_date and window_start <= agenda_action.meeting_date <= window_end
    ]


def _normalize_identifier(value):
    normalized = normalize_text(value)
    if not normalized:
        return None
    compact = re.sub(r"[^a-z0-9]", "", normalized)
    return compact or None


def _normalize_approval_type(value):
    normalized = normalize_text(value)
    if not normalized:
        return None
    return normalize_approval_type(normalized)


def _normalize_parcel_ids(parcel_ids):
    if not parcel_ids:
        return set()

    parsed = parcel_ids
    if isinstance(parcel_ids, str):
        try:
            parsed = json.loads(parcel_ids)
        except json.JSONDecodeError:
            parsed = [parcel_ids]

    if not isinstance(parsed, list):
        parsed = [parsed]

    return {
        normalized
        for normalized in (normalize_text(str(parcel_id)) for parcel_id in parsed)
        if normalized
    }


def _identifier_family(value):
    normalized = normalize_text(value)
    if not normalized:
        return None

    match = re.search(r"([a-z]+)\s*[-/]?\s*(\d{2,4})", normalized)
    if match:
        return match.group(1), match.group(2)

    return None


def _date_distance(minutes_action, agenda_action):
    if not minutes_action.meeting_date or not agenda_action.meeting_date:
        return MATCH_WINDOW_DAYS + CLOSE_MATCH_DAYS + 1
    return abs((minutes_action.meeting_date - agenda_action.meeting_date).days)
