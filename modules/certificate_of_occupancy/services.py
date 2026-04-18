"""Sketch services for the Certificate of Occupancy module."""

from modules.certificate_of_occupancy.schemas import (
    ModuleBootstrapPayload,
    ModuleFocus,
    ModuleHealthPayload,
)


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="certificate-of-occupancy",
        stage="sketch",
        purpose=(
            "Track certificates of occupancy as the clearest operational signal that "
            "a permitted structure crossed the finish line."
        ),
        focus_areas=[
            ModuleFocus(
                label="Issuance tracking",
                detail="Capture CO issuance dates, types, and linked permits.",
            ),
            ModuleFocus(
                label="Completion signal",
                detail="Measure builder cadence and subdivision absorption using CO events.",
            ),
            ModuleFocus(
                label="Exception handling",
                detail="Track temporary COs, finals, revocations, and missing links.",
            ),
        ],
        primary_entities=[
            "certificate_of_occupancy_records",
            "certificate_documents",
            "certificate_permit_links",
            "certificate_property_links",
            "certificate_status_events",
        ],
        suggested_views=[
            "issuance feed",
            "builder completion dashboard",
            "permit completion timeline",
            "subdivision delivery tracker",
        ],
        open_questions=[
            "Should temporary and final COs be separate first-class record types?",
            "Is the main source permit portals, clerk filings, or certificates uploaded elsewhere?",
            "Do we want COs as analytics only, or as an operational exception queue too?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="certificate-of-occupancy", status="ok", stage="sketch")
