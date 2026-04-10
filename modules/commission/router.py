"""Aggregated commission module router.

Mount this on the FastAPI app to expose all Commission Radar endpoints under
``/api/commission/*``. Each sub-router corresponds to one of the original
Flask blueprints (dashboard, process, review, roster, scrape).
"""

from fastapi import APIRouter

from modules.commission.routers.dashboard import (
    docs_router as commission_docs_router,
    router as dashboard_router,
)
from modules.commission.routers.process import router as process_router
from modules.commission.routers.review import router as review_router
from modules.commission.routers.roster import router as roster_router
from modules.commission.routers.scrape import router as scrape_router

router = APIRouter(prefix="/api/commission", tags=["commission"])

# /dashboard/* endpoints from the dashboard blueprint
router.include_router(dashboard_router)
# /documents/{slug}/{filename} and /jurisdictions/{slug}/pin — these sat
# outside of /dashboard in the original Flask app so they live on their own
# router without a prefix.
router.include_router(commission_docs_router)
router.include_router(process_router)
router.include_router(review_router)
router.include_router(roster_router)
router.include_router(scrape_router)
