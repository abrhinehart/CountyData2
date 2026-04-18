# Lake Hamilton, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://www.townoflakehamilton.com/` (Town of Lake Hamilton, within Polk County, FL). One-file scope: Town of Lake Hamilton only — Polk County is mapped separately.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.townoflakehamilton.com/` is server-rendered ASP.NET (CivicPlus CivicEngage); the only JavaScript XHR present is the standard CivicPlus `/antiforgery` bootstrap and Azure App-Insights telemetry. No SPA hydration markers (`__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__`) are present on the CMS. The iWorQ portal (`townoflakehamilton.portal.iworq.net`) is a Laravel-rendered server-side page with a reCAPTCHA widget — it is safe for curl-only probing for shell/shape data but row-level data requires captcha solve (see iWorQ deep probe below). The Municode Library page at `library.municode.com/fl/lake_hamilton` is Angular — content not re-enumerated this run (see ⚠️ GAP under Coverage Notes).

## Summary

- **Jurisdiction:** Town of Lake Hamilton (within Polk County, FL).
- **Town website platform:** CivicPlus CivicEngage. Classic numeric-ID URL pattern (`/{numeric-id}/{slug}`, e.g. `/1205/Community-Development`). Canonical host `www.townoflakehamilton.com`. Footer confirms `Government Websites by CivicPlus®`. Same family as Haines City (`haines-city-fl.md`) and Davenport / Dundee — reuses the same `/RSSFeed.aspx`, `/CalendarICS.aspx`, `/DocumentCenter`, `/ArchiveCenter`, `/AgendaCenter`, `/Jobs.aspx`, `/Bids.aspx`, `/antiforgery`, `/sitemap.xml`, `/robots.txt` shape.
- **Commission surface:** **No external commission platform** (no eScribe, no Legistar, no CivicClerk, no Municode Meetings). Town Council and Boards/Commissions are served directly from the CivicPlus CMS at `/1193/Agendas-Minutes` with packet PDFs linked from `ArchiveCenter/ViewFile/Item/{id}` and `DocumentCenter/View/{id}/{slug}` handlers. This is a single-CMS commission footprint, typical of very small FL towns.
- **Permit surface:** iWorQ at `townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600`. Laravel-backed tenant, reCAPTCHA v3 gate. **Key deviation from Haines City:** on this tenant, anonymous date-range search (`searchField=permit_dt_range`) at fid=600 returns the page shell but **0 data rows** — all row data is fully captcha-gated. However, **fid=601** (a sibling permit category on the same tenant) DOES expose detail-URL anchors for `permit_dt_range` queries (30 detail links across a 365-day window, 15 unique permits on page 1). See ⚠️ GAP — fid-dependent behavior section. The fixture-stage `LakeHamiltonAdapter` currently points at fid=600 and is therefore likely non-functional for anonymous bulk extraction. **Recommendation:** adapter should be re-targeted to fid=601 (or operate via hybrid-captcha on fid=600). Anonymous fid=601 detail pages are also thinner than Haines City's — ~8.6 KB per permit here versus Haines City's ~67 KB at fid=600 — consistent with a smaller tenant config and partially captcha-gated per-permit fields (see §4.2 Notes).
- **Code of ordinances:** Municode Library at `library.municode.com/fl/lake_hamilton/codes/code_of_ordinances`. Angular SPA — client ID not resolved in this curl-only pass. ⚠️ GAP: re-enumerate with a browser to capture `api.municode.com/codes/{client_id}/nodes`.
- **Utility billing surface:** `lakehamilton.authoritypay.com` (Authority Pay — payment-only outbound portal). No on-site utility-billing surface.
- **Property appraiser / parcel data:** Polk County Property Appraiser at `polkpa.org` (out-of-hostname; mapped under Polk County, not here).
- **Polk County Clerk eRecording:** linked from Lake Hamilton portal (Notice of Commencement flow) — out-of-hostname.
- **No ArcGIS / FeatureServer / MapServer endpoints** on the Lake Hamilton footprint. Parcel GIS rides Polk County services.
- **No Bids** actively listed (`Bids.aspx` has "There are no" empty state). Jobs has 3 open positions at survey time.
- **robots.txt stance:** Both CMS and iWorQ disallow broad crawl — CMS enumerates specific admin/search/map paths; iWorQ disallows `/`. Per refined §3.2, treated as operational-risk signal only. Mapping pass was low-volume (~132 requests at 1 req/sec) and observed 0 rate-limit events.
- **Total requests this run:** 132. Cap is 2000. No 429s, no captcha challenges actually invoked (the reCAPTCHA on iWorQ was observed but not solved).

## Platform Fingerprint

| Host | Platform | Fingerprint |
|---|---|---|
| `www.townoflakehamilton.com` | **CivicPlus CivicEngage** | `/{numeric-id}/{slug}` URL pattern; `ASP.NET_SessionId` + `CP_IsMobile` cookies; CSP `frame-ancestors` includes `platform.civicplus.com`, `account.civicplus.com`, `analytics.civicplus.com`, `*.granicus.com`; CivicPlus footer (`Government Websites by CivicPlus®`); `/antiforgery` bootstrap JSON endpoint; `/RSSFeed.aspx?ModID=…` feed index; `cpDomain` = `https://cp-civicplusuniversity2.civicplus.com`. Azure App-Insights instrumentation key `1cde048e-3185-4906-aa46-c92a7312b60f` present. Google Tag Manager GTM-K73C5PS. |
| `townoflakehamilton.portal.iworq.net` | **iWorQ** | nginx/1.18.0 (Ubuntu); Laravel backend (`XSRF-TOKEN` + `iworq_api_session` encrypted cookies, `eyJpdi…` envelopes); Bootstrap 3.3.6 + jQuery UI 1.13.2 chrome; reCAPTCHA v3 widget (`data-sitekey="6Les_AYkAAAAACw9NzcxkcDVfvExxeyw2KS1cao_"`); tenant prefix `LAKEHAMILTON` (case-sensitive — lowercase tenant returns 404); `data-portal-id="368"` on tenant root. permit list at `/LAKEHAMILTON/permits/{fid}` where `fid ∈ {600, 601}` observed as valid categories. |
| `library.municode.com/fl/lake_hamilton` | **Municode Library** | Already in `_platforms.md`. Angular SPA; client ID not discoverable via curl (⚠️ GAP). |
| `lakehamilton.authoritypay.com` | **Authority Pay** | Outbound utility-payment portal. Not deep-mapped (out-of-hostname; no public data surface). |

No new platforms observed this run (CivicPlus + iWorQ + Municode + Authority Pay all already documented or already known outbound). Authority Pay is not yet in `_platforms.md` but is a payment-only outbound portal — adding is deferred to a housekeeping task.

---

## APIs

### /antiforgery

#### Antiforgery token

- **URL:** `https://www.townoflakehamilton.com/antiforgery`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Issues a CivicPlus CSRF token used by any form POST back to the CivicEngage site.
- **Response schema:**
  ```
  {
    "token": "string"
  }
  ```
- **Observed parameters:** none
- **Probed parameters:**
  - `unverified` — only observed as a parameterless GET.
- **Pagination:** `none`
- **Rate limits observed:** none observed at ~1 req/sec
- **Data freshness:** real-time (per-session)
- **Discovered via:** Inline `getAntiForgeryToken` script in the home-page HTML that bootstraps CSRF tokens into every CivicEngage form POST.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/antiforgery'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-antiforgery.json`
- **Notes:** Token is submitted as `__RequestVerificationToken` on same-origin form POSTs. Not useful for data extraction on its own — it gates any POST-driven search/contact forms.

### /sitemap.xml

#### Sitemap index

- **URL:** `https://www.townoflakehamilton.com/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full URL enumeration for every server-rendered page on the CivicEngage site (100 entries).
- **Response schema:**
  ```
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
      <loc>url</loc>
      <lastmod>YYYY-MM-DD</lastmod>
      <changefreq>string</changefreq>
    </url>
  </urlset>
  ```
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none` — all 100 entries inline in a single document.
- **Rate limits observed:** none
- **Data freshness:** Updated on CMS publish (entries with `lastmod` ranging from 2019 to 2025).
- **Discovered via:** Referenced in `/robots.txt`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/sitemap.xml'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-sitemap.xml`
- **Notes:** Canonical drift-target list. Only 100 URLs — one of the smallest CivicPlus tenants observed in Polk County.

### /robots.txt

#### Robots directives

- **URL:** `https://www.townoflakehamilton.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** `text/plain` robots.txt.
- **Response schema:** key–value records.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static.
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/robots.txt'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-robots.txt`
- **Notes:** Blocks Baiduspider and Yandex entirely. For `*`: disallows `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx`. Siteimprove crawlers rate-limited to 20s. Same ruleset as the Haines City tenant (shared CivicPlus default template). `/RSSFeed.aspx` is allowed; `/RSS.aspx` (singular, capitalized) is blocked.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed on this tenant: `1` (News Flash), `51` (Blog — empty), `53` (Department Photo / Banner), `58` (Calendar), `63` (Alert Center), `64` (Real Estate Locator — skeleton), `65` (Agenda Creator — empty), `66` (Jobs — actively populated, 3 postings), `76` (Opportunities — actively populated), `92` (CivicMedia — skeleton). Each optionally accepts a `CID` (category) filter. The canonical index is `/rss.aspx` (HTML; see Scrape Targets).

#### News Flash RSS

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** News Flash items, optionally filtered by category.
- **Response schema:**
  ```
  <rss version="2.0">
    <channel>
      <title>string</title>
      <link>url</link>
      <lastBuildDate>rfc822-date</lastBuildDate>
      <description>string</description>
      <language>string</language>
      <item>
        <title>string</title>
        <link>url</link>
        <pubDate>rfc822-date</pubDate>
        <description>string (may be html)</description>
        <guid isPermaLink="bool">string</guid>
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:**
  - `ModID` (int, required) — `1` for News Flash.
  - `CID` (string, optional) — category filter. Observed values: `All-newsflash.xml`, `Lake-Hamilton-News-1`.
- **Probed parameters:** `unverified`
- **Pagination:** `none` — RSS returns a trailing window.
- **Rate limits observed:** none at 1 req/sec.
- **Data freshness:** publishes with CMS updates. Skeleton-only on this tenant at survey time (345 bytes).
- **Discovered via:** `/rss.aspx` HTML index.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=1'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid1.xml`
- **Notes:** Skeleton at survey time — no current News Flash items.

#### Blog RSS

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog feed (empty — module not used).
- **Response schema:** RSS 2.0 (same as News Flash).
- **Observed parameters:** `ModID=51`, `CID=All-blog.xml`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty (337-byte skeleton).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=51&CID=All-blog.xml'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid51.xml`
- **Notes:** Drift sentinel.

#### Department Photo / Banner RSS (ModID 53)

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Photo/banner items. 12 items returned unfiltered.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=53` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Sample-Parks-2`, `United-States-Armed-Services-3`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** irregular (curator-driven).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid53.xml` (truncated to 5 of 12 items)
- **Notes:** Low BI/PT/CR/CD2 signal; documented for completeness.

#### Calendar RSS

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming calendar events (events module, separate from any external meeting platform).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=58` (int, required)
  - `CID` (string, optional) — observed: `All-calendar.xml`, `Main-Calendar-14`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=58&CID=All-calendar.xml'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid58.xml`
- **Notes:** Only 1 calendar category (`Main-Calendar-14`) defined on this tenant — far simpler than Haines City's 18-category footprint. Skeleton-only at survey time (413 bytes).

#### Alert Center RSS (ModID 63)

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Emergency/alert notifications.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=63` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Emergency-alerts-6`, `Water-Notices-5`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** event-driven.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=63&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid63.xml`
- **Notes:** Skeleton at survey time (349 bytes) — no active alerts. `Water-Notices-5` CID suggests tenant ties this feed to the Water Department.

#### Real Estate Locator RSS (ModID 64)

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Economic-development property listings — skeleton only on this tenant (CID catalog not published in `/rss.aspx` index).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=64`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty skeleton (361 bytes).
- **Discovered via:** Probed based on CivicPlus platform default, not listed in `/rss.aspx` index — module may be disabled.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=64'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid64.xml`
- **Notes:** ⚠️ GAP: module appears inactive on this tenant — worth re-probing quarterly.

#### Agenda Creator RSS (ModID 65)

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Empty skeleton — agendas are served via CivicPlus AgendaCenter pages + DocumentCenter PDFs, not this feed.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=65`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty (348 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=65&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid65.xml`
- **Notes:** Drift sentinel.

#### Jobs RSS

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Open positions, 51 KB at survey time (3 active postings + history).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=66` (int, required)
  - `CommunityJobs` (bool, optional) — observed: `False`.
  - `CID` (string, optional) — observed: `All-0`, `Full-Time-Positions-99`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** posts/deletes with HR postings.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?CommunityJobs=False&ModID=66&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid66.xml` (truncated to 5 items)
- **Notes:** At survey time: Police Officer, Utility GIS Technician, Utility Maintenance Technician II (JobIDs `Police-Officer-9`, `Utility-GIS-Technician-15`, `Utility-Maintenance-Technician-II-14`).

#### Opportunities RSS (ModID 76)

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Opportunity postings (17.9 KB at survey time — actively populated with 50 items).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=76`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** active.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=76&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid76.xml` (truncated to 5 of 50 items)
- **Notes:** Likely analogous to the "Opportunities" module (RFP/RFQ/civic engagement) observed on Haines City. This is the procurement flow — `Bids.aspx` is empty on this tenant.

#### CivicMedia RSS

- **URL:** `https://www.townoflakehamilton.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CivicMedia video/media feed — empty on this tenant.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=92`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty (343 bytes).
- **Discovered via:** Platform-default probe; not listed in `/rss.aspx` index.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/RSSFeed.aspx?ModID=92'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-rssfeed-modid92.xml`
- **Notes:** Drift sentinel.

### /common/modules/iCalendar/iCalendar.aspx

#### Calendar iCalendar feed

- **URL:** `https://www.townoflakehamilton.com/common/modules/iCalendar/iCalendar.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** iCalendar (`.ics`) feed of town events. 2.7 KB at survey time (1 event in window).
- **Response schema:**
  ```
  BEGIN:VCALENDAR
  PRODID:iCalendar-Ruby
  VERSION:2.0
  X-WR-TIMEZONE:America/New_York
  BEGIN:VTIMEZONE
    ...
  END:VTIMEZONE
  BEGIN:VEVENT
    UID:string
    DTSTART:YYYYMMDDTHHMMSS
    DTEND:YYYYMMDDTHHMMSS
    SUMMARY:string
    DESCRIPTION:string
    LOCATION:string
  END:VEVENT
  END:VCALENDAR
  ```
- **Observed parameters:**
  - `catID` (int, required) — category ID. Observed `14` (Main Calendar).
  - `feed` (string, required) — observed `calendar`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/Calendar.aspx` page's "iCal" subscribe link.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-calendar-ics-cid14.ics`
- **Notes:** `PRODID:iCalendar-Ruby` reveals the CivicPlus calendar module is Ruby-generated (not .NET). Same pattern observed on Haines City and Dundee.

### /DocumentCenter

#### Document binary download

- **URL:** `https://www.townoflakehamilton.com/DocumentCenter/View/{documentId}/{slug}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary PDF (or other document MIME) keyed by `documentId` + slug + `bidId` query.
- **Response schema:** binary stream. Observed `application/pdf` (173 KB for Building Permit Application form, ID 258).
- **Observed parameters:**
  - `documentId` (int, path segment, required) — observed range 255–467 (24 unique IDs harvested across town pages).
  - `slug` (string, path segment, required) — URL-slugged filename (e.g. `Building-Permit-Application-8th-Edition-PDF`).
  - `bidId` (string, query, optional) — empty string accepted; unlike Haines City, **omitting `bidId` still returns HTTP 200** on this tenant (tested on documentId=258 without `bidId=` → 200 PDF). Documented parameter for adapter parity but not strictly required here.
- **Probed parameters:**
  - `bidId` omitted → HTTP 200 (tenant is more permissive than Haines City).
  - `/DocumentCenter/View/{documentId}` (no slug) → `unverified` (not tested this run).
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-upload.
- **Discovered via:** `<a href="/DocumentCenter/View/N/slug">` on Building-Permit, Code-Enforcement, Town-Council, Forms-Permits, Community-Development, Planning-Zoning, Business-Tax-Receipts, Lien-Search-Request pages.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/DocumentCenter/View/258/Building-Permit-Application-8th-Edition-PDF' -o bpa.pdf
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-documentcenter-view-258.bin` (173 KB PDF — Building Permit Application 8th Edition).
- **Notes:** Observed IDs this run: 255, 258, 259, 294, 349, 358, 359, 360, 361, 362, 368, 369, 370, 371, 372, 380, 381, 464, 467, 364. Sparse numeric space, non-monotonic — canonical discovery is by scraping parent pages. No structured index — a DocumentCenter JSON/XML endpoint was probed (`/DocumentCenter`, `/DocumentCenterContent`, `/DocumentCenterContent/0`) and all returned the CivicEngage HTML shell (React-rendered; data is client-fetched via a bundle in `/DocumentCenter/Assets/Scripts/docCenterFrontendAndRelatedBidAndJobsApp.react.js`). ⚠️ GAP: Document inventory not enumerable without JS.

### /ImageRepository/Document

#### Binary image/document handler

- **URL:** `https://www.townoflakehamilton.com/ImageRepository/Document`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary blob keyed by numeric `documentID`. Content-Type varies per asset (observed `image/png`, 16.8 KB for documentID=116).
- **Response schema:** binary stream.
- **Observed parameters:**
  - `documentID` (int, required) — opaque asset ID. Observed in home-page HTML: 116, 118, 119.
- **Probed parameters:**
  - `unverified` — canonical discovery is via scraping `<img>` tags.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-asset CMS publish.
- **Discovered via:** `<img src="/ImageRepository/Document?documentID=N" />` tags on home page.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/ImageRepository/Document?documentID=116' -o img.png
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-imagerepository.bin` (PNG, 16.8 KB).
- **Notes:** Parallel to `DocumentCenter/View/`.

### /ArchiveCenter/ViewFile/Item

#### Archive document binary

- **URL:** `https://www.townoflakehamilton.com/ArchiveCenter/ViewFile/Item/{archiveItemId}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary PDF of an archived document (meeting minutes, resolutions, or ordinance packets by context).
- **Response schema:** `application/pdf` binary stream.
- **Observed parameters:**
  - `archiveItemId` (int, path segment, required) — observed: 47, 48 (from `Archive.aspx?AMID=36`).
- **Probed parameters:**
  - `unverified` — canonical discovery is via `Archive.aspx?AMID=N` pages, which themselves are React-rendered (dynamic; anchors are fetched client-side, see ⚠️ GAP below).
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-publish.
- **Discovered via:** Links in rendered Archive.aspx response (`ADID=47`, `ADID=48`).
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/ArchiveCenter/ViewFile/Item/47' -o arc47.pdf
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-archive-viewfile-47.bin` (PDF).
- **Notes:** `Archive.aspx?ADID={id}` is the HTML page wrapper; `ArchiveCenter/ViewFile/Item/{id}` is the raw binary handler. Parallel to `DocumentCenter/View/{id}/{slug}` but for Archive-module assets. ⚠️ GAP: no structured index of archive items without JS rendering.

### /AgendaCenter/Search

#### Agenda search (anonymous)

- **URL:** `https://www.townoflakehamilton.com/AgendaCenter/Search/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML search-results page for agenda-center content.
- **Response schema:** HTML.
- **Observed parameters:**
  - `term` (string, query, optional) — free-text search. Observed anchor `?term=` (empty).
- **Probed parameters:**
  - `term=` (empty) → 200; content React-rendered.
- **Pagination:** `unverified`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/AgendaCenter` page.
- **curl:**
  ```bash
  curl 'https://www.townoflakehamilton.com/AgendaCenter/Search/?term='
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-agendacenter-search.html`
- **Notes:** React-rendered; anchors and agenda metadata are fetched client-side. ⚠️ GAP: agenda enumeration requires JS. The tenant may not actually use AgendaCenter — the agendas-minutes page at `/1193/Agendas-Minutes` only links to `Archive.aspx?AMID=36` (ArchiveCenter module), not AgendaCenter.

---

### townoflakehamilton.portal.iworq.net — iWorQ (Permit platform, deep probe)

Laravel-backed iWorQ tenant. `robots.txt` is `User-agent: * / Disallow: /`, but under refined §3.2 framing that is an operational-risk signal, not an access gate — the production adapter (`modules/permits/scrapers/adapters/lake_hamilton.py`, currently fixture-stage) is designed to reach these paths under user-consented sessions. This deep-probe pass is explicitly authorized for drift detection per §9. Pace: 1 req/sec, 41 new anonymous requests, **0 rate-limit events (no 429s, no 5xx)**.

**Major finding vs. Haines City:** On fid=600 (the adapter's current target), anonymous date-range search `searchField=permit_dt_range` returns **0 data rows** (tbody is 53 chars of whitespace). The search-field dropdown at fid=600 only exposes `permitnum_id` (Permit #) and `text2` (Site Address) — no date-range option — and all row rendering is captcha-gated. **In contrast, fid=601** exposes `permit_dt_range` in the dropdown and the anonymous date-range response does return detail-URL anchors (15 unique permit IDs on page 1 for a 365-day window, 3 more on page 2 = ~18 total across the last year). See ⚠️ GAP: fid=600 vs fid=601 below.

#### /robots.txt (iWorQ)

- **URL:** `https://townoflakehamilton.portal.iworq.net/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** robots.txt. `User-agent: *` / `Disallow: /`.
- **Response schema:** text/plain.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static.
- **Discovered via:** Standard location.
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/robots.txt'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-robots.txt`
- **Notes:** Operational-risk signal only (§3.2). Drift-detection pass below proceeded anyway.

#### /LAKEHAMILTON/permits/600 — Permit list / search grid (Building permits)

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600`
- **Method:** `GET`
- **Auth:** `none` for grid shell. **Row data is fully captcha-gated** at this fid — no anonymous bypass (unlike Haines City's fid=600). Laravel session cookies (`XSRF-TOKEN`, `iworq_api_session`) set on first request; `_token` CSRF input in inspection-request form.
- **Data returned:** HTML search page. 5-column table header (`Permit #`, `Permit Type`, `Site Address`, `Description`, `Status`) — simpler than Haines City's 11-column layout. Empty tbody. reCAPTCHA v3 (`data-sitekey="6Les_AYkAAAAACw9NzcxkcDVfvExxeyw2KS1cao_"`, `data-dsn="LAKEHAMILTON"`, `data-fid="600"`). Search dropdown exposes only `permitnum_id` and `text2`.
- **Response schema:** `text/html; charset=UTF-8`. ~305 KB.
- **Observed parameters:**
  - `searchField` (enum) — anonymously visible: `permitnum_id`, `text2`. Captcha-gated options may exist (not enumerated).
  - `search` (string) — free-text search value.
  - `page` (int, 1-indexed) — HTML pagination.
  - `sort` — `permitnum_id | lookup1 | text2 | text3 | mainStatus.statusname` (observed in `<th>` header links).
  - `direction` — `asc | desc`.
- **Probed parameters:**
  - `page=1,2,3,10,100,9999` — all 200, all return the captcha-gated shell (no rows populate anonymously).
  - `per_page=1,100`, `limit=1`, `size=100` — 200, silently ignored.
  - `searchField=permit_dt_range&startDate=...&endDate=...` with 7/30/120/365-day windows — all 200, all return empty tbody (0 detail anchors).
  - `searchField=permitnum_id&search=` (empty) — 200, captcha-gated.
  - `search=building` (no searchField) — 200, captcha-gated.
  - Alternate fid: `1, 500, 602, 700` → 200 "Page Does Not Exist" stub (~3.2 KB); `601` → 200 real (393 KB, date-range-enabled); all other probed fids map to the error stub.
- **Pagination:** `page` query param, 1-indexed. Anonymous responses don't populate a `rel="last"` link on fid=600 because the tbody is empty.
- **Rate limits observed:** none. 41 anonymous requests at 1 req/sec, 0×429, 0×503.
- **Data freshness:** live (when captcha solved).
- **Discovered via:** `portalhome/townoflakehamilton` landing page + adapter source (`modules/permits/scrapers/adapters/lake_hamilton.py:9`).
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/600?searchField=permit_dt_range&startDate=2026-03-17&endDate=2026-04-17&page=1'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-permits-600-landing.html`, `evidence/lake-hamilton-fl-iworq-filter-dt-{7,30,120,365}d.html`, `evidence/lake-hamilton-fl-iworq-pg-page-{1,2,3,10,100,9999}.html`, `evidence/lake-hamilton-fl-iworq-filter-permitnum-empty.html`, `evidence/lake-hamilton-fl-iworq-filter-search-building.html`.
- **Notes:** ⚠️ GAP / adapter misalignment: the fixture adapter `LakeHamiltonAdapter.search_url` points at fid=600, which has no anonymous date-range bypass. **Recommendation:** retarget to fid=601 (see below) or operate via hybrid-captcha pattern.

#### /LAKEHAMILTON/permits/601 — Permit list / search grid (secondary permit category)

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/601`
- **Method:** `GET`
- **Auth:** `none`. **Anonymous date-range search DOES return detail-URL anchors** (15 unique permit IDs on page 1 of a 365-day window, 3 more on page 2 ≈ ~18 total permits in the last year).
- **Data returned:** HTML search grid. Column layout for fid=601 **only exposes a View column anonymously** (`<th>View</th>`) — all data columns (Permit #, Date, etc.) are suppressed until captcha-solve. Row structure: each `<tr>` contains one `<td>` with an `<a href=".../LAKEHAMILTON/permit/601/{permitId}">View</a>`. This means anonymous crawls can harvest permit IDs but not row-level metadata; detail fetches do carry row metadata (Permit Number + Date).
- **Response schema:** `text/html; charset=UTF-8`. 393 KB landing / 478 KB for 365-day filtered.
- **Observed parameters:**
  - `searchField` (enum) — anonymously visible: `permitnum_id`, `permit_dt_range`. More options may exist captcha-gated.
  - `startDate`, `endDate` (`YYYY-MM-DD`) — active when `searchField=permit_dt_range`.
  - `page` (int, 1-indexed) — HTML pagination. 15 permits/page observed.
  - `sort`, `direction` — same columns as fid=600.
- **Probed parameters:**
  - `searchField=permit_dt_range` with 30/365-day windows — 200, populates View anchors.
  - `page=2` on 365d — 200, returns 3 additional permit IDs.
- **Pagination:** `page` query param, 1-indexed. No `rel="last"` anchor on the tested page 1.
- **Rate limits observed:** none.
- **Data freshness:** live.
- **Discovered via:** fid sweep in this mapping pass (`fid=601` observed valid by size delta vs fid=600).
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permits/601?searchField=permit_dt_range&startDate=2025-04-18&endDate=2026-04-18&page=1'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-permits-601.html`, `evidence/lake-hamilton-fl-iworq-601-filter-dt-{30,365}d.html`, `evidence/lake-hamilton-fl-iworq-601-filter-dt-365d-p2.html`.
- **Notes:** **Key production-signal finding:** fid=601 is the date-range-enabled permit category on this tenant, NOT fid=600. Adapter retarget candidate. Combined with the lightweight detail page (below), a no-captcha extraction path exists — it's just a two-level crawl (grid → per-ID detail). Sample IDs: 26183768, 26364341, 26602904, 28186648, 28192748, 28656066.

#### /LAKEHAMILTON/permit/601/{permitId} — Permit detail page

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permit/601/{permitId}` (singular `permit` path — distinct from list `permits`)
- **Method:** `GET`
- **Auth:** `none`. 3 real IDs tested → all 200, all full detail bodies.
- **Data returned:** 8.6 KB HTML detail page. Page title `Permit #{human-permit-number}` (e.g. `#26008` for permitId 28656066). Body contains `Permit Information` card with (at minimum) `Permit Number` and `Permit Date` fields. Additional fields (Description, Property Owner, Contractor, Status) present in row structure but rendered mostly empty for anonymous viewers — the small 8.6 KB size suggests per-permit field visibility is also partially captcha-gated.
- **Response schema:** `text/html`, Laravel-rendered.
- **Observed parameters:**
  - `fid` (path segment, required) — `601` observed valid.
  - `permitId` (path segment, required) — opaque integer in the range 2.5×10⁷–2.9×10⁷ observed (25964609–28656066).
- **Probed parameters:**
  - 3 real `permitId` values → all 200.
  - `permitId=1` (invalid) → 200 "Not Found" stub (6.6 KB, canonical Laravel 404 page).
- **Pagination:** `none`
- **Rate limits observed:** none.
- **Data freshness:** live.
- **Discovered via:** `<a href="…/permit/601/{id}">View</a>` anchors in fid=601 grid responses.
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/permit/601/28656066'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-601-detail-28656066.html` (8.6 KB), `...-28192748.html`, `...-28186648.html`, `evidence/lake-hamilton-fl-iworq-601-detail-invalid.html` (404 stub).
- **Notes:** The detail body for a permit (Permit Number + Permit Date) is accessible without captcha solve. This is a smaller data surface than Haines City's ~67 KB detail page, reflecting a simpler tenant config (Lake Hamilton: 1 FTE permitting department).

#### /LAKEHAMILTON/inspection-request/601/{permitId}/0

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/inspection-request/601/{permitId}/0`
- **Method:** `GET` — returns 6.6 KB Laravel "Not Found" stub on anonymous access for all 3 tested permit IDs.
- **Auth:** `unverified` — returns stub regardless of valid permit ID. Unlike Haines City where GET returns the inspection form, here the route appears gated (possibly captcha or session required upstream).
- **Data returned:** 6.6 KB "Not Found" page.
- **Response schema:** HTML.
- **Observed parameters:** path-bound `fid=601`, `permitId`, trailing `/0`.
- **Probed parameters:** 3 real `permitId` values → all return the Not Found stub.
- **Pagination:** `none`
- **Rate limits observed:** none.
- **Data freshness:** n/a.
- **Discovered via:** Platform-default probe (Haines City pattern).
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/inspection-request/601/28656066/0'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-601-inspreq-28656066.html`
- **Notes:** ⚠️ GAP: inspection-request anonymous route not available on this tenant. Contrast with Haines City where it works. Documented for drift detection — if this starts returning the form, tenant config drifted.

#### /LAKEHAMILTON/scheduler/601/permit/1/{permitId}

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/scheduler/601/permit/1/{permitId}`
- **Method:** `GET` — returns 418-byte meta-refresh redirect back to `https://townoflakehamilton.portal.iworq.net` on anonymous access.
- **Auth:** `unverified` — session-gated.
- **Data returned:** HTML redirect page.
- **Response schema:** HTML.
- **Observed parameters:** path-bound `fid=601`, `permitId`, numeric `1` (permit index).
- **Probed parameters:** 1 real `permitId` → redirect.
- **Pagination:** `none`
- **Rate limits observed:** none.
- **Data freshness:** n/a.
- **Discovered via:** Platform-default probe.
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/scheduler/601/permit/1/28656066'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-601-scheduler-28656066.html`
- **Notes:** Scheduler is session/captcha-gated on this tenant. Drift-detection only.

#### /LAKEHAMILTON/new-permit/600/1861 — Permit application form

- **URL:** `https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/new-permit/600/1861`
- **Method:** `GET` (form render) / `POST` (submission — not exercised in this read-only pass).
- **Auth:** `none` for GET.
- **Data returned:** 39 KB HTML permit-application form. Sections: Property Owner Information, Contractor Information, Sub-Contractor Information, Project Information, Upload Files. CSRF `_token` embedded.
- **Response schema:** HTML.
- **Observed parameters:** path-bound `fid=600`, trailing `1861` (form template ID).
- **Probed parameters:** `unverified` — single known good path.
- **Pagination:** `none`
- **Rate limits observed:** none.
- **Data freshness:** live (form options reflect current tenant config).
- **Discovered via:** `portalhome/townoflakehamilton` landing page.
- **curl:**
  ```bash
  curl 'https://townoflakehamilton.portal.iworq.net/LAKEHAMILTON/new-permit/600/1861'
  ```
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-sub-new-permit.html`
- **Notes:** Write-path; CountyData2 is read-only and does not submit. Documented because it confirms fid=600 is the Building Permit cluster. `1861` is a form-template ID, not a permit ID.

---

## Scrape Targets

### /{numeric-id}/{slug} — CivicPlus page tree

CivicPlus-rendered pages. Each is a server-rendered HTML document — no separate JSON API exposes the page body. These are the primary source of DocumentCenter links, external references, and department/service narrative.

#### Town Council / Agendas-Minutes / Board pages

- **URL:** `https://www.townoflakehamilton.com/1193/Agendas-Minutes`, `/1192/Town-Council`, `/1196/Boards-Commissions`, `/1199/Board-of-Adjustments`, `/1197/Planning-Commission`, `/1198/Parks-Recreation-Advisory-Board`, `/1195/Town-Charter`, `/1194/Town-Council-Rules-of-Procedures`
- **Data available:** Council/board roster, meeting-schedule narrative, links to DocumentCenter PDFs (agendas/minutes/budget), and one link into `Archive.aspx?AMID=36`.
- **Fields extractable:** Body text, DocumentCenter/Archive URLs.
- **JavaScript required:** no (server-rendered CivicPlus).
- **Anti-bot measures:** none observed.
- **Pagination:** none.
- **Selectors (if stable):** CivicPlus body content is in `<div class="cpMainContent">` / page-body div; DocumentCenter links are direct `<a href="/DocumentCenter/View/{id}/{slug}">`.
- **Why no API:** The CMS page itself is the authoritative source; no JSON/RSS alternative.
- **Notes:** Per memory note `feedback_skip_boa_zba.md`, the Board of Adjustments page exists but the project has decided not to track BOA/ZBA activity. Planning Commission at `/1197` IS tracked.
- **Evidence file:** `evidence/lake-hamilton-fl-page-agendas-minutes.html`, `evidence/lake-hamilton-fl-page-council.html`.

#### Building / Permitting / Code-Enforcement pages

- **URL:** `/1205/Community-Development`, `/1210/Building-Permit-Application`, `/1228/Code-Enforcement`, `/1202/Planning-Zoning-Department`, `/1207/Lien-Search-Request`, `/1209/Permit-Fees`, `/1208/Permit-Utilization-Report`, `/1258/Business-Tax-Receipts`, `/1242/Forms-Permits`
- **Data available:** Department narrative, links to application/fee/utilization PDFs, outbound links to Polk PA, Polk Clerk eRecording, SWFWMD, Municode (zoning sections), Florida statutes.
- **Fields extractable:** Body text, DocumentCenter URLs (permit application, fee schedule, utilization report, permit-fees PDF), external references.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** none.
- **Selectors (if stable):** same CivicPlus body-div pattern.
- **Why no API:** No JSON endpoint exposes fee schedules or lien-search forms — they are PDFs behind DocumentCenter.
- **Notes:** Permit Utilization Report is a quarterly static PDF (`/DocumentCenter/View/372/Permit-Utilization-Report-PDF`), not a database. Building permits flow through iWorQ, not the CMS.
- **Evidence file:** `evidence/lake-hamilton-fl-page-comm-dev.html`, `evidence/lake-hamilton-fl-page-bldg-permit.html`, `evidence/lake-hamilton-fl-page-code-enforce.html`, `evidence/lake-hamilton-fl-page-planning.html`, `evidence/lake-hamilton-fl-page-liensearch.html`, `evidence/lake-hamilton-fl-page-permit-fees.html`, `evidence/lake-hamilton-fl-page-permit-util.html`, `evidence/lake-hamilton-fl-page-btr.html`, `evidence/lake-hamilton-fl-page-forms-permits.html`.

#### Public-Records / Elections / HR / Finance / Police pages

- **URL:** `/1211/Public-Records-Request`, `/1212/Election-2025`, `/1291/Election-2026`, `/1217/Annual-Financial-Reports---Audit`, `/1216/Budget-Information`, `/1215/Towns-Electronic-Annual-Financial-Report`, `/1280/Human-Resources`, `/1282/Employment-Information`, `/1201/Police`
- **Data available:** Department narrative, outbound links, PDFs.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Selectors:** CivicPlus standard body-div.
- **Why no API:** narrative content.
- **Evidence file:** `evidence/lake-hamilton-fl-page-pra.html` (others enumerable from sitemap; not individually pulled this run).

### /Calendar.aspx

- **URL:** `https://www.townoflakehamilton.com/Calendar.aspx`
- **Data available:** HTML calendar grid.
- **Fields extractable:** Event titles, dates (rendered via JS from calendar module).
- **JavaScript required:** partial — initial page loads, but full-grid rendering is React-driven.
- **Anti-bot measures:** none.
- **Pagination:** month-forward via JS.
- **Why no API:** `RSSFeed.aspx?ModID=58` and `/common/modules/iCalendar/iCalendar.aspx` cover the data programmatically. This HTML page documented only because it's the human entry point.
- **Notes:** Prefer the iCal or RSS feeds.
- **Evidence file:** `evidence/lake-hamilton-fl-calendar-aspx.html`
- **Why Listed:** ⚠️ Shadow of API — the iCal + RSS feeds are strictly preferred.

### /AgendaCenter

- **URL:** `https://www.townoflakehamilton.com/AgendaCenter`
- **Data available:** Agenda-center index. On this tenant, body content is React-fetched; server HTML contains only the shell + bootstrap. No AgendaCenter RSS feed is advertised (`ModID=65` returns empty skeleton).
- **JavaScript required:** yes.
- **Anti-bot measures:** none.
- **Why no API:** AgendaCenter uses an internal JSON bundle (`docCenterFrontendAndRelatedBidAndJobsApp.react.js`) that wasn't enumerable this run. ⚠️ GAP: browser-run re-enumeration needed.
- **Evidence file:** `evidence/lake-hamilton-fl-agendacenter.html`
- **Notes:** The town effectively does **not use** AgendaCenter — `/1193/Agendas-Minutes` links to `Archive.aspx?AMID=36` instead.

### /Archive.aspx and /ArchiveCenter

- **URL:** `https://www.townoflakehamilton.com/Archive.aspx` (with `?AMID={moduleId}` or `?ADID={itemId}`)
- **Data available:** Archived agenda packets, meeting minutes, historical budget/resolution PDFs. `AMID=36` returned a page with `ADID=47, 48` anchors.
- **Fields extractable:** Item titles, publish dates (rendered via JS).
- **JavaScript required:** yes — the item list is React-fetched.
- **Anti-bot measures:** none.
- **Pagination:** dynamic.
- **Why no API:** No JSON endpoint surfaced in server-HTML. ⚠️ GAP: browser pass needed to capture the underlying XHR.
- **Notes:** Raw binary at `ArchiveCenter/ViewFile/Item/{id}` (documented as an API above) works for known IDs. Index is the gap.
- **Evidence file:** `evidence/lake-hamilton-fl-archive-aspx.html`, `evidence/lake-hamilton-fl-archive-amid36.html`.

### /Jobs.aspx

- **URL:** `https://www.townoflakehamilton.com/Jobs.aspx`
- **Data available:** Open positions with job-detail pages at `?JobID=Slug-Number`.
- **JavaScript required:** no — HTML is server-rendered and includes 3 visible JobIDs + full job-detail bodies.
- **Anti-bot measures:** none.
- **Pagination:** none (small postings set).
- **Why no API:** RSS feed `RSSFeed.aspx?ModID=66` covers the data programmatically.
- **Notes:** Use the Jobs RSS feed for enumeration; this page is the fallback.
- **Evidence file:** `evidence/lake-hamilton-fl-jobs-aspx.html`, `evidence/lake-hamilton-fl-jobs-detail-15.html`.
- **Why Listed:** Shadow — prefer ModID=66 RSS.

### /Bids.aspx

- **URL:** `https://www.townoflakehamilton.com/Bids.aspx`
- **Data available:** "There are no" empty state at survey time.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Why no API:** Empty page — procurement activity flows through `RSSFeed.aspx?ModID=76` (Opportunities) instead.
- **Evidence file:** `evidence/lake-hamilton-fl-bids-aspx.html`.
- **Notes:** Drift sentinel; if bids ever post here, also expect `RSSFeed.aspx?ModID=75` (Bids) to activate.

### /FAQ.aspx, /Directory.aspx, /CivicAlerts.aspx, /AlertCenter.aspx, /BusinessDirectoryii.aspx, /FormCenter, /Forms.aspx, /Blog.aspx, /Gallery.aspx, /list.aspx

- **URL:** as listed above under `www.townoflakehamilton.com`.
- **Data available:** FAQs, staff directory, civic alerts (empty at survey), business directory, form center, blog (empty), photo gallery, sitemap-style list.
- **JavaScript required:** mixed — most are server-rendered but rely on client-fetched JSON for dynamic content.
- **Anti-bot measures:** none observed; `/Search*` and `/CurrentEvents*` are robots-disallowed.
- **Pagination:** varies per module.
- **Why no API:** Most are dynamic CivicPlus React pages with no RSS equivalent on this tenant. `/list.aspx` is a sitemap-like HTML list (same data as `sitemap.xml`, prefer the XML sitemap).
- **Notes:** Drift-sentinel set. Low signal for CountyData2 suite components except FAQ (lien-search procedure) and FormCenter (permit forms already surface via DocumentCenter).
- **Evidence file:** `evidence/lake-hamilton-fl-faq-aspx.html`, `evidence/lake-hamilton-fl-directory.html`, `evidence/lake-hamilton-fl-civicalerts-aspx.html`, `evidence/lake-hamilton-fl-alertcenter-aspx.html`, `evidence/lake-hamilton-fl-businessdirectoryii-aspx.html`, `evidence/lake-hamilton-fl-formcenter.html`, `evidence/lake-hamilton-fl-forms-aspx.html`, `evidence/lake-hamilton-fl-blog-aspx.html`, `evidence/lake-hamilton-fl-gallery-aspx.html`, `evidence/lake-hamilton-fl-list-aspx.html`.

### /rss.aspx

- **URL:** `https://www.townoflakehamilton.com/rss.aspx`
- **Data available:** HTML index enumerating all `RSSFeed.aspx?ModID=…&CID=…` feeds configured on the tenant.
- **Fields extractable:** Feed name + URL per module/category.
- **JavaScript required:** no.
- **Anti-bot measures:** none. (Note: `/RSS.aspx` — singular, uppercase — IS robots-disallowed, but `/rss.aspx` is not.)
- **Pagination:** none.
- **Why no API:** This IS a directory page; the actual feeds are documented above. Keep for navigation.
- **Evidence file:** `evidence/lake-hamilton-fl-rss-index.html`.

### townoflakehamilton.portal.iworq.net — portal landing + permit application surface

- **URL:** `https://townoflakehamilton.portal.iworq.net/` (portal-id 368), `/portalhome/townoflakehamilton`
- **Data available:** Portal landing with 2 tiles: "Permit Portal" (→ `/LAKEHAMILTON/permits/600`) and "Permit Application" (→ `/LAKEHAMILTON/new-permit/600/1861`). Instruction text referencing Florida Statute 713.13 and Polk County eRecording.
- **JavaScript required:** no.
- **Anti-bot measures:** none at this level; permit grid enforces reCAPTCHA.
- **Why no API:** Static landing; no data surface separate from the permit endpoints already documented.
- **Evidence file:** `evidence/lake-hamilton-fl-iworq-root.html`, `evidence/lake-hamilton-fl-iworq-portalhome-town.html`.

---

## External Platforms

One-line references to out-of-hostname platforms that Lake Hamilton depends on. **Not deep-mapped here** — see the referenced county or platform map for details.

- **Municode Library** — `library.municode.com/fl/lake_hamilton/codes/code_of_ordinances`. Angular SPA. Client ID not resolved in this curl-only pass. See `_platforms.md` for platform signatures; resolve in a future browser-run. ⚠️ GAP.
- **Polk County Property Appraiser** — `www.polkpa.org`. Parcel lookups and GIS. Out-of-hostname; will be mapped under the (future) Polk County map.
- **Polk County Clerk** — `www.polkcountyclerk.net/210/eRecording`. eRecording for Notice of Commencement. Out-of-hostname.
- **Polk County Building** — `polk-county.net/docs/default-source/building/notice-of-commencement.pdf`. Direct-link PDFs for building reference forms.
- **Authority Pay** — `lakehamilton.authoritypay.com`. Utility-bill payment portal (outbound payment-only; no public data surface). Not yet in `_platforms.md` — deferred to housekeeping.
- **SWFWMD (water-management district)** — `www.swfwmd.state.fl.us/business/epermitting/district-water-restrictions`. Regional water-use authority referenced on the Code Enforcement page.
- **Florida Statutes** — `leg.state.fl.us/statutes/…`. Reference only.
- **ICC Safe Codes** — `codes.iccsafe.org/content/IPMC2018/index`. Property Maintenance Code reference from Code Enforcement.
- **DocAccess (docaccess.com/docbox.js)** — CivicPlus-embedded JS widget present on every page; not a data surface, treat as a script dependency.
- **Ready311 apps** — Apple / Google Play store links from the Code Enforcement page. App store pages are not a data surface.

No outbound commission platform (no eScribe, no Legistar, no CivicClerk, no Municode Meetings, no Granicus, no BoardDocs) — commission packets are routed through the CivicPlus CMS itself via Archive module.

---

## Coverage Notes

- **robots.txt — CMS (`www.townoflakehamilton.com`):** per §3.2, recorded and treated as an operational-risk signal. Specific disallows respected during this run: `/Search*`, `/CurrentEvents*`, `/Map*`, `/admin`, `/activedit`, `/OJA`, `/support`, `/RSS.aspx` (singular, uppercase — the documented `/rss.aspx` and `/RSSFeed.aspx` are not affected). Baiduspider and Yandex are entirely disallowed (irrelevant to CountyData2). The Siteimprove crawl-delay of 20s was not matched — CountyData2 ran at 1 req/sec and saw no 429s.
- **robots.txt — iWorQ (`townoflakehamilton.portal.iworq.net`):** `User-agent: *` / `Disallow: /`. Per refined §3.2 framing this is an operational-risk signal only. The production adapter `modules/permits/scrapers/adapters/lake_hamilton.py` (fixture-stage) is designed to reach these paths under user-consented sessions, so this mapping pass probed them for drift detection under §9. Pacing was 1 req/sec, 41 new anonymous iWorQ requests, 0 × 429, 0 × 5xx.
- **User-Agent switch mid-run (iWorQ edge rejection):** The first iWorQ probe batch (request-log rows at 04:37:41 and 04:42:03–04:42:39, all logged as `000:0` — TCP accepted, connection closed before response) was issued with the bare `CountyDataMapper/1.0` UA. iWorQ's edge (nginx/1.18.0 on the tenant, but an upstream WAF/CDN in front) closed the connection with no bytes returned for every such request — CMS requests against `www.townoflakehamilton.com` with the same UA succeeded throughout (see log rows 04:37–04:42 for CMS). At 04:43:08 the UA was switched to `Mozilla/5.0 (compatible; CountyDataMapper/1.0)` and the identical iWorQ URLs immediately returned 200s (log rows 04:43:08 onward — root 200:16462, `/LAKEHAMILTON/permits/601` 200:393529, etc.). The browser-prefixed UA is still self-identifying (the `compatible; CountyDataMapper/1.0` token is preserved) and matches the UA convention used by other iWorQ tenants in this project. Evidence: `evidence/_lake-hamilton-request-log.txt` — compare `000:0` iWorQ rows before 04:43 vs `200:*` iWorQ rows from 04:43 on. No CMS request was ever affected; this is an iWorQ-edge-only quirk.
- **iWorQ date-range bypass (key production signal):** Unlike Haines City where anonymous `searchField=permit_dt_range` at fid=600 returns populated rows, **the Lake Hamilton tenant's fid=600 does NOT bypass captcha** — the row tbody is always empty for anonymous requests regardless of filter. However, **fid=601** (a sibling permit category on the same tenant) DOES populate anonymous date-range detail-URL anchors (15 unique IDs/page, ~18 total in a 365-day window). **Implication for the fixture adapter:** `LakeHamiltonAdapter.search_url` currently hard-codes `/LAKEHAMILTON/permits/600` — this is the wrong fid for anonymous bulk extraction. Two options: (a) retarget to fid=601 (works but harvests only ~18 permits/year and thin data columns are captcha-gated — so detail-page fetches are required to extract Permit Number + Permit Date per row), or (b) keep fid=600 and wire up the hybrid-captcha pattern (human solve + cookie steal) per the project's established playbook (`feedback_hybrid_captcha.md`). Recommendation: start with (a) for coverage, consider (b) for depth. Raise the adapter from fixture-stage as part of next live-validation cycle.
- **AgendaCenter / Archive.aspx inventory:** Both are React-rendered on this tenant. `AgendaCenter/UpdateCategoryList` and `DocumentCenterContent` endpoints return the CMS HTML shell to direct GETs (content is client-fetched via a bundle). ⚠️ GAP: browser-run pass needed to capture the underlying XHR and enumerate archive items beyond the two ADIDs (47, 48) that surfaced in static HTML this run.
- **Municode Library client ID:** `library.municode.com/fl/lake_hamilton` is an Angular SPA; without a browser run, the `api.municode.com/codes/{client_id}/nodes` tree is not enumerable. ⚠️ GAP: re-enumerate with browser on next pass.
- **No Bids active:** `Bids.aspx` has the "There are no" empty state. Procurement flows through `RSSFeed.aspx?ModID=76` (Opportunities) — 50 items actively published. Drift sentinel: if `Bids.aspx` populates, check `ModID=75` for a matching RSS feed.
- **No external commission platform:** Unlike Haines City (eScribe), Dundee (Municode Meetings), or Davenport (Catalis GovOffice), Lake Hamilton keeps all commission packets on the CivicPlus CMS itself. This is typical of very small FL towns (Lake Hamilton population ~1,500). CR pipeline for this town would flow through `Archive.aspx?AMID=36` + `ArchiveCenter/ViewFile/Item/{id}` — not yet automated.
- **Board of Adjustments page:** Per memory `feedback_skip_boa_zba.md`, the `/1199/Board-of-Adjustments` page is out-of-scope for tracking (CountyData2 does not track BOA/ZBA at any level). Documented in the sitemap for completeness but not deep-mapped.
- **Adapter fixture-stage status:** `modules/permits/scrapers/adapters/lake_hamilton.py` was not live-validated prior to this run. The adapter's `search_url` field should be re-checked against this map's findings — specifically the fid=600 vs fid=601 decision above.
- **Total request count:** 132 requests this run (CMS side ~70, iWorQ side 41, ancillary ~20). Cap is 2000. 0 × 429, 0 × 5xx, 0 captcha challenges actually invoked (the reCAPTCHA widget on iWorQ was observed in-DOM but never solved). Request log: `evidence/_lake-hamilton-request-log.txt`.
- **Degraded-mode rationale:** The CMS is server-rendered ASP.NET; curl-only is appropriate. AgendaCenter / Archive / Municode Library are the only client-rendered surfaces, and all are noted as ⚠️ GAPs. A future browser-enabled run would close the client-side rendering gaps and resolve the Municode `client_id`.
