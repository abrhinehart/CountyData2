"""Sketch services for the FLUM Adjacency module."""

from modules.flum_adjacency.schemas import ModuleBootstrapPayload, ModuleFocus, ModuleHealthPayload


def get_bootstrap_payload() -> ModuleBootstrapPayload:
    return ModuleBootstrapPayload(
        module="flum-adjacency",
        stage="sketch",
        purpose=(
            "Model Future Land Use Map adjacency so the team can reason about "
            "what a site touches today and what that context implies for entitlement risk or upside."
        ),
        focus_areas=[
            ModuleFocus(
                label="Context geometry",
                detail="Describe what FLUM categories touch a subdivision, parcel, or project boundary.",
            ),
            ModuleFocus(
                label="Compatibility signals",
                detail="Highlight supportive, neutral, or conflicting adjacent land-use patterns.",
            ),
            ModuleFocus(
                label="Change detection",
                detail="Track when nearby FLUM amendments alter the adjacency picture over time.",
            ),
        ],
        primary_entities=[
            "flum_layers",
            "flum_polygons",
            "adjacency_edges",
            "adjacency_snapshots",
            "compatibility_rules",
        ],
        suggested_views=[
            "adjacency map",
            "site context summary",
            "before-and-after FLUM diff",
            "entitlement compatibility panel",
        ],
        open_questions=[
            "Is the unit of analysis subdivision, parcel cluster, or arbitrary site polygon?",
            "Do we need strict geometric adjacency only, or nearby-within-distance context too?",
            "Should compatibility be rule-based first, or analyst-authored narrative?",
        ],
    )


def get_health_payload() -> ModuleHealthPayload:
    return ModuleHealthPayload(module="flum-adjacency", status="ok", stage="sketch")
