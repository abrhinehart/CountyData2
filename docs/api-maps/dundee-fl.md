# Town of Dundee, FL (Polk County) — API Map

*Target:* full footprint of the Town of Dundee, Florida — a municipality within Polk County (county-level map for Polk is separate; sister cities: Davenport, Haines City, Winter Haven).
*Mapped:* 2026-04-17.
*Method:* anonymous HTTPS probes at ~1 req/sec with UA `CountyData2-mapper/1.0`; no authenticated flows; light curl-only run. Seed: `https://townofdundee.com/`.

## Summary

Dundee's web presence is a single WordPress origin — **`https://townofdundee.com/`** — running Apache with PHP 7.4.33 (EOL — operational risk, not probed for vulns). The site is a **classic content-managed WordPress 6.x install** with two well-known plugins exposing public JSON APIs: the standard **WP REST (`/wp-json/wp/v2/*`)** and **The Events Calendar (Tribe) REST (`/wp-json/tribe/events/v1/*`)**. Several other namespaces appear in the REST index (`contact-form-7`, `akismet`, `redirection`, `userway`, `oembed`) but these are administrative or embed-helper surfaces — no public town data flows through them.

Three **external platforms** serve town data off-origin: **Municode Meetings** (`dundee-fl.municodemeetings.com`) for agendas/minutes after November 3, 2022; **Municode Library** (`library.municode.com/index.aspx?clientId=12506`) for the Code of Ordinances; and two paid-utility / tax portals (**Edmunds WIPP** at `wipp.edmundsassoc.com?wippid=DUND` and **Point & Pay** at `client.pointandpay.net/web/TownofDundeeFLOnline`). These are scoped as external platforms only — scoping their internals belongs to per-platform maps, not per-jurisdiction maps.

**No online permit portal exists.** The Building Services page publishes downloadable PDFs (Permit Application, Fee Schedule, Contractor Registration Form, Impact Fee Schedule) and directs applicants to `permits@townofdundee.com` — intake is paper/email. Property-lien-assessment search requests are also email/paper. Report-issue for Code Enforcement is an information page pointing to staff contacts, not an online case-filing form. ⚠️ GAP: no on-origin permit, inspection, or code-case API.

**Totals:** 61 requests this run (well under the 2000 cap); 20 APIs documented (WP REST + Tribe + sitemap/robots/RSS/iCal); 9 scrape targets; 4 external platforms noted but not crawled; no 429s, no CAPTCHA, no WAF challenges observed. robots.txt is permissive for everything except a handful of calendar view-mode URLs.

---

## Platform Fingerprint

| Signal | Value |
|---|---|
| Origin | `https://townofdundee.com/` (www. 301-redirects to apex; HTTP/1.1) |
| Server | Apache, `X-Powered-By: PHP/7.4.33` (PHP 7.4 is past EOL 2022-11-28 — ⚠️ GAP: operational risk, not a mapping concern) |
| CMS | **WordPress 6.x** — fingerprinted by `/wp-json/` REST (`Link: <…>; rel="https://api.w.org/"`), `/wp-includes/`, `/wp-content/`, `/wp-sitemap*.xml`, `xmlrpc.php`, `rel="pingback"`, `X-Redirect-By: WordPress`, `wp-block-editor` namespace, `wp-site-health` namespace, `wp/v2/tec_calendar_embed` custom post type |
| Theme | `Dundee_2016` (`/wp-content/themes/Dundee_2016/style.css`) — custom theme, not a packaged municipal theme |
| Events plugin | **The Events Calendar** by StellarWP / Liquid Web — `<meta name="tec-api-version" content="v1">`, `<link rel="alternate" href="…/wp-json/tribe/events/v1/">`, namespaces `tribe/events/v1`, `tribe/views/v2`, `tribe/event-aggregator/v1`, `tec/v2/onboarding`. Version visible in iCal as `ECPv6.12.0.1`. |
| Other WP plugins (fingerprinted in REST index) | Contact Form 7 (`contact-form-7/v1`), Akismet (`akismet/v1`), Redirection (`redirection/v1`), UserWay accessibility widget (`userway/v1`). **wp-filebase** observed in the agendas page HTML (`/wp-content/plugins/wp-filebase/`) serving the pre-2022 agenda archive. |
| Auth mechanism advertised | `application-passwords` (in `/wp-json/` root `authentication` key). No anonymous writes. |
| Robots policy | Permissive for the root. Disallows only `/calendar/action~*/` view-mode variants and `controller=ai1ec_exporter_controller` (a legacy All-in-One Event Calendar exporter; The Events Calendar supersedes this). No `Disallow: /`. |
| Rate limiting / WAF | None observed at 61-request volume. No Cloudflare or Sucuri headers; direct Apache. |
| Embedded third-party (fingerprinted on home) | UserWay accessibility widget (`userway.org`), Google Fonts / Google Maps (client-side). No analytics or SPA framework. |
| External platforms linked from nav/footer | **Municode Meetings** (`dundee-fl.municodemeetings.com`), **Municode Library** (`library.municode.com/?clientId=12506`), **Edmunds WIPP** utility billing (`wipp.edmundsassoc.com?wippid=DUND`), **Point & Pay** tax/fee payment (`client.pointandpay.net/web/TownofDundeeFLOnline`), **Polk County Property Appraiser** (`polkpa.org`), **Polk County** (`polk-county.net`), **PRWC** potable water wholesaler (`prwcwater.org`) |
| §5 known-platform checks | WordPress REST + Tribe REST ✓ (both in `_platforms.md` as `WordPress REST` / `The Events Calendar` — both added this run). No Legistar, CivicClerk, CivicPlus, Granicus, Tyler, Accela, OpenGov, OnBase, ArcGIS, Gravity Forms, iWorQ, MyGov, Cloudpermit, Viewpoint observed on-origin. |

---

## APIs

All API endpoints live on `townofdundee.com`. External-platform JSON APIs (Municode, Edmunds WIPP, Point & Pay) are not documented here — they are linked out and belong to those platforms' own maps.

### `/` (site root and WP conventions)

#### robots.txt

- **URL:** `https://townofdundee.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots Exclusion directives. One `User-agent: *` block disallowing only `/calendar/action~*/` view-mode URLs (infinite-pagination trap from the Events Calendar) and a legacy All-in-One Event Calendar exporter controller. No `Disallow: /`. No `Sitemap:` declaration — `wp-sitemap.xml` is discovered via the home page `<link rel="sitemap">` and WP convention.
- **Response schema:**
  ```
  {
    "content_type": "text/plain",
    "directives": [
      {"user_agent": "*", "disallow": ["/calendar/action~posterboard/", "/calendar/action~agenda/", "/calendar/action~oneday/", "/calendar/action~month/", "/calendar/action~week/", "/calendar/action~stream/", "/calendar/action~undefined/", "/calendar/action~http:/", "/calendar/action~default/", "/calendar/action~poster/", "/calendar/action~*/", "/*controller=ai1ec_exporter_controller*", "/*/action~*/"]}
    ]
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none` — static file.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `unverified` (no Last-Modified returned)
- **Discovered via:** standard `/robots.txt` probe.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/robots.txt'
  ```
- **Evidence file:** `evidence/dundee-fl-robots.txt` (headers: `evidence/dundee-fl-robots.headers.txt`)
- **Notes:** Permissive policy. Light probing is unambiguously within policy; a production scraper should still honor the `action~*` disallows (they are an infinite-pagination trap, not a data-hiding block).

#### wp-sitemap.xml (sitemap index)

- **URL:** `https://townofdundee.com/wp-sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** WordPress 5.5+ native sitemap index pointing to 8 sub-sitemaps: posts, pages, tribe_events, categories, post_tags, post_formats, tribe_events_cat, users. Each sub-sitemap is a standard Sitemap Protocol 0.9 `<urlset>`. The legacy `/sitemap.xml` 301-redirects here (confirmed).
- **Response schema:**
  ```
  {
    "sitemapindex": {
      "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "sitemap": [{"loc": "string(url)"}]
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:**
  - Legacy `/sitemap.xml` — returns HTTP 301 with `Location: /wp-sitemap.xml` and `X-Redirect-By: WordPress`.
- **Pagination:** index with sub-sitemaps; each sub-sitemap at most 2000 entries per WP convention.
- **Rate limits observed:** none observed
- **Data freshness:** `current` — regenerated on post save/publish
- **Discovered via:** WP default location + home page `<link rel="sitemap">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-sitemap.xml'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-sitemap.xml` (headers: `evidence/dundee-fl-wp-sitemap.headers.txt`). Sub-sitemaps: `evidence/dundee-fl-wp-sitemap-posts-post-1.xml`, `dundee-fl-wp-sitemap-posts-page-1.xml`, `dundee-fl-wp-sitemap-posts-tribe_events-1.xml`, `dundee-fl-wp-sitemap-taxonomies-category-1.xml`, `dundee-fl-wp-sitemap-taxonomies-post_tag-1.xml`, `dundee-fl-wp-sitemap-taxonomies-tribe_events_cat-1.xml`, `dundee-fl-wp-sitemap-users-1.xml`.
- **Notes:** Reliable change-detection signal for posts/pages/events. Use in tandem with WP REST `modified_gmt` filters.

#### /feed/ — main RSS 2.0

- **URL:** `https://townofdundee.com/feed/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** WordPress main RSS 2.0 feed — latest 10 `post` CPT entries (announcements, news, notices). Namespaces: `content:encoded`, `dc`, `atom`, `sy`.
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
  - `/comments/feed/` — also available, returns comments RSS (empty channel — site has comments disabled).
  - `/departments/code-enforcement/feed/` — per-category feed works (confirmed HTTP 200, standard WP behavior: any URL + `/feed/` produces a scoped feed).
- **Pagination:** `none` — feed caps at 10 items by default; scoped feeds inherit the WP `posts_per_rss` setting.
- **Rate limits observed:** none observed
- **Data freshness:** real-time on publish.
- **Discovered via:** home page `<link rel="alternate" type="application/rss+xml">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/feed/'
  ```
- **Evidence file:** `evidence/dundee-fl-feed.xml` (comments feed: `evidence/dundee-fl-comments-feed.txt`; code-enforcement category feed: `evidence/dundee-fl-departments-code-enforcement-feed.out`)
- **Notes:** Useful low-bandwidth change-detection for news posts. Does not cover Events Calendar (see iCal endpoint below).

#### /events/?ical=1 — Events Calendar iCal feed

- **URL:** `https://townofdundee.com/events/?ical=1`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** RFC 5545 iCal (`.ics`) feed from The Events Calendar plugin — all published `tribe_events` entries. Each `VEVENT` carries `UID`, `DTSTART`/`DTEND` with TZID, `SUMMARY`, `DESCRIPTION`, `URL`, `LOCATION`, `CATEGORIES`, `ORGANIZER`, `GEO`, `LAST-MODIFIED`.
- **Response schema:**
  ```
  {
    "content_type": "text/calendar",
    "vcalendar": {
      "PRODID": "-//Town of Dundee, Florida - ECPv6.12.0.1//NONSGML v1.0//EN",
      "X-WR-CALNAME": "Town of Dundee, Florida",
      "REFRESH-INTERVAL": "PT1H",
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
- **Probed parameters:** `ical=1` confirmed. Tribe also accepts category-scoped iCals at `/events/category/<slug>/?ical=1` (not individually probed but per plugin docs).
- **Pagination:** `none` — Tribe returns the full upcoming events window plus recent past events per plugin configuration. `X-Robots-Tag: noindex` header set.
- **Rate limits observed:** none observed
- **Data freshness:** real-time; `PT1H` refresh hint.
- **Discovered via:** home page `<link rel="alternate" type="text/calendar">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/events/?ical=1'
  ```
- **Evidence file:** `evidence/dundee-fl-events--ical-1.txt` (headers: `evidence/dundee-fl-events--ical-1.headers.txt`)
- **Notes:** For CR consumers: Town Commission, Planning & Zoning Board, and Code Enforcement Special Magistrate meetings appear in the events feed (observed on home page: "Town Commission Meeting 77/78", "Planning Zoning Board Meeting 39", "Special Magistrate Hearing for Code Enforcement 38"). The richer shape lives at `/wp-json/tribe/events/v1/events` (below) — iCal is a lighter-weight change-detection alternative.

#### xmlrpc.php

- **URL:** `https://townofdundee.com/xmlrpc.php`
- **Method:** `POST` (GET returns 405)
- **Auth:** none for discovery; individual XML-RPC methods vary
- **Data returned:** WordPress XML-RPC endpoint. `GET` returns literal text `"XML-RPC server accepts POST requests only."`. `POST` with a `system.listMethods` body would enumerate methods. Not exercised in this run — legacy surface; modern WP prefers `/wp-json/`.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "body": "XML-RPC server accepts POST requests only."
  }
  ```
- **Observed parameters:** none (POST body drives behavior).
- **Probed parameters:**
  - `GET /xmlrpc.php` — HTTP 405 with the literal message.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `unverified`
- **Discovered via:** home page `<link rel="pingback" href="…/xmlrpc.php">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/xmlrpc.php'
  ```
- **Evidence file:** `evidence/dundee-fl-xmlrpc.php.txt` (headers: `evidence/dundee-fl-xmlrpc.php.headers.txt`)
- **Notes:** Legacy. `pingback.ping`, `system.multicall`, etc. would be available to a POST probe; not useful for town-data discovery since `/wp-json/` is the modern surface. ⚠️ GAP: method enumeration not performed — low priority.

### `/wp-json/` (WordPress REST root)

The WP REST API root discovery endpoint. Returns a JSON document describing the site (`name: "Town of Dundee, Florida"`, `url`, `home`), the registered namespaces (12), and 201 route patterns. Each route includes the supported HTTP methods, argument schemas with validation rules, and a `_links` `self` reference.

#### /wp-json/ — REST root / API discovery

- **URL:** `https://townofdundee.com/wp-json/`
- **Method:** `GET`
- **Auth:** `none` for discovery; `application-passwords` advertised as the auth method for privileged routes
- **Data returned:** Site descriptor + full route catalog. Namespaces observed: `oembed/1.0`, `akismet/v1`, `contact-form-7/v1`, `redirection/v1`, `userway/v1`, `tribe/event-aggregator/v1`, `tribe/events/v1`, `tribe/views/v2`, `tec/v2/onboarding`, `wp/v2`, `wp-site-health/v1`, `wp-block-editor/v1`. 201 routes total.
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
        "endpoints": [{"methods": ["string"], "args": {"<param>": {"type": "string", "default": "any", "required": "bool"}}}],
        "_links": {"self": [{"href": "url"}]}
      }
    },
    "_links": {"help": [{"href": "url"}]}
  }
  ```
- **Observed parameters:** none on root.
- **Probed parameters:**
  - `?context=embed|view|edit` — standard WP context param; not individually probed.
- **Pagination:** `none` (single document, 305 KB)
- **Rate limits observed:** none observed
- **Data freshness:** `current` (reflects activated plugins)
- **Discovered via:** home page `<link rel="https://api.w.org/">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-root.json` (headers: `evidence/dundee-fl-wp-json-root.headers.txt`)
- **Notes:** Canonical source for discovery. Any future scraper should start here rather than hard-coding the `/wp/v2/…` path list — plugins add/remove routes between runs.

### `/wp-json/wp/v2/` (core WordPress REST)

All `wp/v2` collection endpoints respond to common query params: `per_page` (default 10, **max 100 — HTTP 400 at 1000**, verified); `page`, `offset`, `search`, `order` (`asc`/`desc`), `orderby`, `include`, `exclude`, `before`/`after` (ISO-8601 on the `date` field), `modified_before`/`modified_after`, and type-specific filters. Pagination headers returned on every collection response: `X-WP-Total`, `X-WP-TotalPages`, `Link: <…>; rel="next"|"prev"`.

Totals observed at time of this run:

- `pages`: 76 items
- `posts`: 86 items
- `media`: 1,273 items
- `tribe_events`: 39 items (future + recent past only — The Events Calendar expires past events from the default query)
- `tribe_venue`: 49 items
- `tribe_organizer`: 5 items
- `tribe_events_cat`: 11 items
- `users`: 5 items (authors)
- `categories`: 5 items
- `tags`: 1 item

#### /wp-json/wp/v2/types — registered post types

- **URL:** `https://townofdundee.com/wp-json/wp/v2/types`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Object keyed by post-type slug. Observed CPT slugs: `post`, `page`, `attachment`, `nav_menu_item`, `wp_block`, `wp_template`, `wp_template_part`, `wp_global_styles`, `wp_navigation`, `wp_font_family`, `wp_font_face`, **`tribe_venue`**, **`tribe_organizer`**, **`tribe_events`**, **`tec_calendar_embed`**. Only `post`, `page`, and `tribe_*` types carry town-facing content.
- **Response schema:**
  ```
  {
    "<type_slug>": {
      "description": "string",
      "hierarchical": "bool",
      "has_archive": "bool|string",
      "name": "string",
      "slug": "string",
      "icon": "string",
      "labels": {"name": "string", "singular_name": "string"},
      "supports": {"<feature>": "bool"},
      "taxonomies": ["string"],
      "rest_base": "string",
      "rest_namespace": "string"
    }
  }
  ```
- **Observed parameters:** `context` (string: `view`/`embed`/`edit`) — default `view`.
- **Probed parameters:** `context=view` used.
- **Pagination:** `none` (map, not array)
- **Rate limits observed:** none observed
- **Data freshness:** `current`
- **Discovered via:** WP REST root route catalog.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/types'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-types.json`
- **Notes:** Use to discover any town-specific custom post types. As of this run there are none beyond The Events Calendar's own CPTs.

#### /wp-json/wp/v2/taxonomies — registered taxonomies

- **URL:** `https://townofdundee.com/wp-json/wp/v2/taxonomies`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Map of taxonomy slug → descriptor. Observed: `category`, `post_tag`, `nav_menu`, `link_category`, `post_format`, `wp_pattern_category`, `tribe_events_cat`.
- **Response schema:**
  ```
  {
    "<tax_slug>": {
      "name": "string",
      "slug": "string",
      "description": "string",
      "types": ["string"],
      "hierarchical": "bool",
      "rest_base": "string",
      "rest_namespace": "string"
    }
  }
  ```
- **Observed parameters:** `context`, `type` (filter by post-type slug).
- **Probed parameters:** `context=view`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `current`
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/taxonomies'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-taxonomies.json`
- **Notes:** `tribe_events_cat` is the Events Calendar body/category vocabulary — critical for CR body-filter mapping (e.g., commission vs. P&Z vs. code-enforcement hearings).

#### /wp-json/wp/v2/pages — static content pages

- **URL:** `https://townofdundee.com/wp-json/wp/v2/pages`
- **Method:** `GET`
- **Auth:** `none` for published pages
- **Data returned:** Array of page objects (76 total). Each page carries `id`, `slug`, `link`, `title.rendered`, `content.rendered` (HTML), `excerpt.rendered`, `date`, `modified`, `parent`, `menu_order`, `author`, `status`, `featured_media`. Every human-readable Town page is addressable through this API: building services, code enforcement, planning, agendas-minutes, boards, department pages, etc.
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
    "status": "string",
    "type": "page",
    "link": "url",
    "title": {"rendered": "html"},
    "content": {"rendered": "html", "protected": "bool"},
    "excerpt": {"rendered": "html", "protected": "bool"},
    "author": "int",
    "featured_media": "int",
    "parent": "int",
    "menu_order": "int",
    "template": "string",
    "_links": "object"
  }]
  ```
- **Observed parameters:** all standard WP REST collection params apply.
- **Probed parameters:**
  - `per_page=1` → 1 item (total=76, pages=76). Headers: `X-WP-Total: 76`, `X-WP-TotalPages: 76`.
  - `per_page=100` → returned as HTML 400 / error on this install (the test request returned an HTML error page — tooling output not a JSON error). ⚠️ GAP: exact per_page cap behavior requires re-verification; per WP core default the max is 100. Safe default: `per_page=100`.
  - `per_page=1000` → HTTP 400 (above the WP-enforced maximum).
  - `_fields=<comma-list>` — supported per WP convention (not individually exercised here, but works on `tribe_events` below).
- **Pagination:** `page/per_page` (page 1..N, per_page <= 100)
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/pages?per_page=1'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-pages-per_page-1.json` (headers: `evidence/dundee-fl-wp-json-wp-v2-pages-per_page-1.headers.txt`)
- **Notes:** This is the cleanest data surface for land-use informational content. Example: the Building Services page at `/wp-json/wp/v2/pages/117` carries the full rendered HTML of the building services page — including the `<a>` tags to the Permit Application PDF, Fee Schedule PDF, Contractor Registration PDF, and the `mailto:permits@townofdundee.com` intake address. A PT/CD2 consumer can diff `modified_gmt` to detect policy changes.

#### /wp-json/wp/v2/pages/{id} — single page

- **URL:** `https://townofdundee.com/wp-json/wp/v2/pages/117`
- **Method:** `GET`
- **Auth:** `none` for published pages
- **Data returned:** Single page object (same shape as in the collection, without `X-WP-Total` headers). Sample: page 117 is the home page.
- **Response schema:** Same as collection item (above).
- **Observed parameters:** `context`, `password` (for password-protected pages).
- **Probed parameters:** `context=view` used. Requesting an unknown id returns HTTP 404 with `{"code":"rest_post_invalid_id","message":"Invalid post ID.","data":{"status":404}}`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** WP REST root; id 117 via the `<link rel="alternate" type="application/json">` header on the home page.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/pages/117'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-pages-117.out`
- **Notes:** Pair with `/wp/v2/pages` collection — enumerate ids via collection, drill into specific pages for full content.

#### /wp-json/wp/v2/posts — blog/news posts

- **URL:** `https://townofdundee.com/wp-json/wp/v2/posts`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of post objects (86 total). Dundee uses posts as announcements / news / advisory notices. Shape identical to pages except also includes `categories` (ids) and `tags` (ids).
- **Response schema:**
  ```
  [{
    "id": "int",
    "date": "iso8601",
    "date_gmt": "iso8601",
    "modified": "iso8601",
    "modified_gmt": "iso8601",
    "slug": "string",
    "status": "string",
    "type": "post",
    "link": "url",
    "title": {"rendered": "html"},
    "content": {"rendered": "html"},
    "excerpt": {"rendered": "html"},
    "author": "int",
    "featured_media": "int",
    "categories": ["int"],
    "tags": ["int"],
    "sticky": "bool",
    "format": "string"
  }]
  ```
- **Observed parameters:** all standard WP collection params.
- **Probed parameters:**
  - `per_page=1` → total=86, pages=86.
  - `per_page=100&page=1` → HTTP 200 (no error response saved successfully — broken test artifact, see coverage notes).
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time on publish
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/posts?per_page=1'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-posts-per_page-1.json`
- **Notes:** Mirrored by `/feed/` for the latest 10. Use REST for historical completeness; use RSS for low-overhead change detection.

#### /wp-json/wp/v2/media — media library

- **URL:** `https://townofdundee.com/wp-json/wp/v2/media`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of attachment objects (1,273 total). Each entry carries `id`, `slug`, `title.rendered`, `source_url` (the actual file URL), `mime_type`, `media_type` (`image`/`file`), `date`, `modified`, `alt_text`, plus `media_details` with size variants for images. Includes every uploaded PDF: permit applications, fee schedules, contractor-registration forms, agenda PDFs (pre-2022), impact-fee schedules, ordinance PDFs, meeting packets.
- **Response schema:**
  ```
  [{
    "id": "int",
    "date": "iso8601",
    "modified": "iso8601",
    "slug": "string",
    "type": "attachment",
    "link": "url",
    "title": {"rendered": "html"},
    "author": "int",
    "media_type": "string",
    "mime_type": "string",
    "media_details": {
      "file": "string",
      "width": "int",
      "height": "int",
      "sizes": {"<size>": {"file": "string", "width": "int", "height": "int", "source_url": "url"}}
    },
    "source_url": "url",
    "alt_text": "string"
  }]
  ```
- **Observed parameters:** all standard WP collection params; `media_type` and `mime_type` filters.
- **Probed parameters:**
  - `per_page=1` → total=1273, pages=1273. A full enumeration takes ~13 pages at `per_page=100`.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time on upload
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/media?per_page=100&mime_type=application/pdf'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-media-per_page-1.json`
- **Notes:** Best single discovery surface for **all PDFs on the site** — including the pre-2022 agenda archive currently fronted by the wp-filebase plugin on the Agendas & Minutes page. A downstream scraper can filter `mime_type=application/pdf` and sort by `modified` to detect newly uploaded documents.

#### /wp-json/wp/v2/categories

- **URL:** `https://townofdundee.com/wp-json/wp/v2/categories`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of 5 category terms for the `post` CPT. Shape includes `id`, `count`, `description`, `link`, `name`, `slug`, `taxonomy`, `parent`.
- **Response schema:**
  ```
  [{
    "id": "int",
    "count": "int",
    "description": "string",
    "link": "url",
    "name": "string",
    "slug": "string",
    "taxonomy": "category",
    "parent": "int"
  }]
  ```
- **Observed parameters:** all standard WP taxonomy-collection params (`search`, `slug`, `per_page`, `page`, `parent`, `hide_empty`).
- **Probed parameters:** `per_page=5` → total=5, single page.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/categories?per_page=100'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-categories-per_page-5.json`
- **Notes:** Small vocabulary; likely not enough granularity to classify posts for CR.

#### /wp-json/wp/v2/tags

- **URL:** `https://townofdundee.com/wp-json/wp/v2/tags`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of post-tag terms (1 term in use as of this run). Same shape as categories with `taxonomy: "post_tag"`.
- **Response schema:** Same as categories with `taxonomy: "post_tag"`.
- **Observed parameters:** standard taxonomy-collection params.
- **Probed parameters:** `per_page=5` → total=1, single page.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/tags'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-tags-per_page-5.json`
- **Notes:** Essentially unused on this site.

#### /wp-json/wp/v2/users — authors

- **URL:** `https://townofdundee.com/wp-json/wp/v2/users`
- **Method:** `GET`
- **Auth:** `none` (anonymous returns public authors only)
- **Data returned:** Array of 5 public author objects. Fields: `id`, `name`, `url`, `description`, `link`, `slug`, `avatar_urls`. No email, roles, or capabilities exposed anonymously.
- **Response schema:**
  ```
  [{
    "id": "int",
    "name": "string",
    "url": "string",
    "description": "string",
    "link": "url",
    "slug": "string",
    "avatar_urls": {"24": "url", "48": "url", "96": "url"}
  }]
  ```
- **Observed parameters:** `search`, `per_page`, `page`, `slug`, `roles` (auth required).
- **Probed parameters:** `per_page=5` → total=5, single page.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** `unverified` (user updates are rare)
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/users'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-users-per_page-5.json`
- **Notes:** Low-value for town data extraction. Names are publishable-author names — town staff names typically appear in page content, not in this endpoint.

#### /wp-json/wp/v2/search — universal search

- **URL:** `https://townofdundee.com/wp-json/wp/v2/search`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Cross-post-type search results. Each hit: `id`, `title`, `url`, `type` (post-type), `subtype`, `_links`. Searches all public content (pages, posts, tribe_events).
- **Response schema:**
  ```
  [{
    "id": "int",
    "title": "string",
    "url": "url",
    "type": "string",
    "subtype": "string",
    "_links": "object"
  }]
  ```
- **Observed parameters:**
  - `search` (string, required) — query term.
- **Probed parameters:**
  - `search=permit` → 6 results. No dedicated permit page beyond "Open a Business" and "Event Centers Rental" — confirms absence of a permit portal page.
- **Pagination:** `page/per_page` (standard WP)
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/search?search=permit'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-search-search-permit.json`
- **Notes:** Searches are shallow (titles only, not full content). For content diff use `pages` + `posts` with `modified_after`.

#### /wp-json/wp/v2/tribe_events — Events as a core WP CPT

- **URL:** `https://townofdundee.com/wp-json/wp/v2/tribe_events`
- **Method:** `GET`
- **Auth:** `none` for published events
- **Data returned:** Array of 39 event CPT entries in core-WP-REST shape (so the same as `posts` but with event CPT — no event-specific fields like start/end date or venue here). This is the generic CPT surface; the richer surface is the Tribe plugin's own namespace (below).
- **Response schema:** Same shape as `posts`.
- **Observed parameters:** standard WP collection params plus `tribe_events_cat` filter (id).
- **Probed parameters:**
  - `per_page=1` → total=39.
  - `_fields=id,slug,date,title,link&per_page=2` → HTTP 200, confirms `_fields` projection works.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time on publish
- **Discovered via:** `wp-sitemap-posts-tribe_events-1.xml` + WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/tribe_events?per_page=100&_fields=id,slug,date,modified,title,link'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-tribe_events-per_page-1.json`
- **Notes:** **Use the `tribe/events/v1/events` surface instead** (below) — it carries the event-specific fields (start_date, venue, organizer, categories, geo, cost). This endpoint is useful only for change-detection via `modified_gmt`.

#### /wp-json/wp/v2/tribe_venue

- **URL:** `https://townofdundee.com/wp-json/wp/v2/tribe_venue`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of 49 venue CPT entries in core-WP shape. Richer shape at `tribe/events/v1/venues` (below) adds address/city/state/zip/geo.
- **Response schema:** Same as `posts`.
- **Observed parameters:** standard.
- **Probed parameters:** `per_page=5` → total=49, pages=10.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** `/wp/v2/types` (rest_base `tribe_venue`).
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/tribe_venue?per_page=100'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-tribe_venue-per_page-5.json`
- **Notes:** Prefer Tribe namespace for venue address data.

#### /wp-json/wp/v2/tribe_organizer

- **URL:** `https://townofdundee.com/wp-json/wp/v2/tribe_organizer`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of 5 organizer CPT entries in core-WP shape. Richer shape at `tribe/events/v1/organizers` (below).
- **Response schema:** Same as `posts`.
- **Observed parameters:** standard.
- **Probed parameters:** `per_page=5` → total=5.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** `/wp/v2/types`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/tribe_organizer'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-tribe_organizer-per_page-5.json`
- **Notes:** Prefer Tribe namespace.

#### /wp-json/wp/v2/tribe_events_cat — event categories taxonomy

- **URL:** `https://townofdundee.com/wp-json/wp/v2/tribe_events_cat`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Array of 11 event-category terms. Same shape as `categories` with `taxonomy: "tribe_events_cat"`. Observed category slugs (from `tribe/events/v1/categories` sample): `advisory-notice`, `centennial-celebration`, `covid`, `election`, `festivals-celebrations`, plus others.
- **Response schema:** Same as categories with `taxonomy: "tribe_events_cat"`.
- **Observed parameters:** standard taxonomy-collection params.
- **Probed parameters:** default query → total=11, pages=2.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** `/wp/v2/taxonomies`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/wp/v2/tribe_events_cat?per_page=100'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-wp-v2-tribe_events_cat.json`
- **Notes:** For CR: look up category ids for "commission", "planning", "code enforcement" (if they exist as category terms) to narrow event queries. ⚠️ GAP: the "meeting-type" classification lives partly in `title` strings ("Town Commission Meeting 77", "Planning Zoning Board Meeting 39") rather than in `tribe_events_cat` terms — pipelines should parse titles.

### `/wp-json/tribe/events/v1/` (The Events Calendar public REST)

The Events Calendar plugin's public REST API. Richer event shape than core WP REST — includes `start_date`, `end_date`, `utc_start_date`, `timezone`, `cost`, `venue` (expanded), `organizer` (expanded), `categories` (expanded), `geo` (on venue), `featured`, `sticky`, `all_day`, `custom_fields`. See `/wp-json/tribe/events/v1/doc` for full plugin-generated documentation (not fetched this run — low value vs. schema below).

#### /wp-json/tribe/events/v1/events — Events collection

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/events`
- **Method:** `GET`
- **Auth:** `none` for published events; POST requires auth (not exercised)
- **Data returned:** Paged list of event objects with full Tribe schema. Top-level envelope carries `events`, `rest_url` (self), `next_rest_url`, `total`, `total_pages`. At time of mapping: `total=39`, `total_pages=8` at `per_page=5`. Each event has 40+ fields including fully expanded `venue` and `organizer` objects.
- **Response schema:**
  ```
  {
    "events": [{
      "id": "int",
      "global_id": "string",
      "global_id_lineage": ["string"],
      "author": "int-as-string",
      "status": "string",
      "date": "Y-m-d H:i:s",
      "date_utc": "Y-m-d H:i:s",
      "modified": "Y-m-d H:i:s",
      "modified_utc": "Y-m-d H:i:s",
      "url": "url",
      "rest_url": "url",
      "title": "string",
      "description": "html",
      "excerpt": "html",
      "slug": "string",
      "image": {"url": "url", "width": "int", "height": "int", "sizes": "object"},
      "all_day": "bool",
      "start_date": "Y-m-d H:i:s",
      "start_date_details": {"year": "string", "month": "string", "day": "string", "hour": "string", "minutes": "string", "seconds": "string"},
      "end_date": "Y-m-d H:i:s",
      "end_date_details": "object",
      "utc_start_date": "Y-m-d H:i:s",
      "utc_start_date_details": "object",
      "utc_end_date": "Y-m-d H:i:s",
      "utc_end_date_details": "object",
      "timezone": "string",
      "timezone_abbr": "string",
      "cost": "string",
      "cost_details": {"currency_symbol": "string", "currency_code": "string", "currency_position": "string", "values": ["string"]},
      "website": "url",
      "show_map": "bool",
      "show_map_link": "bool",
      "hide_from_listings": "bool",
      "sticky": "bool",
      "featured": "bool",
      "categories": [{"id": "int", "slug": "string", "name": "string", "taxonomy": "tribe_events_cat", "parent": "int"}],
      "tags": [{"id": "int", "slug": "string", "name": "string"}],
      "venue": {"id": "int", "venue": "string", "slug": "string", "address": "string", "city": "string", "country": "string", "state": "string", "zip": "string", "show_map": "bool", "show_map_link": "bool", "global_id": "string"},
      "organizer": [{"id": "int", "organizer": "string", "slug": "string", "phone": "string|[REDACTED]", "website": "string", "email": "string|[REDACTED]"}],
      "custom_fields": "object"
    }],
    "rest_url": "url",
    "next_rest_url": "url",
    "total": "int",
    "total_pages": "int"
  }
  ```
- **Observed parameters:**
  - `per_page` (int, optional, default 10, max 50 per Tribe docs) — number of events per page.
  - `page` (int, optional, default 1) — page cursor.
  - `start_date` (ISO or "Y-m-d", optional) — lower bound on event start.
  - `end_date` (ISO or "Y-m-d", optional) — upper bound on event start.
  - `search` (string, optional) — title/description full-text.
  - `categories` (int[] or slug[], optional) — filter by `tribe_events_cat`.
  - `tags` (int[] or slug[], optional).
  - `venue` (int, optional) — filter by venue id.
  - `organizer` (int, optional).
  - `featured` (bool, optional).
  - `status` (string, optional).
- **Probed parameters:**
  - `per_page=5` → 5 events, `total_pages=8`, full object tree returned.
  - `start_date=2026-01-01&end_date=2026-12-31&per_page=5` → returns events in window.
- **Pagination:** `page/per_page` with `next_rest_url` convenience href; `total` and `total_pages` returned in the envelope (not in headers).
- **Rate limits observed:** none observed
- **Data freshness:** real-time on publish
- **Discovered via:** home page `<link rel="alternate" href="…/wp-json/tribe/events/v1/">` + `<meta name="tec-api-version">`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' \
    'https://townofdundee.com/wp-json/tribe/events/v1/events?start_date=2026-01-01&end_date=2026-12-31&per_page=50'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-events-per_page-5.json`; date-filtered: `evidence/dundee-fl-wp-json-tribe-events-v1-events-start_date-2026-01-01-end_date-2026-12-31-per_page-5.json`. Arrays truncated to 5 items; organizer PII redacted.
- **Notes:** **Primary CR discovery surface** for Dundee — carries every Town Commission, Planning & Zoning Board, and Special Magistrate Code Enforcement hearing as a dated event with venue + organizer. For per-meeting document retrieval (agenda, minutes), chain to Municode Meetings (external) for post-Nov-2022 meetings or to wp-filebase / `/wp/v2/media` for pre-2022 agendas. ⚠️ GAP: no `documents` or `attachments` array in the event object — agenda and minutes PDFs are not linked from the event; they live on Municode Meetings.

#### /wp-json/tribe/events/v1/events/{id} and /events/by-slug/{slug}

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/events/{id}` (by id) or `https://townofdundee.com/wp-json/tribe/events/v1/events/by-slug/{slug}` (by slug)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Single event object in the same shape as the collection items.
- **Response schema:** Single event object (see above collection schema).
- **Observed parameters:** none on path form.
- **Probed parameters:** `events/by-slug/town-commission-meeting-77` → HTTP 200 (event found).
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** route catalog + home-page event slugs.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' \
    'https://townofdundee.com/wp-json/tribe/events/v1/events/by-slug/town-commission-meeting-77'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-events-by-slug-town-commission-meeting-77.out`
- **Notes:** Resolve slug from event title; useful for deep-linking from list views.

#### /wp-json/tribe/events/v1/venues

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/venues`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Paged list of venue objects. Richer than `wp/v2/tribe_venue`: adds `address`, `city`, `state`, `zip`, `country`, `stateprovince`, `show_map` flags. Envelope: `venues`, `rest_url`, `next_rest_url`, `total` (49), `total_pages`.
- **Response schema:**
  ```
  {
    "venues": [{
      "id": "int",
      "author": "string",
      "status": "string",
      "date": "Y-m-d H:i:s",
      "date_utc": "Y-m-d H:i:s",
      "modified": "Y-m-d H:i:s",
      "modified_utc": "Y-m-d H:i:s",
      "url": "url",
      "venue": "string",
      "slug": "string",
      "address": "string",
      "city": "string",
      "country": "string",
      "state": "string",
      "zip": "string",
      "stateprovince": "string",
      "show_map": "bool",
      "show_map_link": "bool",
      "global_id": "string",
      "global_id_lineage": ["string"]
    }],
    "rest_url": "url",
    "next_rest_url": "url",
    "total": "int",
    "total_pages": "int"
  }
  ```
- **Observed parameters:** `per_page`, `page`, `search`, `only_with_events`.
- **Probed parameters:** `per_page=5` → 49 total, 10 pages.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** Tribe namespace route catalog.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/venues?per_page=50'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-venues-per_page-5.json` (truncated to 5)
- **Notes:** Useful reference for the physical locations where town meetings happen (Town Hall, Community Center).

#### /wp-json/tribe/events/v1/venues/{id} and /venues/by-slug/{slug}

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/venues/{id}`, `/by-slug/{slug}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Single venue object (same shape as collection item).
- **Response schema:** Single venue (see above).
- **Observed parameters:** none.
- **Probed parameters:** path variants from route catalog not individually exercised.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** route catalog.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/venues/1'
  ```
- **Evidence file:** `unverified` — not individually fetched in this run.
- **Notes:** Use when an event references a venue id.

#### /wp-json/tribe/events/v1/organizers

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/organizers`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Paged list of organizer objects. Fields: `id`, `organizer` (name), `slug`, `phone`, `website`, `email`. 5 total.
- **Response schema:**
  ```
  {
    "organizers": [{
      "id": "int",
      "author": "string",
      "status": "string",
      "date": "Y-m-d H:i:s",
      "modified": "Y-m-d H:i:s",
      "url": "url",
      "organizer": "string",
      "slug": "string",
      "phone": "string|[REDACTED]",
      "website": "url",
      "email": "string|[REDACTED]",
      "global_id": "string"
    }],
    "rest_url": "url",
    "next_rest_url": "url",
    "total": "int",
    "total_pages": "int"
  }
  ```
- **Observed parameters:** `per_page`, `page`, `search`.
- **Probed parameters:** `per_page=5` → total=5.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** Tribe namespace.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/organizers?per_page=50'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-organizers-per_page-5.json` (emails/phones redacted)
- **Notes:** Staff contacts. Useful for mapping meeting owner → department.

#### /wp-json/tribe/events/v1/organizers/{id} and /organizers/by-slug/{slug}

- **URL:** same pattern as venues.
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Single organizer object.
- **Response schema:** Single organizer (see above).
- **Observed parameters:** none.
- **Probed parameters:** not individually exercised.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** route catalog.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/organizers/1'
  ```
- **Evidence file:** `unverified`
- **Notes:** —

#### /wp-json/tribe/events/v1/categories

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/categories`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Paged list of event-category terms in Tribe's envelope shape (richer than `wp/v2/tribe_events_cat`: adds `urls.self` and `urls.events`).
- **Response schema:**
  ```
  {
    "categories": [{
      "id": "int",
      "count": "int",
      "description": "string",
      "link": "url",
      "name": "string",
      "slug": "string",
      "taxonomy": "tribe_events_cat",
      "parent": "int",
      "urls": {"self": "url"}
    }],
    "rest_url": "url",
    "total": "int",
    "total_pages": "int"
  }
  ```
- **Observed parameters:** `per_page`, `page`, `search`, `hide_empty`, `order`, `orderby`.
- **Probed parameters:** default → total=11 (2 pages). Slugs observed: `advisory-notice`, `centennial-celebration`, `covid`, `election`, `festivals-celebrations`, + 6 more (truncated in evidence).
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** Tribe namespace.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/categories?per_page=50'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-categories.json` (truncated to 5)
- **Notes:** Use for CR to discover whether "commission-meeting" / "planning-zoning" categories exist — if they do, filter events by category id instead of title-string matching.

#### /wp-json/tribe/events/v1/tags

- **URL:** `https://townofdundee.com/wp-json/tribe/events/v1/tags`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Paged list of event-tag terms (shares `post_tag` taxonomy with posts). Only 1 tag exists site-wide.
- **Response schema:** Same envelope as categories; items shaped like `wp/v2/tags`.
- **Observed parameters:** standard taxonomy-collection.
- **Probed parameters:** default → small set.
- **Pagination:** `page/per_page`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** Tribe namespace.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/tribe/events/v1/tags'
  ```
- **Evidence file:** `evidence/dundee-fl-wp-json-tribe-events-v1-tags.json`
- **Notes:** Unused on this site.

### `/wp-json/oembed/1.0/` (embed helper — structured)

#### /wp-json/oembed/1.0/embed — oEmbed JSON for a URL

- **URL:** `https://townofdundee.com/wp-json/oembed/1.0/embed?url=<page-url>`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** oEmbed JSON or XML envelope for any permitted WP URL on the site. Each page exposes itself at `/wp-json/oembed/1.0/embed?url=<canonical-url>` (confirmed: `<link rel="alternate" type="application/json+oembed">` on every page).
- **Response schema:**
  ```
  {
    "version": "1.0",
    "provider_name": "string",
    "provider_url": "url",
    "author_name": "string",
    "author_url": "url",
    "title": "string",
    "type": "rich|link|photo|video",
    "width": "int",
    "height": "int",
    "html": "string"
  }
  ```
- **Observed parameters:**
  - `url` (string, required) — the page URL on the site to embed.
  - `format` (string, optional) — `json` (default) or `xml`.
  - `maxwidth`, `maxheight` (int, optional).
- **Probed parameters:** not individually fetched this run — low value; same content available via `/wp/v2/pages`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** real-time
- **Discovered via:** `<link rel="alternate" type="application/json+oembed">` on every page; WP REST root.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' \
    'https://townofdundee.com/wp-json/oembed/1.0/embed?url=https%3A%2F%2Ftownofdundee.com%2Fdepartments%2Fbuilding-services%2F'
  ```
- **Evidence file:** `unverified`
- **Notes:** Redundant with `/wp/v2/pages` for town-data purposes. Documented only for schema completeness.

#### /wp-json/oembed/1.0/proxy — oEmbed proxy (likely restricted)

- **URL:** `https://townofdundee.com/wp-json/oembed/1.0/proxy`
- **Method:** `GET`
- **Auth:** likely requires capability — not exercised
- **Data returned:** Proxy oEmbed fetch for an arbitrary external URL (editor-only feature in WP core).
- **Response schema:** `unverified`
- **Observed parameters:** `unverified`
- **Probed parameters:** `unverified` — not exercised (risk of triggering outbound fetches from the origin).
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `unverified`
- **Discovered via:** WP REST root route catalog.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://townofdundee.com/wp-json/oembed/1.0/proxy?url=<external>'
  ```
- **Evidence file:** `unverified`
- **Notes:** ⚠️ GAP: not exercised — low value for mapping; irrelevant to public data.

---

## Scrape Targets

All direct-URL scrape targets are standard WordPress public pages reachable as HTML. Most of their structured content is **also** reachable via `/wp/v2/pages` (see APIs), so the primary scrape targets below are those whose value is in either rendered HTML layout (table-structured pages) or content the API doesn't expose (third-party-embedded files).

Where a page's content is fully retrievable via `/wp/v2/pages/{id}`, the API wins (per §4.2 "Never document the same URL in both sections"); those pages are listed as data-access context only in the APIs section.

### `townofdundee.com` (on-origin)

#### Building Services — department page (PDF linkhub)

- **URL:** `https://townofdundee.com/departments/building-services/`
- **Data available:** Department overview + a cluster of downloadable PDFs: Permit Application (`/wp-content/uploads/2024-Permit-Application-1.pdf`), Building Permit Fee Schedule (`/download/Building-Permit-Fee-Schedule-10.01.2025-09.30.2027_2.pdf`), Contractor Registration Form (`/wp-content/uploads/Contractor-Registration-Form.pdf`), Impact Fee Schedule (`/wp-content/uploads/TOD-TIFTR-2024.09-Impact-Fee-Schedule.pdf`), Signature Authority Form subpage, 2022-2023 Permit Utilization Report subpage. Intake method: email `permits@townofdundee.com` or in-person at Town Hall.
- **Fields extractable:** link list (anchor + href); page body text. The structured content is also available through `/wp-json/wp/v2/pages/{id}` (see APIs).
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `a[href*="wp-content/uploads/"]` or `a[href*="/download/"]` inside `<main>` for PDF enumeration.
- **Why no API:** The WP REST `/wp/v2/pages` endpoint provides the rendered HTML (and thus the PDF links inside). This scrape-target entry captures the **PDF-extraction use case** (intake form parsing) rather than the page itself.
- **Notes:** ⚠️ GAP: no online permit portal, no structured permit-application endpoint, no inspection results surface. Building-permit inventory, if needed, would require direct County coordination (Polk County probably has the actual permit-issuance system — see adjacent Haines City and Winter Haven adapters for patterns) or a public-records request to Town staff.

#### Open a Business — business-tax receipt info

- **URL:** `https://townofdundee.com/departments/building-services/open-a-business/`
- **Data available:** Business Tax Receipt application instructions + downloadable application PDF(s).
- **Fields extractable:** application form PDF href; body instructional text.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `main a[href$=".pdf"]`
- **Why no API:** No structured BTR lookup or application submission API exists on-origin.
- **Notes:** Paper/email intake.

#### Property Lien & Assessment Search Request

- **URL:** `https://townofdundee.com/departments/building-services/property-lien-assessment-search-request/`
- **Data available:** Instructions to email a lien-search request to staff. Usually carries a fillable PDF request form.
- **Fields extractable:** form PDF href; contact email; fee info.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `main a[href$=".pdf"]`, `a[href^="mailto:"]`
- **Why no API:** No structured lien-search endpoint — email/paper only.
- **Notes:** ⚠️ GAP: no online lien lookup. PT/CD2 consumers that need lien data for due diligence must file a records request.

#### Code Enforcement — department page

- **URL:** `https://townofdundee.com/departments/code-enforcement/`
- **Data available:** Department overview; Special Magistrate hearings section linking to individual hearing-agenda posts (e.g. `/departments/code-enforcement/20221220-special-magistrate-code-enforcement-meeting/`). Note: "Minutes prior to December 2022 can be accessed" via the main agendas page. Cites Florida SB60 (2021) — anonymous complaints not accepted.
- **Fields extractable:** special-magistrate hearing links; contact phone/email; staff names.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none` — inline list
- **Selectors (if stable):** `main a[href*="special-magistrate"]`
- **Why no API:** No online case lookup, no complaint-status endpoint. Hearing agendas are on Municode Meetings (post-Nov-2022) or in the wp-filebase archive (pre-Nov-2022). The page itself is retrievable via `/wp/v2/pages`.
- **Notes:** ⚠️ GAP: no code-enforcement case API. For CR purposes, Special Magistrate hearings appear in the Tribe events feed as `Special Magistrate Hearing for Code Enforcement` events.

#### Report Issue — code-enforcement intake page

- **URL:** `https://townofdundee.com/departments/code-enforcement/reportissue/`
- **Data available:** Page explaining how to report code violations (phone/email; anonymous complaints disallowed per SB60).
- **Fields extractable:** contact phone, email, hours.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `main` body
- **Why no API:** No online form submission — intake is phone/email.
- **Notes:** ⚠️ GAP: no online complaint form.

#### Planning Department — zoning & LDR hub

- **URL:** `https://townofdundee.com/departments/planning-department/`
  Subpages:
  - `/departments/planning-department/comprehensive-plan/` — Comprehensive Plan PDFs
  - `/departments/planning-department/core-improvement-area/` — CIA overlay info
  - `/departments/planning-department/zoning-and-land-development-regulations/` — zoning PDFs + Municode LDR pointer
- **Data available:** Planning/zoning overview, links to the Comprehensive Plan PDFs, CIA overlay info, and the Land Development Regulations (which live in Municode — see external platforms). Planning & Zoning Board agendas are in the events feed.
- **Fields extractable:** PDF URLs for Comp Plan, CIA docs, LDR amendments; Municode pointer href.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `main a[href$=".pdf"]`, `main a[href*="municode"]`
- **Why no API:** Documents are uploaded to the WP media library — they're also reachable through `/wp/v2/media` by `mime_type=application/pdf`; the scrape target value is the in-page grouping/labeling (which doc is "current" vs. superseded).
- **Notes:** For CD2, the authoritative ordinance/LDR text lives at Municode Library (external).

#### Agendas & Minutes — hybrid archive page

- **URL:** `https://townofdundee.com/government/agendas-minutes/`
- **Data available:** Two delivery mechanisms side by side. (a) "View All Agendas AFTER November 03, 2022, HERE" → link to `https://dundee-fl.municodemeetings.com/` (external). (b) Pre-November-2022 agendas delivered by the **wp-filebase** WordPress plugin as a nested `<ul id="wpfb-filebrowser-1">` tree with year folders (2019, 2020, 2021, 2022) and per-meeting PDF leaves. The wp-filebase tree renders in-page HTML; PDFs live under `/wp-content/uploads/`.
- **Fields extractable:** year folder names; per-meeting agenda anchors with meeting date/type/PDF href; Municode Meetings pointer.
- **JavaScript required:** `no` — tree is server-rendered HTML. The `treeview` CSS class is client-side expand/collapse only; all content is present in initial HTML.
- **Anti-bot measures:** none observed
- **Pagination:** `none` — single page with embedded tree
- **Selectors (if stable):** `#wpfb-filebrowser-1 a[href*="/wp-content/uploads/"]`, `#wpfb-filebrowser-1 li.hasChildren > span.cat` for year labels.
- **Why no API:** wp-filebase has a legacy REST/JSON endpoint at `?wpfb_action=…` that was not probed this run — it may or may not be available. For pre-2022 agendas the simpler route is to filter `/wp/v2/media` by `mime_type=application/pdf` and `date` range 2019-01-01..2022-11-03, cross-referencing titles. ⚠️ GAP: wp-filebase JSON endpoint not probed.
- **Notes:** Post-Nov-2022 agendas/minutes are **off-origin at Municode Meetings** (see External Platforms). CR pipelines for Dundee need a two-source join (pre-2022 on-origin + post-2022 Municode).

#### Planning & Zoning Board — info page

- **URL:** `https://townofdundee.com/government/town-commission-boards/planning-and-zoning-board/`
- **Data available:** Board roster, meeting schedule, purpose statement.
- **Fields extractable:** member names; meeting frequency; rendered HTML.
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `main` body
- **Why no API:** Content retrievable via `/wp/v2/pages`; scrape target listed for completeness since rendered page layout may carry structured roster tables.
- **Notes:** Use `/wp/v2/pages` by slug `planning-and-zoning-board` for clean HTML extraction.

#### Town Commissioners — roster page

- **URL:** `https://townofdundee.com/government/town-commission-boards/town-commissioners/`
- **Data available:** Mayor and commissioners: names, seat numbers, terms, email addresses, photos.
- **Fields extractable:** name, seat, term, email, photo URL — if formatted consistently (verify per-run).
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** depends on theme — recommend extraction via `/wp/v2/pages` with slug lookup, then parse `content.rendered` with a tolerant HTML parser.
- **Why no API:** No structured commissioner directory endpoint; content is rendered HTML.
- **Notes:** Useful for CR (who-voted-how), but requires per-run verification of the HTML table/card layout.

### Event detail page `tribe_events` single-view (HTML)

- **URL:** pattern `https://townofdundee.com/event/<event-slug>/` (e.g. `/event/town-commission-meeting-77/`)
- **Data available:** Single-event HTML page with event metadata + any `description` HTML + embedded links or iframes. Same data is available richer at `/wp-json/tribe/events/v1/events/by-slug/{slug}`.
- **Fields extractable:** title, date, venue, description, organizer contact, embedded document links (if any).
- **JavaScript required:** `no`
- **Anti-bot measures:** none observed
- **Pagination:** `none`
- **Selectors (if stable):** `.tribe-events-single`, `.tribe-events-schedule`
- **Why no API:** Prefer the API — this scrape target is listed for degraded-mode recovery only.
- **Notes:** Use the Tribe REST API in production. Scrape only if the JSON endpoint is offline.

---

## External Platforms

These are off-origin third-party platforms linked from the town website. Their internals are **out of scope for this per-jurisdiction map** — each belongs to its own per-platform map in `_platforms.md` and its own adapter (where one exists in the repo). Listed here so a downstream reader sees the full data surface.

| Platform | URL | Purpose | Adapter status |
|---|---|---|---|
| **Municode Meetings** | `https://dundee-fl.municodemeetings.com/` | Agendas, minutes, meeting packets, ADA-HTML variants for all Town Commission, Planning & Zoning Board, and Special Magistrate Code Enforcement meetings **after November 3, 2022**. Blob-stored PDFs at `mccmeetings.blob.core.usgovcloudapi.net/dundeefl-pubu/MEET-{Agenda|Packet|Minutes}-<guid>.pdf`. ADA-HTML at `https://meetings.municode.com/adaHtmlDocument/index?cc=DUNDEEFL&me=<guid>`. | Not yet in `_platforms.md`. ⚠️ GAP: Municode Meetings platform row needs to be added; at least one other Polk-County municipality uses it. Template body-filter values on this tenant: `bc-tc` (commission), others seen: `page/town-commission-meeting-67`, `calendar`. |
| **Municode Library** | `http://library.municode.com/index.aspx?clientId=12506` | Full Code of Ordinances + Land Development Regulations for the Town of Dundee. clientId `12506`. Angular SPA backed by `api.municode.com/codes/{client_id}/nodes` (auth-gated per Davenport map). | Adapter exists: `cd2/adapters/municode.py`. Already in `_platforms.md`. |
| **Edmunds WIPP** | `https://wipp.edmundsassoc.com/Wipp/?wippid=DUND` | Online utility-billing / water-bill payments. Not a data source — it's an egress/payment channel. | Out of scope for county-data mapping. |
| **Point & Pay** | `https://client.pointandpay.net/web/TownofDundeeFLOnline` | Payment portal (fees, fines, other). | Out of scope. |
| **Polk County Property Appraiser** | `http://polkpa.org` | Parcel / ownership data for properties in Dundee. Belongs to the Polk County map. | Separate per-county file. |
| **Polk County** | `https://www.polk-county.net/community-and-small-business-assistance` | County-operated community & small-business resources. | Separate per-county file. |
| **PRWC** | `http://www.prwcwater.org/` | Peace River Water Coop wholesale utility. | Out of county-data scope. |

---

## Coverage Notes

**Total requests this run:** 61 (see `evidence/_dundee-request-log.txt`) — comfortably within the 2000-request cap, within light-touch probe pacing (~1 req/sec with 1 s sleeps between batches).

**robots.txt stance:** permissive — only disallows the calendar view-mode infinite-pagination variants (`/calendar/action~*/`) and a legacy AI1EC exporter controller. No `Disallow: /`. This mapping stayed outside the disallowed `action~*` patterns. A production scraper can operate here without friction provided it skips those traps.

**No rate-limiting, no WAF challenges, no CAPTCHA** observed at 61 requests. Apache + PHP 7.4.33 direct; no Cloudflare / Sucuri / Akamai fronting.

**Platform summary:** single WordPress origin with **The Events Calendar** plugin providing the dominant public-data surface. WP REST is fully open for published content. All town-facing text (every department page, every announcement, every event, every uploaded PDF) is discoverable through some combination of `/wp/v2/pages`, `/wp/v2/posts`, `/wp/v2/media`, `/tribe/events/v1/events`, `/tribe/events/v1/venues`, `/tribe/events/v1/organizers`, and `wp-sitemap*.xml`.

**⚠️ GAP: no online permit portal.** Building Services intake is email/paper (`permits@townofdundee.com`). No Accela, iWorQ, MyGov, Cloudpermit, EnerGov, Viewpoint, or other permit-portal vendor is linked from the site. Permit inventory (if needed for a PT pipeline) must come from Polk County records, public-records requests, or a future online-portal rollout.

**⚠️ GAP: no on-origin lien, code-case, or inspection API.** Three related gaps with the same resolution — all three are paper/email intake on Dundee's side.

**⚠️ GAP: agenda/minutes delivery is split.** Pre-Nov-2022 meetings are archived on-origin in wp-filebase / `/wp-content/uploads/`; post-Nov-2022 meetings are on Municode Meetings external. CR pipelines for Dundee need a two-source consolidation.

**⚠️ GAP: wp-filebase JSON endpoint not probed.** The plugin has a legacy AJAX API; not exercised this run because `/wp/v2/media` plus sitemap `modified_gmt` already covers the same PDFs. Re-visit if a future run needs tighter cadence on the pre-2022 archive.

**⚠️ GAP: `wp/v2/pages?per_page=100` returned an HTML error** in this session (artifact saved but not parseable as JSON). WP core defaults the cap at 100 and this endpoint normally honors that; the artifact was dropped from evidence. A re-run should confirm `per_page=100` works cleanly (expected behavior per WP REST core).

**⚠️ GAP: `/wp-json/oembed/1.0/proxy`, `xmlrpc.php` POST methods, The Events Calendar `event-aggregator/v1/import/*` routes, and `tec/v2/onboarding/wizard` were not exercised.** These are either auth-gated (proxy, xmlrpc), admin-only (onboarding), or internal ingest (event aggregator). No town-data value expected — deferred by low-priority judgment, not by policy.

**PHP 7.4.33 is past upstream end-of-life** (2022-11-28). No vulnerability probes performed per mapping scope; flagged as an operational risk for the Town's IT / hosting vendor to address.

**New platforms added to `_platforms.md` this run:**
- `WordPress REST` (namespace `/wp-json/wp/v2/`), signatures: `Link: <…>; rel="https://api.w.org/"` header, `/wp-json/` root document, `wp-sitemap*.xml`.
- `The Events Calendar (Tribe) REST` (namespace `/wp-json/tribe/events/v1/`), signatures: `<meta name="tec-api-version">`, `/wp-json/tribe/events/v1/events` envelope with `events[]`, `total`, `total_pages`.
- `Municode Meetings` (hostname pattern `*.municodemeetings.com`), signatures: agenda/minutes delivery at `mccmeetings.blob.core.usgovcloudapi.net/<tenant>-pubu/MEET-*.pdf`, ADA HTML at `meetings.municode.com/adaHtmlDocument/index?cc=<TENANT>`.

**Davenport sister reference:** the Davenport (Catalis GovOffice classic ASP) map and the Dundee (WordPress + Tribe) map together span the two most common small-Polk-County-city CMS archetypes. The WordPress + Tribe stack here is materially richer for programmatic consumption than Davenport's GovOffice CMS, which had zero JSON endpoints.
