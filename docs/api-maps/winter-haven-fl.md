# Winter Haven, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://www.mywinterhaven.com/` (city of Winter Haven, Polk County). One-file scope: city of Winter Haven only — county-level (Polk) is mapped separately.
>
> Crawl conducted in **degraded mode** (curl-only) — verified safe because `https://www.mywinterhaven.com/` is server-rendered ASP.NET (CivicPlus CivicEngage); no SPA hydration markers (`__NEXT_DATA__`, `data-reactroot`, `ng-app`, `__NUXT__`, etc.) were found. The only JS markers are a bootstrap-style `XMLHttpRequest` for `/antiforgery` and analytics widgets. The Accela Citizen Access portal at `aca-prod.accela.com/COWH` is Angular (`ng-app="appAca"`) — its Default.aspx + CAP module pages render server-side enough to enumerate tabs/modules, but deep Building record search will need a real browser session on the next pass.

## Summary

- **Jurisdiction:** City of Winter Haven (within Polk County, FL).
- **City website platform:** CivicPlus CivicEngage (classic numeric-ID URL pattern, e.g. `/342/Building-Permits-Licenses`). Title suffix `• CivicEngage` confirmed on module pages. Served under `www.mywinterhaven.com` (canonical) with a mirror at `fl-winterhaven.civicplus.com`.
- **Commission surface:** Granicus ViewPublisher at `winterhaven-fl.granicus.com?view_id=1`, already mapped by the CR adapter (`modules/commission/config/jurisdictions/FL/winter-haven-cc.yaml` + `winter-haven-pc.yaml`). Body filter selects City Commission vs Planning Commission inside the single view.
- **Permit surfaces (three co-existing platforms):**
  1. **Accela Citizen Access** — agency code `COWH`, tenant `aca-prod.accela.com/COWH`. Building module is public; Enforcement/Planning/Licenses appear to be disabled for anon. This is the ACCELA-16 tenant (see Coverage Notes).
  2. **Tyler New World eSuite** — `myinspections.mywinterhaven.com/eSuite.Permits/`. Inspection/permit lookups are session-gated (ASP.NET web forms with VIEWSTATE; unauth requests redirect to Error.aspx). "myinspections" branding.
  3. **Avolve ProjectDox (ePlans)** — `eplans.mywinterhaven.com/Portal/Login/...`. Plan-review portal, auth-gated. Served via `redirect.pizza` edge.
- **Other vendor surfaces:** OpenGov Procurement (403 anon), OpenGov Stories (deep-link only), SeeClickFix 311, Column legal notices, Civilspace engagement, Citibot chat, Jotform, eGovLink legacy archive, Municode Library code of ordinances, Corebook brand portal, `events.mywinterhaven.com` community calendar (Yii2 platform, slug `winterhavenfl`).
- **No ArcGIS / FeatureServer / MapServer endpoints** were found on the city footprint. City-level GIS appears to ride Polk County's service, which is out of this file's scope. ⚠️ GAP: Polk GIS cross-reference deferred to the Polk County map.
- **Request count this run:** 100 (well under the 2000 cap). No 429s, no captcha challenges, no robots violations.

## Platform Fingerprint

| Host | Platform | Fingerprint |
|---|---|---|
| `www.mywinterhaven.com` | **CivicPlus CivicEngage** | URL pattern `/{numeric-id}/{slug}`; ASP.NET_SessionId cookie; `CP_IsMobile` cookie; title suffix `• CivicEngage`; CSP `frame-ancestors` includes `platform.civicplus.com`, `account.civicplus.com`, `analytics.civicplus.com`; `/antiforgery` bootstrap JSON endpoint; `/RSSFeed.aspx?ModID=…` feed index via `/rss.aspx`. |
| `fl-winterhaven.civicplus.com` | CivicPlus CivicEngage (alt-domain mirror) | Same CMS, serves same pages as `www.mywinterhaven.com` under the vendor-native hostname. |
| `winterhaven-fl.granicus.com` | **Granicus ViewPublisher** | Already cataloged in `_platforms.md` + `modules/commission/config/jurisdictions/FL/winter-haven-cc.yaml` / `winter-haven-pc.yaml`. view_id=1, body_filter separates CC vs PC. |
| `aca-prod.accela.com/COWH` | **Accela Citizen Access** | `ng-app="appAca"`, Cloudflare edge, `ApplicationGatewayAffinity` cookies, tab metadata in the Default.aspx response exposes module list. Accela REST v4 remains anon-blocked per `docs/api-maps/accela-rest-probe-findings.md`. |
| `myinspections.mywinterhaven.com` | **Tyler New World eSuite (Permits)** | ASP.NET WebForms, `__VIEWSTATE`, CSS namespace `NewWorld.eSuite.Common.Web.Shared`, Walkme analytics injected. `eSuite.Permits/` root. |
| `eplans.mywinterhaven.com` | **Avolve ProjectDox** | `<title>ProjectDox Login</title>`, served via `redirect.pizza` edge (`X-Powered-By: redirect.pizza`, `X-Server: mex0.prod.edge.redirect.pizza`). |
| `events.mywinterhaven.com` | Yii2-based community-events platform (vendor not identified) | `_frontendCSRF` cookie with Yii2-style base64 CSRF payload, `session_` cookie, client prefix `winterhavenfl`. Soft 404s (200 HTML with "Page not found" div) for unknown routes. |
| `library.municode.com/fl/winter_haven` | **Municode Library** | Already cataloged. Code of Ordinances for Winter Haven. Client ID not resolved in this curl-only pass (SPA-rendered). ⚠️ GAP: re-enumerate with a browser next run to capture `api.municode.com/codes/{client_id}/nodes`. |
| `cityofwinterhaven.column.us` | Column | Legal notices (foreclosures, public hearings). Separate scrape profile. |
| `procurement.opengov.com/portal/winterhavenfl` | **OpenGov Procurement** | 403 anon; likely requires session. ⚠️ GAP. |
| `stories.opengov.com/winterhavenfl` | OpenGov Stories | 404 on base; deep-link only (linked from home). ⚠️ GAP. |
| `winter-haven-fl.civilspace.io` | Civilspace | Community engagement polls / forums. Not explored in this pass. |
| `seeclickfix.com/web_portal/SdLPekA3hqCyR5wYB2xDUDHd` | SeeClickFix | 311-style reports with public feed ID. |

New platforms observed in this run that are **not yet in `docs/api-maps/_platforms.md`**: _Tyler New World eSuite (Permits)_, _Avolve ProjectDox (ePlans)_, _Column (legal notices)_, _Civilspace_, _Citibot_ chat, Yii2 community-events platform at `events.mywinterhaven.com`. Adding them to the registry is deferred to a separate housekeeping task.

---

## APIs

### /antiforgery

#### Antiforgery token

- **URL:** `https://www.mywinterhaven.com/antiforgery`
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
  - `unverified` — only observed as a parameterless GET. Calling additional params had no observed effect.
- **Pagination:** `none`
- **Rate limits observed:** none observed at ~1 req/sec
- **Data freshness:** real-time (per-session)
- **Discovered via:** Inline `getAntiForgeryToken` script in `/` home HTML that bootstraps CSRF tokens into every POST form on the page.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/antiforgery'
  ```
- **Evidence file:** `evidence/winter-haven-fl-antiforgery.json`
- **Notes:** Token must be submitted as `__RequestVerificationToken` field on form POSTs back to `mywinterhaven.com` (but not on absolute URLs, per the inline `absPat` check). Not useful for data extraction on its own, but is the gate for any POST-driven search/contact forms.

### /RSSFeed.aspx

CivicPlus RSS-feed endpoints. Module IDs observed: 1 (News Flash), 51 (Blog), 53 (Street Pole Banners), 58 (Calendar), 65 (Agenda Creator), 66 (Jobs). Each supports an optional `CID` (category) filter. The canonical index of feeds is at `/rss.aspx` (HTML listing).

#### News Flash RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
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
        <enclosure url="url" length="int" type="mime" />  <!-- optional -->
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:**
  - `ModID` (int, required) — `1` for News Flash. Observed values: `1`, `51`, `53`, `58`, `65`, `66`.
  - `CID` (string, optional) — category filter, slug-then-numeric-id form e.g. `All-newsflash.xml`, `City-Commission-34`, `Home-Page-1`. Discovered from `/rss.aspx`.
- **Probed parameters:**
  - `CID=All-0` — returned the full-feed (all items across all categories).
  - `CID=City-Commission-34`, `CID=City-Managers-Office-18`, `CID=Home-Page-1` — each returns the subset of News Flash items tagged to that category.
  - `ModID=9999` (bogus) — still returned HTTP 200 with an empty-channel RSS skeleton (no items), not a 404. Treat as silent-empty.
- **Pagination:** `none` — RSS returns a trailing window (observed ~latest N items; exact cap not identified but not unbounded).
- **Rate limits observed:** none at 1 req/sec.
- **Data freshness:** real-time (CivicPlus updates feed as CMS authors publish).
- **Discovered via:** `/rss.aspx` HTML index links every CivicPlus RSS feed the site exposes.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=1'
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml'
  ```
- **Evidence file:** `evidence/winter-haven-fl-rssfeed-modid1.xml` (trimmed to 5 items)
- **Notes:** `ModID=1` is shared across CivicPlus CivicEngage tenants. The same endpoint with different `ModID` values returns other modules (documented below). Bogus `ModID` values return empty-but-valid RSS, so don't rely on status codes for existence.

#### Blog RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Latest blog posts for the city, with category subfeeds.
- **Response schema:** Same RSS 2.0 shape as News Flash.
- **Observed parameters:**
  - `ModID=51` (int, required)
  - `CID` (string, optional) — observed: `All-blog.xml`, `Haven-Highlights-6`, `Parks-Recreation-Culture-4`, `Public-Works-1`.
- **Probed parameters:** Same CID expansion behavior as News Flash.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=51&CID=All-blog.xml'
  ```
- **Evidence file:** `evidence/winter-haven-fl-probe-RSSFeed.aspx_ModID_1.out` — shares the shared RSS format; no module-specific evidence saved (redundant with News Flash shape). A fresh blob can be captured on next run if needed.
- **Notes:** `unverified` whether pagination/count overrides exist.

#### Street Pole Banners RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Street-pole banner program items (public-works decorative program).
- **Response schema:** RSS 2.0 shape.
- **Observed parameters:**
  - `ModID=53` (int, required)
  - `CID` (string, optional) — observed: `All-0`, `Street-Pole-Banners-2`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** low update cadence (seasonal).
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=53&CID=All-0'
  ```
- **Evidence file:** _(not captured in this run — niche module; skeleton matches News Flash)_
- **Notes:** Low-value for BI/PT/CR/CD2 purposes; documented for completeness.

#### Calendar RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Upcoming city calendar events (public events module, separate from `events.mywinterhaven.com`).
- **Response schema:**
  ```
  <rss version="2.0" xmlns:calendarEvent="https://www.mywinterhaven.com/Calendar.aspx">
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
        <description>string (html)</description>
        <guid isPermaLink="bool">string</guid>
        <!-- plus calendarEvent:* extension elements, not enumerated in this pass -->
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:**
  - `ModID=58` (int, required)
  - `CID` (string, optional) — observed: `All-calendar.xml`, `City-Operational-Days-Holidays-14`, `Library-Programs-24`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx` + homepage footer.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=58&CID=All-calendar.xml'
  ```
- **Evidence file:** `evidence/winter-haven-fl-rssfeed-modid58.xml` (trimmed to 5 items)
- **Notes:** The RSS includes a `calendarEvent:` namespace — additional structured event metadata likely lives there but was not enumerated in the degraded-mode pass. ⚠️ GAP: enumerate `calendarEvent:*` sub-elements on next run.

#### Agenda Creator RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RSS feed of AgendaCenter entries (agendas, minutes). Observed **empty** at crawl time even for `CID=All`.
- **Response schema:** RSS 2.0 shape (empty `<channel>` observed — no `<item>` entries).
- **Observed parameters:**
  - `ModID=65` (int, required)
  - `CID` (string, optional) — observed: `All`, `15`, `16`.
- **Probed parameters:**
  - `CID=All` — returned empty channel despite AgendaCenter having populated `ViewFile/Agenda/…` records (see HTML scrape target). Treat as a known-unreliable feed — the HTML AgendaCenter surface has data the RSS does not.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** stale/empty at time of survey.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?ModID=65&CID=All'
  ```
- **Evidence file:** `evidence/winter-haven-fl-rssfeed-modid65.xml`
- **Notes:** ⚠️ GAP: RSS feed reports zero agenda items but the AgendaCenter HTML shows historic agendas (e.g. 2018–2023). Prefer the Granicus ViewPublisher path already used by the CR adapter, or scrape the HTML. Re-check the feed on next run — may be a temporary misconfiguration at the CMS side.

#### Jobs RSS

- **URL:** `https://www.mywinterhaven.com/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Open job postings, with category filters.
- **Response schema:** RSS 2.0.
- **Observed parameters:**
  - `ModID=66` (int, required)
  - `CommunityJobs` (bool, optional) — observed as `CommunityJobs=False` on the canonical URL from `/rss.aspx`.
  - `CID` (string, optional) — observed: `All-0`, `Full-Time-98`, `PartTime-99`, `Summer-100`, `InternalOnly-Opportunities-102`.
- **Probed parameters:** `unverified`
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/rss.aspx`.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/RSSFeed.aspx?CommunityJobs=False&ModID=66&CID=All-0'
  ```
- **Evidence file:** _(not captured — low value for this codebase's modules)_
- **Notes:** out-of-scope for BI/PT/CR/CD2 but cataloged per §8 "document everything."

### /sitemap.xml

#### Sitemap

- **URL:** `https://www.mywinterhaven.com/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** 350 URL entries across all CivicPlus-published pages (standard sitemaps.org schema with `<loc>`, `<lastmod>`, `<changefreq>`).
- **Response schema:**
  ```
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
      <loc>url</loc>
      <lastmod>YYYY-MM-DD</lastmod>
      <changefreq>string</changefreq>
    </url>
    ...
  </urlset>
  ```
- **Observed parameters:** none
- **Probed parameters:** none (single URL, no query space).
- **Pagination:** `none` — entire index in one response.
- **Rate limits observed:** none
- **Data freshness:** CMS-managed; individual `<lastmod>` dates span 2023–2025.
- **Discovered via:** Standard `/sitemap.xml` probe.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/sitemap.xml'
  ```
- **Evidence file:** `evidence/winter-haven-fl-sitemap.xml` (full — 350 URLs, not truncated because the crawl corpus fits in one probe).
- **Notes:** Primary discovery index for breadth-first crawling on the next pass.

### /robots.txt

#### robots.txt

- **URL:** `https://www.mywinterhaven.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots exclusion rules (plain text, not XML/JSON but per §4.2 is a documented machine-readable protocol — classified as API).
- **Response schema:** standard robots.txt format (user-agent blocks + disallow lines).
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** CMS-managed.
- **Discovered via:** Standard `/robots.txt` probe.
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/robots.txt'
  ```
- **Evidence file:** `evidence/winter-haven-fl-robots.txt`
- **Notes:** See Coverage Notes for restriction summary. Baiduspider and Yandex are blanket-denied; all crawlers are disallowed from `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/Support`, `/currenteventsview.aspx`, `/search.aspx`, `/currentevents.aspx` (each case-variant listed), and a handful of other admin paths.

### /AgendaCenter/

The AgendaCenter module exposes a search form backed by a GET endpoint. The broken RSS feed (ModID=65) is documented above under `/RSSFeed.aspx`. The Granicus ViewPublisher remains the canonical commission data source (configured in CR YAMLs).

#### AgendaCenter search

- **URL:** `https://www.mywinterhaven.com/AgendaCenter/Search/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML fragment of agenda/minutes records matching the given filters. Contains embedded links in the form `/AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{id}` and `/AgendaCenter/ViewFile/Minutes/_…` which resolve (via 302) to the PDF.
- **Response schema:** HTML — this endpoint returns markup, not JSON. Listed under APIs only because it's the search **query** surface; data is HTML. Record links include:
  ```
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}           # PDF
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}?html=true  # HTML variant
  /AgendaCenter/ViewFile/Agenda/_{MMDDYYYY}-{numeric-id}?packet=true # full packet PDF
  ```
- **Observed parameters:**
  - `term` (string, optional) — free-text search.
  - `CIDs` (string, optional) — comma-separated category IDs or `all`. Observed category IDs: `15`, `16`.
  - `startDate` (string, optional) — MM/DD/YYYY.
  - `endDate` (string, optional) — MM/DD/YYYY.
  - `dateRange` (string, optional) — UI-populated presets.
  - `dateSelector` (string, optional) — UI state passthrough.
- **Probed parameters:**
  - `CIDs=all` with all other params empty returned a populated HTML listing including agendas from 2018–2023.
  - `POST /AgendaCenter/UpdateCategoryList` returned 404 despite being referenced in JS — either method-mismatch or anti-CSRF required. Not explored further.
- **Pagination:** `unverified` — not exercised (listing returned multiple results; exact cap unknown).
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** `/AgendaCenter` root page JS (`onSearch` handler).
- **curl:**
  ```bash
  curl 'https://www.mywinterhaven.com/AgendaCenter/Search/?term=&CIDs=all&startDate=&endDate=&dateRange=&dateSelector='
  ```
- **Evidence file:** `evidence/winter-haven-fl-agenda-search.html`
- **Notes:** Since the Granicus ViewPublisher is the canonical commission source (configured in `modules/commission/config/jurisdictions/FL/winter-haven-cc.yaml`), this endpoint is documented but not the primary path for CR. The two CIDs likely map to City Commission vs Planning Commission categories — confirm on next run by diffing `CIDs=15` vs `CIDs=16` results.

### ViewPublisher.php (Granicus)

#### Granicus meetings view

- **URL:** `https://winterhaven-fl.granicus.com/ViewPublisher.php`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML table of meetings with media / agenda / minutes links, filterable by `view_id`. Winter Haven uses a single view (1) for both City Commission and Planning Commission, distinguished by the `Body` column.
- **Response schema:** HTML — this is classified as a Scrape Target per §4.2 would be more correct, but the CR adapter treats ViewPublisher as a structured API surface (consistent DOM schema per tenant). Documented here for cross-ref; full schema + parser lives at `cr/adapters/granicus.py` / `modules/commission/adapters/granicus.py`.
- **Observed parameters:**
  - `view_id` (int, required) — `1` for Winter Haven.
- **Probed parameters:** Not re-probed in this pass — CR adapter already validated. See `_platforms.md`.
- **Pagination:** effectively paginated by year-archive links inside the HTML.
- **Rate limits observed:** `unverified` in this pass; CR pipeline runs at ~1 req/sec without issue.
- **Data freshness:** real-time.
- **Discovered via:** Homepage footer link + existing CR YAML config.
- **curl:**
  ```bash
  curl 'https://winterhaven-fl.granicus.com/ViewPublisher.php?view_id=1'
  ```
- **Evidence file:** `evidence/winter-haven-fl-granicus-viewpublisher.html`
- **Notes:** `winterhaven-fl.granicus.com/podcast.php?site_id=1` returned **403** on this pass (Cloudflare challenge body) — not a reliable programmatic feed. Stick with ViewPublisher HTML.

### Accela Citizen Access (`aca-prod.accela.com/COWH`)

Accela tenant for Winter Haven is `COWH` (City Of Winter Haven). Anonymous browsing is limited to the **Building** module; Enforcement, Planning, and Licenses tabs return the generic landing page without a populated tab ribbon. This is the ACCELA-16 tenant referenced in the project tracker (`TODO.md`).

#### Accela Default.aspx (tab metadata)

- **URL:** `https://aca-prod.accela.com/COWH/Default.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML landing with an embedded JavaScript data structure (`[['Links',[[['Active',...],['Label',...],['URL',...]]]]]`) that enumerates the tenant's tabs, modules, and associated URLs. Not JSON but machine-parseable.
- **Response schema:** HTML with inline JS-encoded array-of-records. Observed record fields per tab entry: `Active`, `Label`, `Key`, `Title`, `URL`, `Module`, `Order`. Tabs observed: `Home` (with child links for `Welcome`, `Search Records/Applications`, `Advanced Search`, `Lookup Property Information`, `Search for a Provider/Education`, `Search for a Licensee`) and `Building` (`Search Applications`, `Schedule an Inspection`, `Create Application`).
- **Observed parameters:** none
- **Probed parameters:** Tab query variants (`?TabName=…`, `?module=…`) exist as downstream URLs the payload links to, not on Default.aspx itself.
- **Pagination:** `none`
- **Rate limits observed:** none at ~1 req/sec. The tenant is fronted by Cloudflare with `_cfuvid` cookie; sustained higher load would likely trigger a challenge.
- **Data freshness:** real-time (tenant configuration).
- **Discovered via:** Link from `https://www.mywinterhaven.com/342/Building-Permits-Licenses`.
- **curl:**
  ```bash
  curl -L 'https://aca-prod.accela.com/cowh/' -o default.html  # 301 -> /COWH/Default.aspx
  ```
- **Evidence file:** `evidence/winter-haven-fl-accela-Default.aspx.html`
- **Notes:** The 301 from lowercase `/cowh/` to mixed-case `/COWH/` is stable — use the mixed-case form directly to avoid a redirect hop. Response Cloudflare-cached (`cf-cache-status: DYNAMIC`). ACCELA-16: this is the P1 open item re: Winter Haven enforcement module HTML probe.

#### Accela CAP module home (Building — anonymous)

- **URL:** `https://aca-prod.accela.com/COWH/Cap/CapHome.aspx`
- **Method:** `GET`
- **Auth:** `none` for the landing ribbon; record search requires session cookies.
- **Data returned:** Accela Citizen Access module landing page for a named module. Returns an ASPX form with a module-specific tab set, search input, and VIEWSTATE. Records themselves are retrieved via POST-back with VIEWSTATE, which a curl-only pass cannot drive cleanly — needs browser or a full web-forms session implementation.
- **Response schema:** HTML/ASPX — ViewState-driven postbacks.
- **Observed parameters:**
  - `module` (string, required) — values observed: `Building`, `Planning`, `Enforcement`, `Licenses`. All four returned HTTP 200, but only `Building` has populated tab ribbons in the DOM. The others render the generic agency-title "Welcome!" page.
  - `IsToShowInspection` (bool, optional) — observed as `yes` on the "Schedule an Inspection" child link.
  - `TabName` (string, optional) — e.g. `Building`, `Home`.
- **Probed parameters:**
  - All four `module` values: only `Building` returned meaningful content.
  - No sort/filter/pagination parameters are exposed via GET — they're postback-driven.
- **Pagination:** `none` via GET; postback-driven on search results.
- **Rate limits observed:** none at ~1 req/sec.
- **Data freshness:** real-time.
- **Discovered via:** Accela Default.aspx tab metadata.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/COWH/Cap/CapHome.aspx?module=Building'
  curl 'https://aca-prod.accela.com/COWH/Cap/CapHome.aspx?module=Building&IsToShowInspection=yes'
  ```
- **Evidence file:** `evidence/winter-haven-fl-accela-Cap_CapHome.aspx_module_Building.html`
- **Notes:** Existing permit adapter at `modules/permits/scrapers/adapters/winter_haven.py` extends `AccelaCitizenAccessAdapter` with `agency_code="COWH"`, `module_name="Building"`, `target_record_type="Building/Residential/New/NA"` but hard-wires the comment *"the COWH Accela portal requires authentication to access the Building module search."* This run confirmed that the module **landing** page is public; whether anonymous record search is blocked needs a real-browser probe (ACCELA-16). ⚠️ GAP: resolve anon-search status with a browser.

#### Accela APO / GeneralProperty lookups

- **URL:** `https://aca-prod.accela.com/COWH/APO/APOLookup.aspx` (and `/COWH/GeneralProperty/PropertyLookUp.aspx`)
- **Method:** `GET`
- **Auth:** `none` to render; results likely postback-driven.
- **Data returned:** Property / licensee lookup forms.
- **Response schema:** HTML/ASPX.
- **Observed parameters:**
  - `TabName` (string, optional) — `Home`.
  - `isLicensee` (string, optional) — `Y` on the "Search for a Licensee" link.
- **Probed parameters:** `unverified` — landing only, not exercised.
- **Pagination:** `none` via GET.
- **Rate limits observed:** none
- **Data freshness:** real-time.
- **Discovered via:** Accela Default.aspx tab metadata.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/COWH/APO/APOLookup.aspx?TabName=Home'
  curl 'https://aca-prod.accela.com/COWH/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y'
  ```
- **Evidence file:** _(not captured in this pass — landing only; deferred to next run)_
- **Notes:** ⚠️ GAP: capture APO lookup response on next browser-enabled pass. Public property lookup could be a useful parcel-resolver if it works anonymously.

---

## Scrape Targets

### / (CivicPlus CivicEngage content pages)

Every page under `www.mywinterhaven.com/{numeric-id}/{slug}` is server-rendered HTML with stable DOM. Representative pages probed this run:

#### City home

- **URL:** `https://www.mywinterhaven.com/`
- **Data available:** Site navigation, featured news flash teasers, quicklinks (residents/business/government/how-do-I), social-media links, department drill-down, footer with vendor links.
- **Fields extractable:** News Flash titles + dates + descriptions (or use RSS); quicklink URLs (categorized navigation); weather widget state; footer contact block.
- **JavaScript required:** no — core content is in the initial HTML.
- **Anti-bot measures:** none observed.
- **Pagination:** n/a.
- **Selectors (if stable):** `.featuredAlert`, `.homeWidget`, navigation lives under `#mainNav`. Stable across CivicPlus tenants.
- **Why no API:** News Flash and Calendar have RSS feeds (documented). The homepage itself is a composite page with no structured export of the widget layout.
- **Notes:** Duplicate content path — `fl-winterhaven.civicplus.com/…` serves the same pages under the vendor-native hostname. Prefer `www.mywinterhaven.com`.

#### Departments index

- **URL:** `https://www.mywinterhaven.com/101/Departments`
- **Data available:** List of all city departments with links to their subpages.
- **Fields extractable:** Department name, link path.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** Standard CivicPlus department-index layout.
- **Why no API:** Department tree is not exposed as JSON.
- **Notes:** Used as the crawl expansion point for building/planning/code-enforcement pages.

#### Building Permits & Licenses

- **URL:** `https://www.mywinterhaven.com/342/Building-Permits-Licenses`
- **Data available:** Static page with links to PDF applications, external permit platforms (Accela, eSuite, ProjectDox), contractor registration, impact fee guide.
- **Fields extractable:** Document links in `/DocumentCenter/View/{id}/{slug}` form; external portal URLs.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** generic CivicPlus content page.
- **Why no API:** Page is a curated landing with no structured export.
- **Notes:** The **primary hub** for discovering Winter Haven's permit stack. All three permit platforms (Accela, eSuite, ProjectDox) are linked here.

#### Building Permit & Inspection Utilization Reports

- **URL:** `https://www.mywinterhaven.com/169/Building-Permit-Inspection-Utilization-R`
- **Data available:** Periodic utilization reports, likely PDFs.
- **Fields extractable:** `unverified` — only external links observed in this pass; full content requires follow-up probe.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** generic.
- **Why no API:** PDF-only.
- **Notes:** ⚠️ GAP: enumerate the report archive on next pass — could be a leading indicator of permit volume for BI/PT.

#### Government / City Commission / Planning Commission hub pages

- **URLs:**
  - `https://www.mywinterhaven.com/27/Government`
  - `https://www.mywinterhaven.com/220/City-Commission`
  - `https://www.mywinterhaven.com/346/Planning-Commission`
- **Data available:** Commissioner biographies, meeting links, committees. Redirects for meeting materials point to AgendaCenter + Granicus.
- **Fields extractable:** Commissioner names + photos + district assignments; links to AgendaCenter / ViewPublisher.
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** n/a.
- **Selectors:** generic CivicPlus.
- **Why no API:** Commission roster is not exposed via JSON/RSS — only HTML.
- **Notes:** CR pipeline ignores these and hits Granicus directly.

#### AgendaCenter index + ArchiveCenter

- **URLs:**
  - `https://www.mywinterhaven.com/AgendaCenter`
  - `https://www.mywinterhaven.com/ArchiveCenter`
- **Data available:** HTML listing of agenda categories (CIDs 15 + 16) and agenda-file links. ArchiveCenter is the broader document archive.
- **Fields extractable:** Agenda keys `_{MMDDYYYY}-{id}` → resolve to PDFs at `/AgendaCenter/ViewFile/Agenda/_{…}`.
- **JavaScript required:** no for listing; agenda PDF fetch is direct GET.
- **Anti-bot measures:** none.
- **Pagination:** AgendaCenter search via `/AgendaCenter/Search/` (documented in APIs).
- **Selectors:** CivicPlus AgendaCenter standard DOM.
- **Why no API:** RSS feed (`ModID=65`) returned empty despite HTML showing records — treat as unreliable fallback only.
- **Notes:** Granicus ViewPublisher remains canonical for CR. AgendaCenter is documented for completeness.

#### DocumentCenter

- **URL:** `https://www.mywinterhaven.com/DocumentCenter`
- **Data available:** Hierarchical document archive with stable IDs. Individual documents: `https://www.mywinterhaven.com/DocumentCenter/View/{id}/{slug-or-blank}`.
- **Fields extractable:** Document ID, document slug, file type (usually PDF). Some `/DocumentCenter/View/{id}` paths returned 404 on HEAD but 200 on GET (likely anti-abuse HEAD rejection) — use GET.
- **JavaScript required:** no.
- **Anti-bot measures:** HEAD requests return 404 for some IDs; GET works.
- **Pagination:** unclear — root index is HTML.
- **Selectors:** CivicPlus DocumentCenter standard.
- **Why no API:** No JSON index of document metadata. IDs are sparse integers (749, 750, 755, 1580, 1581, 1800, 2691, 2814, 2904, …).
- **Notes:** The ID space is enumerable but large — probing would exceed the 2000-request cap on its own. Use the PDF links from the CivicPlus page graph rather than sweeping IDs.

#### Calendar (HTML)

- **URL:** `https://www.mywinterhaven.com/Calendar.aspx` (with optional `?CID=14`, etc.)
- **Data available:** Calendar UI for city events.
- **Fields extractable:** Prefer the Calendar RSS (`ModID=58`) for structured data.
- **JavaScript required:** minimal.
- **Anti-bot measures:** none.
- **Pagination:** month navigation.
- **Selectors:** CivicPlus calendar widget.
- **Why no API:** There **is** an API (Calendar RSS). Documented under APIs.
- **Notes:** Kept here because the HTML surface exposes event descriptions the RSS elides; listed per §4.2 exception ("HTML variant under Notes"). Actually — **removing** per §4.2 rule "never document same URL in both sections": the Calendar.aspx page differs from the RSSFeed.aspx URL, so this is a distinct page, not the same URL, and belongs under Scrape Targets as a secondary surface.

#### Bids / Jobs / FAQ / Directory / Blog

- **URLs:**
  - `https://www.mywinterhaven.com/bids.aspx`
  - `https://www.mywinterhaven.com/jobs.aspx`
  - `https://www.mywinterhaven.com/FAQ.aspx`
  - `https://www.mywinterhaven.com/directory.aspx` / `/directory`
  - `https://www.mywinterhaven.com/blog.aspx`
- **Data available:** Standard CivicPlus modules for bids/jobs/FAQ/staff directory/blog.
- **Fields extractable:** Standard per CivicPlus (title, date, description, attachments).
- **JavaScript required:** no.
- **Anti-bot measures:** none.
- **Pagination:** varies.
- **Selectors:** CivicPlus module-standard.
- **Why no API:** Jobs + Blog + News each have RSS feeds (documented). Bids / FAQ / Directory do not.
- **Notes:** Bids page title `Bid Postings • Winter Haven, FL • CivicEngage` confirms the CivicEngage product suffix.

### myinspections.mywinterhaven.com/eSuite.Permits/

#### Tyler New World eSuite — welcome + search pages

- **URL:** `https://myinspections.mywinterhaven.com/eSuite.Permits/WelcomePage.aspx` (also `Home.aspx`, `Search.aspx`, `PermitLookup.aspx`, `PermitInquiry.aspx`, `InspectionLookup.aspx`, `GenericSearch.aspx`, `CreateUser/Default.aspx`, `Faq.aspx`).
- **Data available:** Permit/inspection lookup (search by permit number, address, contractor).
- **Fields extractable:** Search result rows (permit #, address, type, status, issue date) — only after submitting a search. Unauth search attempts return a redirect to `Error.aspx?aspxerrorpath=…` — the platform is nominally "public" but the search requires a valid session + antiforgery/VIEWSTATE round-trip.
- **JavaScript required:** minimal for navigation; VIEWSTATE is server-posted.
- **Anti-bot measures:** VIEWSTATE/EVENTVALIDATION tokens; WalkMe widget injected (user guidance, not anti-bot); session cookies.
- **Pagination:** result-page pagination (unverified — not exercised).
- **Selectors:** ASP.NET WebForms control IDs under `ctl00$…$gvResults` pattern — need per-page inspection.
- **Why no API:** Tyler New World does not expose a public REST surface on this tenant. Community eSuite versions sometimes have SOAP endpoints; none discovered here.
- **Notes:** ⚠️ GAP: build a session-aware scraper or probe for hidden SOAP/JSON endpoints. The platform supports inspection scheduling + permit status lookup and is a near-complementary surface to Accela — if we can get data out of it, it may fill ACCELA-16's gap.

### eplans.mywinterhaven.com (Avolve ProjectDox)

#### ProjectDox login

- **URL:** `https://eplans.mywinterhaven.com/Portal/Login` (and `/Portal/Login/Index/Winter-Haven-FL`).
- **Data available:** Only the login form — all plan-review content is auth-gated.
- **Fields extractable:** none anonymously.
- **JavaScript required:** yes for full portal.
- **Anti-bot measures:** session cookies, served through `redirect.pizza` edge CDN.
- **Pagination:** n/a.
- **Selectors:** ProjectDox standard DOM (Portal/Login partials).
- **Why no API:** Avolve ProjectDox does not publish a public data surface.
- **Notes:** ⚠️ GAP: no practical anon-extractable data. Document the surface, skip extraction.

### events.mywinterhaven.com

#### Community events calendar (Yii2 platform, unknown vendor)

- **URL:** `https://events.mywinterhaven.com/winterhavenfl` (plus `/calendar`, `/map` subpaths).
- **Data available:** Community events (city + partner events). Separate from the CivicPlus Calendar RSS.
- **Fields extractable:** Event title, date, location, organizer, description, category — all in HTML.
- **JavaScript required:** partial — the listing is server-rendered but filter interactions use AJAX (⚠️ GAP: AJAX endpoints not enumerated in curl-only pass).
- **Anti-bot measures:** Cloudflare; CSRF cookie (`_frontendCSRF`); `session_` cookie.
- **Pagination:** `unverified` — not exercised.
- **Selectors:** Platform-specific; needs inspection.
- **Why no API:** None discoverable at common paths (`/api/events`, `/rss`, `/events.ics`, etc. all returned soft 200 "Page not found" HTML). The platform **likely** has an internal JSON API used by its own filter widgets — deferred to a real-browser pass.
- **Notes:** ⚠️ GAP: browser-based crawl to surface XHR endpoints. Vendor not yet identified (Yii2 framework visible via CSRF token shape; the asset path `/assets/bf724c2b/…` matches Yii2 asset-bundle fingerprints).

### library.municode.com/fl/winter_haven

#### Winter Haven Code of Ordinances

- **URL:** `https://library.municode.com/fl/winter_haven/codes/code_of_ordinances`
- **Data available:** Full municipal code (all chapters / sections) with deep-linked fragments of the form `…?nodeId={path_id}`.
- **Fields extractable:** Node metadata (title, path, children, text content, `IsUpdated`/`IsAmended`/`HasAmendedDescendant` flags per `_platforms.md`).
- **JavaScript required:** yes — the library is a JS SPA that fetches node content from `https://mcclibraryfunctions.azurewebsites.us/api` + `https://mcclibrary.blob.core.usgovcloudapi.net/codecontent/`.
- **Anti-bot measures:** Google reCAPTCHA v3, OIDC client-side integration.
- **Pagination:** tree-walk over `nodeId`.
- **Selectors:** n/a — consume the API once client ID is resolved.
- **Why no API:** The Municode API **does** exist (cataloged in `_platforms.md` with shape `api.municode.com/codes/{client_id}/nodes`) but the Winter Haven client ID was not resolvable from the SPA HTML in a curl-only pass — standard guesses (`16058`, `16057`, `14520`, etc.) returned 404.
- **Notes:** ⚠️ GAP: re-enumerate with a browser next run; capture the JSON request for `/api/codeContent/` or whatever variant Municode's US-gov-cloud variant uses (note the `.usgovcloudapi.net` blob endpoint — this tenant is on GovCloud, which may mean the API path differs from the commercial Municode documented in `_platforms.md`).

### cityofwinterhaven.column.us

#### Column legal notices search

- **URL:** `https://cityofwinterhaven.column.us/search`
- **Data available:** Public legal notices (hearings, ordinances, foreclosures).
- **Fields extractable:** Notice title, publication date, body text, referencing ordinance/case number.
- **JavaScript required:** `unverified` — not fully exercised.
- **Anti-bot measures:** `unverified`.
- **Pagination:** `unverified`.
- **Selectors:** Column platform-standard.
- **Why no API:** Not probed this pass.
- **Notes:** ⚠️ GAP: full Column mapping deferred. Relevant for CR (ordinance publication / public-hearing notices).

### procurement.opengov.com/portal/winterhavenfl

#### OpenGov Procurement

- **URL:** `https://procurement.opengov.com/portal/winterhavenfl`
- **Data available:** Open bids, solicitations (anon 403 in this run).
- **Fields extractable:** none anonymously observed.
- **JavaScript required:** yes (OpenGov is a SPA).
- **Anti-bot measures:** 403 on anon GET — likely IP-gated or requires OpenGov session.
- **Pagination:** n/a.
- **Selectors:** OpenGov standard.
- **Why no API:** OpenGov has `/api/v2/` documented in `_platforms.md`; not exercised here.
- **Notes:** ⚠️ GAP: retry with a `Referer` header from the CivicPlus page, or use the OpenGov public API directly.

### winter-haven-fl.civilspace.io

#### Civilspace engagement portal

- **URL:** `https://winter-haven-fl.civilspace.io/en`
- **Data available:** Community-engagement polls/forums.
- **Fields extractable:** `unverified`.
- **JavaScript required:** likely yes.
- **Anti-bot measures:** `unverified`.
- **Pagination:** `unverified`.
- **Selectors:** `unverified`.
- **Why no API:** Not probed.
- **Notes:** ⚠️ GAP: mostly out-of-scope for BI/PT/CR/CD2; low priority.

### seeclickfix.com/web_portal/SdLPekA3hqCyR5wYB2xDUDHd

#### SeeClickFix 311

- **URL:** `https://seeclickfix.com/web_portal/SdLPekA3hqCyR5wYB2xDUDHd/issues/map` + `/report/category`.
- **Data available:** Citizen-reported issues (code enforcement, potholes, etc.).
- **Fields extractable:** Issue type, location, status, description.
- **JavaScript required:** yes (map UI).
- **Anti-bot measures:** SeeClickFix public API exists; portal is a JS frontend.
- **Pagination:** `unverified`.
- **Selectors:** n/a — use the SeeClickFix API.
- **Why no API cataloged here:** SeeClickFix has a public REST API (`api.seeclickfix.com`) but it was not probed this pass. ⚠️ GAP: add on the next round if we care about enforcement-adjacent citizen reports.
- **Notes:** The embedded `SdLPekA3hqCyR5wYB2xDUDHd` portal ID is stable and is the identifier for the SeeClickFix API.

### www.egovlink.com/public_documents300/winterhaven

#### eGovLink legacy document archive

- **URL:** `https://www.egovlink.com/public_documents300/winterhaven/published_documents/Winter%20Haven/…`
- **Data available:** Historic Winter Haven public documents (observed: housing white paper, quiet-zone report).
- **Fields extractable:** Document files only; no index observed.
- **JavaScript required:** no for direct PDFs.
- **Anti-bot measures:** `unverified`.
- **Pagination:** `unverified`.
- **Selectors:** n/a.
- **Why no API:** eGovLink is a legacy platform CivicPlus acquired; no public API surface.
- **Notes:** Only referenced from Econ-Dev pages for archival documents. Low value.

---

## Coverage Notes

### robots.txt restrictions

The following city-site paths are disallowed for all user-agents and were **not** crawled:
- `/activedit`, `/admin`, `/common/admin/`, `/OJA`, `/Support`
- `/currenteventsview.asp(x)`, `/currentevents.aspx`
- `/search.asp(x)` (both case variants)

Baiduspider and Yandex are blanket-denied. Our crawler uses a distinct UA (`CountyData2-API-Mapper/1.0`) and respects `User-agent: *` rules only.

Full robots.txt: `evidence/winter-haven-fl-robots.txt`.

### Request budget

- **Total requests this run:** 100 (well under the 2000 cap).
- **Rate:** ~1 req/sec target, sustained.
- **HTTP errors observed:** only expected ones — `302` on `/CivicAlerts.aspx?CID=1` (category redirect), `403` on `winterhaven-fl.granicus.com/podcast.php` (Cloudflare challenge), `404` on some `DocumentCenter/View/{id}` HEADs (GET works), `404` on `/AgendaCenter/UpdateCategoryList` POST, `404` on guessed Municode client IDs.
- **No 429s.** No captcha challenges hit (Cloudflare passed everywhere except podcast.php).

Full request log: `evidence/_winter-haven-request-log.txt`.

### Cross-references

- **ACCELA-16 (TODO.md P1):** Winter Haven COWH Enforcement-module HTML probe. This map confirms:
  - Tenant hostname: `aca-prod.accela.com/COWH` (canonical mixed-case).
  - `?module=Enforcement` renders a generic "Welcome!" page with no populated tab ribbon, suggesting Enforcement is **not** anon-public on this tenant. Only `?module=Building` exposes tab content. A real-browser crawl is needed to confirm.
  - Sibling modules in the same state: `?module=Planning`, `?module=Licenses` also render the generic welcome page without tabs.
- **CR adapter already live:** `modules/commission/config/jurisdictions/FL/winter-haven-cc.yaml` (City Commission) + `winter-haven-pc.yaml` (Planning Commission), both platform `granicus_viewpublisher`, `view_id=1`, distinguished by `body_filter`. Not re-verified here per instructions.
- **PT adapter stub exists:** `modules/permits/scrapers/adapters/winter_haven.py` extends `AccelaCitizenAccessAdapter` with `agency_code=COWH`, `target_record_type=Building/Residential/New/NA`. The comment flags auth as blocking — this crawl confirms the **module landing** is public but doesn't disprove the auth claim on record search. Resolving anon search is part of ACCELA-16.

### Open gaps (⚠️ GAP markers summarized by section)

- **/RSSFeed.aspx (Agenda Creator):** ModID=65 feed empty despite HTML showing records. Re-check next run.
- **/RSSFeed.aspx (Calendar):** `calendarEvent:` namespace sub-elements not enumerated.
- **/AgendaCenter/Search/:** pagination cap + CID-to-body mapping (CID 15 vs 16) not confirmed.
- **Accela COWH:** anon record search on Building module; Enforcement/Planning/Licenses anon surface. Full ACCELA-16 probe needs browser.
- **Accela APO / GeneralProperty lookup:** landing only, results not exercised.
- **Tyler New World eSuite:** session-gated search not probed; possible hidden SOAP/JSON endpoints deferred.
- **events.mywinterhaven.com:** internal AJAX/JSON endpoints deferred to browser pass.
- **Municode Library (Winter Haven):** client ID not resolved; tenant is on Municode's GovCloud (`mcclibrary.blob.core.usgovcloudapi.net`) — API path may differ from the commercial Municode entry in `_platforms.md`.
- **cityofwinterhaven.column.us:** full Column mapping deferred.
- **OpenGov Procurement:** 403 anon — retry with referer / OpenGov API.
- **Civilspace, Corebook, Jotform, Citibot:** deferred (out-of-scope for BI/PT/CR/CD2).
- **Building-Permit Reports page (`/169`):** enumerate report archive on next pass.
- **SeeClickFix API:** not probed; public REST API exists (`api.seeclickfix.com`).
- **Polk County GIS / ArcGIS:** no ArcGIS endpoints on the city footprint. County GIS belongs in the Polk County map, not this file.

### `_platforms.md` deltas

Platforms observed here that should be added to `docs/api-maps/_platforms.md` on the next housekeeping pass:
- **Tyler New World eSuite (Permits)** — hostname pattern customer-domain with `/eSuite.Permits/`; signatures: `NewWorld.eSuite.Common.Web.Shared` CSS namespace, Walkme user-guidance widget, VIEWSTATE. No existing adapter.
- **Avolve ProjectDox** — customer-domain `/Portal/Login/Index/{Client-Name}`; title `ProjectDox Login`. No existing adapter.
- **Column (legal notices)** — hostname `*.column.us`.
- **Civilspace** — hostname `*.civilspace.io`.
- **Citibot (chat widget)** — `webchat-ui.citibot.net` script.
- **Yii2 community-events platform at events.mywinterhaven.com** — vendor unidentified; signatures: Yii2 asset-bundle paths (`/assets/{hex}/…`), `_frontendCSRF` cookie.

Adding these is deferred to a follow-up; this map's job is to document the Winter Haven footprint, not maintain the registry.
