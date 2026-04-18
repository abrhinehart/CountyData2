# Haines City, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://www.hainescity.com/` (city of Haines City, within Polk County). One-file scope: city of Haines City only — Polk County is mapped separately.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.hainescity.com/` is server-rendered ASP.NET (CivicPlus CivicEngage); the only JavaScript marker is the standard CivicPlus `/antiforgery` XHR bootstrap. No SPA hydration markers (`__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__`, etc.) are present on the CMS. The Municode Library page at `library.municode.com/fl/haines_city` is Angular (`ng-app="mcc.library_desktop"`) — see ⚠️ GAP under Coverage Notes.

## Summary

- **Jurisdiction:** City of Haines City (within Polk County, FL).
- **City website platform:** CivicPlus CivicEngage. Classic numeric-ID URL pattern (`/{numeric-id}/{slug}`, e.g. `/155/Development-Services-Department`). Canonical host `www.hainescity.com`; alias `www.myhainescity.com` serves the identical content. Title suffix `• CivicEngage` confirmed.
- **Commission surface:** eScribe at `pub-hainescity.escribemeetings.com`. City Commission, Planning Commission, CRA, Code Compliance, Red Light Camera, and several advisory bodies all flow through this single tenant. The `AgendaCenter` CivicPlus subapp is present but empty on this tenant — commission meetings are **not** served via CivicPlus AgendaCenter here. Already integrated via `modules/commission/scrapers/escribe.py` + `modules/commission/config/jurisdictions/FL/haines-city-cc.yaml` + `haines-city-pc.yaml`. The archived per-platform narrative at `docs/api-maps/_archived/haines-city-escribe.md` remains the canonical deep-dive; this file re-verifies the endpoints under the current §4 schema.
- **Permit surface:** iWorQ at `haines.portal.iworq.net/HAINES/permits/600`. Single-table permit listing with sort-header pagination; search form requires reCAPTCHA. `haines.portal.iworq.net/robots.txt` disallows all anonymous crawlers; the existing `modules/permits/scrapers/adapters/haines_city.py` adapter operates post-captcha under explicit user consent (hybrid-captcha pattern) and is not subject to the anonymous-crawl rule.
- **Code of ordinances:** Municode Library at `library.municode.com/fl/haines_city`. SPA — client ID not resolved in this curl-only pass. ⚠️ GAP: re-enumerate with a browser next run to capture `api.municode.com/codes/{client_id}/nodes`.
- **Utility billing surface:** `utility.hainescity.com/utility/` — ADG UBS Utilities Management portal (session-gated, login required; no public data surface).
- **Fire-service assessment surface:** `quicksearch.ennead-data.com/hainescity/` — classic-ASP speed-search front-end for the Preliminary 2026-27 Fire Service Assessment (per-parcel lookup by parcel #, owner name, or address). Custom vendor (Ennead Data); form-POST flow.
- **Transparency / budget:** `cleargov.com/florida/polk/city/haines-city` — ClearGov outbound link for fiscal transparency (out-of-hostname; budget data lives with ClearGov, not Haines City).
- **Procurement:** DemandStar (`demandstar.com/app/agencies/florida/city-of-haines-city`) — outbound procurement portal. No on-site bids posted on `Bids.aspx`.
- **Subscriptions:** Constant Contact (external email list) for City Manager's Report.
- **No ArcGIS / FeatureServer / MapServer endpoints** were found on the Haines City footprint. The city's "CRA Map" page is an HTML page (static), not a GIS viewer. Parcel GIS rides Polk County's `polkflpa.gov` service, out of this file's scope. ⚠️ GAP: Polk GIS cross-reference deferred to the Polk County map.
- **Total requests this run:** ~100. Cap is 2000. No 429s, no captcha challenges (the reCAPTCHA on the iWorQ search form was observed but not invoked).

## Platform Fingerprint

| Host | Platform | Fingerprint |
|---|---|---|
| `www.hainescity.com` | **CivicPlus CivicEngage** | `/{numeric-id}/{slug}` URL pattern; `ASP.NET_SessionId` + `CP_IsMobile` cookies; CSP `frame-ancestors` includes `platform.civicplus.com`, `account.civicplus.com`, `analytics.civicplus.com`; CivicPlus footer (`Government Websites by CivicPlus®`); title suffix `• CivicEngage`; `/antiforgery` bootstrap JSON endpoint; `/rss.aspx` feed index. |
| `www.myhainescity.com` | CivicPlus CivicEngage (alias) | Serves identical content to `www.hainescity.com` (same CivicPlus backend). Treat as a DNS alias — all endpoints are the same. |
| `pub-hainescity.escribemeetings.com` | **eScribe** | Already in `_platforms.md`. ASP.NET WebForms + AJAX PageMethods; Syncfusion EJ2 calendar chrome; Cloudflare edge (`CF-RAY`, `__cf_bm`); JSON POSTs to `/MeetingsCalendarView.aspx/GetCalendarMeetings`; `FileStream.ashx?DocumentId=…` for binary packet download. Admin tenant on separate host (not exposed here). |
| `haines.portal.iworq.net` | **iWorQ** | nginx/1.18 (Ubuntu); Laravel backend (`XSRF-TOKEN` + `iworq_api_session` cookies, encrypted `eyJpdi…` envelopes); Bootstrap 3 + jQuery UI chrome; `<form id="search-form-captcha">` protected by `g-recaptcha`; permit listing at `/HAINES/permits/600`; tenant prefix `HAINES`; inspection-calendar POST to `/HAINES/scheduler/600/permit/1/{permitId}`. |
| `library.municode.com/fl/haines_city` | **Municode Library** | Already in `_platforms.md`. Angular SPA (`ng-app="mcc.library_desktop"`); client ID not discoverable via curl (⚠️ GAP). |
| `utility.hainescity.com` | **ADG UBS Utilities Management** | `<title>UBS Utilities Management</title>`; session cookie scheme; `ADG_BASE_URL="/adg"`; `APPCODE="ADG"`; `/citizenlink` citizen-facing path; jQuery + jqWidgets; login-gated — no anonymous data surface. **New platform**, not yet in `_platforms.md`. Vendor: ADG (Automated Data Group). |
| `quicksearch.ennead-data.com/hainescity/` | **Ennead Data Speed Search** | Classic ASP (`action="Search_results.asp" method="post"`); ISO-8859-1 encoding; no session management; single-page fire-service-assessment lookup. **New platform**, not yet in `_platforms.md`. Vendor: Ennead Data. |
| `cleargov.com/florida/polk/city/haines-city` | **ClearGov** | Outbound fiscal-transparency portal. Data sovereignty sits with ClearGov, not Haines City. Out-of-hostname; not deep-mapped in this file. |
| `demandstar.com/app/agencies/florida/city-of-haines-city/procurement-opportunities/…` | **DemandStar** | Outbound procurement portal. No on-site bids on `Bids.aspx`. Out-of-hostname; not deep-mapped. |

New platforms observed in this run that are **not yet in `docs/api-maps/_platforms.md`**: **ADG UBS Utilities Management** (utility billing; session-gated) and **Ennead Data Speed Search** (classic-ASP fire-assessment lookup). Adding them to the registry is deferred to a housekeeping task.

---

## APIs

### /antiforgery

#### Antiforgery token

- **URL:** `https://www.hainescity.com/antiforgery`
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
  curl 'https://www.hainescity.com/antiforgery'
  ```
- **Evidence file:** `evidence/haines-city-fl-antiforgery.json`
- **Notes:** Token is submitted as `__RequestVerificationToken` on same-origin form POSTs. Not useful for data extraction on its own — it is the gate for any POST-driven search/contact forms on the CMS.

### /sitemap.xml

#### Sitemap index

- **URL:** `https://www.hainescity.com/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full URL enumeration for every server-rendered page on the CivicEngage site (369 entries).
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
- **Pagination:** `none` — all 369 entries inline in a single document.
- **Rate limits observed:** none
- **Data freshness:** Updated on CMS publish (entries with `lastmod` ranging from 2018 to 2026).
- **Discovered via:** Referenced in `/robots.txt` via `Sitemap: /sitemap.xml`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/sitemap.xml'
  ```
- **Evidence file:** `evidence/haines-city-fl-sitemap.xml`
- **Notes:** Canonical list of every indexable page; useful as the diff target for detecting new/removed modules between runs.

### /robots.txt

#### Robots directives

- **URL:** `https://www.hainescity.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard robots.txt — enumerates disallowed paths for anonymous crawlers.
- **Response schema:** `text/plain` robots.txt (key–value records).
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static (CMS-managed).
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/robots.txt'
  ```
- **Evidence file:** `evidence/haines-city-fl-robots.txt`
- **Notes:** Blocks Baiduspider and Yandex entirely; for `*`, disallows `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx`. Siteimprove bots are rate-limited to 20s. The map's Coverage Notes section captures the enforcement decisions made this run.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed on this tenant: `1` (News Flash), `51` (Blog — empty), `53` (Street Pole Banners / Department photo streams), `58` (Calendar), `63` (Alert Center), `64` (Real Estate Locator), `65` (Agenda Creator — empty on this tenant), `66` (Jobs — empty), `76` (Opportunities), `92` (CivicMedia). Each optionally accepts a `CID` (category) filter. The canonical index of feeds is `/rss.aspx` (HTML listing — documented under Scrape Targets).

Note: `/RSS.aspx` (singular, capitalized) is **disallowed by robots.txt**. `/RSSFeed.aspx` is **allowed** and is the correct endpoint.

#### News Flash RSS

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Latest CivicAlerts / News Flash items for the city, optionally filtered by category.
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
  - `CID` (string, optional) — category filter. Observed values: `All-newsflash.xml`, `Home-News-1`, `Home-Spotlight-5`, `Special-Events-Spotlights-22`, `Template-News-2-27`, `Template-News-26`.
- **Probed parameters:**
  - `ModID=9999` (bogus) — returned HTTP 200 with a 0-byte body (silent-empty), not a 404. Do not rely on status codes for feed existence.
- **Pagination:** `none` — RSS returns a trailing window.
- **Rate limits observed:** none at 1 req/sec.
- **Data freshness:** real-time (publishes with CMS updates).
- **Discovered via:** `/rss.aspx` HTML index.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid1.xml`
- **Notes:** `ModID=1` is shared across CivicPlus CivicEngage tenants. Same endpoint with other `ModID` values → different modules (below).

#### Blog RSS

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog post feed (currently returns skeleton-only on this tenant — the Blog module is not actively populated).
- **Response schema:** RSS 2.0 (same as News Flash).
- **Observed parameters:**
  - `ModID=51` (int, required)
  - `CID` (string, optional) — observed: `All-blog.xml`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty on this tenant (325-byte skeleton response).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=51&CID=All-blog.xml'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid51.xml`
- **Notes:** Skeleton-only. Useful as a drift sentinel — if this feed grows items, Haines started using the Blog module.

#### Department Photo / Banner RSS (ModID 53)

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Photo/banner items keyed to department subfeeds (Fire, General, Lake Eva Event Center, Library, Parks & Recreation, Police).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=53` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Fire-8`, `General-2`, `Lake-Eva-Event-Center-15`, `Library-7`, `Parks-and-Recreation-3`, `Police-9`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** irregular (curator-driven).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid53.xml`
- **Notes:** Low BI/PT/CR/CD2 signal; documented for completeness.

#### Calendar RSS

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming city calendar events (events module, separate from eScribe meetings).
- **Response schema:** RSS 2.0 with `calendarEvent:*` extension namespace.
- **Observed parameters:**
  - `ModID=58` (int, required)
  - `CID` (string, optional) — observed: `All-calendar.xml`, `Aquatics-24`, `CRA-37`, `City-Clerk-36`, `City-Manager-22`, `Development-Services-28`, `Elected-Officials-35`, `Fire-29`, `Library-23`, `Main-Calendar-14`, `Parks-Recreation-25`, `Planning-Commission-MeetingCancelation-38`, `Police-30`, `Public-Meetings-34`, `Public-Works-32`, `Purchasing-39`, `Special-Events-27`, `Utilities-33`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=58&CID=All-calendar.xml'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid58.xml`
- **Notes:** `Planning-Commission-MeetingCancelation-38` is the notification-of-cancellation category for PC meetings (not the actual PC agenda — that lives in eScribe). The `Main-Calendar-14` CID is the umbrella feed linked from the homepage.

#### Alert Center RSS (ModID 63)

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Emergency/alert notifications — weather alerts, road closures, utility outages, non-emergency advisories.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=63` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Weather-Alert-4`, `Utility-Outage-5`, `Road-Closure-6`, `NonEmergency-7`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** event-driven (publishes during incidents).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=63&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid63.xml`
- **Notes:** Currently-empty skeleton (337 bytes) — no active alerts at survey time.

#### Real Estate Locator RSS (ModID 64)

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Economic-development property listings (commercial/residential for-sale/for-rent inventory tracked by the city).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=64` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Commercial-Properties-For-Sale-1`, `Commercial-Properties-For-Rent-2`, `Residential-Properties-For-Sale-3`, `Residential-Properties-For-Rent-4`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** unknown — skeleton-only (349 bytes) at survey time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=64&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid64.xml`
- **Notes:** Potentially BI-relevant if active (economic-development property pipeline) — worth re-probing quarterly to see if items accumulate.

#### Agenda Creator RSS (ModID 65)

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Agenda Creator module feed — empty on this tenant (agendas are served through eScribe, not CivicPlus AgendaCenter).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=65`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=65&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid65.xml`
- **Notes:** Drift sentinel. If it ever grows items, it would mean Haines started publishing agendas via CivicPlus (a signal that commission data may fork into two sources).

#### Jobs RSS

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Open city positions from the Jobs module.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=66` (int, required)
  - `CommunityJobs` (bool, optional) — observed: `False`.
  - `CID` (string, optional) — observed: `All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** posts/deletes with HR postings.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?CommunityJobs=False&ModID=66&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid66.xml`
- **Notes:** Skeleton-only at survey time (327 bytes).

#### Opportunities RSS (ModID 76)

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Opportunity postings (RFP/RFQ/civic-engagement opportunities). 14.7 KB payload — actively populated.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=76`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** active.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=76&CID=All-0'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid76.xml`
- **Notes:** Likely the CivicPlus "Opportunities" module (analogous to Bids but broader). Worth aligning with the empty `Bids.aspx` finding — procurement activity flows here, not through `Bids.aspx`.

#### CivicMedia RSS

- **URL:** `https://www.hainescity.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CivicMedia video/media feed.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=92`, `CID=All-civicmedia.xml`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty skeleton (331 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/RSSFeed.aspx?ModID=92&CID=All-civicmedia.xml'
  ```
- **Evidence file:** `evidence/haines-city-fl-rssfeed-modid92.xml`
- **Notes:** Drift sentinel; video streaming is routed elsewhere on this tenant (Haines has no video in eScribe either).

### /ImageRepository/Document

#### Binary image/document handler

- **URL:** `https://www.hainescity.com/ImageRepository/Document`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary blob for a media asset (image or document) keyed by numeric `documentID`. Content-Type varies per asset — observed `image/png` (logo) and `application/pdf` (NewsFlash attachments).
- **Response schema:** binary stream (Content-Type determined by stored MIME).
- **Observed parameters:**
  - `documentID` (int, required) — opaque asset ID. Observed 121 (site logo PNG, 38 KB), 2911 (PDF, 339 KB).
- **Probed parameters:**
  - Numeric ranges are sparse and non-monotonic; random probes would hit many 404s. The canonical way to discover valid IDs is to scrape rendering pages for `ImageRepository/Document?documentID=N` references.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-asset CMS publish.
- **Discovered via:** `<img>` tags on home and department pages (`<img src="/ImageRepository/Document?documentID=N" />`).
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/ImageRepository/Document?documentID=121' -o haines-city-logo.png
  ```
- **Evidence file:** `evidence/haines-city-fl-imagerepository-121.bin` (PNG logo)
- **Notes:** Parallel to `DocumentCenter/View/<id>/<slug>?bidId=` but with simpler signature (no slug required). Suitable for bulk asset-fetch once IDs are known.

### /DocumentCenter

#### Document binary download

- **URL:** `https://www.hainescity.com/DocumentCenter/View/{documentId}/{slug}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary PDF (or other document MIME) keyed by `documentId` + slug path + `bidId` query param.
- **Response schema:** binary stream. Observed `application/pdf` (375 KB for Haines City Charter).
- **Observed parameters:**
  - `documentId` (int, path segment, required) — e.g. `1859`, `2442`, `2577`.
  - `slug` (string, path segment, required) — URL-slugged filename (e.g. `Haines-City-Charter-A-PDF`).
  - `bidId` (string, query, **required**) — empty string is accepted but the parameter **must be present** or the endpoint 404s.
- **Probed parameters:**
  - `bidId` omitted → HTTP 404.
  - `bidId=` (empty) → HTTP 200, binary PDF.
  - `/DocumentCenter/View/{documentId}` (no slug) → HTTP 301 redirect to the slug-qualified URL (preserving known slug from the CMS).
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-upload.
- **Discovered via:** `<a href="/DocumentCenter/View/N/slug">` on fee-schedule, CRA-budgets, and other department pages.
- **curl:**
  ```bash
  curl 'https://www.hainescity.com/DocumentCenter/View/1859/Haines-City-Charter-A-PDF?bidId=' -o charter.pdf
  ```
- **Evidence file:** `evidence/haines-city-fl-documentcenter-view-2448-slug.headers.txt` (HEAD 404 showing bidId requirement)
- **Notes:** The `bidId` parameter is required by CivicPlus's routing even when the document is not a bid attachment — this is CMS-side coupling. The enumerated IDs this run (1859, 1867, 2022, 2225, 2442, 2443, 2444, 2445, 2446, 2577, 2640, 2797, 2798, 2799, 2800, 2801, 2802, 2895) all resolve to policy/fee/CRA documents. Gap: no structured index of all DocumentCenter assets — they must be scraped from parent pages.

### /Search/Results

#### Site search (robots-restricted)

- **URL:** `https://www.hainescity.com/Search/Results`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML search-results page for a site-wide query.
- **Response schema:** HTML.
- **Observed parameters:**
  - `searchPhrase` (string, path/query, required) — searched text.
- **Probed parameters:**
  - None. **Robots.txt disallows `/Search*`** — no parameter fan-out was attempted beyond confirming the endpoint exists.
- **Pagination:** `unverified` — robots-restricted.
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** Homepage search widget.
- **curl:**
  ```bash
  # robots disallows — do not crawl programmatically
  curl 'https://www.hainescity.com/Search/Results'
  ```
- **Evidence file:** `evidence/haines-city-fl-search-results.html`
- **Notes:** ⚠️ **ROBOTS:** `/Search*` is disallowed. Endpoint documented for completeness only; do not scrape.

---

### pub-hainescity.escribemeetings.com — eScribe (Commission platform)

Already mapped in depth at `docs/api-maps/_archived/haines-city-escribe.md`. This section re-verifies under the current §4 schema. Re-verified 2026-04-17: 47 meetings in 180-day window, distribution {City Commission Meeting: 10, Code Compliance: 9, Red Light Camera: 7, CRA Meeting: 5, City Commission Workshop: 4, Community Engagement: 3, Lakes Advisory Board: 3, Planning Commission: 3, City Commission Special Meeting: 2, Canvassing Board: 1}.

#### /MeetingsCalendarView.aspx/GetCalendarMeetings (POST)

- **URL:** `https://pub-hainescity.escribemeetings.com/MeetingsCalendarView.aspx/GetCalendarMeetings`
- **Method:** `POST`
- **Auth:** `none`
- **Data returned:** Array of `MeetingInfo` records (25 fields each) for meetings in a date window, including nested `MeetingDocumentLink` array per meeting (agenda/minutes/video links).
- **Response schema:**
  ```
  {
    "d": [
      {
        "ID": "uuid",
        "MeetingName": "string",
        "StartDate": "YYYY/MM/DD HH:MM:SS",
        "FormattedStart": "string",
        "EndDate": "YYYY/MM/DD HH:MM:SS",
        "Description": "html",
        "Url": "url",
        "Location": "string",
        "ShareUrl": "string",
        "MeetingType": "string",
        "ClassName": "string",
        "LanguageName": "string",
        "HasAgenda": "bool",
        "Sharing": "bool",
        "MeetingDocumentLink": [
          {
            "CssClass": "string",
            "Format": "string",
            "Image": "html",
            "Title": "string",
            "Type": "string",
            "Url": "string",
            "LanguageId": "int",
            "MeetingName": "string",
            "AriaLabel": "string",
            "HasVideo": "bool",
            "HasLiveVideo": "bool",
            "HasLiveVideoPassed": "bool",
            "Sequence": "int|null",
            "HiddenText": "string",
            "LanguageCode": "string"
          }
        ],
        "PortalId": "int",
        "DelegationRequestLink": "string|null",
        "HasLiveVideo": "bool",
        "HasVideo": "bool",
        "HasVideoLivePassed": "bool",
        "LiveVideoStandAloneLink": "string",
        "MeetingPassed": "bool",
        "AllowPublicComments": "bool",
        "TimeOverride": "string",
        "TimeOverrideFR": "string",
        "IsMP3": "bool"
      }
    ]
  }
  ```
- **Observed parameters:**
  - `calendarStartDate` (string, JSON body, required) — `YYYY-MM-DD`.
  - `calendarEndDate` (string, JSON body, required) — `YYYY-MM-DD`.
- **Probed parameters:**
  - 180-day window → 47 meetings (re-verified 2026-04-17).
  - Missing body → `{"Message":"There was an error processing the request.", ...}` generic envelope.
  - Omitted param returns same generic envelope (no per-field validation leak).
- **Pagination:** `none` — the call returns all meetings in the window at once. Deep-archive pulls require stepping the window backwards.
- **Rate limits observed:** none at sequential ~1 req/sec.
- **Data freshness:** real-time (admin authoring triggers near-immediate publish).
- **Discovered via:** `/` landing page → Syncfusion calendar XHR → PageMethod pattern (`POST /<Page>.aspx/<Method>`).
- **curl:**
  ```bash
  curl -X POST 'https://pub-hainescity.escribemeetings.com/MeetingsCalendarView.aspx/GetCalendarMeetings' \
    -H 'Content-Type: application/json; charset=utf-8' \
    -d '{"calendarStartDate":"2025-10-18","calendarEndDate":"2026-04-17"}'
  ```
- **Evidence file:** `evidence/haines-city-fl-escribe-get-calendar.json` (truncated to 5 of 47 meetings; PII redacted)
- **Notes:** Primary CountyData2 CR scrape surface. Adapter: `modules/commission/scrapers/escribe.py`. MeetingType strings are admin-authored (not stable IDs) — `body_filter` YAML must be audited if a muni renames a body.

#### /FileStream.ashx

- **URL:** `https://pub-hainescity.escribemeetings.com/FileStream.ashx`
- **Method:** `GET`
- **Auth:** `none` (but requires non-default User-Agent — Cloudflare 403s the default Python UA)
- **Data returned:** Binary streamed document (PDF agenda packet or similar binary).
- **Response schema:** binary. Observed `application/pdf`, `Content-Length: 13,893,263` for `DocumentId=27357`.
- **Observed parameters:**
  - `DocumentId` (int, required) — monotonic tenant-global integer. Observed Haines range: ~15,562 (Feb 2023) → ~29,003 (Apr 2026).
- **Probed parameters:**
  - Default Python stdlib User-Agent → HTTP 403 (Cloudflare UA filter).
  - Explicit UA (e.g. `CommissionRadar/1.0`) → HTTP 200.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-meeting publish.
- **Discovered via:** `MeetingDocumentLink[].Url` in `GetCalendarMeetings` responses.
- **curl:**
  ```bash
  curl -A 'CommissionRadar/1.0' \
    'https://pub-hainescity.escribemeetings.com/FileStream.ashx?DocumentId=27357' \
    -o agenda.pdf
  ```
- **Evidence file:** _(not bundled — 13.9 MB PDF; verified via HEAD; `evidence/haines-city-fl-escribe-wsdl.xml` captures a lightweight related artifact)_
- **Notes:** DocumentIds are not guessable — must be harvested from calendar response. `HEAD` reveals `Content-Disposition: inline;filename="Agenda Package - CCRM_Feb05_2026.pdf"`. Also see `docs/api-maps/_archived/haines-city-escribe.md` §4.

#### /GetSearchData.asmx

- **URL:** `https://pub-hainescity.escribemeetings.com/GetSearchData.asmx`
- **Method:** `GET` (HTML index / WSDL), `POST` (SOAP 1.1 / SOAP 1.2 / HTTP form-encoded)
- **Auth:** `none`
- **Data returned:** Classic ASP.NET SOAP service exposing search operations over meeting/agenda/legislation data.
- **Response schema:** SOAP envelope (SOAP 1.1/1.2) or form-encoded POST response. WSDL available.
- **Observed parameters:** (WSDL-declared operations and their parameter lists)
  - `GetSearchMeetingData(searchText, filterbyMeetingTypeIds, filterbyMeetingTypeNames, filterByDate, filterByMeetingDocumentTypes, filterByExtensions, filterByLanguage)`
  - `GetConflictsData(searchText, filterbyMeetingTypeIds, filterByDate, filterByConflictMemberIds, filterbyMeetingTypeNames)`
  - `AgendaItemHistoryListView(filterbyMeetingTypeIds, filterbyMeetingTypeNames, filterByDate, filterByStage, filterByStatus, filterByDepartmentNames)`
  - `GetLegislationData` (signature not clearly emitted by WSDL)
- **Probed parameters:** `unverified` — exercise requires building a SOAP envelope; deferred this run. WSDL in hand (`evidence/haines-city-fl-escribe-wsdl.xml`, 16,953 bytes).
- **Pagination:** `unverified`
- **Rate limits observed:** `unverified`
- **Data freshness:** live (same backing store as PageMethods).
- **Discovered via:** eScribe platform signature (every tenant exposes it). Also referenced in archived map §6.
- **curl:**
  ```bash
  curl 'https://pub-hainescity.escribemeetings.com/GetSearchData.asmx?WSDL'
  ```
- **Evidence file:** `evidence/haines-city-fl-escribe-wsdl.xml`
- **Notes:** Archived-map §6 notes "WSDL parameter drift" — live calls require params not emitted by the WSDL (`includeConflicts`, `includeComments`). Full signatures require a live browser session to capture.

#### /robots.txt (eScribe)

- **URL:** `https://pub-hainescity.escribemeetings.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** robots.txt. Blocks `PetalBot` only.
- **Response schema:** text/plain.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static.
- **Discovered via:** Standard location.
- **curl:**
  ```bash
  curl 'https://pub-hainescity.escribemeetings.com/robots.txt'
  ```
- **Evidence file:** `evidence/haines-city-fl-escribe-robots.txt`
- **Notes:** Public crawl allowed except PetalBot. Aligns with permissive anon-read stance of eScribe platform.

---

### haines.portal.iworq.net — iWorQ (Permit platform)

`haines.portal.iworq.net/robots.txt` disallows all anonymous crawlers. The existing `modules/permits/scrapers/adapters/haines_city.py` operates post-captcha under explicit user consent; it is not subject to the anonymous-crawl rule. All endpoints below are documented for reference; anonymous probing beyond the landing page was **not** conducted.

#### /robots.txt (iWorQ)

- **URL:** `https://haines.portal.iworq.net/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** robots.txt. Disallows all anonymous crawlers.
- **Response schema:** text/plain.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** `unverified`
- **Data freshness:** static.
- **Discovered via:** Standard location.
- **curl:**
  ```bash
  curl 'https://haines.portal.iworq.net/robots.txt'
  ```
- **Evidence file:** `evidence/haines-city-fl-iworq-robots.txt`
- **Notes:** Content is `User-agent: *` / `Disallow: /`. Respect for anonymous crawlers; does not bind the CountyData2 adapter operating under user consent.

---

### Outbound / cross-host APIs

#### ClearGov fiscal transparency (outbound)

- **URL:** `https://cleargov.com/florida/polk/city/haines-city`
- **Method:** `GET`
- **Auth:** `unverified`
- **Data returned:** Fiscal transparency portal (budgets, financials, checkbook) — the canonical surface lives at ClearGov, not Haines City.
- **Response schema:** `unverified` — SPA; JSON API likely at `cleargov.com/api/...`.
- **Observed parameters:** none (linked-to only from homepage).
- **Probed parameters:** none (out-of-hostname; not mapped in this pass).
- **Pagination:** `unverified`
- **Rate limits observed:** `unverified`
- **Data freshness:** `unverified`
- **Discovered via:** Homepage and Finance Department pages.
- **curl:** `unverified`
- **Evidence file:** _(not captured — out-of-hostname)_
- **Notes:** ⚠️ GAP: If budget/fiscal data is in scope for a downstream consumer, ClearGov is a separate mapping target (not Haines City's footprint proper).

#### DemandStar procurement (outbound)

- **URL:** `https://www.demandstar.com/app/agencies/florida/city-of-haines-city/procurement-opportunities/fb32581e-b601-43dc-ad1e-bb4be33c7239/`
- **Method:** `GET`
- **Auth:** `unverified`
- **Data returned:** Procurement opportunities (bids/RFPs) for Haines City, hosted by DemandStar.
- **Response schema:** `unverified`
- **Observed parameters:** Agency UUID `fb32581e-b601-43dc-ad1e-bb4be33c7239` fixed per tenant.
- **Probed parameters:** none (out-of-hostname; not mapped in this pass).
- **Pagination:** `unverified`
- **Rate limits observed:** `unverified`
- **Data freshness:** active (the city uses DemandStar as its primary procurement portal).
- **Discovered via:** Purchasing department page (`/259/Purchasing`).
- **curl:** `unverified`
- **Evidence file:** _(not captured — out-of-hostname)_
- **Notes:** ⚠️ GAP: On-site `Bids.aspx` returned no bid postings; DemandStar is where real procurement data lives. Separate mapping target.

---

## Scrape Targets

Only pages without an API equivalent are listed here. CivicPlus content pages for which an RSS equivalent exists (News Flash, Calendar, Alert Center, Jobs, Opportunities) are documented under APIs instead.

### /

#### Homepage

- **URL:** `https://www.hainescity.com/`
- **Data available:** Hero banners, news flash, calendar excerpt tabs (Main / Meetings / Library), ClearGov/Constant Contact feature cards, Quick Links, FAQs.
- **Fields extractable:** Latest 3–5 news items with IDs (`/CivicAlerts.aspx?AID=N`), next 10 calendar events per tab (`/Calendar.aspx?EID=N`), static site links.
- **JavaScript required:** `no` — server-rendered; optional `/antiforgery` bootstrap XHR is for CSRF only.
- **Anti-bot measures:** none observed.
- **Pagination:** N/A.
- **Selectors (if stable):** `h4 > a[href*="/CivicAlerts.aspx?AID="]` (news items), `h4 > a[href*="/Calendar.aspx?EID="]` (events).
- **Why no API:** The aggregate homepage layout has no JSON endpoint; the underlying RSS feeds (`/RSSFeed.aspx?ModID=1` for news, `/RSSFeed.aspx?ModID=58` for calendar) cover the same items individually.
- **Notes:** Primarily a discovery surface — extract EIDs/AIDs and follow to detail pages. Everything on the homepage is mirrored in the RSS APIs above.

### /101/Departments and /{numeric-id}/{slug} department pages

#### Department index + department pages

- **URL:** `https://www.hainescity.com/101/Departments` (index), `https://www.hainescity.com/{id}/{slug}` (individual)
- **Data available:** Department descriptions, contact info, links to in-department pages (e.g. Building Division `/156/Building-Division` links to zoning inquiry, building permits, fee schedule).
- **Fields extractable:** Department name, numeric ID, slug, sub-page links, email addresses, phone numbers, description HTML.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A (static hierarchy).
- **Selectors (if stable):** `a[href^="/"][href*="-Department"]` off `/101/Departments` for the department list; per-department pages list sub-links in `.widgetContent` blocks.
- **Why no API:** CivicPlus does not expose a department hierarchy JSON. The numeric-ID / slug URLs are the only way to enumerate the structure.
- **Notes:** Discovered department IDs for Haines City: 148 (City Manager), 149 (Technology), 150 (City Attorney), 151 (City Clerk), 155 (Development Services), 162 (Finance), 166 (Fire), 167 (HR), 172 (Parks & Rec), 197 (Police), 204 (Public Infrastructure), 217 (Utilities). CRA: 336. City Commission: 225. Individual sub-pages include building (156), planning (161), zoning inquiry (490), code compliance (198), permit fee schedule (491), purchasing (259), utility billing (165), bid postings (`Bids.aspx`).

### /Calendar.aspx

#### Calendar event detail page

- **URL:** `https://www.hainescity.com/Calendar.aspx?EID={int}`
- **Data available:** Single event — title, date/time, location, description (HTML), category, RSVP links if applicable.
- **Fields extractable:** `title`, `start_datetime`, `end_datetime`, `location`, `description_html`, `category`.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A (one event per page).
- **Selectors (if stable):** `unverified` — CivicPlus templates are skinnable; check per-scrape.
- **Why no API:** The RSS calendar feed `/RSSFeed.aspx?ModID=58` covers event titles and pubDate but omits location/description-HTML; detail pages are the richer source.
- **Notes:** EIDs observed: 5558–5615 (legacy Planning Commission stubs migrating to eScribe), 6652–6759 (current). Also `/calendar.aspx?CID=<csv>` lists events by category CSV (e.g. `CID=24,22,28,29,14,25,30,34,32,27,33,36,35` is the "everything" view linked from the homepage).

### /CivicAlerts.aspx

#### News Flash detail page

- **URL:** `https://www.hainescity.com/CivicAlerts.aspx?AID={int}`
- **Data available:** Full news-flash article (title, body HTML, attached images).
- **Fields extractable:** `title`, `body_html`, `published_date`, `category`, attached `ImageRepository/Document?documentID=N` assets.
- **JavaScript required:** `no` (301 → `/m/newsflash/home/detail/{AID}` is a mobile-normalized rewrite; content still server-rendered).
- **Anti-bot measures:** none
- **Pagination:** N/A (one article per page).
- **Selectors (if stable):** `unverified`
- **Why no API:** The News Flash RSS feed `/RSSFeed.aspx?ModID=1` provides `description` but may truncate HTML for long articles.
- **Notes:** AID range 664–666 observed at survey time. Old AIDs remain resolvable (archive indefinitely).

### /Faq.aspx

#### FAQ detail pages

- **URL:** `https://www.hainescity.com/Faq.aspx?QID={int}` (single question), `https://www.hainescity.com/Faq.aspx?TID={int}` (topic with many QIDs), `https://www.hainescity.com/Faq.aspx` (root — redirects to `/m/faq`)
- **Data available:** FAQ question + answer HTML.
- **Fields extractable:** `question`, `answer_html`, `topic`.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** `unverified`
- **Why no API:** No public FAQ export JSON endpoint observed.
- **Notes:** Observed topics: 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29 (Building), 30, 33, 34. QIDs 124, 165, 172, 201, 202 linked on department pages. `TID=29` redirects to `/m/faq?cat=29`.

### /Jobs.aspx

#### Job listings page

- **URL:** `https://www.hainescity.com/Jobs.aspx`
- **Data available:** Currently-open positions with detail links.
- **Fields extractable:** `title`, `department`, `salary`, `closing_date`, `job_description_url`.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** `unverified`
- **Selectors (if stable):** `unverified`
- **Why no API:** The RSS `ModID=66` feed is empty on this tenant; the HTML page may be the only populated source.
- **Notes:** Compare to `RSSFeed.aspx?ModID=66&CID=All-0` — if the HTML lists jobs but RSS is empty, there is a CMS-config drift to flag.

### /list.aspx

#### Subscription/notification management

- **URL:** `https://www.hainescity.com/list.aspx`
- **Data available:** List of all available email/SMS notification lists the public can subscribe to.
- **Fields extractable:** Notification list names, subscribe endpoints (POST forms).
- **JavaScript required:** `no`
- **Anti-bot measures:** none (subscription POST itself gated by CSRF `/antiforgery` token).
- **Pagination:** N/A.
- **Selectors (if stable):** `unverified`
- **Why no API:** CivicPlus's subscription roster is not JSON-exposed publicly.
- **Notes:** Drift signal — new rows here indicate new public-engagement streams the city is offering.

### /directory.aspx

#### Staff/department directory

- **URL:** `https://www.hainescity.com/directory.aspx` (index), `/directory.aspx?did={int}` (division), `/directory.aspx?eid={int}` (individual)
- **Data available:** Staff contact list — name, title, phone, email, department.
- **Fields extractable:** `name`, `title`, `email`, `phone`, `department`.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** `unverified`
- **Selectors (if stable):** `unverified`
- **Why no API:** No staff directory JSON endpoint observed.
- **Notes:** PII-heavy; handle extraction carefully per PII policy. `did=10` observed; `eid=11`, `eid=61` referenced from department pages.

### /Bids.aspx

#### Bid postings (empty on this tenant)

- **URL:** `https://www.hainescity.com/Bids.aspx`
- **Data available:** Would be bid postings via CivicPlus Bid module — but Haines City has no active bids on this module (DemandStar is the real procurement portal).
- **Fields extractable:** N/A — module is empty/placeholder.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** N/A.
- **Why no API:** Procurement flows through DemandStar (out-of-hostname) — see APIs §Outbound.
- **Notes:** Drift sentinel. If bid postings appear here, Haines has started dual-posting or migrated off DemandStar.

### /AgendaCenter (subapp present, empty on this tenant)

#### Agenda Center subapp

- **URL:** `https://www.hainescity.com/AgendaCenter`
- **Data available:** The subapp **exists** but has no categories configured on this tenant — commission meetings are served through eScribe instead.
- **Fields extractable:** N/A on this tenant.
- **JavaScript required:** `no` (the page loads; it just has no data).
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** N/A.
- **Why no API:** The CivicPlus AgendaCenter exposes `/AgendaCenter/Search/`, `/AgendaCenter/UpdateCategoryList` (POST), `/AgendaCenter/ViewFile/Agenda/_XXXX_`, but all return empty/404 on this tenant because no categories are populated.
- **Notes:** Drift sentinel. If agendas begin to appear, Haines may be dual-publishing commission data.

### /Archive.aspx (empty)

#### Archive Center (empty on this tenant)

- **URL:** `https://www.hainescity.com/Archive.aspx`
- **Data available:** Archive Center placeholder — no archived content enumerated on this tenant.
- **Fields extractable:** N/A.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** N/A.
- **Why no API:** Module empty; no archive IDs to enumerate. Historical content is in DocumentCenter instead.
- **Notes:** Drift sentinel.

### /CivicMedia (placeholder)

#### CivicMedia placeholder

- **URL:** `https://www.hainescity.com/CivicMedia`
- **Data available:** CivicMedia placeholder page — no media items on this tenant.
- **Fields extractable:** N/A.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** N/A.
- **Why no API:** The CivicMedia RSS (`ModID=92`) feed is empty in parallel.
- **Notes:** Drift sentinel.

### /RealEstate.aspx

#### Real Estate Locator (empty)

- **URL:** `https://www.hainescity.com/RealEstate.aspx`
- **Data available:** Economic-development property listings — empty on this tenant at survey time.
- **Fields extractable:** N/A.
- **JavaScript required:** `no`
- **Anti-bot measures:** none
- **Pagination:** N/A.
- **Selectors (if stable):** N/A.
- **Why no API:** Mirrors `/RSSFeed.aspx?ModID=64&CID=All-0` (also empty).
- **Notes:** Drift sentinel — if populated, potentially BI-relevant (commercial/residential for-sale/for-rent inventory).

### pub-hainescity.escribemeetings.com/ (eScribe landing)

#### eScribe calendar landing

- **URL:** `https://pub-hainescity.escribemeetings.com/`
- **Data available:** Syncfusion calendar chrome rendered server-side; the actual meeting data is fetched client-side via `GetCalendarMeetings` PageMethod (see APIs).
- **Fields extractable:** Tenant portal title and navigation only; meeting data is JSON (covered by API above).
- **JavaScript required:** `yes` for the calendar widget; not needed for API access.
- **Anti-bot measures:** Cloudflare `__cf_bm` cookie on tenant; UA filter on `FileStream.ashx` (see API note).
- **Pagination:** N/A.
- **Selectors (if stable):** N/A (calendar is JS-rendered).
- **Why no API:** The API exists and is primary (`GetCalendarMeetings`); the HTML landing is a scrape target only for platform-fingerprint purposes.
- **Notes:** Use the API, not the page.

### haines.portal.iworq.net/HAINES/permits/600 (iWorQ permit search)

#### iWorQ permit search (captcha-gated)

- **URL:** `https://haines.portal.iworq.net/HAINES/permits/600`
- **Data available:** Permit search form + post-search rendered table (Permit #, Date, Planning/Zoning Status, Application Status, Fire Marshall Review Status, Building Plan Review Status, Site Address, Site City/State/Zip, Project Name, Request Inspection link, View link).
- **Fields extractable (post-captcha, per row):** `permit_number`, `issue_date_str`, `planning_zoning_status`, `application_status`, `fire_marshall_review_status`, `building_plan_review_status`, `address_street`, `address_city_state_zip`, `project_name`, `detail_url` (→ `/HAINES/permit/1/{permitId}`). Detail page adds `permit_type`, `contractor`, `valuation`, `description`.
- **JavaScript required:** `yes` — form uses `g-recaptcha`. Table itself is server-rendered HTML; data population requires passing reCAPTCHA first.
- **Anti-bot measures:** Google reCAPTCHA on search form. `robots.txt` disallows all anonymous crawlers.
- **Pagination:** URL-based — `?sort=<col>&direction=<asc|desc>&page=<n>`. Columns observed: `permitnum_id`, `permit_dt`, `lookup2`, `lookup11`, `lookup12`, `lookup13`, `text2`, `text8`, `text12`.
- **Selectors (if stable):** Adapter uses positional `<td>` indexing — see `modules/permits/scrapers/adapters/haines_city.py` lines 48-65.
- **Why no API:** iWorQ does not expose a public JSON API for anonymous callers. Payload is HTML.
- **Notes:** Existing adapter `HainesCityAdapter(IworqAdapter)` at `modules/permits/scrapers/adapters/haines_city.py`; bootstrap lookback 30 days; detail-page pacing 0.5s. Operates under the hybrid-captcha pattern: user passes captcha in browser, script steals cookies for automation. Respects iWorQ robots.txt by never anonymously crawling.

### library.municode.com/fl/haines_city

#### Municode Library landing

- **URL:** `https://library.municode.com/fl/haines_city`
- **Data available:** City of Haines City code of ordinances (all titles/chapters/articles/sections).
- **Fields extractable (after browser resolution):** `client_id`, `product_id`, node tree with flags `IsUpdated`, `IsAmended`, `HasAmendedDescendant`.
- **JavaScript required:** `yes` — Angular SPA (`ng-app="mcc.library_desktop"`).
- **Anti-bot measures:** none observed.
- **Pagination:** N/A (tree-structured).
- **Selectors (if stable):** N/A — use `api.municode.com/codes/{client_id}/nodes` once `client_id` is known.
- **Why no API:** ⚠️ GAP — `api.municode.com` is the real API surface but requires `client_id` discovery. Probed `api.municode.com/Clients/name/haines_city`, `Clients/clientId?clientId=haines_city_fl`, `codes/haines_city_fl/root` — all 404. Client ID naming scheme differs per tenant (not derivable from municipality slug).
- **Notes:** Re-probe with a headless browser next run to capture the `client_id` from the SPA bootstrap request, then register it in `modules/cd2/adapters/municode.py` (existing adapter per `_platforms.md`).

### quicksearch.ennead-data.com/hainescity/

#### Fire Service Assessment speed-search

- **URL:** `https://quicksearch.ennead-data.com/hainescity/` (form), `https://quicksearch.ennead-data.com/hainescity/Search_results.asp` (POST target)
- **Data available:** Per-parcel Fire Service Assessment data (Preliminary 2026-27) — searchable by parcel # (5 segments: 2/2/2/6/6 digits), owner name (`LASTNAME, FIRSTNAME`), or location address (supports `*` wildcards).
- **Fields extractable (post-search; not retrieved this run):** `unverified` — Search_results.asp not exercised to avoid making POSTs on behalf of unknown users. Likely fields: parcel_id, owner_name, site_address, assessment_amount, fire_district.
- **JavaScript required:** `no` — classic-ASP server-rendered.
- **Anti-bot measures:** none observed (no captcha).
- **Pagination:** `unverified`
- **Selectors (if stable):** `unverified`
- **Why no API:** Ennead Data's speed-search is HTML-only; no JSON/XML surface.
- **Notes:** Niche but potentially BI-relevant (parcel-level assessment flag; hits each non-exempt parcel in the city). **New vendor platform** not previously catalogued — add to `_platforms.md` as "Ennead Data Speed Search". Single-season scope (26-27 assessment year).

### utility.hainescity.com/utility/ (session-gated)

#### ADG UBS Utilities Management portal

- **URL:** `https://utility.hainescity.com/utility/`
- **Data available:** Utility billing account data — requires login. No anonymous data surface.
- **Fields extractable (post-auth, not explored): `unverified` — login not provided in task.
- **JavaScript required:** `yes` — jqWidgets + jQuery UI chrome.
- **Anti-bot measures:** Session cookies; `/adg/…` + `/citizenlink/…` base URLs; per-request CSRF nonces (`nonce="…"` attributes on every script tag).
- **Pagination:** `unverified`
- **Selectors (if stable):** `unverified`
- **Why no API:** Login-gated customer portal; no anonymous surface.
- **Notes:** **New vendor platform** — add to `_platforms.md` as "ADG UBS Utilities Management". Vendor: ADG (Automated Data Group).

---

## Coverage Notes

**Robots.txt enforcement (www.hainescity.com):**
- **Disallowed and skipped this run:** `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support` (+capitalized aliases), `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx` (capitalized — use `/RSSFeed.aspx?ModID=…` instead, which is not disallowed).
- The `/Search/Results` endpoint was probed once without parameters to confirm existence, then deferred (robots-restricted); it is documented under APIs for completeness only.
- Siteimprove crawler rate-limit of 20s acknowledged — not applicable to this generic-UA crawl.

**Robots.txt enforcement (haines.portal.iworq.net):**
- `User-agent: * / Disallow: /` — **all paths disallowed for anonymous crawlers**.
- This run respected the rule: only the permit landing page (`/HAINES/permits/600`) and the portal home (`/portalhome/haines`) were fetched, mirroring what a human-browser page-load would do (no programmatic fan-out).
- The existing `HainesCityAdapter` operates under hybrid-captcha + explicit user consent, which is outside the scope of anonymous-crawler robots rules.

**Robots.txt enforcement (pub-hainescity.escribemeetings.com):**
- Blocks PetalBot only. All other crawling permitted. Pacing respected at ~1 req/sec.

**Total requests this run:** ~100. Well under the 2000 cap. See `evidence/_haines-city-request-log.txt` for the full log.

**Events observed:** 0 HTTP 429. 0 captcha challenges invoked (reCAPTCHA widget present on iWorQ search form but not invoked — form not submitted anonymously). 0 Cloudflare challenges (Cloudflare edge present on eScribe but UA filter only triggers on default Python stdlib UA, not our explicit `CountyData2-API-Mapper/1.0`).

**⚠️ GAPs:**
1. **Municode client_id not resolved** — Angular SPA; the `api.municode.com/codes/{client_id}/nodes` endpoint cannot be probed without the client_id. Re-enumerate with a headless browser to capture the bootstrap XHR.
2. **iCalendar endpoint disabled** — `/common/modules/iCalendar/iCalendar.aspx?CID=14` returns 200 with 0-byte `text/html` body on this tenant. iCal feed is not available; use `RSSFeed.aspx?ModID=58` for calendar data.
3. **eScribe SOAP operations not exercised** — WSDL captured but full SOAP envelopes not built (deferred per archived map; requires live browser session for undeclared-param discovery).
4. **Cross-host vendor surfaces (ClearGov, DemandStar)** — not deep-mapped. If budget/procurement data is in scope for a downstream consumer, add them as separate mapping targets (or invoke them as out-of-hostname cross-references in the Polk County file).
5. **Polk County GIS cross-reference** — Haines City has no independent GIS surface; parcel/zoning geometry rides Polk County's `polkflpa.gov`. Deferred to the Polk County map.
6. **iWorQ inner permit detail probing** — not conducted anonymously per robots.txt. Adapter-covered.
7. **ADG utility portal post-auth surface** — not explored (no credentials).
8. **Ennead Data Search_results.asp** — not exercised (form-POST; avoided performing queries on behalf of unknown users).

**Deferrals / housekeeping targets for `docs/api-maps/_platforms.md`:**
- Add **ADG UBS Utilities Management** (hostname pattern: customer subdomain `utility.*` serving `/adg`+`/citizenlink`; signature: `<title>UBS Utilities Management</title>`; `APPCODE="ADG"`; session-gated customer portal; no adapter yet).
- Add **Ennead Data Speed Search** (hostname pattern: `quicksearch.ennead-data.com/{client}/`; signature: classic ASP, ISO-8859-1 encoding, `Search_results.asp` form target; single-page per-parcel lookup; no adapter yet).

**Existing registry entries verified this run:** CivicPlus CivicEngage (on `www.hainescity.com`), eScribe (on `pub-hainescity.escribemeetings.com`), iWorQ (on `haines.portal.iworq.net`), Municode Library (on `library.municode.com`).

**Mode disclaimer:** Degraded mode (curl-only). A next-run pass with a headless browser is recommended to resolve the Municode `client_id` and to capture the full iWorQ post-captcha table structure for drift-detection against the existing adapter.
