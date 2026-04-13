from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubdivisionOut(BaseModel):
    id: int
    name: str
    county_id: int
    county_name: str
    has_geometry: bool
    parcel_count: int
    builder_lot_count: int = 0
    distinct_builder_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    properties: dict
    geometry: dict


class GeoJSONImportRequest(BaseModel):
    county_id: int
    features: list[GeoJSONFeature]


class SubdivisionImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[str]
    parcels_linked: int


class SubdivisionGeometryUpdate(BaseModel):
    geometry: dict  # GeoJSON geometry object


class SubdivisionBuilderSummary(BaseModel):
    builder_id: int
    builder_name: str
    lot_count: int


class SubdivisionGeoFeature(BaseModel):
    """One feature in the map GeoJSON response."""
    id: int
    name: str
    county_id: int
    county_name: str
    builder_lot_count: int
    distinct_builder_count: int
    builders: list[SubdivisionBuilderSummary]
    geojson: dict  # GeoJSON Geometry object
