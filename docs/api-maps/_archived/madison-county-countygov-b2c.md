# Madison County AL -- CountyGovServices Probate Deeds API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Madison County Probate Court (Alabama; Probate Judge, not Clerk of Court) |
| Portal URL | `https://madisonprobate.countygovservices.com` |
| Vendor | CountyGovServices (portal host) + Azure AD B2C (auth) |
| UI | Kendo Grid (paginated JSON) |
| Auth Posture | Azure AD B2C email+password (required, per-county tenant) |
| Bypass | `b2c-auth` (7-step OIDC handshake with terms-accept) |
| Client | `county_scrapers.countygov_client.CountyGovSession` |
| Registry entry | `county-registry.yaml` L544-558 (`madison-al.projects.cd2`) |
| Cross-ref | Mortgage same-day / last-name match, ~40% deed-attach rate |

## 2. Probe (2026-04-14)

```
GET https://madisonprobate.countygovservices.com/
-> HTTP 302 chain -> https://madisoncountyalntc.b2clogin.com/.../oauth2/v2.0/authorize?client_id=39401322-58ff-4dac-ad77-e7f86e31306b...
-> HTTP 200 (Azure AD B2C login page; tenant `madisoncountyalntc.onmicrosoft.com`, policy `b2c_1_signupsignin1`)
```

The bare root redirects into Azure B2C immediately. No public landing, no anonymous search. Returns `client_id`, `redirect_uri` = `/signin-oidc`, `response_type=code`, `response_mode=form_post` -- standard OIDC authorization-code flow.

**We did NOT attempt login during this probe** (credentials are per-county env vars; see Auth Posture below).

## 3. Search / Query Capabilities

Post-authentication, the portal exposes Kendo Grid DataSource JSON endpoints (not direct SQL). `CountyGovSession.search_by_date_range(begin, end)` and `search_by_grantor_grantee` wrap them.

Primary capability set:

- Date-range search on record date (MM/DD/YYYY).
- Doc-type filter (empty string = all; code passes `doc_types: ''` for Madison).
- Two session modes: `search_type='deed'` and `search_type='mortgage'`. Second session is constructed identically and searched for the same date window to enable cross-referencing.
- Pagination is handled inside Kendo Grid; the client iterates until the grid returns fewer rows than the page size.

## 4. Field Inventory

Fields returned per record (after Kendo Grid JSON normalization; exact column names vary by `search_type`):

| Logical Field | Deed search | Mortgage search |
|---------------|:-----------:|:---------------:|
| Direct Name (grantor) | YES | YES |
| Reverse Name (grantee) | YES | YES |
| Record Date | YES | YES |
| Doc Type | YES | YES |
| Legal | YES | -- |
| Mortgage Amount (`idVALUE_MORT`) | -- | YES |
| Mortgage Originator | -- | YES |

Sale price: **never present** (Alabama non-disclosure statute). Column mapping per `counties.yaml` is keyed off those names.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted per `pull_records.py` for `"Madison AL"`:

- Grantor / grantee (name normalization includes `L L C` <-> `LLC` aliasing on the downstream entity-match side).
- Record date.
- Doc type (WD, QC, TD, MORT, etc.).
- Legal description.
- Mortgage amount and originator (populated via `_match_mortgages` on matching deed rows; ~40% attach rate).

This is **Alabama non-disclosure**: there is no sale-price field on the deed, and none will ever appear. Mortgage amount is the strongest available price proxy. Same-day / last-name-overlap matching is the only cross-ref algorithm the client implements.

## 6. Auth Posture / Bypass Method

Azure AD B2C, per-county tenant. Madison's tenant: `madisoncountyalntc.onmicrosoft.com`, policy `b2c_1_signupsignin1`, client_id `39401322-58ff-4dac-ad77-e7f86e31306b`. Auth is a 7-step OIDC handshake (302 to B2C authorize, extract `SETTINGS.csrf` + `SETTINGS.transId`, POST `/SelfAsserted`, GET `/CombinedSigninAndSignup/confirmed`, POST `/signin-oidc`, GET `/Home/Requirements`, POST terms-accepted). The full step-by-step is documented in `AL-ONBOARDING.md` L77-88 -- see that doc; this map does not duplicate the sequence.

Required env vars: `MADISON_PORTAL_EMAIL`, `MADISON_PORTAL_PASSWORD`. Each AL CountyGovServices county uses a different B2C tenant but an identical flow shape, so `CountyGovSession` discovers tenant parameters from the initial redirect URL at runtime.

Not attempted during the probe. Credentials are operational secrets.

## 7. What We Extract vs What's Available

| Available in portal | Extracted? |
|---------------------|:----------:|
| Grantor | YES |
| Grantee | YES |
| Record date | YES |
| Doc type | YES |
| Legal description | YES |
| Mortgage amount (cross-ref) | YES (40% attach) |
| Mortgage originator | YES (40% attach) |
| Book / page | NO |
| Consideration | NOT PRESENT (non-disclosure) |
| Document image | NO (would require pay-per-view download) |

## 8. Known Limitations and Quirks

- **Non-disclosure state**: no sale price on deeds. Mortgage cross-ref is the only price proxy -- match rate is ~40%; the other ~60% of deeds receive no derived price.
- Mortgage cross-ref only works on **same-day** deed+mortgage pairs with last-name overlap. If the mortgage records a day off from the deed, the match fails silently.
- B2C sessions expire mid-pull on large date ranges; the client retries, but very large pulls should be chunked monthly.
- Every CountyGovServices AL county is assumed to have **its own** B2C tenant -- parameters extracted per-runtime from the 302. Env-var names are still hardcoded per-county in `pull_records.py` (one branch per county).
- Kendo Grid config HTML has drifted historically (`data-searchqueryid` attribute format); see `AL-ONBOARDING.md` Troubleshooting section for recovery patterns.
- Do NOT confuse this portal with Madison's CityView **permit** portal (`cityview.madisoncountyal.gov`) -- totally separate vendor, auth, and data domain. See `madison-county-cityview.md` and `docs/permits/madison-county-al-cityview-todo.md`.

Source of truth: `county-registry.yaml` (madison-al L544-558), `AL-ONBOARDING.md` (Steps 2-3, Troubleshooting), `county_scrapers/countygov_client.py`, `county_scrapers/pull_records.py`, `counties.yaml` "Madison AL" block, live probe `https://madisonprobate.countygovservices.com/`.
