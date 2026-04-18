"""Sketch router for the Certificate of Occupancy module."""

from fastapi import APIRouter

from modules.certificate_of_occupancy.schemas import ModuleBootstrapPayload, ModuleHealthPayload
from modules.certificate_of_occupancy.services import get_bootstrap_payload, get_health_payload

router = APIRouter(prefix="/api/certificate-of-occupancy", tags=["certificate-of-occupancy"])


@router.get("/bootstrap", response_model=ModuleBootstrapPayload)
def bootstrap() -> ModuleBootstrapPayload:
    """Return the initial sketch payload for the module."""
    return get_bootstrap_payload()


@router.get("/health", response_model=ModuleHealthPayload)
def health() -> ModuleHealthPayload:
    """Expose a simple status endpoint while the module is in sketch mode."""
    return get_health_payload()
