# Lake Alfred, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://www.mylakealfred.com/` (City of Lake Alfred, within Polk County, FL). One-file scope: City of Lake Alfred only — Polk County BCC and shared county infrastructure (Polk PA, Polk Clerk eRecording, county-level ArcGIS) are mapped in `polk-county-fl.md`.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.mylakealfred.com/` is server-rendered ASP.NET (CivicPlus CivicEngage) with the same hydration profile as Haines City / Winter Haven / Lake Hamilton. No SPA hydration markers (`__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__`) on the CMS. The Accela Citizen Access tenant at `aca-prod.accela.com/COLA` is Angular (`ng-app="appAca"`), but Default.aspx + CapHome ribbons render server-side enough to enumerate tabs and module state; record search requires VIEWSTATE postbacks and is deferred to the next browser pass. `User-Agent: Mozilla/5.0 (compatible; CountyDataMapper/1.0)` was used throughout (per the Lake Hamilton finding that bare UAs can be rejected on vendor subdomains).

## Summary

- **Jurisdiction:** City of Lake Alfred (within Polk County, FL).
- **City website platform:** CivicPlus CivicEngage. Classic numeric-ID URL pattern (`/{numeric-id}/{slug}`, e.g. `/166/Building-Permits`). Canonical host `www.mylakealfred.com`. Footer "Government Websites by CivicPlus®". Same shape as Haines City / Winter Haven / Lake Hamilton — reuses `/RSSFeed.aspx`, `/AgendaCenter`, `/DocumentCenter`, `/Archive.aspx`, `/Calendar.aspx`, `/common/modules/iCalendar/iCalendar.aspx`, `/ImageRepository/Document`, `/antiforgery`, `/sitemap.xml`, `/robots.txt`.
- **Commission surface:** **No external commission platform** (no Legistar, eScribe, CivicClerk, Granicus ViewPublisher, Municode Meetings). City Commission, Planning & Zoning Board, CRA Board, Parks & Recreation Board, Code Enforcement Special Magistrate, School Zone Speed Enforcement Special Magistrate all served from the CivicPlus `/AgendaCenter` with PDFs at `/AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{id}`. The CR adapter (`modules/commission/config/jurisdictions/FL/lake-alfred-cc.yaml`) is already configured with `platform: civicplus`, `category_id: 2`. Category IDs observed via search HTML: `15`, `16` (CIDs surfaced by `/AgendaCenter/Search/`), plus distinct CIDs for CC, P&Z, CRA, Parks & Rec, Code-Enforcement Magistrate, and School-Zone Magistrate via `RSSFeed.aspx?ModID=65`.
- **Permit surface:** **Accela Citizen Access** at `aca-prod.accela.com/COLA` (agency code **COLA**). Building Permits page on the CMS (`/166/Building-Permits`) links out to `https://aca-prod.accela.com/COLA/Default.aspx`. **Enforcement** module is also public anon (200 with populated tab ribbon, ~473 KB). **Building** and **Enforcement** are the only anon-exposed modules — `Planning`, `Licenses`, `LandDev` all return 302 redirects with no content. Accela REST v4 at `/v4/agency/COLA` returns 404 (expected per `accela-rest-probe-findings.md`). ⚠️ **Seed-script bug discovered:** `seed_pt_jurisdiction_config.py` currently declares Lake Alfred as iWorQ. That is a copy-paste bug. The production adapter (`modules/permits/scrapers/adapters/lake_alfred.py`) is Accela-based. Lake Alfred has **no** iWorQ tenant — `mylakealfred.portal.iworq.net` and similar variants are not referenced from the CMS. A separate task has been spawned to fix the seed script; this map reflects the live Accela reality.
- **GIS / Planning & Zoning:** City of Lake Alfred operates its own ArcGIS Online org (`services3.arcgis.com/VaAx8WnigGGWjIPd`) with **8 published FeatureServer services**. Primary planning layer `City_of_Lake_ALfred_Planning_WFL1/FeatureServer/0` returned **2013 features** (parcel-level with FLU, zoning, annexation ordinance, PUD, and Green Swamp designation attributes). Separate services for `Lake_Alfred_Zoning`, `LA_FLU_ZN_June_2023`, `LA_City_Boundary2024`, `COLA_Zoning`, and two 2025-dated planning layers (`City_of_Lake_Alfred_Planning_12_2025`, `City_of_Lake_Alfred_Planning_2025_WFL1`). Distinct from Polk County's enterprise ArcGIS — this is a city-owned GIS. Two public webmaps are linked from `/180/Planning-Zoning`.
- **Code of ordinances (ULDC / LDC):** **No Municode Library, no American Legal, no amlegal.com subdomain.** The Unified Land Development Code is distributed as a **PDF linked from `/DocumentCenter/View/2510`** (title "Unified Land Development Code (ULDC) - Interim SB180 - Effective 11/03/2025"). ⚠️ GAP: no searchable code platform — CD2 ingestion must parse the PDF. ⚠️ GAP: full-history chapter index not verified (may exist elsewhere on the CMS — cross-check on next browser pass).
- **Utility billing surface:** `point-pay.mylakealfred.com:8443/ubs1/index.html` (Point & Pay subdomain) — payment-only outbound portal, returns 404 on HEAD but is linked as "Pay Utility Bill" from the homepage. Not deep-probed (out of scope for BI/PT/CR/CD2).
- **Support / helpdesk:** `user.govoutreach.com/lakealfredcityfl/support.php` — GovOutreach/Gov2Go Granicus support portal. Outbound only.
- **Chat widget:** `app.polimorphic.com/react/organizations/lake_alfred_fl/chat` — Polimorphic AI chat SPA. Outbound only.
- **DocAccess:** `docaccess.com/docbox.js` — document-accessibility JS shim loaded inline. Not a data surface.
- **No Tyler eSuite / ProjectDox / OpenGov / Column / SeeClickFix / Civilspace / Citibot** observed on the Lake Alfred footprint (unlike Winter Haven which had all of these).
- **Property appraiser / parcel data:** Polk County Property Appraiser at `polkpa.org` — out-of-hostname, mapped under `polk-county-fl.md`.
- **robots.txt stance:** Same CivicPlus default template as Haines City / Winter Haven / Lake Hamilton — disallows `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx`; Baiduspider and Yandex blanket-denied; Siteimprove throttled to 20-second crawl-delay. Accela `aca-prod.accela.com/robots.txt` returned **404** (no robots at that path). Per refined §3.2 treated as operational-risk signal only.
- **Total requests this run:** ~48 (well under the 2000 cap). No 429s, no captcha challenges.

## Platform Fingerprint

| Host | Platform | Fingerprint |
|---|---|---|
| `www.mylakealfred.com` | **CivicPlus CivicEngage** | `/{numeric-id}/{slug}` URL pattern; `/antiforgery` bootstrap JSON; `/RSSFeed.aspx?ModID=…` feed index via `/rss.aspx`; ASP.NET session cookies; "Government Websites by CivicPlus®" footer. Same template as Haines City, Winter Haven, Lake Hamilton, Davenport, Dundee. |
| `aca-prod.accela.com/COLA` | **Accela Citizen Access** | `ng-app="appAca"`, Cloudflare edge, agency code `COLA` (Accela already in `_platforms.md`). Default.aspx embedded JS enumerates tabs: `Home`, `Building`, `Enforcement` (active); `Planning`, `Licenses`, `LandDev` → 302 (not anon-exposed). Record search is VIEWSTATE postback — landings curl-observable but detail pulls need browser. Adapter: `modules/permits/scrapers/adapters/lake_alfred.py` (`agency_code=COLA`, `module_name=Building`). |
| `services3.arcgis.com/VaAx8WnigGGWjIPd` | **ArcGIS REST / Hosted FeatureServers** | City of Lake Alfred's own ArcGIS Online org. 8 services enumerated at the `/services?f=json` root. Already in `_platforms.md`. |
| `www.arcgis.com/sharing/rest/content/items/{itemId}` | **ArcGIS Online web-map registry** | Webmap item IDs embedded on `/180/Planning-Zoning` → `?webmap=99258f12…` and `?webmap=c3a12ad3…`. `sharing/rest/content/items/{id}/data?f=json` returns the operational-layer JSON. |
| `point-pay.mylakealfred.com:8443` | **Point & Pay (utility payments)** | Outbound payment portal; HEAD returns 404 but the homepage links `/ubs1/index.html`. Not deep-probed. ⚠️ Candidate for `_platforms.md` addition on next housekeeping pass. |
| `user.govoutreach.com/lakealfredcityfl` | **GovOutreach / Gov2Go (Granicus support)** | Outbound support/helpdesk portal. Not a data surface. ⚠️ Candidate for `_platforms.md`. |
| `app.polimorphic.com/react/organizations/lake_alfred_fl` | **Polimorphic (AI chat)** | React-SPA chat widget embedded as iframe on the CMS homepage. Not a data surface. ⚠️ Candidate for `_platforms.md`. |
| `docaccess.com/docbox.js` | **DocAccess** | Third-party document-accessibility JS shim. Not a data surface. |

No net-new platforms with a data surface — CivicPlus + Accela + ArcGIS are all already in `_platforms.md`. Point & Pay, GovOutreach, and Polimorphic are payment/support/chat outbounds that have not yet been promoted into the registry; deferred to a housekeeping pass.

---

## APIs

### /antiforgery

#### CivicPlus antiforgery token

- **URL:** `https://www.mylakealfred.com/antiforgery`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Issues a CivicPlus CSRF token used on any same-origin form POST against the CivicEngage site.
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
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** real-time (per-session).
- **Discovered via:** Inline `getAntiForgeryToken` script in the home HTML that bootstraps CSRF tokens into CivicEngage form POSTs.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/antiforgery'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-antiforgery.json`
- **Notes:** Token is submitted as `__RequestVerificationToken` on same-origin POSTs. Not useful for data extraction; it's the gate for POST-driven search/contact forms.

### /sitemap.xml

#### CivicPlus sitemap

- **URL:** `https://www.mylakealfred.com/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full URL enumeration for every server-rendered page on the CivicEngage site (110 entries).
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
- **Pagination:** `none` — all 110 entries inline.
- **Rate limits observed:** none
- **Data freshness:** CMS-managed; `lastmod` values span 2023–2026.
- **Discovered via:** Referenced in `/robots.txt`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/sitemap.xml'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-sitemap.xml`
- **Notes:** Primary drift-target list. 110 URLs is mid-size for a Polk-county city (between Lake Hamilton's 100 and Winter Haven's 350).

### /robots.txt

#### robots.txt

- **URL:** `https://www.mylakealfred.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots exclusion rules (plain text).
- **Response schema:** standard robots.txt format.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static.
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/robots.txt'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-robots.txt`
- **Notes:** Identical CivicPlus default template as the other Polk-county cities — blocks `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx`. Baiduspider + Yandex blanket-denied. Siteimprove throttled to 20-second crawl-delay.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed on this tenant (via `/rss.aspx`): `1` (News Flash), `51` (Blog), `53` (Photo/Banner), `58` (Calendar), `63` (Alert Center), `64` (Real Estate Locator), `65` (Agenda Creator), `66` (Jobs). Each optionally accepts a `CID` category filter. Feed shape is standard RSS 2.0 across all ModIDs (see §Winter Haven map for detailed schema — identical here).

#### News Flash RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
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
  - `CID` (string, optional) — category filter. Observed: `All-newsflash.xml`, `Home-1`.
- **Probed parameters:**
  - `unverified` — not exercised beyond the two observed CIDs.
- **Pagination:** `none` (trailing window).
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** real-time (CMS-driven).
- **Discovered via:** `/rss.aspx` HTML index.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=1'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid1.xml`
- **Notes:** 1618 bytes — lightly populated. Drift-detection sentinel.

#### Blog RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog posts (empty on this tenant).
- **Response schema:** RSS 2.0 (same shape as News Flash).
- **Observed parameters:** `ModID=51`, `CID=All-blog.xml`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton-only (327 bytes) at survey time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=51&CID=All-blog.xml'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid51.xml`
- **Notes:** Drift sentinel. Blog module is present but unpopulated.

#### Photo / Banner RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Photo/banner module items (empty skeleton).
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=53`, `CID=All-0`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton (362 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid53.xml`
- **Notes:** Low-value for this codebase's modules; cataloged for completeness.

#### Calendar RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming city calendar events (populated — 11 KB at survey).
- **Response schema:** RSS 2.0 with `calendarEvent:` XML namespace.
- **Observed parameters:**
  - `ModID=58` (int, required).
  - `CID` (string, optional) — observed `All-calendar.xml`, `Main-Calendar-14`, `Parks-and-Recreation-3`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=58&CID=All-calendar.xml'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid58.xml`
- **Notes:** Calendar main category = 14 (matches `iCalendar.aspx?catID=14`). `calendarEvent:*` namespace sub-elements not enumerated in this pass. ⚠️ GAP: enumerate on next run.

#### Alert Center RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CivicAlerts items (empty skeleton at survey).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=63` (int, required).
  - `CID` (string, optional) — observed `All-0`, `Emergency-Alerts-6`, `Information-Alerts-5`, `Office-Closures-`, `Road-Closures-8`, `Water-Advisory-9`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton (339 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=63&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid63.xml`
- **Notes:** Useful drift sentinel for emergency/water-advisory alerts.

#### Real Estate Locator RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Real-estate locator listings (empty skeleton).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=64` (int, required).
  - `CID` (string, optional) — observed `All-0`, `Commercial-Properties-For-Rent-`, `Commercial-Properties-For-Sale-1`, `Residential-Properties-For-Rent-4`, `Residential-Properties-For-Sale-3`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** skeleton (351 bytes).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=64&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid64.xml`
- **Notes:** Module configured with residential/commercial categories but no listings at survey time. Worth re-checking — if populated, this could surface BI-adjacent property listings.

#### Agenda Creator RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** AgendaCenter category feed (lightly populated — 744 bytes at survey).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=65` (int, required).
  - `CID` (string, optional) — observed `All-0`, `City-Commission-`, `Code-Enforcement-Special-Magistrate-4`, `Community-Redevelopment-Agency-Board-6`, `Parks-Recreation-Board-5`, `Planning-Zoning-Board-3`, `School-Zone-Speed-Enforcement-Special-Ma-`.
- **Probed parameters:**
  - `unverified` — CID numeric suffix mapping to body not fully enumerated.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time but lightly populated.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?ModID=65&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid65.xml`
- **Notes:** Primary CR-relevant feed. CID numeric IDs (3 = Planning & Zoning Board, 4 = Code Enforcement Special Magistrate, 5 = Parks & Rec Board, 6 = CRA Board; City Commission and School-Zone Magistrate numeric IDs are not present in the observed slugs — likely they trail the hyphen suffix). The CR adapter uses `category_id=2` from the YAML — ⚠️ GAP: confirm `category_id=2` maps to CC vs rest; the RSS CID namespace and the AgendaCenter `/AgendaCenter/Search?CIDs=…` namespace may diverge.

#### Jobs RSS

- **URL:** `https://www.mylakealfred.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Open job postings (populated — 33 KB at survey).
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=66` (int, required).
  - `CommunityJobs` (bool, optional) — observed `False` on the `/rss.aspx` canonical URL.
  - `CID` (string, optional) — observed `All-0`, `Community-Development-98`, `Finance-99`, `Fire-103`, `General-Services-104`, `Parks-Recreation-101`, `Police-10`, `Public-Works-Utilities-100`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/RSSFeed.aspx?CommunityJobs=False&ModID=66&CID=All-0'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-rssfeed-modid66.xml`
- **Notes:** Out-of-scope for BI/PT/CR/CD2 but cataloged per §8 "document everything."

### /AgendaCenter/

The AgendaCenter search endpoint returns HTML (classified API per §4.2 as the query surface — listing is HTML but the URL+querystring are the structured interface the CR adapter consumes). The CR pipeline already uses this path (`modules/commission/config/jurisdictions/FL/lake-alfred-cc.yaml`, `platform: civicplus`, `category_id: 2`). No JSON variant was discovered.

#### AgendaCenter search

- **URL:** `https://www.mylakealfred.com/AgendaCenter/Search/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML listing of agenda/minutes records. Record links take the form `/AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{id}` and `/AgendaCenter/ViewFile/Minutes/_{MMDDYYYY}-{id}` and resolve (via 302) to the PDF.
- **Response schema:** HTML. Record links embedded:
  ```
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}            # PDF
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}?html=true  # HTML variant
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}?packet=true # full packet
  ```
- **Observed parameters:**
  - `term` (string, optional) — free-text search.
  - `CIDs` (string, optional) — comma-separated category IDs or `all`. Observed CIDs in search HTML: `15`, `16`, `all`.
  - `startDate` (string, optional) — MM/DD/YYYY.
  - `endDate` (string, optional) — MM/DD/YYYY.
  - `dateRange` (string, optional) — preset selector.
  - `dateSelector` (string, optional) — UI state passthrough.
- **Probed parameters:**
  - `CIDs=all` with empty other params returned HTML listing with **23 unique ViewFile links** spanning Jan 2026 → forward-dated meetings. Same shape as Winter Haven / Haines City.
  - `POST /AgendaCenter/UpdateCategoryList` — not exercised; sibling tenants have returned 404 for this endpoint.
- **Pagination:** `unverified` — listing fit in one response at survey time.
- **Rate limits observed:** none.
- **Data freshness:** real-time (CMS).
- **Discovered via:** `/AgendaCenter` root page JS (`onSearch` handler).
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/AgendaCenter/Search/?term=&CIDs=all&startDate=&endDate=&dateRange=&dateSelector='
  ```
- **Evidence file:** `evidence/lake-alfred-fl-agenda-search.html`
- **Notes:** CR adapter already uses `https://www.mylakealfred.com/AgendaCenter` with `category_id: 2`. ⚠️ GAP: the adapter's `category_id=2` does not appear among the CIDs observed in the search HTML (`15`, `16`). Confirm whether `category_id: 2` in the YAML refers to a different taxonomy (e.g., body ID used by the CivicPlus adapter, vs the CID surfaced in search URL params). Cross-reference `cr/adapters/civicplus.py` on next run.

### /common/modules/iCalendar/iCalendar.aspx

#### iCal calendar feed

- **URL:** `https://www.mylakealfred.com/common/modules/iCalendar/iCalendar.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RFC 5545 iCalendar feed (VCALENDAR / VEVENT) for the Main Calendar. 180 KB at survey — populated.
- **Response schema:** iCalendar (RFC 5545):
  ```
  BEGIN:VCALENDAR
  VERSION:2.0
  PRODID:string
  BEGIN:VEVENT
  UID:string
  DTSTART:YYYYMMDDTHHMMSS
  DTEND:YYYYMMDDTHHMMSS
  SUMMARY:string
  DESCRIPTION:string
  LOCATION:string
  URL:url
  END:VEVENT
  END:VCALENDAR
  ```
- **Observed parameters:**
  - `feed` (string, required) — observed `calendar`.
  - `catID` (int, required) — observed `14` (Main Calendar).
- **Probed parameters:**
  - `catID=3` (Parks & Recreation per the RSS-feed slug namespace) — not exercised. ⚠️ GAP.
- **Pagination:** `none` — single rolling window.
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** Calendar.aspx page action buttons ("Subscribe to iCalendar").
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-calendar-ics.ics`
- **Notes:** Structured feed preferred over Calendar.aspx HTML for event-extraction. Same shape as other CivicPlus tenants (Haines City / Winter Haven).

### /ImageRepository/Document

#### Image repository doc fetch

- **URL:** `https://www.mylakealfred.com/ImageRepository/Document`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary image/PDF blob for a given `documentID` integer.
- **Response schema:** binary (content-type varies — PNG/JPG/PDF).
- **Observed parameters:**
  - `documentID` (int, required) — tested `1331` → 200, 11214 bytes.
- **Probed parameters:**
  - `unverified` — ID space is sparse and enumerable but was not swept.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** Referenced inline from home HTML (`ImageRepository/Document?documentID=1331`).
- **curl:**
  ```bash
  curl 'https://www.mylakealfred.com/ImageRepository/Document?documentID=1331'
  ```
- **Evidence file:** _(binary — not re-captured; observed via HEAD/GET probe logged in request log)_
- **Notes:** CivicPlus-standard image/PDF fetch. Complements `/DocumentCenter/View/{id}/{slug}` for non-document media. ID space appears shared with DocumentCenter but uses a different route shape.

### Accela Citizen Access (`aca-prod.accela.com/COLA`)

Accela tenant for Lake Alfred is `COLA` (City Of Lake Alfred). Anonymous browsing exposes the **Building** and **Enforcement** modules with populated tab ribbons; `Planning`, `Licenses`, `LandDev` return 302 redirects (likely module-disabled or auth-gated for anon). Record search requires VIEWSTATE postbacks and is deferred to a browser pass.

#### Accela Default.aspx (tab metadata)

- **URL:** `https://aca-prod.accela.com/COLA/Default.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML landing with an embedded JavaScript data structure enumerating the tenant's tabs, modules, and associated URLs. Not JSON but machine-parseable.
- **Response schema:** HTML with inline JS-encoded array-of-records. Observed module labels: `Home`, `Building`, `Enforcement`. Record fields per tab entry: `Active`, `Label`, `Key`, `Title`, `URL`, `Module`, `Order`.
- **Observed parameters:** none on the root; query params live on downstream URLs.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none at ~1 req/sec. Cloudflare front.
- **Data freshness:** real-time (tenant configuration).
- **Discovered via:** Link from `https://www.mylakealfred.com/166/Building-Permits` (confirmed external navigation target).
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/COLA/Default.aspx'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-accela-Default.aspx.html`
- **Notes:** `aca-prod.accela.com/cola/` (lowercase) returns 301 → `/COLA/Default.aspx`. Use mixed-case `COLA` directly.

#### Accela CapHome — Building module

- **URL:** `https://aca-prod.accela.com/COLA/Cap/CapHome.aspx`
- **Method:** `GET`
- **Auth:** `none` for the landing ribbon; record search requires session cookies + VIEWSTATE postbacks.
- **Data returned:** Accela Citizen Access module landing page with tabs, search input, and VIEWSTATE. Records retrieved via ASP.NET WebForms postback (not curl-friendly).
- **Response schema:** HTML/ASPX with `__VIEWSTATE`, `__EVENTVALIDATION` tokens.
- **Observed parameters:**
  - `module` (string, required) — values: `Building` (200, populated), `Enforcement` (200, populated), `Planning` (302), `Licenses` (302), `LandDev` (302).
  - `TabName` (string, optional) — `Building`, `Enforcement`, `Home`.
  - `IsToShowInspection` (bool, optional) — `yes` on "Schedule an Inspection" child link.
- **Probed parameters:**
  - All five `module` values — only `Building` and `Enforcement` returned anon-accessible content.
  - Sort/filter/pagination on GET — not exposed; all postback-driven.
- **Pagination:** `none` via GET; postback-driven on search results.
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** real-time.
- **Discovered via:** Accela Default.aspx tab metadata + `/166/Building-Permits` outbound link.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/COLA/Cap/CapHome.aspx?module=Building&TabName=Building'
  curl 'https://aca-prod.accela.com/COLA/Cap/CapHome.aspx?module=Enforcement&TabName=Enforcement'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-accela-CapHome-Building.html` (477 KB), `evidence/lake-alfred-fl-accela-CapHome-Enforcement.html` (473 KB)
- **Notes:** Production adapter `modules/permits/scrapers/adapters/lake_alfred.py` targets `module=Building`, `target_record_type="Building/Residential/New/NA"`. This survey confirms **Enforcement** is also anon-exposed — a potential future target if code-enforcement records are needed. ⚠️ GAP: anon record-search behavior needs browser verification; `accela-rest-probe-findings.md` notes anon-blocked on v4 REST, which this run re-confirmed (`/v4/agency/COLA` → 404).

#### Accela CapDetail.aspx (record detail pattern)

- **URL:** `https://aca-prod.accela.com/COLA/Cap/CapDetail.aspx`
- **Method:** `GET`
- **Auth:** `session cookie` (derived from a preceding search postback). Not exercised anonymously in this pass.
- **Data returned:** Per-record permit/enforcement detail page (ASPX with VIEWSTATE). Standard Accela shape shared with COWH / POLKCO / etc.
- **Response schema:** HTML/ASPX — record-detail layout is Accela-template-standard.
- **Observed parameters:**
  - `Module` (string, required) — `Building` or `Enforcement`.
  - `TabName` (string, required) — mirrors `Module`.
  - `capID` (string, required) — record identifier, three-part form `X-Y-Z` (e.g. `24BLD-0001`). **Not observed** from this anon-only pass — requires a successful search.
- **Probed parameters:** `unverified` — no real `capID` available without session.
- **Pagination:** `none` (single record).
- **Rate limits observed:** `unverified`.
- **Data freshness:** real-time.
- **Discovered via:** Accela platform-standard URL pattern (cross-ref `polk-county-fl.md`, `winter-haven-fl.md`).
- **curl:**
  ```bash
  # capID required — pattern documented for future session-aware probe
  curl 'https://aca-prod.accela.com/COLA/Cap/CapDetail.aspx?Module=Building&TabName=Building&capID=<X>-<Y>-<Z>'
  ```
- **Evidence file:** _(not captured — needs session)_
- **Notes:** ⚠️ GAP: capture a real record detail on the next browser-enabled pass.

#### Accela APO / Property Lookup

- **URL:** `https://aca-prod.accela.com/COLA/APO/APOLookup.aspx`
- **Method:** `GET`
- **Auth:** `none` to render; results via postback.
- **Data returned:** Property / parcel lookup form (anonymous, Accela-standard).
- **Response schema:** HTML/ASPX (~412 KB landing).
- **Observed parameters:**
  - `TabName` (string, optional) — observed `Home`.
- **Probed parameters:** `unverified` — landing fetched but postback not exercised.
- **Pagination:** `none` via GET.
- **Rate limits observed:** none.
- **Data freshness:** real-time.
- **Discovered via:** Accela Default.aspx tab metadata.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/COLA/APO/APOLookup.aspx?TabName=Home'
  ```
- **Evidence file:** _(not captured — landing only; identical shape to COWH / POLKCO APO pages)_
- **Notes:** Public property lookup — could be a useful parcel-resolver if it works anonymously. ⚠️ GAP: exercise postback on next pass.

#### Accela v4 REST (blocked anon)

- **URL:** `https://aca-prod.accela.com/v4/agency/COLA`
- **Method:** `GET`
- **Auth:** `none` (expected to be blocked).
- **Data returned:** REST v4 agency payload — **blocked with HTTP 404** on this tenant, consistent with `docs/api-maps/accela-rest-probe-findings.md`.
- **Response schema:** n/a (404).
- **Observed parameters:** none.
- **Probed parameters:** none.
- **Pagination:** `none`.
- **Rate limits observed:** none.
- **Data freshness:** n/a.
- **Discovered via:** Accela platform-standard endpoint probe.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/v4/agency/COLA'
  ```
- **Evidence file:** _(HTTP 404 — not captured; 1245-byte Accela error body)_
- **Notes:** Confirms project-wide finding that Accela v4 REST is unavailable for bulk anonymous extraction across FL agencies. HTML scraping remains the primary path.

### ArcGIS FeatureServers (`services3.arcgis.com/VaAx8WnigGGWjIPd`)

City of Lake Alfred's own ArcGIS Online org. Services enumerated at the root; individual FeatureServer layers exposed per layer ID.

#### Services root directory

- **URL:** `https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** List of FeatureServer services published by the City of Lake Alfred's ArcGIS Online org.
- **Response schema:**
  ```
  {
    "currentVersion": int,
    "services": [
      { "name": "string", "type": "string", "url": "string" }
    ]
  }
  ```
- **Observed parameters:**
  - `f` (string, required for JSON) — `json`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** real-time.
- **Discovered via:** Webmap item JSON (`/sharing/rest/content/items/{id}/data?f=json`).
- **curl:**
  ```bash
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services?f=json'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-arcgis-servicesroot.json`
- **Notes:** Enumerates 8 services: `COLA_Zoning`, `LA_City_Boundary2024`, `LA_FLU_ZN_June_2023`, `Lake_Alfred_Zoning`, `City_of_Lake_ALfred_Planning_WFL1`, `City_of_Lake_Alfred_Planning_12_2025`, `City_of_Lake_Alfred_Planning`, `City_of_Lake_Alfred_Planning_2025_WFL1`. Multiple versions suggest historical snapshots preserved alongside current — pick the "2025" or "WFL1" variants for freshest data.

#### Planning FeatureServer (WFL1 — current primary)

- **URL:** `https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/City_of_Lake_ALfred_Planning_WFL1/FeatureServer`
- **Method:** `GET` (service metadata); `GET` on `/{layerId}/query` for features.
- **Auth:** `none`
- **Data returned:** Service metadata with layer list. Layer 0: `LA_FLU_ZN_June_2025` (Feature Layer, 2013 features at survey). Layer 6: `LA_City_Boundary2024` (Feature Layer).
- **Response schema:**
  ```
  {
    "currentVersion": float,
    "serviceDescription": "string",
    "hasStaticData": bool,
    "layers": [ { "id": int, "name": "string", "type": "string" } ],
    "tables": []
  }
  ```
- **Observed parameters:**
  - `f` (string, required for JSON) — `json`.
- **Probed parameters:**
  - `/0/query?where=1%3D1&returnCountOnly=true&f=json` → `{"count":2013}`.
  - `/0/query?where=1%3D1&outFields=*&resultRecordCount=3&f=json` → 3-feature sample with attribute keys `FID`, `PUD`, `Parcel_Id`, `ANNEX_ORD`, `COMMENTS`, `FLU_ORD`, `ZON_ORD`, `Zon_Distri`, `Green_Swam`, `FLU_20`, `ZON_20`, `F2021_Comm`, `Shape__Area`, `Shape__Length`.
- **Pagination:** ArcGIS-standard `resultOffset` / `resultRecordCount` (default page size ~1000; `exceededTransferLimit` flag).
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** service name suffix `June_2025` and `2024` boundary layer suggest semi-annual refresh cadence.
- **Discovered via:** Webmap `99258f1286934a699c242ff2d93bc3ad` (linked from `/180/Planning-Zoning`).
- **curl:**
  ```bash
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/City_of_Lake_ALfred_Planning_WFL1/FeatureServer?f=json'
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/City_of_Lake_ALfred_Planning_WFL1/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=3&f=json'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-arcgis-planning-fs.json`, `evidence/lake-alfred-fl-arcgis-planning-0-query-count.json`, `evidence/lake-alfred-fl-arcgis-planning-0-sample.json` (truncated to 5 features per §6)
- **Notes:** **Primary parcel-level planning/zoning layer** — `Parcel_Id`, `FLU_20`, `ZON_20`, `ANNEX_ORD`, `FLU_ORD`, `ZON_ORD` are all present. Excellent candidate for BI/CD2 ingestion. The "12_2025" and "2025_WFL1" services are likely newer revisions — ⚠️ GAP: diff service schemas and pick the canonical current layer.

#### Zoning FeatureServer

- **URL:** `https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/Lake_Alfred_Zoning/FeatureServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standalone zoning layer (`ZONING_CATERGORIES`, layer 0).
- **Response schema:** ArcGIS FeatureServer (same shape as Planning service above).
- **Observed parameters:** `f=json`.
- **Probed parameters:** `/0/query?returnCountOnly=true` → 200 (count not captured this pass).
- **Pagination:** standard `resultOffset` / `resultRecordCount`.
- **Rate limits observed:** none.
- **Data freshness:** `unverified` (no date suffix in name).
- **Discovered via:** Webmap `c3a12ad316774f838630c9ce3ecebd5b` (linked from `/180/Planning-Zoning`).
- **curl:**
  ```bash
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/Lake_Alfred_Zoning/FeatureServer?f=json'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-arcgis-zoning-fs.json`
- **Notes:** Typo in layer name `CATERGORIES` (sic) — preserved by the vendor. Separate from the `Planning_WFL1/6` boundary and the `COLA_Zoning` alt service — possibly a consumer-facing simplified cut.

#### Future Land Use (June 2023 snapshot) FeatureServer

- **URL:** `https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/LA_FLU_ZN_June_2023/FeatureServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** FLU (Future Land Use) layer, June 2023 snapshot (layer 0).
- **Response schema:** ArcGIS FeatureServer.
- **Observed parameters:** `f=json`.
- **Probed parameters:** `/0/query?returnCountOnly=true` → 200.
- **Pagination:** standard.
- **Rate limits observed:** none.
- **Data freshness:** snapshot-dated (June 2023 — 2 years stale relative to the `June_2025` layer in the primary planning service).
- **Discovered via:** Linked from `Planning_WFL1` webmap.
- **curl:**
  ```bash
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/LA_FLU_ZN_June_2023/FeatureServer?f=json'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-arcgis-flu-fs.json`
- **Notes:** Historical snapshot — prefer the `_WFL1` primary service for current FLU state.

#### Additional FeatureServers (not deep-probed)

Services enumerated at the root but not probed beyond the service-root listing:

- `COLA_Zoning/FeatureServer` — likely alternate / original zoning cut.
- `LA_City_Boundary2024/FeatureServer` — city boundary polygon.
- `City_of_Lake_Alfred_Planning_12_2025/FeatureServer` — December 2025 planning snapshot.
- `City_of_Lake_Alfred_Planning/FeatureServer` — base planning service (no date suffix).
- `City_of_Lake_Alfred_Planning_2025_WFL1/FeatureServer` — alt 2025 planning WFL1.

- **URL:** (see above)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Planning / zoning / boundary layers at various snapshot dates.
- **Response schema:** ArcGIS FeatureServer (same shape).
- **Observed parameters:** `f=json`.
- **Probed parameters:** not deep-probed this pass.
- **Pagination:** standard.
- **Rate limits observed:** none.
- **Data freshness:** mixed (2023–2025).
- **Discovered via:** `/arcgis/rest/services?f=json`.
- **curl:**
  ```bash
  curl 'https://services3.arcgis.com/VaAx8WnigGGWjIPd/arcgis/rest/services/City_of_Lake_Alfred_Planning_2025_WFL1/FeatureServer?f=json'
  ```
- **Evidence file:** _(covered by `arcgis-servicesroot.json` root enumeration — per-service JSON not captured for these five)_
- **Notes:** ⚠️ GAP: diff the five remaining services against `_WFL1` (primary) and pick canonical. Likely only the newest `_12_2025` + `_2025_WFL1` are actively maintained; the others are historical snapshots.

### ArcGIS Online web-map registry

#### Web-map item metadata

- **URL:** `https://www.arcgis.com/sharing/rest/content/items/{itemId}/data`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Operational-layer JSON for an ArcGIS Online web-map, including basemap, layer references (with service URLs), and popup configuration.
- **Response schema:** ArcGIS Online web-map spec (operationalLayers[], baseMap{}, version, authoringApp, spatialReference{}, bookmarks[], …).
- **Observed parameters:**
  - `f` (string, required for JSON) — `json`.
- **Probed parameters:**
  - `/items/{id}` (without `/data`) returns the item descriptor (title, owner, tags); `/items/{id}/data` returns the actual web-map JSON.
- **Pagination:** `none`.
- **Rate limits observed:** none.
- **Data freshness:** real-time (mtime on the AGOL item).
- **Discovered via:** webmap query strings on `/180/Planning-Zoning` (`?webmap=99258f12…` and `?webmap=c3a12ad3…`).
- **curl:**
  ```bash
  curl 'https://www.arcgis.com/sharing/rest/content/items/99258f1286934a699c242ff2d93bc3ad/data?f=json'
  curl 'https://www.arcgis.com/sharing/rest/content/items/c3a12ad316774f838630c9ce3ecebd5b/data?f=json'
  ```
- **Evidence file:** `evidence/lake-alfred-fl-arcgis-webmap1.json`, `evidence/lake-alfred-fl-arcgis-webmap2.json`
- **Notes:** ArcGIS Online's public item API. Useful for resolving user-facing webmap links to the underlying FeatureServer URLs. Not tenant-specific — same endpoint serves any public AGOL item.

---

## Scrape Targets

### / (CivicPlus CivicEngage content pages)

Every `www.mylakealfred.com/{numeric-id}/{slug}` page is server-rendered HTML. Representative pages probed this run:

#### City home

- **URL:** `https://www.mylakealfred.com/`
- **Data available:** Site navigation, featured news/alerts, quicklinks, department drill-down, footer with vendor links (Point & Pay, GovOutreach, DocAccess, Polimorphic).
- **Fields extractable:** News Flash teasers (or use RSS); quicklink categorized navigation; outbound vendor URLs.
- **JavaScript required:** no — core content in initial HTML. Chat widget (Polimorphic) is JS-embedded but not required for content.
- **Anti-bot measures:** none observed.
- **Pagination:** n/a.
- **Selectors (if stable):** Standard CivicPlus layout; stable across tenants.
- **Why no API:** News Flash and Calendar have RSS + iCal feeds (documented). The homepage itself is a composite page with no structured export.
- **Notes:** ~122 KB at survey.

#### Your Government hub

- **URL:** `https://www.mylakealfred.com/27/Your-Government`
- **Data available:** Index of boards/committees, City Commission, City Manager, meeting/holiday schedule.
- **Fields extractable:** Board/committee roster, bios; redirects for meeting materials point to AgendaCenter.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** generic CivicPlus.
- **Why no API:** Commission/board rosters not exposed as JSON/RSS.
- **Notes:** CR pipeline hits AgendaCenter directly; this page is a human-facing index.

#### Community Development + department subpages

- **URLs:**
  - `https://www.mylakealfred.com/161/Community-Development`
  - `https://www.mylakealfred.com/162/Applications-Forms`
  - `https://www.mylakealfred.com/163/Zoning-Land-Use-Resources`
  - `https://www.mylakealfred.com/166/Building-Permits`
  - `https://www.mylakealfred.com/167/Business-Tax-Receipts`
  - `https://www.mylakealfred.com/168/Code-Enforcement`
  - `https://www.mylakealfred.com/169/Community-Redevelopment-Area` (and `/300/Community-Redevelopment-Area`)
  - `https://www.mylakealfred.com/170/CRA-Grant-Programs`
  - `https://www.mylakealfred.com/171/Downtown-Master-Plan`
  - `https://www.mylakealfred.com/172/Floodplain-Information`
  - `https://www.mylakealfred.com/179/Lien-Searches`
  - `https://www.mylakealfred.com/180/Planning-Zoning`
  - `https://www.mylakealfred.com/181/Unified-Land-Development-Code`
- **Data available:** Static department content (descriptions, application forms as PDFs, outbound links to Accela Citizen Access, ArcGIS webmaps).
- **Fields extractable:** Document links in `/DocumentCenter/View/{id}/{slug}` form; outbound vendor URLs (Accela, ArcGIS, Point & Pay).
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** Standard CivicPlus.
- **Why no API:** Static curated pages — no structured export. The PDFs they link are individually fetchable via DocumentCenter.
- **Notes:** **`/166/Building-Permits` is the primary discovery hub** for the Accela COLA tenant (outbound link confirmed this run). **`/180/Planning-Zoning` is the discovery hub for the ArcGIS Online webmaps**. **`/181/Unified-Land-Development-Code` links directly to a PDF at `/DocumentCenter/View/2510`** — no Municode Library, no American Legal. ⚠️ GAP: the ULDC PDF is the full LDC corpus for this city; CD2 ingestion must parse the PDF.

#### AgendaCenter index

- **URL:** `https://www.mylakealfred.com/AgendaCenter`
- **Data available:** HTML listing of agenda categories and file links (per-body filters).
- **Fields extractable:** agenda keys `_{MMDDYYYY}-{id}` → resolve to PDFs at `/AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{id}`.
- **JavaScript required:** minimal (search uses `onSearch` handler → GET `/AgendaCenter/Search/`).
- **Anti-bot measures:** none.
- **Pagination:** via `/AgendaCenter/Search/` (documented in APIs).
- **Selectors:** CivicPlus AgendaCenter standard DOM.
- **Why no API cataloged here:** `AgendaCenter/Search/` GET (documented in APIs) is the structured query surface. RSS `ModID=65` is the feed (documented in APIs).
- **Notes:** Used by the CR pipeline. Bodies visible: City Commission, Planning & Zoning Board, CRA Board, Parks & Rec Board, Code Enforcement Special Magistrate, School Zone Speed Enforcement Special Magistrate, General Employees Retirement Board, Police & Fire Retirement Board. Per the user's `feedback_skip_boa_zba.md` rule, no Board of Adjustment / Zoning Board of Adjustment is tracked — none present on this tenant.

#### DocumentCenter

- **URL:** `https://www.mylakealfred.com/DocumentCenter`
- **Data available:** Hierarchical document archive. Individual documents: `/DocumentCenter/View/{id}/{slug}`. Observed IDs include 1331, 1585, 1600, 1603, 2510 (ULDC PDF).
- **Fields extractable:** Document ID, slug, file type.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** HTML root index.
- **Selectors:** CivicPlus DocumentCenter standard.
- **Why no API:** No JSON index of document metadata.
- **Notes:** The ID space is sparse — sweeping it would exceed the 2000-request cap. Use PDF links from the CivicPlus page graph rather than blind ID sweeps.

#### Archive.aspx (ArchiveCenter)

- **URL:** `https://www.mylakealfred.com/Archive.aspx`
- **Data available:** Historical document archive (`/ArchiveCenter` 302s here).
- **Fields extractable:** Archive items with IDs.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** standard CivicPlus.
- **Selectors:** CivicPlus ArchiveCenter standard.
- **Why no API:** No JSON variant.
- **Notes:** Lighter content than DocumentCenter.

#### Calendar.aspx (HTML calendar)

- **URL:** `https://www.mylakealfred.com/Calendar.aspx`
- **Data available:** Calendar UI for city events.
- **Fields extractable:** Use the iCal feed (`iCalendar.aspx?catID=14&feed=calendar`) for structured data.
- **JavaScript required:** minimal.
- **Anti-bot measures:** none.
- **Pagination:** month navigation.
- **Selectors:** CivicPlus calendar widget.
- **Why no API cataloged here:** The iCal + Calendar RSS feeds (documented in APIs) cover the same events with structured data.
- **Notes:** Listed under Scrape Targets per §4.2 — the HTML surface is a distinct URL from RSSFeed.aspx / iCalendar.aspx.

#### Bids / Jobs / FAQ / Directory / Blog

- **URLs:**
  - `https://www.mylakealfred.com/bids.aspx`
  - `https://www.mylakealfred.com/jobs.aspx`
  - `https://www.mylakealfred.com/FAQ.aspx` (302 → topic redirect)
  - `https://www.mylakealfred.com/directory.aspx`
  - `https://www.mylakealfred.com/blog.aspx`
- **Data available:** Standard CivicPlus modules.
- **Fields extractable:** Standard per CivicPlus.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** varies.
- **Selectors:** CivicPlus module-standard.
- **Why no API cataloged here:** Jobs + Blog + News + Alerts each have RSS feeds (documented). Bids / FAQ / Directory do not.
- **Notes:** Jobs is actively populated (33 KB RSS); Bids present but empty-state at survey.

### aca-prod.accela.com/COLA (HTML surfaces not covered by APIs)

The Accela CapDetail.aspx record-detail page is documented as an API entry above (with the capID parameter contract) because the URL pattern is the structured query surface even though the response is HTML — per §4.2 the structured-param nature wins. The APO lookup is similar. No additional Accela HTML surfaces are cataloged here.

### External platforms (outbound hubs, not mapped in this file)

#### Point & Pay utility payment portal

- **URL:** `https://point-pay.mylakealfred.com:8443/ubs1/index.html`
- **Data available:** Utility billing payment (auth-gated).
- **Fields extractable:** none anonymously.
- **JavaScript required:** yes (JSP servlet).
- **Anti-bot measures:** `unverified` — HEAD returns 404; GET not exercised.
- **Pagination:** n/a.
- **Selectors:** `unverified`.
- **Why no API:** Payment-only outbound. No known public read API.
- **Notes:** Linked as "Pay Utility Bill" from the CivicPlus homepage. Vendor is Point & Pay on a tenant subdomain (port 8443). Out of scope for BI/PT/CR/CD2.

#### GovOutreach support portal

- **URL:** `https://user.govoutreach.com/lakealfredcityfl/support.php?cmd=shell`
- **Data available:** Citizen-support / service-request portal (Granicus "GovOutreach" / "Gov2Go" family).
- **Fields extractable:** `unverified` — not deep-probed.
- **JavaScript required:** partial.
- **Anti-bot measures:** `unverified`.
- **Pagination:** `unverified`.
- **Selectors:** `unverified`.
- **Why no API:** Not probed.
- **Notes:** ⚠️ GAP: if we need 311-style citizen-report data, probe the GovOutreach public API surface on a future pass.

#### Polimorphic chat widget

- **URL:** `https://app.polimorphic.com/react/organizations/lake_alfred_fl/chat`
- **Data available:** AI chat assistant for the city.
- **Fields extractable:** none anonymously (chat state is session-bound).
- **JavaScript required:** yes (React SPA).
- **Anti-bot measures:** `unverified`.
- **Pagination:** n/a.
- **Selectors:** n/a.
- **Why no API:** Not a data-publishing surface — it's an assistant.
- **Notes:** Out of scope.

---

## Coverage Notes

### robots.txt restrictions

- **`www.mylakealfred.com/robots.txt`** disallows `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/support`, `/CurrentEvents*`, `/Search*`, `/Map*`, `/RSS.aspx`. Baiduspider and Yandex are blanket-denied. Siteimprove throttled to 20s. Same template as Haines City / Winter Haven / Lake Hamilton. Treated as operational-risk signal per §3.2; crawl paced at ~1 req/sec.
- **`aca-prod.accela.com/robots.txt`** returned HTTP 404 (no robots file at that path). Confirmed via `evidence/lake-alfred-fl-accela-robots.txt`.

Full text: `evidence/lake-alfred-fl-robots.txt`, `evidence/lake-alfred-fl-accela-robots.txt`.

### Request budget

- **Total requests this run:** ~48 (well under 2000 cap).
- **Rate:** ~1 req/sec target, sustained. Sleeps between each probe in the parallel batches.
- **HTTP errors observed:** only expected ones — `302` on `/ArchiveCenter` (→ `/Archive.aspx`), `302` on `/FAQ.aspx`, `302` on Accela `module=Planning|Licenses|LandDev` (not anon-exposed), `404` on `aca-prod.accela.com/robots.txt` (no robots), `404` on `aca-prod.accela.com/v4/agency/COLA` (expected per `accela-rest-probe-findings.md`), `404` on `point-pay.mylakealfred.com:8443/ubs1/index.jsp` HEAD (use `/index.html`).
- **No 429s. No captcha challenges.**

Full request log: `evidence/_lake-alfred-request-log.txt`.

### Seed-script bug (documented per mapping-pass discovery)

`seed_pt_jurisdiction_config.py` currently declares Lake Alfred's permit platform as **iWorQ**. This is incorrect — a copy-paste bug likely inherited from Haines City's adjacent entry. Ground truth per this survey and per the production adapter:

- **Adapter file:** `modules/permits/scrapers/adapters/lake_alfred.py` extends `AccelaCitizenAccessAdapter` with `agency_code="COLA"`, `module_name="Building"`, `target_record_type="Building/Residential/New/NA"`.
- **Live verification:** `/166/Building-Permits` on the CivicPlus CMS links outbound to `https://aca-prod.accela.com/COLA/Default.aspx`. `aca-prod.accela.com/COLA` returns 200 with a populated Angular tenant (269 KB Default.aspx, 477 KB Building CapHome, 473 KB Enforcement CapHome).
- **No iWorQ tenant exists** for Lake Alfred — `mylakealfred.portal.iworq.net` and similar variants are not referenced anywhere on the CMS. The production permits pipeline would have failed silently if it ever hit the seed script's iWorQ entry.
- **Remediation:** A separate task is already spawned to correct `seed_pt_jurisdiction_config.py`. This map reflects the live Accela reality.

### Drift from archived references

Compared against `docs/api-maps/_archived/polk-county-iworq.md` and `docs/api-maps/accela-rest-probe-findings.md`:

- **Accela v4 REST anon-blocked** (`/v4/agency/COLA` → 404) is consistent with the archived finding across all FL tenants probed.
- **Module availability per tenant varies** — COLA exposes `Building + Enforcement` anonymously; POLKCO exposes `Building`; COWH exposes `Building` (with anon-search TBD per ACCELA-16). Lake Alfred's Enforcement exposure is a **net-positive drift** relative to the typical FL-city Accela tenant, and a candidate future data surface for code-enforcement work.
- **No Tyler eSuite / ProjectDox** on Lake Alfred, unlike Winter Haven — consistent with smaller-city footprint (Lake Alfred population ~5,000 vs Winter Haven ~56,000).
- **City-owned ArcGIS Online org** (`VaAx8WnigGGWjIPd`) distinct from Polk County's enterprise GIS — a new hostname for the registry, but the platform (ArcGIS REST) is already cataloged.

### Open gaps (⚠️ GAP markers summarized)

- **`/RSSFeed.aspx?ModID=58` (Calendar):** `calendarEvent:*` namespace sub-elements not enumerated.
- **`/RSSFeed.aspx?ModID=65` (Agenda Creator):** CID numeric ID → body-name mapping incomplete (CC and School-Zone Magistrate slugs missing numeric suffix in observed URLs).
- **`/AgendaCenter/Search/`:** CR adapter YAML uses `category_id=2`, but observed search CIDs are `15` and `16`. Confirm adapter's `category_id` taxonomy vs search URL CID taxonomy on next pass.
- **Accela COLA:** anon record search on Building + Enforcement modules; CapDetail.aspx real-record capture; APO lookup postback response — all need browser.
- **Accela module coverage:** Planning / Licenses / LandDev all 302 — confirm on next pass whether these are module-disabled or just auth-gated.
- **ArcGIS planning service canonicalization:** 8 services enumerated; only `City_of_Lake_ALfred_Planning_WFL1` deep-probed. Diff against `_12_2025` / `_2025_WFL1` and pick canonical current layer.
- **ULDC code ingestion:** no Municode / amlegal library — ULDC is a flat PDF at `/DocumentCenter/View/2510`. CD2 ingestion needs a PDF-parse path.
- **Point & Pay / GovOutreach / Polimorphic / DocAccess:** deep-probe deferred (out of scope for BI/PT/CR/CD2).
- **`/ImageRepository/Document`:** ID space not swept.
- **Polk County GIS cross-reference:** out of this file's scope; mapped under `polk-county-fl.md`.

### `_platforms.md` deltas

No net-new data-surface platforms from this run — CivicPlus + Accela + ArcGIS are all already in the registry. Candidate additions to the registry (deferred to a housekeeping pass):

- **Point & Pay** — tenant-subdomain utility-payment portal (hostname pattern `<tenant>.point-pay.<something>` or `point-pay.<customer-domain>:8443/ubs1/`).
- **GovOutreach / Gov2Go** — `user.govoutreach.com/<tenant>/support.php` citizen-support portal (Granicus family).
- **Polimorphic (AI chat)** — `app.polimorphic.com/react/organizations/<tenant>/chat` React-SPA chat widget.
- **DocAccess** — `docaccess.com/docbox.js` accessibility JS shim (not a data surface; documented only for fingerprint-recognition).

Not adding in this pass — this map's job is to document the Lake Alfred footprint, not maintain the registry.
