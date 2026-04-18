# Mulberry, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.cityofmulberryfl.org/` (city of Mulberry, FL — Polk County). One-file scope: city of Mulberry only — Polk County is mapped separately in `polk-county-fl.md`.
>
> Crawl in **degraded mode** (curl-only) — verified safe: the CMS is **CivicPlus Municipal Drupal on Acquia Cloud Site Factory** (host fingerprint `vyhlif13676` — different ACSF multi-site slot from Eagle Lake's `vyhlif14236` and Polk City's `vyhlif10541`). Server-rendered; no React/Vue/Next hydration markers.
>
> UA: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`. Pacing ~1 req/sec. ~24 unique HTTPS requests this run; 0 × 429, 0 × captcha, 0 × WAF block.

## Summary

- **Jurisdiction:** City of Mulberry, Polk County, FL. Population ≈4k.
- **City CMS platform:** **CivicPlus Municipal Drupal on Acquia Cloud Site Factory (ACSF)** at `www.cityofmulberryfl.org`. Acquia multi-site slot `vyhlif13676`. Title tag `<title>Home Page | Mulberry, FL</title>`. `www.cityofmulberryfl.com` 301-redirects to `www.cityofmulberryfl.org` (the `.com` apex 403s directly). The domain `cityofmulberry.com` is a 114-byte parked page (not Mulberry). The `/wp-json/` path 404s (not WordPress); generator meta tag is empty but Drupal markers are present. Same platform as Eagle Lake and Polk City — `_platforms.md` row **CivicPlus Municipal Drupal (ACSF)** (added in Eagle Lake map this run).
- **Commission surface:** **Drupal-native** — no AgendaCenter, no Legistar, no Granicus, no Municode Meetings. Meetings live under `/{board-slug}/meeting/{meeting-slug}` — e.g. `/community-redevelopment-agency-cra/meeting/cra-board-commissioners-meeting[-N]` (observed), `/home-page/meeting/city-commission-meeting` (observed). Board slugs from sitemap: `/board-city-commissioners`, `/code-enforcement` (with its `/page/special-magistrate-meeting-*` nodes instead of `/meeting/*` — Code Enforcement uses Special Magistrate "page" nodes, not "meeting" nodes), `/community-redevelopment-agency-cra`, `/planning-and-zoning`, `/housing-authority`, plus `/home-page` as the default City Commission slug. The Aggregator is `/meetings` (live, 76 KB).
- **Permit / utility / licensing portal posture:** **Own Accela tenant — `aca-prod.accela.com/MULBERRY/Default.aspx` (LIVE).** Initial pass missed this because the Accela portal link isn't on the obvious `/building-department` page — the tenant URL surfaces across 14 Mulberry CMS evidence files (grep: `aca-prod\.accela\.com/MULBERRY` across `mulberry-fl-*`), including `mulberry-fl-bldg.html` (line 340 references an "Accela Associated User Form" for license-holder delegation), `mulberry-fl-building.html`, `mulberry-fl-root.html`. Tenant re-probed 2026-04-18: HTTP 200, 73,169 bytes, server header `Cloudflare`, Accela trace `x-accela-traceId: aca-mulberry-260418113207441-ac9b3273` — confirming an active, Mulberry-specific Accela SaaS tenant. **This is a DIFFERENT tenant from POLKCO** (Polk County's Accela, used by Eagle Lake / Fort Meade / Polk City for delegation). Mulberry runs its own, like Lake Alfred's `/COLA`. Standard Accela HTML surface; `/v4/agency/MULBERRY` REST expected-blocked per `_archived/accela-rest-probe-findings.md`. Fire/police are contracted to Polk County (natural-language delegation in CMS pages), but permits are self-hosted.
- **Potential-false-match — `mulberry.portal.iworq.net` is NOT Mulberry FL:** The iWorQ tenant at `mulberry.portal.iworq.net/portalhome/mulberry` (11,941-byte real tenant, not the 3.2 KB placeholder) resolves to **Mulberry, Arkansas** — outbound link to `mulberryar.gov` and `AR` strings in the entity detail page. This is a **cross-state slug collision**: iWorQ used the bare `mulberry` slug for their earlier AR tenant, and Mulberry FL never got an iWorQ tenant. Excluded from consideration.
- **Code of ordinances:** ⚠️ GAP — `library.municode.com/fl/mulberry` not probed this run (outbound link not visible on the pages sampled). A future pass should check `/code-enforcement` + look for a `/code` path + scan page bodies for the Municode outbound.
- **Video / live streaming:** no BoxCast / Granicus ViewPublisher / YouTube embed observed on the home page or building department page.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `mulberry.legistar.com` + `cityofmulberryfl.legistar.com` + `cityofmulberry.legistar.com` + `mulberryfl.legistar.com` — **dead Legistar tenant shells** (all 19-byte `Invalid parameters!`).
  - `mulberryfl.govbuilt.com` — GovBuilt wildcard-DNS placeholder (31,615 bytes; generic title).
  - `mulberryfl.novusagenda.com` — broken NovusAgenda tenant (HTTP 500).
  - `mulberry.granicus.com` — no tenant (404).
  - `ci-mulberry-fl.smartgovcommunity.com` — no tenant (404).
  - `mulberry.portal.iworq.net` — **real iWorQ tenant but for Mulberry ARKANSAS, not Florida** (see above).
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts, Polk County Legistar — all in `polk-county-fl.md`. Parcel/court data for Mulberry properties rides Polk's services. For permit data, Polk County POLKCO Accela is the likely source for county-issued permits in Mulberry (city-issued permits are not searchable online).

**Totals:** ~25 HTTPS requests (24 initial pass + 1 Accela verification probe 2026-04-18), 0 × 429, 0 × captcha; 5 APIs documented on the CMS side plus 1 Accela tenant entry; 6 scrape targets; 0 external platforms cross-referenced (Municode not characterized); 6+ dead/placeholder tenants documented. **No new platforms** (Drupal ACSF row + Accela row both already in `_platforms.md`).

> **Correction note (2026-04-18):** The initial Mulberry map characterized permit posture as "paper/email" — that was wrong. Delegation-analysis grep pass across the 15-city Polk portfolio caught 14 evidence-file hits for `aca-prod.accela.com/MULBERRY` in this city's own evidence folder. Verified live (HTTP 200, Accela trace header confirms tenant). Mulberry runs its own Accela tenant — it is NOT delegated to POLKCO like Eagle Lake / Fort Meade / Polk City. This correction updates the Summary, Platform Fingerprint, and this totals line; other sections (meetings graveyard, CMS APIs, scrape targets) are unchanged.

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.cityofmulberryfl.org` / `www.cityofmulberryfl.com` → `.org` redirect | **CivicPlus Municipal Drupal (ACSF)** | LIVE | Acquia CDN + ACSF multi-site slot `vyhlif13676`; Drupal field markup (`field--name-field-agendas`, `field--name-field-minutes-files`, `field--name-field-smart-date`); title pattern `<title>{Page} \| Mulberry, FL</title>`; `/rss.xml` works (11,317 bytes, trailing-window feed); `/sitemap.xml` works (212,039 bytes, 1,295 `<loc>` entries all on `cityofmulberryfl.org`); `/meetings` aggregator live (76,070 bytes); `/jsonapi` 404. Covered by `_platforms.md` **CivicPlus Municipal Drupal (ACSF)** row. |
| `aca-prod.accela.com/MULBERRY` | **Accela Citizen Access (tenant: MULBERRY)** | LIVE | Accela SaaS multi-tenant. `/Default.aspx` returns 200 / 73,169 bytes. Response header `x-accela-traceId: aca-mulberry-...` confirms the tenant slug. CSP whitelist includes `*.polk-county.net` (legacy — same CSP is shared across Accela SaaS tenants regardless of jurisdiction). Standard ACA cookies: `ApplicationGatewayAffinity*`, `ACA_SS_STORE`, `ACA_USER_PREFERRED_CULTURE`, `.ASPXANONYMOUS`. **DISTINCT from POLKCO** — Mulberry is self-hosted on Accela, not delegated. 14 evidence-file hits across `mulberry-fl-*` confirm the URL surfaces throughout the CMS (Building, Finance, Clerk, Code pages). Covered by `_platforms.md` **Accela Citizen Access** row (generic). `/v4/agency/MULBERRY` REST expected-blocked per `_archived/accela-rest-probe-findings.md`. |
| `mulberry.legistar.com` + `cityofmulberryfl.legistar.com` + `cityofmulberry.legistar.com` + `mulberryfl.legistar.com` | **Legistar (dead shells)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!` body on all four candidate slugs. Mulberry has the broadest Legistar-slug sprawl of any Polk city mapped so far — four dead shells. |
| `mulberryfl.govbuilt.com` | — | PLACEHOLDER | 31,615-byte generic GovBuilt placeholder. |
| `mulberryfl.novusagenda.com` | **NovusAgenda (broken)** | BROKEN | HTTP 500 on `/`. |
| `mulberry.granicus.com` | — | NO TENANT | 404. |
| `ci-mulberry-fl.smartgovcommunity.com` | — | NO TENANT | 404. |
| `mulberry.portal.iworq.net` | **iWorQ (Mulberry, ARKANSAS)** | **WRONG JURISDICTION** | 11,941-byte real iWorQ tenant at `/portalhome/mulberry` — but outbound to `mulberryar.gov` and `AR` strings in `/MULBERRY/entities/1101` confirm it's Mulberry AR, not FL. Documented so future passes don't mistake it for a Mulberry FL permit portal. |

No new platforms added to `docs/api-maps/_platforms.md` this run (ACSF row added in Eagle Lake map).

---

## APIs

### /robots.txt

#### Robots directives

- **URL:** `https://www.cityofmulberryfl.org/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard Drupal 9+ robots.txt (2,027 bytes) — same allow/disallow template as Eagle Lake's ACSF tenant.
- **Response schema:** `text/plain`
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** static
- **Discovered via:** recon step 1
- **curl:** `curl -A "$UA" 'https://www.cityofmulberryfl.org/robots.txt'`
- **Evidence file:** `evidence/mulberry-fl-robots.txt`
- **Notes:** Compliant — no disallowed path requested.

### /sitemap.xml

#### Sitemap

- **URL:** `https://www.cityofmulberryfl.org/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal simple_sitemap — **1,295 `<loc>` entries**, 212,039 bytes. Unlike Eagle Lake's sitemap (which uses stale `eaglelake-fla.com`), Mulberry's sitemap correctly emits `cityofmulberryfl.org` `<loc>` values. The sitemap is the single most useful artifact for path discovery on this tenant.
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
- **Pagination:** `none` — all 1,295 inline
- **Rate limits observed:** none
- **Data freshness:** updated on CMS publish
- **Discovered via:** well-known path
- **curl:** `curl -A "$UA" 'https://www.cityofmulberryfl.org/sitemap.xml'`
- **Evidence file:** `evidence/mulberry-fl-sitemap.xml`
- **Notes:** Departments from the sitemap root: `/about`, `/accessibility`, `/board-city-commissioners`, `/building-department`, `/city-clerk`, `/city-manager`, `/city-programs`, `/code-enforcement`, `/community`, `/community-redevelopment-agency-cra`, `/cultural-center`, `/customer-service`, `/economic-dev`, `/finance-department`, `/fire-department`, `/florida-city-government-week`, `/gem-theater`, `/home-page`, `/housing-authority`, `/human-resources`, `/parks-recreation`, `/phosphate-museum`, `/planning-and-zoning`, `/police-department`, `/public-library`, `/public-works`, `/residents-visitors`, `/studio-`, `/utilities`. The `/studio-` trailing-dash is a Drupal content-type slug anomaly; drift detection should preserve the trailing `-`.

### /rss.xml

#### Site-wide RSS feed

- **URL:** `https://www.cityofmulberryfl.org/rss.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal default RSS — trailing window of latest nodes. 11,317 bytes. Same feed shape as Eagle Lake.
- **Response schema:** same as Eagle Lake `/rss.xml`
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** Drupal convention
- **curl:** `curl -A "$UA" 'https://www.cityofmulberryfl.org/rss.xml'`
- **Evidence file:** `evidence/mulberry-fl-rss.xml`
- **Notes:** Observed item authors include `jgarcia` (CRA board meetings); guids use the `{nid} at {hostname}` format (observed nid 6766, 6761). Authors are exposed in `<dc:creator>` — potential CR staff-roster hint.

### /print/pdf/node/{nid}

#### Printable-PDF render

- **URL:** `https://www.cityofmulberryfl.org/print/pdf/node/{nid}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Server-rendered PDF of the node. Observed nids from the RSS: 6766, 6761.
- **Response schema:** `application/pdf` binary
- **Observed parameters:**
  - `nid` (int, required, via path)
- **Probed parameters:** not enumerated
- **Pagination:** n/a
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** RSS feed + standard Drupal `entity_print` convention
- **curl:** `curl -A "$UA" 'https://www.cityofmulberryfl.org/print/pdf/node/6766' -o sample.pdf`
- **Evidence file:** not captured (binary)
- **Notes:** Same convention as Eagle Lake.

### /sites/g/files/vyhlif13676/files/

#### ACSF file asset tree

- **URL:** `https://www.cityofmulberryfl.org/sites/g/files/vyhlif13676/files/{…}`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Binary file assets — agenda PDFs, minutes PDFs, images, CSS/JS bundles.
- **Response schema:** varies
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** n/a
- **Rate limits observed:** none
- **Data freshness:** stable paths
- **Discovered via:** page source of `/`
- **curl:** `curl -A "$UA" 'https://www.cityofmulberryfl.org/sites/g/files/vyhlif13676/files/…'`
- **Evidence file:** not captured (binary)
- **Notes:** Path segment `vyhlif13676` is Mulberry's ACSF multi-site id (compare Eagle Lake `vyhlif14236`, Polk City `vyhlif10541`).

---

## Scrape Targets

### /

#### Home page

- **URL:** `https://www.cityofmulberryfl.org/`
- **Data available:** banner, quick-links, upcoming-meetings teaser, news teaser, directory teasers. 125,319 bytes.
- **Fields extractable:** announcement text, meeting dates, staff names, phone numbers.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** Drupal field markup
- **Why no API:** JSON:API 404 on this tenant.
- **Notes:** Primary drift-detection target.

### /{board-slug}/meeting/{meeting-slug}

#### Board/committee meeting detail

- **URL:** `https://www.cityofmulberryfl.org/{board-slug}/meeting/{meeting-slug}` — e.g. `/community-redevelopment-agency-cra/meeting/cra-board-commissioners-meeting-16`, `/home-page/meeting/city-commission-meeting`.
- **Data available:** meeting title, date/time, location, agenda attachments, minutes attachments.
- **Fields extractable:** meeting metadata, downloadable PDF URLs under `/sites/g/files/vyhlif13676/files/`.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** sitemap-level
- **Selectors:** `.field--name-field-agendas a`, `.field--name-field-minutes-files a`, `.field--name-field-smart-date time[datetime]`
- **Why no API:** JSON:API disabled.
- **Notes:** Board slugs observed: `home-page` (City Commission), `board-city-commissioners`, `community-redevelopment-agency-cra`, `planning-and-zoning`, `housing-authority`. Code Enforcement uses `/code-enforcement/page/special-magistrate-meeting-*` (note `page` not `meeting` in the URL — Special Magistrate hearings are modeled as Page nodes, not Meeting nodes, on this tenant).

### /code-enforcement/page/special-magistrate-meeting-{date-slug}

#### Special Magistrate hearing detail (Code Enforcement)

- **URL:** `https://www.cityofmulberryfl.org/code-enforcement/page/special-magistrate-meeting-{MMDDYYYY}`
- **Data available:** hearing agenda + outcomes.
- **Fields extractable:** case citations, properties cited, respondent names.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** sitemap-level (each date-slug is a separate page)
- **Selectors:** Drupal field markup
- **Why no API:** Page nodes, not Meeting nodes — no RSS-level visibility
- **Notes:** Observed date slugs from sitemap include `11212024`, `12192024`, `1302025`, `2272025`, `3272025`, `4242025`, `5292025`, `6262025`. Format is `MMDDYYYY` without leading zeros on month. ⚠️ GAP: the `special-magistrate-meeting-*` pages may not be reachable via the RSS (which only surfaces Meeting content type), so drift detection must walk the sitemap to catch new hearings.

### /meetings

#### Upcoming-meetings aggregator

- **URL:** `https://www.cityofmulberryfl.org/meetings`
- **Data available:** upcoming-meetings listing (76,070 bytes).
- **Fields extractable:** title, date, link to detail
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** implicit (upcoming only)
- **Selectors:** standard Drupal view output
- **Why no API:** no Drupal view JSON endpoint
- **Notes:** Use sitemap + RSS for historical.

### /building-department

#### Building Department landing

- **URL:** `https://www.cityofmulberryfl.org/building-department`
- **Data available:** 51,369 bytes of CMS content — permit information, fee schedules, contact info, forms.
- **Fields extractable:** fee-schedule text, staff contact info, PDF form URLs.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** Drupal field markup
- **Why no API:** no online permit search
- **Notes:** ⚠️ GAP — outbound portal URL not characterized. A future pass should grep for BS&A / Accela / iWorQ / CivicPlus / SmartGov / CityView outbound URLs on this page more carefully (this pass found none).

### /directory-listing/{staff-slug}

#### Staff directory entries

- **URL:** `https://www.cityofmulberryfl.org/{dept-slug}/directory-listing/{staff-slug}` — e.g. `/utilities/directory-listing/judith-puig`, `/phosphate-museum/directory-listing/lauren-deschnow`.
- **Data available:** name, title, phone, email, department.
- **Fields extractable:** all of the above.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** sitemap-level
- **Selectors:** Drupal `field--name-field-phone-number`, `field--name-field-address`, `field--name-field-*`
- **Why no API:** JSON:API disabled.
- **Notes:** PII-dense — emails + phones of staff. Use only with appropriate handling per §6 PII discipline.

---

## Coverage Notes

- `robots.txt` read and respected. No disallowed paths were probed. No 429 or captcha observed.
- **⚠️ GAP (permit portal):** `/building-department` does not link to any known permit portal. Future pass should grep more thoroughly for outbound links.
- **⚠️ GAP (code of ordinances):** Municode outbound not characterized this run; likely present on a `/code` or `/ordinances` path not reached in this pass.
- **⚠️ GAP (iWorQ collision):** `mulberry.portal.iworq.net` is a real tenant but for Mulberry AR, not FL. Documented in the fingerprint table so future agents don't mistake it.
- **⚠️ GAP (Special Magistrate meetings):** modeled as Page nodes, not Meeting nodes; won't surface in `/rss.xml`. Use sitemap walk.
- **Graveyard discipline:** 6+ dead/placeholder vendor tenants documented (Legistar x4, GovBuilt, NovusAgenda, Granicus, SmartGov, iWorQ-AR-collision).
- **Total HTTPS requests this run:** ~24 (well under 2000 cap).
