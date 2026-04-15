# Baldwin County AL -- Legistar (Granicus) API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Baldwin County Commission |
| Platform | Legistar (Granicus) |
| Portal URL | `https://baldwincountyal.legistar.com/Calendar.aspx` |
| API Base URL | `https://webapi.legistar.com/v1/baldwincountyal` |
| Auth | Anonymous -- no API key / token required |
| Protocol | OData v3 over REST (JSON) |
| Registry entry | `county-registry.yaml` L585-598 has BI only; **no `cr:` block** |
| Adapter reuse | Legistar OData client already exists in this repo (see `polk-county-legistar.md`, `martin-county-legistar.md`, `indian-river-county-legistar.md`) |

Baldwin is a live Legistar tenant. Commission agendas, meetings, and a companion work-session body are available through the standard OData endpoints.

## 2. Probe (2026-04-14)

```
GET https://baldwincountyal.gov/
-> HTTP 200  (Baldwin county website; "Agendas" link points to https://baldwincountyal.legistar.com/Calendar.aspx)

GET https://webapi.legistar.com/v1/baldwincountyal/bodies
-> HTTP 200  (JSON array; at least 2 commission-related bodies visible in the first 2 KB)
```

Bodies observed in the API response include:

| BodyId (seen) | BodyName | BodyType | MeetFlag | ActiveFlag |
|--------------:|----------|----------|:--------:|:----------:|
| 138 | Baldwin County Commission Regular | Primary Legislative Body | 1 | 1 |
| 180 | Baldwin County Commission Work Session | Work Session | 1 | 1 |

Additional bodies may be present beyond the first page -- full enumeration deferred to first adapter run.

## 3. Search / Query Capabilities

Standard Legistar OData v3 surface (identical shape to Polk FL, Martin FL, Indian River FL tenants documented elsewhere in `docs/api-maps/`):

- `GET /v1/baldwincountyal/bodies` -- body list.
- `GET /v1/baldwincountyal/events` -- meeting events with `$filter=EventDate ge datetime'...' and EventBodyName eq '...'`.
- `GET /v1/baldwincountyal/events/{EventId}/eventitems` -- per-meeting agenda items.
- `GET /v1/baldwincountyal/matters` -- legislative matters.
- `GET /v1/baldwincountyal/votes` -- votes (where published; varies per-tenant).

Page size via `$top`; OData `$orderby`, `$filter`, `$select` supported. Same `CommissionRadar/1.0` user-agent + 0.5s inter-request delay that the existing Legistar client uses is appropriate.

## 4. Field Inventory

Standard Legistar OData record shape across endpoints:

- **Bodies**: BodyId, BodyGuid, BodyLastModifiedUtc, BodyName, BodyTypeId, BodyTypeName, BodyMeetFlag, BodyActiveFlag, BodySort, BodyDescription, BodyNumberOfMembers, BodyContact* fields.
- **Events**: EventId, EventGuid, EventBodyId, EventBodyName, EventDate, EventTime, EventLocation, EventAgendaFile, EventMinutesFile, EventVideoPath, EventInSiteURL, EventAgendaStatusName, etc.
- **EventItems**: EventItemId, EventItemAgendaNumber, EventItemTitle, EventItemActionName, EventItemActionText, EventItemConsent, EventItemMatterStatusName, etc.
- **Matters**: MatterId, MatterFile, MatterName, MatterTypeName, MatterStatusName, MatterBodyName, MatterIntroDate, MatterAgendaDate, MatterRequester, etc.
- **Votes**: VoteId, VoteLastModifiedUtc, VotePersonName, VoteValueName, VoteResult, etc.

(Full field inventory matches the Polk FL Legistar doc; see that file for the 40+ fields enumerated in the same shape.)

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No CR jurisdiction YAML, no config row. An adapter would reuse the existing repo Legistar client and configure two bodies (Commission Regular + Work Session) -- same pattern as Polk FL's dual-body extraction.

## 6. Auth Posture / Bypass Method

Anonymous HTTP GET. No API key, no session cookie, no user-agent gating. Tenant slug `baldwincountyal` is the hostname-derived API client identifier.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Bodies | NO (config gap) |
| Events | NO |
| EventItems | NO |
| Matters | NO |
| Votes | NO (depending on tenant publication setting) |
| Attachments (PDF agendas) | NO |

Full surface available; adapter config is the only gap.

## 8. Known Limitations and Quirks

- `VoteFlag` enablement is per-tenant and per-body. Baldwin's live publication status for votes is **unverified** at probe time -- the `/votes` endpoint returns 200 but the number of published vote rows may be zero.
- Legistar events API requires ISO `datetime'YYYY-MM-DDTHH:mm:ss'` literals in `$filter` expressions; the existing client handles that formatting.
- `EventAgendaFile` / `EventMinutesFile` are URLs to InSite-hosted PDFs; downloads go through the legistar.com host, not webapi.legistar.com.
- Non-disclosure state (deeds) is unrelated to CR.
- Boards/committees beyond the two primary bodies may exist (planning commission, BZA, subcommittees) -- enumerate via `/bodies` on first adapter run.

Source of truth: `county-registry.yaml` (baldwin-al L585-598, BI-only), Baldwin site agenda link at `https://baldwincountyal.gov/`, live probe `https://webapi.legistar.com/v1/baldwincountyal/bodies`, `docs/api-maps/polk-county-legistar.md` (platform reference).
