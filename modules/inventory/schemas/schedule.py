from pydantic import BaseModel, ConfigDict


class ScheduleOut(BaseModel):
    interval_minutes: int
    is_enabled: bool
    model_config = ConfigDict(from_attributes=True)


class ScheduleUpdate(BaseModel):
    interval_minutes: int | None = None
    is_enabled: bool | None = None
