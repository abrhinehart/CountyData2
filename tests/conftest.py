"""Shared pytest fixtures for CountyData2 tests.

This conftest builds a minimal FastAPI app (mounting only the commission
router) against a SQLite ``:memory:`` database. The real ``api.app`` pulls in
``shared.database.pool``, which requires a live Postgres connection; using a
minimal app avoids that import-time side effect.

Column types that SQLite cannot create (PostGIS ``Geometry``, PostgreSQL
``JSONB``) are patched to ``Text`` on the affected tables **before**
``Base.metadata.create_all`` runs. The commission router tests never query
those columns, so the patch is only needed so ``CREATE TABLE`` succeeds.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Text, create_engine, event
from sqlalchemy.orm import sessionmaker

# Importing models has the side effect of defining all tables on Base.metadata.
# We import shared.models first, then the commission module, so every table
# we need (counties, jurisdictions, subdivisions, cr_*) is registered. We also
# pre-import any module-level models that other tests may register on Base —
# this gives us one place to patch Geometry/JSONB columns for the whole
# pytest session.
from shared import models as shared_models  # noqa: F401
from shared.models import Base
from modules.commission import models as commission_models  # noqa: F401
from modules.inventory import models as inventory_models  # noqa: F401
from modules.commission.models import (
    CrCommissioner,
    CrCommissionerVote,
    CrEntitlementAction,
    CrJurisdictionConfig,
    CrSourceDocument,
    SOURCE_DOCUMENT_STATUS_COMPLETED,
    SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
)
from shared.models import County, Jurisdiction, Subdivision
from shared.sa_database import get_db

try:
    from geoalchemy2 import Geometry as _Geometry
except ImportError:  # pragma: no cover - geoalchemy2 is an optional dep
    _Geometry = None

try:
    from sqlalchemy.dialects.postgresql import JSONB as _JSONB
except ImportError:  # pragma: no cover
    _JSONB = None


def _patch_incompatible_columns() -> None:
    """Swap PostGIS ``Geometry`` and PG ``JSONB`` columns for ``Text``.

    SQLite has no PostGIS functions, and ``geoalchemy2`` registers DDL-event
    listeners that emit ``RecoverGeometryColumn`` / ``DropGeometryColumn``
    after ``CREATE TABLE``. Swapping the column types alone leaves those
    listeners in place, so we also drop them from any table whose columns we
    patched.
    """
    for table in list(Base.metadata.tables.values()):
        patched_this_table = False
        for column in table.columns:
            col_type = column.type
            if _Geometry is not None and isinstance(col_type, _Geometry):
                column.type = Text()
                patched_this_table = True
            elif _JSONB is not None and isinstance(col_type, _JSONB):
                column.type = Text()

        if patched_this_table:
            # Remove any DDL event listeners the Geometry type attached to
            # the table (after_create / before_drop hooks that call
            # RecoverGeometryColumn etc).
            for evt_name in ("after_create", "before_drop"):
                try:
                    listeners = list(table.dispatch._listen.get(evt_name, []))
                except AttributeError:  # pragma: no cover - defensive
                    listeners = []
                for listener in listeners:
                    event.remove(table, evt_name, listener)


_patch_incompatible_columns()


@pytest.fixture(scope="session")
def test_engine():
    """Session-scoped in-memory SQLite engine with all tables created."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
    )

    # SQLite needs foreign-key enforcement enabled per-connection.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    """Function-scoped session wrapped in a transaction rolled back on teardown."""
    connection = test_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = Session()

    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    """FastAPI ``TestClient`` with ``get_db`` overridden to yield ``db_session``."""
    # ``shared.database.pool`` is now lazy, so importing ``api.app`` no longer
    # requires a live Postgres connection.
    from api import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass  # teardown handled by db_session fixture

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def seed_commission_fixtures(session):
    """Seed a realistic minimal dataset for commission router tests.

    Creates:
      * 1 County
      * 2 Jurisdictions (one pinned via ``CrJurisdictionConfig``, one active manual)
      * 2 Subdivisions
      * 2 ``CrSourceDocument`` rows (one completed, one flagged)
      * 1 ``CrEntitlementAction`` tied to the completed doc + subdivision
      * 1 ``CrCommissioner`` and 1 ``CrCommissionerVote``

    Returns a dict with the created ORM instances for test assertions.
    """
    county = County(id=1, name="Polk", state="FL", is_active=True)
    session.add(county)
    session.flush()

    juris_pinned = Jurisdiction(
        id=1,
        slug="polk-bocc",
        name="Polk BOCC",
        county_id=county.id,
        is_active=True,
    )
    juris_other = Jurisdiction(
        id=2,
        slug="lakeland-city",
        name="Lakeland City Commission",
        county_id=county.id,
        is_active=True,
    )
    session.add_all([juris_pinned, juris_other])
    session.flush()

    cfg_pinned = CrJurisdictionConfig(
        jurisdiction_id=juris_pinned.id,
        commission_type="bocc",
        agenda_platform="legistar",
        is_active=True,
        pinned=True,
    )
    cfg_other = CrJurisdictionConfig(
        jurisdiction_id=juris_other.id,
        commission_type="city",
        agenda_platform="manual",
        is_active=True,
        pinned=False,
    )
    session.add_all([cfg_pinned, cfg_other])

    sub_a = Subdivision(
        id=10,
        canonical_name="Foo Ranch",
        county="Polk",
        county_id=county.id,
        entitlement_status="in_progress",
        lifecycle_stage="rezoning",
        is_active=True,
    )
    sub_b = Subdivision(
        id=11,
        canonical_name="Bar Estates",
        county="Polk",
        county_id=county.id,
        entitlement_status="not_started",
        is_active=True,
    )
    session.add_all([sub_a, sub_b])
    session.flush()

    doc_completed = CrSourceDocument(
        id=100,
        jurisdiction_id=juris_pinned.id,
        filename="2026-01-15-agenda.pdf",
        document_type="agenda",
        processing_status=SOURCE_DOCUMENT_STATUS_COMPLETED,
        extraction_attempted=True,
        extraction_successful=True,
    )
    doc_flagged = CrSourceDocument(
        id=101,
        jurisdiction_id=juris_pinned.id,
        filename="2026-02-01-minutes.pdf",
        document_type="minutes",
        processing_status=SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
        failure_reason="could not extract text",
    )
    session.add_all([doc_completed, doc_flagged])
    session.flush()

    action = CrEntitlementAction(
        id=1000,
        source_document_id=doc_completed.id,
        subdivision_id=sub_a.id,
        approval_type="zoning",
        outcome="approved",
        project_name="Foo Ranch",
        needs_review=False,
    )
    session.add(action)
    session.flush()

    commissioner = CrCommissioner(
        id=500,
        jurisdiction_id=juris_pinned.id,
        name="Jane Doe",
        title="Commissioner",
        active=True,
    )
    session.add(commissioner)
    session.flush()

    vote = CrCommissionerVote(
        entitlement_action_id=action.id,
        commissioner_id=commissioner.id,
        vote="yes",
    )
    session.add(vote)
    session.commit()

    return {
        "county": county,
        "juris_pinned": juris_pinned,
        "juris_other": juris_other,
        "sub_a": sub_a,
        "sub_b": sub_b,
        "doc_completed": doc_completed,
        "doc_flagged": doc_flagged,
        "action": action,
        "commissioner": commissioner,
    }
