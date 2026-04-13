"""
Builder Inventory (BI) module models.

BI-specific tables live here. Shared spine tables (counties, builders,
subdivisions, builder_aliases, builder_counties) are imported from
shared.models and re-exported so callers can do:

    from modules.inventory.models import County, Builder, Parcel, ...
"""

from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.models import (
    Base,
    Builder,
    BuilderAlias,
    BuilderCounty,
    County,
    Subdivision,
)


# ---------------------------------------------------------------------------
# BI-specific models
# ---------------------------------------------------------------------------


class BiCountyConfig(Base):
    """Per-county GIS field mapping for the BI scraper."""

    __tablename__ = "bi_county_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    county_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("counties.id"), nullable=False, unique=True
    )

    gis_endpoint: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_owner_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_parcel_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_address_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_use_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_acreage_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_subdivision_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_building_value_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_appraised_value_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_deed_date_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_previous_owner_field: Mapped[str | None] = mapped_column(String, nullable=True)
    gis_max_records: Mapped[int] = mapped_column(Integer, default=1000)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    county = relationship("County")


class Parcel(Base):
    """Individual parcel tracked by the BI scraper."""

    __tablename__ = "parcels"
    __table_args__ = (
        UniqueConstraint("parcel_number", "county_id", name="uq_parcel_county"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parcel_number: Mapped[str] = mapped_column(String, nullable=False)
    county_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("counties.id"), nullable=False
    )
    builder_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("builders.id"), nullable=True
    )
    subdivision_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("subdivisions.id"), nullable=True
    )

    owner_name: Mapped[str | None] = mapped_column(String, nullable=True)
    site_address: Mapped[str | None] = mapped_column(String, nullable=True)
    use_type: Mapped[str | None] = mapped_column(String, nullable=True)
    acreage: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)

    centroid = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    geom = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)

    parcel_class: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    lot_width_ft: Mapped[float | None] = mapped_column(Numeric(10, 1), nullable=True)
    lot_depth_ft: Mapped[float | None] = mapped_column(Numeric(10, 1), nullable=True)
    lot_area_sqft: Mapped[float | None] = mapped_column(Numeric(12, 1), nullable=True)

    building_value: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    appraised_value: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    deed_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    previous_owner: Mapped[str | None] = mapped_column(String, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_changed: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    county = relationship("County")
    builder = relationship("Builder")
    subdivision = relationship("Subdivision")


class BiSnapshot(Base):
    """Record of a single BI scraper run against a county."""

    __tablename__ = "bi_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    county_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("counties.id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String, default="running")
    total_parcels_queried: Mapped[int] = mapped_column(Integer, default=0)
    new_count: Mapped[int] = mapped_column(Integer, default=0)
    removed_count: Mapped[int] = mapped_column(Integer, default=0)
    changed_count: Mapped[int] = mapped_column(Integer, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, default=0)
    progress_current: Mapped[int] = mapped_column(Integer, default=0)
    progress_total: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    summary_text: Mapped[str | None] = mapped_column(String, nullable=True)


class BiParcelSnapshot(Base):
    """Per-parcel change record linked to a BiSnapshot."""

    __tablename__ = "bi_parcel_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parcel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parcels.id"), nullable=False
    )
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bi_snapshots.id"), nullable=False
    )
    change_type: Mapped[str] = mapped_column(String, nullable=False)
    old_values = mapped_column(JSONB, nullable=True)
    new_values = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class BiScheduleConfig(Base):
    """Scheduler configuration for automated BI scraper runs."""

    __tablename__ = "bi_schedule_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interval_minutes: Mapped[int] = mapped_column(Integer, default=10080)  # 7 days
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Re-export shared models for convenience:
#   from modules.inventory.models import County, Builder, Subdivision, ...
# ---------------------------------------------------------------------------
__all__ = [
    # Shared
    "Base",
    "County",
    "Builder",
    "BuilderAlias",
    "BuilderCounty",
    "Subdivision",
    # BI-specific
    "BiCountyConfig",
    "Parcel",
    "BiSnapshot",
    "BiParcelSnapshot",
    "BiScheduleConfig",
]
