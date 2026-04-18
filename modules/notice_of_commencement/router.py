"""Sketch router for the Notice of Commencement module."""

from fastapi import APIRouter

from modules.notice_of_commencement.schemas import ModuleBootstrapPayload, ModuleHealthPayload
from modules.notice_of_commencement.services import get_bootstrap_payload, get_health_payload

router = APIRouter(prefix="/api/notice-of-commencement", tags=["notice-of-commencement"])


@router.get("/bootstrap", response_model=ModuleBootstrapPayload)
def bootstrap() -> ModuleBootstrapPayload:
    """Return the initial sketch payload for the module."""
    return get_bootstrap_payload()


@router.get("/health", response_model=ModuleHealthPayload)
def health() -> ModuleHealthPayload:
    """Expose a simple status endpoint while the module is in sketch mode."""
    return get_health_payload()
