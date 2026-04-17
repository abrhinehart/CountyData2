# Seminole County FL -- Legistar OData API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Legistar (Granicus) |
| API Base URL | `https://webapi.legistar.com/v1` |
| Client Slug | `seminolecountyfl` |
| Portal URL | `https://seminolecountyfl.legistar.com` |
| Auth | Anonymous |
| Protocol | OData v3 over REST (JSON) |
| User-Agent | `CommissionRadar/1.0` |
| Page size | 100 (`$top`) |
| Request delay | 0.5s |
| Registry status | `cr: partial_or_outlier` per `county-registry.yaml` L509-522 |

### Configured bodies (CountyData2)

| Slug | Body | `body_names` | `scraping.platform` |
|------|------|--------------|---------------------|
| `seminole-county-bcc` | Seminole County BCC | `["Board of County Commissioners"]` | `legistar` |
| `seminole-county-pz` | Seminole County P&Z | `["Planning and Zoning Commission"]` | `legistar` |
| `seminole-county-boa` | Seminole County BOA | -- | **`manual`** |

Note: Seminole uses `"Planning and Zoning Commission"` (word "and"), unlike Hernando/Marion which use `"Planning & Zoning Commission"` (ampersand). The body-name filter is exact-match.

## 2. Probe (2026-04-14)

```
GET https://webapi.legistar.com/v1/seminolecountyfl/bodies
-> HTTP 200, 9,056 bytes, application/json
   Array of 16 body objects. BodyId 138 = "Board of County Commissioners",
   BodyId 184 = "Planning and Zoning Commission",
   BodyId 140 = "Board of Adjustment".
```

### Bodies on Legistar (16 total)

| BodyId | Body Name | Type | Tracked |
|--------|-----------|------|---------|
| 138 | Board of County Commissioners | Primary Legislative Body | **YES** (`seminole-county-bcc`) |
| 140 | **Board of Adjustment** | Board of Adjustment | NO — on Legistar, YAML is `platform: manual` |
| 182 | Code Enforcement Special Magistrate | Code Enforcement | NO |
| 183 | Development Review Committee | Development Review Committee | NO |
| 184 | Planning and Zoning Commission | Planning and Zoning | **YES** (`seminole-county-pz`) |
| 262 | Animal Control Board | Animal Control Board | NO |
| 265 | Charter Review Commission | Charter Review Commission | NO |
| 293 | Acquisition and Restoration Committee | Acquisition and Restoration Committee | NO |
| 294 | Historical Commission | Historical Commission | NO |
| 295 | Parks and Preservation Advisory Committee | Parks and Preservation Advisory Committee | NO |
| 307 | Seminole County Industrial Development Authority | Seminole County Industrial Development Authority | NO |
| 308 | Committee on Aging | Committee on Aging | NO |
| 309 | Library Advisory Board | Library Advisory Board | NO |
| 310 | Tourist Development Council | Tourist Development Council | NO |
| 311 | Agriculture Advisory Committee | Agriculture Advisory Board | NO |
| 312 | Seminole County Tourism Improvement District Advisory Board | (same) | NO |

## 3. Events Endpoint (BCC + P&Z)

### Request

```
GET https://webapi.legistar.com/v1/seminolecountyfl/events
```

Per-run iteration: once for BCC, once for P&Z. (BOA exists on Legistar as BodyId 140 but YAML `platform: manual` — skipped.)

### OData parameters

| Parameter | Used | Value |
|-----------|------|-------|
| `$filter` | YES | `EventDate ge datetime'{start}' and EventDate le datetime'{end}' and EventBodyName eq '{body}'` |
| `$orderby` | YES | `EventDate desc` |
| `$top` | YES | 100 |
| `$skip` | YES | paginated |

### Headers

```
User-Agent: CommissionRadar/1.0
Accept: application/json
```

## 4. Event Fields

Same canonical contract across all Legistar tenants (see `polk-county-legistar.md` §3). Key fields: `EventId`, `EventBodyName`, `EventDate`, `EventAgendaFile`, `EventMinutesFile`, `EventAgendaStatusName`, etc.

## 5. What We Extract / What a Future Adapter Would Capture

One `DocumentListing` per non-null agenda/minutes PDF per event:

| DocumentListing field | Source |
|-----------------------|--------|
| `title` | `"{EventBodyName} Agenda - {meeting_date}"` / `"... Minutes - ..."` |
| `url` | `EventAgendaFile` / `EventMinutesFile` |
| `date_str` | `EventDate[0:10]` |
| `document_id` | `EventId` stringified |
| `document_type` | `"agenda"` / `"minutes"` |
| `file_format` | `"pdf"` |
| `filename` | `"Agenda_{date}_{EventId}.pdf"` |

Dedup key: `"agenda-{EventId}"` / `"minutes-{EventId}"`.

## 6. Auth / Bypass

Anonymous. No API key, no cookies, no captcha. Plain HTTPS + `Accept: application/json` works.

## 7. What We Extract vs What's Available

| Data Category | Extracted | Source | Not Extracted |
|---------------|-----------|--------|---------------|
| Event ID, date, body | YES | Event* fields | GUID, row version |
| Agenda / Minutes PDF | YES | EventAgendaFile / EventMinutesFile | Status, last-published timestamp |
| Location, portal URL, video | NO | -- | Available on events |
| Agenda items, votes, matters | NO | -- | Via `/eventitems`, `/votes`, `/matters` |

## 8. Known Limitations and Quirks

1. **Body name is `"Planning and Zoning Commission"` (word "and")**, NOT `"Planning & Zoning Commission"` (ampersand) used by Hernando and Marion. Spelling matters: OData `$filter` exact-matches the string.
2. **BOA (BodyId 140) exists on Legistar but is `platform: manual`.** `seminole-county-boa.yaml` has `scraping.platform: manual` even though Legistar has the body. Reason per extraction_notes: "Board of Adjustment — handles variances and appeals, outside core tracking scope." If tracking scope expands, the YAML can flip to `legistar` with `body_names: ["Board of Adjustment"]`.
3. **Status `partial_or_outlier`** per registry (L522). Meaning: Legistar works and is configured, but some completeness/consistency issue keeps it out of "live". Seminole has `has_duplicate_page_bug: false` in both BCC and P&Z YAMLs; the outlier flag may reflect lower-than-expected meeting volume or inconsistent minutes publication.
4. **Development Review Committee (BodyId 183)** — land-use intake body that typically precedes P&Z review. Not tracked currently. If development-lifecycle coverage becomes scope, add as a new YAML.
5. **Code Enforcement Special Magistrate (BodyId 182)** — quasi-judicial code-enforcement body. On Legistar but not relevant to CountyData2 scope.
6. **Seminole County Industrial Development Authority (BodyId 307)** — issues tax-exempt IDA bonds; a separate legal entity from the BCC but on the same Legistar instance. Not tracked.
7. **Charter Review Commission (BodyId 265)** — convenes every 10 years to propose charter amendments. Low activity between cycles.
8. **16 bodies total — mid-range count** within this batch (Hernando 12, Marion 21, Duval 40). Seminole's civic governance has fewer advisory committees than Marion but more than Hernando.
9. **No ampersand in body names.** Seminole's Legistar uses the word "and" consistently: `"Planning and Zoning Commission"`, `"Acquisition and Restoration Committee"`, `"Parks and Preservation Advisory Committee"`, `"Committee on Aging"`. Naming style is unique among this batch.
10. **`webapi.legistar.com` shared gateway** — Seminole shares infra with Hernando / Marion / Polk / Broward / IRC / Duval via `webapi.legistar.com`. Legistar-gateway outages affect all simultaneously.
11. **No separate workshop / budget body variants** — unlike Hernando (which has BOCC Workshop, Budget Hearing, Budget Workshop as distinct bodies) or Marion (with Workshop, Budget Meeting, Public Hearing as separate bodies), Seminole keeps everything under BodyId 138. This means workshop/budget sessions WILL appear in BCC sweeps if their `EventBodyName` is the standard "Board of County Commissioners".

Source of truth: `county-registry.yaml` L509-522 (`seminole-fl.projects.cr`), `modules/commission/config/jurisdictions/FL/seminole-county-bcc.yaml`, `modules/commission/config/jurisdictions/FL/seminole-county-pz.yaml`, `modules/commission/config/jurisdictions/FL/seminole-county-boa.yaml`, live probe of `https://webapi.legistar.com/v1/seminolecountyfl/bodies` (2026-04-14, HTTP 200, 16 bodies). Shared Legistar contract per `docs/api-maps/polk-county-legistar.md`.
