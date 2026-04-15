# Brevard County FL -- Accela Citizen Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) |
| Portal URL | `https://aca-prod.accela.com/BOCC/Default.aspx` |
| Agency code | `BOCC` (all uppercase, four letters -- stands for Board of County Commissioners) |
| Building module entry | `https://aca-prod.accela.com/BOCC/Cap/CapHome.aspx?module=Building` |
| Auth | Anonymous search + detail view; login required for scheduling / payment / upload (same as peer Accela deployments) |
| Adapter | No Brevard-specific adapter -- generic `AccelaCitizenAccessAdapter` in `modules/permits/scrapers/adapters/accela_citizen_access.py` applies |
| Registry status | Not explicitly tracked -- Brevard is **absent from `county-registry.yaml`** (no `brevard-fl` block) |

**CRITICAL cross-reference:** The Accela agency code `BOCC` belongs to **Brevard County**, NOT Escambia. See `escambia-county-mgo-connect.md` (§1, §8 Quirk 5, §2 registry note) for the documented caveat -- a common research mistake is to look up Escambia on `aca-prod.accela.com/BOCC`. Escambia runs on MGO Connect (not Accela); the BOCC agency on Accela is Brevard. This doc resolves that ambiguity: `aca-prod.accela.com/BOCC` is Brevard.

### Probe (2026-04-14)

```
GET https://aca-prod.accela.com/BOCC/Default.aspx
-> HTTP 200, ~73.4 KB (standard ACA shell, Accela Citizen Access portal)
  <title>Accela Citizen Access</title>
  <html ng-app="appAca" ...>
  Uses standard ctl00$PlaceHolderMain ASP.NET form identifiers.
  Customization path: /BOCC/Customization/BOCC/globalcustomscriptbefore.css

GET https://aca-prod.accela.com/BOCC/Cap/CapHome.aspx?module=Building
-> HTTP 200, ~258.3 KB (Building module home with search form)
```

---

## 2. Why `BOCC` = Brevard (not Escambia)

Accela customers typically use an agency code that matches either a short county nickname (e.g. `POLKCO` for Polk, `CITRUS` for Citrus) or a three-letter abbreviation. Brevard chose `BOCC` -- literally "Board of County Commissioners" -- as its four-letter agency code. This is distinctive: most counties do not use the generic BOCC initialism in their Accela agency codes because multiple counties have a BOCC.

Escambia (a separate FL county) runs on a completely different platform -- MGO Connect (MyGovernmentOnline, JurisdictionID=172) -- and does NOT have any Accela portal. The registry block for Escambia permits (`escambia-fl.projects.pt`) explicitly records: "BOCC on aca-prod.accela.com is Brevard County, not Escambia." See `escambia-county-mgo-connect.md` for the Escambia side.

When researching Accela tenants in Florida, if you land on `aca-prod.accela.com/BOCC`, you are looking at Brevard County Building Department -- not Escambia.

---

## 3. Search Capabilities

### Search URL

```
https://aca-prod.accela.com/BOCC/Cap/CapHome.aspx?module=Building&TabName=Building
```

### Search form types (General Search is the adapter default)

Per the inherited `AccelaCitizenAccessAdapter`, the following fields are available on the Building module's General Search form:

#### Record Information
| Field | Type | Used by adapter? |
|-------|------|------------------|
| Permit Number | text | -- |
| Record Type | dropdown | YES (adapter-specific `target_record_type`) |
| Project Name | text | -- |
| Start Date | date picker (MM/DD/YYYY) | YES |
| End Date | date picker (MM/DD/YYYY) | YES |

#### Licensed Professional / Address / Business (available, unused)
| Group | Fields |
|-------|--------|
| Licensed Professional | License Type, State License Number, First Name, Last Name |
| Business | Name of Business, Business License # |
| Address | Street No. (From/To), Direction, Street Name, Street Type, Unit Type/No., Parcel No., City, State, Zip, Country |

### Search results grid

Grid element ID: `ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList` (inherited Accela layout -- the `PlaceHolderMain` ASP.NET control ID is the canonical Accela Citizen Access marker).

Columns: Date, Record Number, Record Type, Address, Project Name, Status, Description.

Pagination: "Showing X-Y of Z" with Next/Prev `__doPostBack` postbacks. The base adapter handles pagination and uses binary date-range splitting when result count >= 100.

---

## 4. Detail page pattern

Detail page URL template:

```
https://aca-prod.accela.com/BOCC/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID1=...&capID2=...&capID3=...&agencyCode=BOCC
```

`agencyCode=BOCC` must be passed verbatim; re-using Polk's `POLKCO` or Citrus's `CITRUS` against this portal returns an error shell.

Standard Accela detail-page fields:

### Header
| Field | Notes |
|-------|-------|
| Record Number | Brevard-issued permit number |
| Record Type / Permit Type | e.g. Residential New Permit |
| Record Status | Applied, Issued, Inspections, Closed-Complete, etc. |

### Work Location / Parcel
| Field | Notes |
|-------|-------|
| Address | Full street, city, state, zip |
| Parcel Number | Links to Property Appraiser side (see `brevard-county-arcgis.md`) |

### Applicant / Licensed Professional / Owner / Project Description / Application Information / Fees / Inspections / Attachments / Processing Status / Related Records
All sections follow the standard Accela Citizen Access layout. Refer to `polk-county-accela.md` §4-§10 for per-section field inventories -- the Brevard portal renders the same sections through the same generic adapter.

---

## 5. Adapter

**No Brevard-specific adapter exists.** `modules/permits/scrapers/adapters/` does NOT contain `brevard_county.py`, `brevard.py`, or `bocc.py`. The generic `AccelaCitizenAccessAdapter` in `accela_citizen_access.py` is the base that a future Brevard adapter would subclass, following the same pattern as `citrus_county.py`:

```python
class BrevardCountyAdapter(AccelaCitizenAccessAdapter):
    slug = "brevard-county"
    display_name = "Brevard County"
    agency_code = "BOCC"            # NOT "BREVARD" or "BCC"
    module_name = "Building"
    target_record_type = "Building/Residential/New/NA"   # to be confirmed against live dropdown
```

Until such a subclass is committed, Brevard permits are not scraped by this repo.

---

## 6. Diff vs Polk / Citrus / Charlotte (Accela peers)

| Attribute | Brevard | Polk | Citrus | Charlotte |
|-----------|---------|------|--------|-----------|
| Agency code | **`BOCC`** (NOT Brevard) | `POLKCO` | `CITRUS` | `BOCC` -- wait, no. Charlotte uses `CHARLOTTE` |
| Actual agency code | `BOCC` | `POLKCO` | `CITRUS` | `CHARLOTTE` |
| Portal URL | `aca-prod.accela.com/BOCC/` | `aca-prod.accela.com/POLKCO/` | `aca-prod.accela.com/CITRUS/` | `aca-prod.accela.com/CHARLOTTE/` |
| County-specific adapter? | **NO** | YES (`polk_county.py`) | YES (`citrus_county.py`) | YES (`charlotte_county.py`) |
| Pre-migration platform | (unknown) | Hansen (legacy `%` prefix) | JSF-Primefaces (2025) | -- |
| Registry PT entry | **ABSENT** | present | present | present |
| Aliasing risk | **Escambia (MGO Connect) confusion** | -- | -- | -- |

---

## 7. REST API

Brevard's ACA portal is eligible for Accela's `/v4/*` REST API (registered Citizen App required). See `polk-county-accela.md` §11 for the full REST endpoint inventory and registration procedure. No attempt is made here to invent Brevard-specific REST behavior -- the API shape is identical across ACA tenants; only the `x-accela-agency: BOCC` header value differs.

---

## 8. Related surfaces (no standalone doc)

- **CD2 (clerk deeds)**: Covered inline in `brevard-county-arcgis.md` §Related surfaces / here. No Brevard clerk-deed API map doc is produced.
- **BI (parcels)**: See `brevard-county-arcgis.md` for the parcels surface (State Plane, EPSG:2881).
- **CR (commission)**: See `brevard-county-legistar.md` for BCC + P&Z; BOA is `manual` and documented in the Legistar doc.

---

## 9. Known Limitations and Quirks

1. **Agency code `BOCC` = Brevard, NOT Escambia.** This is the most common point of confusion in this repo. `escambia-county-mgo-connect.md` captures the research trail -- when researching Escambia permits, do NOT look up `aca-prod.accela.com/BOCC`. Escambia runs on MGO Connect. Brevard is the `BOCC` tenant.

2. **No Brevard-specific adapter.** `modules/permits/scrapers/adapters/` does not contain a Brevard permits adapter. The generic `AccelaCitizenAccessAdapter` is the base; a future subclass would follow the Citrus / Polk shape.

3. **Brevard is absent from `county-registry.yaml`.** No `brevard-fl` block exists. BI is registered only via `seed_bi_county_config.py` (see `brevard-county-arcgis.md`); PT has no registry presence at all. Before running any permits seeder, a `brevard-fl.projects.pt` entry must be authored.

4. **`PlaceHolderMain` is the canonical Accela Citizen Access marker.** The ASP.NET `ctl00$PlaceHolderMain` control ID wraps the main content area on every ACA page (Default.aspx, CapHome.aspx, CapDetail.aspx, Report pages). Finding `PlaceHolderMain` in the HTML is a high-confidence signal that the page is Accela Citizen Access and not a custom portal. Literal token retained.

5. **`agencyCode=BOCC` must be passed on detail URLs.** Omitting it (or substituting `POLKCO` / `CITRUS` from peer doc examples) returns a generic error shell. The agency code is the tenant key.

6. **Brevard issues permits through Brevard County Building Department under the BOCC agency** -- this is the county-wide tenant. Incorporated municipalities (Melbourne, Palm Bay, Titusville, etc.) issue their own permits through separate platforms and are not captured here.

7. **Detail page requires valid `capID1` / `capID2` / `capID3` tuple.** Accela's three-part capID is sequential; invalid tuples return a generic error page rather than a 404.

8. **Pagination via `__doPostBack` + ViewState.** Any scraper must maintain a session, replay `__VIEWSTATE` on each page request, and handle ~100 KB-sized viewstate payloads.

9. **Binary date-range splitting is required when results >= 100.** Accela's search result grid caps at 100 per query; wider ranges must recursively bisect. The generic adapter already implements this.

10. **No inline inspections / fees / documents in search results.** Those live on CapDetail.aspx or (preferably) `/v4/records/{id}/inspections`, `/fees`, `/documents` REST endpoints -- none of which are currently queried by this repo.

11. **Peer Escambia cross-reference is mandatory.** `escambia-county-mgo-connect.md` §8 Quirk 5 ("Agency code `BOCC` on Accela is Brevard, not Escambia. A common research mistake is to look up Escambia on `aca-prod.accela.com`. There is an agency code `BOCC` on Accela, but it belongs to Brevard County. Escambia does NOT run on Accela.") is canonical. This Brevard doc exists partly to resolve the other side of that citation.

12. **`aca-prod.accela.com/BOCC/Handlers/CustomizedCssStyle.ashx?agencyCode=BOCC` is the tenant's customization endpoint.** Confirms the `BOCC` tenant code during a probe. The customization path `/BOCC/Customization/BOCC/` nests `BOCC` twice -- that is the standard ACA layout (the outer `BOCC` is the URL base, the inner `BOCC` is the customization subdirectory name).

**Source of truth:** `docs/api-maps/escambia-county-mgo-connect.md` (§1 `Legacy portal URL`, §2 `county-registry.yaml` notes block, §8 Quirk 5 on `BOCC = Brevard`, confirming the cross-county naming collision), `modules/permits/scrapers/adapters/accela_citizen_access.py` (base adapter; confirmed absence of a Brevard subclass), confirmed absence of a `brevard-fl` block in `county-registry.yaml`, live probes against `https://aca-prod.accela.com/BOCC/Default.aspx` (HTTP 200, ~73.4 KB) and `https://aca-prod.accela.com/BOCC/Cap/CapHome.aspx?module=Building` (HTTP 200, ~258.3 KB), both 2026-04-14.
