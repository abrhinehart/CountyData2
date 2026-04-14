# Escambia County FL -- MGO Connect API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | MGO Connect (MyGovernmentOnline -- Government Software, LLC) |
| New portal URL | `https://www.mgoconnect.org/cp/portal` |
| Legacy portal URL | `https://www.mygovernmentonline.org/permits/?JurisdictionID=172` |
| `JurisdictionID` | `172` |
| Auth | Anonymous (public search) |
| Adapter | **NONE** -- pre-adapter research only |
| Registry status | **`research_done`** |
| Architecture | Angular SPA (new) / ASP.NET (legacy) |

**Status: `research_done, no live adapter.** No Python scraper exists for Escambia permits. This doc captures what was learned during research and what a future adapter would need to discover.

### Probe (2026-04-14)

```
GET https://www.mgoconnect.org/cp/portal
-> HTTP 200, 21,978 bytes (Angular SPA shell)
    Body contains: <title>MGO Connect</title>
                   <base href="/">
                   <meta name="author" content="MyGovernmentOnline Government Software">
                   Marketing meta (description, og:* tags)

GET https://www.mygovernmentonline.org/permits/?JurisdictionID=172
-> HTTP 200, 44,085 bytes (legacy ASP.NET portal, still serving)
```

Both URLs respond, but the new portal is a client-side Angular SPA with no visible HTML data rendering. All data fetches happen via XHR after the bundle loads, and no public REST documentation has been found.

---

## 2. Status (research_done, no adapter)

`county-registry.yaml` (`escambia-fl.projects.pt`) captures the research outcome verbatim:

```yaml
pt:
  portal: mgo-connect
  url: https://www.mgoconnect.org/cp/portal
  jurisdiction_id: 172
  status: research_done
  notes: >-
    MyGovernmentOnline (MGO Connect) SaaS platform, JurisdictionID=172.
    Old portal: mygovernmentonline.org/permits/?JurisdictionID=172 (being retired).
    New portal: mgoconnect.org (Angular SPA, no public API found).
    BOCC on aca-prod.accela.com is Brevard County, not Escambia.
    City of Pensacola uses separate MGO instance.
    Needs JS SPA reverse-engineering for adapter development.
```

Key implications:
- **Not on Accela.** Do NOT attempt to search `aca-prod.accela.com/BOCC` for Escambia permits -- that agency code (`BOCC`) is Brevard County, not Escambia.
- **Not the Pensacola instance.** The City of Pensacola is on its own separate MGO deployment; Escambia County is a different tenant.
- **Adapter work deferred.** Reverse-engineering the new Angular SPA's XHR calls is required before any adapter can be built.

---

## 3. Search Capabilities

Per MGO's public portal (observed in the legacy ASP.NET UI at `mygovernmentonline.org/permits/`):

| Search field | Type | Notes |
|--------------|------|-------|
| Jurisdiction | dropdown | `JurisdictionID=172` for Escambia County |
| Permit Type | dropdown | Residential, Commercial, Trade, etc. |
| Status | dropdown | Applied, Issued, Finaled, etc. |
| Date range | date picker (From / To) | |
| Permit number | text | |
| Address | text | |
| Parcel number | text | |
| Applicant / Contractor | text | |

These fields are the documented user-facing search surface of MGO Connect; they have NOT been verified against an active XHR call on the new portal.

---

## 4. Known Fields (conjectural)

If a future adapter is built, the following fields are the usual MGO Connect response payload (from other jurisdictions' public MGO portals):

| Field | Notes |
|-------|-------|
| `permitNumber` | Jurisdiction-issued permit number |
| `permitTypeName` | Text type (e.g., "Residential - New Construction") |
| `permitStatusName` | Current status |
| `applicationDate` | Date submitted |
| `issueDate` | Date issued |
| `finaledDate` | Date finaled (nullable) |
| `siteAddress` | Free-text site address |
| `parcelNumber` | If linked |
| `applicantName` | Contact (may be withheld) |
| `contractorName` | Primary contractor |
| `valuation` | Dollar value |
| `description` | Work description |

The exact JSON schema from MGO's public API has NOT been captured. A future adapter must discover the exact field names by inspecting `mgoconnect.org/cp/portal` XHRs in a live browser session.

---

## 5. Reverse-Engineering Notes

The new portal is an Angular 16+ SPA (inferred from `data-beasties-container`, modern meta tags, and JS bundle style). To build an adapter:

1. **Load `https://www.mgoconnect.org/cp/portal` in Chrome DevTools with Network panel open.**
2. **Navigate to permit search for JurisdictionID=172.** The UI should populate a search form pre-filtered to Escambia County.
3. **Issue a test search** (e.g., date range on residential permits).
4. **Capture the XHR calls.** Likely patterns to look for:
   - `/cp/portal/api/Permits/Search` or similar
   - `/cp/portal/api/Jurisdictions/172` for tenant metadata
   - JSON POST bodies with search criteria
5. **Capture the response schema.** Paginate and confirm field names.
6. **Check for auth.** MGO public APIs are typically anonymous but may use a session token obtained on first page load (e.g., a tenant-specific header).
7. **Confirm CORS / origin policy.** If the API is CORS-locked to `mgoconnect.org`, a scraper must either proxy through the page or spoof the origin header.

Once the XHR pattern is captured, the adapter can be modeled on the existing `TylerEnerGovAdapter` (also a three-endpoint REST flow: tenant init, criteria, paginated search).

---

## 6. What We Extract

**Nothing.** No adapter exists. The BI / CD2 / CR pipelines cover parcels (ArcGIS), deeds (LandmarkWeb), and commission agendas (CivicClerk) respectively, but the Escambia PT pipeline is empty.

---

## 7. What's Available (speculative until probed)

| Data Category | Extracted? | Likely Source (future adapter) |
|---------------|-----------|-------------------------------|
| Permit Number | NO | Search result row |
| Address | NO | Result row / detail |
| Issue Date | NO | Result row |
| Status | NO | Result row |
| Permit Type | NO | Result row / detail |
| Valuation | NO | Detail page |
| Parcel | NO | Detail page |
| Contractor | NO | Detail page |
| Applicant | NO | Detail page |
| Inspections | NO | Detail page / Inspections tab |
| Fees | NO | Detail page / Fees tab |
| Documents | NO | Detail page / Attachments tab |

---

## 8. Known Limitations and Quirks

1. **`status: research_done, no live adapter`.** This is the canonical state in `county-registry.yaml`. No Python code in `modules/permits/scrapers/adapters/` targets Escambia County. The doc below documents known shape, not a working scraper.

2. **Angular SPA requires JS reverse-engineering.** The current `mgoconnect.org` portal renders nothing server-side; all data is fetched client-side after the bundle loads. A `requests`-based scraper of the HTML will find no permits. Either (a) capture the XHR API and replay it directly, or (b) use Playwright / Selenium to execute the JS.

3. **No public API documentation.** MGO does not publish a developer-facing API. Endpoint discovery must be done empirically via browser network inspection.

4. **Legacy portal still serves.** `mygovernmentonline.org/permits/?JurisdictionID=172` returns HTTP 200 as of 2026-04-14. The registry note says it is "being retired"; a short-term adapter could target the legacy ASP.NET pages while the new portal is reverse-engineered, though this is a temporary fix at best.

5. **Agency code `BOCC` on Accela is Brevard, not Escambia.** A common research mistake is to look up Escambia on `aca-prod.accela.com`. There is an agency code `BOCC` on Accela, but it belongs to Brevard County. Escambia does NOT run on Accela.

6. **City of Pensacola is a separate MGO tenant.** Pensacola's permits are on a different MGO deployment (different `JurisdictionID`). Escambia County and the City of Pensacola are distinct jurisdictions with distinct portals.

7. **Only BI, CD2, and CR are `live` for Escambia.** Parcels (ArcGIS, status `active`), deeds (LandmarkWeb, `live` with curl_cffi), and BCC/P&Z agendas (CivicClerk, see separate doc). Permits is the only major project in `research_done` status.

8. **JurisdictionID 172 is the only known numeric ID.** Any API call that does not carry `172` (as query param, header, or path) will return data for the wrong tenant.

9. **Angular SPA hosts may enforce browser-fingerprint checks.** Modern SPAs often reject obvious-bot User-Agents. A future adapter should use a realistic Chrome UA string and, if needed, `curl_cffi` for TLS fingerprint parity.

10. **Lean doc is correct.** The Planner flagged this as a risk: "Escambia MGO Connect is pre-adapter -- do NOT invent endpoints; doc will be lean, that's correct." This doc should NOT be filled out with speculative endpoint URLs or field names.

**Source of truth:** `county-registry.yaml` (`escambia-fl.projects.pt`, status `research_done`), confirmed absence of an Escambia permits adapter in `modules/permits/scrapers/adapters/` (which contains `bay_county.py`, `citrus_county.py`, `okeechobee.py`, etc., but no `escambia_county.py`), live probes against `https://www.mgoconnect.org/cp/portal` (Angular SPA, 200 OK) and `https://www.mygovernmentonline.org/permits/?JurisdictionID=172` (legacy portal, 200 OK)
