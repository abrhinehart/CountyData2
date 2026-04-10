from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from shared.sa_database import get_db
from modules.inventory.models import BiScheduleConfig
from modules.inventory.scheduler import remove_snapshot_job, setup_snapshot_job
from modules.inventory.schemas.schedule import ScheduleOut, ScheduleUpdate

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _get_or_create_config(db: Session) -> BiScheduleConfig:
    config = db.get(BiScheduleConfig, 1)
    if not config:
        config = BiScheduleConfig(id=1)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("", response_model=ScheduleOut)
def get_schedule(db: Session = Depends(get_db)):
    return _get_or_create_config(db)


@router.put("", response_model=ScheduleOut)
def update_schedule(data: ScheduleUpdate, request: Request, db: Session = Depends(get_db)):
    config = _get_or_create_config(db)
    if data.interval_minutes is not None:
        config.interval_minutes = data.interval_minutes
    if data.is_enabled is not None:
        config.is_enabled = data.is_enabled
    db.commit()
    db.refresh(config)

    # Reschedule or remove the job
    scheduler = request.app.state.scheduler
    if config.is_enabled:
        setup_snapshot_job(scheduler, config.interval_minutes)
    else:
        remove_snapshot_job(scheduler)

    return config
