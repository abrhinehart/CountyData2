"""
Commission Radar module models.

CR's `projects` table has been merged into the shared `subdivisions` table
(commission is the source of truth for subdivision names). CR's `phases` map
to the shared `phases` table. CR's module-specific tables are prefixed `cr_`.

Shared models (Subdivision, Phase, Jurisdiction, etc.) are imported from
shared.models and used in relationships.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from shared.models import Base, Jurisdiction, Phase, Subdivision  # noqa: F401


# Source document processing statuses
SOURCE_DOCUMENT_STATUS_DETECTED = "detected"
SOURCE_DOCUMENT_STATUS_FILTERED_OUT = "filtered_out"
SOURCE_DOCUMENT_STATUS_EXTRACTION_FAILED = "extraction_failed"
SOURCE_DOCUMENT_STATUS_COMPLETED = "completed"
SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW = "flagged_for_review"
SOURCE_DOCUMENT_STATUS_REVIEW_REJECTED = "review_rejected"


def utc_now():
    """Return a timezone-aware UTC timestamp for ORM defaults."""
    return datetime.now(UTC)


class CrJurisdictionConfig(Base):
    """Commission-specific jurisdiction config (commission_type, agenda_platform, etc.)."""

    __tablename__ = "cr_jurisdiction_config"

    id = Column(Integer, primary_key=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id"), unique=True, nullable=False)
    commission_type = Column(String(50), nullable=False)
    agenda_source_url = Column(String(500), nullable=True)
    agenda_platform = Column(String(100), nullable=True)
    has_duplicate_page_bug = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    pinned = Column(Boolean, default=False)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    jurisdiction = relationship("Jurisdiction")


class CrSourceDocument(Base):
    __tablename__ = "cr_source_documents"

    id = Column(Integer, primary_key=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_hash = Column(String(64), nullable=True)
    source_url = Column(String(1000), nullable=True)
    external_document_id = Column(String(255), nullable=True)
    file_format = Column(String(10), nullable=True)
    document_type = Column(String(50), nullable=False)
    meeting_date = Column(Date, nullable=True)
    page_count = Column(Integer, nullable=True)
    extracted_text_length = Column(Integer, nullable=True)
    keyword_filter_passed = Column(Boolean, nullable=True)
    extraction_attempted = Column(Boolean, default=False)
    extraction_successful = Column(Boolean, nullable=True)
    items_extracted = Column(Integer, nullable=True)
    items_after_filtering = Column(Integer, nullable=True)
    processing_status = Column(String(50), nullable=False, default=SOURCE_DOCUMENT_STATUS_DETECTED)
    failure_stage = Column(String(50), nullable=True)
    failure_reason = Column(Text, nullable=True)
    processing_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    jurisdiction = relationship("Jurisdiction")
    entitlement_actions = relationship("CrEntitlementAction", back_populates="source_document")


class CrEntitlementAction(Base):
    """CR entitlement actions. FK to shared subdivisions (formerly projects) and shared phases."""

    __tablename__ = "cr_entitlement_actions"

    id = Column(Integer, primary_key=True)
    source_document_id = Column(Integer, ForeignKey("cr_source_documents.id"), nullable=True)
    subdivision_id = Column(Integer, ForeignKey("subdivisions.id"), nullable=True)
    phase_id = Column(Integer, ForeignKey("phases.id"), nullable=True)
    linked_action_id = Column(Integer, ForeignKey("cr_entitlement_actions.id"), nullable=True)

    case_number = Column(String(100), nullable=True)
    ordinance_number = Column(String(100), nullable=True)
    parcel_ids = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)

    approval_type = Column(String(50), nullable=False)
    outcome = Column(String(50), nullable=True)
    vote_detail = Column(String(100), nullable=True)
    conditions = Column(Text, nullable=True)
    reading_number = Column(String(20), nullable=True)
    scheduled_first_reading_date = Column(Date, nullable=True)
    scheduled_final_reading_date = Column(Date, nullable=True)

    action_summary = Column(Text, nullable=True)
    applicant_name = Column(String(255), nullable=True)
    current_land_use = Column(String(100), nullable=True)
    proposed_land_use = Column(String(100), nullable=True)
    current_zoning = Column(String(100), nullable=True)
    proposed_zoning = Column(String(100), nullable=True)
    acreage = Column(Float, nullable=True)
    lot_count = Column(Integer, nullable=True)
    project_name = Column(String(255), nullable=True)  # raw extracted name before matching
    phase_name = Column(String(100), nullable=True)
    land_use_scale = Column(String(20), nullable=True)
    action_requested = Column(String(100), nullable=True)

    meeting_date = Column(Date, nullable=True)
    agenda_section = Column(String(255), nullable=True)
    multi_project_flag = Column(Boolean, default=False)
    backup_doc_filename = Column(String(255), nullable=True)
    needs_review = Column(Boolean, default=False)
    review_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    source_document = relationship("CrSourceDocument", back_populates="entitlement_actions")
    subdivision = relationship("Subdivision")
    phase = relationship("Phase")
    linked_action = relationship("CrEntitlementAction", remote_side=[id])
    commissioner_votes = relationship(
        "CrCommissionerVote",
        back_populates="entitlement_action",
        cascade="all, delete-orphan",
    )


class CrCommissioner(Base):
    __tablename__ = "cr_commissioners"

    id = Column(Integer, primary_key=True)
    jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    title = Column(String(100), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "name", name="uq_cr_commissioner_juris_name"),
    )

    jurisdiction = relationship("Jurisdiction")
    votes = relationship("CrCommissionerVote", back_populates="commissioner", cascade="all, delete-orphan")


class CrCommissionerVote(Base):
    __tablename__ = "cr_commissioner_votes"

    id = Column(Integer, primary_key=True)
    entitlement_action_id = Column(
        Integer,
        ForeignKey("cr_entitlement_actions.id", ondelete="CASCADE"),
        nullable=False,
    )
    commissioner_id = Column(
        Integer,
        ForeignKey("cr_commissioners.id", ondelete="CASCADE"),
        nullable=False,
    )
    vote = Column(String(20), nullable=False)
    made_motion = Column(Boolean, default=False)
    seconded_motion = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    entitlement_action = relationship("CrEntitlementAction", back_populates="commissioner_votes")
    commissioner = relationship("CrCommissioner", back_populates="votes")


# Legacy aliases for code compatibility with the old CR module names
# (code that imported Project/ProjectAlias/SourceDocument/EntitlementAction/Commissioner/CommissionerVote)
Project = Subdivision  # Projects merged into subdivisions
SourceDocument = CrSourceDocument
EntitlementAction = CrEntitlementAction
Commissioner = CrCommissioner
CommissionerVote = CrCommissionerVote
