# Lake Wales, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.lakewalesfl.gov/` (city of Lake Wales, within Polk County). One-file scope: city of Lake Wales only — Polk County is mapped separately in `polk-county-fl.md`.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.lakewalesfl.gov/` is server-rendered ASP.NET (CivicPlus CivicEngage); the only JavaScript marker is the standard CivicPlus `/antiforgery` XHR bootstrap (no SPA hydration globals — `__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__` — are present on the CMS). One exception: `cityoflakewales.column.us` is a Next.js SSR Firebase-backed SPA; its shell was captured, but the Firestore data surface was not deep-probed this pass (see ⚠️ GAP in Coverage Notes). The ADG Building Department Portal at `secure.lakewalesfl.gov/permits` is also a jQuery-based SPA; its login-gated XHRs were not exercised.

## Summary

- **Jurisdiction:** City of Lake Wales (within Polk County, FL).
- **City website platform:** CivicPlus CivicEngage. Classic numeric-ID URL pattern (`/{numeric-id}/{slug}`, e.g. `/241/Building-Division`, `/909/Contractor-Online-Portal`). Canonical host `www.lakewalesfl.gov`. CivicPlus footer + `/antiforgery` bootstrap + `/RSSFeed.aspx` + `/AgendaCenter/` + `/DocumentCenter/` + `/FormCenter/` all present.
- **Commission surface:** **CivicPlus AgendaCenter at `/AgendaCenter`** — this is authoritative for Lake Wales CR data (matches `modules/commission/config/jurisdictions/FL/lake-wales-cc.yaml`: `platform: civicplus`, `category_id: 4`). The RSS Agenda Creator feed (`ModID=65`) is live and populated (unlike Haines City). Sample permalinks observed: `/AgendaCenter/PreviousVersions/1693`, `/AgendaCenter/ViewFile/Agenda/_04062026-1682`.
- **Vestigial meeting vendors (broken shells):**
  - `lakewalesfl.legistar.com` — tenant provisioned but **unconfigured**. OData returns HTTP 500 with exception "LegistarConnectionString setting is not set up in InSite for client: lakewalesfl". Every UI page (`/Calendar.aspx`, `/People.aspx`, `/Legislation.aspx`) returns the 19-byte string "Invalid parameters!". **Dead tenant.** Likely migration residue from a past platform evaluation.
  - `lakewalesfl.novusagenda.com` — `/` redirects to `/AgendaWeb/` which throws an ASP.NET Runtime Error (HTTP 500, "another exception occurred while executing the custom error page"). **Dead tenant.** No usable data surface.
- **Video / legacy archive:** `lakewales.granicus.com` Granicus ViewPublisher (view_id=1). Live — archives 300+ Commission meeting video clips with `AgendaViewer.php?view_id=1&clip_id=*` links. Crucially, every `AgendaViewer.php?clip_id=*` **302-redirects to the CivicPlus `/AgendaCenter/ViewFile/Agenda/…` URL** — confirming that Granicus hosts video, CivicPlus hosts the agenda/packet documents. The live stream is at `player/camera/3?publish_id=2`.
- **Public legal notices:** `cityoflakewales.column.us` — Column, PBC notice portal. Next.js SSR shell on Cloudflare, Firebase/Firestore backend (`enotice-production.firebaseapp.com`). Data surface is Firestore via SPA. ⚠️ GAP: direct collection paths not enumerated from anon curl — needs a browser pass to capture XHRs. **New platform added to `_platforms.md`.**
- **Utility billing surface:** `secure.lakewalesfl.gov/ubs1/` — ADG UBS Utilities portal (login-gated; `a_no`/`a_pass` form POSTs to `/custubs/main.php`). Same vendor pattern as Haines City's `utility.hainescity.com/utility/`, but this is the bare-PHP flavor of the ADG UBS product (no UBS Utilities Management wrapper).
- **Permit portal (Contractor Online Portal):** `secure.lakewalesfl.gov/permits` + mobile redirector `/permitsmu/`. **ADG Building Department Portal** — the permit-side sibling to ADG UBS. jQuery-based SPA (`ADG_BASE_URL="/adg"`, `APPCODE="ADG"`, `USERCD="BPSUSER"`); login-gated with a UI-only "Public View" mode. Anonymous data surface not characterized — `/adg/citizenlink` 403 and common public-search URL guesses 404. ⚠️ GAP: needs browser pass. **New platform added to `_platforms.md`.**
- **Code of ordinances:** Municode Library at `library.municode.com/fl/lake_wales` (external; Angular SPA; covered by existing Municode Library entry in `_platforms.md`).
- **No GovBuilt tenant.** All four probed slugs (`lakewalesfl`, `cityoflakewales`, `lakewales`, `mylakewales`) return the 31,617-byte generic placeholder (`<title>GOVBUILT PLATFORM - Tomorrow's Government Built Today</title>`) and the API probe `/PublicReport/GetAllContentToolModels` returns the 8110-byte 404 error page — **placeholder signature matches detection discipline per `_platforms.md`**.
- **No iWorQ tenant.** Both `lakewales.portal.iworq.net` and `cityoflakewales.portal.iworq.net` 302-redirect to `/portalhome/<slug>` and then return the Laravel "Page Can Not Be Found" shell (3210 bytes). No real permit tenant. (Permits live on ADG, not iWorQ, on this city.)
- **No Accela, no SmartGov, no Laserfiche, no CityView** tenants observed (confirming Planner recon).
- **No ArcGIS / FeatureServer / MapServer** endpoints on the Lake Wales footprint; parcel GIS rides Polk County (`polkflpa.gov`), out of this file's scope.
- **Total requests this run:** ~95. Cap is 2000. No 429s, no captchas.

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.lakewalesfl.gov` | **CivicPlus CivicEngage** | LIVE | `/{numeric-id}/{slug}` URL pattern; `ASP.NET_SessionId` + `CP_IsMobile` cookies; `/antiforgery` bootstrap JSON endpoint; `/rss.aspx` feed index enumerates 73 RSS module/category combinations across 9 `ModID` values (1 News Flash, 51 Blog, 53 Banner/Photo, 58 Calendar, 63 Alert Center, 64 Real Estate, 65 Agenda Creator, 76 Pages, 92 Media Center); `AgendaCenter` live and populated with agenda PreviousVersions 1-1696+; CivicPlus GA4 tag `G-WT37YK4XB3`, AppInsights instrumentation key `1cde048e-3185-4906-aa46-c92a7312b60f`. |
| `secure.lakewalesfl.gov/ubs1/` | **ADG UBS Utilities (bare)** | LIVE (login-gated) | `<title>City Of Lake Wales, Florida - Utilities and Online Payments</title>`; login form fields `a_no` + `a_pass`, POST to `/custubs/main.php`; Apache + PHP; assets under `/ubs1/style.css`. Same vendor as `utility.hainescity.com`; the bare-PHP flavor (no "UBS Utilities Management" wrapper). |
| `secure.lakewalesfl.gov/permits` | **ADG Building Department Portal** | LIVE (login-gated SPA) | `<title>Building Department Portal</title>`; inline `ADG_BASE_URL="/adg"`, `ADG_CITIZENLINK_URL="/adg/citizenlink"`, `APPCODE="ADG"`, `SESSION=<sid>`; base64 `<input id="common-object">` carries `{SITENAME:"PERMITS", USERCD:"BPSUSER", ORGCODE:1, webUrlMatch:"permits", redirector:"/permitsmu/", frameWork:"JQUERYUI"}`; `/adg/supporting/jquery/{jqwidgets-19.2.0,datatables-1.10.21,uploader-10.32.0,select2-4.0.13,lobibox-1.2.7,plyr-3.5.4,moment-2.29.4,qtip2-3.0.3}/` shared with UBS asset layout; jQuery 3.7.1; Apache + PHP/8.3. **New platform**, added to `_platforms.md`. |
| `lakewalesfl.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | Tenant resolves; every path returns 200 but with body "Invalid parameters!" (19 bytes). OData `webapi.legistar.com/v1/lakewalesfl/{Bodies,Events,Matters,Persons,OfficeRecords}` returns HTTP 500 with `"ExceptionMessage":"LegistarConnectionString setting is not set up in InSite for client: lakewalesfl"`. Likely a migration residue from a past platform evaluation — not authoritative for any Lake Wales data. |
| `lakewalesfl.novusagenda.com` | **NovusAgenda (dead shell)** | BROKEN | `/` 302→`/AgendaWeb/` which returns HTTP 500 ASP.NET Runtime Error ("another exception occurred while executing the custom error page for the first exception"). No usable data surface. |
| `lakewales.granicus.com` | **Granicus ViewPublisher** | LIVE (video + archive) | ViewPublisher.php?view_id=1 serves 302,829 bytes enumerating 300+ clip_ids; `AgendaViewer.php?view_id=1&clip_id=*` 302-redirects to `https://www.lakewalesfl.gov/AgendaCenter/ViewFile/Agenda/_<date>-<id>` — i.e. Granicus hands agenda document rendering off to CivicPlus. Video live stream at `player/camera/3?publish_id=2`. `robots.txt` is `Disallow: /` for `*` with `/JSON.php` (returns 2-byte empty JSON `[]`) listed separately — **operational-risk signal; pace conservatively**. |
| `cityoflakewales.column.us` | **Column (Public Notices)** | LIVE (Firebase SPA) | Next.js SSR shell (`x-powered-by: Next.js`, `netlify-vary` headers) on Cloudflare edge; React/CRA chunks reference `enotice-production.firebaseapp.com` + `enotice-production.appspot.com` — Firebase/Firestore backend (Column's internal project is "enotice"). Stripe.js included for payment flows. No plain-text `/robots.txt` served — the SPA returns HTML for unknown paths. **New platform**, added to `_platforms.md`. |
| `library.municode.com/fl/lake_wales` | **Municode Library** | LIVE (external) | Angular SPA; covered by `_platforms.md` row. Not deep-mapped here. |
| GovBuilt slugs (4 tested) | — | PLACEHOLDER (wildcard DNS) | All 4 slugs return 31,617-byte generic placeholder; `/PublicReport/GetAllContentToolModels` returns 404 + 8110-byte error page. Detection confirmed placeholder per `_platforms.md` discipline. |
| iWorQ portal slugs (2 tested) | — | EMPTY TENANT SHELLS | Both `lakewales.portal.iworq.net` and `cityoflakewales.portal.iworq.net` redirect to `/portalhome/<slug>` → Laravel 404 shell. No real permit tenant. |

New platforms added to `docs/api-maps/_platforms.md` this run: **Column (Public Notices)** and **ADG Building Department Portal**.

---

## APIs

### /antiforgery

#### Antiforgery token

- **URL:** `https://www.lakewalesfl.gov/antiforgery`
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
- **Rate limits observed:** none at ~1 req/sec
- **Data freshness:** real-time (per-session)
- **Discovered via:** Inline `getAntiForgeryToken` script in every CivicPlus page.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/antiforgery'
  ```
- **Evidence file:** `evidence/lake-wales-fl-antiforgery.json`
- **Notes:** Token submitted as `__RequestVerificationToken` on same-origin form POSTs. Gate for any POST-driven form on the CMS.

### /robots.txt

#### Robots directives (main site)

- **URL:** `https://www.lakewalesfl.gov/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard CivicPlus robots — disallows admin/search/map paths, allows `/RSSFeed.aspx` but disallows `/RSS.aspx`, references sitemap.
- **Response schema:** `text/plain` robots.txt.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static (CMS-managed)
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/robots.txt'
  ```
- **Evidence file:** `evidence/lake-wales-fl-www-lakewalesfl-gov-robots-txt`
- **Notes:** Baidu + Yandex disallowed entirely; for `*`, disallows `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEventsView.*`, `/Search.*`, `/Search`, `/CurrentEvents.aspx`, `/Map.*`, `/RSS.aspx`. Siteimprove rate-limited to 20s. `Sitemap: /sitemap.xml`.

#### Robots directives (Granicus video archive)

- **URL:** `https://lakewales.granicus.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** `Disallow: /` for `*` — all anonymous crawlers blocked. Operational-risk signal.
- **Response schema:** `text/plain`.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none; pacing ~1 req/sec this run, no 429s.
- **Data freshness:** static.
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl 'https://lakewales.granicus.com/robots.txt'
  ```
- **Evidence file:** `evidence/lake-wales-fl-lakewales-granicus-com-robots-txt`
- **Notes:** Named bots (Googlebot, Slurp, msnbot, search-one-scgov) disallow only `/JSON.php` + crawl-delay 10; generic `*` disallows all. Mapping pass is consented + low-volume per §3.2; observes pacing not hard gate.

### /sitemap.xml

#### Sitemap index (main site)

- **URL:** `https://www.lakewalesfl.gov/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full URL enumeration for every server-rendered page on the CivicEngage site (339 entries).
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
- **Pagination:** `none` — 339 entries inline.
- **Rate limits observed:** none
- **Data freshness:** updated on CMS publish (entries with `lastmod` 2014 through 2026).
- **Discovered via:** `/robots.txt`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/sitemap.xml'
  ```
- **Evidence file:** `evidence/lake-wales-fl-www-lakewalesfl-gov-sitemap-xml`
- **Notes:** Canonical diff target for drift detection on CMS structure.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed on this tenant: `1` (News Flash), `51` (Blog), `53` (Banner/Photo), `58` (Calendar), `63` (Alert Center), `64` (Real Estate Locator), `65` (Agenda Creator — **live on this tenant**), `76` (Pages), `92` (Media Center). Full categorized feed list in evidence file `lake-wales-fl-rss-modids.txt` (73 URLs).

Note: `/RSS.aspx` (singular, capitalized) is **disallowed by robots.txt**. `/RSSFeed.aspx` is **allowed** and is the correct endpoint.

#### News Flash RSS (ModID 1)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Latest CivicAlerts / News Flash items, optionally category-filtered.
- **Response schema:**
  ```
  <rss version="2.0">
    <channel>
      <title>string</title>
      <link>url</link>
      <lastBuildDate>rfc822-date</lastBuildDate>
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
  - `CID` (string, optional) — category filter. Observed: `All-newsflash.xml`, `2023-Library-Carousel-24`, `City-Administration-1`, `Florida-Water-Star-25`, `Library-8`, `Police-15`.
- **Probed parameters:** `unverified`
- **Pagination:** `none` — trailing window.
- **Rate limits observed:** none at 1 req/sec.
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx` HTML index.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod1.xml`
- **Notes:** 5725-byte sample captured; live News Flash content.

#### Blog RSS (ModID 51)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog posts (Depot Museum subfeed observed as only category).
- **Response schema:** RSS 2.0 (same shape as News Flash).
- **Observed parameters:**
  - `ModID=51`
  - `CID` — `All-blog.xml`, `Depot-Museum-1`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton only (324-byte feed).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=51'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod51.xml`
- **Notes:** Drift sentinel.

#### Banner / Photo RSS (ModID 53)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Banner/photo items keyed to venue or department.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=53`
  - `CID` — `All-0`, `Crystal-Lake-Park-3`, `Fire-Department-2`, `Kiwanis-Park-4`, `Lake-Wailes-Park-5`, `Library-Childrens-Room-7`, `Library-Teen-Room-8`, `Parks-and-Recreation-9`, `Tourist-Club-Rental-6`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** irregular (curator-driven).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod53.xml`
- **Notes:** 52,853-byte sample; live content.

#### Calendar RSS (ModID 58)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming city calendar events (distinct from AgendaCenter meetings).
- **Response schema:** RSS 2.0 with `calendarEvent:*` extension namespace.
- **Observed parameters:**
  - `ModID=58`
  - `CID` — `All-calendar.xml`, `Bid-Due-Dates-34`, `Boards-Commissions-Committees-37`, `City-Clerk-30`, `City-Commission-22`, `Fire-Department-31`, `Lake-Wales-Family-Recreation-Center-40`, `Library-Events-24`, `Library-Youth-Events-26`, `Main-Calendar-14`, `Museum-39`, `Planning-Zoning-32`, `Police-Department-Events-36`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod58.xml`
- **Notes:** `City-Commission-22`, `Planning-Zoning-32`, `Boards-Commissions-Committees-37` are the CR-relevant category filters (meeting calendars for CC, P&Z, and other boards). This is the calendar module — actual meeting agenda documents are in `/AgendaCenter`.

#### Alert Center RSS (ModID 63)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Emergency/alert notifications.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=63`, `CID=All-0` (only category observed in index).
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** event-driven (currently empty — 336-byte skeleton).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=63&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod63.xml`
- **Notes:** Drift sentinel.

#### Real Estate Locator RSS (ModID 64)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Economic-development property listings (empty on this tenant).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=64`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton-only (348 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=64&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod64.xml`
- **Notes:** Potentially BI-relevant if ever populated; re-probe quarterly.

#### Agenda Creator RSS (ModID 65) — **LIVE on this tenant**

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Every CivicPlus AgendaCenter agenda publication — titles, meeting dates, and `/AgendaCenter/PreviousVersions/{id}` permalinks.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=65`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none` — trailing window of most recent publishes.
- **Rate limits observed:** none
- **Data freshness:** real-time (each agenda publication fires a feed item).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=65&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod65.xml`
- **Notes:** **CR-relevant.** 11,521-byte sample includes agendas for City Commission, Police Pension Board, Fire Pension Board. Items reference `/AgendaCenter/PreviousVersions/1693`, `/1696`, `/1566`, `/1567`, `/1634`, `/1635`, `/1696`, etc. Complements (and overlaps with) the existing `civicplus` scraper surface used by `lake-wales-cc.yaml`.

#### Pages RSS (ModID 76)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CMS page updates (numeric-ID pages with lastmod).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=76`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=76'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod76.xml`
- **Notes:** 14,339-byte sample. Channel title "Lake Wales, FL - Pages"; items link to numeric CMS page IDs (e.g. `/362`, `/752`). Useful as a page-change sentinel.

#### Media Center RSS (ModID 92)

- **URL:** `https://www.lakewalesfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CivicMedia module feed (empty on this tenant).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=92`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** empty (330-byte skeleton).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/RSSFeed.aspx?ModID=92&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-wales-fl-rssfeed-mod92.xml`
- **Notes:** Drift sentinel.

### /common/modules/iCalendar/iCalendar.aspx

#### Calendar iCal export

- **URL:** `https://www.lakewalesfl.gov/common/modules/iCalendar/iCalendar.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** iCal (`.ics`) export of the CivicPlus calendar module, optionally filtered by category.
- **Response schema:**
  ```
  BEGIN:VCALENDAR
  PRODID:iCalendar-Ruby
  VERSION:2.0
  X-WR-TIMEZONE:America/New_York
  BEGIN:VTIMEZONE ... END:VTIMEZONE
  BEGIN:VEVENT
  DESCRIPTION:url
  DTEND;TZID=...:YYYYMMDDTHHMMSS
  DTSTAMP;TZID=...:YYYYMMDDTHHMMSS
  DTSTART;TZID=...:YYYYMMDDTHHMMSS
  LAST-MODIFIED;TZID=...:YYYYMMDDTHHMMSS
  LOCATION:string
  SEQUENCE:int
  SUMMARY:string
  UID:uuid
  END:VEVENT
  END:VCALENDAR
  ```
- **Observed parameters:**
  - `catID` (int, optional) — calendar category ID matching the RSS `CID` numeric suffixes (e.g. `14` for Main Calendar, `22` for City Commission, `32` for Planning-Zoning).
  - `feed` (string, optional) — `calendar` observed.
- **Probed parameters:**
  - `catID=14&feed=calendar` — returns 70,833-byte ICS with many VEVENTs stretching years ahead.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** Pattern-match to CivicPlus standard iCal endpoint (not directly linked from HTML — standard CivicEngage path).
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar'
  ```
- **Evidence file:** `evidence/lake-wales-fl-calendar-ics-14.ics`
- **Notes:** Serves the same events as the Calendar RSS (ModID=58) but in iCal format. Useful for direct calendar-app subscription.

### /ImageRepository/Document

#### Image/document repository

- **URL:** `https://www.lakewalesfl.gov/ImageRepository/Document`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Raw binary media file (image, PDF) from the CivicPlus image repository.
- **Response schema:** binary (`Content-Type: image/png`, `image/jpeg`, `application/pdf`, etc.).
- **Observed parameters:**
  - `documentID` (int, required) — repository document ID. Observed: `6119` (header logo), `6123` (Facebook icon), `6131` (Twitter icon), many more in homepage and newsflash HTML.
- **Probed parameters:** `unverified`
- **Pagination:** `none` (single-asset fetcher).
- **Rate limits observed:** none
- **Data freshness:** static per documentID.
- **Discovered via:** Inline `<img src="/ImageRepository/Document?documentID=…">` in home-page HTML.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/ImageRepository/Document?documentID=6119' -o logo.png
  ```
- **Evidence file:** `unverified` (no sample captured — would require binary download)
- **Notes:** Not a data API in the semantic sense but does serve structured binary content by numeric ID. ⚠️ GAP: no way to enumerate valid documentIDs without parsing referring HTML.

### /AgendaCenter (data-surface entry points)

CivicPlus AgendaCenter — **the authoritative CR data surface for Lake Wales.** The `/AgendaCenter` landing page is documented under Scrape Targets because it returns HTML; the two endpoints below return binary/structured document data keyed by agenda IDs.

#### AgendaCenter agenda file download

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter/ViewFile/Agenda/{slug}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Agenda document (typically PDF) for a specific meeting.
- **Response schema:** binary PDF or HTML-rendered agenda depending on `?html=true` query.
- **Observed parameters:**
  - `{slug}` (path segment, required) — underscore-prefixed date+id, e.g. `_04062026-1682`.
  - `html` (bool, optional) — `true` serves HTML render instead of PDF. Observed in Granicus AgendaViewer 302-redirect pattern.
- **Probed parameters:**
  - `html=true` — returns `text/html` instead of PDF. Granicus's `AgendaViewer.php?view_id=1&clip_id=668` redirects to `/AgendaCenter/ViewFile/Agenda/_05072024-1442?html=true`.
- **Pagination:** `none` (single-document fetcher)
- **Rate limits observed:** none
- **Data freshness:** real-time (per agenda publish)
- **Discovered via:** AgendaCenter landing-page cards + Agenda Creator RSS (`ModID=65`).
- **curl:**
  ```bash
  curl -I 'https://www.lakewalesfl.gov/AgendaCenter/ViewFile/Agenda/_04062026-1682'
  ```
- **Evidence file:** `evidence/lake-wales-fl-agenda-viewfile-1682.pdf` (HEAD-only; body deferred)
- **Notes:** Similar patterns exist for `ViewFile/Minutes/{slug}` and `ViewFile/Packet/{slug}`. Known structure from CivicPlus convention; not fully enumerated this pass. Already reachable by the existing `cr/adapters/civicplus.py` adapter.

#### AgendaCenter PreviousVersions browse

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter/PreviousVersions/{id}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML page listing all historical versions (agenda + minutes + packets) for a given meeting-history root ID.
- **Response schema:** HTML page (categorized under Scrape Targets below; no structured API).
- **Observed parameters:**
  - `{id}` (path, required) — integer. Observed range: `303` (2016) through `1696` (2026).
- **Probed parameters:** `unverified`
- **Pagination:** `none` per ID.
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** AgendaCenter landing-page links, Agenda Creator RSS.
- **curl:**
  ```bash
  curl 'https://www.lakewalesfl.gov/AgendaCenter/PreviousVersions/1693'
  ```
- **Evidence file:** `evidence/lake-wales-fl-agenda-previous-1693.html`
- **Notes:** Documented here because every entry links to one or more `ViewFile/` binary endpoints — structured IDs. ⚠️ GAP: no JSON equivalent observed.

### Granicus ViewPublisher

#### ViewPublisher agenda archive feed (HTML)

The `ViewPublisher.php?view_id=1` response is **HTML** (302,829 bytes) — documented under Scrape Targets. The RSS variant is below.

#### ViewPublisher RSS (agendas)

- **URL:** `https://lakewales.granicus.com/ViewPublisherRSS.php`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RSS 2.0 feed enumerating every Granicus clip in the view — Commission Workshops, Regular meetings, P&Z, etc. — with pub-date and deep-link to `AgendaViewer.php?clip_id=…`.
- **Response schema:**
  ```
  <rss version="2.0" xmlns:gran="https://www.granicus.com/schema/rss-supplements">
    <channel>
      <title>City of Lake Wales, FL: Lake Wales, FL View (Agenda Feed)</title>
      <gran:sourceURL>url</gran:sourceURL>
      <link>url</link>
      <item>
        <guid isPermaLink="false">uuid</guid>
        <title>string</title>
        <pubDate>rfc822-date</pubDate>
        <gran:pubDateParts yr="..." mo="..." day="..." hr="..." min="..." sec="..." tz="..." />
        <link>url</link>
        <description>html</description>
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:**
  - `view_id` (int, required) — `1` observed.
  - `mode` (string, optional) — `agendas` observed.
- **Probed parameters:** `unverified`
- **Pagination:** `none` (full archive in single feed; 82,363 bytes, dozens of items).
- **Rate limits observed:** none; robots.txt `Disallow: /` for `*` — pace conservatively.
- **Data freshness:** real-time (publish at meeting record).
- **Discovered via:** Standard Granicus ViewPublisher pattern.
- **curl:**
  ```bash
  curl 'https://lakewales.granicus.com/ViewPublisherRSS.php?view_id=1&mode=agendas'
  ```
- **Evidence file:** `evidence/lake-wales-fl-granicus-viewpub-rss.xml`
- **Notes:** `<link>` targets `AgendaViewer.php?view_id=1&clip_id=…` which 302-redirects to the CivicPlus AgendaCenter `ViewFile/Agenda/_<date>-<id>` URL. Authoritative agenda document lives at CivicPlus; Granicus just hosts video + legacy archive.

#### Granicus JSON.php

- **URL:** `https://lakewales.granicus.com/JSON.php`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** 2-byte empty JSON array `[]` — placeholder endpoint, no meaningful data.
- **Response schema:**
  ```
  []
  ```
- **Observed parameters:** none
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none; explicitly listed in robots.txt as `Disallow: /JSON.php` for crawlers.
- **Data freshness:** static-empty.
- **Discovered via:** robots.txt enumeration.
- **curl:**
  ```bash
  curl 'https://lakewales.granicus.com/JSON.php'
  ```
- **Evidence file:** `evidence/lake-wales-fl-granicus-JSON-php.out`
- **Notes:** Documented for completeness; the endpoint exists but returns no data for anonymous callers.

### Legistar OData (broken — documented for drift detection)

#### OData /Bodies (500 — unconfigured)

- **URL:** `https://webapi.legistar.com/v1/lakewalesfl/Bodies`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Should return JSON array of Body entities. Actually returns HTTP 500 with `"ExceptionMessage":"LegistarConnectionString setting is not set up in InSite for client: lakewalesfl"`.
- **Response schema:**
  ```
  {
    "Message": "An error has occurred.",
    "ExceptionMessage": "string",
    "ExceptionType": "string",
    "StackTrace": "string"
  }
  ```
- **Observed parameters:** none (default collection listing)
- **Probed parameters:** `$top`, `$filter`, `$orderby` — not tested because the tenant is unconfigured; all would 500.
- **Pagination:** `unverified` (OData `$skip`/`$top` by convention, untestable here)
- **Rate limits observed:** none observed.
- **Data freshness:** dead tenant — no data.
- **Discovered via:** Planner recon — Legistar subdomain resolves 200, routine OData probe.
- **curl:**
  ```bash
  curl 'https://webapi.legistar.com/v1/lakewalesfl/Bodies'
  ```
- **Evidence file:** `evidence/lake-wales-fl-legistar-odata-bodies.json`
- **Notes:** ⚠️ GAP: tenant is unconfigured; if Lake Wales ever migrates CR to Legistar, this endpoint and siblings (`Events`, `EventItems`, `Matters`, `Persons`, `OfficeRecords`) would light up. Documented here as a drift sentinel. Other siblings return the same 500 shape or 404.

---

## Scrape Targets

### / (CivicPlus CivicEngage home + inner pages)

#### Home page + numeric-ID content pages

- **URL:** `https://www.lakewalesfl.gov/{id}/{slug}` (e.g. `/909/Contractor-Online-Portal`, `/241/Building-Division`, `/252/Forms-Checklists`, `/217/City-Commission`, `/213/Planning-Zoning-Board`, `/160/Boards-Commissions-Committees`, etc.)
- **Data available:** CMS-rendered department/page content. Cross-links to other pages, image gallery, contact form references, outbound vendor links (Granicus, ADG, Column, Municode, etc.).
- **Fields extractable:** page title, breadcrumb path, body HTML, Quick Links widget, Feature Column items (e.g. external portal buttons), sidebar navigation tree.
- **JavaScript required:** no (server-rendered ASP.NET; only `/antiforgery` XHR is JS).
- **Anti-bot measures:** none observed at 1 req/sec; `robots.txt` disallows admin/search/map paths.
- **Pagination:** per-page; nav tree enumerated by sitemap (339 entries).
- **Selectors (if stable):**
  - Page title: `<h1>` within `<main>` or `<div class="widget editor pageStyles">`.
  - Breadcrumbs: `#breadCrumbs ol.breadCrumbs li`.
  - Body content: `.fr-view` (Froala editor-rendered body).
  - Feature buttons: `a.fancyButton` (cross-link to external vendor portals).
- **Why no API:** CivicPlus doesn't expose a CMS JSON API for inner pages; content is HTML-only.
- **Notes:** Sitemap at `/sitemap.xml` is the canonical enumeration. Example CR-relevant inner pages: `/217/City-Commission`, `/218/Duties-Responsibilities`, `/219/Elections`, `/705/Agenda`, `/213/Planning-Zoning-Board`, `/216/Charter-Amendment`. BI/PT-relevant: `/241/Building-Division`, `/909/Contractor-Online-Portal`, `/251/Choosing-a-Contractor`, `/254/Permit-Requirements`, `/879/Permit-Utilization-Reports`, `/253/Permit-Inspection-Fees`, `/252/Forms-Checklists`.

### /rss.aspx (HTML index)

#### RSS feed index

- **URL:** `https://www.lakewalesfl.gov/rss.aspx`
- **Data available:** HTML listing of every RSSFeed.aspx endpoint available (73 categorized feed URLs across 9 ModIDs).
- **Fields extractable:** feed title, category name, `/RSSFeed.aspx?ModID=…&CID=…` URL.
- **JavaScript required:** no.
- **Anti-bot measures:** none; `robots.txt` explicitly disallows `/RSS.aspx` (singular, capital) but this endpoint `/rss.aspx` (mixed case / lowercase) is served without challenge.
- **Pagination:** none (all feeds inline).
- **Selectors (if stable):** `<a href="RSSFeed.aspx?ModID=…&CID=…">`.
- **Why no API:** this IS the index page for the RSS APIs below; the individual RSSFeed.aspx endpoints themselves are APIs.
- **Notes:** Evidence `lake-wales-fl-civicplus-rss-aspx.html` (111,507 bytes). Enumerated feed list in `lake-wales-fl-rss-modids.txt`.

### /AgendaCenter (landing + search)

#### AgendaCenter landing

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter`
- **Data available:** Grid of upcoming + recent agendas across all boards/committees, with links to `ViewFile/Agenda/{slug}` PDF/HTML and `PreviousVersions/{id}` history pages.
- **Fields extractable:** meeting title, date, category ID (CIDs observed: `28`, `49`), `ViewFile/Agenda/_<date>-<id>` slug.
- **JavaScript required:** no (fully server-rendered 374,530-byte HTML).
- **Anti-bot measures:** none observed.
- **Pagination:** none visible on landing; full archive via `PreviousVersions` or Agenda Creator RSS.
- **Selectors (if stable):** agenda cards under `.catAgendaRow`; slug in `<a href="/AgendaCenter/ViewFile/Agenda/_<slug>">`.
- **Why no API:** the binary `/AgendaCenter/ViewFile/*` endpoints ARE the API; this landing is the HTML index that links to them. The CR adapter at `cr/adapters/civicplus.py` already consumes this shape.
- **Notes:** Authoritative CR surface per `lake-wales-cc.yaml`. AgendaCenter inner AJAX endpoints `/AgendaCenter/Search` (POST) and `/AgendaCenter/UpdateCategoryList` both returned 404 when probed — the live search UI likely uses JS-synthesized paths not directly exposed. ⚠️ GAP: inner search API not probed from browser.

#### AgendaCenter Search (HTML — 404 on direct POST)

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter/Search`
- **Data available:** Search UI for agenda archive (term + category + date range).
- **Fields extractable:** same as AgendaCenter landing.
- **JavaScript required:** no for GET landing; POST-based AJAX for in-page search.
- **Anti-bot measures:** none observed.
- **Pagination:** UI-driven.
- **Selectors (if stable):** same card shape as landing.
- **Why no API:** direct POST probes to `/AgendaCenter/Search/` and `/AgendaCenter/UpdateCategoryList` returned 404 — the search endpoints require JS-synthesized request shapes (likely an antiforgery token + specific form-encoded body). Needs a browser pass to capture XHRs. ⚠️ GAP.
- **Notes:** Evidence `lake-wales-fl-civicplus-AgendaCenter-Search.html` (97,197 bytes — HTML landing).

### /AgendaCenter/PreviousVersions/{id}

#### Meeting version history

- **URL:** `https://www.lakewalesfl.gov/AgendaCenter/PreviousVersions/{id}`
- **Data available:** All historical versions of a given meeting's agenda, packet, and minutes documents, with publish timestamps.
- **Fields extractable:** document type (Agenda, Minutes, Packet), version timestamp, `ViewFile/{type}/{slug}` link, notes on amendments.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** none per ID.
- **Selectors (if stable):** stable CivicPlus AgendaCenter markup (`.catAgendaRow`).
- **Why no API:** CivicPlus AgendaCenter surfaces its data entirely via HTML + the binary `ViewFile/*` endpoints; no JSON version-history API exists.
- **Notes:** Evidence `lake-wales-fl-agenda-previous-1693.html` (115,487 bytes).

### /DocumentCenter

#### Document Center index + sub-index

- **URL:** `https://www.lakewalesfl.gov/DocumentCenter` and `https://www.lakewalesfl.gov/DocumentCenter/Index/{folderID}`
- **Data available:** Categorized document archive. Observed folder ID: `201` (City Budget), `433` (Ordinance Business Impact Statements).
- **Fields extractable:** folder name, sub-folder list, document links (`DocumentCenter/View/{docID}/{slug}`).
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** per-folder; none observed at current volume.
- **Selectors (if stable):** `.documentListView` list items.
- **Why no API:** no JSON document-index endpoint observed.
- **Notes:** Evidence `lake-wales-fl-civicplus-DocumentCenter.html` + `lake-wales-fl-civicplus-documentindex-433.html`.

### /Archive.aspx

#### Archive center landing

- **URL:** `https://www.lakewalesfl.gov/Archive.aspx`
- **Data available:** Archive module index (redirected from `/ArchiveCenter`); historic content archives.
- **Fields extractable:** archive category, item list, download links (typically `Archive/ViewFile/Item/{id}` shape).
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** UI-driven.
- **Selectors (if stable):** `<table>` / `<ul>` varies by category; inspect per-category.
- **Why no API:** no JSON archive index.
- **Notes:** 200 response captured (`lake-wales-fl-civicplus-Archive-aspx.html`). Usage on this tenant low — most archive-type content sits in DocumentCenter.

### /FormCenter

#### FormCenter index + sub-forms

- **URL:** `https://www.lakewalesfl.gov/FormCenter`
- **Data available:** List of all contact/request forms grouped by category (Building Division, Citizen Board Application, Code Enforcement, Contact City Officials, Contact Us). Numeric IDs `16` (Building Division) → `84` (Contractor-Online-Portal-Access-Request), `18` → `83` (Citizen-Board-Application-Form), `4` → `44` (Report-a-Code-Violation), etc.
- **Fields extractable:** form title, form ID, category ID, form URL.
- **JavaScript required:** no (HTML index + `/antiforgery` for form POSTs).
- **Anti-bot measures:** antiforgery token required on POST; no captcha observed on index.
- **Pagination:** none.
- **Selectors (if stable):** sidebar `<a href="/FormCenter/{cat-N}/{form-M}">`.
- **Why no API:** forms are inbound (data-write, not read).
- **Notes:** Inbound forms; no BI/PT/CR data surface here — documented for CMS-drift reference.

### /Calendar.aspx

#### Calendar HTML view

- **URL:** `https://www.lakewalesfl.gov/Calendar.aspx`
- **Data available:** HTML calendar UI showing upcoming events.
- **Fields extractable:** same as Calendar RSS (ModID=58) + iCalendar.aspx.
- **JavaScript required:** partial (navigation JS; event list server-rendered).
- **Anti-bot measures:** none observed.
- **Pagination:** month/week navigation query params.
- **Selectors (if stable):** `.calendarEvent` entries.
- **Why no API:** same data available via `RSSFeed.aspx?ModID=58` (API) and `common/modules/iCalendar/iCalendar.aspx` (iCal API) — both documented above. **Prefer those APIs.**
- **Notes:** Documented for completeness; use RSS/iCal for machine consumption.

### lakewales.granicus.com/ViewPublisher.php

#### ViewPublisher HTML archive

- **URL:** `https://lakewales.granicus.com/ViewPublisher.php?view_id=1`
- **Data available:** 300+ historical meeting video clips with `AgendaViewer.php?clip_id=…` links (which 302-redirect to CivicPlus `/AgendaCenter/ViewFile/Agenda/…`).
- **Fields extractable:** clip title (meeting name + date), clip_id, video MP4/stream link, agenda redirect target.
- **JavaScript required:** no (full HTML archive — 302,829 bytes captured).
- **Anti-bot measures:** robots.txt `Disallow: /` for `*` — pace conservatively; named bots disallow `/JSON.php` only.
- **Pagination:** none (entire archive inline).
- **Selectors (if stable):** `a[href*="AgendaViewer.php?clip_id="]`.
- **Why no API:** `ViewPublisherRSS.php` (documented in APIs above) provides the same data in RSS form.
- **Notes:** Authoritative video archive for Commission meetings (not agendas — CivicPlus is authoritative for agenda documents). Evidence `lake-wales-fl-granicus-viewpub.html`.

### lakewales.granicus.com/player/camera/3

#### Live video player

- **URL:** `https://lakewales.granicus.com/player/camera/3?publish_id=2&redirect=true`
- **Data available:** HLS / Flash-legacy live video stream for Commission chamber.
- **Fields extractable:** stream URL (embedded); player UI.
- **JavaScript required:** yes (streaming player).
- **Anti-bot measures:** same as above.
- **Pagination:** none.
- **Selectors (if stable):** `<video>` or legacy Flash embed.
- **Why no API:** stream is a live video feed — no structured data.
- **Notes:** Evidence `lake-wales-fl-granicus-player-camera-3.out` (73,841 bytes).

### secure.lakewalesfl.gov/ubs1/

#### ADG UBS login page

- **URL:** `https://secure.lakewalesfl.gov/ubs1/index.html`
- **Data available:** Login gate only — no public search / account lookup.
- **Fields extractable:** none without auth.
- **JavaScript required:** no for login page; form submits classic POST.
- **Anti-bot measures:** none observed; no captcha on login.
- **Pagination:** n/a.
- **Selectors (if stable):** `form[name=form1]` with fields `a_no`, `a_pass`, `a_org=1`; submits to `/custubs/main.php`.
- **Why no API:** no anonymous data surface — login-only.
- **Notes:** ⚠️ GAP: authenticated UBS data (utility accounts, billing history) not accessible without per-account credentials.

### secure.lakewalesfl.gov/permits

#### ADG Building Department Portal landing

- **URL:** `https://secure.lakewalesfl.gov/permits`
- **Data available:** ADG Citizenlink jQuery SPA — Licenses, Permits, Applications dashboard. Public-view mode exists (per CMS page `/909/Contractor-Online-Portal`: "Public View allows you to search by permit number or address") but is UI-triggered from inside the SPA rather than a direct URL.
- **Fields extractable:** via SPA session only — permit number, permit status, address, inspection history.
- **JavaScript required:** yes (jQuery-UI + jqwidgets SPA).
- **Anti-bot measures:** login button present; public-view requires UI activation.
- **Pagination:** SPA-driven (jQuery DataTables).
- **Selectors (if stable):** `#data-display-block`, `#center-block-body`, `#public-front-page` — stubs populated by SPA JS.
- **Why no API:** direct URL probes `/permits/publicSearch.php`, `/permits/public`, `/permits/searchpermits`, `/adg/citizenlink/permits` all 404. `/adg/citizenlink` itself 403 anon. Data XHRs fire from within the SPA after a session init.
- **Notes:** ⚠️ GAP: anonymous permit-search API not enumerated. Needs browser pass to capture SPA XHRs (Public View flow). Mobile sibling at `/permitsmu/` (115,819 bytes, jQuery Mobile). Evidence `lake-wales-fl-secure-permits.html` + `lake-wales-fl-permits-permitsmu.html`.

### cityoflakewales.column.us/search

#### Column public notices tenant SPA

- **URL:** `https://cityoflakewales.column.us/search`
- **Data available:** Public legal notices posted by the city / attending newspapers. Data rendered by SPA from Firestore.
- **Fields extractable:** via SPA / Firestore — notice_id, title, publication, published_date, body, jurisdiction, logo attachment URL.
- **JavaScript required:** yes (Next.js SSR shell + CRA SPA hydration; shell does not contain notice data inline).
- **Anti-bot measures:** Cloudflare edge (`CF-RAY` header), `cf-2fa-verify` meta tag — but no active challenge observed on unauthenticated `/search`.
- **Pagination:** SPA-driven.
- **Selectors (if stable):** `<div id="root">` hydrated by `/static/js/main.*.chunk.js` — selectors are JS-generated.
- **Why no API:** the underlying data is in **Firebase/Firestore**. Direct REST to `firestore.googleapis.com/v1/projects/enotice-production/databases/(default)/documents/…` would work but requires collection-path enumeration from a browser session. Probed `/api`, `/api/v1/notices`, `/api/notices`, `/graphql`, `/api/public/notices`, `/_next/data` — all return the SSR HTML shell (the SPA swallows unknown paths). `/api/search` + `/_next/data` explicitly 404.
- **Notes:** ⚠️ GAP: Firestore data surface not enumerated anon — needs browser pass to capture Firestore XHR calls. Firebase project name: `enotice-production`. Evidence `lake-wales-fl-column-search.html` + `lake-wales-fl-column-root.html`.

### lakewalesfl.legistar.com (broken)

#### Legistar dead tenant

- **URL:** `https://lakewalesfl.legistar.com/Calendar.aspx` (and all other Legistar paths)
- **Data available:** **none** — tenant is provisioned in the domain but unconfigured at the application layer.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** none; just fails.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a — response is the literal 19-byte string `Invalid parameters!`.
- **Why no API:** OData 500s with "LegistarConnectionString setting is not set up in InSite for client: lakewalesfl".
- **Notes:** ⚠️ GAP: drift sentinel. If Lake Wales ever completes a CR platform migration to Legistar, these URLs will activate. For current runs, CivicPlus AgendaCenter is authoritative.

### lakewalesfl.novusagenda.com (broken)

#### NovusAgenda dead tenant

- **URL:** `https://lakewalesfl.novusagenda.com/` → `/AgendaWeb/`
- **Data available:** **none** — tenant throws ASP.NET Runtime Error 500.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a.
- **Why no API:** application-level error; the custom error page itself also fails.
- **Notes:** ⚠️ GAP: drift sentinel. Likely orphan from an earlier CR platform era (pre-CivicPlus AgendaCenter). Evidence `lake-wales-fl-novus-redirect-chain.html`.

---

## External Platforms (cross-reference only; not deep-mapped here)

- **Municode Library** — `library.municode.com/fl/lake_wales`. Covered by the existing Municode Library row in `_platforms.md`. Angular SPA; client-ID not resolved in this curl-only pass. ⚠️ GAP: re-enumerate with browser to capture `api.municode.com/codes/{client_id}/nodes`.
- **Polk County parent infrastructure** — Polk County Property Appraiser (`polkflpa.gov`), Polk County Clerk Legistar, Polk County official records — documented in `docs/api-maps/polk-county-fl.md`. Parcel GIS for Lake Wales properties rides Polk's service.
- **Comm100** — `vue.comm100.com` / `standby.comm100vue.com` referenced as chat vendor script. Outbound service only; no data surface.
- **AudioEye** — `wsmcdn.audioeye.com` script referenced. Accessibility widget; no data surface.
- **DocAccess** — `docaccess.com/docbox.js` script referenced. Document accessibility widget; no data surface.

---

## Coverage Notes

- **Total requests this run:** ~95 (well under 2000 cap). No 429s, no captchas encountered. Pacing ~1 req/sec throughout.
- **User-Agent:** `Mozilla/5.0 (compatible; CountyDataMapper/1.0)` per Lake Hamilton finding.
- **Request log:** `evidence/_lake-wales-request-log.txt` enumerates every request with timestamp, status code, URL, and output file.
- **robots.txt stance per hostname (operational-risk signal):**
  - `www.lakewalesfl.gov` — standard CivicPlus disallows (admin/search/map/`/RSS.aspx`); `/RSSFeed.aspx` allowed; Sitemap referenced. Mapping pass compliant (no disallowed path requested).
  - `lakewales.granicus.com` — **`Disallow: /` for `*`** — highest-risk signal. Paced ~1 req/sec; no 429s. ⚠️ GAP: if repeated runs ever trip a block, scale back to one Granicus request per pass (or use only ViewPublisherRSS which was captured once this pass).
  - `secure.lakewalesfl.gov` — no robots served (404). No explicit stance.
  - `lakewalesfl.legistar.com`, `lakewalesfl.novusagenda.com` — 404 (no robots). Not relevant given dead-tenant status.
  - `cityoflakewales.column.us` — app returns HTML SPA shell for `/robots.txt` (no plain-text robots). Cloudflare edge + Firebase backend; conservative pacing advised.
- **Meeting-vendor disambiguation (authoritative for current CR data):** **CivicPlus AgendaCenter on `www.lakewalesfl.gov`.** Matches `modules/commission/config/jurisdictions/FL/lake-wales-cc.yaml` (`platform: civicplus`, `category_id: 4`). Legistar and NovusAgenda tenants exist as domain artifacts but are BROKEN shells (Legistar unconfigured, NovusAgenda ASP.NET Runtime Error). Granicus hosts video archive only; `AgendaViewer.php?clip_id=*` 302s to CivicPlus. The live stream at `player/camera/3` is the only Granicus-original surface for current use.
- **NovusAgenda migration status:** **Dead tenant.** Tenant subdomain resolves but `/AgendaWeb/` throws ASP.NET runtime error — both the primary and the error-fallback pages fail. Not a redirect-to-Legistar (Legistar is also dead). Treat as orphan infrastructure from a pre-CivicPlus era.
- **GovBuilt detection outcome:** **Placeholder (no tenant).** All four slugs tested (`lakewalesfl`, `cityoflakewales`, `lakewales`, `mylakewales`) returned the 31,617-byte generic placeholder HTML with title `GOVBUILT PLATFORM - Tomorrow's Government Built Today` and `/PublicReport/GetAllContentToolModels?contentType=case&Start=0&Length=5` returning 404 + 8110-byte error page. Matches placeholder signatures per `_platforms.md` detection discipline. **No browser / CF-challenge pass was needed** — curl with the CountyDataMapper UA reached all four slugs directly without a JS challenge.
- **Column platform added to `_platforms.md`:** **Yes.** New row for "Column (Public Notices)" captures tenant pattern (`<tenant>.column.us`), Firebase/Firestore backend (`enotice-production`), SSR shell fingerprints. Data surface (Firestore) is scrapable in principle — justifies direct-edit per Lake Alfred QA ruling — but anon-curl could not enumerate the collection paths. ⚠️ GAP flagged in the row itself.
- **ADG Building Department Portal added to `_platforms.md`:** **Yes.** Separate from the existing `ADG UBS` row because it's a distinct ADG product (permits vs. utility billing). Shares vendor + asset layout but different `SITENAME`, `USERCD`, redirector. ⚠️ GAP flagged in the row for anon data surface.
- **UBS1 backend identified:** **American Data Group (ADG) UBS** — same vendor family as Haines City's `utility.hainescity.com`, but this is the bare-PHP flavor rather than the "UBS Utilities Management" wrapper. `/custubs/main.php` is the login-post target; login-only (no anon data surface).
- **iWorQ:** No real permit tenant. Both `lakewales.portal.iworq.net` and `cityoflakewales.portal.iworq.net` resolve but return Laravel "Page Can Not Be Found" (3,210/3,216 bytes) after redirect. Permits on this city live on ADG, not iWorQ.
- **Accela / SmartGov / Laserfiche / CityView:** Not observed (Planner recon confirmed). No re-probe this pass.
- **Known unsurveyed / ⚠️ GAPs:**
  - AgendaCenter in-page search + UpdateCategoryList AJAX endpoints (404 on direct POST; need browser pass).
  - Column Firestore collection paths (needs browser pass to capture SPA XHRs).
  - ADG permits public-view XHRs (needs browser pass to capture SPA session init + public-view activation).
  - Municode Library Lake Wales client_id (needs browser pass).
  - `ImageRepository/Document` — no way to enumerate valid documentIDs without parsing referring HTML.
- **Evidence directory:** all files prefixed `lake-wales-fl-*` under `docs/api-maps/evidence/`. Key samples: home HTML (pre-seeded), sitemaps, robots.txt per host, RSS samples per ModID, iCal export, AgendaCenter landing + search + sample PreviousVersions, Granicus ViewPublisher + RSS, Legistar OData 500, NovusAgenda runtime error, Column SPA shell, ADG permits + permitsmu, UBS1 login.
