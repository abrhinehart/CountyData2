# Escambia County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://escambiacofl.portal.civicclerk.com` |
| CivicClerk subdomain | `escambiacofl` |
| Protocol | CivicClerk public web UI (React SPA); underlying REST to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | BCC and P&Z `live` / `usable_seed` on CivicClerk; BOA is `manual` (not on CivicClerk) |

### Probe (2026-04-14)

```
GET https://escambiacofl.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML with React app mount points
```

Standard CivicClerk SPA shell. All meaningful data is loaded via client-side XHR to CivicClerk REST endpoints.

---

## 2. Bodies / Categories

Escambia County has three bodies configured. Two are on CivicClerk; one (BOA) is manual.

| Slug | Body | `scraping.platform` | `category_id` |
|------|------|----------------------|---------------|
| `escambia-county-bcc` | Board of County Commissioners | **civicclerk** | **26** |
| `escambia-county-pz` | Escambia County Planning Board | **civicclerk** | **32** |
| `escambia-county-boa` | Board of Adjustment | **manual** (out of scope for this doc) | -- |

Both CivicClerk YAMLs share `base_url: https://escambiacofl.portal.civicclerk.com` and `civicclerk_subdomain: escambiacofl`.

### BOA is NOT on CivicClerk

`escambia-county-boa.yaml` sets `scraping.platform: manual` and does NOT have a `base_url`, `civicclerk_subdomain`, or `category_id`. The BOA's agendas and minutes are processed manually (presumably pulled from the county website or emailed to the research team). The scraper for BOA documents is out of scope for this doc.

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `escambia-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `ESCAMBIA COUNTY` | wide |
| `escambia-county-pz` | `PLANNING` | `ESCAMBIA COUNTY` | wide |
| `escambia-county-boa` (manual) | `ADJUSTMENT`, `APPEALS` | `ESCAMBIA COUNTY` | wide |

---

## 3. Events Endpoint

### Request (CivicClerk public REST)

```
GET https://escambiacofl.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq {category_id})&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

The exact path is portal-version-specific; the React bundle abstracts it. Inspect live XHRs if the scraper stops returning events.

### Query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq {category_id})`; optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

Page-through 100 events at a time. 0.5s inter-page delay recommended.

### Body iteration

Scraper iterates over category IDs `[26, 32]` for Escambia (BCC + P&Z). BOA (manual) is handled separately.

---

## 4. Event Fields

Typical CivicClerk event JSON fields (same as Citrus CivicClerk doc):

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | CivicClerk event ID |
| `startDate` | datetime | Meeting start (ISO 8601) |
| `endDate` | datetime | Meeting end |
| `title` | string | Meeting title |
| `location` | string | Room / venue |
| `categories` | array of int | Body / category IDs |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | Direct agenda PDF URL |
| `minutesPdfUrl` | string | Direct minutes PDF URL |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

---

## 5. What We Extract

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"{body_name} Agenda - {meeting_date}"` / `"{body_name} Minutes - {meeting_date}"` |
| `url` | `agendaPdfUrl` / `minutesPdfUrl` | Direct PDF download |
| `date_str` | `startDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `id` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` / `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |
| `filename` | Computed | `"Agenda_{date}_{id}.pdf"` |

---

## 6. Unused / Additional Endpoints

| Endpoint | What it returns | Used? |
|----------|-----------------|-------|
| `GET /api/v1/Events/{id}` | Full event detail (agenda items inline) | NO |
| `GET /api/v1/Events/{id}/Items` | Per-item agenda content | NO |
| `GET /api/v1/Categories` | List of category IDs with display names | NO (IDs hardcoded per body) |
| `GET /api/v1/Bodies` | Body roster | NO |
| `GET /api/v1/Documents/{id}` | Document metadata | NO |
| Video / streaming endpoints | Meeting video | NO |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Event ID | YES | `id` | -- | -- |
| Meeting Date | YES | `startDate` (first 10 chars) | Full datetime, meeting end | `startDate`, `endDate` |
| Body | YES | category lookup | Body ID list | `categories[]` |
| Agenda PDF URL | YES | `agendaPdfUrl` | -- | -- |
| Minutes PDF URL | YES | `minutesPdfUrl` | -- | -- |
| Meeting title | NO | -- | `title` | Event JSON |
| Location | NO | -- | Room / venue | `location` |
| Video | NO | -- | Meeting video when posted | `videoUrl` |
| Published flag | NO | -- | `isPublished` | Event JSON |
| Individual agenda items | NO | -- | Per-item action text | `/api/v1/Events/{id}/Items` |
| BOA events | NO (out of scope for this doc) | -- | Manually processed | `escambia-county-boa.yaml` (`manual`) |

---

## 8. Known Limitations and Quirks

1. **Subdomain is `escambiacofl`.** Per YAML: `civicclerk_subdomain: escambiacofl`. Any attempt to hit `escambia.portal.civicclerk.com` or `escambiafl.portal.civicclerk.com` will fail with DNS or 404. The canonical subdomain is `escambiacofl`.

2. **Category IDs: BCC=26, P&Z=32.** Note P&Z is `32` for Escambia (vs `33` for Citrus). Numeric category IDs are per-tenant and not portable.

3. **BOA is NOT on CivicClerk.** `escambia-county-boa.yaml` uses `platform: manual` and does not include a CivicClerk base URL. The BOA's documents must be processed through a manual workflow; any scraper targeting Escambia BOA must NOT assume CivicClerk access.

4. **P&Z is labeled "Planning Board" in YAML name.** The slug is `escambia-county-pz` but the human-readable `name` field in the YAML is `"Escambia County Planning Board"`. Downstream display should use the YAML `name`, not the slug.

5. **Document format is PDF.** Per `document_formats: [pdf]` in both CivicClerk YAMLs.

6. **`has_duplicate_page_bug: false`** for both BCC and P&Z -- pagination is reliable on this CivicClerk tenant.

7. **No keyword list.** Neither YAML defines a `keywords` list; downstream keyword routing uses `_florida-defaults.yaml`.

8. **Header zone is `wide`** for all three Escambia bodies -- the header-keyword matcher scans the entire page header area.

9. **React SPA; XHR schema may change.** The probed response is a ~1.1 KB SPA shell. If event data stops returning, re-inspect `escambiacofl.portal.civicclerk.com` XHRs in a browser to find the current `api/v1` path and parameters.

10. **BCC status `live`, P&Z status `usable_seed`.** Per `county-registry.yaml` (`escambia-fl.projects.cr`): the BCC is fully validated; P&Z is `usable_seed` (scraper configured but not yet validated against a full event sweep). Re-run validation when meaningful P&Z events are expected.

**Source of truth:** `modules/commission/config/jurisdictions/FL/escambia-county-bcc.yaml`, `escambia-county-pz.yaml`, `escambia-county-boa.yaml` (manual), `county-registry.yaml` (`escambia-fl.projects.cr`), live probe against `https://escambiacofl.portal.civicclerk.com/web/home`
