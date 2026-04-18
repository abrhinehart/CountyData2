# Bartow, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://www.cityofbartow.net/` (city of Bartow, FL — county seat of Polk County). One-file scope: city of Bartow only — Polk County is mapped separately in `polk-county-fl.md`.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.cityofbartow.net/` is server-rendered ASP.NET (CivicPlus CivicEngage); no SPA hydration globals (`__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__`) in the shell. Only JS XHR is the standard CivicPlus `/antiforgery` bootstrap. The one SPA surface touched — Municode Library — is already characterized in `_platforms.md` and cross-referenced, not deep-probed.
>
> UA: `Mozilla/5.0 (compatible; CountyDataMapper/1.0)`. Pacing ~1 req/sec. 46 unique HTTPS requests this run (well under the 2000 cap); 0 × 429, 0 × captcha, 0 × WAF block on cityofbartow.net.

## Summary

- **Jurisdiction:** City of Bartow, Polk County, FL (county seat). Population ≈20k.
- **City CMS platform:** **CivicPlus CivicEngage** on `www.cityofbartow.net` (CNAME to tenant canonical `fl-bartow.civicplus.com`). Classic numeric-ID URL pattern (`/{id}/{slug}`, e.g. `/303/City-Commission`, `/159/Building-Department`, `/443/Permit-Application`). CivicPlus footer (`&reg;`), `/antiforgery` bootstrap, `/rss.aspx` feed index enumerates **27 feed URLs across 7 ModIDs** (1 News Flash, 51 Blog, 53 Banner, 58 Calendar, 63 Alert Center, **65 Agenda Creator**, 76 Pages). CivicPlus GA4 tag `G-PBJTJHBC66`; AppInsights instrumentation key `1cde048e-3185-4906-aa46-c92a7312b60f` (shared CivicPlus-tenant telemetry).
- **Commission surface:** **CivicPlus AgendaCenter at `https://www.cityofbartow.net/AgendaCenter`** — this is authoritative for both CR YAMLs in the repo (`modules/commission/config/jurisdictions/FL/bartow-cc.yaml` with `category_id: 5` → City Commission; `bartow-pz.yaml` with `category_id: 2` → Planning-Zoning Commission). Agenda PDFs served as `AgendaCenter/ViewFile/Agenda/_<MMDDYYYY>-<id>`; history via `AgendaCenter/PreviousVersions/{id}`. AgendaCenter/Search accepts GET with `CIDs` param (confirmed live). ⚠️ The Agenda Creator RSS (`ModID=65`) is **empty on this tenant** for every category — provisioned but no agenda publications fire to the RSS feed, unlike Lake Wales. Agenda discovery must use the AgendaCenter HTML landing or AgendaCenter/Search endpoint (both verified live this run).
- **Video / live streaming:** **BoxCast** on `boxcast.tv` with public JSON API at `api.boxcast.com`. Account `kpcnkyfgetmxappqpclx` ("City of Bartow - Bartow, FL"); channel `v97dttfeoqpr2vkmzmfo` ("City Commission Meetings") confirmed populated with 10+ recorded broadcasts (named "City Commission Meeting - M/D/YYYY"). BoxCast has a scrapable metadata surface — added to `_platforms.md` this run.
- **Permit portal posture:** **NO ONLINE PERMIT SYSTEM.** Building Department pages (`/159`, `/162`, `/443`, `/483`, `/161`) route all permit workflow through **paper/email submission** of PDFs. `/443/Permit-Application` embeds a **CivicPlus FormCenter widget** (`formID=72`) — an inbound contact/request form, not a permit-search/portal. No GovBuilt / SmartGov / Tyler EnerGov / Accela / iWorQ / Cloudpermit / CityView / PermitTrax tenant for Bartow. ⚠️ GAP: Bartow has no PT-relevant public data surface; permit inventory reconstruction would require either public-records requests or scraping the BoxCast recorded meeting videos for permit-granting votes referenced on agendas.
- **Employment:** **NEOGOV GovernmentJobs** at `governmentjobs.com/careers/bartow` — external, linked from every CMS page footer; not deep-mapped this pass.
- **Code of ordinances:** **Municode Library** (Angular SPA) at `library.municode.com/fl/bartow` — external, already characterized in `_platforms.md`; not deep-probed.
- **Meeting-vendor graveyard (per Lake Wales pattern):**
  - `bartow.legistar.com` + `bartowfl.legistar.com` — **dead Legistar tenant shells.** Both resolve 200 but every page returns the 19-byte body `Invalid parameters!`. OData `webapi.legistar.com/v1/bartow/Bodies` returns HTTP 500 with `"LegistarConnectionString setting is not set up in InSite for client: bartow"` — same provisioned-but-unconfigured pattern seen on Lake Wales. Migration residue or trial tenant.
  - `bartowfl.novusagenda.com` — **dead NovusAgenda tenant shell.** `/` 302→`/AgendaWeb` 302→`/agendaweb/Error.html?aspxerrorpath=/AgendaWeb` — ASP.NET runtime error on the application root, same pattern as Lake Wales.
  - `bartow.granicus.com` — **no Granicus tenant.** `/ViewPublisher.php?view_id=1` 302-redirects to `/core/error/NotFound.aspx`. Legistar-web-api behavior is tenanted but ViewPublisher is not provisioned.
  - `bartowfl.govbuilt.com` + `cityofbartow.govbuilt.com` — **GovBuilt wildcard-DNS placeholders** (31,611 / 31,619 bytes, generic `<title>GOVBUILT PLATFORM - Tomorrow's Government Built Today</title>` per `_platforms.md` detection discipline).
  - `bartow.portal.iworq.net` + `cityofbartow.portal.iworq.net` — **iWorQ empty tenant shells** (3,207 / 3,213 bytes, Laravel "Page Can Not Be Found"). No real tenant.
  - `ci-bartow-fl.smartgovcommunity.com` — **no SmartGov tenant** (`/Public/Home` 404). Not provisioned on either standard or `.validation.` subdomain.
- **Accela ruled out by Planner** (404 on BARTOW/COBA/CITYBARTOW/BARTOWFL agency slugs) — not re-probed this run.
- **`bartowfl.gov` DNS status:** still fails resolution this run (retry on all four subdomains `bartowfl.gov`, `secure.bartowfl.gov`, `utility.bartowfl.gov`, `permits.bartowfl.gov` — every one returned `code=000, remote_ip=empty` from curl; nslookup echoes the name without an IP). ⚠️ GAP: if the domain ever resolves, there may be an ADG utility / ADG permits portal pattern (mirroring Lake Wales's `secure.lakewalesfl.gov/ubs1` + `/permits` layout) and we should re-probe. For now, no evidence such a portal exists — the CMS links all point to CivicPlus-internal paths for utilities/permit info.
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts (NewVision BrowserView, Tyler Odyssey PRO), Polk County Legistar — all documented in `polk-county-fl.md`; parcel/court data for Bartow properties rides Polk's services.

**Totals:** ~46 HTTPS requests, 0 × 429, 0 × captcha, 0 × WAF block; 24 APIs documented; 15 scrape targets; 3 external platforms cross-referenced; 6 dead/placeholder tenants documented for negative evidence.

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.cityofbartow.net` / `fl-bartow.civicplus.com` | **CivicPlus CivicEngage** | LIVE | `/{numeric-id}/{slug}` URL pattern; `ASP.NET_SessionId` + `CP_IsMobile` cookies; `/antiforgery` bootstrap JSON endpoint; `/rss.aspx` index enumerates 27 RSS URLs across 7 ModIDs (1, 51, 53, 58, 63, 65, 76); AgendaCenter live + populated (categories `5` City Commission, `2` Planning-Zoning, `10` Beautification, `6` Canvassing, `11` CAC, `9` Code Enforcement, `12` CRA, `15` DRC, `7` GEPB, `8` MAC, `17` Public Meetings, `4` REC, `16` RedLight Camera, `3` ZBA); CivicPlus GA4 tag `G-PBJTJHBC66`; AppInsights instrumentation key `1cde048e-3185-4906-aa46-c92a7312b60f`. `fl-bartow.civicplus.com` hosts identical content (CivicPlus tenant-canonical) but its `/robots.txt` is `Disallow: /` for `*` (only Screaming Frog seeded with a UUID is Allow:/). |
| `api.boxcast.com` + `boxcast.tv` | **BoxCast** | LIVE (public JSON API) | Version `9.8.0` at `api.boxcast.com/`; account `kpcnkyfgetmxappqpclx` ("City of Bartow - Bartow, FL"); channel `v97dttfeoqpr2vkmzmfo` ("City Commission Meetings") populated; CloudFront-signed HLS at `play.boxcast.com/p/{channel_id}/v/all-ext.m3u8` + `play.boxcast.com/p/{broadcast_id}/v/all-byteranges.m3u8`; uploads/posters/thumbs under `recordings.boxcast.com/YYYY/MM/DD/HHMMSS-{broadcast_id}/`; attachments under `uploads.boxcast.com/{account_id}/YYYY-MM/{path}/`. `robots.txt` is `User-agent: * \n Disallow:` (permissive). **New platform added to `_platforms.md` this run.** |
| `www.governmentjobs.com/careers/bartow` | **NEOGOV GovernmentJobs** | LIVE (external) | `<title>Current Openings \| ...</title>`; 192 KB landing page; classic NEOGOV careers portal. External; not deep-mapped this pass. |
| `library.municode.com/fl/bartow` | **Municode Library** | LIVE (external) | Angular SPA (`ng-app="mcc.library_desktop"`); `base href="https://library.municode.com/"`; covered by existing `_platforms.md` row. Not deep-mapped here. |
| `bartow.legistar.com` + `bartowfl.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | Both tenants resolve 200 but body is 19-byte `Invalid parameters!`. OData `webapi.legistar.com/v1/bartow/Bodies` returns HTTP 500 `"LegistarConnectionString setting is not set up in InSite for client: bartow"` — identical pattern to Lake Wales dead shell. Drift sentinel only. |
| `bartowfl.novusagenda.com` | **NovusAgenda (dead shell)** | BROKEN | `/` → `/AgendaWeb` → `/agendaweb/Error.html?aspxerrorpath=/AgendaWeb` — ASP.NET runtime error on the application root; dead tenant. Drift sentinel only. |
| `bartow.granicus.com` | — | NO TENANT | `/ViewPublisher.php?view_id=1` 302 → `/core/error/NotFound.aspx`. Granicus domain resolves but no tenant on this host. |
| `bartowfl.govbuilt.com` + `cityofbartow.govbuilt.com` | — | PLACEHOLDER (wildcard DNS) | 31,611 / 31,619 byte generic placeholder; `<title>GOVBUILT PLATFORM - Tomorrow's Government Built Today</title>`. Matches placeholder signatures per `_platforms.md`. |
| `bartow.portal.iworq.net` + `cityofbartow.portal.iworq.net` | — | EMPTY TENANT SHELLS | 3,207 / 3,213 byte Laravel "Page Can Not Be Found". No real iWorQ tenant. |
| `ci-bartow-fl.smartgovcommunity.com` | — | NO TENANT | `/Public/Home` returns 404 "The resource you are looking for has been removed". |
| `bartowfl.gov` + `secure.bartowfl.gov` + `utility.bartowfl.gov` + `permits.bartowfl.gov` | — | DNS FAILS | Probed this run; all four still return `code=000` + empty `remote_ip`. Planner-flagged coverage gap; if resolution comes back, re-probe for ADG utility/permit patterns. |
| `public.coderedweb.com` | **Crisis24 CodeRed** | LINKED (external) | Referenced from `/159/Building-Department`; probe TIMED OUT from this network (15s). Outbound emergency-alert signup; no read API. |
| `connect.civicplus.com` / `cp-civicplusuniversity2.civicplus.com` / `wsmcdn.audioeye.com` / `docaccess.com/docbox.js` / `js.monitor.azure.com` | CivicPlus control-plane + 3rd-party accessibility / telemetry scripts | LIVE (outbound) | Not Bartow-specific data surfaces — CivicPlus referral + university + AudioEye + DocAccess + Azure Monitor AppInsights. Documented for completeness of 3rd-party inventory. |

New platforms added to `docs/api-maps/_platforms.md` this run: **BoxCast** (real scrapable JSON API).

---

## APIs

### /antiforgery

#### Antiforgery token

- **URL:** `https://www.cityofbartow.net/antiforgery`
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
- **Discovered via:** Inline `getAntiForgeryToken` script in every CivicPlus page.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/antiforgery'
  ```
- **Evidence file:** `evidence/bartow-fl-antiforgery.json`
- **Notes:** Token submitted as `__RequestVerificationToken` on same-origin form POSTs. Gate for any POST-driven form on the CMS.

### /robots.txt

#### Robots directives (main site)

- **URL:** `https://www.cityofbartow.net/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard CivicPlus robots directives — disallows admin, search, map, currentevents, `/RSS.aspx` (singular capital); allows everything else; Siteimprove crawl-delay 20; Baidu + Yandex fully disallowed. References `Sitemap: /sitemap.xml`.
- **Response schema:** `text/plain` robots.txt
- **Observed parameters:** none
- **Probed parameters:** none — static file
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static (CMS-managed)
- **Discovered via:** Recon step 1.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/robots.txt'
  ```
- **Evidence file:** `evidence/bartow-fl-robots.txt` (headers: `evidence/bartow-fl-robots.txt.headers.txt`)
- **Notes:** Mapping pass compliant — no disallowed path requested. `/RSSFeed.aspx` is not disallowed; `/RSS.aspx` is.

#### Robots directives (CivicPlus tenant-canonical mirror)

- **URL:** `https://fl-bartow.civicplus.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** `User-agent: * \n Disallow: /` — all anonymous crawlers blocked (operational-risk signal). A single hard-coded Screaming Frog UUID (`bde2423e-3cc7-42a6-96a8-d2d5bc7d2a2a`) is `Allow:/` — likely CivicPlus's internal SEO crawler.
- **Response schema:** `text/plain`
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none observed at 1 req/sec
- **Data freshness:** static
- **Discovered via:** Outbound link in `/238/Unified-Land-Development-Code` (`https://fl-bartow.civicplus.com/Directory.aspx`).
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://fl-bartow.civicplus.com/robots.txt'
  ```
- **Evidence file:** `evidence/bartow-fl-cp-staff-robots.txt`
- **Notes:** Mapping pass minimized its fl-bartow.civicplus.com hits to two (`/` + `/Directory.aspx` + `/robots.txt`). `fl-bartow.civicplus.com` is the CivicPlus-tenant canonical host; `www.cityofbartow.net` is a CNAME fronting the same content. Treat as a mirror — prefer `www.cityofbartow.net` for all data access.

### /sitemap.xml

#### Sitemap (main site)

- **URL:** `https://www.cityofbartow.net/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Single `urlset` enumerating **231 numeric-ID CMS pages** (e.g. `/1/Home`, `/303/City-Commission`, `/159/Building-Department`, `/129/Agendas-Minutes`, etc.) plus 62 supplementary CMS shells. Total 293 `<url>` entries; 45 KB.
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
- **Pagination:** `none` — all 293 entries inline.
- **Rate limits observed:** none
- **Data freshness:** updated on CMS publish.
- **Discovered via:** `/robots.txt`.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/sitemap.xml'
  ```
- **Evidence file:** `evidence/bartow-fl-sitemap.xml`
- **Notes:** Canonical diff target for drift detection on CMS structure.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed on this tenant (from the `/rss.aspx` HTML index): `1` (News Flash), `51` (Blog), `53` (Banner/Photo), `58` (Calendar), `63` (Alert Center), `65` (Agenda Creator — **provisioned but EMPTY on this tenant**), `76` (Pages). 27 categorized URLs across 7 ModIDs; full feed list in `evidence/bartow-fl-rss-aspx.html`.

Note: `/RSS.aspx` (singular capital) is **disallowed by robots.txt**. `/RSSFeed.aspx` is the correct endpoint.

#### News Flash RSS (ModID 1)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Latest CivicAlerts / News Flash items, optionally category-filtered.
- **Response schema:**
  ```
  <rss version="2.0">
    <channel>
      <title>string</title>
      <link>url</link>
      <lastBuildDate>rfc822</lastBuildDate>
      <item>
        <title>string</title>
        <link>url</link>
        <pubDate>rfc822</pubDate>
        <description>html</description>
        <guid isPermaLink="bool">string</guid>
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:**
  - `ModID` (int, required) — `1` for News Flash
  - `CID` (string, optional) — `All-newsflash`, `Home-1`
- **Probed parameters:** `unverified`
- **Pagination:** `none` — trailing window
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** `/rss.aspx` HTML index
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=1&CID=All-newsflash'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod1.xml`
- **Notes:** 325-byte response — **empty channel** this run (no current news flash items).

#### Blog RSS (ModID 51)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog posts feed.
- **Response schema:** RSS 2.0 (same shape as News Flash).
- **Observed parameters:** `ModID=51`, `CID=All-blog`
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/rss.aspx`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=51&CID=All-blog'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod51.xml`
- **Notes:** 317-byte skeleton — empty this run. Drift sentinel.

#### Banner / Photo RSS (ModID 53)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Banner/photo items keyed to venue or department.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=53`, `CID=All-0`
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** irregular
- **Discovered via:** `/rss.aspx`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod53.xml`
- **Notes:** 352-byte skeleton — empty this run.

#### Calendar RSS (ModID 58)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming city calendar events (distinct from AgendaCenter meetings).
- **Response schema:** RSS 2.0 with `calendarEvent:*` extension namespace.
- **Observed parameters:**
  - `ModID=58`
  - `CID` — `All-calendar`, `Events-14`, `Library-24`, `Meetings-23`, `Parks-Recreation-26`
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/rss.aspx`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=58&CID=All-calendar'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod58.xml` (22,712 bytes — **populated**), `evidence/bartow-fl-rssfeed-mod58-meetings.xml`
- **Notes:** **LIVE content.** `Meetings-23` category filter is the CR-relevant subfeed for commission/board meeting calendar entries (not agenda documents — those are in `/AgendaCenter`). The iCal export at `/common/modules/iCalendar/iCalendar.aspx?catID=23` serves the same data.

#### Alert Center RSS (ModID 63)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Emergency / alert notifications.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=63`, `CID` — `All-0`, `Hurricane-Milton-5`
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** event-driven (currently empty — 329-byte skeleton)
- **Discovered via:** `/rss.aspx`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=63&CID=All-0'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod63.xml`
- **Notes:** `Hurricane-Milton-5` category enumerated but not probed (empty overall feed). Drift sentinel.

#### Agenda Creator RSS (ModID 65) — provisioned but EMPTY

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Should return every CivicPlus AgendaCenter agenda publication with deep links to `/AgendaCenter/PreviousVersions/{id}`. **Empty on this tenant** — 328-byte RSS skeleton with no `<item>` entries for `CID=All-0` and for every category-specific CID.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=65`
  - `CID` — `All-0`, `Beautification-Advisory-Board-10`, `Canvassing-Board-6`, `Citizens-Advisory-Committee-11`, `City-Commission-5`, `Code-Enforcement-Special-Magistrate-9`, `Community-Redevelopment-Agency-12`, `Development-Review-Committee-15`, `General-Employees-Pension-Board-7`, `Mayors-Art-Club-8`, `Planning-Zoning-Commission-2`, `Public-Meetings-17`, `Recreation-Advisory-Board-4`, `RedLight-Camera-16`, `Zoning-Board-of-Adjustment-3`
- **Probed parameters:** Tested `CID=All-0`, `CID=City-Commission-5`, `CID=Planning-Zoning-Commission-2`, `CID=Community-Redevelopment-Agency-12` — all return 328–363 byte empty-channel skeletons even though `/AgendaCenter` HTML is densely populated.
- **Pagination:** `none` (empty)
- **Rate limits observed:** none
- **Data freshness:** ⚠️ GAP: the Agenda Creator RSS module is provisioned but not wired to publish on agenda save — unlike Lake Wales where this feed is live. Agenda discovery for Bartow must fall back to the AgendaCenter HTML landing or AgendaCenter/Search endpoint.
- **Discovered via:** `/rss.aspx` HTML index
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=65&CID=City-Commission-5'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod65.xml`, `evidence/bartow-fl-rssfeed-mod65-cc5.xml`, `evidence/bartow-fl-rssfeed-mod65-pz2.xml`, `evidence/bartow-fl-rssfeed-mod65-cra12.xml`
- **Notes:** Category IDs here match `modules/commission/config/jurisdictions/FL/bartow-cc.yaml` (`category_id: 5`) and `bartow-pz.yaml` (`category_id: 2`) exactly — the CR YAMLs use the AgendaCenter HTML pagination (category CIDs), not this RSS feed. Drift sentinel: if this feed ever becomes populated, it becomes an alternate CR discovery path.

#### Pages RSS (ModID 76)

- **URL:** `https://www.cityofbartow.net/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** CMS page-update feed — most recent published CMS pages with numeric IDs.
- **Response schema:** RSS 2.0.
- **Observed parameters:** `ModID=76`, `CID=All-0`
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/rss.aspx`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/RSSFeed.aspx?ModID=76&CID=All-0'
  ```
- **Evidence file:** `evidence/bartow-fl-rssfeed-mod76.xml`
- **Notes:** 16,019-byte sample — **LIVE** CMS page-change feed. Useful page-change sentinel.

### /common/modules/iCalendar/iCalendar.aspx

#### Calendar iCal export

- **URL:** `https://www.cityofbartow.net/common/modules/iCalendar/iCalendar.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** iCal (`.ics`) export of the CivicPlus calendar module, optionally filtered by category. `PRODID:iCalendar-Ruby`, `VERSION:2.0`, `X-WR-TIMEZONE:America/New_York`, full `VTIMEZONE` + `VEVENT` entries with `DTSTART`/`DTEND`/`LOCATION`/`DESCRIPTION`/`SEQUENCE`.
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
  - `catID` (int, optional) — calendar category ID matching the Calendar-RSS `CID` numeric suffixes. Observed: `14` (Events), `23` (Meetings), `24` (Library), `26` (Parks & Rec)
  - `feed` (string, optional) — `calendar` observed
- **Probed parameters:**
  - `catID=14&feed=calendar` — 5,636-byte ICS (Events calendar — sparse)
  - `catID=23&feed=calendar` — **41,221-byte ICS with many VEVENTs spanning through 2027** (Meetings calendar — the CR-relevant feed)
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Pattern-match to CivicPlus standard iCal endpoint.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/common/modules/iCalendar/iCalendar.aspx?catID=23&feed=calendar'
  ```
- **Evidence file:** `evidence/bartow-fl-calendar-ics-14.ics`, `evidence/bartow-fl-calendar-ics-23.ics`
- **Notes:** `catID=23` (Meetings) is the **primary CR-scheduling data surface** — VEVENT items include the `cityofbartow.net/calendar.aspx?EID=<n>` deep link and `LOCATION` (usually "City Hall Commission Chambers 450 N. Wilson Ave Bartow FL 33830"). Serves the same events as Calendar RSS `ModID=58&CID=Meetings-23` but in iCal format — prefer this for drift detection and subscription.

### /AgendaCenter (data-surface entry points)

CivicPlus AgendaCenter — **the authoritative CR data surface for Bartow.** Matches both `bartow-cc.yaml` (`category_id: 5` — City Commission) and `bartow-pz.yaml` (`category_id: 2` — Planning-Zoning Commission). The `/AgendaCenter` landing page is documented under Scrape Targets (returns HTML); the three endpoints below return structured / binary data keyed by agenda or meeting IDs.

#### AgendaCenter agenda file download

- **URL:** `https://www.cityofbartow.net/AgendaCenter/ViewFile/Agenda/{slug}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Agenda document (PDF) for a specific meeting. `Content-Type: application/pdf`; `Content-Disposition: inline; filename=<meeting-date><board>.pdf`. Agenda byte-size on sample: 139 KB.
- **Response schema:** binary PDF (or HTML-rendered agenda when `?html=true` is appended — CivicPlus convention).
- **Observed parameters:**
  - `{slug}` (path segment, required) — underscore-prefixed date+id pattern `_MMDDYYYY-<id>`. Observed range on this tenant: `_01062025-302` (Jan 6 2025, seq 302) through `_04072026-421` (Apr 7 2026, seq 421) — ~120 agendas across 14 boards/committees.
  - `html` (bool, optional) — `true` returns HTML render instead of PDF (`unverified` this run; per CivicPlus convention).
- **Probed parameters:**
  - `_04022026-417` — returned 139,393-byte PDF `2026-04-02 agenda Canvassing Board...pdf` (confirmed live binary delivery).
- **Pagination:** `none` (single-document fetcher)
- **Rate limits observed:** none
- **Data freshness:** real-time (per agenda publish)
- **Discovered via:** AgendaCenter landing-page cards
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' -o agenda.pdf 'https://www.cityofbartow.net/AgendaCenter/ViewFile/Agenda/_04022026-417'
  ```
- **Evidence file:** `evidence/bartow-fl-agenda-viewfile-417.bin` (139 KB PDF) + `.headers.txt`
- **Notes:** Sibling endpoints `ViewFile/Minutes/{slug}` and `ViewFile/Packet/{slug}` exist per CivicPlus convention (not individually probed this pass). Already consumed by the existing `cr/adapters/civicplus.py` adapter via the two `bartow-*.yaml` configs.

#### AgendaCenter PreviousVersions browse

- **URL:** `https://www.cityofbartow.net/AgendaCenter/PreviousVersions/{id}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML page listing all historical versions (agenda + minutes + packets) for a given meeting-history root ID.
- **Response schema:** HTML page (categorized under Scrape Targets — no structured JSON equivalent observed).
- **Observed parameters:**
  - `{id}` (path, required) — integer. Observed range: `300` (2025) through `421` (Apr 2026).
- **Probed parameters:** `unverified`
- **Pagination:** `none` per ID
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** AgendaCenter landing-page links
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/AgendaCenter/PreviousVersions/417'
  ```
- **Evidence file:** `evidence/bartow-fl-agenda-previous-417.html` (99,221 bytes)
- **Notes:** Documented here as an API entry because every response embeds structured ID-keyed document links (`ViewFile/Agenda/_<slug>`, `ViewFile/Minutes/_<slug>`) — no JSON equivalent observed. ⚠️ GAP: no JSON version-history endpoint.

#### AgendaCenter Search (HTML-returning GET)

- **URL:** `https://www.cityofbartow.net/AgendaCenter/Search/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Filtered AgendaCenter landing with agenda cards matching the supplied term / categories / date range. Returns **HTML** (160,392 bytes on probe) — documented as API per §4.2's "structured content by key" interpretation: the URL itself is a structured query surface, but the response payload is HTML to be parsed. No JSON equivalent.
- **Response schema:** HTML page with `.catAgendaRow` cards (same shape as the AgendaCenter landing).
- **Observed parameters:**
  - `term` (string, optional) — free-text search
  - `CIDs` (comma-separated ints, optional) — category filter; `5` = City Commission, `2` = Planning-Zoning Commission. Multi-value supported.
  - `startDate` (date, optional) — `MM/DD/YYYY`
  - `endDate` (date, optional) — `MM/DD/YYYY`
  - `dateRange` (string, optional) — calendar-month filter shortcut
  - `dateSelector` (string, optional) — pre-canned range label
- **Probed parameters:**
  - `CIDs=5&term=&startDate=&endDate=&dateRange=&dateSelector=` → 160,392-byte HTML (City Commission only) — confirmed live
- **Pagination:** `unverified` — search response returned all results inline; true pagination behavior on larger result sets not exercised this pass.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Inline JS on `/AgendaCenter`: `/AgendaCenter/Search/?term=…&CIDs=…&startDate=…`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://www.cityofbartow.net/AgendaCenter/Search/?term=&CIDs=5&startDate=&endDate=&dateRange=&dateSelector='
  ```
- **Evidence file:** `evidence/bartow-fl-agendacenter-search.html`
- **Notes:** ⚠️ The sibling endpoint `/AgendaCenter/UpdateCategoryList` (POST from inline JS) returns 404 on a bare GET — POST-only, requires `__RequestVerificationToken`. Not exercised this pass.

### /ImageRepository/Document

#### Image / document repository

- **URL:** `https://www.cityofbartow.net/ImageRepository/Document`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Raw binary media file (image, PDF) from the CivicPlus image repository, keyed by numeric document ID.
- **Response schema:** binary (`Content-Type: image/png | image/jpeg | application/pdf | ...`).
- **Observed parameters:**
  - `documentID` (int, required) — repository document ID. Observed inline in home-page HTML for header logo + social icons + banner images.
- **Probed parameters:**
  - `documentID=1` — **returns 200 with 0-byte body** (ID 1 exists but is empty, likely a reserved slot). Higher IDs referenced in the home-page HTML were not individually tested.
- **Pagination:** `none` (single-asset fetcher)
- **Rate limits observed:** none
- **Data freshness:** static per documentID
- **Discovered via:** Inline `<img src="/ImageRepository/Document?documentID=…">` in home-page HTML.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' -o asset.bin 'https://www.cityofbartow.net/ImageRepository/Document?documentID=6119'
  ```
- **Evidence file:** `evidence/bartow-fl-imgrepo-probe.bin` (0-byte sample from ID=1)
- **Notes:** Not a data API in the semantic sense but does serve structured binary content by numeric ID. ⚠️ GAP: no way to enumerate valid documentIDs without parsing referring HTML.

### api.boxcast.com

BoxCast's public JSON API — unauthenticated read for account, channel, and broadcast metadata. Streaming video + posters + uploads are served via CloudFront-signed URLs embedded in these JSON responses. Bartow account ID: `kpcnkyfgetmxappqpclx`.

#### BoxCast API root / version

- **URL:** `https://api.boxcast.com/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** `{"version": "9.8.0"}` — API version descriptor.
- **Response schema:**
  ```
  {
    "version": "string"
  }
  ```
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none observed at 1 req/sec
- **Data freshness:** static per deploy
- **Discovered via:** BoxCast embedded player JS references to `api.boxcast.com`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-api-root.json`
- **Notes:** Same 19-byte `{"version":"9.8.0"}` response at `rest.boxcast.com/` — alias. `robots.txt` at `boxcast.tv` is fully permissive.

#### BoxCast account descriptor

- **URL:** `https://api.boxcast.com/accounts/{account_id}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Account metadata — id, name, captioning preference, linkback display flag, and CloudFront-signed HLS playlists for the default channel (both video + audio-only variants).
- **Response schema:**
  ```
  {
    "id": "string",
    "name": "string",
    "channel_id": "string",
    "content_settings": {
      "requestsCaptioning": "bool",
      "hide_linkback": "bool"
    },
    "static_playlist_url": "https://play.boxcast.com/p/<channel_id>/v/all-ext.m3u8?Expires=...&Signature=...&Key-Pair-Id=...",
    "static_audio_playlist_url": "https://play.boxcast.com/p/<channel_id>/v/audio-ext.m3u8?Expires=...&Signature=...&Key-Pair-Id=..."
  }
  ```
- **Observed parameters:**
  - `{account_id}` (path, required) — `kpcnkyfgetmxappqpclx` for Bartow
- **Probed parameters:**
  - Singular `/account/{id}` → 404 (path is **plural** `/accounts/{id}`)
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time per API call (signed URLs have `Expires=2147483647` — effectively unbounded)
- **Discovered via:** BoxCast player JSON + trial of standard BoxCast API shape.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/accounts/kpcnkyfgetmxappqpclx'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-acct.json`
- **Notes:** Default channel is `pzo8uo3hgxrf0pmwalhj` — unlabeled "All Broadcasts" style channel. The labeled "City Commission Meetings" channel (`v97dttfeoqpr2vkmzmfo`) is exposed separately via `/accounts/{id}/channels`.

#### BoxCast account channels list

- **URL:** `https://api.boxcast.com/accounts/{account_id}/channels`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of channel descriptors for the account.
- **Response schema:**
  ```
  [
    {
      "id": "string",
      "name": "string",
      "is_ticketed": "bool",
      "ticket_price": "number",
      "free_variant": "string",
      "content_settings": {}
    }
  ]
  ```
- **Observed parameters:**
  - `{account_id}` (path, required) — `kpcnkyfgetmxappqpclx`
- **Probed parameters:** none
- **Pagination:** `unverified` — response returned all 1 channel inline
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** BoxCast API shape convention
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/accounts/kpcnkyfgetmxappqpclx/channels'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-acct-channels.json`
- **Notes:** Single channel returned: `{"id":"v97dttfeoqpr2vkmzmfo","name":"City Commission Meetings","is_ticketed":false,"ticket_price":0,"free_variant":"best","content_settings":{}}`. This is the CR-relevant channel.

#### BoxCast channel descriptor

- **URL:** `https://api.boxcast.com/channels/{channel_id}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Channel metadata — id, name, description, ticketing flags.
- **Response schema:**
  ```
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "is_ticketed": "bool",
    "ticket_price": "number",
    "free_variant": "string",
    "content_settings": {}
  }
  ```
- **Observed parameters:**
  - `{channel_id}` (path, required) — `v97dttfeoqpr2vkmzmfo` for "City Commission Meetings"
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** BoxCast API shape convention
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/channels/v97dttfeoqpr2vkmzmfo'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-channel-cc.json`
- **Notes:** The individual-broadcast ID (e.g. `kwmmo9svs8cd7ia5tl4d`) is **also** accepted at this path and returns a broadcast-style descriptor — BoxCast overloads `/channels/{id}` with channel-slug / broadcast-id dispatch.

#### BoxCast channel broadcasts list

- **URL:** `https://api.boxcast.com/channels/{channel_id}/broadcasts`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of broadcast descriptors within a channel. Each entry: id, name (e.g. "City Commission Meeting - M/D/YYYY"), description, starts_at/stops_at (ISO-8601 UTC), timeframe (current/future/past), tags, transcoder_profile, poster/preview URL templates, account_id, channel_id.
- **Response schema:**
  ```
  [
    {
      "id": "string",
      "account_id": "string",
      "channel_id": "string",
      "name": "string",
      "description": "string",
      "description_html": "string",
      "starts_at": "iso8601-utc",
      "stops_at": "iso8601-utc",
      "poster": "url",
      "preview": "url",
      "tags": ["string"],
      "timeframe": "string",
      "transcoder_profile": "string"
    }
  ]
  ```
- **Observed parameters:**
  - `{channel_id}` (path, required) — `v97dttfeoqpr2vkmzmfo` (City Commission Meetings) or `pzo8uo3hgxrf0pmwalhj` (default channel)
  - `q` (string, optional) — search term (empty-string observed)
  - `s` (string, optional) — sort. `-starts_at` (descending) observed
  - `l` (int, optional) — limit. `l=10` tested; caps/true-max not exercised this pass
- **Probed parameters:**
  - `s=-starts_at&l=10` on channel `v97dttfeoqpr2vkmzmfo` — returned 10 broadcasts; 9,439 bytes
  - Same params on channel `pzo8uo3hgxrf0pmwalhj` — returned 10 broadcasts; 20,436 bytes (broader default-channel catalog)
- **Pagination:** `unverified` — `l` supported; offset / cursor mechanism not probed beyond `l=10`. Typical BoxCast pattern is offset-based via `f` (from) param.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** BoxCast API shape convention
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/channels/v97dttfeoqpr2vkmzmfo/broadcasts?q=&s=-starts_at&l=10'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-channel-cc-broadcasts.json`, `evidence/bartow-fl-boxcast-channel-default-broadcasts.json`
- **Notes:** **CR-adjacent video catalog.** Every broadcast's `name` follows "City Commission Meeting - M/D/YYYY" (or "Commission Meeting - ..." / "Joint Meeting - ..."). For each broadcast the actual playable stream URL is obtained via `/broadcasts/{id}/view` (next endpoint). PII-clean metadata.

#### BoxCast broadcast descriptor

- **URL:** `https://api.boxcast.com/broadcasts/{broadcast_id}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full broadcast metadata — superset of the channel-broadcasts list entry. Includes `account_name`, `account_market`, `do_not_record`, `is_private`, `streamed_at`, `time_zone`, `time_zone_offset`, `poster_url_template`, `thumbnail_url_template`, plus all channel-broadcasts fields.
- **Response schema:**
  ```
  {
    "id": "string",
    "account_id": "string",
    "account_name": "string",
    "account_market": "string",
    "channel_id": "string",
    "name": "string",
    "description": "string",
    "description_html": "string",
    "do_not_record": "bool",
    "free_variant": "string",
    "is_private": "bool",
    "is_ticketed": "bool",
    "poster": "url",
    "poster_url_template": "url",
    "preview": "url",
    "starts_at": "iso8601-utc",
    "stops_at": "iso8601-utc",
    "streamed_at": "iso8601-utc",
    "tags": ["string"],
    "thumbnail_url_template": "url",
    "ticket_price": "number",
    "time_zone": "string",
    "time_zone_offset": "number",
    "timeframe": "string",
    "transcoder_profile": "string",
    "content_settings": {}
  }
  ```
- **Observed parameters:**
  - `{broadcast_id}` (path, required) — e.g. `kwmmo9svs8cd7ia5tl4d`
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** BoxCast embedded player JSON embed in `boxcast.tv/view/...`
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/broadcasts/kwmmo9svs8cd7ia5tl4d'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-broadcast-one.json`
- **Notes:** 2,984 bytes. `time_zone:"America/New_York"`, `transcoder_profile` observed as `hdReady`. `account_market` observed as municipal-govt segmentation.

#### BoxCast broadcast view (playlist manifest + playback tokens)

- **URL:** `https://api.boxcast.com/broadcasts/{broadcast_id}/view`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Playback descriptor — CloudFront-signed HLS playlist URL (`play.boxcast.com/p/{broadcast_id}/v/all-byteranges.m3u8`), audio-only variant, and recorded-content poster/thumb URLs.
- **Response schema:**
  ```
  {
    "playlist": "url",
    "audio_playlist": "url",
    "poster_url": "url",
    "thumbnail_url": "url",
    "status": "string"
  }
  ```
  (schema inferred from 1,163-byte response; not all fields exhaustively enumerated)
- **Observed parameters:**
  - `{broadcast_id}` (path, required)
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time; signed-URL `Expires` timestamp is ~3-5 days out (one sample expired 2025-03-19)
- **Discovered via:** BoxCast API shape convention
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://api.boxcast.com/broadcasts/kwmmo9svs8cd7ia5tl4d/view'
  ```
- **Evidence file:** `evidence/bartow-fl-boxcast-broadcast-view.json`
- **Notes:** This is the playback-manifest endpoint. The returned `playlist` URL is an HLS master playlist — for archival / AI-agenda-extraction workflows, downstream pipelines would pair this with BoxCast's per-broadcast transcript offering (not exposed on this endpoint — likely requires paid tier).

### Legistar OData (broken — drift sentinel only)

#### OData /Bodies (500 — unconfigured)

- **URL:** `https://webapi.legistar.com/v1/bartow/Bodies`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Should return JSON array of Body entities. Actually returns HTTP 500 with `"ExceptionMessage":"LegistarConnectionString setting is not set up in InSite for client: bartow"`.
- **Response schema:**
  ```
  {
    "Message": "string",
    "ExceptionMessage": "string",
    "ExceptionType": "string",
    "StackTrace": "string"
  }
  ```
- **Observed parameters:** none
- **Probed parameters:** `$top`, `$filter`, `$orderby` — not tested (tenant is unconfigured; all would 500).
- **Pagination:** `unverified` (OData `$skip`/`$top` by convention, untestable here)
- **Rate limits observed:** none observed
- **Data freshness:** dead tenant — no data
- **Discovered via:** Planner negative-evidence — Legistar subdomain resolves, routine OData probe.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://webapi.legistar.com/v1/bartow/Bodies'
  ```
- **Evidence file:** `evidence/bartow-fl-legistar-odata.json`
- **Notes:** ⚠️ GAP: tenant unconfigured. Same pattern as Lake Wales Legistar dead shell. Documented as a drift sentinel: if Bartow ever migrates CR to Legistar, this endpoint + siblings (`Events`, `EventItems`, `Matters`, `Persons`, `OfficeRecords`) would activate.

---

## Scrape Targets

### / (CivicPlus CivicEngage home + inner pages)

#### Home page + numeric-ID content pages

- **URL:** `https://www.cityofbartow.net/{id}/{slug}` (e.g. `/1/Home`, `/27/Government`, `/129/Agendas-Minutes`, `/159/Building-Department`, `/162/Permitting-Inspections`, `/443/Permit-Application`, `/161/Contractor-Registration`, `/164/Code-Compliance-Neighborhood-Services`, `/235/Planning`, `/238/Unified-Land-Development-Code`, `/253/Community-Services-Team-CST`, `/294/Planning-Zoning-Commission`, `/303/City-Commission`, etc. — 231 numeric-ID pages enumerated in `/sitemap.xml`)
- **Data available:** CMS-rendered department/page content. Cross-links to other pages, FormCenter widget embeds, outbound vendor links (BoxCast, NEOGOV, Municode, CivicPlus University, CodeRed).
- **Fields extractable:** page title, breadcrumb path, body HTML, Quick Links widget, feature column items (external portal buttons), sidebar navigation tree, FormCenter widget `formID` references.
- **JavaScript required:** no (server-rendered ASP.NET; only `/antiforgery` XHR is JS).
- **Anti-bot measures:** none observed at ~1 req/sec; `robots.txt` disallows admin/search/map/currentevents only.
- **Pagination:** per-page; nav tree enumerated by sitemap (293 entries including supplementary shells).
- **Selectors (if stable):**
  - Page title: `<h1>` within `<main>` or `<div class="widget editor pageStyles">`
  - Breadcrumbs: `#breadCrumbs ol.breadCrumbs li`
  - Body content: `.fr-view` (Froala editor-rendered body)
  - Feature buttons: `a.fancyButton` (cross-link to external vendor portals)
- **Why no API:** CivicPlus doesn't expose a CMS JSON API for inner pages; content is HTML-only.
- **Notes:** Sitemap at `/sitemap.xml` is the canonical enumeration. CR-relevant inner pages: `/303/City-Commission`, `/294/Planning-Zoning-Commission`, `/129/Agendas-Minutes`. BI/PT-relevant: `/159/Building-Department`, `/160/City-of-Bartow-Building-Permit-Fee-Sched`, `/161/Contractor-Registration`, `/162/Permitting-Inspections`, `/443/Permit-Application` (embeds FormCenter formID=72), `/483/Building-Permit-Application`, `/164/Code-Compliance-Neighborhood-Services`. CD2-relevant: `/238/Unified-Land-Development-Code` (links to Municode Library external). Evidence files: `bartow-fl-home.html` + 10 `bartow-fl-page-*` samples.

### /rss.aspx (HTML index)

#### RSS feed index

- **URL:** `https://www.cityofbartow.net/rss.aspx`
- **Data available:** HTML listing of every `/RSSFeed.aspx` endpoint available — 27 categorized feed URLs across 7 ModIDs (1, 51, 53, 58, 63, 65, 76).
- **Fields extractable:** feed title, category name, `/RSSFeed.aspx?ModID=…&CID=…` URL.
- **JavaScript required:** no.
- **Anti-bot measures:** none; `robots.txt` explicitly disallows `/RSS.aspx` (singular capital) but this endpoint `/rss.aspx` (lowercase) is served without challenge.
- **Pagination:** none (all feeds inline).
- **Selectors (if stable):** `<a href="RSSFeed.aspx?ModID=…&CID=…">`.
- **Why no API:** this IS the index page for the RSS APIs above; the individual `/RSSFeed.aspx` endpoints themselves are APIs.
- **Notes:** Evidence `bartow-fl-rss-aspx.html` (93,263 bytes).

### /AgendaCenter (landing)

#### AgendaCenter landing

- **URL:** `https://www.cityofbartow.net/AgendaCenter`
- **Data available:** Grid of upcoming + recent agendas across all 14 boards/committees, with links to `ViewFile/Agenda/{slug}` PDF and `PreviousVersions/{id}` history pages.
- **Fields extractable:** meeting title, date, category ID (CID), `ViewFile/Agenda/_<date>-<id>` slug. 120+ agendas enumerated on the single HTML page.
- **JavaScript required:** no (fully server-rendered 262,121-byte HTML).
- **Anti-bot measures:** none observed.
- **Pagination:** none visible on landing; full archive via `PreviousVersions` or category-filtered `AgendaCenter/Search`.
- **Selectors (if stable):** agenda cards under `.catAgendaRow`; slug in `<a href="/AgendaCenter/ViewFile/Agenda/_<slug>">`.
- **Why no API:** the binary `/AgendaCenter/ViewFile/*` endpoints ARE the API; this landing is the HTML index that links to them; the `/AgendaCenter/Search/` GET (documented above) is the filtered variant. The CR adapter at `cr/adapters/civicplus.py` consumes this shape via the two `bartow-*.yaml` configs.
- **Notes:** Authoritative CR surface for Bartow. Evidence `bartow-fl-agendacenter.html`.

### /AgendaCenter/PreviousVersions/{id}

#### Meeting version history

- **URL:** `https://www.cityofbartow.net/AgendaCenter/PreviousVersions/{id}`
- **Data available:** All historical versions of a given meeting's agenda / packet / minutes documents, with publish timestamps.
- **Fields extractable:** document type (Agenda, Minutes, Packet), version timestamp, `ViewFile/{type}/{slug}` link, amendment notes.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** none per ID.
- **Selectors (if stable):** stable CivicPlus AgendaCenter markup (`.catAgendaRow`).
- **Why no API:** CivicPlus AgendaCenter surfaces its data entirely via HTML + the binary `ViewFile/*` endpoints; no JSON version-history API exists.
- **Notes:** Evidence `bartow-fl-agenda-previous-417.html` (99,221 bytes — for meeting-id 417, the 2026-04-02 Canvassing Board session).

### /DocumentCenter

#### Document Center index

- **URL:** `https://www.cityofbartow.net/DocumentCenter`
- **Data available:** Categorized document archive landing — folder cards with sub-folder navigation into `DocumentCenter/Index/{folderID}` → document links (`DocumentCenter/View/{docID}/{slug}`).
- **Fields extractable:** folder name, sub-folder list, document links.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** per-folder.
- **Selectors (if stable):** `.documentListView` list items.
- **Why no API:** no JSON document-index endpoint observed; sibling `/DocumentCenter/View/1` 404s (IDs assigned non-contiguously; no bulk enumeration).
- **Notes:** Evidence `bartow-fl-documentcenter.html` (81,824 bytes landing). ⚠️ GAP: no way to enumerate folder IDs or document IDs without crawling inner pages.

### /Calendar.aspx

#### Calendar HTML view

- **URL:** `https://www.cityofbartow.net/Calendar.aspx`
- **Data available:** HTML calendar UI showing upcoming events.
- **Fields extractable:** same as Calendar RSS (`ModID=58`) + `iCalendar.aspx`.
- **JavaScript required:** partial (navigation JS; event list server-rendered).
- **Anti-bot measures:** none observed.
- **Pagination:** month/week navigation query params.
- **Selectors (if stable):** `.calendarEvent` entries.
- **Why no API:** same data available via `RSSFeed.aspx?ModID=58` (API) and `common/modules/iCalendar/iCalendar.aspx` (iCal API) — both documented above. **Prefer those APIs.**
- **Notes:** 161,308-byte HTML. Evidence `bartow-fl-calendar-aspx.html`.

### /Archive.aspx

#### Archive Center landing

- **URL:** `https://www.cityofbartow.net/Archive.aspx`
- **Data available:** Archive Center module landing; effectively empty on this tenant — no `AMID` anchors present (probed `/Archive.aspx?AMID=37` → 404).
- **Fields extractable:** none of substance; HTML shell only.
- **JavaScript required:** no.
- **Anti-bot measures:** none observed.
- **Pagination:** n/a (empty).
- **Selectors (if stable):** `.archiveTable` / `#archiveContainer` — empty on this tenant.
- **Why no API:** no content to API-ify; module is provisioned but unused.
- **Notes:** 103,760-byte HTML shell. Evidence `bartow-fl-archive-aspx.html`. Drift sentinel: if Archive Center ever gets populated, `/Archive.aspx?AMID=<n>` typically becomes the landing for a specific archive module.

### /FormCenter

#### FormCenter index

- **URL:** `https://www.cityofbartow.net/FormCenter`
- **Data available:** List of contact/request forms grouped by category.
- **Fields extractable:** form title, form ID, category ID, form URL.
- **JavaScript required:** no (HTML index + `/antiforgery` for form POSTs).
- **Anti-bot measures:** antiforgery token required on POST; no captcha observed on index.
- **Pagination:** none.
- **Selectors (if stable):** sidebar `<a href="/FormCenter/{cat-N}/{form-M}">`.
- **Why no API:** forms are inbound (data-write, not read). No public read of prior submissions.
- **Notes:** 88,494 bytes. Evidence `bartow-fl-formcenter.html`. ⚠️ GAP: the `/FormCenter/ItemViaWidget?formID=72` endpoint referenced from `/443/Permit-Application` returns 404 on direct GET — it's an iframe-embed-only endpoint requiring a parent context.

### /443/Permit-Application (FormCenter widget embed — permit-application paper workflow)

#### Permit application (paper / email submit via FormCenter)

- **URL:** `https://www.cityofbartow.net/443/Permit-Application`
- **Data available:** Static instructions page embedding a **CivicPlus FormCenter widget** (referenced inline as `/FormCenter/ItemViaWidget?formID=72`) for inbound permit-application submission. The page text confirms **email copy / mail** are the submission channels — no online permit portal.
- **Fields extractable:** form structure (field labels, required flags, category selectors like `category0`..`category4`), submit action (CivicPlus `/FormCenter/Submit` convention).
- **JavaScript required:** no for the container page; the widget endpoint is iframe-only and returns 404 on direct GET.
- **Anti-bot measures:** CSRF via `__RequestVerificationToken` (antiforgery-token-gated POST).
- **Pagination:** n/a.
- **Selectors (if stable):** CivicPlus FormCenter widget iframe; page body under `.fr-view`.
- **Why no API:** submission is inbound-only (data-write); no read API for historical permit applications.
- **Notes:** ⚠️ **Key PT finding for Bartow.** Confirms **no online permit portal** — permits are submitted via paper + email through this FormCenter form. Same posture as Dundee. Evidence `bartow-fl-page-443-permit-application.html` (118,308 bytes). Related pages: `/159/Building-Department`, `/162/Permitting-Inspections`, `/161/Contractor-Registration`, `/483/Building-Permit-Application` (duplicate landing).

### Legistar dead tenant

#### Legistar provisioned-but-unconfigured shell

- **URL:** `https://bartow.legistar.com/` (and all Legistar paths: `/Calendar.aspx`, `/People.aspx`, `/LegislationDetail.aspx`, ...). Also `https://bartowfl.legistar.com/` — identical shell.
- **Data available:** **none** — tenant provisioned in Legistar DNS but unconfigured at the application layer.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** none; just fails.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a — response is the literal 19-byte string `Invalid parameters!`.
- **Why no API:** OData 500s with `"LegistarConnectionString setting is not set up in InSite for client: bartow"`.
- **Notes:** ⚠️ GAP: drift sentinel. Identical pattern to Lake Wales. If Bartow ever migrates CR to Legistar, these URLs will activate. For current runs, CivicPlus AgendaCenter is authoritative. Evidence `bartow-fl-probe-legistar.html`, `bartow-fl-probe-legistar-alt.html`, `bartow-fl-legistar-odata.json`.

### NovusAgenda dead tenant

#### NovusAgenda broken shell

- **URL:** `https://bartowfl.novusagenda.com/` → `/AgendaWeb` → `/agendaweb/Error.html?aspxerrorpath=/AgendaWeb`
- **Data available:** **none** — tenant throws ASP.NET runtime error chain.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a.
- **Why no API:** application-level error; both primary and error-fallback pages fail.
- **Notes:** ⚠️ GAP: drift sentinel. Same pattern as Lake Wales NovusAgenda. Likely orphan from pre-CivicPlus CR platform era. Evidence `bartow-fl-probe-novusagenda.html`, `bartow-fl-probe-novusagenda-agendaweb.html`.

### Granicus (no tenant)

#### Granicus ViewPublisher placeholder

- **URL:** `https://bartow.granicus.com/ViewPublisher.php?view_id=1`
- **Data available:** **none** — 302 redirect to `/core/error/NotFound.aspx?Url=%2FViewPublisher.php%3Fview_id%3D1`. No Granicus tenant for Bartow.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** n/a.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a.
- **Why no API:** no tenant provisioned.
- **Notes:** Unlike Lake Wales, Bartow does NOT use Granicus for video archive — it uses BoxCast. Evidence `bartow-fl-probe-granicus.html` + `.headers.txt` (captures the 302 Location header).

### GovBuilt placeholder (no tenant)

#### GovBuilt wildcard-DNS placeholder

- **URL:** `https://bartowfl.govbuilt.com/` and `https://cityofbartow.govbuilt.com/`
- **Data available:** **none** — 31,611 / 31,619 byte generic placeholder HTML.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** n/a.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a — `<title>GOVBUILT PLATFORM - Tomorrow's Government Built Today</title>` is the placeholder signature.
- **Why no API:** no tenant provisioned; matches `_platforms.md` GovBuilt placeholder detection discipline.
- **Notes:** Evidence `bartow-fl-probe-govbuilt1.html`, `bartow-fl-probe-govbuilt2.html`. API probe of `/PublicReport/GetAllContentToolModels` not exercised (would return the 8.1-KB 404 error page per established placeholder pattern).

### iWorQ empty tenant

#### iWorQ Laravel 404 shell

- **URL:** `https://bartow.portal.iworq.net/portalhome/bartow` + `https://cityofbartow.portal.iworq.net/portalhome/cityofbartow`
- **Data available:** **none** — 3,207 / 3,213 byte Laravel "Page Can Not Be Found" response.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** n/a.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a.
- **Why no API:** no tenant provisioned.
- **Notes:** Evidence `bartow-fl-probe-iworq.html`, `bartow-fl-probe-iworq-alt.html`.

### SmartGov (no tenant)

#### SmartGov Public Portal 404

- **URL:** `https://ci-bartow-fl.smartgovcommunity.com/Public/Home`
- **Data available:** **none** — HTTP 404 "The resource you are looking for has been removed, had its name changed, or is temporarily unavailable." Neither standard nor `.validation.` subdomain responds.
- **Fields extractable:** none.
- **JavaScript required:** n/a.
- **Anti-bot measures:** n/a.
- **Pagination:** n/a.
- **Selectors (if stable):** n/a.
- **Why no API:** no tenant provisioned.
- **Notes:** Evidence `bartow-fl-probe-smartgov.html` (103-byte 404 body).

---

## External Platforms (cross-reference only; not deep-mapped here)

- **Municode Library** — `library.municode.com/fl/bartow`. Covered by existing `_platforms.md` row. Angular SPA; code-of-ordinances CD2 surface. Not deep-probed this pass.
- **NEOGOV GovernmentJobs** — `www.governmentjobs.com/careers/bartow`. External employment portal; covered by NEOGOV generally; not deep-mapped. Evidence `bartow-fl-neogov-root.html` (192 KB landing).
- **Polk County parent infrastructure** — Polk County Property Appraiser (`polkpa.org` / `polkflpa.gov`), Polk County Clerk Official Records (NewVision BrowserView on `apps.polkcountyclerk.net/browserviewor/`), Polk County Clerk of Courts civil / court records (Tyler Odyssey PRO on `pro.polkcountyclerk.net/PRO`), Polk County Legistar — documented in `docs/api-maps/polk-county-fl.md`. Parcel GIS + court records for Bartow properties ride Polk's services.
- **Crisis24 CodeRed (emergency alerts)** — `public.coderedweb.com/CNE/en-US/BF6E3000010E`. Linked from the Building Department page as the public sign-up for emergency notifications. Probe **TIMED OUT** from this network (15-second curl timeout on Connect). Outbound-only opt-in portal; no public read API. Not deep-mapped.
- **Azure Monitor AppInsights** — `js.monitor.azure.com/scripts/a/ai.0.js` (instrumentation key `1cde048e-3185-4906-aa46-c92a7312b60f`, shared CivicPlus tenant telemetry). Outbound telemetry; no public read surface.
- **AudioEye accessibility** — `wsmcdn.audioeye.com/aem.js`. Outbound script; no data surface.
- **DocAccess** — `docaccess.com/docbox.js`. Accessibility widget for document embeds; outbound only.
- **CivicPlus control plane** — `connect.civicplus.com/referral` + `cp-civicplusuniversity2.civicplus.com`. Vendor CMS operational surfaces; no tenant data.
- **Facebook / social** — `facebook.com/bartowfloridacity`. Outbound social only.

---

## Coverage Notes

- **Total requests this run:** ~46 unique HTTPS probes (plus 5 DNS-fail entries logged and 1 TIMEOUT entry). Well under the 2000 cap. No 429s, no captchas, no WAF blocks on `cityofbartow.net`. Pacing ~1 req/sec throughout.
- **User-Agent:** `Mozilla/5.0 (compatible; CountyDataMapper/1.0)` per Lake Hamilton finding.
- **Request log:** `evidence/_bartow-fl-request-log.txt` enumerates every request with timestamp, status code, URL, and output file.
- **robots.txt stance per hostname (operational-risk signal):**
  - `www.cityofbartow.net` — standard CivicPlus `Disallow` set (admin/search/map/currentevents/`/RSS.aspx`); `/RSSFeed.aspx` allowed; Siteimprove `Crawl-delay: 20`; Baidu + Yandex fully disallowed. Mapping pass compliant (no disallowed path requested).
  - `fl-bartow.civicplus.com` — **`Disallow: /` for `*`** (only a Screaming Frog UUID is `Allow:/`). Mapping pass touched this host with 3 requests (`/`, `/Directory.aspx`, `/robots.txt`) — operationally safe at this volume but **prefer `www.cityofbartow.net` for any data access** because it's the public canonical CNAME.
  - `boxcast.tv` — `User-agent: * \n Disallow:` (fully permissive).
  - `bartow.legistar.com`, `bartowfl.legistar.com`, `bartowfl.novusagenda.com`, `bartow.granicus.com`, `*.govbuilt.com`, `*.portal.iworq.net`, `*.smartgovcommunity.com` — robots not probed (dead/empty tenants — not worth the request budget).
- **Meeting-vendor disambiguation (authoritative for current CR data):** **CivicPlus AgendaCenter on `www.cityofbartow.net`.** Matches both `bartow-cc.yaml` (`platform: civicplus`, `category_id: 5` — City Commission) and `bartow-pz.yaml` (`platform: civicplus`, `category_id: 2` — Planning-Zoning Commission). Legistar and NovusAgenda tenants exist as DNS artifacts but are BROKEN (Legistar unconfigured, NovusAgenda ASP.NET runtime error). **BoxCast hosts commission-meeting video** (channel `v97dttfeoqpr2vkmzmfo`), not Granicus; unlike Lake Wales which uses Granicus.
- **Agenda Creator RSS (ModID=65) posture:** **Provisioned but EMPTY on this tenant.** Every category filter (including `City-Commission-5`, `Planning-Zoning-Commission-2`, `Community-Redevelopment-Agency-12`) returns a 328–363 byte empty-channel RSS skeleton. Unlike Lake Wales, this feed is not a viable CR discovery path. Agenda discovery must use the AgendaCenter HTML landing or `AgendaCenter/Search/?CIDs=…` GET endpoint — both verified live. Drift sentinel: monitor for population.
- **BoxCast platform decision:** **Direct-edited into `_platforms.md`.** Real scrapable data surface: `api.boxcast.com` returns unauthenticated JSON for `/accounts/{id}`, `/accounts/{id}/channels`, `/channels/{id}`, `/channels/{id}/broadcasts`, `/broadcasts/{id}`, `/broadcasts/{id}/view`. Embedded view pages at `boxcast.tv/view/{channel_id}` include the full player JSON inline. Signatures verified on Bartow. Justifies direct-edit per Lake Alfred QA ruling.
- **NEOGOV / Municode:** External; not promoted to new `_platforms.md` rows. Both are pre-existing well-known platforms (Municode already has a row; NEOGOV is a standalone careers portal sufficient as a one-liner here).
- **GovBuilt / SmartGov / iWorQ / Accela / Tyler EnerGov / CityView / Cloudpermit / PermitTrax / Laserfiche / CivicClerk / eScribe / iCompass / BoardDocs / iQM2 / Catalis / Authority Pay / ADG:** Not observed (negative evidence confirmed where tested; the rest ruled out by Planner per plan-file vendor pre-recon).
- **`bartowfl.gov` DNS status:** **Still down.** Retried all four subdomains (`bartowfl.gov`, `secure.bartowfl.gov`, `utility.bartowfl.gov`, `permits.bartowfl.gov`) via curl + nslookup; every probe returned `code=000` with empty `remote_ip`. ⚠️ GAP: if the domain ever resolves, there may be a secondary City of Bartow property (perhaps an ADG-powered permit/utility portal — mirroring Lake Wales's `secure.lakewalesfl.gov/ubs1` + `/permits`). Re-probe on the next mapping run. For this run: no evidence such a portal exists — all utility / permit workflows route through the CMS and email.
- **Permit posture:** **PAPER / EMAIL ONLY.** `/443/Permit-Application` (and its sibling `/483/Building-Permit-Application`) embeds a CivicPlus FormCenter inbound widget (`formID=72`); the page text explicitly describes email + mail submission. No online permit portal. Same posture as Dundee. **⚠️ GAP: no PT-relevant public data surface for Bartow.** Permit inventory reconstruction would require public-records requests or scraping recorded commission meetings on BoxCast for permit-granting votes. BI/PT scrapers have **no adapter target** for Bartow beyond the CivicPlus FormCenter submit (outbound).
- **Known unsurveyed / ⚠️ GAPs:**
  - `/AgendaCenter/UpdateCategoryList` POST endpoint — required CSRF token; not exercised (GET returns 404; behavior with `__RequestVerificationToken` POST untested).
  - `/ImageRepository/Document` — no way to enumerate valid documentIDs without parsing referring HTML.
  - `/DocumentCenter/Index/{folderID}` inner folders — not individually crawled (no bulk folder-ID enumeration).
  - BoxCast `l=` upper bound / offset pagination on `/channels/{id}/broadcasts` — not fully exercised; likely `f` (from) param per BoxCast convention.
  - Municode Library `clientId` for Bartow — not resolved (SPA requires browser for `api.municode.com/codes/{clientId}/nodes` enumeration).
  - `bartowfl.gov` family — DNS down; ⚠️ re-probe next run.
- **Evidence directory:** all files prefixed `bartow-fl-*` under `docs/api-maps/evidence/`. Key samples: home HTML, sitemap.xml, robots per host, `/antiforgery` JSON, 9 RSS feed samples, 2 iCal exports, AgendaCenter landing + search + sample PreviousVersions + sample ViewFile PDF, BoxCast 7-endpoint suite, Legistar OData 500, NovusAgenda runtime-error follow, GovBuilt placeholder, iWorQ Laravel 404, SmartGov 404, 10 CMS inner pages (Building / Permit / Planning / Code / ULDC / Commission / P&Z / Agendas-Minutes / Code-Compliance).
