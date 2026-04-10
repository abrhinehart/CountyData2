from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BuilderCount(BaseModel):
    builder_id: int
    builder_name: str
    count: int


class CountyInventory(BaseModel):
    county_id: int
    county: str
    total: int
    builders: list[BuilderCount]


class SubdivisionInventory(BaseModel):
    subdivision_id: int | None
    subdivision: str
    total: int
    builders: list[BuilderCount]


class CountyDetail(BaseModel):
    county_id: int
    county: str
    total: int
    subdivisions: list[SubdivisionInventory]


class MapMarker(BaseModel):
    subdivision_id: int
    subdivision_name: str
    county_id: int
    county_name: str
    builder_id: int
    builder_name: str
    lot_count: int
    lat: float | None
    lng: float | None


class TrendPoint(BaseModel):
    date: datetime
    county_id: int
    county: str
    total_parcels: int
    new_count: int
    removed_count: int
    changed_count: int
    model_config = ConfigDict(from_attributes=True)
