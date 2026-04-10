"""Aggregated inventory module router.

Mount this on the FastAPI app to expose all BI endpoints under /api/inventory/*.
"""

from fastapi import APIRouter

from modules.inventory.routers.builders import router as builders_router
from modules.inventory.routers.counties import router as counties_router
from modules.inventory.routers.inventory import router as inventory_router
from modules.inventory.routers.parcels import router as parcels_router
from modules.inventory.routers.raw_land import router as raw_land_router
from modules.inventory.routers.schedule import router as schedule_router
from modules.inventory.routers.snapshots import router as snapshots_router
from modules.inventory.routers.subdivisions import router as subdivisions_router

router = APIRouter(prefix="/api/inventory", tags=["inventory"])

router.include_router(builders_router)
router.include_router(counties_router)
router.include_router(inventory_router)
router.include_router(parcels_router)
router.include_router(raw_land_router)
router.include_router(schedule_router)
router.include_router(snapshots_router)
router.include_router(subdivisions_router)
