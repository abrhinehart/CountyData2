"""Sketch router for the Our Projects module."""

from fastapi import APIRouter

from modules.our_projects.schemas import ModuleBootstrapPayload, ModuleHealthPayload
from modules.our_projects.services import get_bootstrap_payload, get_health_payload

router = APIRouter(prefix="/api/our-projects", tags=["our-projects"])


@router.get("/bootstrap", response_model=ModuleBootstrapPayload)
def bootstrap() -> ModuleBootstrapPayload:
    """Return the initial sketch payload for the module."""
    return get_bootstrap_payload()


@router.get("/health", response_model=ModuleHealthPayload)
def health() -> ModuleHealthPayload:
    """Expose a simple status endpoint while the module is in sketch mode."""
    return get_health_payload()
