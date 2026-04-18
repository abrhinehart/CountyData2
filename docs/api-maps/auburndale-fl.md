# City of Auburndale, FL (Polk County) — API Map

*Target:* full footprint of the City of Auburndale, Florida — a municipality within Polk County (county-level map for Polk is separate; sister cities already mapped: Davenport, Dundee, Haines City, Lake Alfred, Lake Hamilton, Winter Haven).
*Mapped:* 2026-04-17.
*Method:* anonymous HTTPS probes at ~1 req/sec with UA `Mozilla/5.0 (compatible; CountyDataMapper/1.0)` (bare `CountyData2-mapper/*` UAs get WAF-rejected on vendor edges — see Lake Hamilton finding); no authenticated flows; curl-only run. Seed: `https://auburndalefl.com/`.

## Summary

Auburndale's digital footprint spans **five first-party hostnames** and several external platforms. The primary CMS origin is **`https://auburndalefl.com/`** — a WordPress 6.9.4 install on the **Enfold (Avia/Kriesi)** theme, served through **GoDaddy Managed WordPress** (LiteSpeed backend → Cloudflare edge). On-origin plugins expose three JSON/XML API families: **WP REST** (`/wp-json/wp/v2/*`, 331 routes, 19 namespaces), **The Events Calendar (Tribe) REST** (`/wp-json/tribe/events/v1/*` and the TEC `/wp-json/tec/v1/*` variant), and **Yoast SEO sitemaps** at `/sitemap_index.xml` (Yoast supersedes the native WP `wp-sitemap.xml`, which 301s to the Yoast index).

**Online permit portal EXISTS.** Construction-services links to **GovBuilt** (`https://auburndalefl.govbuilt.com/`), an Orchard Core-based SaaS by **MCC Innovations**. Its public reporting API — `/PublicReport/GetAllContentToolModels` — returns **30,142 case records** (building/zoning/planning/code applications) and **716 license records** (contractor registrations) with applicant names, addresses, phones, GPS coordinates, case numbers, and status — all unauthenticated and DataTables-paginated up to at least `Length=1000`. A parallel **SmartGov Public Portal (Granicus)** tenant exists at `ci-auburndale-fl.validation.smartgovcommunity.com` (the `.validation.` subdomain is a staging/tenant-validation environment) but the live construction page routes citizens to GovBuilt — SmartGov is a legacy/parallel tenant kept accessible behind a secondary button.

**Other first-party subdomains:**
- **`weblink.auburndalefl.com`** — **Laserfiche WebLink 10** Angular SPA on Microsoft-IIS/10.0 hosting the public Official Records / Agendas / Minutes archive. Repository is named `CityOfAuburndale`, `dbid=0`. Legacy `/weblink8/` paths auto-redirect to `/WebLink/`. Cookie-gated Angular hydration — probed as a scrape target.
- **`utility.auburndalefl.com/ubs1/`** — **American Data Group (ADG) UBS** utility billing portal (new vendor added to `_platforms.md`). Login-only (`a_no` account + `a_pass` password); no public data surface — deferred per Lake Alfred rule.

**External platforms (linked, not crawled):** **Municode Library** for the Code of Ordinances (`library.municode.com/fl/auburndale/codes/code_of_ordinances`, `clientId=10379`) — already in `_platforms.md`; **Polk County Property Appraiser** (`polkpa.org`); **PRWC** (Polk Regional Water Cooperative, `prwcwater.org`); **SWFWMD e-Permitting** (`swfwmd.state.fl.us/business/epermitting/…`); **EyeOnWater** (`helpeyeonwater.com`) for AMI meter readings; Chamber of Commerce (`myauburndalechamber.com`). All cross-reference `polk-county-fl.md` for parent-county infra (Polk Property Appraiser, Polk GIS, Polk Legistar).

**Totals:** 74 HTTPS requests this run (well under the 2000 cap); 22 APIs documented (WP REST + TEC + sitemap + RSS + iCal + GovBuilt JSON); 8 scrape targets; 6 external platforms noted; 0 × 429, 0 × captcha, **1 × Cloudflare WAF 403** (on `POST /xmlrpc.php` — the WAF blocks XML-RPC POSTs by default on GoDaddy Managed WordPress). Cloudflare `__cf_bm` bot-management cookie was set on every auburndalefl.com request but did not interfere with probing at this volume. GovBuilt, WebLink, and ADG did not issue Cloudflare challenges.

**No lien-assessment or code-case online search is public outside the GovBuilt portal** — code-compliance pages on the CMS are static info; GovBuilt already covers "Code Enforcement" case types under the same search.

---

## Platform Fingerprint

| Signal | Value |
|---|---|
| Primary origin | `https://auburndalefl.com/` — apex serves content directly; `www.` not confirmed but Yoast canonicals point to apex. HTTP/1.1 through Cloudflare. |
| Edge / fronting | **Cloudflare** — `CF-RAY`, `CF-Cache-Status`, `__cf_bm` HttpOnly cookie, `Server: cloudflare`. `alt-svc: h3=":443"` advertises HTTP/3. |
| Gateway | **GoDaddy Managed WordPress (MWP)** — `x-gateway-cache-key`, `x-gateway-cache-status: HIT|MISS|BYPASS`, `x-gateway-request-id`, `x-gateway-skip-cache`, `x-litespeed-tag` headers. Wildcards with LiteSpeed origin behind MWP fronting. |
| CMS | **WordPress 6.9.4** — `<meta name="generator" content="WordPress 6.9.4">`, `/wp-json/` REST, `wp-includes/`, `wp-content/`, `rel="pingback"` link, `Link: <…>; rel="https://api.w.org/"`. 19 registered REST namespaces. |
| Theme | **Enfold** (`wp-content/themes/enfold`) by Kriesi/Avia — classic non-block theme with `avia_*` CSS classes, `av-special-heading-tag`, `avia-image-overlay-wrap`. Image-tile navigation on home / dept pages. |
| SEO / sitemap | **Yoast SEO** — overrides native WP sitemap: `/wp-sitemap.xml` HTTP 301s (via `x-redirect-by: Yoast SEO`) to `/sitemap_index.xml`. 9 Yoast sub-sitemaps. |
| Events plugin | **The Events Calendar** by StellarWP — iCal `PRODID:-//City of Auburndale - ECPv6.15.20//NONSGML v1.0//EN` (version 6.15.20). Namespaces `tribe/events/v1`, `tribe/views/v2`, `tribe/event-aggregator/v1`, `tec/v2/onboarding`, `tec/v1`. |
| Tabular content | **TablePress** (`wp-content/plugins/tablepress`) — referenced on the Meetings page; tables rendered client-side into the HTML. No public API. |
| Analytics | **Independent Analytics** (`wp-content/plugins/independent-analytics`) — namespace `iawp` with `/iawp` and `/iawp/search` routes (privileged; returns 401 for anon but the plugin is fingerprinted). |
| Caching | **LiteSpeed Cache** — namespaces `litespeed/v1`, `litespeed/v3` (privileged admin surface; fingerprinted only). |
| GoDaddy-specific plugins | **WP-Aas** (`wpaas/v1`), **Site Designer** (`wp-site-designer/v1`) — GoDaddy-injected control-plane namespaces; not public-data surfaces. |
| Security / admin | **Two-Factor** (`two-factor`), **Simple History** (`simple-history/v1`), **Object Cache** (`objectcache/v1`) — privileged only. |
| Auth mechanism advertised | `application-passwords` at `/wp-admin/authorize-application.php`. No anonymous writes. |
| Robots policy | `User-Agent: * \n Disallow:` — fully permissive; no `Sitemap:` directive (Yoast auto-announces via `<link rel="sitemap">` on the home page). `last-modified: Mon, 06 Apr 2020`. |
| Rate limiting / WAF | No 429 or captcha at 74-req volume. One WAF hit: `POST /xmlrpc.php` → **HTTP 403 "Sorry, you have been blocked" (Cloudflare)** — standard Cloudflare Super Bot Fight Mode default for xmlrpc. |
| Permit / licensing SaaS | **GovBuilt (MCC Innovations)** on `auburndalefl.govbuilt.com` — Orchard Core / ASP.NET / Azure App Service (`ARRAffinity` cookies); Froala editor, dataTables, Esri pin assets. Public JSON APIs under `/PublicReport/`. **30,142 cases / 716 licenses.** |
| Secondary permit SaaS | **SmartGov Public Portal (Granicus)** on `ci-auburndale-fl.validation.smartgovcommunity.com` — `.validation.` staging-tenant subdomain; landing renders but deeper case search requires auth. Kept as a secondary tile on the construction-services CMS page; GovBuilt is the live primary. |
| Records archive | **Laserfiche WebLink 10** on `weblink.auburndalefl.com` — repo `CityOfAuburndale`, `dbid=0`. `/weblink8/` auto-rewrites to `/WebLink/`. Microsoft-IIS/10.0; Angular SPA shell; cookie-gated. |
| Utility billing | **American Data Group (ADG) UBS** on `utility.auburndalefl.com/ubs1/` — PHP/8.3 on IIS/10; login-gated. No public data surface. |
| External platforms linked from nav/footer/dept pages | **Municode Library** (`library.municode.com/fl/auburndale/…`, `clientId=10379`), **Polk County Property Appraiser** (`polkpa.org`), **PRWC** (`prwcwater.org`), **SWFWMD e-Permitting** (`swfwmd.state.fl.us/business/epermitting/…`), **EyeOnWater** (`helpeyeonwater.com`), **Auburndale Chamber** (`myauburndalechamber.com`). Facebook and Instagram social links. |
| §5 known-platform checks | WordPress REST + TEC ✓ (both in `_platforms.md`). Municode Library ✓ (external, already registered). GovBuilt, Laserfiche WebLink 10, American Data Group UBS, SmartGov Public Portal — all **added to `_platforms.md` this run**. No Legistar, CivicClerk, CivicPlus, Granicus ViewPublisher, eScribe, Municode Meetings, Tyler EnerGov/Munis, Accela, OpenGov, OnBase, ArcGIS on-origin, Gravity Forms, iWorQ, Cloudpermit, Catalis GovOffice, or Authority Pay observed. |

---

## APIs

All on-origin API endpoints live on `auburndalefl.com`. The GovBuilt JSON APIs live on `auburndalefl.govbuilt.com`. External-platform JSON APIs (Municode, Polk PA, SWFWMD, EyeOnWater) are not documented here — they are linked out and belong to those platforms' own maps.

### `/` (site root and WP conventions) — `auburndalefl.com`

#### robots.txt

- **URL:** `https://auburndalefl.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots Exclusion directives — a single `User-Agent: *` block with an empty `Disallow:` (fully permissive). No `Sitemap:` line; the Yoast sitemap is discovered via the home page `<link rel="sitemap">` or by convention at `/sitemap_index.xml`.
- **Response schema:**
  ```
  {
    "content_type": "text/plain",
    "directives": [
      {"user_agent": "*", "disallow": []}
    ]
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** none — static file.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `last-modified: 2020-04-06` — static; has not been touched since site relaunch.
- **Discovered via:** standard `/robots.txt` probe.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/robots.txt'
  ```
- **Evidence file:** `evidence/auburndale-fl-robots.txt` (headers: `evidence/auburndale-fl-robots.headers.txt`)
- **Notes:** Unambiguously permissive. Cloudflare cached (`CF-Cache-Status: HIT`).

#### wp-sitemap.xml → sitemap_index.xml (Yoast SEO)

- **URL:** `https://auburndalefl.com/sitemap_index.xml` (legacy `/wp-sitemap.xml` HTTP 301-redirects here via `x-redirect-by: Yoast SEO`)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Yoast SEO sitemap index pointing to 9 sub-sitemaps: posts, pages, tribe_events, portfolio, category, post_tag, tribe_events_cat, portfolio_entries, author. Each sub-sitemap is a standard Sitemap Protocol 0.9 `<urlset>` with Yoast's XSL stylesheet.
- **Response schema:**
  ```
  {
    "sitemapindex": {
      "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "sitemap": [{"loc": "url", "lastmod": "iso8601"}]
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:**
  - Legacy `/wp-sitemap.xml` — returns HTTP 301 with `Location: /sitemap_index.xml` and `x-redirect-by: Yoast SEO`. Native WP sitemap disabled by Yoast.
- **Pagination:** index → 9 sub-sitemaps; each sub-sitemap at most 2000 entries per Yoast default.
- **Rate limits observed:** none observed
- **Data freshness:** `current` — regenerated on content change (lastmod on `page-sitemap.xml` = mapping-run day).
- **Discovered via:** WP default location + home page `<link rel="sitemap">`.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/sitemap_index.xml'
  ```
- **Evidence file:** `evidence/auburndale-fl-sitemap-index.xml` (headers: `evidence/auburndale-fl-sitemap-index.headers.txt`). Sub-sitemaps: `evidence/auburndale-fl-{post,page,tribe_events,portfolio,category,post_tag,tribe_events_cat,portfolio_entries,author}-sitemap.xml`.
- **Notes:** Reliable change-detection signal for every public CPT + taxonomy. `post-sitemap` and `category-sitemap` have a lastmod of 2024-12-20 — classic-blog (news) side is semi-dormant; operational updates flow through `page-sitemap` and `tribe_events-sitemap`.

#### /feed/ — main RSS 2.0

- **URL:** `https://auburndalefl.com/feed/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** WordPress main RSS 2.0 feed — latest 10 `post` CPT entries (news, citizen commendations, department announcements). Namespaces: `content:encoded`, `dc`, `atom`, `sy`.
- **Response schema:**
  ```
  {
    "rss": {
      "channel": {
        "title": "string",
        "link": "url",
        "description": "string",
        "lastBuildDate": "rfc822",
        "item": [{
          "title": "string",
          "link": "url",
          "guid": "string",
          "pubDate": "rfc822",
          "dc:creator": "string",
          "category": ["string"],
          "description": "html",
          "content:encoded": "html"
        }]
      }
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:**
  - `/comments/feed/` — also available; returns comments RSS (channel with empty `item` set — site has comments disabled).
- **Pagination:** `none` — feed caps at 10 items by default; scoped feeds inherit the WP `posts_per_rss` setting.
- **Rate limits observed:** none observed
- **Data freshness:** real-time on post publish (WordPress pushes to the feed on save).
- **Discovered via:** home page `<link rel="alternate" type="application/rss+xml">`.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/feed/'
  ```
- **Evidence file:** `evidence/auburndale-fl-feed.xml` (headers: `evidence/auburndale-fl-feed.headers.txt`; comments feed: `evidence/auburndale-fl-comments-feed.xml`)
- **Notes:** `post` CPT is semi-dormant (latest posts are police/citizen commendations circa 2021–2024). Event / meeting data does not flow through this feed — see the iCal + Tribe REST below.

#### /comments/feed/ — comments RSS 2.0

- **URL:** `https://auburndalefl.com/comments/feed/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RSS 2.0 comments feed — empty channel; comments are disabled site-wide on Auburndale's WP install.
- **Response schema:** same shape as `/feed/` with zero `item` entries.
- **Observed parameters:** none.
- **Probed parameters:** none.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `n/a` (empty).
- **Discovered via:** WP convention + home page `<link>` hints.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/comments/feed/'
  ```
- **Evidence file:** `evidence/auburndale-fl-comments-feed.xml` (headers: `evidence/auburndale-fl-comments-feed.headers.txt`)
- **Notes:** Not useful — documenting only for completeness of WP-convention surfaces.

#### /events/?ical=1 — Events Calendar iCal feed

- **URL:** `https://auburndalefl.com/events/?ical=1`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RFC 5545 iCal feed from The Events Calendar plugin — all published `tribe_events` entries. Each `VEVENT` carries `UID`, `DTSTART`/`DTEND` with `TZID=America/New_York`, `SUMMARY`, `DESCRIPTION`, `URL`, `LOCATION`, `CATEGORIES`, `ORGANIZER`, `GEO`, `LAST-MODIFIED`. `PRODID:-//City of Auburndale - ECPv6.15.20//NONSGML v1.0//EN`.
- **Response schema:**
  ```
  {
    "content_type": "text/calendar",
    "vcalendar": {
      "PRODID": "-//City of Auburndale - ECPv6.15.20//NONSGML v1.0//EN",
      "X-WR-CALNAME": "City of Auburndale",
      "X-ORIGINAL-URL": "https://auburndalefl.com",
      "X-WR-CALDESC": "Events for City of Auburndale",
      "vtimezone": "America/New_York",
      "vevent": [{
        "uid": "string",
        "dtstart": "tz-aware datetime",
        "dtend": "tz-aware datetime",
        "summary": "string",
        "description": "html",
        "url": "url",
        "location": "string",
        "categories": ["string"],
        "organizer": "string",
        "last_modified": "utc datetime"
      }]
    }
  }
  ```
- **Observed parameters:**
  - `ical` (int, required) — set `1` to trigger iCal output.
- **Probed parameters:** `ical=1` confirmed. Per TEC docs, category-scoped iCals also work at `/events/category/<slug>/?ical=1`.
- **Pagination:** `none` — TEC emits the full upcoming window plus recent past events per plugin config. `X-Robots-Tag: noindex` on response.
- **Rate limits observed:** none observed
- **Data freshness:** real-time; iCal standard `REFRESH-INTERVAL` hint not confirmed on this run.
- **Discovered via:** home page `<link rel="alternate" type="text/calendar">` + explicit nav link.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/events/?ical=1'
  ```
- **Evidence file:** `evidence/auburndale-fl-events-ical.ics` (headers: `evidence/auburndale-fl-events-ical.headers.txt`)
- **Notes:** CR consumers: City Commission meetings, Planning Commission meetings, and Community Development public hearings ride this feed. Lightweight change-detection alternative to the Tribe REST below — 3 KB payload vs ~25 KB for the equivalent REST call.

#### xmlrpc.php — WordPress XML-RPC (WAF-blocked)

- **URL:** `https://auburndalefl.com/xmlrpc.php`
- **Method:** `POST` (GET returns the standard WordPress text message, but POST is WAF-blocked)
- **Auth:** n/a — WAF intercepts before WordPress sees the request
- **Data returned:** `POST` returns **HTTP 403 "Sorry, you have been blocked" (Cloudflare)** with a Ray ID. GoDaddy MWP's default Cloudflare Super Bot Fight Mode blocks anonymous XML-RPC POSTs. GET returns the harmless WordPress landing message.
- **Response schema:** n/a (403 HTML from Cloudflare).
- **Observed parameters:** none on GET.
- **Probed parameters:**
  - `GET /xmlrpc.php` — HTTP 200, returns the XML-RPC landing HTML (Cloudflare does not block GET).
  - `POST /xmlrpc.php` (with `system.listMethods` body) — HTTP 403 "Attention Required! | Cloudflare".
- **Pagination:** `none`
- **Rate limits observed:** 403 on every POST, 0 on GET — this is a WAF rule, not a rate limit.
- **Data freshness:** `n/a`
- **Discovered via:** home page `<link rel="pingback" href="…/xmlrpc.php">`.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/xmlrpc.php'
  # POST attempt (expect 403):
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' -X POST -d '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>' -H 'Content-Type: text/xml' 'https://auburndalefl.com/xmlrpc.php'
  ```
- **Evidence file:** `evidence/auburndale-fl-xmlrpc.txt` (headers: `evidence/auburndale-fl-xmlrpc.headers.txt`)
- **Notes:** ⚠️ GAP: XML-RPC method enumeration not possible anonymously. Low priority — `/wp-json/` is the modern surface and carries everything useful.

### `/wp-json/` (WordPress REST root) — `auburndalefl.com`

The WP REST root advertises **19 namespaces** and **331 routes**. Site descriptor: `name: "City of Auburndale"`, `description: "A wonderful place to live, work &amp; play"`, `timezone_string: "America/New_York"`, `gmt_offset: -4`. Advertised auth: `application-passwords` at `/wp-admin/authorize-application.php`.

#### /wp-json/ — REST root / API discovery

- **URL:** `https://auburndalefl.com/wp-json/`
- **Method:** `GET`
- **Auth:** `none` for discovery; `application-passwords` advertised for privileged routes
- **Data returned:** Site descriptor + full route catalog (331 routes). Namespaces: `oembed/1.0`, `two-factor`, `wp-site-designer/v1`, `wpaas/v1`, `iawp`, `litespeed/v1`, `litespeed/v3`, `simple-history/v1`, `yoast/v1`, `tribe/event-aggregator/v1`, `tribe/events/v1`, `tribe/views/v2`, `tec/v2/onboarding`, `tec/v1`, `objectcache/v1`, `wp/v2`, `wp-site-health/v1`, `wp-block-editor/v1`, `wp-abilities/v1`.
- **Response schema:**
  ```
  {
    "name": "string",
    "description": "string",
    "url": "url",
    "home": "url",
    "gmt_offset": "string",
    "timezone_string": "string",
    "namespaces": ["string"],
    "authentication": {"application-passwords": {"endpoints": {"authorization": "url"}}},
    "routes": {
      "<path>": {
        "namespace": "string",
        "methods": ["string"],
        "endpoints": [{"methods": ["string"], "args": {"<param>": {"type": "string", "required": "bool"}}}],
        "_links": {"self": [{"href": "url"}]}
      }
    },
    "_links": {"help": [{"href": "url"}]}
  }
  ```
- **Observed parameters:** none on root.
- **Probed parameters:**
  - `?context=embed|view|edit` — standard; not individually probed.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** regenerated on plugin install / plugin config change.
- **Discovered via:** home page `Link: <https://auburndalefl.com/wp-json/>; rel="https://api.w.org/"` header.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-json.json` (truncated: route catalog sampled to first 20 keys; full shape always available from live endpoint). Headers: `evidence/auburndale-fl-wp-json.headers.txt`.
- **Notes:** The plugin-specific namespaces (`iawp`, `litespeed/*`, `objectcache/v1`, `simple-history/v1`, `two-factor`, `wpaas/v1`, `wp-site-designer/v1`) are privileged or admin-only and return `rest_forbidden` 401 for anonymous callers. The public-data namespaces are `wp/v2`, `tribe/events/v1`, `tribe/views/v2`, `tec/v1`, `yoast/v1`, `oembed/1.0` — documented below. Cross-ref `polk-county-fl.md` for the Polk parent infra.

### `/wp-json/wp/v2/*` — WordPress core public routes

#### /wp-json/wp/v2/pages

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/pages`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** List of published `page` entries — the primary content surface (City Commission, City Departments, Meetings, Public Notices, Construction Services, Utilities, etc.). 69 total pages.
- **Response schema:**
  ```
  [{
    "id": "int",
    "date": "iso8601",
    "date_gmt": "iso8601",
    "guid": {"rendered": "url"},
    "modified": "iso8601",
    "modified_gmt": "iso8601",
    "slug": "string",
    "status": "publish",
    "type": "page",
    "link": "url",
    "title": {"rendered": "string"},
    "content": {"rendered": "html", "protected": "bool"},
    "excerpt": {"rendered": "html", "protected": "bool"},
    "author": "int",
    "featured_media": "int",
    "parent": "int",
    "menu_order": "int",
    "comment_status": "string",
    "ping_status": "string",
    "template": "string",
    "meta": "object",
    "class_list": ["string"],
    "_links": "object"
  }]
  ```
- **Observed parameters:**
  - `per_page` (int, optional) — default 10; WP hard-caps at 100.
- **Probed parameters:**
  - `per_page=100` — accepted; `X-WP-Total: 69`, `X-WP-TotalPages: 1`.
  - Pagination via `page=N` — standard WP; `Link: rel="next"` header present when more pages exist.
- **Pagination:** `page` (1-based) with `per_page` up to 100. Headers `X-WP-Total` and `X-WP-TotalPages` on every response.
- **Rate limits observed:** none observed
- **Data freshness:** real-time; includes `modified_gmt` for delta queries (standard `?modified_after=…` filter).
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/pages?per_page=100'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-pages.json` (truncated to 3 items; `content.rendered`/`excerpt.rendered` stripped per §6). Headers: `evidence/auburndale-fl-wp-pages.headers.txt`.
- **Notes:** Primary structural surface for crawling. Every department page shows up here with its full HTML body and `modified_gmt` — a single call plus a delta query replaces the whole site crawl.

#### /wp-json/wp/v2/posts

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/posts`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** List of published `post` (news/announcements) entries. 32 total posts — semi-dormant; latest items include citizen commendations 2021–2024.
- **Response schema:** same as `/wp/v2/pages` minus `parent`/`menu_order`; adds `sticky: bool`, `categories: [int]`, `tags: [int]`, `format: "standard"`.
- **Observed parameters:**
  - `per_page` (int, optional).
- **Probed parameters:**
  - `per_page=100` — returns all 32 in one page; `X-WP-Total: 32`, `X-WP-TotalPages: 1`.
  - Standard `?categories=…`, `?tags=…`, `?search=…`, `?after=…`, `?before=…`, `?modified_after=…` filters are supported per WP core.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** real-time on publish.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/posts?per_page=100'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-posts.json` / `auburndale-fl-wp-posts-max.json` (truncated). Headers: `evidence/auburndale-fl-wp-posts.headers.txt`.
- **Notes:** Use the RSS feed or `modified_after=…` delta for change-detection — cheaper than polling the full list.

#### /wp-json/wp/v2/media

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/media`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Media library entries (images + uploaded PDFs — budgets, drinking water reports, zoning print layouts, utility area maps, approved FY26-27 budget book). 985 total media items.
- **Response schema:** standard WP media shape — `id`, `date`, `slug`, `mime_type`, `media_type`, `source_url`, `caption`, `alt_text`, `media_details: {width, height, file, sizes: {<size>: {file, width, height, source_url}}}`, `_links`.
- **Observed parameters:**
  - `per_page` (int, optional; max 100).
- **Probed parameters:**
  - `per_page=3` — `X-WP-Total: 985`, `X-WP-TotalPages: 329`.
  - Standard `?search=`, `?media_type=image|file`, `?mime_type=application/pdf` filters per WP core.
- **Pagination:** `page` / `per_page` (max 100).
- **Rate limits observed:** none observed
- **Data freshness:** real-time on upload.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/media?per_page=100&mime_type=application/pdf'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-media.json` (truncated). Headers: `evidence/auburndale-fl-wp-media.headers.txt`.
- **Notes:** Useful for enumerating the PDF corpus (budgets, drinking-water reports, annual audits, zoning layouts) without page-scraping. Filter `?mime_type=application/pdf` is the canonical way to list documents.

#### /wp-json/wp/v2/users

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/users`
- **Method:** `GET`
- **Auth:** `none` for authors of published content
- **Data returned:** Public author profiles for users who have published content. 2 users: Josh Starr (id 30, slug `jstarr`) and Seth Teston (id 27, slug `steston`) — the site's content editors.
- **Response schema:** `id`, `name`, `url`, `description`, `link`, `slug`, `avatar_urls: {"24","48","96"}`, `meta: {}`, `_links`.
- **Observed parameters:**
  - `per_page` (int, optional).
- **Probed parameters:**
  - `per_page=20` — returns both users.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** static; changes only when an editor publishes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/users'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-users.json` (avatar URLs stripped). Headers: `evidence/auburndale-fl-wp-users.headers.txt`.
- **Notes:** Low signal.

#### /wp-json/wp/v2/categories

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/categories`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Post categories. 10 total.
- **Response schema:** `id`, `count`, `description`, `link`, `name`, `slug`, `taxonomy`, `parent`, `meta`, `_links`.
- **Observed parameters:** `per_page`.
- **Probed parameters:** `per_page=50` — `X-WP-Total: 10`.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/categories?per_page=50'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-categories.json`. Headers: `evidence/auburndale-fl-wp-categories.headers.txt`.
- **Notes:** Sibling taxonomy `/wp/v2/tags` exists; not probed individually (standard WP shape, identical semantics).

#### /wp-json/wp/v2/portfolio — Enfold Portfolio CPT

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/portfolio`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Enfold theme's `portfolio` CPT — used here for completed CIP / infrastructure projects (City Hall Underground Utilities, Cindy Hummel Tennis Center, Bridgers Avenue Signalization, Downtown Clock Tower, Ariana Ave resurfacing, Historic Train Depot design, etc.). 12 total entries.
- **Response schema:** standard WP CPT shape — `id`, `date`, `slug`, `status`, `type: "portfolio"`, `link`, `title`, `content`, `excerpt`, `featured_media`, `_links`. Taxonomy attached: `portfolio_entries`.
- **Observed parameters:** `per_page`.
- **Probed parameters:** `per_page=3` — `X-WP-Total: 12`, `X-WP-TotalPages: 4`.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** updated when a CIP project is added (last activity 2026-01-29).
- **Discovered via:** `/wp-json/wp/v2/types` enumeration.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/portfolio?per_page=100'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-portfolio.json` (truncated). Headers: `evidence/auburndale-fl-wp-portfolio.headers.txt`.
- **Notes:** Maps to BI (Builder Inventory) suite relevance — completed public-infrastructure projects tracked here.

#### /wp-json/wp/v2/types

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/types`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Post-type registry. Observed types: `post`, `page`, `attachment`, `nav_menu_item`, `wp_block`, `wp_template`, `wp_template_part`, `wp_global_styles`, `wp_navigation`, `wp_font_family`, `wp_font_face`, `tribe_venue`, `tribe_organizer`, `tribe_events`, `portfolio`, `tec_calendar_embed`.
- **Response schema:** `{ "<type>": {"description","hierarchical","name","slug","rest_base","rest_namespace","icon","labels","taxonomies","_links"} }`.
- **Observed parameters:** none.
- **Probed parameters:** none.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes (on plugin activation).
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/types'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-types.json`. Headers: `evidence/auburndale-fl-wp-types.headers.txt`.
- **Notes:** The `tribe_*` and `portfolio`/`portfolio_entries` types confirm the plugin stack.

#### /wp-json/wp/v2/taxonomies

- **URL:** `https://auburndalefl.com/wp-json/wp/v2/taxonomies`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Taxonomy registry. Observed: `category`, `post_tag`, `nav_menu`, `wp_pattern_category`, `tribe_events_cat`, `portfolio_entries`.
- **Response schema:** `{ "<taxonomy>": {"name","slug","description","types","hierarchical","rest_base","rest_namespace","_links"} }`.
- **Observed parameters:** none.
- **Probed parameters:** none.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/wp/v2/taxonomies'
  ```
- **Evidence file:** `evidence/auburndale-fl-wp-taxonomies.json`. Headers: `evidence/auburndale-fl-wp-taxonomies.headers.txt`.
- **Notes:** Use with `/wp/v2/tribe_events_cat` and `/wp/v2/portfolio_entries` terms to filter CPT queries.

### `/wp-json/tribe/events/v1/*` — The Events Calendar (Tribe) REST

#### /wp-json/tribe/events/v1/events

- **URL:** `https://auburndalefl.com/wp-json/tribe/events/v1/events`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Paginated list of `tribe_events` with rich event shape: times with timezone details, venue object, organizer object, categories, tags, featured image, cost, description. 8 total upcoming events.
- **Response schema:**
  ```
  {
    "events": [{
      "id": "int",
      "global_id": "string",
      "global_id_lineage": ["string"],
      "author": "string",
      "status": "publish",
      "date": "iso8601",
      "date_utc": "iso8601",
      "modified": "iso8601",
      "modified_utc": "iso8601",
      "url": "url",
      "rest_url": "url",
      "title": "string",
      "description": "html",
      "excerpt": "html",
      "slug": "string",
      "image": {"url","id","extension","width","height","filesize","sizes":{"<size>":{"width","height","mime-type","filesize","url"}}},
      "all_day": "bool",
      "start_date": "Y-m-d H:i:s",
      "start_date_details": {"year","month","day","hour","minutes","seconds"},
      "end_date": "Y-m-d H:i:s",
      "end_date_details": "object",
      "utc_start_date": "Y-m-d H:i:s",
      "utc_end_date": "Y-m-d H:i:s",
      "timezone": "America/New_York",
      "timezone_abbr": "EDT|EST",
      "cost": "string",
      "cost_details": "object",
      "website": "url",
      "show_map": "bool",
      "show_map_link": "bool",
      "hide_from_listings": "bool",
      "sticky": "bool",
      "featured": "bool",
      "categories": [{"id","name","slug","term_id","taxonomy","parent","count","description","urls":{"self","collection"}}],
      "tags": ["array"],
      "venue": {"id","venue","slug","address","city","country","province","zip","phone","website","stateprovince","show_map","show_map_link","url"},
      "organizer": {"id","organizer","slug","phone","website","email","url"},
      "custom_fields": "array"
    }],
    "rest_url": "url",
    "total": "int",
    "total_pages": "int",
    "next_rest_url": "url"
  }
  ```
- **Observed parameters:**
  - `per_page` (int, optional; default 10).
  - `start_date` (date, optional).
  - `end_date` (date, optional).
- **Probed parameters:**
  - `per_page=5` → 5 events returned; `total: 8, total_pages: 2`.
  - `per_page=50&start_date=2025-01-01&end_date=2027-01-01` → 8 events returned (full year-range window).
  - Per plugin docs the endpoint also accepts `categories`, `tags`, `venue`, `organizer`, `search`, `status`, `featured`, `geoloc`, `geoloc_lat`, `geoloc_lng` — not individually probed.
- **Pagination:** `page` / `per_page`. `next_rest_url` field in body for forward traversal.
- **Rate limits observed:** none observed
- **Data freshness:** real-time on event save.
- **Discovered via:** `<link rel="alternate" href="…/wp-json/tribe/events/v1/">` in home HTML.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/tribe/events/v1/events?per_page=50&start_date=2026-01-01&end_date=2027-01-01'
  ```
- **Evidence file:** `evidence/auburndale-fl-tribe-events.json` (truncated to 3 events; descriptions stripped). Also `evidence/auburndale-fl-tribe-events-paged.json`. Headers: `evidence/auburndale-fl-tribe-events.headers.txt`, `evidence/auburndale-fl-tribe-events-paged.headers.txt`.
- **Notes:** Primary CR surface. City Commission, Planning Commission, Community Development public hearings all flow here. Use `modified_utc` for delta.

#### /wp-json/tribe/events/v1/categories

- **URL:** `https://auburndalefl.com/wp-json/tribe/events/v1/categories`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Event-calendar categories. 8 total.
- **Response schema:** `{"categories": [{"id","name","slug","term_id","taxonomy","parent","count","description","urls"}], "rest_url","total","total_pages","next_rest_url"}`.
- **Observed parameters:** `per_page`.
- **Probed parameters:** default paging.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/tribe/events/v1/categories?per_page=50'
  ```
- **Evidence file:** `evidence/auburndale-fl-tribe-cats.json`. Headers: `evidence/auburndale-fl-tribe-cats.headers.txt`.
- **Notes:** Same data also at `/wp-json/wp/v2/tribe_events_cat` (standard WP taxonomy shape).

#### /wp-json/tribe/events/v1/venues

- **URL:** `https://auburndalefl.com/wp-json/tribe/events/v1/venues`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Event venues (City Hall, Civic Center, etc.). 30 total.
- **Response schema:** `{"venues": [{"id","venue","slug","address","city","country","province","zip","phone","website","stateprovince","show_map","show_map_link","url"}], "rest_url","total","total_pages","next_rest_url"}`.
- **Observed parameters:** `per_page`.
- **Probed parameters:** default paging.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/tribe/events/v1/venues?per_page=50'
  ```
- **Evidence file:** `evidence/auburndale-fl-tribe-venues.json`. Headers: `evidence/auburndale-fl-tribe-venues.headers.txt`.
- **Notes:** CPT mirror at `/wp-json/wp/v2/tribe_venue`.

#### /wp-json/tribe/events/v1/organizers

- **URL:** `https://auburndalefl.com/wp-json/tribe/events/v1/organizers`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Event organizers. 7 total.
- **Response schema:** `{"organizers": [{"id","organizer","slug","phone","website","email","url"}], "rest_url","total","total_pages","next_rest_url"}`.
- **Observed parameters:** `per_page`.
- **Probed parameters:** default paging.
- **Pagination:** `page` / `per_page`.
- **Rate limits observed:** none observed
- **Data freshness:** rarely changes.
- **Discovered via:** `/wp-json/` route catalog.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/tribe/events/v1/organizers?per_page=50'
  ```
- **Evidence file:** `evidence/auburndale-fl-tribe-org.json`. Headers: `evidence/auburndale-fl-tribe-org.headers.txt`.
- **Notes:** CPT mirror at `/wp-json/wp/v2/tribe_organizer`.

### `/wp-json/tec/v1/*` — The Events Calendar v2 REST (Stellar namespace)

#### /wp-json/tec/v1/events (and /organizers /venues /docs)

- **URL:** `https://auburndalefl.com/wp-json/tec/v1/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Newer StellarWP-branded REST namespace with 8 routes: `/tec/v1`, `/tec/v1/events`, `/tec/v1/events/(?P<id>\d+)`, `/tec/v1/organizers`, `/tec/v1/organizers/(?P<id>\d+)`, `/tec/v1/venues`, `/tec/v1/venues/(?P<id>\d+)`, `/tec/v1/docs`. Parallel to the `tribe/events/v1` surface; likely the forward-looking successor.
- **Response schema:** catalog (listed namespace root) — shape of `/tec/v1/events` not individually probed in this run.
- **Observed parameters:** unverified
- **Probed parameters:** unverified — only namespace root probed.
- **Pagination:** unverified
- **Rate limits observed:** none observed
- **Data freshness:** unverified
- **Discovered via:** `/wp-json/` namespace listing.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/tec/v1/'
  ```
- **Evidence file:** `evidence/auburndale-fl-tec-v1.json`. Headers: `evidence/auburndale-fl-tec-v1.headers.txt`.
- **Notes:** ⚠️ GAP: `/tec/v1/events` not probed for parameter semantics. Next run should exercise alongside `/tribe/events/v1/events` to confirm shape parity.

### `/wp-json/oembed/1.0/*` — WordPress oEmbed

#### /wp-json/oembed/1.0/embed

- **URL:** `https://auburndalefl.com/wp-json/oembed/1.0/embed`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard oEmbed discovery endpoint — returns oEmbed-formatted metadata for any WP post/page URL on the site.
- **Response schema:** standard oEmbed 1.0 shape — `version`, `type`, `url`, `title`, `author_name`, `author_url`, `provider_name`, `provider_url`, `html`, `width`, `height`, `thumbnail_url`, `thumbnail_width`, `thumbnail_height`.
- **Observed parameters:**
  - `url` (url, required).
  - `format` (enum, optional) — `json` (default) or `xml`.
- **Probed parameters:** not individually probed this run; discovered only via home-page `<link rel="alternate">` tags.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time on content edit.
- **Discovered via:** home page `<link rel="alternate" type="application/json+oembed" href="…/wp-json/oembed/1.0/embed?url=…">`.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/oembed/1.0/embed?url=https%3A%2F%2Fauburndalefl.com%2F'
  ```
- **Evidence file:** `unverified` — not captured (low priority).
- **Notes:** Convention endpoint. XML variant at `?format=xml`. ⚠️ GAP: shape not captured in evidence this run.

### `/wp-json/yoast/v1/*` — Yoast SEO REST

- **URL:** `https://auburndalefl.com/wp-json/yoast/v1/`
- **Method:** `GET`
- **Auth:** most routes require `edit_posts` capability (401 for anonymous); namespace root + a couple of routes return data for unauth callers
- **Data returned:** 46 routes — almost all admin-only (`file_size`, `statistics`, `readability_scores`, `seo_scores`, `setup_steps_tracking`, `available_posts`, etc.). No public data surface.
- **Response schema:** `{"namespace", "routes", "_links"}`.
- **Observed parameters:** n/a (admin-only).
- **Probed parameters:** namespace root only.
- **Pagination:** varies per route.
- **Rate limits observed:** none observed
- **Data freshness:** n/a
- **Discovered via:** `/wp-json/` namespace listing.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/yoast/v1/'
  ```
- **Evidence file:** `evidence/auburndale-fl-yoast.json`. Headers: `evidence/auburndale-fl-yoast.headers.txt`.
- **Notes:** Fingerprint only. The value of Yoast on this site is the `/sitemap_index.xml` surface (documented above), not the REST namespace.

### `/wp-json/iawp/*` — Independent Analytics

- **URL:** `https://auburndalefl.com/wp-json/iawp/`
- **Method:** `GET`
- **Auth:** admin-only (`manage_options`); returns `rest_forbidden` for anonymous callers on deeper routes
- **Data returned:** 2 routes — `/iawp` and `/iawp/search`. Admin-only plugin.
- **Response schema:** `{"namespace", "routes", "_links"}`.
- **Observed parameters:** n/a.
- **Probed parameters:** namespace root only.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** n/a
- **Discovered via:** `/wp-json/` namespace listing.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.com/wp-json/iawp/'
  ```
- **Evidence file:** `evidence/auburndale-fl-iawp.json`. Headers: `evidence/auburndale-fl-iawp.headers.txt`.
- **Notes:** Fingerprint only — confirms Independent Analytics plugin install. No citizen-facing data.

### `auburndalefl.govbuilt.com` — GovBuilt (MCC Innovations) permit + licensing portal

All endpoints below are on `auburndalefl.govbuilt.com`. Cloudflare-fronted (`CF-RAY`) with Azure App Service origin (`ARRAffinity`, `ARRAffinitySameSite` cookies). Orchard Core CMS substrate. No auth required for public search / type listings.

#### /PublicReport/GetAllContentToolModels — unified case + license DataTables search (⭐ primary permit API)

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/GetAllContentToolModels`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** DataTables-shaped JSON of all public `case` entries (building permits, planning/zoning applications, code-enforcement cases, annexations, variances, etc.) OR `license` entries (contractor registrations, private-provider registrations) depending on `contentType`. **Observed totals at crawl time: 30,142 cases / 716 licenses.** Each record carries applicant name, full address, GPS coordinates, phone, business name, case number, status, type+subtype, created/modified timestamps.
- **Response schema:**
  ```
  {
    "draw": "int",
    "recordsTotal": "int",
    "recordsFiltered": "int",
    "data": [{
      "contentItemId": "string (Orchard ContentItem id)",
      "type": "string (e.g., 'Residential Building Permit Application')",
      "typeTitle": "string",
      "title": "string (case/license number, e.g., 'BR-26-0366')",
      "name": "string (applicant name — PII)",
      "address": "string (full address)",
      "subtype": "string (e.g., 'Residential New Single Family Residence')",
      "created": "MM/DD/YYYY",
      "edited": "MM/DD/YYYY",
      "mapPin": "relative url to pin image",
      "status": "string (e.g., 'Under Plan Review', 'Active', 'Closed')",
      "phoneNumber": "string (PII)",
      "submissionType": "Case|License",
      "isAllowPublicView": "bool",
      "showOnFrontEndLicenseViewButton": "bool",
      "showCaseDetailsReport": "bool",
      "createdDateUtc": "iso8601",
      "modifiedDateUtc": "iso8601",
      "applicantFirstName": "string|null",
      "applicantLastName": "string|null",
      "number": "string (same as title)",
      "allowFeSearch": "bool",
      "applicationLocation": "JSON-encoded string: {Address, Latitude, Longitude, ApartmentSuite, StreetRoute, City, State, PostalCode, Country}",
      "businessName": "string",
      "displayText": "string|null",
      "id": "string|null",
      "caseDisplayText": "string",
      "licenseDisplayText": "string"
    }]
  }
  ```
- **Observed parameters:**
  - `contentType` (enum, required) — `case` or `license`.
  - `searchText` (string, optional) — free-text search.
  - `filter` (string, optional) — additional filter string.
  - `type` (string ContentItemId, optional) — case- or license-type filter (values from `GetAllowedCaseType` / `GetAllowedLicenseType`).
  - `subType` (string ContentItemId, optional) — subtype filter (values from `GetCaseSubTypesByTypeId` / `GetLicenseSubTypesByTypeId`).
  - `days` (int, optional) — recency window in days.
  - `isHideClosedStatus` (bool, optional) — `true` hides closed cases.
  - `Start` (int, required) — page number (1-based).
  - `Length` (int, required) — page size.
  - `SortBy` (string, optional) — one of `Reference|Classification|Type|Sub-Type|Name|Address|Phone Number|Created Date|Last Activity|Status`. Default `Created Date`.
  - `SortType` (enum, optional) — `asc|desc`. Default `desc`.
  - `draw` (int, required by jQuery DataTables for sync) — echo-back value.
- **Probed parameters:**
  - `Length=10` — 10 records returned.
  - `Length=100` — 100 records returned.
  - `Length=1000` — **1000 records returned, no silent cap** (`recordsTotal`/`recordsFiltered` still 30142). Larger limits not probed.
  - `contentType=case` vs `contentType=license` both return data.
  - `SortType=desc` and `SortBy=Created Date` confirmed.
- **Pagination:** DataTables `Start` (1-based page number) + `Length` (page size). Server returns `recordsTotal`/`recordsFiltered` for total count. `Length=1000` works.
- **Rate limits observed:** none observed at ~1 req/sec.
- **Data freshness:** real-time (latest records show `created: 04/17/2026` — mapping-run day).
- **Discovered via:** `/activitysearchtool` HTML + `PublicReport/Scripts/SearchTool.js` source inspection.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/GetAllContentToolModels?searchText=&filter=&contentType=case&type=&days=&subType=&isHideClosedStatus=false&Start=1&Length=100&SortBy=Created%20Date&SortType=desc&draw=1'
  ```
- **Evidence file:** `evidence/auburndale-fl-govbuilt-casesearch.json`, `evidence/auburndale-fl-govbuilt-casesearch-100.json`, `evidence/auburndale-fl-govbuilt-casesearch-1000.json`, `evidence/auburndale-fl-govbuilt-licensesearch.json` (all truncated to 5 items; PII fields `name`/`phoneNumber`/`applicantFirstName`/`applicantLastName`/`businessName` replaced with `[REDACTED]` per §6). Headers: `evidence/auburndale-fl-govbuilt-casesearch.headers.txt`.
- **Notes:** The richest permit dataset in any Polk city mapped to date. **PII-dense** — applicant names, phones, addresses are all in the response. Production adapters must apply retention/consent policy.

#### /PublicReport/PublicReport/GetAllowedCaseType

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetAllowedCaseType`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of all case types configured as publicly searchable — Annexation Application, BOA Variance Application, Residential Building Permit Application, Commercial Building Permit Application, Zoning / PUD / Special Exception, Code Enforcement Case, Planning Commission Application, Fire Inspection Request, Parks Reservation, etc. Each record carries `contentItemId`, `title`, `id`.
- **Response schema:** JSON array `[{ "contentItemId", "type", "typeTitle", "title", "name", "address", "subtype", "created", "edited", "mapPin", "status", "phoneNumber", "submissionType", "isAllowPublicView", "showOnFrontEndLicenseViewButton", "showCaseDetailsReport", "createdDateUtc", "modifiedDateUtc", "applicantFirstName", "applicantLastName", "number", "allowFeSearch", "applicationLocation", "businessName", "displayText", "id", "caseDisplayText", "licenseDisplayText" }]` — same shape as `GetAllContentToolModels.data[]` but most data fields are null/empty; this is a type-catalog dressed in the same schema.
- **Observed parameters:**
  - `contentType` (string, required) — observed value `CaseType`.
- **Probed parameters:** `contentType=CaseType` confirmed.
- **Pagination:** `none` — returns full type list.
- **Rate limits observed:** none observed
- **Data freshness:** regenerated when staff add/retire case types.
- **Discovered via:** `/activitysearchtool` HTML.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetAllowedCaseType?contentType=CaseType'
  ```
- **Evidence file:** `evidence/auburndale-fl-govbuilt-getallowedcase.json` (truncated). Headers: `evidence/auburndale-fl-govbuilt-getallowedcase.headers.txt`.
- **Notes:** Use to build a type-filter dropdown; feed `contentItemId` into `GetAllContentToolModels?type=…` or `GetCaseSubTypesByTypeId?caseTypeId=…`.

#### /PublicReport/PublicReport/GetAllowedLicenseType

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetAllowedLicenseType`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of all license types configured publicly — Contractor Registration, Private Provider Registration. Same record shape as `GetAllowedCaseType`.
- **Response schema:** identical to `GetAllowedCaseType`.
- **Observed parameters:**
  - `contentType` (string, required) — observed value `LicenseType`.
- **Probed parameters:** `contentType=LicenseType` confirmed.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** regenerated on type changes.
- **Discovered via:** `/activitysearchtool` + `/licensed-entities` HTML.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetAllowedLicenseType?contentType=LicenseType'
  ```
- **Evidence file:** `evidence/auburndale-fl-govbuilt-getallowedlicense.json` (truncated). Headers: `evidence/auburndale-fl-govbuilt-getallowedlicense.headers.txt`.
- **Notes:** 2 types observed (Contractor, Private Provider). Use with `GetAllContentToolModels?contentType=license&type=<contentItemId>`.

#### /PublicReport/PublicReport/GetCaseSubTypesByTypeId

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetCaseSubTypesByTypeId`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Subtype catalog scoped to a specific case type.
- **Response schema:** unverified — not probed this run.
- **Observed parameters:**
  - `caseTypeId` (string ContentItemId, required).
- **Probed parameters:** unverified.
- **Pagination:** unverified
- **Rate limits observed:** none observed
- **Data freshness:** unverified
- **Discovered via:** `/activitysearchtool` HTML (URL template `GetCaseSubTypesByTypeId?caseTypeId=${caseTypeId}`).
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetCaseSubTypesByTypeId?caseTypeId=<contentItemId-from-GetAllowedCaseType>'
  ```
- **Evidence file:** `unverified`.
- **Notes:** ⚠️ GAP: shape not captured this run — next pass should pick a real `caseTypeId` from `GetAllowedCaseType` and probe.

#### /PublicReport/PublicReport/GetLicenseSubTypesByTypeId

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetLicenseSubTypesByTypeId`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Subtype catalog scoped to a specific license type.
- **Response schema:** unverified.
- **Observed parameters:**
  - `licenseTypeId` (string ContentItemId, required).
- **Probed parameters:** unverified.
- **Pagination:** unverified
- **Rate limits observed:** none observed
- **Data freshness:** unverified
- **Discovered via:** `/activitysearchtool` HTML.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetLicenseSubTypesByTypeId?licenseTypeId=<contentItemId>'
  ```
- **Evidence file:** `unverified`.
- **Notes:** ⚠️ GAP: next pass should probe with a real `licenseTypeId`.

#### /PublicReport/PublicReport/GetCaseOrLicenseInspectionsByCaseIdOrLicenseId

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetCaseOrLicenseInspectionsByCaseIdOrLicenseId`
- **Method:** `GET` probed; likely needs POST + anti-forgery in SPA flow
- **Auth:** `none` for the route but anti-forgery may be enforced — probe returned the full site HTML landing (sentinel response for invalid requests).
- **Data returned:** Inspection records for a given case or license — intended shape.
- **Response schema:** unverified (probe returned HTML, not JSON).
- **Observed parameters:**
  - `caseIdOrLicenseId` (string ContentItemId, required).
  - `isCase` (bool, required) — `true` for case, `false` for license.
- **Probed parameters:**
  - `GET` with a real `contentItemId` and `isCase=true` → HTML landing (403-ish behavior; anti-forgery enforced on this route).
- **Pagination:** unverified
- **Rate limits observed:** none observed
- **Data freshness:** unverified
- **Discovered via:** `/activitysearchtool` + `PublicReport/Scripts/SearchTool.js` (`ViewInspectionScore` function).
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/PublicReport/PublicReport/GetCaseOrLicenseInspectionsByCaseIdOrLicenseId?caseIdOrLicenseId=4ynx6dyzsav606rfk27by4bgcp&isCase=true'
  ```
- **Evidence file:** `evidence/auburndale-fl-govbuilt-inspections.json` (HTML sentinel, not JSON). Headers: `evidence/auburndale-fl-govbuilt-inspections.headers.txt`.
- **Notes:** ⚠️ GAP: anti-forgery token likely required (the Orchard Core MVC convention). Next pass: harvest `__RequestVerificationToken` from a prior page POST, try with `X-CSRF-TOKEN` header and/or `POST` method.

#### /SearchRecommendations

- **URL:** `https://auburndalefl.govbuilt.com/SearchRecommendations`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Typeahead search recommendations. Current response is a literal text string `"Search is not configured."` — the site-wide search index has not been provisioned on Auburndale's tenant.
- **Response schema:** `string` (plain text).
- **Observed parameters:**
  - `Terms` (string, required) — search query.
- **Probed parameters:** `Terms=permit` returned the not-configured message.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** n/a (unconfigured).
- **Discovered via:** home-page JavaScript.
- **curl:**
  ```bash
  curl -A 'Mozilla/5.0 (compatible; CountyDataMapper/1.0)' 'https://auburndalefl.govbuilt.com/SearchRecommendations?Terms=permit'
  ```
- **Evidence file:** `evidence/auburndale-fl-govbuilt-searchrec.json` (plain text). Headers: `evidence/auburndale-fl-govbuilt-searchrec.headers.txt`.
- **Notes:** ⚠️ GAP: disabled on Auburndale tenant; may return JSON on other GovBuilt tenants.

---

## Scrape Targets

All on-origin HTML pages below are enumerated via the `page-sitemap.xml` and department nav. Only those without a corresponding API are listed (per §4.4 — the API wins when both exist). The WP REST `/wp/v2/pages` already covers body text + metadata, so only pages with additional external widgets or embedded portals are listed here.

### `auburndalefl.com` (CMS pages with unique data surfaces)

#### /meetings/ — Meetings & Agendas hub

- **URL:** `https://auburndalefl.com/meetings/`
- **Data available:** City Commission meeting schedule, standing board meeting times (Planning Commission, Community Redevelopment Agency, Code Enforcement Special Magistrate), inline **TablePress** tables of 2026 commission meeting dates, and outbound links to **Laserfiche WebLink 10** for agendas (`weblink.auburndalefl.com/weblink8/Browse.aspx?dbid=0&startid=38271`) and minutes (`?startid=433`).
- **Fields extractable:** meeting date, meeting type, meeting status, agenda link (external), minutes link (external).
- **JavaScript required:** partial — TablePress renders its tables client-side but the table HTML is present in the initial payload. WebLink links are static `<a>` tags.
- **Anti-bot measures:** Cloudflare `__cf_bm` cookie at edge; no captcha at this volume.
- **Pagination:** `none` — single page with full-year table.
- **Selectors (if stable):** TablePress tables wrap in `table.tablepress#tablepress-<id>`; rows in `tbody > tr > td`. Unstable across TablePress upgrades.
- **Why no API:** the meeting schedule is not exposed via `/wp/v2/pages`' rendered content in a structured way (HTML is a table blob). Tribe Events already carries live future meetings; the TablePress table is a human-readable annual schedule.
- **Notes:** Agendas + minutes themselves live on WebLink (Angular SPA — separate scrape target).

#### /public-notices/ — Public Notices

- **URL:** `https://auburndalefl.com/public-notices/`
- **Data available:** Current public notices (RFPs, zoning notices, annexation notices, drinking-water reports, audit reports, budget books). Links to PDFs hosted under `/wp-content/uploads/…`.
- **Fields extractable:** notice title, posted date, PDF URL, expiration/hearing date (when present).
- **JavaScript required:** `no` — plain HTML body.
- **Anti-bot measures:** Cloudflare at edge; none page-level.
- **Pagination:** `none`
- **Selectors (if stable):** Enfold `.avia_textblock` blocks wrap prose; PDF links via `<a href="…/wp-content/uploads/…*.pdf">`.
- **Why no API:** the page aggregates announcements + PDFs inline; `/wp/v2/pages` gives HTML but no notice-level structure. The PDF corpus itself is enumerable via `/wp/v2/media?mime_type=application/pdf` — prefer that API.
- **Notes:** Partial API coverage — PDFs enumerable via media API, but notice-level metadata (expiration, hearing date) only in HTML.

#### /construction-services/ — Construction Services hub

- **URL:** `https://auburndalefl.com/construction-services/`
- **Data available:** Tile links to **GovBuilt** (`https://auburndalefl.govbuilt.com/`) as the primary permit portal and **SmartGov** (`ci-auburndale-fl.validation.smartgovcommunity.com/Public/Home`) as a secondary/legacy tile, plus narrative about Community Development / Building & Zoning divisions, contact info, inspection request phone, etc.
- **Fields extractable:** division contact info, hours, portal links, public-provider registration hints.
- **JavaScript required:** `no` — Enfold renders server-side.
- **Anti-bot measures:** Cloudflare at edge.
- **Pagination:** `none`
- **Selectors (if stable):** `.avia-image-overlay-wrap > a[href]` for the portal tiles.
- **Why no API:** the page exists to direct citizens to the portals; data flows through GovBuilt/SmartGov, not through any on-origin API.
- **Notes:** Confirms GovBuilt as the **live primary permit portal** and SmartGov as **legacy/parallel** (`.validation.` staging subdomain).

#### /rfps/ — Active RFPs

- **URL:** `https://auburndalefl.com/rfps/`
- **Data available:** current Request-For-Proposal listings with deadlines, scope, contact, and PDF attachments.
- **Fields extractable:** RFP number, title, deadline, contact, PDF links.
- **JavaScript required:** `no`.
- **Anti-bot measures:** Cloudflare at edge.
- **Pagination:** `none`
- **Selectors (if stable):** ad-hoc Enfold blocks — unstable.
- **Why no API:** RFPs are authored as page content, not as a CPT. `/wp/v2/pages` carries the rendered HTML but no line-item structure.
- **Notes:** ⚠️ GAP: no RFP CPT; future parse requires HTML scraping of this page.

#### /jobs/ — City Job Openings

- **URL:** `https://auburndalefl.com/jobs/`
- **Data available:** open positions, department, salary band, closing date, applicant instructions, links to PDF application.
- **Fields extractable:** job title, department, closing date, contact, PDF URL.
- **JavaScript required:** `no`.
- **Anti-bot measures:** Cloudflare at edge.
- **Pagination:** `none`
- **Selectors (if stable):** ad-hoc Enfold blocks.
- **Why no API:** jobs authored as page content. No ATS (e.g., NeoGov) observed.
- **Notes:** Out-of-scope for BI/CR/PT/CD2 typically; documented for completeness.

#### /utility_billing/ + /utilities/ — Utility billing info hub

- **URL:** `https://auburndalefl.com/utility_billing/` (and sibling `https://auburndalefl.com/utilities/`)
- **Data available:** payment instructions, outbound link to **ADG** portal (`utility.auburndalefl.com/ubs1/`), autopay enrollment, rate info, after-hours contact, **EyeOnWater** AMI meter link (`helpeyeonwater.com`), PRWC water-quality links, SWFWMD watering restrictions.
- **Fields extractable:** rate tables (if embedded as TablePress), payment portal URL, contact info.
- **JavaScript required:** `no`.
- **Anti-bot measures:** Cloudflare at edge.
- **Pagination:** `none`
- **Selectors (if stable):** Enfold blocks + TablePress tables.
- **Why no API:** informational hub. No on-origin rate API.
- **Notes:** The data itself (balances/transactions) lives on ADG behind login — not scrapable anonymously.

### `weblink.auburndalefl.com` (Laserfiche WebLink 10 Angular SPA)

#### /WebLink/Browse.aspx?startid=… — folder browse

- **URL:** `https://weblink.auburndalefl.com/WebLink/Browse.aspx?dbid=0&startid=<folderId>`
- **Data available:** Document folder contents for the `CityOfAuburndale` repo. Observed folder IDs: `38271` (Commission Agendas), `433` (Commission Minutes). Other folders not enumerated.
- **Fields extractable:** (after JS hydration) document name, date, type, size, folder hierarchy, document ID for `DocView.aspx`.
- **JavaScript required:** `yes` — Angular SPA; empty HTML shell is returned until `app.bundle.js` hydrates with cookie `WebLinkSession`. `MachineTag` and `AcceptsCookies` cookies required.
- **Anti-bot measures:** cookie gate (`AcceptsCookies=1` required); no captcha observed; no IP rate limiting at ~1 req/sec.
- **Pagination:** pagination controls render in the Angular UI after hydration — underlying API route not yet characterized.
- **Selectors (if stable):** Angular view components — volatile; re-inspect on each WebLink upgrade.
- **Why no API:** WebLink 10's JSON surface lives behind Angular services (`FolderListingService`, `DocumentService`, `SearchService`, `CustomSearchService`) whose URL templates are obfuscated in the JS bundle. Direct `/WebLink/api/*` probes (`GetEntry`, `GetChildren`) return 404 — the real endpoint paths are not plain in the bundle.
- **Notes:** ⚠️ GAP: underlying JSON API not enumerated; next pass should capture XHR via headless browser. Legacy `/weblink8/Browse.aspx?dbid=0&startid=<id>` URLs (used in the CMS meeting-page links) HTTP-rewrite via client-side JS to `/WebLink/Browse.aspx?dbid=0&startid=<id>`.

#### /WebLink/DocView.aspx?id=… — document view

- **URL:** `https://weblink.auburndalefl.com/WebLink/DocView.aspx?dbid=0&id=<docId>`
- **Data available:** Per-document viewer for the `CityOfAuburndale` repo.
- **Fields extractable:** document metadata (title, pages, type, template fields), inline PDF/image viewer. Hydrated client-side.
- **JavaScript required:** `yes`.
- **Anti-bot measures:** same cookie gate as Browse.aspx.
- **Pagination:** document-page pagination in the viewer.
- **Selectors (if stable):** Angular — volatile.
- **Why no API:** same as Browse.aspx — JSON surface obfuscated.
- **Notes:** Per the app bundle, sibling aspx entry points exist: `/WebLink/Search.aspx`, `/WebLink/CustomSearch.aspx?SearchName=<name>`, `/WebLink/PdfViewer.aspx?file=…`, `/WebLink/EmailDocument.aspx?id=…`, `/WebLink/MyWebLink.aspx`, `/WebLink/Welcome.aspx`. All are SPA entry points.

### `auburndalefl.govbuilt.com` (GovBuilt HTML pages)

#### /PublicReport/GetAllCaseDetailsData/{contentItemId} — case detail report

- **URL:** `https://auburndalefl.govbuilt.com/PublicReport/GetAllCaseDetailsData/<contentItemId>`
- **Data available:** Full case detail (permit history, fees, inspection log, plan review comments) for cases where `showCaseDetailsReport: true` on the search result.
- **Fields extractable:** fees, inspections, review comments, applicant/owner/contractor parties, tied contracts.
- **JavaScript required:** partial — depends on the report template.
- **Anti-bot measures:** `ARRAffinity` cookies + Cloudflare; no captcha.
- **Pagination:** single page per case.
- **Selectors (if stable):** Orchard Core widget-based — unstable across config changes.
- **Why no API:** the `GetCaseOrLicenseInspectionsByCaseIdOrLicenseId` JSON endpoint exists but needs an anti-forgery token not yet captured; until that's solved, the HTML report is the fallback.
- **Notes:** Most records have `showCaseDetailsReport: false`, suppressing the link.

### `ci-auburndale-fl.validation.smartgovcommunity.com` (SmartGov — secondary/legacy)

#### /Public/Home — SmartGov landing

- **URL:** `https://ci-auburndale-fl.validation.smartgovcommunity.com/Public/Home`
- **Data available:** Granicus SmartGov citizen-portal landing with tiles for Permits, Applications, Licenses, Reports. Public Notices widget. Case-search requires auth.
- **Fields extractable:** (anonymous) branding text, tile list, public-notices widget content.
- **JavaScript required:** `no` for the landing; `yes` for deeper search.
- **Anti-bot measures:** none observed at landing.
- **Pagination:** `none`
- **Selectors (if stable):** standard SmartGov markup — `.widget-title`, `.widget-content`.
- **Why no API:** deep permit search gated; landing is purely informational for Auburndale's tenant. GovBuilt carries the live dataset.
- **Notes:** `.validation.` subdomain indicates a staging / tenant-validation environment. Auburndale's construction-services page keeps a tile for it (legacy-migration affordance) but the primary flow is GovBuilt. ⚠️ GAP: whether the validation tenant carries real data is unverified; treat as legacy/stubbed until confirmed.

---

## External Platforms (linked, not crawled)

These are documented in their own per-platform references in `_platforms.md`. Auburndale-specific tenant IDs are noted.

- **Municode Library** (`library.municode.com`, `api.municode.com`) — code of ordinances for Auburndale; `clientId=10379`. See `cd2/adapters/municode.py`.
- **Polk County Property Appraiser** (`polkpa.org`) — parcel/ownership data for Auburndale parcels; see `polk-county-fl.md`.
- **PRWC — Polk Regional Water Cooperative** (`prwcwater.org`) — potable water wholesaler linked from utilities pages.
- **SWFWMD e-Permitting** (`swfwmd.state.fl.us/business/epermitting/local-government-water-restrictions`) — regional water-use restrictions; state-level platform.
- **EyeOnWater** (`helpeyeonwater.com`) — AMI meter reading tenant portal; requires resident login.
- **Auburndale Chamber of Commerce** (`myauburndalechamber.com`) — non-governmental; out of scope.
- **Polk County parent infrastructure** — PolkPA, Polk GIS, Polk Legistar — see `polk-county-fl.md`.

---

## Coverage Notes

- **robots.txt** (auburndalefl.com): `User-Agent: * \n Disallow:` — fully permissive. Evidence: `evidence/auburndale-fl-robots.txt`.
- **robots.txt for other hosts:** not probed (`utility.auburndalefl.com`, `weblink.auburndalefl.com`, `auburndalefl.govbuilt.com`, `ci-auburndale-fl.validation.smartgovcommunity.com`). ⚠️ GAP: next pass should capture.
- **Total HTTPS requests this run:** 74 (well under the 2000 cap).
- **429 events:** 0.
- **CAPTCHA events:** 0.
- **Cloudflare WAF blocks:** 1 — `POST /xmlrpc.php` → HTTP 403 "Attention Required! | Cloudflare". Standard Cloudflare Super Bot Fight Mode behavior; GoDaddy MWP applies this by default on XML-RPC. Documented, not circumvented.
- **New platforms added to `_platforms.md` this run:** GovBuilt (MCC Innovations), Laserfiche WebLink 10, American Data Group UBS, SmartGov Public Portal (Granicus).
- **Permit portal finding (explicit):** ⭐ **Auburndale DOES have a live online permit portal** — **GovBuilt** at `https://auburndalefl.govbuilt.com/`. Public JSON API at `/PublicReport/GetAllContentToolModels` exposes **30,142 cases + 716 licenses** with applicant names, full addresses (incl. GPS), phones, business names, case numbers, and status. A parallel SmartGov tenant exists on the `.validation.` staging subdomain but is not the live primary.
- **Utility-subdomain vendor (explicit):** **American Data Group (ADG)** — `utility.auburndalefl.com/ubs1/`. Login-gated utility billing portal; PHP/8.3 on Microsoft-IIS/10.0. Signatures: `/adg-custom-site/`, `/adg/supporting/`, meta copyright "American Data Group". Not a Tyler / PSN / InvoiceCloud tenant.
- **Records archive (explicit):** Laserfiche WebLink 10 on `weblink.auburndalefl.com`, repo `CityOfAuburndale`, `dbid=0`. Commission agendas folder `startid=38271`; Commission minutes `startid=433`. Angular SPA; JSON API not yet characterized (⚠️ GAP).
- **Deferred per §6/§7:**
  - ⚠️ GAP: WebLink 10 JSON API routes (obfuscated in `app.bundle.js`; need headless-browser XHR capture).
  - ⚠️ GAP: GovBuilt `GetCaseSubTypesByTypeId`, `GetLicenseSubTypesByTypeId` response shapes (need real `*TypeId` arguments from allowed-type catalog).
  - ⚠️ GAP: GovBuilt `GetCaseOrLicenseInspectionsByCaseIdOrLicenseId` needs anti-forgery token + possibly POST method.
  - ⚠️ GAP: `/wp-json/tec/v1/events` shape not probed (only namespace root); expected to mirror `/tribe/events/v1/events`.
  - ⚠️ GAP: `/wp-json/oembed/1.0/embed` response shape not captured in evidence (standard oEmbed 1.0).
  - ⚠️ GAP: SmartGov `.validation.` tenant — whether carrying real data vs stub.
  - ⚠️ GAP: robots.txt not captured for non-CMS hostnames.
