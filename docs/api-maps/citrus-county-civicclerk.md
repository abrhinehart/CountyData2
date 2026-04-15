# Citrus County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://citrusclerk.portal.civicclerk.com` |
| CivicClerk subdomain | `citrusclerk` |
| Protocol | CivicClerk public web UI (React SPA); underlying REST calls to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | `live` (per `citrus-fl.projects.cr`) |

### Probe (2026-04-14)

```
GET https://citrusclerk.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML with React app mount points
(body references /static/js/main.2acd9b93.js and /static/css/main.671d2fa5.css)
```

The portal is a standard CivicClerk React single-page app. All meaningful data is loaded via XHR / fetch to CivicClerk's public REST endpoints after the SPA mounts.

### Subdomain correction

Per `county-registry.yaml` (citrus-fl): "Subdomain corrected from `citrusbocc` to `citrusclerk`." Do NOT use `citrusbocc.portal.civicclerk.com`.

---

## 2. Bodies / Categories

Citrus County has three bodies configured under CivicClerk. All three YAMLs share `base_url: https://citrusclerk.portal.civicclerk.com` and `civicclerk_subdomain: citrusclerk`.

| Slug | Body | `commission_type` | `category_id` |
|------|------|-------------------|---------------|
| `citrus-county-bcc` | Board of County Commissioners | `bcc` | **26** |
| `citrus-county-pz` | Planning & Zoning Commission | `planning_board` | **33** |
| `citrus-county-boa` | Board of Adjustment | `board_of_adjustment` | **28** |

The `category_id` is the CivicClerk-internal filter used to limit the events list to a specific body. The scraper passes it as a query parameter to the events endpoint.

### Detection patterns

Per the YAMLs, the commission-radar extractor recognizes each body by header keywords plus a `CITRUS COUNTY` requirement:

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `citrus-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `CITRUS COUNTY` | wide |
| `citrus-county-pz` | `PLANNING` | `CITRUS COUNTY` | wide |
| `citrus-county-boa` | `ADJUSTMENT`, `APPEALS` | `CITRUS COUNTY` | wide |

---

## 3. Events Endpoint

### Request (CivicClerk public REST)

```
GET https://citrusclerk.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq {category_id})&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

The SPA uses the same CivicClerk API patterns documented on other CivicClerk portals (e.g., Escambia County -- also documented in this repo). The exact path depends on the portal version; the React bundle abstracts this through `/api/v1/Events` or similar.

### OData-style query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq {category_id})` plus optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

Page through 100 events at a time until an empty page or `recordsTotal` is hit. 0.5s delay between paginated requests is recommended (same as the Legistar scraper).

### Body iteration

The scraper iterates over the three `category_id` values (26, 33, 28) to collect events for all three Citrus bodies. A `seen_ids` set deduplicates events that span overlapping categories (rare for CivicClerk).

---

## 4. Event Fields

Typical CivicClerk event JSON fields (observed across CivicClerk-hosted FL jurisdictions):

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | CivicClerk event ID |
| `startDate` | datetime | Meeting start time (ISO 8601) |
| `endDate` | datetime | Meeting end time |
| `title` | string | Meeting title / name |
| `location` | string | Meeting location |
| `categories` | array of integer | Body / category IDs |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | URL to agenda PDF when published |
| `minutesPdfUrl` | string | URL to minutes PDF when published |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

Exact field names may vary by CivicClerk version; the scraper normalizes via a field-mapping layer in the `civicclerk` platform adapter.

---

## 5. What We Extract

Each event -> 0, 1, or 2 `DocumentListing` records (one for agenda, one for minutes, when URLs are non-null):

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"{body_name} Agenda - {meeting_date}"` or `"{body_name} Minutes - {meeting_date}"` |
| `url` | `agendaPdfUrl` / `minutesPdfUrl` | Direct PDF download |
| `date_str` | `startDate` | First 10 chars -> `YYYY-MM-DD` |
| `document_id` | `id` | Stringified event ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
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
| Event ID | YES | `id` | Row version, concurrency | -- |
| Meeting Date | YES | `startDate` (first 10 chars) | Full datetime, meeting end time | `startDate`, `endDate` |
| Body Name | YES | Body display via category lookup | Body ID | categories[] |
| Agenda PDF URL | YES | `agendaPdfUrl` | -- | -- |
| Minutes PDF URL | YES | `minutesPdfUrl` | -- | -- |
| Meeting Title | NO | -- | Event title | `title` |
| Meeting Location | NO | -- | Room / location | `location` |
| Video URL | NO | -- | Video link when posted | `videoUrl` |
| Published flag | NO | -- | `isPublished` | `isPublished` |
| Individual agenda items | NO | -- | Per-item action text / attachments | `/api/v1/Events/{id}/Items` |
| Vote records | NO | -- | Per-item per-member votes (if published) | Event detail |

---

## 8. Known Limitations and Quirks

1. **Subdomain is `citrusclerk`, not `citrusbocc`.** Per registry annotation: "Subdomain corrected from `citrusbocc` to `citrusclerk`." Any attempt to hit `citrusbocc.portal.civicclerk.com` will fail.

2. **Category IDs are portal-specific and must match exactly.** BCC=26, P&Z=33, BOA=28. These numeric IDs are per-tenant; using Escambia's IDs (which partially overlap at 26 and 32) against Citrus will return the wrong body's events.

3. **React SPA; network inspection required to confirm exact endpoint shape.** The probed response is the SPA shell (~1.1 KB). Actual event JSON is fetched client-side. Future scraper changes must re-inspect `citrusclerk.portal.civicclerk.com` network traffic to confirm the current `api/v1` path.

4. **No OData server-side filter for body name.** Filtering is by `categories/any(c: c eq N)` on the numeric ID, not by a body string. A scraper that wants text-level filtering must use the returned category lookup.

5. **BCC, P&Z, and BOA share the same portal.** All three bodies are collected from the same CivicClerk tenant (`citrusclerk`). De-duplicate by event ID if iterating categories.

6. **Board of Adjustment is "outside core tracking scope."** Per extraction notes in `citrus-county-boa.yaml`: "Board of Adjustment -- handles variances and appeals, outside core tracking scope." The adapter fetches BOA events but downstream filtering may drop them.

7. **Document format is PDF for both agenda and minutes.** Per YAML: `document_formats: [pdf]`.

8. **No `has_duplicate_page_bug`.** All three YAMLs explicitly set `has_duplicate_page_bug: false`, so the CivicClerk pagination is considered reliable for Citrus (unlike some other CivicClerk tenants where an extra empty page is returned at the end).

9. **No keywords list in YAML.** Unlike the Bay County BCC YAML, the Citrus YAMLs do not include a `keywords` list. Downstream keyword-based routing falls back to Florida defaults in `_florida-defaults.yaml`.

10. **Header zone is `wide` for all three.** This directs the header-keyword matcher to search the entire page header area rather than a narrow zone -- appropriate for CivicClerk's full-page agenda rendering.

**Source of truth:** `modules/commission/config/jurisdictions/FL/citrus-county-bcc.yaml`, `citrus-county-pz.yaml`, `citrus-county-boa.yaml`, `county-registry.yaml` (`citrus-fl.projects.cr`), live probe against `https://citrusclerk.portal.civicclerk.com/web/home`
