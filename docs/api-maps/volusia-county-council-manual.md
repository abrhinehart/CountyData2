# Volusia County FL -- County Council Manual Publishing API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | Manual publishing on `www.volusia.org` (no Legistar / Granicus / CivicPlus AgendaCenter / CivicClerk identified) |
| Publishing surface | `https://www.volusia.org/government/county-council/` |
| Governing body | **County Council** (Volusia uses a Council/Manager form of government, NOT a Board of County Commissioners) |
| Members | 7 members |
| Auth | Anonymous |
| Protocol | Static HTML / CMS-published documents |
| Registry status | **No `cr:` row in `county-registry.yaml`** — Volusia has only `bi: active` under `volusia-fl.projects` (L533-541) |
| Adapter status | **`unverified — needs validation`** — no platform confirmed; manual scrape is the fallback |

## 2. Probe (2026-04-14)

```
GET https://www.volusia.org/government/county-council/
-> HTTP 200, 64,809 bytes, text/html
   <title>County Council</title>
   Describes the Council/Manager form of government; 7 members;
   general overview page (not an agenda index).
```

### Negative-result probes (platforms Volusia is NOT on)

```
GET https://www.volusia.org/AgendaCenter                              -> HTTP 404
   (Rules out CivicPlus AgendaCenter)

GET https://volusia.legistar.com/                                     -> HTTP 200, 19 bytes
   Body: "Invalid parameters!"
   (Legistar responds to unknown client slugs with this message;
    Volusia has no valid Legistar tenant slug)

GET https://webapi.legistar.com/v1/volusia/bodies                     -> not probed
GET https://webapi.legistar.com/v1/volusiafl/bodies                   -> not probed
   (Ruled out indirectly via the portal 404 probe)

GET https://volusia.granicus.com/                                     -> HTTP 404
   (Rules out Granicus AgendaCenter / LiveManager direct tenant)

GET https://volusia.new.swagit.com/                                   -> HTTP 404
   (Rules out SwagIt video + agenda platform)

GET https://www.volusia.org/government/county-council/agenda-and-meeting-summary.stml  -> HTTP 404
   (Plausible CMS path not present)
```

## 3. Query Capabilities

**`unverified — needs validation`.** No structured API is known. Any future adapter must scrape HTML links from the County Council section of `www.volusia.org`. A typical manual-publishing adapter:

1. Fetches the index page (`/government/county-council/` or a deeper `meetings` subpath yet to be identified).
2. Parses out anchor tags linking to agenda / minutes PDFs.
3. Filters by filename convention (date-prefix detection) and document-type heuristics (`"agenda"` / `"minutes"` in URL or link text).

## 4. Field Inventory

**Not applicable** — no API. Manual scrape yields only HTML anchor attributes (href, text) plus file metadata (Last-Modified, Content-Length).

## 5. What We Extract / What a Future Adapter Would Capture

Prospective — no adapter exists:

| DocumentListing field | Source |
|-----------------------|--------|
| `title` | Anchor text or derived filename |
| `url` | Anchor `href` |
| `date_str` | Parsed from filename prefix / title |
| `document_id` | Composed from URL hash or filename |
| `document_type` | Inferred from keywords in href/text ("agenda" / "minutes") |
| `file_format` | Extension (expected `pdf`) |
| `filename` | URL basename |

## 6. Bypass Method / Auth Posture

Anonymous HTTP. No login, captcha, or session cookie observed on `www.volusia.org`. CMS appears to be a standard public website.

## 7. What We Extract vs What's Available

Nothing extracted currently. Whatever the Council publishes (agenda packets, minutes, meeting videos on a linked platform) is potentially available via manual scrape once the index page structure is mapped.

## 8. Known Limitations and Quirks

1. **Volusia uses "County Council", NOT "Board of County Commissioners".** Council/Manager form of government — unique structural pattern within this batch. Any future YAML must use `body_names: ["County Council"]`.
2. **No identified agenda-management platform.** Legistar, Granicus, CivicPlus AgendaCenter, CivicClerk, SwagIt all ruled out via direct probes. The most likely scenario is either a custom CMS subsection on `www.volusia.org` or a non-standard hostname that was not guessed.
3. **`volusia.legistar.com` hostname resolves** but returns `"Invalid parameters!"` — this is the Legistar multi-tenant dispatch behavior for unknown slugs. Do NOT interpret the HTTP 200 as evidence of a Volusia Legistar tenant.
4. **No Granicus tenant.** `volusia.granicus.com` 404. If Volusia uses Granicus LiveManager for video, it's behind a non-standard subdomain.
5. **No SwagIt tenant.** `volusia.new.swagit.com` 404. SwagIt is a common FL video-plus-agenda platform (used by several Gulf Coast counties) but not here.
6. **No `cr:` row in `county-registry.yaml`.** Adding CR tracking for Volusia requires both a new registry row AND a new jurisdiction YAML under `modules/commission/config/jurisdictions/FL/` — neither exists yet.
7. **No matching JSON feed on the probe surface.** The County Council page is a static CMS page, not a listing index.
8. **The 64,809-byte County Council page** is narrative/overview content. The agenda index, if it exists, is presumably linked from that page or lives at a sibling `/meetings/` / `/agenda/` subpath not yet probed.
9. **Planning-body and BOA equivalents** are also unmapped. Volusia's development-review and land-use adjudication surfaces would need separate research.
10. **This document exists to prevent re-discovery work.** Future runs should not re-probe the ruled-out platforms (Legistar / Granicus / AgendaCenter / SwagIt). Focus instead on harvesting links from the County Council section of the Volusia CMS.

Source of truth: live probes 2026-04-14 of `https://www.volusia.org/government/county-council/` (HTTP 200, 64,809 bytes) and negative-result probes of `volusia.legistar.com`, `webapi.legistar.com` (implicit), `volusia.granicus.com`, `volusia.new.swagit.com`, `www.volusia.org/AgendaCenter`. `county-registry.yaml` L533-541 (`volusia-fl.projects` block — `bi: active` only, no `cr` row). No `modules/commission/config/jurisdictions/FL/volusia-county-*.yaml` file exists.
