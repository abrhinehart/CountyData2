# Jefferson County AL -- IQM2 (Accela Meeting Portal) API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Jefferson County Commission (Birmingham metro) |
| Platform | IQM2 / Accela Meeting Portal (MinuteTraq heritage; formerly IQM2 Inc.) |
| Portal URL | `https://jeffersoncountyal.iqm2.com/Citizens/Default.aspx` |
| Auth | Anonymous public read |
| Protocol | ASP.NET Web Forms + OpenSearch XML descriptor (no REST/OData API) |
| Registry entry | **Not present** -- `county-registry.yaml` jefferson-al has BI only |
| CR adapter | None currently -- no existing `commission_radar` adapter for IQM2 in this repo |
| Scope | Jefferson County Commission ONLY |

**Out-of-scope: City of Birmingham City Council.** Birmingham City Council is a separate governing body with its own agenda platform; it is **not** covered by this doc. Only Jefferson County Commission meetings (pre-commission, regular commission, Bessemer-division meetings) are tracked under this CR surface.

## 2. Probe (2026-04-14)

```
GET https://jeffersoncountyal.iqm2.com/Citizens/Default.aspx
-> HTTP 200  (IQM2 Citizens landing, ~40 KB; OpenSearch descriptor `/Services/GetFederatedSearch.aspx` referenced; domain cookie `iqm2.com`)
```

This returns a live IQM2 Citizens page (unlike Madison's IQM2 subdomain, which returns ErrorPage.aspx). Confirmed live by OpenSearch metadata tag, IQM2 script bundle, and `domain: "iqm2.com"` cookie config.

The county main-site page `jccal.org` links out to this portal for "Commission Minutes & Agendas" and "Agendas and Minutes" from multiple nav locations, plus the calendar shows active commission + pre-commission + Bessemer-division meetings (2026 schedule seen on the main site).

## 3. Search / Query Capabilities

IQM2 / Accela Meeting Portal Citizens side:

- Calendar list: `/Citizens/Calendar.aspx` (meeting-type-filtered)
- Meeting detail: `/Citizens/Detail_Meeting.aspx?ID={MeetingID}`
- Split-view agenda: `/Citizens/SplitView.aspx?Mode=Agenda&MeetingID={MeetingID}`
- Federated search: `/Services/GetFederatedSearch.aspx` (OpenSearch XML declared, full query shape not probed here)

No REST / OData. HTML-parse only. Attachments (PDF agendas + minutes + exhibits) linked from the SplitView and Detail_Meeting pages.

## 4. Field Inventory

Expected (standard IQM2 citizens-side shape):

- Meeting: ID, meeting type / body name, date, time, status.
- Agenda items: item number, title, item type (e.g., Resolution, Ordinance), body text.
- Attachments per item: PDF URLs, names.
- Vote roll-ups (where the county publishes them -- not all IQM2 customers expose Votes publicly).

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No CR jurisdiction-YAML, no `cr_jurisdiction_config` row. A future IQM2 adapter would parse the calendar + detail + splitview pages, emit meeting + agenda-item + vote records through the standard CR model surface.

Relevant bodies (from the `jccal.org` calendar):

- Jefferson County Commission (regular meetings, Tuesdays in Birmingham chambers)
- Pre-Commission Meeting (work session, day before regular)
- Commission Meeting - Bessemer (periodic meetings at the Bessemer Division)

## 6. Auth Posture / Bypass Method

Fully anonymous public read. No login, no rate-limit observed on a single landing-page probe.

## 7. What We Extract vs What's Available

Zero extraction currently -- CR config gap. Full surface (meetings, items, attachments, votes-if-published) is accessible once an IQM2 adapter is written.

## 8. Known Limitations and Quirks

- No REST API -- HTML-parse only. ViewState is minimal on the Citizens side (compared to ACA), so brittleness is lower than Accela Citizen Access.
- Votes publication is agency-dependent. Whether Jefferson County publishes roll-call votes on IQM2 needs confirmation on first crawl; the Citizens skin typically exposes votes when enabled, but agencies can hide them.
- **Two meeting locales: Birmingham + Bessemer.** Meeting type filters should distinguish. The `Commission Meeting - Bessemer` entries visible in the calendar run less frequently than Birmingham regulars.
- **Out of scope: City of Birmingham City Council** (separate body with its own platform). Other municipal councils inside Jefferson County (Hoover, Vestavia Hills, Mountain Brook, Homewood, Bessemer city-proper) are also out of scope -- this CR surface covers the county commission only.
- Non-disclosure (deeds) is unrelated to CR data.

Source of truth: `county-registry.yaml` (jefferson-al L571-583, no cr: block), live probe `https://jeffersoncountyal.iqm2.com/Citizens/Default.aspx`, county-site links from `https://www.jccal.org/`.
