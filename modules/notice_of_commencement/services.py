"""Sketch services for the Notice of Commencement module."""

from modules.notice_of_commencement.schemas import (
    ModuleBootstrapPayload,
    ModuleFocus,
    ModuleHealthPayload,
)


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="notice-of-commencement",
        stage="sketch",
        purpose=(
            "Track recorded notices of commencement to monitor project starts, "
            "contractor relationships, and document validity windows."
        ),
        focus_areas=[
            ModuleFocus(
                label="Recording intake",
                detail="Capture when and where the notice was recorded and which property it touches.",
            ),
            ModuleFocus(
                label="Entity extraction",
                detail="Track owner, contractor, surety, lender, and job description details.",
            ),
            ModuleFocus(
                label="Permit linkage",
                detail="Connect notices back to permits, subdivisions, and project starts.",
            ),
        ],
        primary_entities=[
            "notice_of_commencement_records",
            "notice_parties",
            "notice_documents",
            "notice_property_links",
            "notice_status_history",
        ],
        suggested_views=[
            "recording queue",
            "project start monitor",
            "document detail panel",
            "permit-to-notice linkage board",
        ],
        open_questions=[
            "Will this be county-clerk driven, permit-portal driven, or both?",
            "Do we care about renewals, expirations, and superseding notices in v1?",
            "Should notices attach to parcels, permits, subdivisions, or all three?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="notice-of-commencement", status="ok", stage="sketch")
