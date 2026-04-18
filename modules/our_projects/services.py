"""Sketch services for the Our Projects module."""

from modules.our_projects.schemas import ModuleBootstrapPayload, ModuleFocus, ModuleHealthPayload


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="our-projects",
        stage="sketch",
        purpose=(
            "Track internally curated projects from first signal through pursuit, "
            "underwriting, entitlement, execution, and closeout."
        ),
        focus_areas=[
            ModuleFocus(
                label="Pipeline",
                detail="Keep one canonical record for every internally tracked project.",
            ),
            ModuleFocus(
                label="Ownership",
                detail="Show who owns the next action, blocker, or decision.",
            ),
            ModuleFocus(
                label="Cross-module links",
                detail="Tie project records back to subdivisions, permits, and commission actions.",
            ),
        ],
        primary_entities=[
            "projects",
            "project_stages",
            "project_participants",
            "project_notes",
            "project_dependencies",
        ],
        suggested_views=[
            "pipeline board",
            "project detail timeline",
            "owner dashboard",
            "cross-module subdivision lens",
        ],
        open_questions=[
            "Should this represent only owned pursuits or any project worth monitoring?",
            "What is the canonical lifecycle: lead, active, hold, won, dead, built?",
            "Do we need portfolio-level rollups by market, builder, or county?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="our-projects", status="ok", stage="sketch")
