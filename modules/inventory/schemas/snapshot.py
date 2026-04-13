from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SnapshotOut(BaseModel):
    id: int
    county_id: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    total_parcels_queried: int
    new_count: int
    removed_count: int
    changed_count: int
    unchanged_count: int
    error_message: str | None
    summary_text: str | None = None
    progress_current: int = 0
    progress_total: int = 0
    model_config = ConfigDict(from_attributes=True)


class SnapshotRunRequest(BaseModel):
    county_id: int | None = None


class SnapshotRunResponse(BaseModel):
    message: str
    snapshot_ids: list[int] = []


# ---------------------------------------------------------------------------
# Change detail schemas
# ---------------------------------------------------------------------------


class ParcelChangeOut(BaseModel):
    parcel_id: int
    parcel_number: str
    site_address: str | None
    subdivision: str | None
    owner_name: str | None
    change_type: str
    old_values: dict | None
    new_values: dict | None


class BuilderChangeSummary(BaseModel):
    builder_name: str
    new_count: int
    removed_count: int
    changed_count: int
    parcels: list[ParcelChangeOut]


class SnapshotChangesOut(BaseModel):
    snapshot_id: int
    county_id: int
    county: str
    summary_text: str | None
    builders: list[BuilderChangeSummary]
