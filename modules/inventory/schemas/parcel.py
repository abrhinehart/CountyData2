from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParcelOut(BaseModel):
    id: int
    parcel_number: str
    county: str
    entity: str
    subdivision: str | None
    owner_name: str | None
    site_address: str | None
    use_type: str | None
    acreage: float | None
    lot_width_ft: float | None
    lot_depth_ft: float | None
    lot_area_sqft: float | None
    building_value: float | None
    appraised_value: float | None
    deed_date: datetime | None
    previous_owner: str | None
    parcel_class: str | None
    is_active: bool
    first_seen: datetime
    last_seen: datetime
    last_changed: datetime
    model_config = ConfigDict(from_attributes=True)


class ParcelPage(BaseModel):
    items: list[ParcelOut]
    total: int
    page: int
    page_size: int
