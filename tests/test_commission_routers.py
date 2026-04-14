"""Tests for Commission Radar routers.

These tests protect the recent CR router sweep — the removal of several
schema-mismatch TODOs — by exercising each router against an in-memory
SQLite database via FastAPI ``TestClient``. The goal is regression coverage,
not exhaustive behaviour verification.
"""

from __future__ import annotations

import json

import pytest
from fastapi.responses import JSONResponse

from modules.commission.models import (
    CrEntitlementAction,
    CrJurisdictionConfig,
    CrSourceDocument,
    SOURCE_DOCUMENT_STATUS_COMPLETED,
    SOURCE_DOCUMENT_STATUS_FLAGGED_FOR_REVIEW,
)
from modules.commission.routers import helpers as helpers_module
from shared.models import Jurisdiction

from tests.conftest import seed_commission_fixtures


# ---------------------------------------------------------------------------
# Dashboard tests (Wave 2)
# ---------------------------------------------------------------------------


def test_dashboard_jurisdictions_groups_by_county(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/dashboard/jurisdictions")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert set(body.keys()) == {"pinned", "groups", "flat"}
    # The pinned jurisdiction has pinned=True on CrJurisdictionConfig.
    assert len(body["pinned"]) == 1
    assert body["pinned"][0]["slug"] == "polk-bocc"
    # County name must come from the shared counties table via county_id.
    assert body["pinned"][0]["county"] == "Polk"
    # Non-pinned jurisdictions are grouped by county name.
    assert "Polk" in body["groups"]
    other_slugs = [e["slug"] for e in body["groups"]["Polk"]]
    assert "lakeland-city" in other_slugs
    # Flat is a slug -> name map.
    assert body["flat"]["polk-bocc"] == "Polk BOCC"


def test_dashboard_summary_returns_counts(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/dashboard/summary")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    expected = {
        "documents_processed",
        "projects_tracked",
        "actions_extracted",
        "needs_review",
        "jurisdictions_active",
    }
    assert expected.issubset(body.keys())
    for key in expected:
        assert isinstance(body[key], int), f"{key} should be an int"

    # 1 completed doc, 1 action tied to subdivision, 2 active configs.
    assert body["documents_processed"] == 1
    assert body["actions_extracted"] == 1
    assert body["projects_tracked"] == 1
    assert body["jurisdictions_active"] == 2
    assert body["needs_review"] == 0


def test_dashboard_summary_category_filter(client, db_session):
    fixtures = seed_commission_fixtures(db_session)

    # Add a second action with approval_type outside the "development" set.
    non_dev = CrEntitlementAction(
        source_document_id=fixtures["doc_completed"].id,
        subdivision_id=fixtures["sub_b"].id,
        approval_type="text_amendment",  # regulatory, not development
        outcome="approved",
    )
    db_session.add(non_dev)
    db_session.commit()

    # Without filter: 2 actions total.
    resp_all = client.get("/api/commission/dashboard/summary")
    assert resp_all.status_code == 200
    assert resp_all.json()["actions_extracted"] == 2

    # With development filter: only the zoning action counts.
    resp_dev = client.get(
        "/api/commission/dashboard/summary",
        params={"approval_category": "development"},
    )
    assert resp_dev.status_code == 200
    assert resp_dev.json()["actions_extracted"] == 1


def test_dashboard_actions_happy_path(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/dashboard/actions")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert {"items", "total", "page", "pages"}.issubset(body.keys())
    assert body["total"] == 1
    assert body["page"] == 1
    assert body["pages"] >= 1

    item = body["items"][0]
    # jurisdiction_name comes from the source document's jurisdiction.
    assert item["jurisdiction_name"] == "Polk BOCC"
    assert item["jurisdiction_slug"] == "polk-bocc"
    assert item["approval_type"] == "zoning"
    # project_name should fall back to subdivision.canonical_name if needed.
    assert item["project_name"] == "Foo Ranch"


def test_dashboard_actions_jurisdiction_filter(client, db_session):
    fixtures = seed_commission_fixtures(db_session)

    # Create a second action attached to a document in the other jurisdiction.
    other_doc = CrSourceDocument(
        jurisdiction_id=fixtures["juris_other"].id,
        filename="other.pdf",
        document_type="agenda",
        processing_status=SOURCE_DOCUMENT_STATUS_COMPLETED,
    )
    db_session.add(other_doc)
    db_session.flush()
    other_action = CrEntitlementAction(
        source_document_id=other_doc.id,
        subdivision_id=fixtures["sub_b"].id,
        approval_type="zoning",
        outcome="approved",
    )
    db_session.add(other_action)
    db_session.commit()

    # No filter: both actions returned.
    resp_all = client.get("/api/commission/dashboard/actions")
    assert resp_all.status_code == 200
    assert resp_all.json()["total"] == 2

    # Filter to the pinned jurisdiction by slug.
    resp_filtered = client.get(
        "/api/commission/dashboard/actions",
        params={"jurisdiction": "polk-bocc"},
    )
    assert resp_filtered.status_code == 200
    body = resp_filtered.json()
    assert body["total"] == 1
    assert body["items"][0]["jurisdiction_slug"] == "polk-bocc"


# ---------------------------------------------------------------------------
# Review queue + Roster + Scrape tests (Wave 3)
# ---------------------------------------------------------------------------


def test_review_queue_empty(client, db_session):
    # No seeded data — no flagged docs.
    resp = client.get("/api/commission/review/queue")
    assert resp.status_code == 200
    assert resp.json() == []


def test_review_queue_returns_flagged_only(client, db_session):
    seed_commission_fixtures(db_session)
    # Seeded data includes one completed doc and one flagged doc.

    resp = client.get("/api/commission/review/queue")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["filename"] == "2026-02-01-minutes.pdf"
    assert items[0]["jurisdiction"] == "Polk BOCC"


def test_roster_counties_distinct(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/roster/counties")
    assert resp.status_code == 200
    counties = resp.json()
    # Both subdivisions share Polk county; the endpoint must dedupe via DISTINCT.
    assert counties == ["Polk"]


def test_roster_list_happy_path(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/roster")
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert {"items", "total", "page", "pages"}.issubset(body.keys())
    # Roster joins Project -> Jurisdiction via shared county_id, which produces
    # one row per (project, jurisdiction) pair. With 2 projects and 2
    # jurisdictions sharing Polk County, that's 4 rows.
    assert body["total"] == 4
    project_names = {item["name"] for item in body["items"]}
    assert project_names == {"Foo Ranch", "Bar Estates"}
    # jurisdiction_name must populate via Jurisdiction.county_id == Project.county_id.
    juris_names = {item["jurisdiction_name"] for item in body["items"]}
    assert juris_names & {"Polk BOCC", "Lakeland City Commission"}


def test_roster_list_search_filter(client, db_session):
    seed_commission_fixtures(db_session)

    resp = client.get("/api/commission/roster", params={"search": "foo"})
    assert resp.status_code == 200
    body = resp.json()
    # "Foo Ranch" matches; "Bar Estates" does not. Two jurisdictions share
    # Polk county so the ILIKE filter returns 2 (project × jurisdiction) rows.
    assert body["total"] == 2
    assert {item["name"] for item in body["items"]} == {"Foo Ranch"}


def test_roster_detail_returns_lifecycle_and_actions(client, db_session):
    fixtures = seed_commission_fixtures(db_session)

    resp = client.get(f"/api/commission/roster/{fixtures['sub_a'].id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["id"] == fixtures["sub_a"].id
    assert body["name"] == "Foo Ranch"
    assert "lifecycle_progress" in body
    assert isinstance(body["lifecycle_progress"], list) and body["lifecycle_progress"]
    assert "actions" in body
    assert len(body["actions"]) == 1
    assert body["actions"][0]["approval_type"] == "zoning"

    # 404 for missing project.
    missing = client.get("/api/commission/roster/999999")
    assert missing.status_code == 404


def test_scrape_jurisdictions_filters_inactive(client, db_session):
    fixtures = seed_commission_fixtures(db_session)

    # Seed has: polk-bocc (legistar, active) and lakeland-city (manual, active).
    # The scrape/jurisdictions endpoint excludes platform=="manual" and inactive
    # rows. Add an inactive legistar config to confirm the filter.
    inactive_juris = Jurisdiction(
        slug="inactive-city",
        name="Inactive City",
        county_id=fixtures["county"].id,
        is_active=True,
    )
    db_session.add(inactive_juris)
    db_session.flush()
    inactive_cfg = CrJurisdictionConfig(
        jurisdiction_id=inactive_juris.id,
        commission_type="city",
        agenda_source_url="https://example.com/agendas",
        agenda_platform="legistar",
        is_active=False,
    )
    db_session.add(inactive_cfg)

    # Give the pinned juris a real agenda URL so it's "scrapable".
    cfg = (
        db_session.query(CrJurisdictionConfig)
        .filter_by(jurisdiction_id=fixtures["juris_pinned"].id)
        .first()
    )
    cfg.agenda_source_url = "https://example.com/polk"
    db_session.commit()

    resp = client.get("/api/commission/scrape/jurisdictions")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    slugs = {item["slug"] for item in body}
    assert "polk-bocc" in slugs
    assert "lakeland-city" not in slugs  # platform is "manual"
    assert "inactive-city" not in slugs  # is_active is False


# ---------------------------------------------------------------------------
# Helpers pure function tests (Wave 4)
# ---------------------------------------------------------------------------


def test_helpers_pure_functions():
    # _send prefixes SSE data: and trailing newlines.
    frame = helpers_module._send({"event": "hello"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    # Round-trips through JSON.
    payload = json.loads(frame.removeprefix("data: ").strip())
    assert payload == {"event": "hello"}

    # _json_error returns a FastAPI JSONResponse with the given status.
    err = helpers_module._json_error("nope", status_code=418)
    assert isinstance(err, JSONResponse)
    assert err.status_code == 418
    # JSONResponse.body is bytes of the rendered JSON.
    assert json.loads(err.body.decode("utf-8")) == {"error": "nope"}

    # _document_storage_slug prefers slug when set.
    class _J:
        slug = "polk-bocc"
        name = "Polk BOCC"

    assert helpers_module._document_storage_slug(_J()) == "polk-bocc"

    # Falls back to lower-case dashed name when slug is empty.
    class _JNoSlug:
        slug = ""
        name = "Some County"

    assert helpers_module._document_storage_slug(_JNoSlug()) == "some-county"

    # _source_document_file_path joins storage dir + slug + filename.
    class _Doc:
        filename = "agenda.pdf"

    full = helpers_module._source_document_file_path(_J(), _Doc())
    assert full.endswith("agenda.pdf")
    assert "polk-bocc" in full.replace("\\", "/")
