# Lee County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://leecofl.portal.civicclerk.com` |
| CivicClerk subdomain | `leecofl` (exact) |
| Protocol | CivicClerk public web UI (React SPA); underlying REST calls to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | `bi: active` is the only registry slot Lee has; CR is NOT in `county-registry.yaml` -- YAML-only |
| Bodies configured | 3 (BCC, BOA, P&Z); **only BCC is auto-scraped** (BOA + P&Z are `platform: manual`) |

### Probe (2026-04-14)

```
GET https://leecofl.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML
(standard CivicClerk React SPA)
```

---

## 2. Bodies / Categories

Lee County has three bodies configured under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `scraping.platform` | `category_id` | Portal |
|------|------|-------------------|---------------------|---------------|--------|
| `lee-county-bcc` | Board of County Commissioners | `bcc` | **`civicclerk`** | **26** | `leecofl.portal.civicclerk.com` |
| `lee-county-boa` | Board of Adjustment | `board_of_adjustment` | **`manual`** | n/a | (hosted on separate `leegov.com` platform) |
| `lee-county-pz` | Planning & Zoning | `planning_board` | **`manual`** | n/a | (hosted on separate `leegov.com` platform) |

**Only BCC is on CivicClerk.** BOA and P&Z both have `platform: manual` -- their agendas are hosted on a different `leegov.com`-based infrastructure, and the YAMLs' `extraction_notes` explicitly state: "documents must be uploaded manually (hosted on separate leegov.com platform)."

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `lee-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `LEE COUNTY` | wide |
| `lee-county-boa` | `ADJUSTMENT`, `APPEALS` | `LEE COUNTY` | wide |
| `lee-county-pz` | `PLANNING` | `LEE COUNTY` | wide |

---

## 3. Events Endpoint (BCC only)

### Request (CivicClerk public REST)

```
GET https://leecofl.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq 26)&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

The scraper iterates ONLY `category_id=26` (BCC). BOA and P&Z are skipped by the platform-dispatch layer because their `scraping.platform` is `manual`.

### OData-style query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq 26)` plus optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

100 events per page. Per YAML, `has_duplicate_page_bug: false` -- the CivicClerk pagination is considered reliable for `leecofl`.

---

## 4. Event Fields

Standard CivicClerk event JSON (same shape as Citrus / Collier / Escambia):

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Event ID |
| `startDate` | datetime | Meeting start (ISO 8601) |
| `endDate` | datetime | Meeting end |
| `title` | string | Meeting title |
| `location` | string | Meeting location |
| `categories` | array of integer | Body / category IDs (26 = BCC) |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | URL to agenda PDF when published |
| `minutesPdfUrl` | string | URL to minutes PDF when published |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

---

## 5. What We Extract (BCC only)

Each event -> 0, 1, or 2 `DocumentListing` records (agenda + minutes):

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Board of County Commissioners Agenda - {meeting_date}"` or `"... Minutes - ..."` |
| `url` | `agendaPdfUrl` / `minutesPdfUrl` | Direct PDF download |
| `date_str` | `startDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `id` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

BOA and P&Z events are NOT fetched programmatically. Their documents must be uploaded manually.

---

## 6. Diff vs Collier (4-body CivicClerk) + Citrus (3-body all-auto)

| Attribute | Lee | Collier | Citrus |
|-----------|-----|---------|--------|
| CivicClerk subdomain | `leecofl` | `colliercofl` | `citrusclerk` |
| Bodies (YAMLs) | 3 (BCC, BOA, P&Z) | 4 (BCC, BOA, CCPC, HEX) | 3 (BCC, P&Z, BOA) |
| Bodies auto-scraped | **1 (BCC only)** | 4 (all on CivicClerk) | 3 (all on CivicClerk) |
| BCC `category_id` | **26** | 26 | 26 |
| Mixed-platform bodies | YES (BOA/P&Z `platform: manual`) | NO | NO |
| Registry CR status | **ABSENT** (YAML-only) | `usable_seed` (but notes `legistar` -- YAML wins; see `collier-county-civicclerk.md`) | `live` |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Notes |
|---------------|--------------------|-------|
| BCC Event ID | YES | via `/api/v1/Events?$filter=categories/any(c: c eq 26)` |
| BCC Meeting Date | YES | `startDate` (first 10 chars) |
| BCC Agenda PDF URL | YES | `agendaPdfUrl` |
| BCC Minutes PDF URL | YES | `minutesPdfUrl` |
| BCC Meeting Title / Location / Video | NO | -- |
| BCC individual agenda items / votes | NO | `/api/v1/Events/{id}/Items` not called |
| BOA Events | NO | `platform: manual` -- hosted on `leegov.com` |
| P&Z Events | NO | `platform: manual` -- hosted on `leegov.com` |

---

## 8. Known Limitations and Quirks

1. **Only BCC is auto-scraped; BOA and P&Z are `platform: manual`.** Unlike Collier (all 4 bodies on CivicClerk) or Citrus (all 3 bodies on CivicClerk), Lee BOA and P&Z are hosted on a separate `leegov.com`-adjacent platform and must be uploaded manually. The YAML `extraction_notes` explicitly say: "documents must be uploaded manually (hosted on separate leegov.com platform)."

2. **Subdomain is `leecofl`, not `leefl`, `leecountyfl`, or `lee-fl`.** Copy verbatim from the YAML: `civicclerk_subdomain: "leecofl"`.

3. **`category_id: 26` for BCC.** Same numeric ID as Citrus BCC (26) and Collier BCC (26). Per-tenant IDs -- do NOT assume transferability beyond BCC.

4. **Registry CR absence.** Lee has `bi: active` in `county-registry.yaml` (L444-451) but NO `cr:` slot. The CR surface lives in jurisdiction YAMLs alone.

5. **BOA + P&Z YAMLs exist but are flagged manual.** `lee-county-boa.yaml` and `lee-county-pz.yaml` under `modules/commission/config/jurisdictions/FL/` both set `scraping.platform: manual` and omit `base_url` / `civicclerk_subdomain` / `category_id`. The dispatch layer routes them to the manual workflow.

6. **Lee PA hosts the BI surface separately (`leepa.org`).** See `lee-county-arcgis.md`. BI and CR live on completely different infrastructures.

7. **`has_duplicate_page_bug: false` for the BCC YAML.** Pagination is considered reliable for `leecofl`.

8. **No `keywords` list in the YAMLs.** The BCC YAML relies on the Florida defaults in `_florida-defaults.yaml` for keyword-based item routing.

9. **Header zone `wide` for all three bodies.** Same pattern as Citrus.

10. **Extraction note "Generic Florida county. Flag sparse items for review." appears on all three YAMLs.** A boilerplate line used across multiple FL counties in this repo.

11. **`commission_type` for Lee P&Z is `planning_board`** (matches the FL taxonomy used across Citrus, Collier CCPC, etc.).

12. **"County body -- cannot annex." inline comment in `lee-county-bcc.yaml`.** A standard BCC-only note indicating the BCC cannot take annexation actions (which flow through municipalities).

**Source of truth:** `modules/commission/config/jurisdictions/FL/lee-county-bcc.yaml`, `lee-county-boa.yaml`, `lee-county-pz.yaml`, `county-registry.yaml` (`lee-fl.projects.bi`, L444-451 -- CR slot absent), live probe against `https://leecofl.portal.civicclerk.com/web/home` (HTTP 200, 1.1 KB SPA shell, 2026-04-14)
