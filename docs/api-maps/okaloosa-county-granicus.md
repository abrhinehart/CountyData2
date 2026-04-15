# Okaloosa County FL -- Granicus IQM2 API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Granicus IQM2 (Meeting Portal / Citizens) |
| Portal URL | `https://okaloosacountyfl.iqm2.com/Citizens` |
| Protocol | Server-rendered ASP.NET (Meeting Portal HTML); Granicus federated search endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction configs | `modules/commission/config/jurisdictions/FL/okaloosa-county-bcc.yaml`, `-boa.yaml`, `-pz.yaml` (3 bodies) |
| Registry status | `pending_validation` (per `okaloosa-fl.projects.cr`, `county-registry.yaml` L237-240) |
| Adapter added in commit | **`aa19d98`** ("feat: add Granicus/iQM2 CR scraper adapter for Okeechobee and Okaloosa FL") |

### Probe (2026-04-14)

```
GET https://okaloosacountyfl.iqm2.com/Citizens
-> HTTP 301 (redirect to /Citizens/)
GET https://okaloosacountyfl.iqm2.com/Citizens/
-> HTTP 200, body ~35.7 KB
Body contains: <title>Meeting Portal - Okaloosa County, Florida</title>
               <link rel="search" href="/Services/GetFederatedSearch.aspx" title="IQM2 search" />
               Agency meta tags (google-site-verification, msvalidate.01)
```

---

## 2. Bodies / Categories

Okaloosa County has **three** commission YAMLs configured for the same IQM2 portal:

| Slug | Body | commission_type | `scraping.platform` |
|------|------|-----------------|----------------------|
| `okaloosa-county-bcc` | Okaloosa County BCC | `bcc` | `granicus` |
| `okaloosa-county-boa` | Okaloosa County BOA | `board_of_adjustment` | `granicus` |
| `okaloosa-county-pz` | Okaloosa County P&Z | `planning_board` | `granicus` |

All three use `base_url: "https://okaloosacountyfl.iqm2.com/Citizens"`. The scraper discriminates between bodies via the `detection_patterns.header_keywords` + `require_also` combination.

```yaml
# okaloosa-county-bcc.yaml (verbatim)
slug: okaloosa-county-bcc
name: "Okaloosa County BCC"
state: FL
county: Okaloosa
municipality: null
commission_type: bcc
scraping:
  platform: granicus
  base_url: "https://okaloosacountyfl.iqm2.com/Citizens"
  document_formats: [pdf]
  has_duplicate_page_bug: false
detection_patterns:
  header_keywords:
    - "COUNTY COMMISSIONERS"
    - "BOARD OF COUNTY COMMISSIONERS"
  require_also:
    - "OKALOOSA COUNTY"
  header_zone: wide
extraction_notes:
  - "County body -- cannot annex."
  - "Generic Florida county. Flag sparse items for review."
```

The `-boa.yaml` and `-pz.yaml` follow the same shape with substitutions:

- BOA: `commission_type: board_of_adjustment`, `header_keywords: [ADJUSTMENT, APPEALS]`, `extraction_notes: ["Board of Adjustment -- handles variances and appeals, outside core tracking scope."]`
- P&Z: `commission_type: planning_board`, `header_keywords: [PLANNING]`, `extraction_notes: ["Planning/advisory board -- recommendations only, not final authority on legislative items."]`

---

## 3. Events Endpoint

Granicus IQM2 uses a server-rendered ASP.NET portal. The primary public surfaces:

```
GET https://okaloosacountyfl.iqm2.com/Citizens/
GET https://okaloosacountyfl.iqm2.com/Citizens/Default.aspx
GET https://okaloosacountyfl.iqm2.com/Citizens/Board.aspx?Board={boardId}&Year={year}
GET https://okaloosacountyfl.iqm2.com/Citizens/Detail_Meeting.aspx?ID={meetingId}
GET https://okaloosacountyfl.iqm2.com/Citizens/FileOpen.aspx?Type=1&ID={docId}&Inline=True
GET https://okaloosacountyfl.iqm2.com/Services/GetFederatedSearch.aspx?q={query}
GET https://okaloosacountyfl.iqm2.com/Services/Calendar.ashx?From={date}&To={date}
```

### Expected flow for the scraper

1. Load `Default.aspx` / `Citizens/` to discover `Board={id}` parameters for BCC / BOA / P&Z.
2. For each board, iterate meetings by year.
3. Fetch `Detail_Meeting.aspx?ID=...` to collect agenda / minutes PDF links.
4. Download PDFs via `FileOpen.aspx?Type={1|2}&ID=...`.

Granicus IQM2 does NOT expose an OData or JSON REST API; scrapers must parse HTML.

---

## 4. Event Fields

Per-meeting fields from `Detail_Meeting.aspx`:

| Field | Source | Notes |
|-------|--------|-------|
| `meeting_id` | URL query `ID` | Numeric |
| `meeting_date` | Page header | ISO `YYYY-MM-DD` |
| `meeting_time` | Page header | Free-text |
| `meeting_title` | Heading | E.g., "Regular Meeting" |
| `body_name` | Breadcrumb | Per body config |
| `location` | Page content | -- |
| `agenda_url` | `FileOpen.aspx?Type=1&ID=...` | PDF |
| `minutes_url` | `FileOpen.aspx?Type=2&ID=...` (nullable) | PDF |

---

## 5. What We Extract

| DocumentListing Field | Source | Value Pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"Okaloosa County {BCC|BOA|P&Z} Agenda - {meeting_date}"` |
| `url` | Agenda / minutes PDF | `FileOpen.aspx?...` |
| `date_str` | Meeting date | `YYYY-MM-DD` |
| `document_id` | `meeting_id` | Numeric |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

---

## 6. Diff vs Okeechobee Granicus (1-body peer)

Both Okaloosa and Okeechobee use Granicus IQM2, but the body count and status differ.

| Attribute | Okaloosa | Okeechobee |
|-----------|----------|------------|
| Portal URL | `okaloosacountyfl.iqm2.com/Citizens` | `okeechobeecountyfl.iqm2.com/Citizens` |
| Bodies configured | 3 (BCC + BOA + P&Z) | 1 (BCC only) |
| Status | `pending_validation` | `pending_validation` |
| `has_duplicate_page_bug` | false | false |
| Adapter commit | **`aa19d98`** | `aa19d98` (same commit onboarded both) |
| P&Z config | YES | NO |
| BOA config | YES | NO |
| Federated search | Available, unused | Available, unused |

---

## 7. Unused / Additional Endpoints

| Endpoint | What it returns | Used? |
|----------|-----------------|-------|
| `Services/GetFederatedSearch.aspx` | Full-text search | NO |
| `Services/Calendar.ashx` | Calendar-view events | NO |
| `Services/OpenSearch.ashx` | OpenSearch discovery XML | NO |
| `Citizens/MembersList.aspx` | Member roster per board | NO |
| `Citizens/BoardsList.aspx` | All boards listing | NO |
| `Media/Play_Meeting.aspx?MeetingID=...` | Meeting video | NO |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Meeting ID | YES | URL `ID` | -- | -- |
| Meeting date | YES | Detail header | -- | -- |
| Meeting time | NO | -- | Free-text time | Detail header |
| Agenda PDF | YES | `FileOpen.aspx?Type=1` | -- | -- |
| Minutes PDF | YES (when posted) | `FileOpen.aspx?Type=2` | -- | -- |
| Per-item agendas | NO | -- | Rendered in detail page body | `Detail_Meeting.aspx` |
| Per-item attachments | NO | -- | `FileOpen.aspx` sub-links | Detail page |
| Meeting video | NO | -- | `Media/Play_Meeting.aspx` | Detail page |
| Vote records | NO | -- | Not generally published in IQM2 HTML | -- |
| Member roster | NO | -- | `MembersList.aspx` | -- |
| Combined 3-body parity | YES (BCC+BOA+P&Z configured) | Per-YAML | -- | -- |

---

## 9. Known Limitations and Quirks

1. **Adapter landed in commit `aa19d98`.** "feat: add Granicus/iQM2 CR scraper adapter for Okeechobee and Okaloosa FL". Both counties' IQM2 support was introduced in the same commit.

2. **Status is `pending_validation`.** The YAMLs exist, the adapter exists, but a full-sweep validation against `live` listings has not been run. Promotion to `live` requires confirming that all three bodies return meetings in a recent window.

3. **Three bodies share one portal.** BCC + BOA + P&Z all route through the same `okaloosacountyfl.iqm2.com/Citizens` base. Disambiguation is handled entirely by `detection_patterns.header_keywords` + `require_also`. Any header-detection regression affects all three bodies simultaneously.

4. **URL 301-redirects at `/Citizens` (no slash) to `/Citizens/`.** The HTTP client must follow redirects. The probe on 2026-04-14 confirmed the 301 -> 200 chain.

5. **IQM2 does NOT expose REST / OData.** Unlike Legistar (used by Polk BCC), IQM2 is HTML-only. Scrapers must parse server-rendered pages.

6. **`FileOpen.aspx?Type=1` vs `Type=2`.** Type 1 = agenda PDF; Type 2 = minutes PDF. Other type values may exist for supplemental packets on some tenants.

7. **`has_duplicate_page_bug: false`.** Okaloosa IQM2 does not exhibit the duplicate-page pagination bug that affects some IQM2 deployments.

8. **Google / Bing verification tokens present in HTML.** Benign; indicates tenant is configured for search-engine indexing.

9. **OpenSearch advertised but unused.** `<link rel="search" ... href="/Services/GetFederatedSearch.aspx">` declared; scraper doesn't use it.

10. **BCC extraction note: "County body -- cannot annex."** Any "annexation" keyword hit on a BCC meeting is a false positive.

11. **Single-word `granicus` platform label.** Platform registry key is lowercase `granicus` (not `iqm2`, `IQM2`, `Granicus`, or `Granicus IQM2`). Match exact casing.

12. **P&Z is advisory only.** Per extraction_notes: "recommendations only, not final authority on legislative items." Downstream consumers weighing legislative impact should flag P&Z items accordingly.

**Source of truth:** `modules/commission/config/jurisdictions/FL/okaloosa-county-bcc.yaml`, `okaloosa-county-boa.yaml`, `okaloosa-county-pz.yaml`, `county-registry.yaml` (`okaloosa-fl.projects.cr`, L237-240), commit `aa19d98` ("feat: add Granicus/iQM2 CR scraper adapter for Okeechobee and Okaloosa FL"), live probe of `https://okaloosacountyfl.iqm2.com/Citizens` (HTTP 301 -> HTTP 200, 35.7 KB).
