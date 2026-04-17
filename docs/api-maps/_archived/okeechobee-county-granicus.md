# Okeechobee County FL -- Granicus IQM2 API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Granicus IQM2 (Meeting Portal / Citizens) |
| Portal URL | `https://okeechobeecountyfl.iqm2.com/Citizens` |
| Protocol | Server-rendered ASP.NET (Meeting Portal HTML); Granicus JSON-ish federated search endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction config | `modules/commission/config/jurisdictions/FL/okeechobee-county-bcc.yaml` |
| Registry status | `pending_validation` (per `okeechobee-fl.projects.cr`) |
| Body configured | BCC only (no P&Z, BOA in `modules/commission/config/jurisdictions/FL/`) |

### Probe (2026-04-14)

```
GET https://okeechobeecountyfl.iqm2.com/Citizens
-> HTTP 301 (one redirect to /Citizens/)
-> HTTP 200, body 45,061 bytes

Body contains: <title>Meeting Portal - Okeechobee County, Florida</title>
               <link rel="search" href="/Services/GetFederatedSearch.aspx" title="IQM2 search" />
               Agency meta tags (google-site-verification, msvalidate.01)
```

---

## 2. Bodies / Categories

Okeechobee County has only **one** commission YAML for this platform: `okeechobee-county-bcc.yaml` (BCC). There is no `okeechobee-county-pz.yaml` or `okeechobee-county-boa.yaml` in the `FL/` jurisdiction config directory.

| Slug | Body | `scraping.platform` |
|------|------|----------------------|
| `okeechobee-county-bcc` | Board of County Commissioners | **granicus** |

```yaml
# okeechobee-county-bcc.yaml (verbatim)
slug: okeechobee-county-bcc
name: "Okeechobee County BCC"
state: FL
county: Okeechobee
municipality: null
commission_type: bcc
scraping:
  platform: granicus
  base_url: "https://okeechobeecountyfl.iqm2.com/Citizens"
  document_formats: [pdf]
  has_duplicate_page_bug: false
detection_patterns:
  header_keywords:
    - "COUNTY COMMISSIONERS"
    - "BOARD OF COUNTY COMMISSIONERS"
  require_also:
    - "OKEECHOBEE COUNTY"
  header_zone: wide
extraction_notes:
  - "County body -- cannot annex."
  - "Generic Florida county. Flag sparse items for review."
```

No Planning & Zoning or Board of Adjustment configs exist for Okeechobee; those bodies (if they meet and publish agendas) are not yet in the commission-radar pipeline.

---

## 3. Events Endpoint

Granicus IQM2 uses a server-rendered ASP.NET portal. The primary public surfaces:

```
GET https://okeechobeecountyfl.iqm2.com/Citizens/
GET https://okeechobeecountyfl.iqm2.com/Citizens/Default.aspx
GET https://okeechobeecountyfl.iqm2.com/Citizens/Board.aspx?Board={boardId}&Year={year}
GET https://okeechobeecountyfl.iqm2.com/Citizens/Detail_Meeting.aspx?ID={meetingId}
GET https://okeechobeecountyfl.iqm2.com/Citizens/FileOpen.aspx?Type=1&ID={docId}&Inline=True
GET https://okeechobeecountyfl.iqm2.com/Services/GetFederatedSearch.aspx?q={query}
GET https://okeechobeecountyfl.iqm2.com/Services/Calendar.ashx?From={date}&To={date}
```

### Expected flow for the scraper

1. **List bodies** via `Default.aspx` or `Board.aspx` to discover `Board={id}` parameters.
2. **Iterate meetings** by year for each board.
3. **Fetch per-meeting detail page** (`Detail_Meeting.aspx?ID=...`) to get agenda / minutes PDF links.
4. **Download PDFs** via `FileOpen.aspx?Type=1&ID=...` (Type=1 is typical for agendas; Type=2 for minutes on some IQM2 deployments).

Granicus does NOT publish an OData or JSON REST API for IQM2 (unlike Legistar); scrapers must parse HTML.

### Federated search endpoint

```
GET https://okeechobeecountyfl.iqm2.com/Services/GetFederatedSearch.aspx?q={query}&Start={offset}
```

Returns a JSON-ish response describing search matches. Not currently used by the commission-radar scraper.

---

## 4. Event Fields

From the IQM2 detail page (`Detail_Meeting.aspx`), per meeting:

| Field | Source | Notes |
|-------|--------|-------|
| `meeting_id` | URL query `ID` | Numeric IQM2 meeting ID |
| `meeting_date` | Page header | Parsed to ISO `YYYY-MM-DD` |
| `meeting_time` | Page header | Free-text (e.g., `"9:00 AM"`) |
| `meeting_title` | Page heading | E.g., "Regular Meeting" |
| `body_name` | Breadcrumb / page title | Always `"Board of County Commissioners"` for this config |
| `location` | Page content | Room / venue |
| `agenda_url` | `FileOpen.aspx?Type=1&ID=...` link | PDF download |
| `minutes_url` | `FileOpen.aspx?Type=2&ID=...` link (nullable) | PDF download |
| `attachment_urls` | Per-item `FileOpen.aspx` links | PDF attachments |

---

## 5. What We Extract

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Okeechobee County BCC Agenda - {meeting_date}"` / `"... Minutes - {meeting_date}"` |
| `url` | Agenda / minutes PDF link | `FileOpen.aspx?...` |
| `date_str` | Meeting date | `YYYY-MM-DD` |
| `document_id` | `meeting_id` | Numeric IQM2 ID |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |
| `filename` | Computed | `"Agenda_{date}_{meeting_id}.pdf"` |

---

## 6. Unused / Additional Endpoints

| Endpoint | What it returns | Used? |
|----------|-----------------|-------|
| `Services/GetFederatedSearch.aspx` | Full-text search | NO |
| `Services/Calendar.ashx` | Calendar-view events | NO |
| `Services/OpenSearch.ashx` | OpenSearch discovery XML | NO |
| `Citizens/MembersList.aspx` | Member roster per board | NO |
| `Citizens/BoardsList.aspx` | All boards listing | NO (single body hardcoded) |
| `Media/Play_Meeting.aspx?MeetingID=...` | Meeting video | NO |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Meeting ID | YES | URL `ID` param | -- | -- |
| Meeting Date | YES | Detail page header | -- | -- |
| Meeting Time | NO | -- | Free-text meeting time | Detail page |
| Agenda PDF | YES | `FileOpen.aspx?Type=1` link | -- | -- |
| Minutes PDF | YES (when posted) | `FileOpen.aspx?Type=2` link | -- | -- |
| Individual agenda items | NO | -- | Item list rendered on detail page | `Detail_Meeting.aspx` body |
| Attachments per item | NO | -- | Sub-links to PDF exhibits | Detail page |
| Meeting video | NO | -- | `Media/Play_Meeting.aspx` | Detail page |
| Vote records | NO | -- | Not generally published in IQM2 HTML | -- |
| Member roster | NO | -- | `MembersList.aspx` | -- |
| P&Z / BOA meetings | NO | No config | -- | -- |

---

## 8. Known Limitations and Quirks

1. **Registry status is `pending_validation`.** Per `county-registry.yaml` (`okeechobee-fl.projects.cr`): "Granicus. pending_validation". The scraper is configured but has NOT been validated against a complete meeting sweep.

2. **Only BCC is configured.** There is no `okeechobee-county-pz.yaml` or `okeechobee-county-boa.yaml` in `modules/commission/config/jurisdictions/FL/`. If Okeechobee operates a Planning & Zoning board or Board of Adjustment with published agendas, those bodies are currently invisible to the commission-radar pipeline.

3. **IQM2 does NOT expose a REST / OData API.** Unlike Legistar (CR Polk / Broward / Hernando / etc.), Granicus IQM2 is a server-rendered ASP.NET portal. Scrapers must parse HTML; there is no JSON endpoint for the events list.

4. **URL redirect.** `https://okeechobeecountyfl.iqm2.com/Citizens` 301-redirects to `https://okeechobeecountyfl.iqm2.com/Citizens/` (trailing slash). Use a client that follows redirects (`curl -L`, `requests(allow_redirects=True)`).

5. **`FileOpen.aspx?Type=1` vs `Type=2`.** Type `1` is typically the agenda PDF; `Type=2` is the minutes PDF. Other type values may exist for supplemental packets or video metadata. Scrapers should use the explicit `Type` parameter rather than assuming.

6. **`has_duplicate_page_bug: false`.** Okeechobee's IQM2 does not have the duplicate-page pagination bug that affects some tenants.

7. **Google / Bing site verification tokens visible.** The HTML includes `google-site-verification` and `msvalidate.01` meta tags. These are benign but indicate the tenant is configured for search-engine indexing.

8. **IQM2 search is OpenSearch-compatible.** The page declares `<link rel="search" type="application/opensearchdescription+xml" href="/Services/GetFederatedSearch.aspx" title="IQM2 search" />`. Federated search is available but unused by the scraper.

9. **Text extraction note:** "County body -- cannot annex." Per YAML -- any "annexation" keyword hit is a false positive.

10. **Single-word `granicus` platform label.** The YAML uses `platform: granicus` (lowercase). This matches the commission-radar platform registry key; do not rewrite as `IQM2`, `iqm2`, or `Granicus IQM2`.

**Source of truth:** `modules/commission/config/jurisdictions/FL/okeechobee-county-bcc.yaml`, `county-registry.yaml` (`okeechobee-fl.projects.cr`), live probe against `https://okeechobeecountyfl.iqm2.com/Citizens` (HTTP 301 -> HTTP 200, 45 KB)
