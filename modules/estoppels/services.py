"""Sketch services for the Estoppels module."""

from modules.estoppels.schemas import ModuleBootstrapPayload, ModuleFocus, ModuleHealthPayload


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="estoppels",
        stage="sketch",
        purpose=(
            "Manage estoppel requests and responses so transaction teams can track "
            "fees, delinquency exposure, restrictions, and closing readiness."
        ),
        focus_areas=[
            ModuleFocus(
                label="Request tracking",
                detail="Track when estoppels were requested, from whom, and on which asset.",
            ),
            ModuleFocus(
                label="Risk extraction",
                detail="Surface balances due, transfer fees, violations, and expiration dates.",
            ),
            ModuleFocus(
                label="Closing readiness",
                detail="Make outstanding estoppels visible on a transaction or subdivision dashboard.",
            ),
        ],
        primary_entities=[
            "estoppel_requests",
            "estoppel_contacts",
            "estoppel_documents",
            "estoppel_obligations",
            "estoppel_status_history",
        ],
        suggested_views=[
            "request queue",
            "asset readiness board",
            "document review panel",
            "closing checklist summary",
        ],
        open_questions=[
            "Is the unit of work parcel, lot, subdivision, association, or transaction?",
            "Will documents be parsed automatically or reviewed manually first?",
            "Do we need fee payment tracking and reimbursement audit trails?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="estoppels", status="ok", stage="sketch")
