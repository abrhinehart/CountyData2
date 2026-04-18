"""Sketch services for the Public Works module."""

from modules.public_works.schemas import ModuleBootstrapPayload, ModuleFocus, ModuleHealthPayload


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="public-works",
        stage="sketch",
        purpose=(
            "Track public infrastructure work that changes land value, timing, "
            "servicing capacity, or development feasibility."
        ),
        focus_areas=[
            ModuleFocus(
                label="Capital programs",
                detail="Capture road, utility, drainage, parks, and mobility projects.",
            ),
            ModuleFocus(
                label="Delivery risk",
                detail="Show schedule drift, funding gaps, and procurement status.",
            ),
            ModuleFocus(
                label="Impact radius",
                detail="Relate each project to counties, corridors, subdivisions, and permits.",
            ),
        ],
        primary_entities=[
            "public_projects",
            "funding_sources",
            "project_milestones",
            "project_impacts",
            "capital_documents",
        ],
        suggested_views=[
            "capital plan dashboard",
            "corridor map",
            "project detail timeline",
            "subdivision impact feed",
        ],
        open_questions=[
            "Do we care more about funded projects or proposed pipeline items too?",
            "Should impacts be geofenced spatially or attached manually to subdivisions?",
            "Is this a pure monitoring module or should it support internal scoring?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="public-works", status="ok", stage="sketch")
