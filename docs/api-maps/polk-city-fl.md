# Polk City, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.mypolkcity.org/` (city of Polk City, FL — Polk County). One-file scope: city of Polk City only — Polk County is mapped separately in `polk-county-fl.md`.
>
> **Note on naming:** the canonical city domain is the non-intuitive `mypolkcity.org` — all the expected alternates (`polkcityfl.gov`, `cityofpolkcity.com`, `polkcity.org`, `polkcityfl.com`, `polkcity.gov`, `polkcity.net`) either fail DNS or return a 114-byte parked page. The "Polk City" name collides with Polk County's parent name, which likely led the city to pick the `mypolkcity` prefix to disambiguate.
>
> Crawl in **degraded mode** (curl-only) — verified safe: the CMS is **CivicPlus Municipal Drupal on Acquia Cloud Site Factory** (host fingerprint `vyhlif10541` — the lowest-numbered ACSF slot of the three Polk Drupal tenants mapped, suggesting the earliest provisioning date). Server-rendered; no React/Vue/Next hydration markers.
>
> UA: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`. Pacing ~1 req/sec. ~20 unique HTTPS requests this run; 0 × 429, 0 × captcha, 0 × WAF block.

## Summary

- **Jurisdiction:** City of Polk City, Polk County, FL. Population ≈3.6k.
- **City CMS platform:** **CivicPlus Municipal Drupal on Acquia Cloud Site Factory (ACSF)** at `www.mypolkcity.org`. Acquia multi-site slot `vyhlif10541`. Title tag `<title>Home Page | Polk City FL</title>`. Same platform as Eagle Lake (`vyhlif14236`) and Mulberry (`vyhlif13676`) — covered by the `CivicPlus Municipal Drupal (ACSF)` row added to `_platforms.md` in the Eagle Lake map this run.
- **⚠️ CRITICAL LEAK — sitemap reveals ACSF internal hostname:** `/sitemap.xml` returns a **336-byte single-entry sitemap** whose sole `<loc>` is `http://d9template1.test-civiccms.acsitefactory.com/` — the **ACSF internal staging/template hostname for the Drupal 9 template**. This indicates the tenant's simple_sitemap module was left pointing at the template source rather than the production hostname. **The sitemap is effectively useless as an index for Polk City** (only the template homepage, wrong hostname); all path discovery for Polk City must be done from the RSS feed + HTML link-walking on the home page. This is a different failure mode from Eagle Lake (which has 564 entries but wrong hostname on all of them) — Polk City's sitemap is simply not populated.
- **Commission surface:** **Drupal-native** — meetings live under `/administration/meeting/{meeting-slug}` (observed: `/administration/meeting/city-commission-meeting-0`) and under `/city-commission/page/city-commission-meeting-{N}` (observed: meetings 1, 2, 3, 4, 5 on home page). Split between `/administration/meeting/*` (Meeting content type) and `/city-commission/page/*` (Page content type) suggests a tenant-level inconsistency similar to Mulberry's Special Magistrate pattern. ⚠️ GAP: the full set of board slugs has not been enumerated — no Planning Commission, CRA, or Code Enforcement path surfaced in the pages sampled this run.
- **Permit / utility / licensing portal posture:** ⚠️ GAP — `/building` returns 200 (39,016 bytes) but outbound-portal characterization is incomplete. No outbound BS&A / Accela / iWorQ / GovBuilt / CivicPlus portal / SmartGov / CityView / EnerGov / Cloudpermit / PermitTrax URL visible in the samples taken. Deeper building-department body scan deferred.
- **Notable public-service pages observed from home page:** `/home-page/page/duke-energy-pole-replacement-projects-close-lake-mabel-loop-road-and-old-polk-city`, `/home-page/page/tire-collection-event-april-18-2026-bronson-center`, `/water/page/2023-water-quality-reports-polk-city-and-mt-olive`, `/administration/page/textmygov-announcement`, `/administration/page/swfwmd-declared-severe-water-shortage` — indicates TextMyGov subscription-based alert system is in use and SWFWMD water-restriction notices are being published. ⚠️ GAP: TextMyGov API not probed.
- **Code of ordinances:** ⚠️ GAP — Municode outbound not observed on the home page or `/calendar`. A future pass should check `/city-commission`, `/document-library`, and specifically grep for `library.municode.com` / `amlegal.com` / `codelibrary.amlegal.com`.
- **Video / live streaming:** ⚠️ GAP — no BoxCast / Granicus / YouTube embed observed on home page.
- **WP-json is 403-blocked:** `/wp-json/` returns 403 (4,554 bytes, not a Drupal 404) — this is unusual for an ACSF Drupal tenant; likely a WAF rule blocking the WordPress path prefix specifically. Not meaningful (this is Drupal, not WordPress), but worth noting.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `polkcity.legistar.com` — dead Legistar shell (19-byte `Invalid parameters!`).
  - `polkcityfl.govbuilt.com` — GovBuilt wildcard-DNS placeholder (31,615 bytes; generic title).
  - `polkcity.portal.iworq.net` — empty iWorQ tenant shell (3,209 bytes).
  - `polkcity.granicus.com` — no tenant (404).
  - `ci-polk-city-fl.smartgovcommunity.com` — no tenant (404).
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts, Polk County Legistar — all in `polk-county-fl.md`. Parcel/court data for Polk City properties rides Polk's services. Polk County POLKCO Accela is the likely source for county-issued permits in Polk City.

**Totals:** ~20 HTTPS requests, 0 × 429, 0 × captcha; 3 APIs documented; 6 scrape targets; 0 external platforms cross-referenced; 5 dead/placeholder tenants documented. **No new platforms** (ACSF row covers this).

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.mypolkcity.org` | **CivicPlus Municipal Drupal (ACSF)** | LIVE | Acquia CDN + ACSF multi-site slot `vyhlif10541`; Drupal 9 template base (note the template-hostname leak in sitemap — `d9template1.test-civiccms.acsitefactory.com`); `/rss.xml` works (14,070 bytes); `/meetings` works (37,507 bytes); `/calendar` 200 (42,463 bytes); `/building` 200 (39,016 bytes); `/directory` 200 (90,916 bytes); `/document-library` 200 (115,452 bytes); `/city-commission` 200 (45,449 bytes); `/planning` 404; `/wp-json/` 403 (WAF rule on WP path prefix). Covered by `_platforms.md` **CivicPlus Municipal Drupal (ACSF)** row. |
| `d9template1.test-civiccms.acsitefactory.com` | **ACSF internal template** (leaked via sitemap) | LEAKED REFERENCE | Sole `<loc>` value in `/sitemap.xml`. Internal CivicPlus/Acquia staging hostname for the Drupal 9 template. Not a live data source; documented for drift-detection value (once the tenant reconfigures simple_sitemap to point at production, this leak will disappear). |
| `polkcity.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!`. |
| `polkcityfl.govbuilt.com` | — | PLACEHOLDER | 31,615 byte generic. |
| `polkcity.portal.iworq.net` | — | EMPTY TENANT SHELL | 3,209 bytes Laravel 404. |
| `polkcity.granicus.com` | — | NO TENANT | 404. |
| `ci-polk-city-fl.smartgovcommunity.com` | — | NO TENANT | 404. |
| `polkcityfl.gov`, `cityofpolkcity.com`, `polkcity.org`, `polkcityfl.com`, `polkcity.gov`, `cityofpolkcityfl.com` | — | DNS FAILS or parked | None of these alternate candidate domains are the city site. `polkcity.net` returns a 114-byte parked page. Canonical is `mypolkcity.org`. |

No new platforms added to `docs/api-maps/_platforms.md` this run.

---

## APIs

### /robots.txt

#### Robots directives

- **URL:** `https://www.mypolkcity.org/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Standard Drupal 9+ robots.txt (2,027 bytes) — same template as Eagle Lake and Mulberry.
- **Response schema:** `text/plain`
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** static
- **Discovered via:** recon step 1
- **curl:** `curl -A "$UA" 'https://www.mypolkcity.org/robots.txt'`
- **Evidence file:** `evidence/polk-city-fl-robots.txt`
- **Notes:** Compliant — no disallowed path requested.

### /sitemap.xml

#### Sitemap — ⚠️ broken (template-hostname leak)

- **URL:** `https://www.mypolkcity.org/sitemap.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **336-byte degenerate sitemap** with a single `<loc>http://d9template1.test-civiccms.acsitefactory.com/</loc>`. No production URLs.
- **Response schema:**
  ```
  <urlset>
    <url>
      <loc>http://d9template1.test-civiccms.acsitefactory.com/</loc>
      <changefreq>daily</changefreq>
      <priority>1.0</priority>
    </url>
  </urlset>
  ```
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** n/a
- **Rate limits observed:** none
- **Data freshness:** stale / broken
- **Discovered via:** well-known path
- **curl:** `curl -A "$UA" 'https://www.mypolkcity.org/sitemap.xml'`
- **Evidence file:** `evidence/polk-city-fl-sitemap.xml`
- **Notes:** **⚠️ GAP — load-bearing Polk City finding.** The tenant's simple_sitemap module was left pointing at the internal ACSF D9 template hostname rather than production. The sitemap is unusable for path discovery. Relying on RSS + home-page link-walking for index is the only option until this is fixed.

### /rss.xml

#### Site-wide RSS feed

- **URL:** `https://www.mypolkcity.org/rss.xml`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** Drupal default RSS — trailing window of latest nodes (14,070 bytes). Title `"Polk City FL"`.
- **Response schema:** same shape as Eagle Lake / Mulberry `/rss.xml`
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** real-time on publish
- **Discovered via:** Drupal convention
- **curl:** `curl -A "$UA" 'https://www.mypolkcity.org/rss.xml'`
- **Evidence file:** `evidence/polk-city-fl-rss.xml`
- **Notes:** Primary index for Polk City given the broken sitemap — this is the only real-time feed to subscribe to. Sample item: "City Commission Meeting" linking to `/administration/meeting/city-commission-meeting-0`.

---

## Scrape Targets

### /

#### Home page

- **URL:** `https://www.mypolkcity.org/`
- **Data available:** banner, quick-links, news teaser, upcoming-events, outbound services. 60,512 bytes.
- **Fields extractable:** announcement text, meeting-link URLs, department-link URLs.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** Drupal field markup
- **Why no API:** JSON:API not exposed; sitemap broken.
- **Notes:** Load-bearing discovery surface given the broken sitemap.

### /administration/meeting/{meeting-slug}

#### Meeting detail (Meeting content type)

- **URL:** `https://www.mypolkcity.org/administration/meeting/{meeting-slug}` — e.g. `/administration/meeting/city-commission-meeting-0`.
- **Data available:** meeting title, date, agenda and minutes attachments.
- **Fields extractable:** meeting metadata, PDF URLs under `/sites/g/files/vyhlif10541/files/`.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** RSS or home-page walk
- **Selectors:** `.field--name-field-agendas a`, `.field--name-field-minutes-files a`, `.field--name-field-smart-date time[datetime]`
- **Why no API:** JSON:API not exposed
- **Notes:** Observed route under `/administration/` department — City Commission meetings live under the administration board slug, not under a dedicated `/city-commission/meeting/*` path.

### /city-commission/page/city-commission-meeting-{N}

#### Meeting detail (Page content type — alternate)

- **URL:** `https://www.mypolkcity.org/city-commission/page/city-commission-meeting-{N}` where N is a sequence number (observed 1 through 5 on the home page).
- **Data available:** same as above (agenda, minutes, metadata).
- **Fields extractable:** same
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** home-page walk only
- **Selectors:** same Drupal field markup
- **Why no API:** JSON:API not exposed
- **Notes:** ⚠️ GAP — the dual URL pattern (`/administration/meeting/*` vs `/city-commission/page/*`) suggests tenant-level content-typing inconsistency. Drift detection must walk both. A browser pass should determine which is canonical and which is legacy.

### /building

#### Building Department landing

- **URL:** `https://www.mypolkcity.org/building`
- **Data available:** 39,016 bytes of Building Department info.
- **Fields extractable:** permit-fee text, staff contact info, PDF form URLs.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** Drupal field markup
- **Why no API:** no online permit search observed
- **Notes:** ⚠️ GAP — outbound portal URL not characterized this pass.

### /calendar

#### City calendar

- **URL:** `https://www.mypolkcity.org/calendar`
- **Data available:** event calendar (42,463 bytes).
- **Fields extractable:** event title, date, time.
- **JavaScript required:** likely (Drupal calendar views often lazy-load)
- **Anti-bot measures:** none
- **Pagination:** JS-driven
- **Selectors:** Drupal calendar view markup
- **Why no API:** Drupal view JSON endpoint not exposed
- **Notes:** ⚠️ GAP — XHR contract not characterized in curl mode.

### /document-library

#### Document library

- **URL:** `https://www.mypolkcity.org/document-library`
- **Data available:** document/form index (115,452 bytes — substantial).
- **Fields extractable:** document titles, PDF URLs, categories.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** unknown (single large page observed)
- **Selectors:** Drupal view output
- **Why no API:** no view JSON endpoint
- **Notes:** Large response size suggests this is the primary discovery surface for forms and plans. Grep for PDF references under `/sites/g/files/vyhlif10541/files/`.

### /directory

#### Staff directory

- **URL:** `https://www.mypolkcity.org/directory`
- **Data available:** staff roster (90,916 bytes).
- **Fields extractable:** name, title, phone, email, department.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** unknown
- **Selectors:** Drupal directory view markup
- **Why no API:** no view JSON endpoint
- **Notes:** PII-dense.

---

## Coverage Notes

- `robots.txt` read and respected.
- **⚠️ GAP (sitemap broken):** `/sitemap.xml` points at ACSF internal template hostname. Drift-detection target: the day this changes to `mypolkcity.org` `<loc>` values is the day discovery-via-sitemap becomes usable.
- **⚠️ GAP (building/permit portal):** `/building` returns 200 but outbound portal URL not characterized.
- **⚠️ GAP (Municode):** code-of-ordinances outbound not located.
- **⚠️ GAP (calendar XHR):** `/calendar` likely JS-driven; needs browser pass.
- **⚠️ GAP (dual meeting routes):** `/administration/meeting/*` vs `/city-commission/page/*` pattern unresolved.
- **⚠️ GAP (video):** no video archive outbound observed.
- **⚠️ GAP (`/planning` 404):** the city mentions planning commission meetings but there is no `/planning` or `/planning-commission` path on this tenant. The planning function may be folded into the general `/city-commission` agenda stream.
- **Total HTTPS requests this run:** ~20 (well under 2000 cap).
