# Duval County FL -- Legistar OData (Jacksonville City Council) API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug | **`jaxcityc`** |
| Portal URL | `https://jaxcityc.legistar.com` |
| Auth | Anonymous |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page size | 100 (`$top`) |
| Request delay | 0.5s |
| Registry status | `cr: partial_or_outlier` per `county-registry.yaml` L408-419 |

### Consolidated government — Jacksonville City Council IS the BCC

Duval County and the City of Jacksonville consolidated in 1968. There is **no separate Board of County Commissioners**; the **Jacksonville City Council** (19 members) serves as the combined legislative body for the entire county. Per `modules/commission/config/jurisdictions/FL/duval-county-bcc.yaml`:

```yaml
slug: duval-county-bcc
name: "Duval County BCC"
county: Duval
commission_type: bcc
scraping:
  platform: legistar
  base_url: "https://webapi.legistar.com/v1/jaxcityc"
  legistar_client: "jaxcityc"
  body_names:
    - "City Council"
extraction_notes:
  - "County body — cannot annex."
  - "Jacksonville consolidated city-county. City Council on Legistar (jaxcityc)."
```

### Configured CountyData2 bodies

| Slug | Body | `body_names` | `scraping.platform` |
|------|------|--------------|---------------------|
| `duval-county-bcc` | Duval County BCC (= Jacksonville City Council) | `["City Council"]` | `legistar` |
| `duval-county-pz` | Duval County P&Z | -- | **`manual`** ("P&Z hosted on separate COJ site, not Legistar") |
| `duval-county-boa` | Duval County BOA | -- | **`manual`** ("BOA hosted on separate COJ site, not Legistar") |

## 2. Probe (2026-04-14)

```
GET https://webapi.legistar.com/v1/jaxcityc/bodies
-> HTTP 200, 21,842 bytes, application/json
   Array of 40 body objects. BodyId 138 = "City Council" (NOT "Board of County Commissioners").
```

### Bodies on Legistar (40 total — selection)

| BodyId | Body Name | Type | Tracked |
|--------|-----------|------|---------|
| 138 | **City Council** | Primary Legislative Body | **YES** (`duval-county-bcc`) |
| 139 | Finance Committee | Standing Committees | NO |
| 140 | Land Use & Zoning Committee | Standing Committees | NO (land-use committee of City Council) |
| 181 | Neighborhoods, Community Services, Public Health and Safety Committee | Standing Committees | NO |
| 182 | Rules Committee | Standing Committees | NO |
| 183 | Transportation, Energy & Utilities Committee | Standing Committees | NO |
| 188 | Jacksonville Waterways Commission | Boards or Commission | NO |
| 216 | Personnel Committee | Standing Committees | NO |
| 235 | Charter Revision Commission | Boards or Commission | NO |
| 236 | Finance Committee - Budget Hearings | Standing Committees | NO |
| 259 / 272 / 279 | Value Adjustment Board (2023 / 2024 / 2025) | Boards or Commission | NO |
| 267 | Community Redevelopment Agency Board | Boards or Commission | NO |
| 271 | Committee of the Whole | Standing Committees | NO |
| ... | (27 other committees, special committees, and advisory groups) | | NO |

Plus special committees covering permitting, downtown development, social justice, JEA investigatory work, JSEB, Youth Empowerment, Community Benefits Agreement (1.0 and 2.0), CQLI, and others.

## 3. Events Endpoint

### Request

```
GET https://webapi.legistar.com/v1/jaxcityc/events
```

Per CommissionRadar run: one iteration with `body_names=["City Council"]` (BCC). P&Z and BOA are skipped (`platform: manual` in their YAMLs).

### OData query parameters (standard Legistar contract)

| Parameter | Used | Value |
|-----------|------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq 'City Council'` |
| `$orderby` | YES | `EventDate desc` |
| `$top` | YES | 100 |
| `$skip` | YES | paginated |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

## 4. Event Fields

Same canonical field contract as all Legistar tenants (see `polk-county-legistar.md` §3 for full table): `EventId`, `EventGuid`, `EventBodyId`, `EventBodyName`, `EventDate`, `EventTime`, `EventLocation`, `EventAgendaFile`, `EventMinutesFile`, `EventAgendaStatusName`, `EventMinutesStatusName`, `EventInSiteURL`, etc.

## 5. What We Extract / What a Future Adapter Would Capture

One `DocumentListing` per non-null agenda/minutes PDF per event:

| DocumentListing field | Source | Value pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"City Council Agenda - {meeting_date}"` / `"City Council Minutes - ..."` |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL |
| `date_str` | `EventDate[0:10]` | `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified |
| `document_type` | Hardcoded | `"agenda"` / `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |

Dedup key: `"agenda-{EventId}"` / `"minutes-{EventId}"`.

## 6. Auth / Bypass

Anonymous. No API key, no cookies, no captcha.

## 7. What We Extract vs What's Available

| Data Category | Extracted | Source | Not Extracted |
|---------------|-----------|--------|---------------|
| Event ID, date, body | YES | Event* fields | GUID, row version |
| Agenda / Minutes PDF | YES | EventAgendaFile / EventMinutesFile | Status, last-published timestamp |
| Location, portal URL, video | NO | -- | Available |
| **Committee proceedings** | NO | -- | 39 other bodies on `jaxcityc` (Finance Committee, Land Use & Zoning, etc.) |
| Agenda items, votes, matters | NO | -- | Via `/eventitems`, `/votes`, `/matters` — very active on `jaxcityc` because the Council legislates for a major city |

## 8. Known Limitations and Quirks

1. **Duval has no BCC in the traditional sense.** Jacksonville is a consolidated city-county; the "County body" is the **Jacksonville City Council**. Any UI surface that refers to `duval-county-bcc` under the rubric "Board of County Commissioners" is misleading — correct terminology is "City Council". Detection patterns in the YAML use `"COUNTY COMMISSIONERS"` / `"BOARD OF COUNTY COMMISSIONERS"` keywords with `"DUVAL COUNTY"` as require_also, which may mis-match Jacksonville City Council agenda headers. Fieldwork validation has not surfaced this as a blocker because `body_names: ["City Council"]` drives the API filter, but downstream header-based detection may need separate tuning for Duval.
2. **40 bodies on `jaxcityc`** — the largest count among all 6 counties in this batch. Most are standing or special committees of the Council. Only BodyId 138 (City Council) is tracked.
3. **Land Use & Zoning Committee (BodyId 140) is a standing committee** of the Council, not an independent P&Z Commission. Duval's actual P&Z functions (like development review, subdivision platting) live in the City Planning Department, which publishes on `coj.net` — hence `duval-county-pz.yaml` has `platform: manual`.
4. **Three separate Value Adjustment Boards** (2023, 2024, 2025 — BodyIds 259, 272, 279). Each year's VAB is a distinct body. Typical for counties that keep VAB rosters annually.
5. **Separate "Finance Committee" and "Finance Committee - Budget Hearings" and "Finance Committee - Independent External Auditor Selection Committee"** (BodyIds 139, 236, 276). The Finance Committee has multiple focused session types.
6. **"Committee of the Whole" (BodyId 271)** — when City Council meets with all members acting as a committee. Separate body; not tracked.
7. **`has_duplicate_page_bug: false`** in the BCC YAML.
8. **Status `partial_or_outlier`** per registry (L419). Meaning: Legistar works and is configured, but some completeness/consistency issue keeps it out of "live". The consolidated-government body-naming mismatch (BCC YAML detection patterns vs. actual "City Council" headers) is the most likely cause.
9. **P&Z and BOA are `platform: manual` for intentional reasons.** Per the respective YAML extraction_notes: "P&Z hosted on separate COJ site, not Legistar" and "BOA hosted on separate COJ site, not Legistar. Documents must be uploaded manually." These surfaces live on `www.coj.net` (which returned HTTP 503 on the 2026-04-14 probe — `coj.net` has bot mitigation). Don't attempt to crawl them through Legistar.
10. **`EventInSiteURL`** for City Council events points to `https://jaxcityc.legistar.com/MeetingDetail.aspx?...` — useful for direct-citation UX features.
11. **Body list cross-check recommended annually.** With 40 bodies and frequent creation of new Special Committees (Opioid Epidemic, JEA Matters, Redistricting, Downtown Development, etc.), Jacksonville's Legistar shape evolves. Quarterly sweep of `/bodies` keeps the "not tracked" roster accurate.
12. **No Community Redevelopment Agency Board events currently tracked.** BodyId 267 exists and is active; if CRA plan-amendment proceedings become scope, add as a new YAML.

Source of truth: `county-registry.yaml` L408-419 (`duval-fl.projects.cr`), `modules/commission/config/jurisdictions/FL/duval-county-bcc.yaml` (legistar client `jaxcityc`, body `City Council`), `modules/commission/config/jurisdictions/FL/duval-county-pz.yaml` (platform `manual`), `modules/commission/config/jurisdictions/FL/duval-county-boa.yaml` (platform `manual`), live probe of `https://webapi.legistar.com/v1/jaxcityc/bodies` (2026-04-14, HTTP 200, 40 bodies).
