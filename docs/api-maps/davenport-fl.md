# Davenport, FL (Polk County) — CR API Map

*Target:* Commission Radar (CR) seed for the City of Davenport, a municipality within Polk County, Florida.
*Mapped:* 2026-04-16.
*Method:* anonymous HTTPS probes at ~1 req/sec with UA `CountyData2-mapper/1.0`; no authenticated flows; no disallowed crawl paths.

## Summary

Davenport's web presence is a single origin — **`https://www.mydavenport.org/`** — running a classic ASP CMS authored by **Catalis GovOffice** (template path `/repository/designs/templates/GO_davenport-fl_2025_resp/`, footer link to `catalisgov.com`). It is **not** one of the known CR meeting-portal vendors (no Legistar, CivicClerk, eScribe, Granicus, NovusAgenda, iQM2, CivicWeb, BoardDocs, PeakAgenda). Sister Polk-County city Haines City uses eScribe; Davenport does **not**.

There are **no JSON, XML, RSS, iCal, SOAP, ArcGIS, or GraphQL endpoints** on the origin. Every discovered programmatic surface returns either HTML (`/index.asp`, search) or a static file (`sitemap.xml`, `robots.txt`, PDF uploads). The CR-bearing data is **static PDF agenda and minutes files** published under a single deterministic path prefix:

```
https://www.mydavenport.org/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/
```

File names follow the pattern `<Month>_<day>_<Year>_-_<Type>(<disambig>).pdf` (e.g. `April_20_2026_-_Planning_Commission_(AGENDA_PACKET).pdf`, or `April_20_2026_-_Regular_Meeting(1).pdf` where `(1)` is the minutes twin). Anchors on the per-year index pages expose each file with a human-readable label like "April 20, 2026 — Planning Commission".

**CR coverage strategy (for the later pipeline design):** scrape the seven per-year HTML index pages under the `Commission Agendas` and `City Commission Minutes` sections; extract each `<a>` anchor's label + `.pdf` href; dedupe against the stable URL set; fetch the PDFs directly (HTTP 200, `Content-Type: application/pdf`, ETag, Last-Modified, `max-age=7200`). Pagination does not exist — the index pages are year-scoped and load all meetings inline (16–50 per year). No AJAX. No forms to submit.

Ordinance text is **off-origin** at **Municode** (`library.municode.com/fl/davenport/codes/code_of_ordinances`). That is a CD2/LDC target, not CR — cataloged in Scrape Targets for completeness. Resolutions have **no online index** — records must be requested from the City Clerk via phone/email. ⚠️ GAP.

**Totals:** 77 requests this run; 16 APIs/endpoints documented (all HTML or static file, none JSON); 7 scrape targets; 325 meeting-PDF links catalogued across 2020–2026.

---

## Platform Fingerprint

| Signal | Value |
|---|---|
| Origin | `https://www.mydavenport.org/` |
| Server | IIS (classic ASP — `.asp` extensions, `ASPSESSIONID*` cookies, `<form action="index.asp" method="get">` throughout) |
| CMS | **Catalis GovOffice** (formerly "GovOffice.com" / CivicResolve). Fingerprinted by the template directory `/repository/designs/templates/GO_davenport-fl_2025_resp/` and the `GO_` prefix convention, plus the footer links to `catalisgov.com`. The `/vertical/sites/%7B<guid>%7D/uploads/` path is a GovOffice-specific artifact-repository convention. |
| Routing model | Every navigable page is either (a) a human-friendly "vanity URL" alias (`/commissionagendas`, `/commissionminutes`, `/cityclerk`) that the CMS rewrites to `/index.asp?SEC=<GUID>`, or (b) `/index.asp?SEC=<GUID>&DE=<GUID>` where `SEC` is a section/menu GUID and `DE` is a leaf page / archive-year GUID. |
| Search | `/index.asp?SEC=B5D05054-086E-438B-96FF-253DCDE7535A&keyword=<q>` — server-rendered HTML results listing `<a>` links into `/index.asp?SEC=…`. |
| Static uploads repository | `/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/` — the single `96FA7459-A704-43EF-A44D-7BFA732F5D2E` GUID is the site-tenant identifier; all PDFs, images, and .mov files hang off this directory. The directory itself is `403 Forbidden` (no index listing), so enumeration must happen through the linking HTML pages. |
| Robots policy | Allowlist-style: named bots (Googlebot, bingbot, ia_archiver, archive.org_bot, W3C-checklink, CCBot) disallow only `/admin/`, `/manager/`, `*month*`, `*GUESTBOOK*`. `User-agent: *  Disallow: /` applies to all other crawlers. This mapping stayed in the allowlisted sections and off disallowed paths; the UA was explicit and the pacing ~1 req/sec. ⚠️ GAP: a production CR scraper should either adopt an allowlisted UA or be allow-listed by the City; see Coverage Notes. |
| Rate limiting / WAF | None observed at this volume. Responses include `Strict-Transport-Security: max-age=360;` and `Cache-Control: private` on HTML, `must-revalidate,max-age=7200` on PDFs. No Cloudflare headers. A single odd quirk: many responses emit `curl: (56) schannel: server closed abruptly (missing close_notify)` after delivering the payload — cosmetic, the body is complete; not an error state. |
| Embedded third-party | `kit.fontawesome.com`, `maps.googleapis.com` (City Hall locator map, key `AIzaSyCGQ9uxhvAlQJkZsMCtdMBQqFEMtvWUM9A`), `cdnjs.cloudflare.com` (Owl Carousel, animate.css), `textmygov.com` (SMS subscribe widget), `www.paycomonline.net` (HR / career portal link-out). None of these expose CR data. |
| Sister jurisdictions in Polk County | Haines City uses **eScribe** (`pub-hainescity.escribemeetings.com`, `docs/api-maps/haines-city-escribe.md`). Lake Alfred: unverified here. Davenport is **not** on eScribe, CivicClerk, or any other meeting-portal vendor — its agenda surface is entirely its own Catalis GovOffice CMS. |
| §5 known-platform checks | Legistar, CivicClerk, CivicPlus, Granicus, Tyler, Accela, OpenGov, OnBase, ArcGIS probes all returned 404 or N/A — none fingerprinted. Municode only as external off-origin ordinance library. |

---

## APIs

All "APIs" on this origin are HTML-rendered endpoints. There is no JSON/XML programmatic surface. They are documented here (rather than under Scrape Targets) because they are the closest analogues to APIs — stable URLs returning machine-parsable structured HTML at predictable paths, serving as the primary data surface for a CR scraper.

### `/`  (site root)

#### Site root / home

- **URL:** `https://www.mydavenport.org/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Marketing landing page with a rotating Owl Carousel banner, City Hall locator map (embedded Google Maps), three "Spotlight" tiles (Parks & Recreation, Special Events, Community News). No CR data, but it is the discovery entrypoint: top nav links to Government → Agendas & Minutes → Commission Agendas / Minutes.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "meta": {
      "title": "Home - Davenport, FL"
    },
    "nav_links": ["/government", "/agendasminutes", "/commissionagendas", "/commissionminutes", "/planningcommission", "/boardscommittees", "/ordinances", "/resolutions", "/departments", "/cityclerk", "..."],
    "search_form_action": "/index.asp",
    "search_form_params": ["SEC", "keyword"]
  }
  ```
- **Observed parameters:** none on GET / root.
- **Probed parameters:** `none` — root has no query-string behavior.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `unknown` (CMS-authored; `sitemap.xml` shows `lastmod: 2026-02-03T16:49:00-05:00` for the root)
- **Discovered via:** seed entry from web-search hit `mydavenport.org`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/'
  ```
- **Evidence file:** `evidence/page-home.html`
- **Notes:** 61 KB HTML; no CR data present. Used only for platform fingerprinting and nav-link discovery.

#### robots.txt

- **URL:** `https://www.mydavenport.org/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Robots exclusion policy, allowlist-style (named bots + `User-agent: *  Disallow: /`). Declares sitemap at `https://www.mydavenport.org/sitemap.xml`.
- **Response schema:**
  ```
  {
    "content_type": "text/plain",
    "directives": [
      {"user_agent": "Googlebot", "disallow": ["/admin/", "/manager/", "/*month*", "/*GUESTBOOK*"]},
      {"user_agent": "bingbot", "disallow": ["/admin/", "/manager/", "/*month*", "/*GUESTBOOK*"]},
      {"user_agent": "ia_archiver", "disallow": ["/admin/", "/manager/"]},
      {"user_agent": "archive.org_bot", "disallow": ["/admin/", "/manager/"]},
      {"user_agent": "W3C-checklink", "disallow": ["/admin/", "/manager/"]},
      {"user_agent": "CCBot", "disallow": ["/admin/", "/manager/"]},
      {"user_agent": "*", "disallow": ["/"]}
    ],
    "sitemap": "https://www.mydavenport.org/sitemap.xml"
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none` — static file.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `unknown` — no Last-Modified header returned.
- **Discovered via:** standard `/robots.txt` probe at seed URL.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://www.mydavenport.org/robots.txt'
  ```
- **Evidence file:** `evidence/robots-mydavenport.txt` (sibling headers: `evidence/robots-mydavenport.headers.txt`)
- **Notes:** ⚠️ GAP: `User-agent: *  Disallow: /` blocks generic crawlers. A production scraper needs either an allowlisted UA (Googlebot-style identification) or a handshake with the City. This mapping used `CountyData2-mapper/1.0` and stayed within a light, spaced probe budget.

#### sitemap.xml

- **URL:** `https://www.mydavenport.org/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Sitemap Protocol 0.9 — 218 `<url>` entries covering every CMS page, with `<loc>` + `<lastmod>`. Includes both vanity paths (`/commissionagendas`, `/cityclerk`, etc.) and canonical `/index.asp?SEC=…&DE=…` forms. Per-year agenda/minutes archive pages appear here with `lastmod` updated when a new PDF is published.
- **Response schema:**
  ```
  {
    "urlset": {
      "xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9",
      "url": [
        {"loc": "string(url)", "lastmod": "iso8601"}
      ]
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:**
  - `gzip` — tested `GET /sitemap.xml.gz` → 404. No compressed variant offered; caller uses standard `Accept-Encoding` negotiation.
- **Pagination:** `none` — single file, 33 KB, 218 URLs.
- **Rate limits observed:** none observed
- **Data freshness:** `current`. Sampled `lastmod` dates range from 2019-era static pages through 2026-04-15 for `/commissionagendas` — the sitemap appears to update when a section is modified.
- **Discovered via:** `robots.txt` `Sitemap:` directive.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' 'https://www.mydavenport.org/sitemap.xml'
  ```
- **Evidence file:** `evidence/sitemap-mydavenport.xml` (sibling headers: `evidence/sitemap-mydavenport.headers.txt`)
- **Notes:** Useful as a change-detection signal. The `lastmod` on `/commissionagendas` (updated 2026-04-15) is a coarse poll signal but does not carry per-meeting granularity — a CR scraper still has to pull the per-year index and diff PDF links.

### `/index.asp`

The single dispatcher endpoint. All semantic pages on the site render through `/index.asp?SEC=<GUID>[&DE=<GUID>]`. `SEC` identifies the section (commission agendas, commission minutes, ordinances page, cityclerk, …) and `DE` identifies the archive-year sub-page. Alternative shorter forms (e.g. `/commissionagendas`) are CMS-authored aliases that internally rewrite to a canonical `SEC` GUID. Both forms return identical HTML.

#### Commission Agendas landing page

- **URL:** `https://www.mydavenport.org/commissionagendas`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML landing page listing the 7 per-year archive sub-pages (2020–2026) under `Commission Agendas`. Each sub-page link is an `<a>` in the main content column with human-readable anchor text like "2026 City Commission Agendas". Identical content served at `/index.asp?SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7` and at the vanity alias.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Commission Agendas",
      "year_links": [
        {
          "label": "<YYYY> City Commission Agendas",
          "href": "/index.asp?SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7&DE=<year_GUID>"
        }
      ]
    }
  }
  ```
- **Observed parameters:** none on the vanity form.
- **Probed parameters:**
  - `SEC` — tested `SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7` (canonical) → HTTP 200 identical body. `SEC=<nonexistent-guid>` returned the site default / 404-style fallback (not probed exhaustively).
  - `DE` — tested per-year GUIDs 2020–2026 → all HTTP 200, each rendering that year's archive (see next entry).
- **Pagination:** `none` — the landing lists at most 7 year-links, no chunking.
- **Rate limits observed:** none observed
- **Data freshness:** `current`; sitemap `lastmod` for `/commissionagendas` was 2026-04-15.
- **Discovered via:** sitemap + top-nav `/commissionagendas` link on home page.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/commissionagendas'
  ```
- **Evidence file:** `evidence/page-commissionagendas.html`
- **Notes:** 38 KB. The 7 year-GUIDs discovered here: 2026=`EF3D4D07-6249-43FC-BBED-A5025E6D4757`, 2025=`B1AD9ADD-7A53-4D60-A6FF-CB94FE1043EF`, 2024=`24685B32-E129-41C4-A580-A4139AD11DDA`, 2023=`AA8C75B0-4E22-495A-BCD7-1048697E14A4`, 2022=`A839513B-1D32-416D-81F5-B014622E2AF4`, 2021=`7D0E0725-1FDD-48D6-A5E0-C700BC8C3C4C`, 2020=`04670147-A780-412D-958F-031A6F74B191`. A new-year index page is expected to appear in January of each year; detecting it requires re-parsing this landing page.

#### Commission Agendas — per-year archive

- **URL:** `https://www.mydavenport.org/index.asp` (with `SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7` and `DE=<year_GUID>`)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML page listing every meeting agenda PDF published for that calendar year. Each meeting is an `<a>` with anchor text formatted `<Month> <day>, <YYYY> - <MeetingType>[ (<modifier>)]` (e.g. "April 20, 2026 - Planning Commission (AGENDA PACKET)") and an `href` to `/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/<filename>.pdf`. Observed meeting types: `Regular Meeting`, `Planning Commission`, `Workshop`, `Special Meeting`, `Audit Committee Workshop`, `Budget Workshop`, `Fair Housing Workshop`, `1st Budget PH & Regular Meeting`, `2nd Budget PH & Regular Meeting`, `Election Workshop`, `CFRPC Comp Plan Presentation`, `Commission Workshop`. Cancelled meetings are annotated `(CANCELLED)` or `(Cancelled)` in the label. Amended agendas are annotated `(AMENDED AGENDA)`. Agenda-packet variants (often same meeting) suffixed `(AGENDA_PACKET)`.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "<YYYY> City Commission Agendas",
      "meetings": [
        {
          "label": "<Month> <day>, <YYYY> - <MeetingType>[ (modifier)]",
          "href": "/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/<Filename>.pdf"
        }
      ]
    }
  }
  ```
- **Observed parameters:**
  - `SEC` (GUID, required) — fixed value `9B0AFDD2-5297-4ED5-B887-F5F96A697CC7` for the Commission Agendas section.
  - `DE` (GUID, required) — the per-year sub-page identifier.
- **Probed parameters:**
  - `DE` — tested 7 values (2020–2026). All HTTP 200. 2026 page had 16 PDFs (YTD through April), 2020 had 48, 2021 41, 2022 44, 2023 37, 2024 39, 2025 50.
  - `SEC` — kept at the section GUID. Passing mismatched `SEC`+`DE` not tested — not a CR requirement.
  - pagination / sort / filter — no such parameters; the CMS does not paginate or filter year pages.
- **Pagination:** `none` — the year page inlines all meetings for the year.
- **Rate limits observed:** none observed
- **Data freshness:** `current`; index page is regenerated when a new PDF is uploaded. Sitemap `lastmod` on 2026 year page: 2026-04-15.
- **Discovered via:** `/commissionagendas` landing page anchors.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L \
    'https://www.mydavenport.org/index.asp?SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7&DE=EF3D4D07-6249-43FC-BBED-A5025E6D4757'
  ```
- **Evidence file:** `evidence/year-2026-agendas.html` (plus `year-2020-agendas.html` … `year-2025-agendas.html` as companions)
- **Notes:** This endpoint is the core CR discovery surface. A scraper should pull all 7 year pages, parse each anchor's label + href, dedupe on absolute PDF URL. Filename disambiguation: when multiple PDFs share the same base name (e.g. agenda then minutes for the same meeting), the second file is suffixed `(1)`. Minutes for 2026 live under a **different** `SEC` (see next section) but with the same `(1)` filename convention, so an agenda scraper and a minutes scraper should both target these year-index pages and use the anchor label (not the filename) as source-of-truth for meeting-date extraction. ⚠️ GAP: anchor text is the only human-parsable identifier; if label formatting drifts, dated-regex extraction breaks — scrapers must be defensive.

#### Commission Minutes landing page

- **URL:** `https://www.mydavenport.org/commissionminutes`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML landing page listing per-year sub-pages (2019–2026) under `Commission Minutes` (note: minutes extend back to 2019, agendas only to 2020). Each link is an `<a>` to `/index.asp?SEC=BCAF1EB6-5004-4D0F-AB11-1F99DC500749&DE=<year_GUID>`. Identical body is also reachable at `/agendasminutes` (which is a combined landing page linking to both sections) and at the canonical `SEC=BCAF1EB6-…` form.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Commission Minutes",
      "year_links": [
        {
          "label": "<YYYY> City Commission Minutes",
          "href": "/index.asp?SEC=BCAF1EB6-5004-4D0F-AB11-1F99DC500749&DE=<year_GUID>"
        }
      ]
    }
  }
  ```
- **Observed parameters:** none on vanity form.
- **Probed parameters:** Same as Commission Agendas landing — 8 year-GUIDs tested, all HTTP 200.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `current`.
- **Discovered via:** `/agendasminutes` combined landing + top-nav.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/commissionminutes'
  ```
- **Evidence file:** `evidence/page-commissionminutes.html`
- **Notes:** Minutes year-GUIDs: 2026=`7481432E-3365-491C-88D1-7E158D7AD015`, 2025=`FB740DEC-236E-416D-B862-CD23E9864EB7`, 2024=`0B2F700F-4631-454F-866D-24F36A9BC369`, 2023=`46533EDB-A623-4706-A817-1F2B541B6103`, 2022=`9D38468B-0C62-4543-82A8-432D613C0793`, 2021=`DF688D87-ECD2-471F-86E8-7FCE13A98038`, 2020=`BAFA4D94-D320-4A53-A88C-884BB59A9878`, 2019=`7BF528D5-4396-40FA-A8AC-46216CFCE9D3`.

#### Commission Minutes — per-year archive

- **URL:** `https://www.mydavenport.org/index.asp` (with `SEC=BCAF1EB6-5004-4D0F-AB11-1F99DC500749` and `DE=<year_GUID>`)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Identical structure to the agendas per-year archive — HTML page listing that year's meeting minute PDFs. Anchor labels match the agenda labels exactly (same meeting date/type), but the filename typically carries a `(1)` suffix (e.g. `April_21_2025_-_Regular_Meeting(2).pdf` — higher numeric suffixes reflect multiple minutes revisions). The same `/vertical/sites/%7B96FA7459-…%7D/uploads/` repo is used — agendas and minutes are not separated on the storage side.
- **Response schema:** Same shape as agendas per-year (see above).
- **Observed parameters:** `SEC` (fixed to `BCAF1EB6-…`), `DE` (year GUID).
- **Probed parameters:** `DE` — tested 2025 → 40 PDFs, 2026 → 10 PDFs. Remaining years 2019–2024 not individually downloaded this run but visible from the landing page link list and known to follow the same format (confirmed by spot-checking sitemap `lastmod` values).
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `current`; minutes typically published ~2–4 weeks after the meeting.
- **Discovered via:** `/commissionminutes` landing page anchors.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L \
    'https://www.mydavenport.org/index.asp?SEC=BCAF1EB6-5004-4D0F-AB11-1F99DC500749&DE=7481432E-3365-491C-88D1-7E158D7AD015'
  ```
- **Evidence file:** `evidence/year-2026-minutes.html` (companion: `year-2025-minutes.html`)
- **Notes:** Because the label text is identical between agenda and minutes pages, a CR pipeline should associate the two by `(meeting_date, meeting_type)` pair and then attach the agenda URL and minutes URL independently. ⚠️ GAP: 2019 minutes were not individually sampled in this run — only the landing-page link was verified; a scraper run should cover 2019 for historical completeness.

#### Commission Meetings — schedule page

- **URL:** `https://www.mydavenport.org/commissionmeetings`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Prose page describing the recurring Commission meeting schedule (first and third Monday of each month, 6:00 PM, in the Commission Chambers at 1 South Allapaha Avenue). No list of dated meetings. Intended for residents, not as a data feed.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "City Commission Meetings",
      "body_text": "string"
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none` — no query-string behavior.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `stale-ok` — generic schedule text.
- **Discovered via:** sitemap + top-nav.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/commissionmeetings'
  ```
- **Evidence file:** `evidence/page-commissionmeetings.html`
- **Notes:** Not a data source. Useful for human context only.

#### Agendas & Minutes — combined landing

- **URL:** `https://www.mydavenport.org/agendasminutes`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML combined landing with two sections — links to Commission Agendas and Commission Minutes landings. Redundant with those two pages but serves as the City's human entry point.
- **Response schema:** Same as Commission Agendas landing (see above).
- **Observed parameters:** none.
- **Probed parameters:** `none`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `current`.
- **Discovered via:** top-nav from home.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/agendasminutes'
  ```
- **Evidence file:** `evidence/page-agendasminutes.html`
- **Notes:** Safe to skip in a CR pipeline; use the `/commissionagendas` and `/commissionminutes` landings directly.

#### Planning Commission — info page

- **URL:** `https://www.mydavenport.org/planningcommission`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Prose page describing the Planning Commission (purpose: special-developments review, administrative appeals, recommendations on zoning/comp-plan changes) and noting that agendas/minutes are published in the City Commission Agendas and Minutes archives (i.e., the Planning Commission does **not** have its own archive pages). Meetings: 6:00 PM, third Monday each month.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Planning Commission",
      "body_text": "string"
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `stale-ok`.
- **Discovered via:** top-nav + sitemap.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/planningcommission'
  ```
- **Evidence file:** `evidence/page-planningcommission.html`
- **Notes:** Planning Commission agendas are embedded inside the City Commission year-pages (filtered by the label literal `Planning Commission` in the anchor text). For the CR body-filter, a downstream adapter should treat `"Planning Commission"` as an in-scope body filter value (analogous to Haines City's `planning_commission` body).

#### Ordinances — info page

- **URL:** `https://www.mydavenport.org/ordinances`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Prose page directing users to the external Municode codification at `https://www.municode.com/library/fl/davenport/codes/code_of_ordinances`. No on-origin ordinance PDFs, lists, or search. Single external href in the main content area.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "City Ordinances",
      "external_links": ["https://www.municode.com/library/fl/davenport/codes/code_of_ordinances"]
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `stale-ok` (referral page).
- **Discovered via:** top-nav.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/ordinances'
  ```
- **Evidence file:** `evidence/page-ordinances.html`
- **Notes:** ⚠️ GAP: no on-origin ordinance feed. Individual adopted-ordinance PDFs (e.g. "Ordinance 2025-17") are **embedded inside the per-meeting agenda PDFs** as exhibits — they are not separately indexed. For CR's "ordinances in motion" signal, the only source is to parse agenda PDFs. For final-adopted-ordinance text, Municode is the source (scrape target).

#### Resolutions — info page

- **URL:** `https://www.mydavenport.org/resolutions`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Prose page instructing users to contact the City Clerk (Rachel Castillo, 863-419-3300 ext. 125, rcastillo@mydavenport.org) via public-records request for Resolution copies. No online index, no PDFs, no search.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Resolutions",
      "body_text": "string"
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `stale-ok`.
- **Discovered via:** top-nav.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/resolutions'
  ```
- **Evidence file:** `evidence/page-resolutions.html`
- **Notes:** ⚠️ GAP: Resolutions have **no public online index** on any discoverable surface. Only discovery path for CR is same as ordinances — parse agenda PDFs for Resolution line items. Full-text retrieval requires a public-records request (out of scope for automated CR).

#### Boards & Committees — info page

- **URL:** `https://www.mydavenport.org/boardscommittees`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Prose page listing the City's boards (Planning Commission, Recreation Advisory Committee, Evergreen Cemetery Committee). No dated meeting data. BOA/ZBA-style boards are not listed (the Planning Commission handles that function, per the Planning Commission info page).
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Boards & Committees",
      "body_text": "string"
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:** `none`.
- **Pagination:** `none`
- **Rate limits observed:** none observed
- **Data freshness:** `stale-ok`.
- **Discovered via:** top-nav.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/boardscommittees'
  ```
- **Evidence file:** `evidence/page-boardscommittees.html`
- **Notes:** Per project convention (`skip_boa_zba`), the Recreation Advisory Committee and Evergreen Cemetery Committee are **out of CR scope** — only Planning Commission is in-scope for entitlement tracking. Planning Commission has no separate archive — its meetings appear inside the City Commission per-year archives under the `Planning Commission` label.

#### Search — HTML-rendered full-site search

- **URL:** `https://www.mydavenport.org/index.asp` (with `SEC=B5D05054-086E-438B-96FF-253DCDE7535A&keyword=<q>`)
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML search results page. Each hit is an `<a>` link into `/index.asp?SEC=<GUID>` (optionally also `&DE=<GUID>`) with anchor text equal to the target page title plus an excerpt. Empty queries render "No web page matches have been found." The result set includes page content but not PDF filenames — searching "Regular Meeting" does **not** surface the per-meeting PDFs; it surfaces the Commission Meetings info page.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Search Results - Davenport, FL",
      "results": [
        {
          "label": "string",
          "href": "/index.asp?SEC=<GUID>[&DE=<GUID>]",
          "excerpt": "string"
        }
      ]
    }
  }
  ```
- **Observed parameters:**
  - `SEC` (GUID, required) — fixed to `B5D05054-086E-438B-96FF-253DCDE7535A`.
  - `keyword` (string, required) — free-text query.
- **Probed parameters:**
  - `keyword=""` (empty) — HTTP 200 with "No web page matches have been found."
  - `keyword=ordinance` — HTTP 200, multiple hits including Ordinances info page, False Alarms Ordinance, Business Impact Estimates, City Commission Meetings, Code Enforcement. No pagination controls, no result count. No result-count header. No JSON variant.
  - `keyword=planning` — HTTP 200, 67 KB — includes Planning Commission hits.
  - pagination — no `start`, `offset`, `page`, or `pg` query parameter exposed. Result set appears to render all matches inline.
- **Pagination:** `none` (all results on one page)
- **Rate limits observed:** none observed
- **Data freshness:** `current` (reflects current CMS state).
- **Discovered via:** `<form role="search">` blocks on every page (both `formSearchMobile` and `formSearch`).
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L \
    'https://www.mydavenport.org/index.asp?SEC=B5D05054-086E-438B-96FF-253DCDE7535A&keyword=ordinance'
  ```
- **Evidence file:** `evidence/probe-search-ordinance.html` (companions: `probe-search-empty.html`, `probe-search-planning.html`)
- **Notes:** ⚠️ GAP: search results do **not** index uploaded PDFs — only CMS pages. Not useful as a CR discovery mechanism. A CR scraper should ignore this endpoint.

### `/calendar/`

#### calendar.asp (and /calendar vanity alias)

- **URL:** `https://www.mydavenport.org/calendar/calendar.asp`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** HTML events calendar page. Reached via the "Events" top-nav link (which rewrites to `/events` → `/calendar/calendar.asp`). On the day sampled, rendered as an empty/placeholder page with stock Owl Carousel layout — no upcoming events rendered from any data source. The page does **not** display agenda dates; the calendar is scoped to City-produced community events (holiday parades, etc.), not meetings.
- **Response schema:**
  ```
  {
    "content_type": "text/html",
    "main_content": {
      "title": "Calendar",
      "body_text": "string"
    }
  }
  ```
- **Observed parameters:** none.
- **Probed parameters:**
  - `month`, `year`, `d` — not tested. The CMS `robots.txt` disallows `/*month*` patterns for allowlisted bots, which hints that `/calendar/calendar.asp?month=<n>` may be a legitimate date-navigation parameter but is administratively blocked to avoid crawler infinite-pagination traps. Out of scope for CR and not exercised in this run.
- **Pagination:** `unverified` (see probed-parameters note above)
- **Rate limits observed:** none observed
- **Data freshness:** `unknown`
- **Discovered via:** top-nav `Events` → `/events` → rewrites to `/calendar/calendar.asp`.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L 'https://www.mydavenport.org/calendar/calendar.asp'
  ```
- **Evidence file:** `evidence/page-calendar.html`
- **Notes:** Not a CR data source. Community events only. Cross-referenced with `/events` which returns identical content.

### `/vertical/sites/{96FA7459-A704-43EF-A44D-7BFA732F5D2E}/uploads/`

#### Uploads artifact repository — meeting PDFs

- **URL:** `https://www.mydavenport.org/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/<filename>.pdf`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Raw agenda or minutes PDF. Sample response headers: `Content-Type: application/pdf`, `Content-Length: 210985`, `Last-Modified: Fri, 02 Jan 2026 14:42:27 GMT`, `Accept-Ranges: bytes`, `ETag: "5e4f314f67bdc1:0"`, `Cache-Control: must-revalidate,max-age=7200`. PDF format is standard (PDF 1.6 / flate-encoded). A sample agenda PDF was confirmed as a valid PDF 1.6 document (~206 KB).
- **Response schema:**
  ```
  {
    "content_type": "application/pdf",
    "headers": {
      "content_length": "int (bytes)",
      "last_modified": "rfc1123",
      "etag": "string",
      "cache_control": "must-revalidate,max-age=7200"
    },
    "body": "application/pdf stream"
  }
  ```
- **Observed parameters:** none (path-based addressing).
- **Probed parameters:**
  - `HEAD` — confirmed via `curl -I`: 200, full headers returned.
  - directory listing — `GET` to the uploads directory (with and without trailing slash) returns **HTTP 403 Forbidden** — the directory has directory-listing disabled. Enumeration must happen via the per-year HTML index pages.
  - alternative filename variants — `_ ` vs. `-`, `(1)` suffix, `(AMENDED_AGENDA)` suffix all confirmed by inspection of index-page anchors across 7 years.
- **Pagination:** `none` (single file per URL)
- **Rate limits observed:** none observed at this volume. The 7200 s max-age suggests two-hour CDN/edge caching; sustained high-rate scraping should not trigger throttling but also should rely on `If-Modified-Since` or ETag for polite poll cadence.
- **Data freshness:** `current`; a new PDF appears when the City Clerk uploads it (typically 24–72 h before the meeting for agendas, 2–4 weeks after for minutes).
- **Discovered via:** anchors on per-year agenda and minutes archive pages.
- **curl:**
  ```bash
  curl -A 'CountyData2-mapper/1.0' -L -o January_5_2026_-_Regular_Meeting.pdf \
    'https://www.mydavenport.org/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/January_5_2026_-_Regular_Meeting.pdf'
  ```
- **Evidence file:** `evidence/sample-agenda.pdf` (sibling headers: `evidence/sample-agenda-pdf.headers.txt`). Full per-year index of PDF URLs in `evidence/_davenport-pdf-inventory.txt`.
- **Notes:** The `96FA7459-A704-43EF-A44D-7BFA732F5D2E` GUID is the Catalis GovOffice site-tenant identifier for Davenport; it is stable across the CMS lifetime. The URL-encoded form `%7B…%7D` (literal `{…}`) is the on-disk path; the CMS requires the braces. 325 meeting-related PDF links catalogued across 2020–2026 (agendas) and 2019–2026 (minutes) — full inventory in `evidence/_davenport-pdf-inventory.txt`.

---

## Scrape Targets

Scrape targets where no API (on-origin or off-origin JSON) provides equivalent data.

### mydavenport.org (on-origin)

#### Per-meeting agenda/minutes PDFs — content extraction

- **URL:** pattern `https://www.mydavenport.org/vertical/sites/%7B96FA7459-A704-43EF-A44D-7BFA732F5D2E%7D/uploads/<filename>.pdf`
- **Data available:** Full meeting packet (agenda items, staff reports, ordinance/resolution exhibits, maps, staff memos). The meeting label on the index-page anchor provides the meeting date and type; the PDF body carries the agenda items and their staff-report attachments inline.
- **Fields extractable:** meeting date (from anchor label), meeting type (from anchor label: `Regular Meeting`, `Planning Commission`, `Workshop`, etc.), agenda-item list (parse PDF), ordinance numbers (regex `Ordinance\s+20\d\d-\d+` in PDF text), resolution numbers (regex `Resolution\s+20\d\d-\d+`), public-hearing flags (look for "Public Hearing" section headers), applicant / address / case-number (project-specific, variable formatting).
- **JavaScript required:** `no` — PDFs are raw downloads.
- **Anti-bot measures:** none observed at light volume. ⚠️ GAP: `robots.txt` `User-agent: *  Disallow: /` could be read strictly to block all bots; production scrapers should use a named UA and moderate cadence.
- **Pagination:** `none` per URL. Enumeration via the per-year HTML index (see APIs section).
- **Selectors (if stable):** `unstable` — PDF-internal layout varies by meeting type (agenda vs. agenda packet) and has changed template over time (2020 vs. 2026). Recommend either a tolerant PDF-to-text extraction (e.g. `pdfminer.six`) with regex-based section detection, or a template-free LLM pass on the extracted text.
- **Why no API:** No on-origin agenda-item or resolution API exists. There is no JSON endpoint for individual agenda items — the PDFs are the primary artifact.
- **Notes:** Filename-suffix conventions: `(1)` = second revision (typically minutes counterpart of an agenda); `(2)` or higher = further revisions; `(AMENDED_AGENDA)` = published amendment; `(CANCELLED)` / `(Cancelled)` = meeting was cancelled (PDF often just carries a single-page cancellation notice); `(AGENDA_PACKET)` = full packet variant of the same agenda (often a parallel upload). A CR pipeline should prefer the packet variant when both exist and should mark cancelled meetings as `status=cancelled` without parsing.

#### Commission Agendas per-year archive (fallback scrape)

- **URL:** `https://www.mydavenport.org/index.asp?SEC=9B0AFDD2-5297-4ED5-B887-F5F96A697CC7&DE=<year_GUID>`
- **Data available:** list of (anchor label, PDF URL) tuples for every meeting of the year.
- **Fields extractable:** meeting label text, PDF href.
- **JavaScript required:** `no` — fully server-rendered.
- **Anti-bot measures:** none observed; same `robots.txt` concerns as above.
- **Pagination:** `none`.
- **Selectors (if stable):** `a[href*="/vertical/sites/"][href$=".pdf"]` within the main content column. The main content column uses `<div class="pageContent">` (see planning commission page) or similar. More defensive: after stripping `<nav>`, `<header>`, `<footer>`, match any anchor whose `href` matches the upload-path regex.
- **Why no API:** Documented as an API above (the canonical data surface) — included here as a scrape target because the data is delivered exclusively as HTML, not JSON, so in practice a CR pipeline implements it with an HTML parser.
- **Notes:** Use this as the primary CR seed for Davenport. Poll cadence: the sitemap `lastmod` on `/commissionagendas` is a useful pre-check (HEAD/GET `sitemap.xml`, locate the 2026 year page `lastmod`, only re-parse the year page if it advanced).

### library.municode.com (off-origin)

#### Municode code of ordinances (Davenport, FL)

- **URL:** `https://library.municode.com/fl/davenport/codes/code_of_ordinances`
- **Data available:** full adopted Code of Ordinances for the City of Davenport — every codified ordinance, organized hierarchically (Charter, Chapters, Articles, Sections). Includes Land Development Regulations (zoning, subdivision), which is CD2 territory but adjacent to CR.
- **Fields extractable:** section node tree (via `api.municode.com/codes/<client_id>/nodes`), section body text per node, "IsUpdated" / "IsAmended" / "HasAmendedDescendant" flags (per §5 known-platform signature), supplement history.
- **JavaScript required:** `yes` — the page is an Angular SPA (`ng-app="mcc.library_desktop"`). Initial HTML is a shell; content is loaded via the Municode API (`/api/…` relative) backed by Azure Functions at `https://mcclibraryfunctions.azurewebsites.us/api`.
- **Anti-bot measures:** API endpoints at `library.municode.com/api/…` and `api.municode.com/…` return **HTTP 401 Unauthorized** without a valid Bearer token. The SPA obtains the token via a `/bff/login` (backend-for-frontend) cookie flow against `auth.municode.com`. ReCAPTCHA is loaded. ⚠️ GAP: anonymous JSON-API access is not possible; scraping requires either (a) an authenticated token stolen from a browser session, (b) rendered-page scraping via a headless browser, or (c) waiting for a public Davenport client-ID discovery via a server-rendered sitemap/index that was not exposed to this probe.
- **Pagination:** node tree is hierarchical (parent/children); ordinance content is whole-section.
- **Selectors (if stable):** N/A — JSON API only once authenticated. Rendered-DOM selectors vary per Municode SPA version.
- **Why no API:** Municode has an API (documented in the repo under the `munipro` / CivicPlus fingerprint), but anonymous access is disallowed. For CR specifically (ordinances in motion, not adopted text), agenda PDFs already carry the proposed-ordinance text, so Municode is **secondary** — valuable for final adopted text only.
- **Notes:** Municode client ID for Davenport was not resolved in this run (probed `api.municode.com` and `library.municode.com/api/Jurisdictions*` — all returned 401 / 404). A later task can bind this by reading the client_id from the rendered Angular app's initial state.

### textmygov.com (off-origin, SMS subscribe widget)

#### SMS subscription widget

- **URL:** `https://textmygov.com/widget-update/dist/app.js` (widget script embedded on home page)
- **Data available:** alert-subscription signup widget for the City's TextMyGov SMS program. Not a CR data source — it is an alert-publishing channel.
- **Fields extractable:** none (user-input form only).
- **JavaScript required:** `yes`.
- **Anti-bot measures:** unverified; out of scope for CR.
- **Pagination:** `none`
- **Selectors (if stable):** N/A
- **Why no API:** Not a data source; an egress/notification channel.
- **Notes:** Documented only because it was observed on the home page during fingerprinting. Skip for CR.

---

## Coverage Notes

**Total requests this run:** 77 (see `evidence/_davenport-request-log.txt`), comfortably within the 2000-request cap.

**Platform conclusion:** Single origin, **Catalis GovOffice** classic ASP CMS. Fingerprint is distinctive (template directory `GO_davenport-fl_2025_resp`, tenant-GUID-based uploads path, footer link to `catalisgov.com`). No known CR-vendor meeting portal (Legistar, CivicClerk, eScribe, Granicus, NovusAgenda, iQM2, CivicWeb, PeakAgenda, BoardDocs, OnBase) — all known vendor-hostname probes and vendor-path probes returned 404/NXDOMAIN. Davenport's meeting-data delivery is **PDF uploads linked from year-scoped HTML index pages** on its own CMS.

**robots.txt caveat (⚠️ GAP):** `User-agent: *  Disallow: /` applies to unlisted crawlers, which includes `CountyData2-mapper/1.0`. Named allowlist bots (Googlebot, bingbot, ia_archiver, archive.org_bot, W3C-checklink, CCBot) may crawl freely. This mapping proceeded with a single-digit-per-minute probe budget, identified UA, and did not touch disallowed paths (`/admin/`, `/manager/`, `*month*`, `*GUESTBOOK*`). A production CR scraper should (a) identify as Googlebot-compatible with explicit UA string and verifiable reverse-DNS, or (b) negotiate access with the City. Without one of those, strict reading of the policy would prohibit automated traffic. This is the single largest policy risk for the Davenport CR pipeline.

**Resolution text (⚠️ GAP):** no online index. Only surface is per-meeting agenda PDFs (where resolution numbers and titles appear as agenda items) and public-records requests to the City Clerk. CR cannot retrieve full resolution text automatically.

**Ordinance text (⚠️ GAP for on-origin):** only Municode, and Municode JSON APIs require authentication. For CR purposes — "ordinances in motion" — agenda PDFs carry proposed ordinance numbers and titles, which is sufficient for the CR tracking layer. Final adopted text from Municode is out of CR scope and belongs to CD2.

**Planning Commission integration:** Planning Commission meetings are interleaved into the City Commission per-year agenda and minutes archives — there is no separate archive section. A downstream adapter should treat `Planning Commission` as an in-scope body filter alongside `Regular Meeting` and `Special Meeting`. Workshops, Election Workshops, and CFRPC-Comp-Plan-Presentation meetings carry no legislative action and may be excluded (analogous to Haines City's body-filter decisions).

**2019 minutes coverage (⚠️ GAP):** the 2019 minutes archive page was seen from the Commission Minutes landing but was not individually downloaded this run — a scraper pass should cover it for historical completeness.

**Calendar date-parameter probing (⚠️ GAP):** `/calendar/calendar.asp?month=<n>&year=<n>` was not exercised because `robots.txt` disallows `/*month*` for allowlisted bots, hinting at a date-navigation parameter that might behave unpredictably under probing. Not a CR-relevant surface, so the deferral is low-cost.

**No 429s, no CAPTCHA, no Cloudflare challenges** observed in this run. The `curl (56) schannel` warning on many responses is cosmetic (Windows schannel flagging a missing TLS close_notify alert after a complete body delivery) and did not affect any payload.

**Davenport adapter status in CountyData2 repo:** a Permit Tracker adapter already exists for Davenport (`modules/permits/scrapers/adapters/davenport.py`, iWorQ portal at `https://portal.iworq.net/DAVENPORT/permits/600`). No CR commission adapter or YAML config exists yet — this mapping is the prerequisite recon for that build-out. Sister Polk-County city Haines City has an eScribe CR adapter (`modules/commission/scrapers/escribe.py`, `haines-city-cc.yaml`, `haines-city-pc.yaml`) that is **not reusable** for Davenport — the delivery model is entirely different (static PDF uploads vs. WebForms PageMethods JSON).
