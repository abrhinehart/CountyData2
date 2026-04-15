# Putnam County FL -- Citizenserve API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Citizenserve (SaaS permitting / licensing / inspections / code enforcement) |
| Portal URL | `https://www4.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=355` |
| Hero identifier | **`installationID=355`** |
| Query-string keys | `Action`, `ctzPagePrefix`, `installationID` |
| Auth | Anonymous (for browsing); account required for apply/pay workflows |
| Protocol | ASP.NET MVC (server-rendered HTML) with partial-postback controllers |
| Status | `research_done` (per `county-registry.yaml` L316-324) |
| Legacy surfaces | `apps.putnam-fl.com/bocc/pds/pds_inq/` (PDS Inquiry, 100-record limit), `apps.putnam-fl.com/bocc/pds/Permits.html` (static listing) |
| Phone | (386) 329-0307 |

### Probe (2026-04-14)

```
GET https://www4.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=355
-> HTTP 200, body ~94 KB
<title>Citizenserve Online Portal</title>
```

Content includes an "Apply, track, pay, and schedule inspections online" banner, standard Citizenserve portal navigation, and county-branded theming at `installationID=355`.

---

## 2. Citizenserve URL Structure

Citizenserve is a SaaS platform shared across many jurisdictions. Each jurisdiction is keyed by a numeric `installationID`. All `PortalController` URLs follow the same shape:

```
https://www{N}.citizenserve.com/Portal/PortalController
  ?Action={action_name}            # e.g., showHomePage, searchPermits, searchProjects
  &ctzPagePrefix=Portal_
  &installationID={id}             # Putnam = 355
```

Typical actions observed on Citizenserve portals:

| Action | What it does |
|--------|--------------|
| `showHomePage` | Portal landing (this is the probed URL) |
| `showPermitList` / `searchPermits` | Permit search UI / results |
| `showProjectList` / `searchProjects` | Project search |
| `showInspectionList` / `searchInspections` | Inspection scheduling / results |
| `showCodeCaseList` | Code enforcement case listing |
| `showLicenseList` | Business / professional licensing |
| `loginUser` | User login |

**The public API surface is HTML-only.** Citizenserve does not advertise a REST/OData endpoint; any permit scraping must drive the HTML form flows.

---

## 3. Registry Note (verbatim)

From `county-registry.yaml` L316-324:

> "Citizenserve SaaS platform (installationID=355). Apply, track, pay, and schedule inspections online. Also has legacy custom PDS Permits Public Inquiry at `apps.putnam-fl.com/bocc/pds/pds_inq/` (search by permit number, parcel, property name, 911 address, or date range; 100-record limit). New permits listing at `apps.putnam-fl.com/bocc/pds/Permits.html`. Phone: (386) 329-0307."

---

## 4. Legacy Surfaces (non-primary)

### PDS Inquiry (custom ASP)

```
https://apps.putnam-fl.com/bocc/pds/pds_inq/
```

A custom PDS (Planning & Development Services) Permits Public Inquiry. Search by:

- Permit number
- Parcel
- Property name
- 911 address
- Date range

**Known limit: 100 records per result set.** This is a hard cap on the inquiry UI; backfills via this surface require date-range chunking under 100 records per window.

### Static listing

```
https://apps.putnam-fl.com/bocc/pds/Permits.html
```

HTML page -- likely a recent-permits dump or a link catalog. Not a queryable surface.

### `apps.putnam-fl.com/bocc/` itself

Probe returned HTTP 403 (Forbidden):

```
GET https://apps.putnam-fl.com/bocc/
-> HTTP 403, 199 bytes
```

Likely requires internal county-network access. Do not rely on this root URL for scraping.

---

## 5. Scraper Status

No Citizenserve adapter exists in `modules/permits/scrapers/adapters/` as of 2026-04-14. The registry status `research_done` means:

1. The URL and installationID have been identified.
2. The legacy surfaces (`pds_inq/`, `Permits.html`) have been catalogued.
3. The 100-record limit on PDS Inquiry has been documented.
4. An adapter has NOT been written.

Before any automation:

- Decide between Citizenserve (primary, SaaS, richer) and PDS Inquiry (legacy, simpler, capped at 100).
- Reverse-engineer the Citizenserve search action URLs (`Action=searchPermits&installationID=355&...`).
- Identify permit-type / status filters and residential classifications.

---

## 6. Expected Search Capabilities (to verify on implementation)

Typical Citizenserve permit search fields:

| Field | Expected on Putnam? |
|-------|---------------------|
| Permit number | YES |
| Parcel | YES |
| Address | YES |
| Applicant name | YES |
| Contractor name | YES |
| Issue date range | YES |
| Apply date range | YES |
| Final date range | YES |
| Permit status | YES |
| Permit type | YES |
| Work class | YES |
| Project | YES |

All exposed through form-based HTML search; server renders a results table (often with server-side pagination and optional CSV export on some tenants).

---

## 7. Diff vs Okeechobee Tyler EnerGov (closest PT peer in doc set)

Putnam's Citizenserve portal is structurally very different from Okeechobee's Tyler EnerGov REST API.

| Attribute | Putnam (Citizenserve) | Okeechobee (Tyler EnerGov) |
|-----------|-----------------------|-----------------------------|
| Vendor | Citizenserve (SaaS) | Tyler Technologies |
| Protocol | HTML form postback | REST JSON |
| Three-endpoint REST flow | **NO** | YES (tenants -> criteria -> search) |
| installationID / TenantID | `installationID=355` (URL param) | TenantID in header |
| Search via | `Action=searchPermits` HTML query | POST JSON to `/api/energov/search/search` |
| Adapter exists | **NO** | YES (`OkeechobeeAdapter`) |
| Status | `research_done` | `live` |
| Registry URL | `www4.citizenserve.com/Portal/PortalController?...` | `okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice` |
| Legacy surfaces | 2 (PDS Inquiry, Permits.html) | 1 (migrated from TRAKiT) |

---

## 8. What We Would Extract (prospective)

Fields a future adapter should capture, based on typical Citizenserve tenants and Putnam's PDS Inquiry field list:

| Output field | Source field | Notes |
|--------------|--------------|-------|
| `permit_number` | Permit Number | Citizenserve-canonical format |
| `address` | Property Address or 911 Address | -- |
| `parcel_id` | Parcel | -- |
| `issue_date` | Issue Date | -- |
| `status` | Status | -- |
| `permit_type` | Permit Type | For residential filtering |
| `valuation` | Valuation | Present on some tenants |
| `raw_subdivision_name` | Project / Subdivision | -- |
| `raw_contractor_name` | Contractor | -- |
| `raw_applicant_name` | Applicant | -- |

Whether all fields are exposed at Putnam's `installationID=355` requires live inspection.

---

## 9. Known Limitations and Quirks

1. **`installationID=355` is the hero identifier.** All Citizenserve URL variations (home page, search page, results page, detail page) carry `installationID=355` as the query-string discriminator. Treat this integer as the primary tenant key.

2. **Status is `research_done`** -- no adapter exists yet. The Citizenserve integration is staged in research but not in code.

3. **Two legacy surfaces coexist with Citizenserve.** `apps.putnam-fl.com/bocc/pds/pds_inq/` (capped at 100 records) and `apps.putnam-fl.com/bocc/pds/Permits.html` (static listing) are the older PDS surfaces. Decide which single surface is authoritative before building a scraper -- running both is redundant and may produce duplicate permits.

4. **PDS Inquiry has a 100-record hard limit.** Date windows wider than ~100 permits silently truncate. Any backfill via the legacy surface must chunk windows narrowly.

5. **`apps.putnam-fl.com/bocc/` returns 403.** The root of the apps subdomain is not publicly accessible. Do NOT rely on it as a discovery surface; stick to the documented sub-paths.

6. **Citizenserve does NOT advertise REST/OData.** Any adapter must parse HTML. Server-side pagination is cookie/state driven (PostBack-style), so session-cookie management is non-trivial.

7. **The URL is shared with many other jurisdictions.** `www4.citizenserve.com/Portal/PortalController` hosts dozens of tenants via `installationID`. Ensure every request pins `installationID=355`; dropping the parameter lands on the shared Citizenserve home page, not Putnam's.

8. **Phone number in registry note: `(386) 329-0307`.** This is the public-facing PDS phone -- useful for manual verification when the scraper returns unexpected results.

9. **Tyler EnerGov peer template was the starting point** for this doc. Citizenserve's protocol is HTML-only but the Portal Overview / Source-of-truth / Quirks structure parallels the Tyler EnerGov docs.

10. **No `jurisdiction_registry.json` entry** for Putnam under `modules/permits/data/jurisdiction_registry.json` -- the registry lists Walton, Marion, DeSoto MS, Citrus, Polk, Okeechobee, but NOT Putnam. Adding Putnam requires both (a) writing a Citizenserve adapter and (b) registering it in `jurisdiction_registry.json`.

11. **`www4` subdomain vs `www3`/`www5`.** Citizenserve sharding spreads tenants across multiple www subdomains. Putnam is on `www4`. Hardcode the `www4` form in the adapter; the `installationID` alone is not sufficient (different tenants live on different www numbers).

12. **Planning Commission and Zoning Board of Adjustment are active** per registry note -- but those are commission bodies (CR surface), not permit surfaces. They do not appear in Citizenserve search. Separate tracking for those lives under `modules/commission/...`.

**Source of truth:** `county-registry.yaml` (`putnam-fl.projects.pt`, L316-324 -- full Citizenserve + legacy-surfaces note), live probe of `https://www4.citizenserve.com/Portal/PortalController?Action=showHomePage&ctzPagePrefix=Portal_&installationID=355` (HTTP 200, 94 KB, title "Citizenserve Online Portal"), probe of `https://apps.putnam-fl.com/bocc/` (HTTP 403, 199 bytes).
