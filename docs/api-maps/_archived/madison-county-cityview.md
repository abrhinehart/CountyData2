# Madison County AL -- CityView (Harris) Permits API Map (PT)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Madison County Building & Zoning (PRBD permits) |
| Portal URL | `https://cityview.madisoncountyal.gov/Portal` |
| Vendor | CityView (Harris Computer) |
| UI | ASP.NET server-rendered (jQuery 1.12 / jQuery UI 1.13) |
| Auth Posture | Vendor-native form login at `/Portal/Account/Login` (required for PRBD search) |
| Adapter | `modules/permits/scrapers/adapters/madison_county_al.py` (stub; `mode = "fixture"`) |
| Adapter status | **Blocked on CityView credentials** |
| Companion doc | `docs/permits/madison-county-al-cityview-todo.md` (execution plan when creds arrive) |
| Registry entry | `county-registry.yaml` L559-564 (`madison-al.projects.pt`) |

This map exists to record the external surface as we currently see it. The execution / implementation plan for the adapter lives in `docs/permits/madison-county-al-cityview-todo.md` -- that companion doc owns the step-by-step integration sequence, env-var names, verification checklist, and session-handling pattern references. This map references that plan and does not duplicate it.

## 2. Probe (2026-04-14)

```
GET https://cityview.madisoncountyal.gov/Portal
-> HTTP 200 (public landing: "Welcome - Madison County, AL - CityView Portal")
```

Landing page renders anonymously. Navigating into the Permit Application Search (`/Portal/Permit/Locator`) requires authentication -- the link triggers an ASP.NET postback that redirects unauthenticated visitors to `/Portal/Account/Login`. Login was **not** attempted during this probe per task constraints (no attempted account creation, no credential use).

## 3. Search / Query Capabilities

Anticipated (not yet verified -- adapter is a stub):

- **Permit Application Search** at `/Portal/Permit/Locator`. Target query: PRBD permit-number prefix + year (e.g., `PRBD-2026-*`).
- For each search row, follow the per-record permit-status detail URL to extract the per-permit fields.

The adapter's stub `NotImplementedError` message lists the expected authenticated flow succinctly: login POST, session reuse, PRBD-by-year search, follow status links, filter to residential-dwelling permit types. The full plan and required-tier discussion (citizen vs. contractor account) is in the companion todo -- not restated here.

## 4. Field Inventory

Expected per-permit fields (from `source_research.json` as referenced in the companion todo -- to be confirmed on first live run):

| Field | Source |
|-------|--------|
| Application Number | PRBD-YYYY-NNNNN |
| Address | Situs address |
| Property ID / Parcel | Cross-link to ArcGIS layer 185 |
| Type | Permit type (NEW, ALT, etc.) |
| Status | Issued / in-review / rejected |
| Category of Work | Residential / commercial |
| Description of Work | Free-form |
| Application Date | Filed |
| Issued Date | If status = issued |
| Property Owner | At time of application |

## 5. What We Extract / What a Future Adapter Would Capture

**We currently extract nothing.** The adapter is a stub that raises `NotImplementedError` with a message pointing at the companion todo. When credentials land and the adapter flips to `mode = "live"`, a future run would capture the 10 fields listed in Section 4, filter to likely new-residential-dwelling permits via PRBD-prefix + residential-type vocabulary, and emit one row per permit through the standard `JurisdictionAdapter.fetch_permits` interface.

## 6. Auth Posture / Bypass Method

**Auth is required for the search we need.** Landing page is public; Permit Application Search is not.

Expected auth shape (not yet implemented): HTTP POST to `/Portal/Account/Login` with email + password, carrying ASP.NET anti-forgery tokens extracted from the login-form HTML. Session cookies persist across subsequent search and detail-page fetches. The env vars `MADISON_AL_CITYVIEW_EMAIL` / `MADISON_AL_CITYVIEW_PASSWORD` are the intended credential holders.

Unresolved at probe time: whether a citizen-tier account is sufficient or a contractor/owner-tier account is required to see cross-parcel PRBD search results. This gating question is called out in the companion todo as a pre-implementation blocker. **unverified -- needs validation after credentials provisioned.**

## 7. What We Extract vs What's Available

| Available (expected) | Extracted? |
|----------------------|:----------:|
| Application number | NO (adapter stub) |
| Address | NO |
| Parcel | NO |
| Type / category / description | NO |
| Application + issued dates | NO |
| Owner | NO |
| Status | NO |

Everything pending credential acquisition + stub replacement.

## 8. Known Limitations and Quirks

- Adapter is **intentionally a stub** (`modules/permits/scrapers/adapters/madison_county_al.py`). `mode = "fixture"`, all calls raise `NotImplementedError`.
- The stub message and the companion todo (`docs/permits/madison-county-al-cityview-todo.md`) both emphasize one anti-footgun: this portal is NOT the Madison probate portal at `madisonprobate.countygovservices.com`. Different vendor (CityView/Harris vs. CountyGovServices), different auth (vendor-native form vs. Azure B2C), different UI (ASP.NET server-rendered vs. Kendo Grid), different data (permits vs. deeds). The probate integration's auth code and selectors are not reusable here.
- Search results are only available post-login -- any endpoint enumeration behind the wall would require an account, which is out of scope for this map.
- Account tier (citizen vs. owner/contractor) may gate which PRBD search views are reachable -- must be confirmed at account-creation time per the companion todo's blocker note.
- Session-handling pattern to follow is the Tyler EnerGov / CountyGovServices shape (build_session -> extract_form_fields -> POST login -> follow search) but with the CityView-specific ASP.NET anti-forgery token treatment; again per the companion todo.

Source of truth: `docs/permits/madison-county-al-cityview-todo.md`, `modules/permits/scrapers/adapters/madison_county_al.py`, `county-registry.yaml` (madison-al L559-564), live probe `https://cityview.madisoncountyal.gov/Portal`.
