# Montgomery County AL -- CivicWeb (iCompass) Commission API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Montgomery County Commission (state capital county, unincorporated + countywide bodies) |
| Platform | CivicWeb Portal (iCompass Technologies; Granicus-owned product line) |
| Portal URL | `https://mc-ala.civicweb.net/Portal/` |
| Auth | Anonymous public read |
| Protocol | ASP.NET Web Forms (legacy iCompass; no public REST / OData API advertised) |
| Registry entry | `county-registry.yaml` L600-613 has BI only; **no `cr:` block** |
| Adapter reuse | None existing for CivicWeb in this repo (new vendor family for CR; other CR platforms covered: Legistar, Granicus/IQM2, CivicClerk, CivicPlus) |

CivicWeb is iCompass's agenda-management portal, acquired by Granicus in 2018. Branding on Montgomery's tile set is consistent with iCompass heritage (Welcome / Live Stream / Search / Subscribe / Meeting Archives / Attendance & Voting tiles).

## 2. Probe (2026-04-14)

```
GET https://mc-ala.civicweb.net/Portal/
-> HTTP 200  (CivicWeb Portal; title "Montgomery County - Home"; iCompass asset paths like /content/portal/Tiles/...; bundled jQuery + iCompass tech support email "developers@icompasstech.com")
```

Portal is live, public, and branded for Montgomery County. Tile layout confirms CivicWeb feature surface: calendar / live stream / library search / subscription / meeting archives / attendance-voting. The county's own website (`www.mc-ala.org` -- Akamai-shielded) links out to this portal for agendas and minutes.

## 3. Search / Query Capabilities

CivicWeb Portal exposes:

- **Calendar** (`MeetingSchedule.aspx`): upcoming and past meetings by date.
- **Meetings** (`MeetingTypeList.aspx`): enumerate by body / meeting type.
- **Virtual Library** (`VirtualLibrary.aspx`): document search (agendas, minutes, reports) -- keyword + date + meeting filters.
- **Attendance & Voting** (`VotingRecords.aspx`): member attendance + roll-call votes.
- **Meeting detail pages**: Agenda item list + attachments + (if published) votes + minutes PDFs.
- **Live stream** (`Video.aspx`): embedded video player, typically backed by Granicus streaming.

No public REST / OData API documented. Scraping is HTML / form-post, similar in shape to IQM2 but with CivicWeb-specific URL paths.

## 4. Field Inventory

Expected (CivicWeb standard Portal shape):

- Meeting: MeetingId (often GUID or integer), Meeting Type / Body name, date/time, location, status (scheduled / held / cancelled).
- Agenda items: item number, title, category, body text.
- Attachments: PDF URLs (agendas, minutes, backup materials).
- Voting records: member, meeting, motion, vote value (Yes/No/Abstain/Absent/Recuse).
- Attendance: member, meeting, attended (Y/N).

Exact field keys and URL querystring shapes require a live crawl -- `unverified -- needs validation` for schema specifics.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No CR config; no CivicWeb adapter in this repo. A future adapter would:

1. Pull meeting list via Calendar / MeetingSchedule paginated HTML.
2. For each meeting, fetch detail + agenda + attachments + votes.
3. Populate the standard CR model (Meeting -> AgendaItem -> Vote).

Voting publication is iCompass-tenant-configurable -- Montgomery's tile set includes "Attendance & Voting", so votes appear to be published (presumed; per-body confirmation pending).

## 6. Auth Posture / Bypass Method

Anonymous public read. Portal greets as "Public User" by default. No login gate for search / calendar / detail pages / votes.

## 7. What We Extract vs What's Available

Zero extraction currently. Full CivicWeb public surface is available (meetings, items, attachments, votes, attendance). Adapter work is the only gap.

## 8. Known Limitations and Quirks

- **CivicWeb / iCompass is a new vendor family** for CR in this repo -- no existing adapter to reuse. Jefferson and Madison (same batch) use IQM2/Accela; Baldwin (same batch) uses Legistar. Montgomery is alone on CivicWeb.
- No REST/OData API -- HTML scraping only. ViewState is present but lighter than ACA; brittleness is moderate.
- **County commission ONLY is in scope.** The City of Montgomery City Council is a separate governing body with its own agenda platform (and is the dominant population center of the county since Montgomery is the state capital). **City Council is explicitly out of scope for this CountyData2 CR doc.** Smaller Montgomery County municipalities (Pike Road, etc.) likewise have separate city-level bodies that are out of scope.
- Live-stream video hosting is typically Granicus (since iCompass is now a Granicus brand) -- video URLs may reference both `mc-ala.civicweb.net` and a Granicus CDN endpoint.
- The main county website is Akamai-shielded; CivicWeb subdomain is NOT -- direct scraping should work against `mc-ala.civicweb.net` even when the main site rejects the same UA.
- Non-disclosure (deeds) is unrelated to CR.

Source of truth: `county-registry.yaml` (montgomery-al L600-613, no cr: block), live probe `https://mc-ala.civicweb.net/Portal/`, archived Montgomery County Commission page (web.archive.org capture of `www.mc-ala.org/government/county-commission/county-commission-agendas`).
