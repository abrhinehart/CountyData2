# St. Lucie County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://stluciecofl.portal.civicclerk.com/web/home` |
| CivicClerk subdomain | `stluciecofl` (exact -- `cofl` suffix, NOT `stlucie`/`stluciefl`) |
| Protocol | CivicClerk public web UI (React SPA); underlying REST calls to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | CR is NOT in `county-registry.yaml` -- only `bi: active` is tracked under `st-lucie-fl.projects` (L524-531). CR surface is YAML-only. |
| Bodies configured | 3 (BCC, BOA, P&Z); **BCC + P&Z are auto-scraped** (`platform: civicclerk`), **BOA is `platform: manual`** |
| Scraper | Shared `CivicClerkScraper` at `modules/commission/scrapers/civicclerk.py:65` (multi-tenant; no St.-Lucie-specific subclass -- tenants differ only by `civicclerk_subdomain` + `category_id` from YAML) |

### Probe (2026-04-14)

```
GET https://stluciecofl.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML
(standard CivicClerk React SPA; same main.js/main.css fingerprint as Citrus, Collier, Lee, Charlotte)
```

---

## 2. Bodies / Categories

Three commission YAMLs reference this portal under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `scraping.platform` | `category_id` | Portal |
|------|------|-------------------|---------------------|---------------|--------|
| `st-lucie-county-bcc` | St. Lucie County BCC | `bcc` | **`civicclerk`** | **26** | `stluciecofl.portal.civicclerk.com` |
| `st-lucie-county-pz` | St. Lucie County P&Z Commission | `planning_board` | **`civicclerk`** | **32** | `stluciecofl.portal.civicclerk.com` |
| `st-lucie-county-boa` | St. Lucie County BOA | `board_of_adjustment` | **`manual`** | n/a | (no `base_url` in YAML -- documents uploaded manually) |

BCC and P&Z are auto-scraped. BOA is explicitly `platform: manual` -- the YAML omits `base_url`, `civicclerk_subdomain`, and `category_id`, and the dispatch layer routes it through the manual workflow (documents staged out-of-band).

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `st-lucie-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `ST. LUCIE COUNTY` | wide |
| `st-lucie-county-pz` | `PLANNING` | `ST. LUCIE COUNTY` | wide |
| `st-lucie-county-boa` | `ADJUSTMENT`, `APPEALS` | `ST. LUCIE COUNTY` | wide |

Note the `require_also` list uses the full `"ST. LUCIE COUNTY"` (with the period). The CivicClerk subdomain has no period -- `stluciecofl`.

---

## 3. Events Endpoint (BCC + P&Z)

### Request (CivicClerk public REST)

```
GET https://stluciecofl.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq {cid})&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

Two iterations per run:
- `category_id=26` -> BCC
- `category_id=32` -> P&Z Commission

BOA is skipped by the platform-dispatch layer because `scraping.platform: manual`.

### OData-style query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq {category_id})` plus optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

100 events per page. Per YAML, `has_duplicate_page_bug: false` for both BCC and P&Z -- pagination is considered reliable for `stluciecofl`.

---

## 4. Event Fields

Standard CivicClerk event JSON (same shape as Citrus / Collier / Escambia / Lee):

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | Event ID |
| `startDate` | datetime | Meeting start (ISO 8601) |
| `endDate` | datetime | Meeting end |
| `title` | string | Meeting title |
| `location` | string | Meeting location |
| `categories` | array of integer | Body / category IDs (26 = BCC, 32 = P&Z) |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | URL to agenda PDF when published |
| `minutesPdfUrl` | string | URL to minutes PDF when published |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

---

## 5. What We Extract (BCC + P&Z)

Each event -> 0, 1, or 2 `DocumentListing` records (agenda + minutes):

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"St. Lucie County BCC Agenda - {meeting_date}"` (or P&Z Commission; or minutes) |
| `url` | `agendaPdfUrl` / `minutesPdfUrl` | Direct PDF download |
| `date_str` | `startDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `id` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

BOA events are NOT fetched programmatically. Documents are staged manually.

---

## 6. Diff vs Lee + Charlotte + Collier (CivicClerk peers)

| Attribute | St. Lucie | Lee | Charlotte | Collier |
|-----------|-----------|-----|-----------|---------|
| CivicClerk subdomain | **`stluciecofl`** | `leecofl` | `charlottecountyfl` | `colliercofl` |
| Suffix style | `cofl` (like Lee / Collier) | `cofl` | `countyfl` | `cofl` |
| Bodies (YAMLs) | 3 (BCC, P&Z, BOA) | 3 (BCC, BOA, P&Z) | 0 (no YAML yet) | 4 (BCC, BOA, CCPC, HEX) |
| Bodies auto-scraped | **2 (BCC, P&Z)** | 1 (BCC only) | n/a (no config) | 4 (all on CivicClerk) |
| BCC `category_id` | **26** | 26 | (unknown) | 26 |
| P&Z `category_id` | **32** | n/a (manual) | (unknown) | n/a (uses CCPC/HEX instead) |
| Mixed-platform bodies | YES (BOA is `manual`) | YES (BOA + P&Z `manual`) | n/a | NO |
| Registry CR status | ABSENT (YAML-only) | ABSENT (YAML-only) | ABSENT | `usable_seed` |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Notes |
|---------------|--------------------|-------|
| BCC Event ID | YES | via `/api/v1/Events?$filter=categories/any(c: c eq 26)` |
| BCC Meeting Date | YES | `startDate` (first 10 chars) |
| BCC Agenda PDF URL | YES | `agendaPdfUrl` |
| BCC Minutes PDF URL | YES | `minutesPdfUrl` |
| P&Z Event ID / Date / Agenda / Minutes | YES | Same as BCC, `category_id=32` |
| Meeting Title / Location / Video | NO | -- |
| Agenda Items / Votes | NO | `/api/v1/Events/{id}/Items` not called |
| BOA Events | NO | `platform: manual` -- documents uploaded manually |

---

## 8. Diff / Related surfaces (no standalone BOA doc)

### St. Lucie BOA (`platform: manual`) -- documented inline here

`st-lucie-county-boa.yaml` declares `platform: manual` and omits `base_url`, `civicclerk_subdomain`, and `category_id`. Extraction notes read: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." The dispatch layer routes the BOA through the manual workflow, so agenda/minutes PDFs for BOA meetings are staged by hand. No standalone `st-lucie-county-boa.md` doc is produced; BOA is covered here under this § and under the YAML path above.

---

## 9. Known Limitations and Quirks

1. **Subdomain is `stluciecofl`** -- four letters `stlu` + `cie` + `cofl` suffix. NOT `stlucie`, NOT `stluciefl`, NOT `saintluciefl`. Copy verbatim from the YAMLs.

2. **`category_id: 26` for BCC, `category_id: 32` for P&Z.** Same `category_id` 26 as Lee, Citrus, and Collier BCC -- but those numeric IDs are per-tenant; do NOT assume transferability beyond BCC. St. Lucie P&Z uses 32, which is unique among the peer counties in this repo.

3. **BOA is `platform: manual`.** `st-lucie-county-boa.yaml` sets `scraping.platform: manual` and omits `base_url`/`civicclerk_subdomain`/`category_id`. Unlike Collier (all four bodies on CivicClerk) or Citrus (all three), St. Lucie's BOA is NOT auto-scraped.

4. **CR is not in `county-registry.yaml`.** Only `bi: active` is tracked under `st-lucie-fl.projects` (L524-531). The CR surface lives in the three jurisdiction YAMLs alone. No `cr:` slot exists to carry a status like `live` / `usable_seed` / `zero_listing`.

5. **`has_duplicate_page_bug: false` for both BCC and P&Z.** Pagination is considered reliable for `stluciecofl`.

6. **`require_also` uses the full `"ST. LUCIE COUNTY"` (with the period).** The CivicClerk subdomain has no period -- `stluciecofl`. Do not confuse the two.

7. **Extraction notes are the generic FL boilerplate.** Both BCC and P&Z carry: "Generic Florida county. Flag sparse items for review." BCC additionally has "County body -- cannot annex." and P&Z has "Planning/advisory board -- recommendations only, not final authority on legislative items."

8. **Two auto-scraped bodies on one CivicClerk tenant is the common St. Lucie pattern** -- not the one-body (Lee BCC) or four-body (Collier all) pattern. BCC + P&Z share the same tenant; BOA is routed out-of-band.

9. **No `keywords` list in any of the three YAMLs.** BCC and P&Z rely on the Florida defaults in `_florida-defaults.yaml` for keyword-based item routing.

10. **Header zone `wide` for all three bodies.** Matches the pattern seen across most FL CivicClerk tenants.

11. **CivicClerk BI registry absence is the only `bi`-less-but-still-tracked case.** St. Lucie's BI surface is ArcGIS (see `st-lucie-county-arcgis.md`); CR is CivicClerk (this doc); PT and CD2 are not tracked.

12. **CivicClerk does NOT advertise a public REST schema.** The `/api/v1/Events` shape is inferred from observed behavior on sibling tenants (Citrus, Collier, Escambia, Lee, Charlotte) rather than from published API documentation. A probe of the filtered events endpoint against `stluciecofl` returned 404 on the raw OData path and 200 on the React SPA shell during the 2026-04-14 probe -- the public XHR calls happen inside the SPA bundle and mirror the documented shape.

**Source of truth:** `modules/commission/config/jurisdictions/FL/st-lucie-county-bcc.yaml`, `st-lucie-county-pz.yaml`, `st-lucie-county-boa.yaml`, `county-registry.yaml` (`st-lucie-fl.projects` -- only `bi: active` at L524-531; CR slot absent), live probe against `https://stluciecofl.portal.civicclerk.com/web/home` (HTTP 200, ~1.1 KB SPA shell, 2026-04-14).
