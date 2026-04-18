# Fort Meade, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.cityoffortmeade.org/` (city of Fort Meade, FL — Polk County). One-file scope: city of Fort Meade only — Polk County is mapped separately in `polk-county-fl.md`.
>
> Crawl in **degraded mode** (curl-only) — verified safe: the CMS is **Revize** (server-rendered PHP/ASP shell; `.php` extensionless paths in hrefs; `revize.css` + `/revize/util/snippet_helper.js` signatures; `cms2.revize.com` admin backend at `webspace=fortmeadefl`). No React/Vue/Next/Nuxt markers.
>
> UA: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36`. Pacing ~1 req/sec. ~22 unique HTTPS requests this run; 0 × 429, 0 × captcha, 0 × WAF block.

## Summary

- **Jurisdiction:** City of Fort Meade, Polk County, FL. Population ≈6k.
- **City CMS platform:** **Revize** on `www.cityoffortmeade.org`. Classic Revize structure with `.php` suffix pages under `/departments/`, `/index.php`, `/calendar.php`, `/alert_detail.php`. `fortmeadefl.gov` apex redirects to `www.cityoffortmeade.org`. Admin backend at `cms2.revize.com/revize/security/index.jsp?webspace=fortmeadefl`. All other candidate domains (`fortmeade.org`, `cityoffortmeade.com`) return a 114-byte redirect-or-parked response. `X-Frame-Options: SAMEORIGIN`, `Content-Security-Policy: frame-ancestors 'self'`, `X-XSS-Protection: 1; mode=block`. Server header elided. **New platform row for `_platforms.md`: Revize CMS.**
- **Permit / utility portal posture:** **BS&A Online** as the primary citizen self-service portal at `https://bsaonline.com/?uid=2524` (Fort Meade City tenant uid=2524). Landing page title `"BS&A Online"` with `"Fort Meade City"` entity displayed. Modules visible on the landing include Utility Billing Record Search (`/SiteSearch/UtilityBillingRecordSearch?uid=2524`) and Pay a Utility Bill (`/BsaPayment/TakeUtilityBillingPayment?uid=2524`). The landing page shows "Services", "Pay a Bill", "Detailed Record Search", "Create an Account", "Access Additional Services", "Go to Municipal Directory" navigation. No Accela / GovBuilt / iWorQ / CivicPlus / Tyler EnerGov tenant. **New platform row for `_platforms.md`: BS&A Online.**
- **Commission surface:** **Revize-native** — agendas and minutes live under `/departments/city_commssion.php` (note the Revize-authored typo `commssion` in the URL slug — stable; do not "fix"). The Revize site does not expose an agenda-index API; drift detection should diff `/departments/city_commssion.php` HTML. No Legistar, no Granicus, no AgendaCenter, no NovusAgenda (see graveyard).
- **Code of ordinances:** **Municode Library** at `https://library.municode.com/FL/Fort_Meade` (case-sensitive slug `Fort_Meade` — note title-case, unlike Eagle Lake's `eagle_lake` lowercase). Covered by existing `_platforms.md` row; not deep-mapped.
- **Public-notices / legal ads:** **Column** via Polk County at `https://polkcounty.column.us/search` — linked through a SOPHOS link-protection wrapper (`us-west-2.protection.sophos.com/?d=column.us&...`) on the home page. This means Fort Meade's city email system is Sophos-protected; the Column link itself is just the standard Polk County public-notices URL.
- **Other linked services:** `fortmeadeflmuseum.com` (museum, external), `ftmeadechamber.com` (chamber of commerce, external), `streamsongresort.com` (tourism outbound). None are city-operated data surfaces.
- **No sitemap, no robots at root:** `/sitemap.xml` returns **404** and `/robots.txt` returns **302** (likely a redirect to a vendor wildcard or to the Revize shell). `/wp-json/` 404 (no WordPress). `/rss` 404, `/feed` 404, `/search` 404. **Revize does not emit a machine-readable site index on this tenant.** The only structured artifact is the outbound Municode Library and BS&A Online portals.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `fortmeade.legistar.com` — **dead Legistar shell** (19-byte `Invalid parameters!`).
  - `fortmeadefl.govbuilt.com` — GovBuilt wildcard-DNS placeholder (31,617 bytes; generic title).
  - `fortmeade.portal.iworq.net` — empty iWorQ tenant shell (3,210 bytes).
  - `fortmeade.granicus.com` — no tenant (404).
  - `ci-fort-meade-fl.smartgovcommunity.com` — no tenant (404).
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts, Polk County Legistar — all in `polk-county-fl.md`. Column public-notices for Fort Meade are part of Polk County's Column tenant.

**Totals:** ~22 HTTPS requests, 0 × 429, 0 × captcha; 3 APIs documented; 6 scrape targets; 2 external platforms cross-referenced (Municode Library, Column); 5 dead/placeholder tenants documented. **2 new platform rows for `_platforms.md`: Revize CMS, BS&A Online.**

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `www.cityoffortmeade.org` / `fortmeadefl.gov` | **Revize CMS** | LIVE | `.php` extensionless paths under `/departments/*`; asset prefix `_assets_/`; `revize.css` + `/revize/util/snippet_helper.js`; admin backend at `cms2.revize.com/revize/security/index.jsp?webspace=fortmeadefl`; bxSlider + matchHeight + Modernizr custom + add-to-homescreen plugins bundled. Security headers: `X-Frame-Options: SAMEORIGIN`, `Content-Security-Policy: frame-ancestors 'self'`, `X-XSS-Protection: 1; mode=block`, `X-Content-Type-Options: nosniff`. No sitemap, no robots (404 / 302). **New platform row for `_platforms.md`.** |
| `bsaonline.com/?uid=2524` | **BS&A Online** | LIVE | Citizen self-service portal (tax, utility billing, assessment, payments) for Fort Meade City (tenant uid=2524). Cloudflare-fronted; App Gateway affinity cookies (`ApplicationGatewayAffinity`, `ApplicationGatewayAffinityCORS`), `ASP.NET_SessionId` session cookie, `IsWeb` cookie (encrypted gateway-level tag). Title `"BS&A Online"`. Navigation: "Services", "Pay a Bill", "Detailed Record Search", "Create an Account", "Utility Billing Record Search", "Pay a Utility Bill", "Go to Municipal Directory". **New platform row for `_platforms.md`.** |
| `library.municode.com/FL/Fort_Meade` | **Municode Library** | LIVE (external) | Existing `_platforms.md` row. Client slug is **title-case** (`Fort_Meade`), unlike Eagle Lake's lowercase `eagle_lake`. |
| `polkcounty.column.us/search` | **Column (Public Notices)** | LIVE (external) | Existing `_platforms.md` row — Column tenant for Polk County covers Fort Meade. Linked through a Sophos email-protection wrapper from the CMS home page (which reveals that Fort Meade's email is `*.onmicrosoft.com`-backed, Sophos-protected). |
| `fortmeade.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!` (Bartow pattern). |
| `fortmeadefl.govbuilt.com` | — | PLACEHOLDER | 31,617 byte generic GovBuilt placeholder. |
| `fortmeade.portal.iworq.net` | — | EMPTY TENANT SHELL | 3,210 bytes Laravel 404. |
| `fortmeade.granicus.com` | — | NO TENANT | `/ViewPublisher.php?view_id=1` 404. |
| `ci-fort-meade-fl.smartgovcommunity.com` | — | NO TENANT | 404 on `/`. |

New platforms added to `docs/api-maps/_platforms.md` this run: **Revize CMS**, **BS&A Online**.

---

## APIs

### /robots.txt — 302-redirect (no usable content)

Not an API — `/robots.txt` returns a 302 (176-byte body). Not characterized further. Documented for completeness of the recon step.

- **URL:** `https://www.cityoffortmeade.org/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** 302 redirect; no directives
- **Response schema:** n/a
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** none
- **Data freshness:** n/a
- **Discovered via:** recon step 1
- **curl:** `curl -A "$UA" 'https://www.cityoffortmeade.org/robots.txt'`
- **Evidence file:** `evidence/fort-meade-fl-robots.txt`
- **Notes:** ⚠️ GAP — Revize tenant has no public robots.txt or sitemap.

### BS&A Online (cross-reference)

#### Fort Meade BS&A landing

- **URL:** `https://bsaonline.com/Home/MunicipalityHome?uid=2524`
- **Method:** `GET`
- **Auth:** `none` (session cookie bootstrapped by the gateway; persists via `ApplicationGatewayAffinity` + `ASP.NET_SessionId`)
- **Data returned:** HTML landing for the Fort Meade City tenant — shows modules Utility Billing Record Search, Pay a Utility Bill, Municipal Directory. 47,904 bytes.
- **Response schema:** HTML
- **Observed parameters:**
  - `uid` (int, required) — tenant id. Fort Meade = 2524.
- **Probed parameters:**
  - `uid=2524` confirmed
- **Pagination:** n/a
- **Rate limits observed:** none at 1 req/sec
- **Data freshness:** real-time
- **Discovered via:** outbound link on Fort Meade CMS home page
- **curl:** `curl -A "$UA" -c cookies.txt -b cookies.txt -L 'https://bsaonline.com/?uid=2524'`
- **Evidence file:** `evidence/fort-meade-fl-bsa-landing.html`
- **Notes:** A cookie jar is required — the initial `/?uid=2524` request 302-chains through `/Home/LandingPage` and only settles at `/Home/MunicipalityHome` with a session. BS&A does not expose a public JSON search endpoint on this tenant; the landing HTML is the entry point. Utility Billing Record Search URL `/SiteSearch/UtilityBillingRecordSearch?uid=2524` is HTML (returns 36,128 bytes), not JSON. Deep BS&A integration deferred to browser pass.

#### Utility Billing Record Search (HTML form)

- **URL:** `https://bsaonline.com/SiteSearch/UtilityBillingRecordSearch?uid=2524`
- **Method:** `GET` (form rendered) / `POST` (search submission, not probed)
- **Auth:** `none` (session-bootstrapped)
- **Data returned:** HTML search form for utility billing records. 36,128 bytes.
- **Response schema:** HTML form + empty results table
- **Observed parameters:**
  - `uid` (int, required)
- **Probed parameters:** `uid=2524` confirmed
- **Pagination:** form-controlled
- **Rate limits observed:** none
- **Data freshness:** real-time (BS&A tenant)
- **Discovered via:** BS&A landing
- **curl:** `curl -A "$UA" -b cookies.txt 'https://bsaonline.com/SiteSearch/UtilityBillingRecordSearch?uid=2524'`
- **Evidence file:** `evidence/fort-meade-fl-bsa-ub.html`
- **Notes:** Primary utility-bill data surface for Fort Meade. Not strictly an API — search submission POSTs back to the same URL and returns HTML. Formalize this as a Scrape Target in production ingestion.

---

## Scrape Targets

### /

#### Home page (Revize landing)

- **URL:** `https://www.cityoffortmeade.org/`
- **Data available:** banner image, quick-links, alert teaser, department navigation, outbound-portal links.
- **Fields extractable:** announcement text, outbound-portal URLs (BS&A, Municode, Column via Sophos, museum, chamber).
- **JavaScript required:** no
- **Anti-bot measures:** none (no Cloudflare challenge; standard security headers)
- **Pagination:** n/a
- **Selectors:** stable on `_assets_/images/logo.png` and `.bxslider` containers; Revize does not emit semantic classnames.
- **Why no API:** Revize tenant has no public API surface; sitemap + robots + rss + feed all 404.
- **Notes:** Primary drift-detection target.

### /departments/city_commssion.php

#### City Commission department page (note URL typo)

- **URL:** `https://www.cityoffortmeade.org/departments/city_commssion.php` (sic — `commssion` not `commission`)
- **Data available:** commissioner roster, meeting schedule, agendas and minutes links.
- **Fields extractable:** commissioner names, meeting dates, agenda/minutes PDF URLs.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** unstable — Revize emits untagged text; inspection per-scrape required
- **Why no API:** Revize tenant exposes no agenda-index API
- **Notes:** **Load-bearing CR surface for Fort Meade.** The URL-slug typo `commssion` is baked into Revize since site inception; drift-detection must include this as a known-typo entry.

### /departments/building.php

#### Building Department page

- **URL:** `https://www.cityoffortmeade.org/departments/building.php`
- **Data available:** permit information, fee schedules, contact info.
- **Fields extractable:** permit-fee text, staff contact info.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** unstable
- **Why no API:** no permit search on the Fort Meade city site; permit issuance is paper/in-person and utility-billing rides BS&A.
- **Notes:** ⚠️ GAP — no online permit search for Fort Meade. PT-style ingestion must rely on Polk County Accela (POLKCO) if Polk-issued, or FOIA requests for city-issued.

### /calendar.php

#### City calendar

- **URL:** `https://www.cityoffortmeade.org/calendar.php`
- **Data available:** event calendar — city meetings, community events.
- **Fields extractable:** event title, date, time, location.
- **JavaScript required:** likely (Revize calendars usually use jQuery + AJAX). 30,221 bytes initial HTML.
- **Anti-bot measures:** none
- **Pagination:** JS-driven month navigation
- **Selectors:** unstable (Revize's calendar widget varies across tenants)
- **Why no API:** no JSON calendar endpoint observed at the Revize-asset layer; further investigation requires a browser pass to watch XHRs.
- **Notes:** ⚠️ GAP — a browser pass should characterize the XHR backing the calendar navigation. Revize tenants sometimes expose `/calendar.php?month=N&year=Y` GET-only, sometimes JSON POSTs.

### /alert_detail.php

#### Alert detail pages

- **URL:** `https://www.cityoffortmeade.org/alert_detail.php`
- **Data available:** emergency-alert details (boil water notices, road closures, etc.).
- **Fields extractable:** alert text, date, category.
- **JavaScript required:** no
- **Anti-bot measures:** none
- **Pagination:** n/a
- **Selectors:** unstable
- **Why no API:** Revize does not expose alerts as feed.
- **Notes:** 32,220 bytes. No alert-index URL observed — the listing presumably lives on the home page banner.

### bsaonline.com/?uid=2524

Documented above under APIs.

### library.municode.com/FL/Fort_Meade (cross-reference)

Characterized in `_platforms.md`.

### polkcounty.column.us/search (cross-reference)

Characterized in `_platforms.md`.

---

## Coverage Notes

- `robots.txt` returns 302; `sitemap.xml` returns 404. **No machine-readable site index is published by the Revize tenant.** Drift detection against a Revize site must diff the HTML of key pages; there is no content feed to subscribe to.
- **⚠️ GAP (permits):** Fort Meade city has no online permit search. PT ingestion must rely on Polk County's POLKCO Accela tenant for Polk-issued permits and on Florida state contractor licensing (`myfloridalicense.com`) for state-issued.
- **⚠️ GAP (calendar XHR):** `/calendar.php` is JS-driven; XHR contract not characterized in curl-only mode.
- **⚠️ GAP (BS&A search API):** BS&A Online's search submission is form-POST HTML, not JSON. A browser pass would enumerate whether the tenant exposes any JSON endpoints (sometimes `/ApiServices/` routes exist).
- **Total HTTPS requests this run:** ~22 (well under 2000 cap).
