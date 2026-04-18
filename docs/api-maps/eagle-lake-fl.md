# Eagle Lake, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.eaglelakefl.gov/` (city of Eagle Lake, FL — Polk County). One-file scope: city of Eagle Lake only — Polk County is mapped separately in `polk-county-fl.md`.
>
> Crawl in **degraded mode** (curl-only) — verified safe: the CMS is **CivicPlus Municipal Drupal on Acquia Cloud Site Factory** (host fingerprint `vyhlif14236`, `x-ah-environment: 04live`, `via: varnish`). Pages are server-rendered; no React/Vue/Next/Nuxt hydration markers. One SPA-like surface (the Accela Citizen Access portal at Polk County's tenant) is already characterized in `_platforms.md` and cross-referenced rather than deep-probed.
>
> UA: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`. Pacing ~1 req/sec. ~38 unique HTTPS requests this run; 0 × 429, 0 × captcha, 0 × WAF block.

## Summary

- **Jurisdiction:** City of Eagle Lake, Polk County, FL. Population ≈2.7k.
- **City CMS platform:** **CivicPlus Municipal Drupal on Acquia Cloud Site Factory (ACSF)** at `www.eaglelakefl.gov` (HTTP 301 from apex `eaglelakefl.gov`; Cloudflare-fronted, Acquia `04live` backend, Varnish cache). Host-scoped asset prefix `/sites/g/files/vyhlif14236/` — `vyhlif14236` is the ACSF multi-site slot for the Eagle Lake tenant. Title tag `<title>Home Page | Eagle Lake FL</title>`; generator tag empty but Drupal signatures present throughout. Footer outbound `civicplus.com` branding. Meetings and agendas surfaced through Drupal content types (`field-agendas`, `field-minutes-files`, `field-smart-date`) rendered under path patterns `/{board-slug}/meeting/{meeting-slug}` and `/{board-slug}/page/{page-slug}`.
- **Commission surface:** **Drupal-native** — no AgendaCenter, no Legistar, no Granicus, no Municode Meetings. City Commission meetings live under `/city/meeting/regular-city-commission-meeting[-N]` (76 meeting nodes in sitemap). Planning Commission under `/bc-pc/meeting/*` (20 nodes); Community Redevelopment Agency under `/bc-cra/meeting/*` (23 nodes). There is **no `/bc-cc` path** (the City Commission uses the `/city/*` prefix rather than `/bc-cc/*`, unlike the Planning Commission which does use the `bc-*` prefix convention). The aggregator landing `/meetings` enumerates upcoming only; sitemap is authoritative for historical.
- **Permit portal posture:** **DELEGATED to Polk County's Accela tenant** at `https://aca-prod.accela.com/POLKCO/` — linked from `/building`. **Eagle Lake does not operate its own Accela tenant** (the planner-specified `aca-prod.accela.com/EAGLELAKE/` 404s on Default.aspx, `/`, and every module variant; the slugs `EAGLELAKEFL`, `CITYEAGLELAKE`, `COEL`, `CEL`, `EAGLE_LAKE`, `CITYOFEAGLELAKE` all return 404 — prior-agent claim of a confirmed EAGLELAKE tenant was wrong). Eagle Lake building permits are issued through Polk County's Building Division, which is why the city CMS points there. Polk County's POLKCO tenant is a real Accela Citizen Access instance (62 KB login page, `Accela Agency Citizen Access` branding, `Building` and `Enforcement` modules confirmed 200; `Planning`, `Licenses`, `PublicWorks`, `Zoning` return 302 auth-redirects). **Deep probing of POLKCO is scope-of `polk-county-fl.md`, not this file** — recorded here as the load-bearing Eagle Lake permit finding.
- **Code of ordinances:** **Municode Library** at `https://library.municode.com/fl/eagle_lake/` (linked from `/code`). External SPA already characterized in `_platforms.md`; not deep-probed. `api.municode.com/codes/eagle_lake/nodes` returns 404 — the Municode client slug on api.municode.com is **not** `eagle_lake` for Eagle Lake; the correct slug must be rediscovered via the Angular SPA bundle (deferred to browser pass).
- **Video / live streaming:** No BoxCast, no Granicus ViewPublisher, no YouTube channel embedded on the CMS root. ⚠️ GAP: if meetings are video-archived, the archive is not linked from the home page; a future browser pass should check the meeting-detail templates for a video-embed field.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `eaglelake.legistar.com` + `eaglelakefl.legistar.com` — **dead Legistar tenant shells.** Both resolve 200 but body is the 19-byte `Invalid parameters!` (same provisioned-but-unconfigured pattern as Bartow / Lake Wales).
  - `eaglelakefl.novusagenda.com` — **broken NovusAgenda tenant.** HTTP 500 on `/`.
  - `eaglelake.granicus.com` — no tenant (404 `/ViewPublisher.php`).
  - `eaglelakefl.govbuilt.com` + `cityofeaglelake.govbuilt.com` — **GovBuilt wildcard-DNS placeholders** (31,617 / 31,625 bytes, generic `<title>GOVBUILT PLATFORM - Tomorrow's Government Built Today</title>`).
  - `eaglelake.portal.iworq.net` — **empty iWorQ tenant shell** (3,210 bytes, Laravel 404).
  - `ci-eagle-lake-fl.smartgovcommunity.com` — no SmartGov tenant (404 on root).
- **Sitemap canonical mismatch:** `/sitemap.xml` advertises **564 URLs** but every `<loc>` points to an old domain `https://www.eaglelake-fla.com/` which returns **403 Forbidden** (Cloudflare-level block — no longer the city domain). The current `www.eaglelakefl.gov` serves identical content on matched paths (verified `/community`, `/clerk`, `/city`, `/building`, `/code`, `/bc-pc`, `/bc-cra` all 200; `/bc-cc` 404). ⚠️ GAP: the CMS `simple_sitemap` module still emits the decommissioned hostname and needs reconfiguring on the tenant side; drift-detection should diff the sitemap on every run to catch when it is finally regenerated with `eaglelakefl.gov` `<loc>` values. The sitemap is still **structurally useful** — paths are correct, only the hostname is stale.
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts (NewVision BrowserView, Tyler Odyssey PRO), Polk County Legistar — all documented in `polk-county-fl.md`; parcel/court data and permits for Eagle Lake properties ride Polk's services.

**Totals:** ~38 HTTPS requests, 0 × 429, 0 × captcha; 9 APIs documented; 6 scrape targets; 2 external platforms cross-referenced (Accela POLKCO, Municode Library); 6 dead/placeholder tenants documented for negative evidence. **1 new platform row for `_platforms.md`: CivicPlus Municipal Drupal (ACSF)**.

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.eaglelakefl.gov` / `eaglelakefl.gov` | **CivicPlus Municipal Drupal (ACSF)** | LIVE | Cloudflare edge + Acquia Cloud Site Factory (`x-ah-environment: 04live`, `via: varnish`, `x-request-id: v-<uuid>`, `x-cache: HIT`); asset prefix `/sites/g/files/vyhlif14236/`; Drupal field markup (`field--name-field-agendas`, `field--name-field-minutes-files`, `field--name-field-smart-date`, `field--name-field-address`, `field--name-field-phone-number`); title pattern `<title>{Page Name} \| Eagle Lake FL</title>`; `/rss.xml` works; `/sitemap.xml` works; `/feed` 404; `/node.json` 404 (JSON:API disabled); `/jsonapi` 404; `/taxonomy/term/1/feed` returns empty RSS (feed infra exists, taxonomy term 1 has no content). **New platform added to `_platforms.md` this run.** |
| `aca-prod.accela.com/POLKCO/` | **Accela Citizen Access** (Polk County tenant — shared) | LIVE | Eagle Lake permits delegated to Polk County via `https://aca-prod.accela.com/POLKCO/Login.aspx` (linked from `/building`). Already characterized in `_platforms.md`. Deep probe lives in `polk-county-fl.md`. Module-level spot-check this run: `module=Building` and `module=Enforcement` 200; `module=Planning/Licenses/PublicWorks/Zoning` 302. |
| `library.municode.com/fl/eagle_lake/` | **Municode Library** | LIVE (external) | Angular SPA already in `_platforms.md`; not deep-mapped. `api.municode.com` client slug is **not** `eagle_lake` (404) — correct slug deferred to browser pass. |
| `eaglelake.legistar.com` + `eaglelakefl.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!` body (Bartow-pattern drift sentinel). |
| `eaglelakefl.novusagenda.com` | **NovusAgenda (broken)** | BROKEN | HTTP 500 on `/`. |
| `eaglelake.granicus.com` | — | NO TENANT | `/ViewPublisher.php?view_id=1` 404. |
| `eaglelakefl.govbuilt.com` + `cityofeaglelake.govbuilt.com` | — | PLACEHOLDER (wildcard DNS) | 31,617 / 31,625 byte generic `<title>GOVBUILT PLATFORM…</title>` (per `_platforms.md` detection discipline). |
| `eaglelake.portal.iworq.net` | — | EMPTY TENANT SHELL | 3,210 byte Laravel "Page Can Not Be Found". |
| `ci-eagle-lake-fl.smartgovcommunity.com` | — | NO TENANT | 404 on `/`. |
| `www.eaglelake-fla.com` | **(legacy decommissioned CMS)** | 403 | Apex blocked by Cloudflare. Old domain referenced by the current sitemap's stale `<loc>` values (see Coverage Notes). |

New platforms added to `docs/api-maps/_platforms.md` this run: **CivicPlus Municipal Drupal (ACSF)**.

---

## APIs

### /robots.txt

#### Robots directives

- **URL:** `https://www.eaglelakefl.gov/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard Drupal robots.txt — disallows `/core/`, `/profiles/`, `/README.md`, all `/admin/*`, `/node/*/edit`, CSS-Allow / JS-Allow carve-outs for core + profiles.
- **Response schema:** `text/plain`
- **Observed parameters:** none
- **Probed parameters:** none (static file)
- **Pagination:** `none`
- **Rate limits observed:** none at ~1 req/sec
- **Data freshness:** static (CMS-managed)
- **Discovered via:** recon step 1
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/robots.txt'`
- **Evidence file:** `evidence/eagle-lake-fl-robots.txt`
- **Notes:** No sitemap directive — sitemap is discovered via its well-known path `/sitemap.xml`. Mapping pass compliant (no `/core/`, `/profiles/`, or `/admin/*` requested).

### /sitemap.xml

#### Sitemap (stale hostname)

- **URL:** `https://www.eaglelakefl.gov/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal simple_sitemap output — 564 `<url>` entries (91,858 bytes). **All `<loc>` values reference the legacy `https://www.eaglelake-fla.com/` hostname**, which is now 403-blocked. Paths are valid on the current `www.eaglelakefl.gov`.
- **Response schema:**
  ```
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
      <loc>url</loc>
      <lastmod>iso8601</lastmod>
      <changefreq>string</changefreq>
      <priority>float</priority>
    </url>
  </urlset>
  ```
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none` — all 564 inline (one sitemap)
- **Rate limits observed:** none
- **Data freshness:** updated on CMS publish
- **Discovered via:** well-known path
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/sitemap.xml'`
- **Evidence file:** `evidence/eagle-lake-fl-sitemap.xml`
- **Notes:** ⚠️ GAP — the `<loc>` hostname is **stale and must be regex-substituted** before use. Canonical transform: replace `https://www.eaglelake-fla.com` with `https://www.eaglelakefl.gov`. Meeting breakdown from sitemap paths: `/city/meeting/*` = 76 City Commission meetings; `/bc-pc/meeting/*` = 20 Planning Commission meetings; `/bc-cra/meeting/*` = 23 CRA meetings. Recommend the production drift detector open a ticket with the tenant to regenerate the sitemap with the current hostname.

### /rss.xml

#### Site-wide RSS feed

- **URL:** `https://www.eaglelakefl.gov/rss.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal default RSS feed — latest nodes across the whole site (news + meetings + pages). 10,701 bytes, ~10 items per fetch.
- **Response schema:**
  ```
  <rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
    <channel>
      <title>string</title>
      <link>url</link>
      <description/>
      <language>string</language>
      <item>
        <title>string</title>
        <link>url</link>
        <description>escaped-html</description>
        <pubDate>rfc822</pubDate>
        <dc:creator>string</dc:creator>
        <guid isPermaLink="bool">{node-id} at {hostname}</guid>
      </item>
    </channel>
  </rss>
  ```
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none` — trailing window (~10 items)
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** Drupal default feed path
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/rss.xml'`
- **Evidence file:** `evidence/eagle-lake-fl-drupal-rss.xml.out`
- **Notes:** The `<link>` values in items use the live `eaglelakefl.gov` hostname (unlike the sitemap). Primary lightweight monitoring feed for CR-style drift detection. `<guid>` format `"{nid} at {hostname}"` gives stable node IDs.

### /taxonomy/term/{tid}/feed

#### Taxonomy-term RSS (per-term)

- **URL:** `https://www.eaglelakefl.gov/taxonomy/term/{tid}/feed`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal per-taxonomy-term RSS feed. Term 1 returns an empty `<channel>` (303-byte skeleton) — the taxonomy exists but has no tagged content at term id 1.
- **Response schema:** same RSS shape as `/rss.xml`
- **Observed parameters:**
  - `tid` (int, required, via path) — taxonomy term id
- **Probed parameters:**
  - `tid=1` → 200 with empty channel; higher tids not enumerated this run (⚠️ GAP)
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** Drupal convention
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/taxonomy/term/1/feed'`
- **Evidence file:** `evidence/eagle-lake-fl-taxonomy-term-1-feed.out`
- **Notes:** Term IDs must be discovered — the `/taxonomy` index is not public. A future browser pass should enumerate term IDs from the CMS admin breadcrumbs or from `og:` tags on article pages.

### /search

#### Drupal Search API / Search Autocomplete

- **URL:** `https://www.eaglelakefl.gov/search`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Full-text search result HTML (server-rendered). Not strictly a JSON API, but returns a structured search results page when `keys=` is set. The Drupal `search_api_autocomplete` JSON endpoint at `/search/autocomplete/search_api_autocomplete` returns 404 — autocomplete is not exposed publicly on this tenant.
- **Response schema:** HTML
- **Observed parameters:**
  - `keys` (string, optional) — search term
- **Probed parameters:**
  - `keys=permit` → 200, 29,590 bytes, result listing
  - autocomplete path → 404 (feature disabled)
- **Pagination:** HTML-level (Drupal pager URL params `?page=N`)
- **Rate limits observed:** none
- **Data freshness:** real-time index
- **Discovered via:** standard Drupal path
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/search?keys=permit'`
- **Evidence file:** `evidence/eagle-lake-fl-search.html`
- **Notes:** Because this returns HTML, it lives here only because it is the only indexable data surface beyond RSS + sitemap; it is the fallback mechanism to rediscover paths when the sitemap hostname is stale. True entry is **Scrape Target** class but documented here once because it exposes a structured URL parameter space.

### /print/pdf/node/{nid}

#### Printable-PDF render

- **URL:** `https://www.eaglelakefl.gov/print/pdf/node/{nid}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Server-rendered PDF of a given Drupal node. Triggered by Drupal `entity_print` / `print_pdf` module. Nodes include meetings (e.g. `/print/pdf/node/2293` on a City Commission meeting detail).
- **Response schema:** `application/pdf` binary
- **Observed parameters:**
  - `nid` (int, required, via path)
- **Probed parameters:** not enumerated — valid nids are extracted from meeting-detail pages via the `/print/pdf/node/{nid}` link in each
- **Pagination:** n/a
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** `/city/meeting/regular-city-commission-meeting` meeting-detail template
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/print/pdf/node/2293' -o sample.pdf`
- **Evidence file:** not captured (binary; ~1-2 MB each; skipped to conserve evidence dir)
- **Notes:** PDF rendering of the full meeting detail page — not the agenda PDF itself. The actual agenda attachment PDFs are referenced via a `field-agendas` entity-reference on the meeting node and live under `/sites/g/files/vyhlif14236/files/…`. ⚠️ GAP: a future pass should extract one sample agenda-file URL from `/city/meeting/regular-city-commission-meeting` HTML to characterize the `sites/g/files` attachment-path convention.

### /sites/g/files/vyhlif14236/files/

#### ACSF file asset tree

- **URL:** `https://www.eaglelakefl.gov/sites/g/files/vyhlif14236/files/{…}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary file assets — agenda PDFs, minutes PDFs, image uploads, CSS/JS bundles. Served directly by Acquia + Cloudflare; cached aggressively.
- **Response schema:** varies (application/pdf, image/png, text/css, application/javascript)
- **Observed parameters:** none on the file-GET itself
- **Probed parameters:** none
- **Pagination:** n/a
- **Rate limits observed:** none (CDN-fronted)
- **Data freshness:** immutable per-path (CSS/JS bundles carry hash-based filenames); user-uploaded files have stable paths
- **Discovered via:** page source of `/`, `/city/meeting/*`
- **curl:** `curl -A "$UA" 'https://www.eaglelakefl.gov/sites/g/files/vyhlif14236/files/…'`
- **Evidence file:** not captured (binary)
- **Notes:** Path segment `vyhlif14236` is the ACSF multi-site slot id — stable for the lifetime of the tenant. Agenda/minute PDFs are referenced from meeting-node HTML via this path prefix.

### Polk County Accela Citizen Access (cross-reference)

#### POLKCO Citizen Access login landing

- **URL:** `https://aca-prod.accela.com/POLKCO/Login.aspx`
- **Method:** `GET`
- **Auth:** `none` (anonymous landing; deeper search/apply requires account)
- **Data returned:** Accela Citizen Access login page. HTML. 62,921 bytes. Title `<title>Accela Agency Citizen Access</title>`.
- **Response schema:** HTML (see `pt/adapters/accela_html.py`)
- **Observed parameters:** none on the Login page; deeper module URLs use `module=Building|Enforcement|Planning|Licenses|PublicWorks|Zoning`
- **Probed parameters:**
  - `module=Building` → 200 (270,725 bytes; module provisioned and searchable anonymously — see `polk-county-fl.md`)
  - `module=Enforcement` → 200 (229,040 bytes; provisioned)
  - `module=Planning`, `module=Licenses`, `module=PublicWorks`, `module=Zoning` → 302 to `Login.aspx` (modules exist but search requires auth; or the redirect is due to tenant-level module configuration)
- **Pagination:** standard Accela CAP search pagination; characterized in the PT adapter
- **Rate limits observed:** none at 1 req/sec on the landing
- **Data freshness:** real-time
- **Discovered via:** `/building` on the Eagle Lake CMS outbound link
- **curl:** `curl -A "$UA" -L 'https://aca-prod.accela.com/POLKCO/Login.aspx'`
- **Evidence file:** `evidence/eagle-lake-fl-accela-polkco.html`
- **Notes:** **This endpoint is Polk County's, not Eagle Lake's.** Eagle Lake delegates all permit issuance to Polk County's Building Division. Deep-probing the POLKCO tenant is scope-of `polk-county-fl.md`. Recorded here only because `/building` on the Eagle Lake CMS is the entry point for any PT-style ingestion of Eagle-Lake-located permits.

---

## Scrape Targets

### /

#### Home page (CMS landing)

- **URL:** `https://www.eaglelakefl.gov/`
- **Data available:** banner image, quick-links, news teaser, upcoming-meetings teaser, directory teasers.
- **Fields extractable:** announcement text, event dates, staff names, phone numbers.
- **JavaScript required:** no — server-rendered.
- **Anti-bot measures:** none observed at 1 req/sec (Cloudflare edge, no challenge issued).
- **Pagination:** n/a
- **Selectors:** Drupal field markup — `.field--name-field-*`
- **Why no API:** no JSON:API on this ACSF tenant (404 on `/jsonapi`); the RSS feeds cover news/meetings but not the full home-page composition.
- **Notes:** Primary drift-detection target for CMS-shape changes.

### /city/meeting/{meeting-slug}

#### City Commission meeting detail

- **URL:** `https://www.eaglelakefl.gov/city/meeting/regular-city-commission-meeting[-N]`
- **Data available:** meeting title, date/time (field-smart-date), location (field-address), agenda attachments (field-agendas), minutes attachments (field-minutes-files), printable-PDF link.
- **Fields extractable:** meeting metadata, downloadable agenda and minutes file URLs under `/sites/g/files/vyhlif14236/files/`.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** not on this page — meeting index is the sitemap (filtered by `/city/meeting/` prefix) or the `/meetings` aggregator.
- **Selectors:** `.field--name-field-agendas a`, `.field--name-field-minutes-files a`, `.field--name-field-smart-date time[datetime]`
- **Why no API:** JSON:API disabled on this ACSF tenant; no REST node export enabled.
- **Notes:** 76 city-commission meetings in sitemap (all with stale hostname). Each page exposes agenda + minutes attachments; this is the CR-primary surface for Eagle Lake.

### /bc-pc/meeting/{meeting-slug}

#### Planning Commission meeting detail

- **URL:** `https://www.eaglelakefl.gov/bc-pc/meeting/regular-planning-commission-meeting[-N]`
- **Data available:** same shape as City Commission meeting detail.
- **Fields extractable:** same (agendas + minutes)
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a (listing at `/bc-pc` + sitemap)
- **Selectors:** same Drupal field markup
- **Why no API:** see above
- **Notes:** 20 meetings in sitemap.

### /bc-cra/meeting/{meeting-slug}

#### CRA meeting detail

- **URL:** `https://www.eaglelakefl.gov/bc-cra/meeting/regular-cra-meeting[-N]`
- **Data available:** same shape.
- **Fields extractable:** same
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** same Drupal field markup
- **Why no API:** see above
- **Notes:** 23 meetings in sitemap.

### /meetings

#### Upcoming-meetings aggregator

- **URL:** `https://www.eaglelakefl.gov/meetings`
- **Data available:** upcoming meetings only — does not include historical. 33,328 bytes.
- **Fields extractable:** title, date, link to detail
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** implicit — only upcoming shown
- **Selectors:** standard Drupal view output
- **Why no API:** no Drupal view JSON endpoint exposed
- **Notes:** Use sitemap (with hostname substitution) or per-board pages for historical; use this for what-is-next.

### /building

#### Building Department landing — **gateway to Polk County Accela**

- **URL:** `https://www.eaglelakefl.gov/building`
- **Data available:** Building Department description, staff directory, and the **outbound link to `https://aca-prod.accela.com/POLKCO/Login.aspx`** that is the load-bearing finding. Also links to `library.municode.com/fl/eagle_lake/codes/land_development_regulations_*`, `polkpa.org` (Polk County Property Appraiser), and `myfloridalicense.com` (state contractor licensing).
- **Fields extractable:** outbound-portal URLs.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a (single page)
- **Selectors:** outbound `<a href=...>` tags
- **Why no API:** this is a CMS content page, not a data surface.
- **Notes:** **This page is the permission-granting evidence for using POLKCO Accela as Eagle Lake's permit source.** If this page ever stops linking to POLKCO, re-probe — that would signal Eagle Lake has stood up its own portal.

---

## Coverage Notes

- `robots.txt` read and respected. No disallowed paths were probed. No 429 or captcha observed.
- **⚠️ GAP (sitemap hostname):** `/sitemap.xml` emits 564 `<loc>` values against the decommissioned `eaglelake-fla.com` hostname. Paths are valid; hostname must be rewritten to `eaglelakefl.gov`. Re-probe next run to detect a fix.
- **⚠️ GAP (Accela EAGLELAKE):** prior agent's assertion of a confirmed `aca-prod.accela.com/EAGLELAKE/` tenant was wrong — Eagle Lake delegates to POLKCO. Correction captured in Summary; `_platforms.md` unchanged (Accela row already present).
- **⚠️ GAP (Municode slug):** `api.municode.com/codes/eagle_lake/nodes` returns 404; correct slug must be rediscovered via the Angular SPA bundle on a browser pass.
- **⚠️ GAP (video archive):** no BoxCast/Granicus/YouTube video link visible from the CMS root or building/clerk pages. Meeting-detail templates may carry a `field-video` — untested this run.
- **⚠️ GAP (taxonomy term IDs):** `/taxonomy/term/1/feed` works; higher tids not enumerated. Browser pass should walk the taxonomy admin or scrape `og:` tags on article pages.
- **Graveyard discipline:** six dead/placeholder vendor tenants documented for negative evidence (Legistar x2, NovusAgenda, Granicus, GovBuilt x2, iWorQ, SmartGov) — consistent with the Bartow / Lake Wales pattern.
- **Total HTTPS requests this run:** ~38 (well under 2000 cap). Request log: `evidence/_eagle-lake-fl-request-log.txt`.
