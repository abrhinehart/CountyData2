"""Sketch services for the Commission Elections module."""

from modules.commission_elections.schemas import (
    ModuleBootstrapPayload,
    ModuleFocus,
    ModuleHealthPayload,
)


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="commission-elections",
        stage="sketch",
        purpose=(
            "Track local elected-official races so policy posture, seat turnover risk, "
            "and upcoming political shifts can be tied back to commission activity."
        ),
        focus_areas=[
            ModuleFocus(
                label="Seat inventory",
                detail="Track seats, districts, incumbents, term limits, and election calendars.",
            ),
            ModuleFocus(
                label="Candidate intelligence",
                detail="Capture challengers, endorsements, funding, and platform signals.",
            ),
            ModuleFocus(
                label="Policy linkage",
                detail="Connect elections back to commissioner votes, agenda behavior, and development posture.",
            ),
        ],
        primary_entities=[
            "election_cycles",
            "commission_seats",
            "candidates",
            "race_events",
            "policy_signals",
        ],
        suggested_views=[
            "seat map",
            "election calendar",
            "candidate comparison board",
            "incumbent voting profile",
        ],
        open_questions=[
            "Should this cover county and city commissions only, or school boards and other bodies too?",
            "How much historical election data matters before the module becomes useful?",
            "Should policy posture be manually scored first or inferred from commission records?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="commission-elections", status="ok", stage="sketch")
