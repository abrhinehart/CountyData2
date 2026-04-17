# Baldwin County AL -- CitizenServe Permits API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Baldwin County Planning & Zoning / Building Department (unincorporated county) |
| Portal URL | `https://www3.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=363&original_iid=0&original_contactID=0` |
| Reports URL | `https://www5.citizenserve.com/Portal/PortalController?Action=showPortalReports&installationID=363` |
| Vendor | CitizenServe (Online Solutions LLC) |
| Installation ID | 363 |
| UI | Java-style server session (JSP/Spring Admin backend; `Admin/Login.jsp`); Portal front-end is plain HTML + jQuery |
| Auth | Anonymous for public search/portal reports; named account for apply-filing |
| Registry entry | `county-registry.yaml` L585-598 has BI only; **no `pt:` block** |

Baldwin County has a **county-level** residential + commercial + septic permit portal at CitizenServe installation 363. **Coast cities each operate their own city permit portals** -- see §8 -- and those are out of scope.

## 2. Probe (2026-04-14)

```
GET https://baldwincountyal.gov/permits-and-licenses/building-planning-zoning
-> HTTP 200  (links out to CitizenServe installation 363)

GET https://www3.citizenserve.com/Portal/PortalController?Action=showHomePage&installationID=363
-> HTTP 200  (Citizenserve Online Portal; title "Home | Citizenserve Online Portal"; session cookie + Admin/Login.jsp reference)
```

CitizenServe is an established vendor in the PT space; their portals across jurisdictions follow the same shell (installation-ID keyed), so a future adapter could follow a generic CitizenServe pattern.

## 3. Search / Query Capabilities

Standard CitizenServe Portal search set:

- Permit Search: by permit number, address, parcel, applicant, date range, permit type.
- Inspection results search.
- Portal Reports (a separate `showPortalReports` action) lists summary reports the installation chooses to publish -- these are public pre-built views.
- Per-record detail: permit history, conditions, inspections, fees (fees visible if the installation exposes them).

No public REST / OData API. HTML / form-post only.

## 4. Field Inventory

Expected (standard CitizenServe Portal output):

- Permit / record number.
- Type, sub-type, work description, status.
- Address, parcel.
- Applicant, contractor, owner.
- Application date, issued date, expiration date.
- Valuation (when published).
- Inspection list + outcomes.

Exact field labels vary by installation configuration -- Baldwin's installation 363 specific field set is `unverified -- needs validation` until a crawl run.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No adapter under `modules/permits/scrapers/adapters/` for Baldwin AL. A CitizenServe adapter would mirror the Putnam County FL CitizenServe pattern (`docs/api-maps/putnam-county-citizenserve.md`) -- this repo already has CitizenServe integration code to reuse.

## 6. Auth Posture / Bypass Method

Anonymous for public search. Named account only for apply-filing / paying fees. Admin/Login.jsp is not our concern (that's the staff-side).

CitizenServe uses Java session cookies; a future adapter must hold the session across the initial home-page hit (which sets the cookie) and subsequent searches.

## 7. What We Extract vs What's Available

Zero extraction currently -- full surface available if/when an adapter lands.

## 8. Known Limitations and Quirks

- **County-level portal IS present** (CitizenServe installation 363). The registry-level permits surface is therefore in-scope as a genuine county-level adapter target, not a "no surface" note.
- **Coast cities operate their own permit portals and are OUT OF SCOPE for this CountyData2 county-level PT doc.** One-line probe notes per the task spec:
  - **Gulf Shores, AL**: city permits via the City of Gulf Shores Development Services department (city-run portal; out of scope for county-level CountyData2 PT).
  - **Orange Beach, AL**: city permits via the City of Orange Beach Community Development (separate city portal; out of scope).
  - **Fairhope, AL**: city permits via the City of Fairhope Building Department (separate city portal; out of scope). Fairhope is also a Probate Office physical location on the deed side -- do not conflate.
  - **Foley, AL**: city permits via the City of Foley Building and Planning (separate city portal; out of scope). Foley is also a Probate Office physical location.
  - Smaller municipalities (Daphne, Spanish Fort, Robertsdale, Bay Minette, Loxley, Summerdale, Silverhill, Elberta, Magnolia Springs, Perdido Beach, etc.) also issue their own permits inside city limits.
- CitizenServe front-end exposes `installationID=363` in the querystring -- this is the stable Baldwin ID and can be used in adapter config without worrying about per-user rewriting.
- CitizenServe "www3" vs "www5" subdomains appear to be the same installation served from a load-balancer pool -- both resolve to the same tenant data. Adapters should not pin to a specific "wwwN" number.
- Non-disclosure (deeds) is unrelated to permits; permit valuations (when published) are legitimate public data.
- `L L C` spacing applies on applicant/contractor/owner fields originating from county records downstream.

Source of truth: `county-registry.yaml` (baldwin-al L585-598, BI-only), Baldwin permits page `https://baldwincountyal.gov/permits-and-licenses/building-planning-zoning`, `docs/api-maps/putnam-county-citizenserve.md` (vendor pattern reference), live probe `https://www3.citizenserve.com/Portal/PortalController?...installationID=363`.
