"""Sketch router for the Commission Elections module."""

from fastapi import APIRouter

from modules.commission_elections.schemas import ModuleBootstrapPayload, ModuleHealthPayload
from modules.commission_elections.services import get_bootstrap_payload, get_health_payload

router = APIRouter(prefix="/api/commission-elections", tags=["commission-elections"])


@router.get("/bootstrap", response_model=ModuleBootstrapPayload)
def bootstrap() -> ModuleBootstrapPayload:
    """Return the initial sketch payload for the module."""
    return get_bootstrap_payload()


@router.get("/health", response_model=ModuleHealthPayload)
def health() -> ModuleHealthPayload:
    """Expose a simple status endpoint while the module is in sketch mode."""
    return get_health_payload()
