"""
Shared SQLAlchemy models for the foundation tables.

All modules import these models to reference the shared spine
(counties, jurisdictions, subdivisions, builders, phases).
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Double, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, relationship

try:
    from geoalchemy2 import Geometry
    _HAS_GEO = True
except ImportError:
    Geometry = None
    _HAS_GEO = False


class Base(DeclarativeBase):
    pass


class County(Base):
    __tablename__ = "counties"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    state = Column(String(2), nullable=False, default="FL")
    dor_county_no = Column(Integer)
    county_fips = Column(String(10))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(Integer, primary_key=True)
    slug = Column(String(100), unique=True)
    name = Column(Text, nullable=False)
    county_id = Column(Integer, ForeignKey("counties.id"), nullable=False)
    municipality = Column(String(100))
    jurisdiction_type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    county = relationship("County")


class Subdivision(Base):
    __tablename__ = "subdivisions"

    id = Column(Integer, primary_key=True)
    canonical_name = Column(Text, nullable=False)
    county = Column(Text, nullable=False)  # Legacy text column, kept for CD2 compat
    county_id = Column(Integer, ForeignKey("counties.id"))
    geom = Column(Geometry("MULTIPOLYGON", srid=4326)) if _HAS_GEO else Column(Text)
    source = Column(Text)
    plat_book = Column(Text)
    plat_page = Column(Text)
    developer_name = Column(Text)
    recorded_date = Column(Date)
    platted_acreage = Column(Double)
    entitlement_status = Column(String(50), default="not_started")
    lifecycle_stage = Column(String(50))
    last_action_date = Column(Date)
    next_expected_action = Column(String(100))
    location_description = Column(Text)
    proposed_land_use = Column(String(100))
    proposed_zoning = Column(String(100))
    watched = Column(Boolean, default=False)
    notes = Column(Text)
    classification = Column(String(30), default="scattered", server_default="scattered")
    is_active = Column(Boolean, default=True)
    is_relevant = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Geometry columns (PostGIS) and plat info handled at DB level,
    # not mapped here to avoid geoalchemy2 dependency in shared models.
    # Modules that need geometry import from their own model extensions.

    @hybrid_property
    def name(self):
        """Alias for canonical_name (BI compatibility)."""
        return self.canonical_name

    @name.inplace.setter
    def _name_setter(self, value):
        self.canonical_name = value

    @name.inplace.expression
    @classmethod
    def _name_expression(cls):
        return cls.canonical_name


class SubdivisionAlias(Base):
    __tablename__ = "subdivision_aliases"

    id = Column(Integer, primary_key=True)
    subdivision_id = Column(Integer, ForeignKey("subdivisions.id", ondelete="CASCADE"), nullable=False)
    alias = Column(Text, nullable=False)
    source = Column(String(20), default="manual")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Phase(Base):
    __tablename__ = "phases"

    id = Column(Integer, primary_key=True)
    subdivision_id = Column(Integer, ForeignKey("subdivisions.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    acreage = Column(Double)
    lot_count = Column(Integer)
    proposed_land_use = Column(String(100))
    proposed_zoning = Column(String(100))
    entitlement_status = Column(String(50), default="not_started")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Builder(Base):
    __tablename__ = "builders"

    id = Column(Integer, primary_key=True)
    canonical_name = Column(Text, nullable=False, unique=True)
    type = Column(String(20), nullable=False, default="builder")
    scope = Column(String(20), nullable=False, default="national")
    source = Column(String(20), nullable=False, server_default="manual")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    aliases = relationship("BuilderAlias", back_populates="builder", cascade="all, delete-orphan")
    counties = relationship("BuilderCounty", back_populates="builder", cascade="all, delete-orphan")


class BuilderAlias(Base):
    __tablename__ = "builder_aliases"

    id = Column(Integer, primary_key=True)
    builder_id = Column(Integer, ForeignKey("builders.id", ondelete="CASCADE"), nullable=False)
    alias = Column(Text, nullable=False, unique=True)

    builder = relationship("Builder", back_populates="aliases")


class BuilderCounty(Base):
    __tablename__ = "builder_counties"

    id = Column(Integer, primary_key=True)
    builder_id = Column(Integer, ForeignKey("builders.id", ondelete="CASCADE"), nullable=False)
    county_id = Column(Integer, ForeignKey("counties.id", ondelete="CASCADE"), nullable=False)

    builder = relationship("Builder", back_populates="counties")
    county = relationship("County")


class LookupCategory(Base):
    __tablename__ = "lookup_categories"

    id = Column(Integer, primary_key=True)
    domain = Column(String(50), nullable=False)
    code = Column(String(50), nullable=False)
    label = Column(Text, nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
