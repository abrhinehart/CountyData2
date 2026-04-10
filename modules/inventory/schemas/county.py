from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CountyOut(BaseModel):
    id: int
    name: str
    state: str
    dor_county_no: int | None
    is_active: bool
    has_endpoint: bool
    last_snapshot_at: datetime | None = None
    last_snapshot_parcels: int | None = None
    model_config = ConfigDict(from_attributes=True)
