# Madison County, AL — CityView Permits Adapter (Blocked on Credentials)

Status: **Blocked — waiting on CityView portal credentials.** The adapter at
`modules/permits/scrapers/adapters/madison_county_al.py` is intentionally a
stub that raises `NotImplementedError` until a working CityView account is
provisioned. This document is the execution plan for when that happens.

## Target portal

- **URL**: `https://cityview.madisoncountyal.gov/Portal`
- **Vendor**: CityView (Harris) — the same platform family used for
  CityView deployments at other Alabama jurisdictions and by Bay County FL's
  CityView portal. See `modules/permits/scrapers/adapters/bay_county.py` for
  a *public-facing* CityView reference, though note Madison's public surface
  is much smaller: most data sits behind auth.
- **Login endpoint**: `https://cityview.madisoncountyal.gov/Portal/Account/Login`
- **Primary search we need**: `https://cityview.madisoncountyal.gov/Portal/Permit/Locator`
  (Permit Application Search, queryable by PRBD permit-number prefix and year,
  then follow detail links to permit-status pages).

## Required environment variables

Add to `.env.example` and to the deploy secret store once credentials exist:

- `MADISON_AL_CITYVIEW_EMAIL`
- `MADISON_AL_CITYVIEW_PASSWORD`

The credentials question that matters at account-creation time: CityView
distinguishes between citizen/public accounts and licensed-owner/contractor
accounts. The `source_research.json` notes previously claimed the permit
locator is only reachable after authentication — it is currently unverified
whether a basic citizen-tier account is sufficient, or whether an
owner/contractor tier is required to see cross-parcel PRBD search results.
**Confirm which tier is needed as part of account setup** before investing in
the scraper implementation.

## Target extraction flow (once credentials land)

1. POST login against `/Portal/Account/Login` with email + password,
   carrying anti-forgery tokens extracted from the login form.
2. Reuse the authenticated `requests.Session` cookie jar for subsequent
   search and detail requests.
3. POST a PRBD-by-year query against `/Portal/Permit/Locator`.
4. For each result row, follow the permit-status detail link and extract
   the fields listed in `source_research.json` under this jurisdiction:
   application number, address, property id, type, status, category of
   work, description of work, application date, issued date, property
   owner.
5. Filter to likely new-residential-dwelling permits (the original stub
   doc described "filters permit-status details down to likely new
   residential dwelling permits" — port the same heuristic the author had
   in mind: PRBD prefix + residential-type vocabulary).

## Session-handling reference patterns

Use existing authenticated adapters in this repo as the template, rather
than inventing a new session helper:

- **Tyler EnerGov** adapters (`modules/permits/scrapers/adapters/tyler_energov.py`
  and the jurisdiction subclasses) show the public-API pattern — not
  directly applicable here because EnerGov exposes a REST API — but do
  show the session/retry wrapper conventions this codebase prefers.
- **CountyGovServices / Azure B2C** auth helpers used by the probate-side
  integration (`modules/probate/...`, see `AL-ONBOARDING.md`) show the
  login-flow + cookie-jar shape. **Do not copy the auth payload** — that
  portal uses Azure AD B2C and is a different vendor — but the
  session-scaffolding pattern (build_session → extract_form_fields → POST
  login → follow search) is the right shape to mirror for CityView.

## This is NOT the Madison probate portal

`AL-ONBOARDING.md` documents extensive work against
`madisonprobate.countygovservices.com`. That is the **probate records**
portal — deeds, liens, marriage records — provided by **CountyGovServices**
(vendor), using **Azure AD B2C** for auth and a **Kendo Grid** UI for data.

This CityView permit portal is a completely different animal:

| Attribute        | Madison Probate (`AL-ONBOARDING.md`)   | Madison CityView (this doc)    |
|------------------|----------------------------------------|--------------------------------|
| Domain           | `madisonprobate.countygovservices.com` | `cityview.madisoncountyal.gov` |
| Vendor           | CountyGovServices                      | CityView (Harris)              |
| Auth             | Azure AD B2C                           | Vendor-native form login       |
| UI framework     | Kendo Grid                             | ASP.NET server-rendered        |
| Data domain      | Probate records (deeds, liens)         | Building permits               |
| Integration home | `modules/probate/`                     | `modules/permits/`             |

Findings, auth code, selectors, and session helpers from the probate
integration do **not** transfer. Treat this as a greenfield CityView
scraper.

## Verification checklist before marking live

When the future author flips this adapter to `mode = "live"`:

- [ ] Both env vars are present in `.env.example` and the secret store.
- [ ] `source_research.json` → `live_ready: true`, `status: "live-authenticated-cityview-adapter"`.
- [ ] `jurisdiction_registry.json` → `active: true`, `fragile_note` updated
      to describe the real fragility (auth session expiry, PRBD prefix
      drift, etc.).
- [ ] `seed_pt_jurisdiction_config.py` → `scrape_mode` tuple entry back to
      `"live"`.
- [ ] `tests/test_madison_county_al_adapter.py` → replaced (not merely
      deleted) with live-path tests modeled on `test_davenport_adapter.py`
      or `test_accela_citizen_access_adapter.py`: a fixture HTML row, an
      extraction test, a permit-type filter test.
- [ ] Full test suite still green.
