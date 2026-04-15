# Hernando County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug | `hernandocountyfl` |
| Portal URL | `https://hernandocountyfl.legistar.com` |
| Auth | Anonymous — no API key or token required |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page size | 100 (`$top`) |
| Request delay | 0.5s between paginated requests |
| Registry status | `cr: live` per `county-registry.yaml` L186-190 |
| Registry note | "Legistar OData API validated. 6 listings in 60-day window. Reverted from civicclerk (404) to legistar." |

### Configured bodies (CountyData2)

| Slug | Body | `body_names` | `commission_type` | `scraping.platform` |
|------|------|--------------|-------------------|---------------------|
| `hernando-county-bcc` | Hernando County BCC | `["Board of County Commissioners"]` | `bcc` | `legistar` |
| `hernando-county-pz` | Hernando County P&Z | `["Planning & Zoning Commission"]` | `planning_board` | `legistar` |

Both bodies share one Legistar client (`hernandocountyfl`). No `hernando-county-boa` entry exists.

## 2. Probe (2026-04-14)

```
GET https://webapi.legistar.com/v1/hernandocountyfl/bodies
-> HTTP 200, 6,370 bytes, application/json
   Array of 12 body objects. BodyId 138 = "Board of County Commissioners",
   BodyId 140 = "Planning & Zoning Commission".
```

### Bodies on Legistar (12 total)

| BodyId | Body Name | Type | MeetFlag | Active | Tracked |
|--------|-----------|------|----------|--------|---------|
| 138 | Board of County Commissioners | Primary Legislative Body | 1 | 1 | **YES** (`hernando-county-bcc`) |
| 139 | Community Redevelopment Agency | CRA | 1 | 1 | NO |
| 140 | Planning & Zoning Commission | Planning and Zoning | 1 | 1 | **YES** (`hernando-county-pz`) |
| 233 | Metropolitan Planning Organization | MPO | 1 | 1 | NO |
| 235 | Board of County Commissioners Budget Hearing | Budget Hearing | 1 | 1 | NO |
| 236 | Board of County Commissioners Budget Workshop | Workshop | 1 | 1 | NO |
| 237 | Board of County Commissioners, School Board, and Brooksville City Council Interlocal Governmental Meeting | Special | 1 | 1 | NO |
| 238 | Port Authority | Port Authority | 1 | 1 | NO |
| 239 | Board of County Commissioners Workshop | BOCC Workshop | 1 | 1 | NO |
| 240 | Value Adjustment Board | VAB | 1 | 1 | NO |
| 243 | Special Masters | Special Masters | 1 | 1 | NO |
| 244 | I Messed Up | Department | 1 | 1 | NO (clerical placeholder) |

## 3. Events Endpoint (BCC + P&Z)

### Request

```
GET https://webapi.legistar.com/v1/hernandocountyfl/events
```

Iterated once per tracked body (BCC, P&Z) on each CommissionRadar run.

### OData query parameters

| Parameter | Used | Value | Notes |
|-----------|------|-------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq '{body}'` | OData v3 filter expression |
| `$orderby` | YES | `EventDate desc` | Newest first |
| `$top` | YES | `100` | Page size |
| `$skip` | YES | Incremented by 100 | Pagination offset |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

## 4. Event Fields (contract shared across Legistar tenants)

Same as the Polk/Broward/Indian River API maps:

| Field | Type | Notes |
|-------|------|-------|
| EventId | int | Primary key; composes `agenda-{EventId}` / `minutes-{EventId}` dedup keys |
| EventGuid | string | GUID |
| EventBodyId | int | Foreign key → `/bodies` |
| EventBodyName | string | Body display name |
| EventDate | datetime | First 10 chars parsed to `YYYY-MM-DD` |
| EventTime | string | `"9:00 AM"` — text, not datetime |
| EventLocation | string | |
| EventAgendaFile | string/null | Direct agenda PDF URL |
| EventMinutesFile | string/null | Direct minutes PDF URL |
| EventAgendaStatusName | string | `"Closed"`, `"Draft"`, etc. |
| EventMinutesStatusName | string | Same |
| EventAgendaLastPublishedUTC | datetime/null | |
| EventMinutesLastPublishedUTC | datetime/null | |
| EventComment | string | Internal notes |
| EventVideoPath | string/null | |
| EventInSiteURL | string | Meeting detail page on portal |
| EventItems | array | Empty in list response; fetch via `/events/{id}/eventitems` |

## 5. What We Extract / What a Future Adapter Would Capture

One `DocumentListing` per non-null agenda/minutes PDF per event:

| DocumentListing field | Source | Value pattern |
|-----------------------|--------|---------------|
| `title` | Computed | `"{EventBodyName} Agenda - {meeting_date}"` / `"Minutes - ..."` |
| `url` | `EventAgendaFile` / `EventMinutesFile` | Direct PDF URL on Legistar CDN |
| `date_str` | `EventDate` | First 10 chars → `YYYY-MM-DD` |
| `document_id` | `EventId` | Stringified |
| `document_type` | Hardcoded | `"agenda"` or `"minutes"` |
| `file_format` | Hardcoded | `"pdf"` |
| `filename` | Computed | `"Agenda_{date}_{EventId}.pdf"` / `"Minutes_{date}_{EventId}.pdf"` |

### Deduplication

Composite dedup key `"agenda-{EventId}"` / `"minutes-{EventId}"` prevents duplicates across body iterations (in Hernando's case, BCC vs. P&Z — BCC events can appear tagged under the BOCC Budget / Workshop / Interlocal body IDs too, but we only request `EventBodyName eq 'Board of County Commissioners'` which filters those out).

## 6. Auth Posture / Bypass

Anonymous — no API key, no login, no captcha, no Cloudflare. Plain HTTPS + `Accept: application/json` works.

## 7. What We Extract vs What's Available

| Data Category | Extracted | Source | Available-but-unused | Source |
|---------------|-----------|--------|---------------------|--------|
| Event ID | YES | EventId | EventGuid, EventRowVersion | -- |
| Meeting date | YES | EventDate[0:10] | Full datetime, EventTime (text) | EventDate, EventTime |
| Body name | YES | EventBodyName | BodyId, BodyTypeName | /bodies |
| Agenda PDF | YES | EventAgendaFile | Agenda status, last published | EventAgendaStatusName, EventAgendaLastPublishedUTC |
| Minutes PDF | YES | EventMinutesFile | Minutes status, last published | EventMinutesStatusName, EventMinutesLastPublishedUTC |
| Meeting location | NO | -- | EventLocation | -- |
| Portal URL | NO | -- | EventInSiteURL | -- |
| Video | NO | -- | EventVideoPath / Status | -- |
| Agenda items | NO | -- | `/events/{id}/eventitems` | Separate endpoint |
| Vote records | NO | -- | `/eventitems/{id}/votes` | Separate endpoint |
| Matters | NO | -- | `/matters` | Separate endpoint |

## 8. Known Limitations and Quirks

1. **Reverted from CivicClerk after 404.** Per `county-registry.yaml` L190: "Reverted from civicclerk (404) to legistar." — a prior Hernando CR attempt used CivicClerk (`pascocofl`-style tenant) and failed; Legistar is the verified good source.
2. **Three BOCC variants.** `Board of County Commissioners Budget Hearing` (235), `Budget Workshop` (236), `Workshop` (239) are separate bodies from the regular BCC (138). We track only 138. Budget/workshop sessions will NOT appear in BCC sweeps — explicit inclusion would be required.
3. **Planning & Zoning is a single body.** Unlike Marion (where Board of County Commissioners P&Z sits as a separate body 229) or Polk (where "Planning Commission" is used), Hernando's P&Z body is named exactly `"Planning & Zoning Commission"` (with an ampersand, no "and"). Yaml must spell it that way or filter returns empty.
4. **"I Messed Up" body.** BodyId 244, type `Department`, name `"I Messed Up"` — a clerical placeholder left in the Legistar admin UI. Active=1, MeetFlag=1, but never has real events. Harmless, listed here so future readers don't waste time debugging.
5. **Port Authority (238), Value Adjustment Board (240), Special Masters (243)** are county-level advisory or quasi-judicial bodies available on Legistar but not currently configured. Adding them requires new commission YAMLs.
6. **60-day window returned 6 listings** (per registry note). That's within the expected cadence: BCC meets roughly twice per month; P&Z roughly monthly. Higher counts may indicate the registry note is outdated after additional documents published.
7. **`EventAgendaFile` / `EventMinutesFile` can be null even after a meeting.** When `EventAgendaStatusName == "Draft"` the PDF URL is null. Wait for `"Closed"` to confirm publication.
8. **`has_duplicate_page_bug: false`** in both YAMLs — Hernando Legistar does not exhibit the agenda-pagination duplication observed on some other Legistar tenants.
9. **No agenda-item or vote extraction.** CommissionRadar only pulls PDF listings; `/events/{id}/eventitems` and `/eventitems/{id}/votes` are unused. Adding them would quadruple request volume.
10. **`webapi.legistar.com` is the shared API gateway** — not a Hernando-owned host. Outages on this hostname affect all Legistar counties simultaneously (see Polk/Broward/IRC maps).
11. **No registered BOA.** Hernando does not have a `hernando-county-boa` yaml. Hernando County's land-use adjudication is typically handled through the P&Z Commission and Special Masters rather than a standalone BOA. Do not invent a BOA config.

Source of truth: `county-registry.yaml` L164-190 (`hernando-fl.projects.cr`), `modules/commission/config/jurisdictions/FL/hernando-county-bcc.yaml`, `modules/commission/config/jurisdictions/FL/hernando-county-pz.yaml`, live probe of `https://webapi.legistar.com/v1/hernandocountyfl/bodies` (2026-04-14, HTTP 200, 12 bodies), plus the shared Legistar conventions documented in `docs/api-maps/polk-county-legistar.md`.
