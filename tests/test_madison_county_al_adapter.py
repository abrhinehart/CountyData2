"""Unit tests for the Madison County, AL CityView adapter.

The adapter is intentionally a blocked-on-credentials stub: it must refuse
to return permits (rather than silently falling back to fixture data) so
that registry introspection and live-runs surface the missing credential
situation loudly.

These tests pin that contract:
  1. Attribute sanity — slug, display_name, portal_url, and especially
     ``mode`` (must NOT be "live" while the adapter is a stub).
  2. ``fetch_permits`` raises ``NotImplementedError`` referencing the
     required credentials, rather than silently returning data.

No network, no fixtures, no credentials required.
"""

from __future__ import annotations

import pytest

from modules.permits.scrapers.adapters.madison_county_al import (
    MadisonCountyAlAdapter,
)
from modules.permits.scrapers.base import JurisdictionAdapter


def test_madison_instantiates_with_expected_attributes():
    adapter = MadisonCountyAlAdapter()
    assert adapter.slug == "madison-county-al"
    assert adapter.display_name == "Madison County, AL"
    assert adapter.portal_url == "https://cityview.madisoncountyal.gov/Portal"
    # Critical: adapter is a stub; mode must NOT be "live". Previously this
    # silently reported live while fetch_permits returned fixture data.
    assert adapter.mode != "live"
    assert adapter.mode == "fixture"
    assert isinstance(adapter, JurisdictionAdapter)


def test_madison_fetch_permits_raises_not_implemented():
    adapter = MadisonCountyAlAdapter()
    with pytest.raises(NotImplementedError, match="credentials"):
        adapter.fetch_permits()


def test_madison_fetch_permits_raises_with_date_args():
    # Confirm the date-argument signature also raises (no hidden fixture path).
    from datetime import date

    adapter = MadisonCountyAlAdapter()
    with pytest.raises(NotImplementedError):
        adapter.fetch_permits(date(2026, 1, 1), date(2026, 4, 1))
