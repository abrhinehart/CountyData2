# Pasco County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus agenda management) |
| Tenant subdomain | `pascocofl` |
| Portal URL | `https://pascocofl.portal.civicclerk.com` |
| API base | `https://pascocofl.portal.civicclerk.com/api/v1/Meetings` (standard CivicClerk shape) |
| Auth | Anonymous |
| Protocol | JSON REST over HTTPS; PDF downloads via Azure Blob Storage SAS-signed URLs |
| Adapter | `civicclerk` platform (shared with Escambia / Charlotte / Citrus / Collier / Lee / Saint Lucie / Santa Rosa-adjacent) |
| Download storage | Azure Blob: `https://civicclerk.blob.core.windows.net/stream/pascocofl/{guid}...pdf?<SAS params>` (7-day expiry) |
| Registry status | `cr: live` (per `county-registry.yaml` entry — BCC validated) |

### Configured bodies (CountyData2)

| Slug | Body | `category_id` | `scraping.platform` |
|------|------|---------------|---------------------|
| `pasco-county-bcc` | Pasco County BCC | **26** | `civicclerk` |
| `pasco-county-pz` | Pasco County Planning Commission | **27** | `civicclerk` |
| `pasco-county-boa` | Pasco County BOA | -- | `manual` (same base_url) |

Both BCC and Planning Commission ride the same CivicClerk tenant (`pascocofl`), disambiguated only by `category_id`.

## 2. Probe (2026-04-14)

```
GET https://pascocofl.portal.civicclerk.com/
-> HTTP 200, 1,112 bytes, text/html
   React SPA shell for CivicClerk events and agendas.

GET https://pascocofl.portal.civicclerk.com/events?category=26
-> HTTP 200 (React SPA HTML; events load via client-side fetch of
   /api/v1/Meetings?categoryId=26 — not probed directly here)
```

**Prior live validation (2026-04-14, per `docs/commission/live-validation/pasco-county-bcc.md`):**

- Listings returned: 15 (11 agendas + 4 minutes)
- Date window: 2025-10-01 → 2026-04-14 (6 months)
- First 3 listings:
  1. `3-10-26 FINAL Agenda` — 2026-03-10 — agenda (pdf)
  2. `2-17-26 FINAL Agenda` — 2026-02-17 — agenda (pdf)
  3. `BCC AA 02-17-2026 REVISED` — 2026-02-17 — minutes (pdf)
- **Download smoke:** Azure Blob signed URL at `https://civicclerk.blob.core.windows.net/stream/pascocofl/45176558-....pdf?<SAS params>`, 269,741 bytes, magic bytes `%PDF-1.7`.

## 3. Query Capabilities

Standard CivicClerk API contract (shared with all CivicClerk tenants):

### Request: listings

```
GET https://pascocofl.portal.civicclerk.com/api/v1/Meetings
Query params:
  $filter: eventDate gt {ISO start} and eventDate lt {ISO end} and categoryId eq {26|27}
  $orderby: eventDate desc
  $top: {page size}
  $skip: {offset}
```

### Request: detail / documents

Per-meeting detail endpoints expose the agenda PDF (and minutes if published). PDF URLs redirect to Azure Blob SAS URLs; the scraper issues fresh GETs each run (no caching of the SAS URL, since the signature expires).

### Pagination

Standard `$top` / `$skip` OData-style; 25-100 per page typical.

### Date-range semantics

`eventDate` on meeting objects; filter is inclusive of the date range. CommissionRadar's cr_live_validate harness uses `gt` / `lt` inclusive ends.

## 4. Field Inventory (per-meeting)

Per the CivicClerk contract (observed on Escambia / Charlotte / validated on Pasco):

| Field | Type | Notes |
|-------|------|-------|
| id | GUID | Meeting ID |
| categoryId | int | **26 = BCC, 27 = Planning Commission for Pasco** |
| eventDate | ISO datetime | |
| title | string | e.g. `"3-10-26 FINAL Agenda"`, `"BCC AA 02-17-2026 REVISED"` |
| category | object | `{ id: 26, name: "BCC", ...}` |
| documents | array | [{ type: "Agenda"|"Minutes", url: "<signed Azure Blob URL>", ... }] |
| publishedAgendaTimestamp | datetime/null | |
| publishedMinutesTimestamp | datetime/null | |

## 5. What We Extract / What a Future Adapter Would Capture

| DocumentListing field | Source |
|-----------------------|--------|
| `title` | Meeting `title` (e.g. `"3-10-26 FINAL Agenda"`) |
| `url` | Azure Blob SAS-signed URL |
| `date_str` | `eventDate[0:10]` |
| `document_id` | Composite `"{categoryId}-{meetingId}-{docType}"` |
| `document_type` | `"agenda"` or `"minutes"` |
| `file_format` | `"pdf"` |
| `filename` | Synthesized, e.g. `"BCC_Agenda_2026-03-10.pdf"` |

## 6. Auth / Bypass

Anonymous — no API key, login, or captcha. React SPA + CivicClerk JSON API over HTTPS. Standard `User-Agent` suffices.

**Azure Blob SAS signatures expire in 7 days.** The scraper must not cache the URL — always re-fetch the detail payload to get a fresh SAS URL.

## 7. What We Extract vs What's Available

| Data Category | Extracted | Source | Not Extracted |
|---------------|-----------|--------|---------------|
| Meeting ID / GUID | YES | `id` | -- |
| Meeting date | YES | `eventDate` | |
| Title | YES | `title` | |
| Agenda PDF | YES | documents[type=Agenda].url | |
| Minutes PDF | YES | documents[type=Minutes].url | |
| Category ID / name | YES (filter key) | `categoryId`, `category.name` | Broader category metadata |
| Publish timestamps | NO | -- | publishedAgendaTimestamp, publishedMinutesTimestamp |
| Agenda items / votes | NO | -- | Individual item breakdowns (if CivicClerk exposes; not used) |
| Attachments | NO | -- | Supplemental files on detail page |
| Video | NO | -- | If CivicClerk links to Granicus / YouTube, not captured |

## 8. Known Limitations and Quirks

1. **Two bodies on one CivicClerk tenant, disambiguated by `category_id`.** BCC = 26, Planning Commission = 27. The same pascocofl tenant serves both; only the category filter differs.
2. **BOA shares base_url but is `platform: manual`.** `pasco-county-boa.yaml` still points `base_url` at `pascocofl.portal.civicclerk.com`, but `scraping.platform: manual` means the scraper skips automated fetch — BOA documents are staged by hand.
3. **Azure Blob SAS expiry = 7 days.** Any URL captured for historical reference becomes a 404 after a week. The scraper re-resolves URLs on each run; downstream archival must fetch the PDF itself within the 7-day window.
4. **`publishedMinutesTimestamp: null` is normal for recent meetings.** Minutes lag the meeting by 2-6 weeks while drafts circulate. The 15-listing sample (2025-10-01 → 2026-04-14) had 11 agendas + 4 minutes, reflecting this lag.
5. **Title strings are mixed-format.** Observed examples: `"3-10-26 FINAL Agenda"` (date prefix), `"BCC AA 02-17-2026 REVISED"` (body prefix). Downstream normalization relies on filename-prefix date parsing plus `eventDate` as the authoritative date.
6. **CivicClerk React SPA shell at `/events?category=26`** renders client-side; anonymous scraping of the HTML alone yields no event data. API is at `/api/v1/Meetings`.
7. **Download smoke verified 2026-04-14.** PDF returned 269,741 bytes with magic bytes `%PDF-1.7`, confirming full extraction flow works on Pasco.
8. **Second CivicClerk validation on the same tenant.** Per `docs/commission/live-validation/pasco-county-bcc.md`: "confirms BCC lives on the same tenant as the already-validated Pasco PZ (category_id=26 for BCC vs different id for PZ)." That makes Pasco the canonical test case for multi-body-single-tenant CivicClerk pattern.
9. **Cadence:** 11 agendas in 6 months matches expected BCC cadence of ~2/month.
10. **Recently added to `county-registry.yaml` as live after initial validation.** The registry now reflects current known-good state; do not re-run discovery unless a status regression is observed.
11. **`has_duplicate_page_bug: false`** in all three YAMLs — Pasco's CivicClerk tenant does not exhibit the duplicated-listing bug seen on some CivicClerk deployments.

Source of truth: `county-registry.yaml` (`pasco-fl.projects.cr` block), `modules/commission/config/jurisdictions/FL/pasco-county-bcc.yaml` (category_id=26), `modules/commission/config/jurisdictions/FL/pasco-county-pz.yaml` (category_id=27), `modules/commission/config/jurisdictions/FL/pasco-county-boa.yaml` (platform=manual, shared base_url), `docs/commission/live-validation/pasco-county-bcc.md` (validation record, 15 listings, download smoke confirmed 269,741 bytes), live probe of `https://pascocofl.portal.civicclerk.com/` (2026-04-14, HTTP 200).
