# Frostproof, FL — API Map

> Last surveyed: 2026-04-18. Seed: `https://www.cityoffrostproof.com/` (city of Frostproof, FL — Polk County). One-file scope: city of Frostproof only — Polk County is mapped separately in `polk-county-fl.md`.
>
> **Site is currently returning HTTP 509 "Bandwidth Limit Exceeded"** on every path (root, wp-json, robots, sitemap) — the hosting provider has shut the tenant down for overage. This is not transient: repeat requests over the mapping-pass window all returned 509 identically. Archive-based recon (archive.org wayback, snapshot 2024-12-31) was used to fingerprint the CMS as **WordPress** — confirmed via `wp-content/plugins/contact-form-7`, `cf7-conditional-fields`, and standard WP asset paths in the wayback HTML.
>
> Crawl in **degraded mode** (curl-only). ~14 HTTPS requests to live site (all 509) + ~2 wayback lookups. No 429, no captcha — **but the 509 is itself the critical operational finding** and is flagged as the load-bearing Frostproof coverage note.

## Summary

- **Jurisdiction:** City of Frostproof, Polk County, FL. Population ≈3k.
- **City CMS platform:** **WordPress** (confirmed from archive.org wayback snapshot 2024-12-31 at `web.archive.org/web/2024/https://www.cityoffrostproof.com/` — 78,693 bytes rendered, title `"City of Frostproof | The Friendly City"`, `wp-content/plugins/contact-form-7/`, `wp-content/plugins/cf7-conditional-fields/`). **Currently unreachable live — the host is serving a static 509 Apache-default error page (7,309 bytes, `<TITLE>509 Bandwidth Limit Exceeded</TITLE>`) for `/`, `/wp-json/`, `/robots.txt`, `/sitemap.xml`, and every other path.** The 509 comes from the hosting provider (likely a shared WordPress host that rate-limited the tenant for overage or billing issues). No Cloudflare in front — direct origin 509.
- **Operational risk signal:** The 509 has been persistent across the mapping-pass window. ⚠️ GAP: **Frostproof has no public data surface online until the host restores service.** This is the load-bearing coverage note for Frostproof — all endpoint probes this run failed with 509; re-probe on the next scheduled mapping pass to see if service is restored.
- **No candidate alternate hostnames resolve:** `frostproof.net`, `frostprooffl.org`, `ci.frostproof.fl.us`, `frostproof.org`, `frostproof.fl.gov` all fail DNS. `cityoffrostproof.com` is the only live hostname, and it is serving 509.
- **Permit / utility portal posture:** ⚠️ GAP — cannot be characterized while host is down. Wayback 2024-12-31 HTML shows outbound links to `/departments/building/` and `/government/meeting-agendas-minutes/` as CMS-internal paths; no outbound portal URL visible in the wayback snapshot. A future pass should re-examine for BS&A / Accela / iWorQ / GovBuilt outbound links once the host is restored.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `frostproof.legistar.com` — dead Legistar shell (19-byte `Invalid parameters!`).
  - `frostprooffl.govbuilt.com` — GovBuilt wildcard-DNS placeholder (31,619 bytes; generic title).
  - `frostproof.portal.iworq.net` — empty iWorQ tenant shell (3,211 bytes).
  - `frostproof.granicus.com` — no tenant (404).
  - `ci-frostproof-fl.smartgovcommunity.com` — no tenant (404).
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts, Polk County Legistar — all in `polk-county-fl.md`. Parcel and court data for Frostproof properties ride Polk's services regardless of city CMS status.

**Totals:** ~16 HTTPS requests (14 × 509 on live site + 2 × 200 on wayback); 0 APIs documented (nothing reachable live); 0 scrape targets (nothing reachable live); 5 dead/placeholder vendor tenants documented; 1 archive.org-based CMS fingerprint captured. **No new platforms added to `_platforms.md`** — the CMS is standard WordPress already covered.

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `cityoffrostproof.com` / `www.cityoffrostproof.com` | **WordPress** (inferred from wayback) | **DOWN — HTTP 509 BANDWIDTH LIMIT EXCEEDED** | Live site returns 509 on every path tested (`/`, `/wp-json/`, `/robots.txt`, `/sitemap.xml`). Wayback snapshot 2024-12-31 confirms WordPress (contact-form-7 plugin, cf7-conditional-fields plugin, wp-content asset paths). Existing `_platforms.md` row for WordPress REST covers this once the tenant comes back online. |
| `frostproof.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!` (Bartow pattern). |
| `frostprooffl.govbuilt.com` | — | PLACEHOLDER | 31,619 byte generic GovBuilt placeholder. |
| `frostproof.portal.iworq.net` | — | EMPTY TENANT SHELL | 3,211 bytes Laravel 404. |
| `frostproof.granicus.com` | — | NO TENANT | 404. |
| `ci-frostproof-fl.smartgovcommunity.com` | — | NO TENANT | 404. |
| `frostproof.net`, `frostprooffl.org`, `ci.frostproof.fl.us`, `frostproof.org`, `frostproof.fl.gov` | — | DNS FAILS | No A records; these candidate alternate domains do not exist. |

No new platforms added to `docs/api-maps/_platforms.md` this run.

---

## APIs

(None reachable — host is serving HTTP 509 Bandwidth Limit Exceeded on every path.)

### /robots.txt — 509 (not characterizable)

- **URL:** `https://cityoffrostproof.com/robots.txt`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **HTTP 509 Bandwidth Limit Exceeded** — 7,309-byte Apache-default static error page. No robots.txt content.
- **Response schema:** n/a (error page)
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** `none`
- **Rate limits observed:** n/a — pre-empted by the 509 overage
- **Data freshness:** n/a
- **Discovered via:** recon step 1
- **curl:** `curl -A "$UA" 'https://cityoffrostproof.com/robots.txt'`
- **Evidence file:** `evidence/frostproof-fl-robots.txt` (contains the 509 page, not actual robots content)
- **Notes:** ⚠️ GAP — re-probe next mapping pass.

### /wp-json/ — 509 (not characterizable)

- **URL:** `https://cityoffrostproof.com/wp-json/`
- **Method:** `GET`
- **Auth:** `none`
- **Data returned:** **HTTP 509** — 7,309-byte error page. Expected to return WordPress site descriptor JSON when service is restored.
- **Response schema:** expected WordPress REST descriptor (see `dundee-fl.md` / `haines-city-fl.md` for the shape once reachable)
- **Observed parameters:** none
- **Probed parameters:** none
- **Pagination:** n/a
- **Rate limits observed:** n/a
- **Data freshness:** n/a
- **Discovered via:** WordPress convention (fingerprinted via wayback)
- **curl:** `curl -A "$UA" 'https://cityoffrostproof.com/wp-json/'`
- **Evidence file:** `evidence/frostproof-fl-wp-json.json` (contains 509 page)
- **Notes:** ⚠️ GAP — once host service is restored, standard WordPress REST probe set applies: `/wp-json/wp/v2/{pages,posts,media,categories,tags,users,search,types,taxonomies}` with `per_page=100` capped at 100 by default.

---

## Scrape Targets

(None reachable — host is serving HTTP 509 on every path. Wayback artifacts are not documented as scrape targets because archive.org is not the canonical data source; it is only used here for fingerprinting.)

⚠️ GAP: once `cityoffrostproof.com` is restored, the following should be documented as scrape targets on a re-probe:
- `/` (home page)
- `/departments/building/` (observed in wayback as an internal path)
- `/government/meeting-agendas-minutes/` (observed in wayback as an internal path — load-bearing CR surface)

---

## Coverage Notes

- **⚠️ GAP (service outage):** `cityoffrostproof.com` is serving **HTTP 509 Bandwidth Limit Exceeded** on every probed path. Persistent across the mapping-pass window. The single operational recommendation this run is: **flag Frostproof for re-probe on the next mapping pass.** If the 509 persists, the downstream Health page should shade Frostproof "down" rather than "stale map".
- **⚠️ GAP (wp-json enumeration):** full WordPress REST probe deferred until service restored.
- **⚠️ GAP (permit / agenda / portal posture):** cannot be characterized.
- **Wayback used for CMS-only fingerprinting**, not content ingestion. Archive.org snapshot 2024-12-31 at `web.archive.org/web/2024/https://www.cityoffrostproof.com/` confirms WordPress.
- **Total HTTPS requests this run:** ~16 (well under 2000 cap). Live site: 14 × 509. Wayback: 2 × 200.
