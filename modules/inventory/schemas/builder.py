from pydantic import BaseModel, ConfigDict


class AliasOut(BaseModel):
    id: int
    alias: str
    model_config = ConfigDict(from_attributes=True)


class BuilderCountyOut(BaseModel):
    id: int
    county_id: int
    model_config = ConfigDict(from_attributes=True)


class BuilderOut(BaseModel):
    id: int
    canonical_name: str
    type: str
    is_active: bool
    scope: str
    aliases: list[AliasOut]
    counties: list[BuilderCountyOut]
    model_config = ConfigDict(from_attributes=True)


class BuilderCreate(BaseModel):
    canonical_name: str
    type: str = "builder"
    aliases: list[str] = []
    scope: str = "national"
    county_ids: list[int] = []


class BuilderUpdate(BaseModel):
    canonical_name: str | None = None
    type: str | None = None
    aliases: list[str] | None = None
    is_active: bool | None = None
    scope: str | None = None
    county_ids: list[int] | None = None


# ---------------------------------------------------------------------------
# Portfolio schemas
# ---------------------------------------------------------------------------

class BuilderInfo(BaseModel):
    id: int
    canonical_name: str
    type: str
    scope: str
    alias_count: int


class PortfolioCounty(BaseModel):
    county_id: int
    county_name: str
    lot_count: int
    acreage: float


class PortfolioSubdivision(BaseModel):
    subdivision_id: int
    subdivision_name: str
    county_name: str
    lot_count: int


class PortfolioChange(BaseModel):
    parcel_id: int
    parcel_number: str
    site_address: str | None
    county_name: str
    subdivision_name: str | None
    change_type: str
    snapshot_date: str | None  # ISO datetime string


class BuilderPortfolio(BaseModel):
    builder: BuilderInfo
    total_lots: int
    total_acreage: float
    counties: list[PortfolioCounty]
    top_subdivisions: list[PortfolioSubdivision]
    recent_changes: list[PortfolioChange]
