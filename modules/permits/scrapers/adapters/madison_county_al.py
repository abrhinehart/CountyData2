"""Madison County, AL permit adapter — CityView (Harris) portal.

Status: **Blocked on credentials.** The target portal at
``https://cityview.madisoncountyal.gov/Portal`` is an authenticated CityView
(Harris) deployment. Public browsing is limited; the permit search we need
(the Permit Application Search at ``/Portal/Permit/Locator`` for PRBD permit
numbers by year, with links out to permit-status detail pages) is only
reachable after logging in at ``/Portal/Account/Login``.

This adapter is intentionally a no-op until CityView portal credentials are
provisioned. Required environment variables (to be added to ``.env.example``
once accounts exist):

* ``MADISON_AL_CITYVIEW_EMAIL``
* ``MADISON_AL_CITYVIEW_PASSWORD``

Implementation notes for the future author:

* Session pattern: follow the authenticated adapter patterns used elsewhere
  in this codebase (Tyler EnerGov / CountyGov session helpers) — login POST,
  reuse the ``requests.Session`` cookie jar across subsequent search
  requests, extract anti-forgery tokens from the login form if CityView
  uses them.
* Target flow: after login, POST against ``/Portal/Permit/Locator`` with a
  PRBD year search, then follow the permit-status links for each result to
  scrape detail pages.

**Do not confuse this with the Madison County probate portal.** The probate
records integration documented in ``AL-ONBOARDING.md`` targets
``madisonprobate.countygovservices.com`` — a completely different vendor
(CountyGovServices / Azure AD B2C) with a Kendo Grid UI. Findings from that
portal do not apply here: different domain, different vendor, different
auth flow, different data.
"""

from __future__ import annotations

from datetime import date

from modules.permits.scrapers.base import JurisdictionAdapter


class MadisonCountyAlAdapter(JurisdictionAdapter):
    """Stub adapter: raises ``NotImplementedError`` until CityView creds land."""

    slug = "madison-county-al"
    display_name = "Madison County, AL"
    # Inherit the base-class default of ``"fixture"``. Explicitly set here so
    # that registry introspection (``adapter.mode``) never again reports
    # ``"live"`` while the adapter is actually a stub.
    mode = "fixture"
    bootstrap_lookback_days = 90
    rolling_overlap_days = 14

    portal_url = "https://cityview.madisoncountyal.gov/Portal"

    def fetch_permits(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        raise NotImplementedError(
            "Madison County, AL permit adapter is blocked on CityView portal "
            "credentials. To implement: set MADISON_AL_CITYVIEW_EMAIL and "
            "MADISON_AL_CITYVIEW_PASSWORD, then build an authenticated session "
            "against https://cityview.madisoncountyal.gov/Portal/Account/Login "
            "and search /Portal/Permit/Locator (PRBD by year). See "
            "docs/permits/madison-county-al-cityview-todo.md for the full plan."
        )
