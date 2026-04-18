# Polk County, FL — API Map

> Last surveyed: 2026-04-17. Seed: `https://aca-prod.accela.com/POLKCO/Default.aspx` (Permit Tracker — Accela Citizen Access). One-file scope: Polk County government + its unincorporated digital footprint. The five east-Polk cities that we actively track (Davenport, Winter Haven, Haines City, Dundee, Lake Hamilton) each have their own map under `docs/api-maps/{city}-fl.md` — cross-referenced from Coverage Notes, not re-mapped here.
>
> Crawl conducted in mixed mode. WordPress REST, ArcGIS REST, and Legistar OData were enumerated as structured APIs (JSON); ASP.NET portals on `aca-prod.accela.com/POLKCO` and `apps.polkcountyclerk.net/browserviewor/` and `pro.polkcountyclerk.net/PRO` were sampled for platform/surface identification but their deep search flows remain VIEWSTATE-driven and would require a browser session for full detail-page probing. See the archived per-platform deep dives (`_archived/polk-county-{accela,arcgis,iworq,legistar,improvement-report}.md`) for field-level inventories that this unified file cross-references but does not reproduce line-for-line.
>
> Six subsystems. Total request count this run: ~56 (well under the 300-400 budget — shallow-per-subsystem strategy held). No 429s, no captcha challenges.

## Summary

- **Jurisdiction:** Polk County, Florida. County BCC + unincorporated Polk. The incorporated municipalities within Polk (17 cities/towns) are outside this file's scope; the five we actively track (Davenport, Dundee, Haines City, Lake Hamilton, Winter Haven) are mapped in sibling files.
- **Six-platform stack (NEW to the Polk map on this run — previously fragmented across 4 archived files):**
  1. **County CMS:** `www.polkfl.gov` — WordPress 6.8.5 + Yoast SEO + ACF + FacetWP + WP Engine host. Rebrand from the old `polk-county.net` apex (301 redirect in place + `Sitemap:` directive still points at the old host but 301s back to the new one; harmless stale string in `robots.txt`). Full `/wp-json/` REST surface; 4 custom post types (`bid-form`, `cemetery`, `notice`, `park`).
  2. **Clerk of Court CMS:** `www.polkclerkfl.gov` — CivicPlus CivicEngage (classic numeric-ID URL pattern, e.g. `/297/Court-Records`). Rebrand from `polkcountyclerk.net` (301 redirect). Outbound records search splits across two vendor portals (see (5) / (6)).
  3. **GIS Enterprise portal:** `gis.polk-county.net` — ArcGIS Enterprise 11.5 (portal version 2025.1). 11 root `/server/rest/services/` services + 5 folders (`PCU` auth-gated, `PNR`, `Printer`, `Test`, `Utilities`). **Richer than the archived deep-dive recorded** — the archived map covered only `Map_Property_Appraiser/FeatureServer/1`; 10 other map/feature services are anonymous-public including `Polk_Development_Tracker_Map` (18 layers), `Map_Development_Overlays` (8 overlay districts), `Map_Flood_and_Drainage` (12 FEMA layers), `Map_Street_and_Addresses` (6), `Map_Surveyors_Info`, `Map_Utilities_Service_Area`, `Commissioners_Redistrict_MIL`, `Mosquito_Control_MIL`, `PNR/PNR_DataViewer` (6 parks/environmental layers).
  4. **Permit portal (seed):** `aca-prod.accela.com/POLKCO/` — Accela Citizen Access, tenant `POLKCO`. Confirmed modules visible from the landing's public tab ribbon: **Building, LandDev, Enforcement**, plus public lookup surfaces **APO/Property** (5 modes: address / parcel / owner / record / licensed pro) and **GeneralProperty/Licensee**. A **"Develop Polk" curated portal** (Land Use, Commercial, Residential sub-portals) is linked from Default.aspx and surfaces as a guided-intake UI over the same underlying modules. Code Enforcement exposes 4 record types anonymously (Complaint, Lien, Search Request, Sign Offense) — **correction to the archived `polk-county-accela.md` wording** which listed only Complaint + Lien Search Request. `apis.accela.com/v4/…` remains blocked for anonymous extraction per `accela-rest-probe-findings.md`.
  5. **Commission / CR:** `polkcountyfl.legistar.com` + shared OData API at `webapi.legistar.com/v1/polkcountyfl/`. 12 bodies; PDFs hosted on `polkcountyfl.legistar1.com`. Discovery on this run: **`EventItemAccelaRecordId` is a first-class field on Legistar event items** — giving a direct Legistar↔Accela join key (previously not flagged in archived map). Matter titles like `"LDLVAR-2025-78 - 2787 Recker HWY - Withdrawn"` carry Accela Land Dev record IDs in human-readable form.
  6. **Clerk records surfaces (NEW platform fingerprints, registered in `_platforms.md` this run):**
     - **Official Records (deed/mortgage/lien):** `apps.polkcountyclerk.net/browserviewor/` — NewVision Systems Corporation (© 2018). Public multi-form search (party name / document type / date range / property ID / board) without login; no captcha on landing.
     - **Civil / Court Records:** `pro.polkcountyclerk.net/PRO` — Tyler Odyssey PRO v1.2.4.0. Public Access acknowledgment gate (no captcha observed). Criminal traffic records deep-link to a sibling path at the old `polkcountyclerk.net/299` which still resolves.
- **iWorq (secondary permit/asset):** ⚠️ **No county-level iWorq tenant exists.** The archived `_archived/polk-county-iworq.md` actually documents the three east-Polk *city* tenants (Davenport / Haines City / Lake Hamilton), which are now maintained as per-city map files. Those three cities are the only place iWorq lives in Polk. Cross-ref note in Coverage Notes.
- **CD2 / clerk-records adapter — GAP confirmed.** Grep across `modules/` returns zero hits for `polkclerkfl.gov`, `polkcountyclerk.net`, `browserviewor`, `pro.polkcountyclerk.net`, or NewVision. The clerk's Official Records portal is currently unmapped by any adapter. The PT pipeline also does not consume Clerk records. The Marion BrowserView memory's hybrid-captcha pattern would apply to NewVision once characterized.
- **Stale BOA YAML flagged, not modified.** `modules/commission/config/jurisdictions/FL/polk-county-boa.yaml` (`platform: manual`) is orphaned per the "Skip BOA/ZBA" feedback memory. Do not convert it to Legistar (LEGISTAR-01 in the archived improvement report is overridden by that memory); leave the file in place for historical traceability, but it should not drive new scraping.
- **Cross-reference to Polk cities (sibling maps):** `davenport-fl.md`, `dundee-fl.md`, `haines-city-fl.md`, `lake-hamilton-fl.md`, `winter-haven-fl.md`. The 12 other incorporated Polk municipalities (Auburndale, Bartow, Eagle Lake, Eaton Park, Fort Meade, Frostproof, Highland Park, Hillcrest Heights, Lake Alfred, Lake Wales, Lakeland, Mulberry, Polk City) are not yet mapped — deferred.

## Platform Fingerprint

| Host | Platform | Fingerprint |
|---|---|---|
| `www.polkfl.gov` | **WordPress + Yoast SEO** (WP Engine hosted) | `<meta generator>` = `https://wordpress.org/?v=6.8.5`; `/wp-json/` returns 11 REST namespaces including `wpe/cache-plugin/v1`, `wp-rocket/v1`, `yoast/v1`, `facetwp/v1`; `<?xml-stylesheet href="…/wordpress-seo/css/main-sitemap.xsl">` on the sitemap index; ACF fields surface in page responses. No TEC / Tribe Events (`/wp-json/tribe/events/v1/events` returns 404). Events and meetings live as `/events/{slug}/` and `/meetings/{slug}/` permalinks; the `notice` CPT is the closest REST-exposed analogue but was empty at crawl time. |
| `www.polkclerkfl.gov` | **CivicPlus CivicEngage** | `<title>…CivicEngage</title>` not observed but CMS footer says "Government Websites by CivicPlus®"; numeric-ID URL pattern (`/297/Court-Records`); classic `/RSSFeed.aspx?ModID={1,51,53,58,63,76}` shape; `/rss.aspx` HTML index lists 6 ModIDs; `robots.txt` matches the standard CivicPlus shape (Baidu + Yandex blanket-denied, `/activedit`, `/admin`, `/common/admin/`, `/currenteventsview.{asp,aspx}`, `/search.{asp,aspx}`, `/Map.{asp,aspx}`, `/RSS.aspx` all disallowed). |
| `gis.polk-county.net` | **ArcGIS Enterprise 11.5 (portal 2025.1)** | `/portal/sharing/rest?f=json` returns `currentVersion: "2025.1"`, `enterpriseVersion: "11.5.0"`, `enterpriseBuild: "56755"`; `/server/rest/services?f=json` returns `currentVersion: 11.5`; 11 root services + 5 folders. Already in `_platforms.md` under **ArcGIS REST**. |
| `aca-prod.accela.com/POLKCO` | **Accela Citizen Access** | ASP.NET WebForms with `__VIEWSTATE`, `__doPostBack`, `ctl00$…` control IDs; Cloudflare edge (`_cfuvid` cookie); `ApplicationGatewayAffinity` cookies. Tenant code `POLKCO`. Already in `_platforms.md`. REST v4 at `apis.accela.com` returns 404 / 403 for anonymous — `accela-rest-probe-findings.md` governs. |
| `polkcountyfl.legistar.com` + `webapi.legistar.com/v1/polkcountyfl/` | **Legistar (Granicus)** | ASPX portal at `polkcountyfl.legistar.com`; JSON OData v3 at `webapi.legistar.com`; PDFs on `polkcountyfl.legistar1.com`. Already in `_platforms.md`. |
| `apps.polkcountyclerk.net/browserviewor/` | **NewVision Systems (Clerk Official Records)** (NEW to registry this run) | `© 2018 NewVision Systems Corporation` footer; ASP.NET WebForms shell; landing URL segment `/browserviewor/` (Browser View — Official Records). Public search forms (party name / document type / date range / property ID / board-commission) coexist with a login section. No captcha observed. Now registered in `_platforms.md`. |
| `pro.polkcountyclerk.net/PRO` | **Tyler Odyssey PRO (Civil / Court)** (NEW to registry this run) | `PRO Release Version 1.2.4.0` + Tyler branding; `PublicAccess` acknowledgment gate (click-through, no captcha). Distinct from Tyler MSS / EnerGov / Eagle / Munis. Now registered in `_platforms.md`. |
| `inspections.polk-county.net` | **Accela Inspection Tracker (session-gated)** | 403 to anonymous GET; requires session cookies established via the ACA portal. Recorded but not probed deeper. |
| `library.municode.com/fl/polk_county` | **Municode Library** | Already cataloged in `_platforms.md`. SPA — curl-only pass could not resolve the Polk tenant `client_id`; ⚠️ GAP. |
| `polkcountyfl.legistar1.com` | Legistar CDN / agenda-PDF storage | `{EventId}_A_{Body}_{YY-MM-DD}_Meeting_Agenda.pdf` naming. Edge host, not a distinct platform. |

---

## APIs

### /robots.txt (all hostnames)

#### robots.txt

- **URL:** (one per hostname — see Evidence files)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots Exclusion Protocol rules (plain text). Per §4.2, classified as API because the format is machine-readable and documented.
- **Response schema:** standard robots.txt format (user-agent blocks + allow/disallow lines + optional Sitemap directive).
- **Observed parameters:** none
- **Probed parameters:** none (single static document per hostname)
- **Pagination:** `none`
- **Rate limits observed:** none (single request per host)
- **Data freshness:** CMS/tenant-managed; stable.
- **Discovered via:** Standard `/robots.txt` probe.
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/robots.txt'
  curl 'https://www.polkclerkfl.gov/robots.txt'
  curl 'https://gis.polk-county.net/robots.txt'       # 404 — ArcGIS Enterprise omits
  curl 'https://aca-prod.accela.com/robots.txt'       # 404 — ACA omits
  curl 'https://polkcountyfl.legistar.com/robots.txt' # 404 — Legistar omits
  curl 'https://webapi.legistar.com/robots.txt'       # 404 — OData API omits
  ```
- **Evidence file:** `evidence/polk-county-fl-polkfl-gov-robots.txt`, `evidence/polk-county-fl-polkclerkfl-gov-robots.txt`, `evidence/polk-county-fl-gis-robots.txt`, `evidence/polk-county-fl-accela-robots.txt`, `evidence/polk-county-fl-legistar-robots.txt`
- **Notes:** See Coverage Notes for the operational-risk read per §3.2. The polkfl.gov Yoast block explicitly allows ClaudeBot, GPTBot, PerplexityBot, etc., so mapping-pass UAs are not hostile. The polkclerkfl.gov shape is a standard CivicPlus restriction set (Baiduspider + Yandex blanket-denied; `/admin`, `/search*`, `/map*`, `/RSS.aspx` disallowed for all UAs). `gis.polk-county.net`, ACA, and Legistar serve no robots.txt — operational risk is governed by rate-limiting / 429 response rather than convention.

### Subsystem 1 — County CMS (`www.polkfl.gov`, WordPress)

#### /sitemap_index.xml

- **URL:** `https://www.polkfl.gov/sitemap_index.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Yoast SEO sitemap index — 8 child sitemaps (post, page, meetings, meetings2, bid-form, park, events, news).
- **Response schema:**
  ```xml
  <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
      <loc>url</loc>
      <lastmod>iso8601</lastmod>
    </sitemap>
    …
  </sitemapindex>
  ```
- **Observed parameters:** none
- **Probed parameters:** `https://www.polk-county.net/sitemap_index.xml` — 301 to this URL. `/wp-sitemap.xml` also 200s at the same path (WP core sitemap is superseded by Yoast's).
- **Pagination:** index of 8 child sitemaps; each is ≤ ~500 URLs.
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** child `<lastmod>` values span 2023-03 → 2026-04 depending on module.
- **Discovered via:** `robots.txt` Sitemap directive (with stale `polk-county.net` host that 301s).
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/sitemap_index.xml'
  ```
- **Evidence file:** `evidence/polk-county-fl-sitemap-index.xml` (not captured on this run — XML returned inline in the Wave-1 probe; re-capture on next pass)
- **Notes:** `/meetings-sitemap.xml` (500+ entries) and `/events-sitemap.xml` (487 entries) are the most BI/CR-useful child sitemaps. `/bid-form-sitemap.xml` indexes the RFP/Bid CPT for procurement. Stale `polk-county.net/sitemap_index.xml` in robots.txt — operationally irrelevant because it 301s back to `polkfl.gov`.

#### /wp-json/ (WordPress REST discovery)

- **URL:** `https://www.polkfl.gov/wp-json/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** WordPress REST API site-descriptor JSON — namespaces, authentication capabilities, site name/description, timezone, gmt_offset.
- **Response schema:**
  ```
  {
    "name": "string",
    "description": "string",
    "url": "string",
    "home": "string",
    "gmt_offset": "int",
    "timezone_string": "string",
    "namespaces": ["string"],
    "authentication": { … },
    "routes": { … },
    "_links": { … }
  }
  ```
- **Observed parameters:** none on the root endpoint (sub-routes take their own).
- **Probed parameters:** n/a — descriptor endpoint.
- **Pagination:** `none`
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** real-time (reflects current plugin activation).
- **Discovered via:** Standard WP REST probe (per `_platforms.md` WordPress REST row).
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-root.json` (not captured this run — re-capture on next pass)
- **Notes:** Observed namespaces: `wp/v2`, `wpe/cache-plugin/v1`, `wpe_sign_on_plugin/v1`, `redirection/v1`, `yoast/v1`, `filebird/v1`, `filebird/public/v1`, `weglot/v1`, `wp-rocket/v1`, `wp-pwmwdb-api/v1`, `facetwp/v1`. The `wp-pwmwdb-api/v1` is unusual — likely a custom address-DB plugin; its surface was not probed (⚠️ GAP). `facetwp/v1` implies there's a filtered-search experience somewhere on the site.

#### /wp-json/wp/v2/types

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/types`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full post-type catalog. Custom post types on Polk: `bid-form`, `cemetery`, `notice`, `park`. Standard types (`post`, `page`, `attachment`, `nav_menu_item`, etc.) also present.
- **Response schema:**
  ```
  {
    "<type_key>": {
      "name": "string",
      "slug": "string",
      "hierarchical": "bool",
      "taxonomies": ["string"],
      "rest_base": "string",
      "rest_namespace": "string",
      "icon": "string",
      "_links": { … }
    }
  }
  ```
- **Observed parameters:** none
- **Probed parameters:** n/a
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Standard WP REST probe.
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/types'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-types.json`
- **Notes:** The `notice` CPT advertises the `meeting-type` taxonomy (40+ committee names observed via `/wp-json/wp/v2/meeting-type`) and was presumably intended to replace the 500+ `/meetings/{slug}/` static permalinks, but `/wp-json/wp/v2/notice?per_page=2` currently returns `[]` — the CPT is provisioned but empty. ⚠️ GAP: re-probe after a future content push to confirm whether meetings migrate into the REST surface. For now, the meeting agenda/minute PDFs are pushed to the CivicPlus Legistar portal, not surfaced via the CMS REST.

#### /wp-json/wp/v2/pages

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/pages`
- **Method:** `GET`
- **Auth:** `none` (published content)
- **Data returned:** Collection of all public Pages (department pages, service pages, landing pages).
- **Response schema:**
  ```
  [
    {
      "id": "int",
      "date": "iso8601",
      "date_gmt": "iso8601",
      "slug": "string",
      "status": "string",
      "type": "string",
      "link": "url",
      "title": {"rendered": "string"},
      "content": {"rendered": "string", "protected": "bool"},
      "excerpt": {"rendered": "string"},
      "featured_media": "int",
      "parent": "int",
      "menu_order": "int",
      "template": "string",
      "acf": { … }
    }
  ]
  ```
- **Observed parameters:**
  - `per_page` (int, optional) — 1-100, default 10.
  - `page` (int, optional)
  - `search` (string, optional)
  - `order` (string, optional) — `asc|desc`
  - `orderby` (string, optional) — `date|modified|id|title|slug|menu_order|relevance|author`
  - `parent` (int, optional) — filter to children of a specific page
  - `status` (string, optional) — publish is the default for anon.
- **Probed parameters:** `per_page=2` confirmed; higher values not probed (WP core caps at 100).
- **Pagination:** `page` + `per_page`; response headers `X-WP-Total` and `X-WP-TotalPages` expected (not visible in the fetched summary — `unverified` in this pass).
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** real-time
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/pages?per_page=2'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-pages.json` (not captured — re-capture on next pass)
- **Notes:** `acf` field surfaces on both pages and CPTs — Advanced Custom Fields is active. Page `template` field distinguishes default vs `page-flex.php` layouts.

#### /wp-json/wp/v2/posts

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/posts`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Blog/news posts. Mix of department news, public service announcements, events recaps.
- **Response schema:** WP-core `posts` schema: `id, date, slug, status, type, link, title, content, excerpt, author, featured_media, categories, tags, acf`.
- **Observed parameters:** Same shape as `/pages` plus `categories`, `tags`, `author`, `sticky`.
- **Probed parameters:** `per_page=2` confirmed.
- **Pagination:** `page` + `per_page`. `X-WP-Total` header expected.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/posts?per_page=2'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-posts.json` (not captured — re-capture on next pass)
- **Notes:** RSS feed at `/feed/` is an RSS 2.0 equivalent with ~50-item trailing window (see next entry).

#### /feed/ (WordPress RSS 2.0)

- **URL:** `https://www.polkfl.gov/feed/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard WordPress RSS 2.0 channel — ~50-item trailing window of the latest posts.
- **Response schema:**
  ```xml
  <rss version="2.0" xmlns:content="…" xmlns:dc="…" xmlns:atom="…" xmlns:sy="…" xmlns:slash="…">
    <channel>
      <title>string</title>
      <atom:link href="url" rel="self" type="application/rss+xml"/>
      <link>url</link>
      <description>string</description>
      <lastBuildDate>rfc822-date</lastBuildDate>
      <language>string</language>
      <sy:updatePeriod>hourly</sy:updatePeriod>
      <sy:updateFrequency>int</sy:updateFrequency>
      <generator>https://wordpress.org/?v=6.8.5</generator>
      <image>…</image>
      <item>
        <title>string</title>
        <link>url</link>
        <dc:creator>string</dc:creator>
        <pubDate>rfc822-date</pubDate>
        <category>string</category>
        <guid isPermaLink="false">url</guid>
        <description>string</description>
        <content:encoded>cdata-html</content:encoded>
        …
      </item>
      …
    </channel>
  </rss>
  ```
- **Observed parameters:** none (trailing 50 items returned).
- **Probed parameters:** `?paged=2` — `unverified` on this run. Category feeds at `/category/{slug}/feed/` follow the WP convention.
- **Pagination:** `paged=N` query parameter on pageable feeds; trailing window otherwise.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** WP convention; `<generator>` tag in RSS confirmed WP 6.8.5.
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/feed/'
  ```
- **Evidence file:** `evidence/polk-county-fl-feed.xml` (not captured — re-capture on next pass)
- **Notes:** Redundant with `/wp-json/wp/v2/posts` but cheaper to parse for humans; kept as documentation completeness.

#### /wp-json/wp/v2/bid-form

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/bid-form`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Bid/RFP registry. Most recent entries: `RFP 26-228` (published 2026-04-17), `Bid 26-231` (2026-04-16). IDs are WP post-IDs; slug is the bid reference number.
- **Response schema:** WP CPT shape + `bid-form-type` taxonomy.
- **Observed parameters:** Standard WP collection params (`per_page`, `page`, `order`, `orderby`, `search`, `slug`, `status`).
- **Probed parameters:** `per_page=2` confirmed.
- **Pagination:** `page` + `per_page`.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/bid-form?per_page=2'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-bid-form.json`
- **Notes:** `content` is empty on all observed entries — the bid number is the title and the detail content lives behind a PDF link on the rendered page (`featured_media=4019` — same placeholder for every bid). This CPT is a registry / index, not a data surface; use the `link` field to resolve the HTML page, then fetch the PDF attachment from the page body. The `bid-form-type` taxonomy was empty on the sample.

#### /wp-json/wp/v2/park

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/park`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Public parks, preserves, boat ramps — each with `cities`, `park_amenities`, `park_type` taxonomies.
- **Response schema:** WP CPT shape. Observed additional denormalized fields `city_names[]` and `amenity_names[]` alongside the raw term-ID arrays — the site has a custom REST extension flattening taxonomy IDs into strings.
- **Observed parameters:** Standard WP collection params.
- **Probed parameters:** `per_page=2` confirmed.
- **Pagination:** `page` + `per_page`.
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/park?per_page=2'
  ```
- **Evidence file:** `evidence/polk-county-fl-wp-json-park.json`
- **Notes:** Lower analytical value for BI/PT/CR/CD2 but cataloged. The `cities` taxonomy values (e.g., "Kissimmee", "Poinciana") cross county lines — Polk's parks CMS tracks neighboring-county park inventory too, not just Polk cities.

#### /wp-json/wp/v2/notice

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/notice`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Notices CPT with `city` + `meeting-type` taxonomies. **Empty at crawl time** — returned `[]`.
- **Response schema:** WP CPT shape (unverified against live data since sample was empty).
- **Observed parameters:** Standard WP collection params.
- **Probed parameters:** `per_page=2` → empty array.
- **Pagination:** `page` + `per_page`.
- **Rate limits observed:** none
- **Data freshness:** empty / not populated.
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/notice?per_page=2'
  ```
- **Evidence file:** not captured (empty response).
- **Notes:** ⚠️ GAP: `meeting-type` taxonomy has 40+ terms including `Board of County Commissioners Board Meeting`, `Contractor Licensing Board`, `Citizens Healthcare Oversight Committee`, and `Affordable Housing Advisory Committee` — implying the CPT is *intended* to carry structured meeting notices, but publishing has not started. Watch on re-surveys; a populated `notice` endpoint would be a cleaner CR signal than scraping `/meetings/{slug}/` HTML permalinks.

#### /wp-json/wp/v2/cemetery

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/cemetery`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Cemetery records CPT (no taxonomy). Not probed live on this run.
- **Response schema:** `unverified` — WP CPT shape expected.
- **Observed parameters:** Standard WP collection params.
- **Probed parameters:** none on this run.
- **Pagination:** `page` + `per_page`.
- **Rate limits observed:** `unverified`
- **Data freshness:** `unverified`
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/cemetery?per_page=2'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** Low analytical value for BI/PT/CR/CD2. Documented for completeness.

#### /wp-json/wp/v2/media

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/media`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Attachment records — PDF uploads (ADAs, ordinances, reports, bid packets). Each entry has `source_url`, `mime_type`, `title`, `media_details`.
- **Response schema:** WP media shape.
- **Observed parameters:** Standard collection params + `mime_type`, `media_type`, `parent`.
- **Probed parameters:** `per_page=1` confirmed (observed entry: ADA-Repeal-of-Burn-Ban PDF from 2026-04-17).
- **Pagination:** `page` + `per_page`.
- **Rate limits observed:** none
- **Data freshness:** real-time (newest PDF attached moments before the probe — "ADA-Repeal-of-Burn-Ban-25-02-04-17-2026.pdf").
- **Discovered via:** `/wp-json/wp/v2/types`
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/media?per_page=1'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** Useful for BI/CD2 — ordinance text, code amendments, and board advisories arrive here before they arrive on the Clerk side. `media_type=application` + `mime_type=application/pdf` filter would isolate regulatory-document uploads from banner images.

#### /wp-json/wp/v2/meeting-type (taxonomy)

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/meeting-type`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Taxonomy terms for the `notice` CPT. 40+ committee / board names observed (BCC, CFDC, CRAC, CLASAC, Contractor Licensing Board, etc.). All `count` values were `0` at crawl time (matches the empty `notice` collection).
- **Response schema:**
  ```
  [
    {
      "id": "int",
      "count": "int",
      "description": "string",
      "link": "url",
      "name": "string",
      "slug": "string",
      "taxonomy": "meeting-type",
      "parent": "int"
    }
  ]
  ```
- **Observed parameters:** `per_page`, `page`, `order`, `orderby`, `hide_empty`, `parent`, `search`, `slug`.
- **Probed parameters:** unqualified GET returned the default (10 terms).
- **Pagination:** `page` + `per_page`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `types` response listed the `meeting-type` taxonomy on the `notice` CPT.
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/meeting-type?per_page=100&hide_empty=false'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** Good index of the committee/board landscape — this is a cleaner enumeration than scraping Legistar `/Bodies` because it includes committees that don't meet publicly on Legistar.

#### /wp-json/wp/v2/city (taxonomy)

- **URL:** `https://www.polkfl.gov/wp-json/wp/v2/city`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Taxonomy terms — cities and unincorporated communities within and adjacent to Polk. Observed terms include Alturas, Auburndale, Babson Park, Bartow, Davenport, Dundee, Eagle Lake, Eaton Park, Eloise, plus neighboring-county entries (Kissimmee, Clermont). Sample `count` values range 0–9, indicating which cities have associated content.
- **Response schema:** Standard WP taxonomy shape (`id`, `name`, `slug`, `count`, `description`, `link`, `taxonomy`, `parent`).
- **Observed parameters:** Standard taxonomy params.
- **Probed parameters:** unqualified GET.
- **Pagination:** `page` + `per_page`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `types` response
- **curl:**
  ```bash
  curl 'https://www.polkfl.gov/wp-json/wp/v2/city?per_page=100&hide_empty=false'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** This is the authoritative county-government-side enumeration of Polk municipalities. Useful for BI/CR to validate that our 5 tracked cities line up with the official taxonomy.

### Subsystem 2 — Clerk of Court (`www.polkclerkfl.gov`, CivicPlus)

#### /RSSFeed.aspx (CivicPlus RSS)

- **URL:** `https://www.polkclerkfl.gov/RSSFeed.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RSS 2.0 feed of CivicPlus module content. Observed ModIDs on Polk Clerk: `1` (News Flash), `51` (Blog), `53` (Photo Gallery), `58` (Calendar), `63` (Alert Center), `76` (Pages).
- **Response schema:** Standard CivicPlus RSS 2.0 channel shape (matches the pattern in `_platforms.md`).
- **Observed parameters:**
  - `ModID` (int, required) — values observed: `1`, `51`, `53`, `58`, `63`, `76`.
  - `CID` (string, optional) — category filter.
- **Probed parameters:**
  - `ModID=1&CID=All-newsflash.xml` — returned a valid-but-empty RSS channel. The Clerk currently does not publish News Flash items.
- **Pagination:** `none` (trailing window per module).
- **Rate limits observed:** none
- **Data freshness:** real-time (subject to empty channels as above).
- **Discovered via:** `/rss.aspx` HTML index lists the 6 ModIDs.
- **curl:**
  ```bash
  curl 'https://www.polkclerkfl.gov/RSSFeed.aspx?ModID=1&CID=All-newsflash.xml'
  curl 'https://www.polkclerkfl.gov/RSSFeed.aspx?ModID=63'   # Alert Center
  curl 'https://www.polkclerkfl.gov/RSSFeed.aspx?ModID=58'   # Calendar
  ```
- **Evidence file:** _(News Flash feed was empty on fetch — no evidence capture; ⚠️ GAP: capture Alert Center, Calendar, and Blog on next pass when they have content)_
- **Notes:** The Clerk's CivicEngage tenant looks identical in shape to the Winter Haven tenant but with a Clerk-specific ModID set (Polk Clerk has `76 Pages` and `63 Alert Center` that Winter Haven lacks; Winter Haven has `65 Agenda Creator` and `66 Jobs` that the Clerk lacks).

#### /sitemap.xml (CivicPlus)

- **URL:** `https://www.polkclerkfl.gov/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Sitemap — 327 URLs, all using the CivicPlus numeric-ID URL pattern (`/{id}/{slug}`).
- **Response schema:** Standard `<urlset>` with `<url><loc/><lastmod/></url>` entries.
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none` — single flat document.
- **Rate limits observed:** none
- **Data freshness:** CMS-managed.
- **Discovered via:** `robots.txt` Sitemap directive.
- **curl:**
  ```bash
  curl 'https://www.polkclerkfl.gov/sitemap.xml'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP; re-capture on next pass)_
- **Notes:** Key URL groupings: Services, Records (Court/Criminal-Traffic/Official/Public-Records-Searches), Court Operations, Family Law Services, Property Services (Foreclosure Sales, Tax Deeds, eRecording, Real Estate Resources), Vital Services, Legal Processes, Administrative.

### Subsystem 3 — GIS Enterprise (`gis.polk-county.net`, ArcGIS 11.5)

#### /portal/sharing/rest?f=json

- **URL:** `https://gis.polk-county.net/portal/sharing/rest`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** ArcGIS Portal descriptor — currentVersion, enterpriseVersion, enterpriseBuild.
- **Response schema:**
  ```
  {
    "currentVersion": "string",
    "fullVersion": "string",
    "enterpriseVersion": "string",
    "enterpriseBuild": "string"
  }
  ```
- **Observed parameters:**
  - `f` (string, required for JSON) — `json`
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** versioned (2025.1 observed)
- **Discovered via:** Standard ArcGIS Enterprise probe.
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/portal/sharing/rest?f=json'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP; re-capture on next pass)_
- **Notes:** Version diff between portal (`2025.1`) and services (`11.5`) is normal — portal is on the ArcGIS Online calendar-versioning track, services on the ArcGIS Server classic versioning.

#### /server/rest/services?f=json

- **URL:** `https://gis.polk-county.net/server/rest/services`
- **Method:** `GET`
- **Auth:** `none` (except PCU folder — returns HTTP 499 "Authentication required")
- **Data returned:** Services root listing — 11 root services + 5 folders.
- **Response schema:**
  ```
  {
    "currentVersion": "float",
    "folders": ["string"],
    "services": [
      {"name": "string", "type": "MapServer|FeatureServer|GPServer|ImageServer|…"}
    ]
  }
  ```
- **Observed parameters:**
  - `f=json` (required for JSON)
- **Probed parameters:** Per-folder probes listed below.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Standard ArcGIS probe.
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services?f=json'
  ```
- **Evidence file:** `evidence/polk-county-fl-arcgis-services-root.json`
- **Notes:** 11 root services — `Base_Map_Reference` (MapServer), `Commissioners_Redistrict_MIL`, `Map_Development_Overlays`, `Map_Flood_and_Drainage`, `Map_Property_Appraiser` (FeatureServer + MapServer — same name, two bindings), `Map_Street_and_Addresses`, `Map_Surveyors_Info`, `Map_Utilities_Service_Area`, `Mosquito_Control_MIL`, `Polk_Development_Tracker_Map`. Folders: `PCU` (auth-gated — HTTP 499), `PNR`, `Printer`, `Test`, `Utilities`.

#### /server/rest/services/Map_Property_Appraiser/FeatureServer

- **URL:** `https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** FeatureServer descriptor — 6 layers (Parcels, Parcel Labels, Subdivision, Lots, Parcel Dimension, Parcel Misc).
- **Response schema:** standard ArcGIS FeatureServer metadata.
- **Observed parameters:** `f=json`
- **Probed parameters:** n/a (descriptor)
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time (layer mtimes — not surfaced in the descriptor; re-probe per-layer for `editingInfo`).
- **Discovered via:** Services root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer?f=json'
  ```
- **Evidence file:** `evidence/polk-county-fl-arcgis-property-appraiser-featureserver.json` (not separately captured — summary in `_request-log.txt`)
- **Notes:** Deep dive in `_archived/polk-county-arcgis.md` §1-3. Confirmed consistent with this run.

#### /server/rest/services/Map_Property_Appraiser/FeatureServer/1 (Parcels)

- **URL:** `https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Layer descriptor — **56 fields** (archived map counted 55; the additional field is `PROP_ADRNO_SFX` which is in the archived inventory but may have been re-added or renamed). `maxRecordCount: 2000`, `geometryType: esriGeometryPolygon`, `spatialReference.wkid: 102100` (Web Mercator).
- **Response schema:** standard ArcGIS layer metadata.
- **Observed parameters:** `f=json`
- **Probed parameters:** n/a (descriptor only; `?query` substring is a separate endpoint).
- **Pagination:** `none` (descriptor is single-document).
- **Rate limits observed:** none
- **Data freshness:** PA-sourced; refreshed by Polk Property Appraiser pipeline.
- **Discovered via:** FeatureServer root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1?f=json'
  ```
- **Evidence file:** _(not separately captured this run — archived `_archived/polk-county-arcgis.md` §3 has the full field table)_
- **Notes:** See `_archived/polk-county-arcgis.md` for the full 56-field inventory (PARCELID, NAME, PROP_ADRSTR, TOT_ACREAGE, ASSESSVAL, DEED_DT, etc.). Production adapter is `seed_bi_county_config.py` Polk row + generic `GISQueryEngine`. Query endpoint at `/1/query` supports `where`, `outFields`, `returnGeometry`, `outSR`, `resultOffset`, `resultRecordCount`, `f` — see archive for full probed-parameter table.

#### /server/rest/services/Polk_Development_Tracker_Map/MapServer

- **URL:** `https://gis.polk-county.net/server/rest/services/Polk_Development_Tracker_Map/MapServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **NEW to the Polk map this run.** 18 feature layers covering infrastructure + planning context: fire/ambulance stations, hospitals, schools, bus stops, GFTS routes, elementary/middle/high school zones, complete streets network, law enforcement, `Landuse_4corners` (the Four Corners boundary between Polk/Osceola/Lake/Orange), municipality polygons, `Polk_Unincorporated`, 2017 census blocks, **`TPO_2040_Forecast_Final`** (transportation planning forecast), regions, county boundary.
- **Response schema:** standard ArcGIS MapServer metadata.
- **Observed parameters:** `f=json`
- **Probed parameters:** Individual layers not yet queried — descriptor-level only.
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** `unverified` per-layer; `TPO_2040_Forecast_Final` implies ~8-year horizon.
- **Discovered via:** Services root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Polk_Development_Tracker_Map/MapServer?f=json'
  ```
- **Evidence file:** `evidence/polk-county-fl-arcgis-development-tracker.json`
- **Notes:** Layer 12 `Landuse_4corners` is immediately relevant to the east-Polk / Four Corners mapping work — worth a per-layer field probe next run. Layer 16 `TPO_2040_Forecast_Final` pairs with the Legistar TPO bodies (246/251/252). ⚠️ GAP: enumerate per-layer fields.

#### /server/rest/services/Map_Development_Overlays/MapServer

- **URL:** `https://gis.polk-county.net/server/rest/services/Map_Development_Overlays/MapServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **NEW.** 8 overlay districts: Joint Planning Areas, Mineral Resource-Protection Districts, Redevelopment Districts, SR 17 Ridge Scenic Highway, Transit Corridors and Centers Overlay, Wellfield-Protection Districts, Green Swamp Protection Area, Special Protection Areas (SPAs).
- **Response schema:** standard.
- **Observed parameters:** `f=json`
- **Probed parameters:** per-layer not probed
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** `unverified`
- **Discovered via:** Services root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Map_Development_Overlays/MapServer?f=json'
  ```
- **Evidence file:** `evidence/polk-county-fl-arcgis-development-overlays.json`
- **Notes:** Direct input to land-development decisions. Joint Planning Areas intersect with city-county annexation scope; Wellfield & Green Swamp constrain building permit approvals. ⚠️ GAP: per-layer field enumeration.

#### /server/rest/services/Map_Flood_and_Drainage/MapServer

- **URL:** `https://gis.polk-county.net/server/rest/services/Map_Flood_and_Drainage/MapServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **NEW.** 12 flood/drainage layers: Base Flood Elevations (polyline), FEMA Floodways, FEMA Flood Zones 2016, 2012, 2000, 1983 (four temporal snapshots — excellent for change detection), FEMA Panels, Wetlands NWI, OLD Maintenance Units, Drainage Basins, Soils, DrainageAssetsManagement.
- **Response schema:** standard.
- **Observed parameters:** `f=json`
- **Probed parameters:** per-layer not probed
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** per-layer (2016 is the latest FEMA snapshot published).
- **Discovered via:** Services root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Map_Flood_and_Drainage/MapServer?f=json'
  ```
- **Evidence file:** _(summarized in request log; JSON not separately captured — ⚠️ GAP: capture on next run)_
- **Notes:** The temporal FEMA stack (2016 / 2012 / 2000 / 1983) is unusually rich — most counties only publish the current panel. Could support a "flood risk historical expansion" analysis.

#### /server/rest/services/Map_Street_and_Addresses/MapServer

- **URL:** `https://gis.polk-county.net/server/rest/services/Map_Street_and_Addresses/MapServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** 6 layers: Addresses (point, visible at 1:2500), interstate/major-road symbols, Major Roads, SAP Proposed Roads, Local Roads. No parcel or subdivision layers (those are on Map_Property_Appraiser).
- **Response schema:** standard.
- **Observed parameters:** `f=json`
- **Probed parameters:** per-layer not probed
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** `unverified`
- **Discovered via:** Services root
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/Map_Street_and_Addresses/MapServer?f=json'
  ```
- **Evidence file:** _(summarized in request log; ⚠️ GAP)_
- **Notes:** The `Addresses` point layer is attractive as a reverse-geocoding fallback when Census TIGER misses rural roads (see `accela-rest-probe-findings.md` observation that Polk's rural-road ACCELA-11 coverage gap comes from TIGER, not our wiring).

#### /server/rest/services/PNR/PNR_DataViewer/FeatureServer

- **URL:** `https://gis.polk-county.net/server/rest/services/PNR/PNR_DataViewer/FeatureServer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Parks and Natural Resources inventory — 6 layers: Park Locations (point), Centers (point), Boat Ramps (point), Trails (polyline), Park Boundaries (polygon), Environmental Lands (polygon).
- **Response schema:** standard.
- **Observed parameters:** `f=json`
- **Probed parameters:** per-layer not probed
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** `unverified`
- **Discovered via:** Services root (PNR folder)
- **curl:**
  ```bash
  curl 'https://gis.polk-county.net/server/rest/services/PNR/PNR_DataViewer/FeatureServer?f=json'
  ```
- **Evidence file:** _(summarized in request log; ⚠️ GAP)_
- **Notes:** This is the GIS-side authoritative counterpart to the CMS `park` CPT — worth a cross-check between `/wp-json/wp/v2/park` names and `Park Locations.NAME`.

### Subsystem 4 — Permit portal / Accela (`aca-prod.accela.com/POLKCO`)

#### /POLKCO/Cap/CapHome.aspx?module={Building|LandDev|Enforcement}

- **URL:** `https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx`
- **Method:** `GET` (landing) / `POST` (search via ASP.NET postback)
- **Auth:** `none` for the landing ribbon; anonymous search works for Building / LandDev / Enforcement modules (confirmed).
- **Data returned:** HTML/ASPX with `__VIEWSTATE` form that drives search postbacks. General Search exposes fields documented in `_archived/polk-county-accela.md` §2. Classified here as API because the enclosing framework (Accela CapHome) is a machine-readable contract — callers must replay VIEWSTATE + fire `__doPostBack(ctl00$PlaceHolderMain$btnNewSearch, …)`.
- **Response schema:** HTML/ASPX — see `_archived/polk-county-accela.md` §2 for grid structure (`ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList`), detail-page fields, and §3 for record-type hierarchy.
- **Observed parameters:**
  - `module` (string, required) — **values verified on this run: `Building`, `LandDev`, `Enforcement`.** The archived map documented all three but with slightly different wording ("Land Dev" module); URL slug is specifically `LandDev` (not `Planning`; `?module=PLANNING` returned an error page).
  - `TabName` (string, optional) — mirror of `module` for tab labeling.
  - Record type is a form-level dropdown `ddlGSPermitType`, not a query parameter.
- **Probed parameters:**
  - `module=Building` → 200, populated General Search with all field IDs per archive.
  - `module=LandDev` → 200, populated General Search with 27+ record types in `ddlGSPermitType` (Access Solely By Easement, Admin-Administrative Action, Admin-Administrative Determination, Admin-Administrative Interpretation, Admin-Non-Conforming Use, BOA-Special Exception, BOA-Temporary Special Exception, BOA-Variance, BOCC-Community Development District, BOCC-Conditional Use, BOCC-CPA Large, BOCC-CPA Small, BOCC-Developer's Agreement, BOCC-Development of Regional Impact, BOCC-Infrastructure Agreement, BOCC-LDC District Change, BOCC-LDC Text Change, BOCC-Planned Development, BOCC-Waiver, DRC-Action, …).
  - `module=Enforcement` → 200, populated General Search with 4 record types: Complaint, Lien, Search Request, Sign Offense. **Correction to archive:** the archived `polk-county-accela.md` §3 listed only `Complaint` + `Lien Search Request`; live recon finds 4 separate types.
  - `module=PLANNING` → 200 with "An error has occurred. We are experiencing technical difficulties." — slug is wrong.
  - `module=Licenses` → not probed this run (would likely 200; archive didn't list Licenses as anon-public).
- **Pagination:** `__doPostBack` grid pagination; binary date-range split via the PT adapter when `total >= search_result_cap=100`. See archive §2.
- **Rate limits observed:** none at 1 req/sec. Cloudflare edge fronts the tenant; sustained load would likely challenge.
- **Data freshness:** real-time
- **Discovered via:** Default.aspx tab metadata (`Search Records` tab lists 3 module deep-links).
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Building&TabName=Building'
  curl 'https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=LandDev&TabName=LandDev'
  curl 'https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Enforcement&TabName=Enforcement'
  ```
- **Evidence file:** _(landings returned HTML; not re-captured this run since `_archived/polk-county-accela.md` already has comprehensive fixture HTML. ⚠️ GAP: re-capture Enforcement + LandDev landing HTML to pin current DOM + VIEWSTATE shape — archive only has Building.)_
- **Notes:** For detail-page fields (CapDetail.aspx?capID1/capID2/capID3/agencyCode=POLKCO) and the full record-type taxonomy, see `_archived/polk-county-accela.md` §2-4. The Angular UI signature `ng-app="appAca"` that exists on the Winter Haven COWH tenant is present on POLKCO too.

#### /POLKCO/Default.aspx (tab metadata)

- **URL:** `https://aca-prod.accela.com/POLKCO/Default.aspx`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML with an embedded JS-encoded array-of-records enumerating the tenant's tabs, modules, and associated URLs. Same shape as Winter Haven COWH (`[['Links',[[['Active',…],['Label',…],['URL',…]]]]]`).
- **Response schema:** HTML with inline JS array. Tab records carry `Active, Label, Key, Title, URL, Module, Order`.
- **Observed parameters:** none
- **Probed parameters:** none (Default.aspx is a landing)
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time (tenant configuration)
- **Discovered via:** canonical Accela landing.
- **curl:**
  ```bash
  curl -L 'https://aca-prod.accela.com/POLKCO/Default.aspx'
  ```
- **Evidence file:** _(not captured — archive has the structural pattern; ⚠️ GAP: capture on next pass to log the current POLKCO tab set verbatim)_
- **Notes:** Tab groups observed on POLKCO: `Submit an Application`, `Develop Polk` (Land Use / Commercial / Residential sub-portals — curated guided-intake over the same Building / LandDev modules), `Property Search` → APOLookup, `Search Records` (Building, LandDev, Enforcement deep-links), `Pay Fees`, `Building Inspections` (Inspection Tracker → `inspections.polk-county.net/`, Schedule an Inspection), `Code Enforcement Complaint/Lien Search`, `Help`, `My Records`, `My Account`.

#### /POLKCO/APO/APOLookup.aspx (Property Lookup)

- **URL:** `https://aca-prod.accela.com/POLKCO/APO/APOLookup.aspx?TabName=Home`
- **Method:** `GET` (landing) / `POST` (VIEWSTATE postback search)
- **Auth:** `none`
- **Data returned:** 5-mode property lookup — Address / Parcel Information / Owner / Record Information / Licensed Professional. Standard Accela APO module structure. Publicly accessible.
- **Response schema:** HTML/ASPX with `__VIEWSTATE` postback.
- **Observed parameters:** `TabName=Home`; `isLicensee=Y` observed on the sibling GeneralProperty/PropertyLookUp link.
- **Probed parameters:** landing only (search results not exercised without a browser).
- **Pagination:** postback-driven
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Default.aspx tab metadata → "Property Search" tab.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/POLKCO/APO/APOLookup.aspx?TabName=Home'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** Potential parcel-resolver alternative to the ArcGIS `Map_Property_Appraiser` FeatureServer when we need Accela-side linkage (APO results are joined to Accela records via `capID`). Unconfirmed whether APO exposes owner mailing address — the 5-mode form suggests it does.

#### /POLKCO/GeneralProperty/PropertyLookUp.aspx (Licensee Search)

- **URL:** `https://aca-prod.accela.com/POLKCO/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y`
- **Method:** `GET` (landing) / `POST` (search)
- **Auth:** `none`
- **Data returned:** Licensee search (contractors, trades). Fields: License Type (50+ values), License Number, License State, Provider Name, Provider Number, Business Type (Contractor, Electrical, Mechanical, Plumbing), Personal name fields, Business Name, Address block, Phone/Fax, Contractor's License # and Business Name.
- **Response schema:** HTML/ASPX with postback.
- **Observed parameters:** `isLicensee=Y`
- **Probed parameters:** landing only
- **Pagination:** postback-driven
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** Default.aspx tab metadata → "Search for a Licensee" child link.
- **curl:**
  ```bash
  curl 'https://aca-prod.accela.com/POLKCO/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y'
  ```
- **Evidence file:** _(not captured — ⚠️ GAP)_
- **Notes:** Contractor-licensing data surface — complements the ACCELA-04 structured-contact capture that the PT adapter now does from CapDetail pages.

### Subsystem 5 — Commission / CR (`polkcountyfl.legistar.com`, `webapi.legistar.com/v1/polkcountyfl`)

#### /v1/polkcountyfl/Bodies

- **URL:** `https://webapi.legistar.com/v1/polkcountyfl/Bodies`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** 12 legislative bodies registered on the Polk tenant. Field inventory: `BodyId, BodyGuid, BodyLastModifiedUtc, BodyRowVersion, BodyName, BodyTypeId, BodyTypeName, BodyMeetFlag, BodyActiveFlag, BodyDescription, BodyContactNameId, BodyContactFullName, BodyContactEmail, BodyUsedControlFlag, BodyNumberOfMembers, BodyNumberOfOfficeHolders`.
- **Response schema:** Standard Legistar OData v3 body object.
- **Observed parameters:** OData standard (`$filter`, `$orderby`, `$top`, `$skip`, `$select`).
- **Probed parameters:** unqualified GET returns all 12 bodies.
- **Pagination:** `$top` + `$skip` (not needed for 12 rows).
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** real-time
- **Discovered via:** OData endpoint convention.
- **curl:**
  ```bash
  curl 'https://webapi.legistar.com/v1/polkcountyfl/Bodies'
  ```
- **Evidence file:** `evidence/polk-county-fl-legistar-bodies.json`
- **Notes:** 12 bodies matches archived count. BodyIds as documented in `_archived/polk-county-legistar.md` §1 — tracked by current CR YAMLs: 138 BCC (bcc.yaml), 228 Planning Commission (pz.yaml). Untracked: 139 PRWC, 140 LUHO, 239/240/241 BCC variants, 246/251/252 TPO, 254 Budget Office Documents, 258 Citizen's Healthcare Oversight. The `polk-county-boa.yaml` is `platform: manual` and should stay that way (Skip BOA/ZBA memory).

#### /v1/polkcountyfl/Events

- **URL:** `https://webapi.legistar.com/v1/polkcountyfl/Events`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Meeting events for all bodies. 21 fields per event: `EventId, EventGuid, EventLastModifiedUtc, EventRowVersion, EventBodyId, EventBodyName, EventDate, EventTime, EventVideoStatus, EventAgendaStatusId, EventAgendaStatusName, EventMinutesStatusId, EventMinutesStatusName, EventLocation, EventAgendaFile, EventMinutesFile, EventAgendaLastPublishedUTC, EventMinutesLastPublishedUTC, EventComment, EventVideoPath, EventMedia, EventInSiteURL, EventItems`.
- **Response schema:** Standard Legistar OData v3 event object.
- **Observed parameters:** OData standard.
- **Probed parameters:** `$top=2&$orderby=EventDate+desc` returned the 2 most recent events (LUHO 2026-04-23, BCC 2026-04-21). `EventAgendaFile` populated for both (Final status). `EventInSiteURL` present.
- **Pagination:** `$top` + `$skip` (production adapter uses `$top=100`, `$skip+=100`, 0.5s delay).
- **Rate limits observed:** none documented; 0.5s delay is precautionary.
- **Data freshness:** real-time (`EventAgendaLastPublishedUTC` is the freshness field).
- **Discovered via:** OData endpoint convention.
- **curl:**
  ```bash
  curl 'https://webapi.legistar.com/v1/polkcountyfl/Events?$top=2&$orderby=EventDate+desc'
  ```
- **Evidence file:** `evidence/polk-county-fl-legistar-events.json`
- **Notes:** Agenda PDFs live on `polkcountyfl.legistar1.com` (separate edge host). `EventInSiteURL` is a permalink to the portal MeetingDetail page. Production scraper `modules/commission/scrapers/legistar.py` already handles this surface; expansion opportunities are in `_archived/polk-county-improvement-report.md` §LEGISTAR-02..05.

#### /v1/polkcountyfl/Events/{id}/EventItems

- **URL:** `https://webapi.legistar.com/v1/polkcountyfl/Events/{EventId}/EventItems`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Agenda items for a specific event. **34 fields per item** including motions, mover/seconder, consent flag, roll-call flag, tally, linked Matter, and **`EventItemAccelaRecordId`** — a first-class Legistar→Accela cross-reference field.
- **Response schema:**
  ```
  [
    {
      "EventItemId": "int",
      "EventItemGuid": "string",
      "EventItemLastModifiedUtc": "iso8601",
      "EventItemRowVersion": "string",
      "EventItemEventId": "int",
      "EventItemAgendaSequence": "int",
      "EventItemMinutesSequence": "int",
      "EventItemAgendaNumber": "string",
      "EventItemVideo": "string|null",
      "EventItemVideoIndex": "int|null",
      "EventItemVersion": "string",
      "EventItemAgendaNote": "string",
      "EventItemMinutesNote": "string",
      "EventItemActionId": "int|null",
      "EventItemActionName": "string|null",
      "EventItemActionText": "string|null",
      "EventItemPassedFlag": "int|null",
      "EventItemPassedFlagName": "string|null",
      "EventItemRollCallFlag": "int",
      "EventItemFlagExtra": "int",
      "EventItemTitle": "string",
      "EventItemTally": "string|null",
      "EventItemAccelaRecordId": "string|null",
      "EventItemConsent": "int",
      "EventItemMoverId": "int|null",
      "EventItemMover": "string|null",
      "EventItemSeconderId": "int|null",
      "EventItemSeconder": "string|null",
      "EventItemMatterId": "int|null",
      "EventItemMatterGuid": "string|null",
      "EventItemMatterFile": "string|null",
      "EventItemMatterName": "string|null",
      "EventItemMatterType": "string|null",
      "EventItemMatterStatus": "string|null",
      "EventItemMatterAttachments": "array"
    }
  ]
  ```
- **Observed parameters:** `$top`, `$skip`, `$orderby`, `$filter`
- **Probed parameters:** `$top=3` against EventId 1816 (upcoming BCC meeting) — most fields null on the sample because the agenda is not finalized.
- **Pagination:** `$top` + `$skip`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** `_archived/polk-county-legistar.md` §5
- **curl:**
  ```bash
  curl 'https://webapi.legistar.com/v1/polkcountyfl/Events/1816/EventItems?$top=3'
  ```
- **Evidence file:** `evidence/polk-county-fl-legistar-eventitems.json`
- **Notes:** `EventItemAccelaRecordId` is the key discovery — it means a Legistar BCC agenda item for a Planned Development rezoning can be directly joined back to the underlying Accela LandDev record without heuristic text matching. Production scraper already has `_fetch_event_items` behind the `fetch_event_items` config flag (b16df13) — see improvement report LEGISTAR-03.

#### /v1/polkcountyfl/Matters

- **URL:** `https://webapi.legistar.com/v1/polkcountyfl/Matters`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Legislative matters (ordinances, resolutions, variances, hearings). Sample latest: MatterFile `26-0662` with MatterTitle `"LDLVAR-2025-78 - 2787 Recker HWY - Withdrawn"` — carries the Accela LandDev record ID (`LDLVAR-2025-78`) in human-readable form.
- **Response schema:** Standard Legistar OData v3 matter object (MatterId, MatterGuid, MatterFile, MatterName, MatterTitle, MatterTypeName, MatterStatusName, MatterBodyName, MatterIntroDate, MatterAgendaDate, MatterPassedDate, MatterEnactmentDate, MatterRequesterId, MatterRequester, MatterNotes, MatterAttachments, MatterText1..5).
- **Observed parameters:** OData standard.
- **Probed parameters:** `$top=2&$orderby=MatterId+desc` returned latest two (both Land Use Hearing Officer matters).
- **Pagination:** `$top` + `$skip`
- **Rate limits observed:** none
- **Data freshness:** real-time
- **Discovered via:** OData endpoint convention.
- **curl:**
  ```bash
  curl 'https://webapi.legistar.com/v1/polkcountyfl/Matters?$top=2&$orderby=MatterId+desc'
  ```
- **Evidence file:** `evidence/polk-county-fl-legistar-matters.json`
- **Notes:** MatterFile values like `26-0662` and MatterTitle substrings like `"LDLVAR-2025-78"` are the paired keys to fuse Legistar matter history with the Accela LandDev record lifecycle. Production scraper does not currently consume Matters (LEGISTAR-06 in improvement report).

### Subsystem 6 — Clerk records portals (`apps.polkcountyclerk.net`, `pro.polkcountyclerk.net`)

Both are HTML/ASPX portals. The API/scraping distinction here is subtle — VIEWSTATE-driven search forms are documented under APIs (they're the canonical programmatic entry point for the platform, even though the response is HTML). Pure HTML browsing pages (category indexes, detail views) are documented under Scrape Targets.

#### /browserviewor/ (NewVision Systems Clerk Official Records — landing)

- **URL:** `https://apps.polkcountyclerk.net/browserviewor/`
- **Method:** `GET` (landing) / `POST` (search postback)
- **Auth:** `none` (public search)
- **Data returned:** HTML/ASPX landing with multiple search forms and an optional login block. Search modes: party name, document type, date range, property identification, board/commission.
- **Response schema:** HTML; VIEWSTATE-driven forms.
- **Observed parameters:** none observed on the landing URL itself — form params not exercised without a browser session.
- **Probed parameters:**
  - `https://apps.polkcountyclerk.net/browserviewor/Search.aspx` → 404 (search is not a separate URL; it's a postback on the root).
- **Pagination:** `unverified` — not exercised.
- **Rate limits observed:** none at 1 req/sec on the landing probe.
- **Data freshness:** real-time (official records are filed continuously).
- **Discovered via:** Linked from `www.polkclerkfl.gov/184/Official-Records`.
- **curl:**
  ```bash
  curl 'https://apps.polkcountyclerk.net/browserviewor/'
  ```
- **Evidence file:** _(not captured — deferred; ⚠️ GAP: capture landing HTML on next pass)_
- **Notes:** ⚠️ GAP: API shape / XHR endpoints not yet characterized. The "Marion BrowserView" hybrid-captcha pattern in the user memory refers to a Tyler BrowserView deployment — this is a *different* vendor (NewVision Systems, © 2018) despite the similar URL segment. Production adapter doesn't exist for this host. CD2 (LDC/ordinance) doesn't directly consume Official Records, but recording histories / deed chains intersect BI enrichment. Hybrid-captcha pattern from memory would apply once we try to automate it — no captcha observed on the landing, but postback-depth behavior is unknown.

#### /PRO (Tyler Odyssey PRO Civil / Court — landing)

- **URL:** `https://pro.polkcountyclerk.net/PRO/`
- **Method:** `GET`
- **Auth:** `none` (Public Access click-through)
- **Data returned:** HTML landing with three entry buttons: Public Access, Register, Login. Tyler PRO version string `"PRO Release Version 1.2.4.0"` in footer.
- **Response schema:** HTML/ASPX. Deep flows not enumerated without a browser.
- **Observed parameters:** none on the root.
- **Probed parameters:** none (root only).
- **Pagination:** `unverified`
- **Rate limits observed:** none on landing.
- **Data freshness:** real-time
- **Discovered via:** Linked from `www.polkclerkfl.gov/297/Court-Records`.
- **curl:**
  ```bash
  curl 'https://pro.polkcountyclerk.net/PRO/'
  ```
- **Evidence file:** _(not captured — deferred; ⚠️ GAP: capture the Public Access flow on next pass with a browser)_
- **Notes:** Tyler Odyssey PRO is **new to `_platforms.md` this run**. Criminal traffic records deep-link to `www.polkcountyclerk.net/299` which still resolves (old apex pre-rebrand). Case records accessible include docket, documents, court dates, fines, party information. Not relevant to the current BI/PT/CR/CD2 adapters, but foundational for any future civil-case / foreclosure enrichment.

---

## Scrape Targets

### Subsystem 1 — polkfl.gov CMS (HTML routes not covered by /wp-json/)

#### /meetings/{slug}/ (meeting permalinks)

- **URL:** `https://www.polkfl.gov/meetings/{slug}/` (observed slugs include `board-of-county-commissioners-board-meeting`, `development-review-committee-8`, etc., from `/meetings-sitemap.xml`).
- **Data available:** Static meeting pages — title, date, committee, location, agenda-PDF link.
- **Fields extractable:** Meeting title, date, associated `meeting-type` taxonomy term, any attached agenda PDF URL.
- **JavaScript required:** no — standard WordPress permalinks render server-side.
- **Anti-bot measures:** none.
- **Pagination:** n/a (individual pages). The `/meetings-sitemap.xml` is the index.
- **Selectors (if stable):** Generic WP `.entry-content`, `.wp-block-post-title`. `unverified` specifically for this site's theme.
- **Why no API:** `notice` CPT exists and advertises the `meeting-type` taxonomy but returns empty at `/wp-json/wp/v2/notice`. Until populated, the static `/meetings/{slug}/` permalinks are the only data surface.
- **Notes:** Some slugs from `/meetings-sitemap.xml` 404 on direct access (observed: `board-of-county-commissioners-board-meeting/` → 404). Suggests the sitemap carries stale URLs. Prefer the Legistar surface for BCC/P&Z/LUHO; this CMS surface is useful only for the non-Legistar committees (Contractor Licensing Board, CLASAC, CFDC, etc.).

#### /events/{slug}/ (event permalinks)

- **URL:** `https://www.polkfl.gov/events/{slug}/`
- **Data available:** 487 events (per `/events-sitemap.xml`) — community events, public hearings, holidays. Title, date, venue, description.
- **Fields extractable:** Standard event metadata.
- **JavaScript required:** `unverified` — likely no (WP static permalinks), but not tested on this run.
- **Anti-bot measures:** none.
- **Pagination:** n/a (individual pages).
- **Selectors:** `unverified` theme-specific.
- **Why no API:** `/wp-json/tribe/events/v1/events` returned 404 — Tribe Events plugin is not present on this tenant. Events are a custom permalink layout without a matching REST endpoint.
- **Notes:** ⚠️ GAP: probe whether FacetWP's `/wp-json/facetwp/v1/…` namespace exposes an events-query shape. That would be the cleanest structured replacement.

#### Department landings under /services/ and hub pages

- **URL:** e.g. `https://www.polkfl.gov/services/utilities/direct-potable-reuse/` (observed in `/wp-json/wp/v2/pages` response).
- **Data available:** Department service descriptions, contact info, PDFs.
- **Fields extractable:** Title, content body, featured media (PDF icon for downloadable packets), ACF fields.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** follow page tree via `parent` field in `/wp-json/wp/v2/pages`.
- **Selectors:** `unverified`
- **Why no API cataloged here:** `/wp-json/wp/v2/pages` already provides the full page tree — these HTML permalinks are the rendered views of the same data. Listed only because some embedded assets (inline PDFs, form widgets) aren't surfaced in the REST `content.rendered` reliably.
- **Notes:** Prefer the REST endpoint.

### Subsystem 2 — polkclerkfl.gov CivicEngage HTML pages

#### Records / Court Operations / Property Services hub pages

- **URL:** e.g. `/184/Official-Records`, `/297/Court-Records`, `/299/Criminal-Traffic-Records`, `/213/Foreclosure-Sales`, `/210/eRecording`, `/262/County-Commission-Records`, `/187/Public-Records-Searches`.
- **Data available:** Hub pages with outbound links to vendor portals (NewVision BrowserView, Tyler PRO, etc.) and PDFs of schedules / policies / fee structures.
- **Fields extractable:** Outbound portal URL, any inline document links.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** Standard CivicEngage `.widget-content`.
- **Why no API:** CivicEngage content pages are CMS-rendered HTML; RSS feeds (`/RSSFeed.aspx?ModID={1,51,58,63}`) cover news/blog/calendar but not the static hub pages.
- **Notes:** Primary discovery index for Clerk-side vendor portals. `/213/Foreclosure-Sales` specifically should carry the foreclosure-sales-portal vendor URL — deferred on this run (the crawl summary didn't surface the outbound link cleanly — ⚠️ GAP: re-probe for foreclosure-sales vendor, likely Realauction / GovEase / MyFloridaCountyClerk).

### Subsystem 3 — GIS `/portal/home` (ArcGIS Enterprise UI)

- **URL:** `https://gis.polk-county.net/portal/home/`
- **Data available:** Web mapping apps (Experience Builder, Dashboards), gallery of featured items, department maps.
- **Fields extractable:** Item IDs on the portal (backed by `/portal/sharing/rest/content/items/{id}`).
- **JavaScript required:** yes (SPA).
- **Anti-bot measures:** `unverified`
- **Pagination:** portal-driven.
- **Selectors:** n/a — consume the REST API.
- **Why no API cataloged separately:** `/portal/sharing/rest/content/items` / `/portal/sharing/rest/search` endpoints provide the structured surface; not exercised on this run (⚠️ GAP — all featured-app enumeration deferred).
- **Notes:** Would surface apps like a "Polk County Property Viewer" that the production BI adapter doesn't use but which humans navigate.

### Subsystem 4 — ACA portals (HTML detail pages)

#### /POLKCO/Cap/CapDetail.aspx (permit / land-dev / enforcement detail)

- **URL:** `https://aca-prod.accela.com/POLKCO/Cap/CapDetail.aspx?Module={Module}&TabName={Tab}&capID1=...&capID2=...&capID3=...&agencyCode=POLKCO`
- **Data available:** Record detail — Work Location, Applicant, Licensed Professional, Owner, Project Description, Additional Information (ASI custom forms), Parcel Information, Inspections (hash-anchored `<div id="tab-inspections">` — empty for anon per `_archived/polk-county-improvement-report.md` ACCELA-05/06), Attachments, Fees, Processing Status, Related Records.
- **Fields extractable:** See `_archived/polk-county-accela.md` §4 for the full inventory and current PT-adapter coverage (ACCELA-03 owner + ACCELA-04 contact regexes shipped; ACCELA-04a subcontractor list shipped; ACCELA-12 ASI capture P2 open).
- **JavaScript required:** no for the initial detail HTML; yes for the `__doPostBack` inspection refresh (empty for anon regardless).
- **Anti-bot measures:** Cloudflare edge; no captcha observed at ~1 req/sec.
- **Pagination:** n/a per record; search-grid pagination covered under APIs.
- **Selectors:** Flattened text + regex approach documented in `_archived/polk-county-accela.md` and `_archived/polk-county-improvement-report.md`.
- **Why no API:** `apis.accela.com/v4/…` is blocked for anonymous extraction per `accela-rest-probe-findings.md`. HTML is the only path.
- **Notes:** Already the primary production PT path. No change this run.

### Subsystem 5 — Legistar portal (HTML for human navigation)

#### /MeetingDetail.aspx, /LegislationDetail.aspx, /DepartmentDetail.aspx, /Calendar.aspx

- **URL:** `https://polkcountyfl.legistar.com/MeetingDetail.aspx?LEGID={id}&GID={gid}&G={guid}` et al.
- **Data available:** Same data as the OData endpoints render, but HTML-formatted for human browsing.
- **Fields extractable:** Same as OData.
- **JavaScript required:** partial (Calendar.aspx drives calendar via JS; MeetingDetail renders server-side).
- **Anti-bot measures:** none observed.
- **Pagination:** Calendar has year/month navigation.
- **Selectors:** Standard Legistar portal DOM.
- **Why no API:** OData at `webapi.legistar.com/v1/polkcountyfl` provides the same data structured — always prefer OData.
- **Notes:** Documented for completeness. `EventInSiteURL` from the events endpoint links here.

### Subsystem 6 — Clerk records portals (non-search HTML)

Search landings for both NewVision BrowserView and Tyler PRO are documented above under APIs (they're the canonical programmatic entry point even though the response is HTML). The broader category / help / disclaimer pages beneath are pure Scrape Targets — not re-enumerated until a deeper browser-based probe.

---

## External Platforms (brief)

One-liners for platforms referenced by this county footprint but documented more extensively elsewhere or out of current scope:

- **Municode Library (`library.municode.com/fl/polk_county`):** Municipal code of ordinances. SPA — curl-only could not resolve the Polk `client_id` for the `api.municode.com/codes/{client_id}/nodes` REST surface. Already cataloged in `_platforms.md`; ⚠️ GAP: browser-based probe to capture `client_id` on next pass. Relevant for CD2 (LDC text).
- **apis.accela.com v4 REST:** Cataloged as blocked for anonymous extraction (`accela-rest-probe-findings.md`). POLKCO returns `anonymous_user_unavailable` just like every other tested FL agency.
- **inspections.polk-county.net:** Accela inspection-tracker spinoff; 403 to anonymous GET. Session-gated from the ACA portal.
- **polkcountyfl.legistar1.com:** Legistar CDN for agenda/minute PDFs. Stable URL pattern per `EventAgendaFile` responses.
- **iWorq (`portal.iworq.net`):** No Polk County tenant; only the three east-Polk cities (Davenport, Haines City, Lake Hamilton) — see their per-city map files.
- **Tyler New World eSuite / ProjectDox:** Observed on Winter Haven (`myinspections.mywinterhaven.com`, `eplans.mywinterhaven.com`) — not on the Polk County (POLKCO) surface.

---

## Coverage Notes

### robots.txt (operational-risk signal per §3.2)

- **`www.polkfl.gov`:** Yoast-managed. ChatGPT-User / ClaudeBot / GPTBot / PerplexityBot explicitly allowed. `Crawl-delay: 10` suggested for generic UAs. Sitemap directive still points at `www.polk-county.net/sitemap_index.xml` (301 redirect — stale but harmless). File: `evidence/polk-county-fl-polkfl-gov-robots.txt`.
- **`www.polkclerkfl.gov`:** Standard CivicPlus disallow set — Baiduspider + Yandex blanket-denied; admin / search / map / RSS paths disallowed for all UAs; Siteimprove subject to `Crawl-delay: 20`. File: `evidence/polk-county-fl-polkclerkfl-gov-robots.txt`.
- **`gis.polk-county.net`:** HTTP 404 — ArcGIS Enterprise omits robots.txt. Operational risk governed by rate-limiting. File: `evidence/polk-county-fl-gis-robots.txt`.
- **`aca-prod.accela.com`:** HTTP 404 — Accela Citizen Access tenants do not publish robots.txt; Cloudflare edge is the governor. File: `evidence/polk-county-fl-accela-robots.txt`.
- **`polk-county-fl.legistar.com` / `polkcountyfl.legistar.com` / `webapi.legistar.com`:** HTTP 404 across all Legistar hosts. No robots convention. File: `evidence/polk-county-fl-legistar-robots.txt`.

All 5 robots files are captured. Pacing this run: ~1 req/sec. No 429s or captcha events observed.

### Request budget

- **Total requests this run:** ~56 (substantially under the 300-400 planned budget). Shallow-per-subsystem held — the archived deep-dives for Accela, ArcGIS, and Legistar carried enough field-level coverage that live re-enumeration was only needed to verify (a) vendor fingerprints, (b) new surfaces (Develop Polk, LandDev slug, Polk_Development_Tracker_Map, Map_Development_Overlays, NewVision BrowserView, Tyler PRO), and (c) the WordPress REST footprint on polkfl.gov which had no prior documentation.
- **Requests by subsystem:**
  - Accela POLKCO: 8 (plus 2 gated: `apis.accela.com` 404, `inspections.polk-county.net` 403)
  - ArcGIS Enterprise: 11 (1 gated — PCU folder 499)
  - Legistar OData: 5
  - CMS polkfl.gov: 15 (WP REST + sitemap + RSS + misc)
  - Clerk polkclerkfl.gov: 11 (CivicEngage + BrowserView + Tyler PRO + Municode)
  - iWorq: 1 (verified no county tenant)
  - Robots/sitemap/rebrand Wave 1: 10
- Full request log: `evidence/_polk-county-fl-request-log.txt`.

### Rebrand redirects recorded

- `https://www.polk-county.net/` → `https://www.polkfl.gov/` (301)
- `https://www.polk-county.net/sitemap_index.xml` → `https://www.polkfl.gov/sitemap_index.xml` (301)
- `https://www.polkcountyclerk.net/` → `http://www.polkclerkfl.gov/` (301; target uses HTTP, not HTTPS)
- Criminal records deep-link on the clerk side still uses `www.polkcountyclerk.net/299` (not redirected per current observation — old apex resolves and serves).

Full seed + rebrand notes: `evidence/_polk-county-fl-seed.txt`.

### Cross-references (not re-mapped here)

- **Five east-Polk cities (PT/BI/CR scope):** `davenport-fl.md`, `dundee-fl.md`, `haines-city-fl.md`, `lake-hamilton-fl.md`, `winter-haven-fl.md`.
- **PT adapter:** `modules/permits/scrapers/adapters/polk_county.py` — Accela, live, hardened in 2026-04 (ACCELA-01/03/04/04a/11/14 shipped per improvement report).
- **CR YAMLs:**
  - `modules/commission/config/jurisdictions/FL/polk-county-bcc.yaml` — Legistar, live.
  - `modules/commission/config/jurisdictions/FL/polk-county-pz.yaml` — Legistar, live.
  - `modules/commission/config/jurisdictions/FL/polk-county-tpo.yaml` — ⚠️ needs verification; the improvement report LEGISTAR-05 flags TPO as untracked but a YAML matching the slug pattern may exist.
  - `modules/commission/config/jurisdictions/FL/polk-county-boa.yaml` — ⚠️ **stale per Skip-BOA/ZBA memory. Flag-only: do NOT convert to Legistar. Leave `platform: manual`.**
- **BI seed:** `seed_bi_county_config.py` — Polk row (archive `_archived/polk-county-arcgis.md` §5 documents the 9 mapped fields + 46 unmapped).
- **Archived deep-dives retained (canonical for field-level detail):**
  - `_archived/polk-county-accela.md`
  - `_archived/polk-county-arcgis.md`
  - `_archived/polk-county-iworq.md` (actually city-scope; historical)
  - `_archived/polk-county-legistar.md`
  - `_archived/polk-county-improvement-report.md`
  - `accela-rest-probe-findings.md`
- **CD2 / clerk-records adapter: CONFIRMED GAP.** No in-repo adapter for `www.polkclerkfl.gov`, `apps.polkcountyclerk.net/browserviewor/`, or `pro.polkcountyclerk.net/PRO`. Marion BrowserView hybrid-captcha pattern (user memory) is a viable approach model when Official Records automation becomes a priority; captcha-posture unverified on NewVision / Tyler PRO — none on landings but deep flows were not exercised.

### Key production findings (executive summary of the drift / new-surface results)

1. **Accela drift since archived map** is small but real:
   - Enforcement module now has **4 public record types** (Complaint, Lien, Search Request, Sign Offense) — archive said 2.
   - Land Dev module slug is `LandDev`, not `Planning` (archive had the right name but not the slug).
   - Default.aspx exposes a **"Develop Polk" curated portal** (Land Use / Commercial / Residential sub-portals) not mentioned in the archive. Same underlying modules, different onboarding UI.
   - `apis.accela.com/v4/settings/agencies/POLKCO` 404 — matches the April 2026 REST probe finding.
2. **ArcGIS layers available exceed archive substantially.** The archive covered only `Map_Property_Appraiser/FeatureServer/1` (Parcels). 10 additional services are anonymous-public; three stand out for BI/CD2:
   - `Polk_Development_Tracker_Map/MapServer` (18 layers — fire/EMS, schools, zoning, municipalities, TPO 2040 forecast).
   - `Map_Development_Overlays/MapServer` (8 overlay districts — JPAs, wellfield, Green Swamp, redevelopment).
   - `Map_Flood_and_Drainage/MapServer` (12 layers — FEMA 1983/2000/2012/2016 temporal snapshots + wetlands + soils).
3. **Clerk-records access posture:** Public search available on both vendor portals without captcha on landings. NewVision Systems (Official Records) is new-to-registry; Tyler Odyssey PRO (Civil/Court) is new-to-registry. Neither has an in-repo adapter. Captcha posture on deep flows is unverified.
4. **iWorq current status:** No county-level Polk tenant. Only three east-Polk *cities* (Davenport, Haines City, Lake Hamilton). Mapping responsibility sits in the per-city files.
5. **CD2 gap confirmed.** No adapter exists for clerk records. Municode Library for Polk County exists but SPA tenant ID deferred to a browser-based pass.
6. **Legistar↔Accela link discovery.** `EventItemAccelaRecordId` field on EventItems + MatterTitle substrings like `"LDLVAR-2025-78"` enable direct join between Legistar land-use hearing agenda items and Accela LandDev records. Production CR scraper has the fetch path shipped (`_fetch_event_items`) but is gated off per-YAML — LEGISTAR-03 in the improvement report is the flip-switch work.

### Open gaps (⚠️ GAP markers summarized by section)

- **WordPress REST:** `/wp-json/wp/v2/notice` empty at crawl time despite `meeting-type` having 40+ terms — re-probe on future runs. `cemetery` CPT not probed (low analytical value). `media` not captured (⚠️ GAP — useful for ordinance-PDF discovery). `facetwp/v1` + `wp-pwmwdb-api/v1` namespaces not enumerated.
- **Tribe Events:** confirmed absent on polkfl.gov (`/wp-json/tribe/events/v1/events` → 404). Events ride WordPress permalinks without a matching REST endpoint.
- **ArcGIS per-layer fields:** descriptor-level coverage only on Polk_Development_Tracker_Map, Map_Development_Overlays, Map_Flood_and_Drainage, Map_Street_and_Addresses, PNR_DataViewer. Full per-layer field tables deferred.
- **ArcGIS PCU folder:** HTTP 499 "Authentication required" — internal-only surface. Not pursued.
- **Accela landings:** HTML not re-captured this run (archive fixtures suffice). On next run, capture Enforcement + LandDev VIEWSTATE HTML to keep current.
- **ACA APOLookup / Licensee search:** results not exercised anonymously. Browser-based probe to confirm what parcel/licensee data anonymous users can extract.
- **ACA inspections.polk-county.net:** 403 anon; requires ACA session.
- **Clerk BrowserView / PRO deep flows:** captcha/disclaimer posture not characterized beyond landings.
- **Municode Library Polk tenant `client_id`:** SPA; curl-only pass could not resolve.
- **Polk foreclosure-sales vendor:** `/213/Foreclosure-Sales` page HTML returned but vendor-portal URL not surfaced cleanly in the fetch summary — re-probe.
- **polkclerkfl.gov RSS content:** multiple feeds currently empty (News Flash ModID=1 returned valid-but-empty channel). Cataloged the discovery; re-probe when content is present.
- **Legistar bodies 139/140/246/251/252/254/258:** no YAMLs (LEGISTAR-05 in improvement report — decision-pending, likely P1 for TPO, P2 for others).
- **Legistar `/Matters`, `/Persons`, `/Bodies`, `/Codefiles`, `/Votes` endpoints:** out-of-scope for current scraper.

### `_platforms.md` deltas

Added two rows to `docs/api-maps/_platforms.md` on this run:

- **NewVision Systems (Clerk Official Records):** signatures + known-endpoint gap note; no adapter.
- **Tyler Odyssey PRO (Civil / Court Records):** signatures + gap note; no adapter. Distinct from Tyler MSS / EnerGov / Eagle / Munis rows that already exist.

No other platform discoveries this run — the Polk footprint otherwise reuses already-registered platforms.
