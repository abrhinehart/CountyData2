# Hillcrest Heights, FL — API Map

> Last surveyed: 2026-04-18. Seed: (none — the town has no official website). One-file scope: Town of Hillcrest Heights, Polk County, FL.
>
> **This map is a stub-class record documenting the absence of a town web presence.** Hillcrest Heights is a tiny town (~230 population — one of the smallest incorporated municipalities in Florida) that appears to have no official website. Every candidate domain tested either fails DNS or returns a wrong-owner / domain-squatting site. The one domain that does resolve, `townofhillcrestheights.com`, is a Spanish-language Adsense content farm named "TOHCH News" that has **no relation to the town government** despite the name.
>
> Crawl in **degraded mode** (curl-only). ~14 HTTPS requests; 0 × 429, 0 × captcha.

## Summary

- **Jurisdiction:** Town of Hillcrest Heights, Polk County, FL. Population ≈230 (per most recent census).
- **City CMS platform: NONE (no official town website identified).**
- **Candidate domain discovery:**
  - `hillcrestheightsfl.gov` — DNS fails.
  - `hillcrestheightsfl.org` — DNS fails.
  - `townofhillcrestheightsfl.gov` — DNS fails.
  - `hillcrestheights.com` — 114-byte parked page.
  - `townofhillcrestheights.com` — **Spanish-language WordPress blog, NOT the town.** Hosted on Hostinger; running WordPress 6.9.4 with GeneratePress theme, Jetpack, RankMath SEO, Ad Inserter, WP Rocket. Title is `"TOHCH News"` (not "Town of Hillcrest Heights"). About-page text: *"At TOHCH News, we pride ourselves on delivering breaking news in an easily digestible format… Fundado en 2012, The TOHCH NEWS sirve como su centro integral para ayuda gubernamental, iniciativas del gobierno, impuestos, asuntos de seguridad social, temas financieros y las últimas notificaciones de empleo."* Post categories include `/category/blog/`, `/category/venezuela/`, `/category/noticia/` — content is Spanish-language personal-finance / Social Security / Venezuela news, clearly a content-farm operation unrelated to a Polk County town government. 53 posts in post-sitemap; 10 pages in page-sitemap (About, Contact, Disclaimer, Editorial Policy, Fact-Checking Policy, Privacy Policy, Terms & Conditions, "The CSC 2/3"). **Documented here as a name-collision warning, not as the town's site.**
- **Permit / agenda / utility / code posture:** **NONE observed.** Given the town's tiny population, it is entirely plausible that Hillcrest Heights has no digital public-records footprint at all. Town council meetings, permits, and any public records are presumably handled via paper correspondence routed through the town hall directly, or are covered entirely by Polk County at the county level.
- **Meeting-vendor graveyard (Bartow pattern):**
  - `hillcrestheights.legistar.com` — dead Legistar shell (19-byte `Invalid parameters!`).
  - `hillcrestheightsfl.govbuilt.com` — GovBuilt wildcard-DNS placeholder (31,631 bytes; generic title).
  - `hillcrestheights.portal.iworq.net` — empty iWorQ tenant shell (3,217 bytes).
  - `hillcrestheights.granicus.com` — no tenant (404).
  - `ci-hillcrest-heights-fl.smartgovcommunity.com` — no tenant (404).
- **Polk County parent infrastructure:** Polk County Property Appraiser, Polk County Clerk of Courts, Polk County Legistar — all in `polk-county-fl.md`. **All public-records access for Hillcrest Heights properties and residents rides Polk County services.** Parcel data (PolkPA), court records (Clerk BrowserView / Tyler Odyssey PRO), county-issued permits (POLKCO Accela) all cover Hillcrest Heights by virtue of county-level operation.

**Totals:** ~14 HTTPS requests, 0 × 429, 0 × captcha; 0 APIs documented; 0 scrape targets; 5 dead/placeholder tenants documented; 1 name-collision (TOHCH News) documented for negative-evidence purposes. **No new platforms added** (the WordPress blog at `townofhillcrestheights.com` is irrelevant; standard WordPress REST is already in `_platforms.md` and this tenant is not the town).

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `townofhillcrestheights.com` | **WordPress 6.9.4 blog (TOHCH News — NOT the town)** | **NAME COLLISION — NOT OFFICIAL** | Hostinger-hosted WordPress with Jetpack, RankMath SEO, GeneratePress theme, Ad Inserter, WP Rocket, Google Site Kit. Title `"TOHCH News"`. About text is a content-mill boilerplate about delivering "breaking news". Categories in Spanish. Published posts are about Social Security, Venezuela bonuses, unemployment checks — **no town-government content.** Documented so future mapping agents don't mistake it for the Hillcrest Heights town site. |
| `hillcrestheights.com` | — | PARKED | 114-byte parked page. |
| `hillcrestheights.legistar.com` | **Legistar (dead shell)** | PROVISIONED BUT UNCONFIGURED | 19-byte `Invalid parameters!`. |
| `hillcrestheightsfl.govbuilt.com` | — | PLACEHOLDER | 31,631 byte generic. |
| `hillcrestheights.portal.iworq.net` | — | EMPTY TENANT SHELL | 3,217 bytes Laravel 404. |
| `hillcrestheights.granicus.com` | — | NO TENANT | 404. |
| `ci-hillcrest-heights-fl.smartgovcommunity.com` | — | NO TENANT | 404. |
| `hillcrestheightsfl.gov`, `hillcrestheightsfl.org`, `townofhillcrestheightsfl.gov` | — | DNS FAILS | No A records. |

No new platforms added to `docs/api-maps/_platforms.md` this run.

---

## APIs

(None — town has no official digital presence.)

---

## Scrape Targets

(None — town has no official digital presence.)

---

## Coverage Notes

- **⚠️ GAP (no official website):** Hillcrest Heights does not publish a town website at any plausible domain. All town activity — council meetings, permits, code enforcement, utility billing — is either handled via paper/in-person through the town hall or is covered by Polk County at the county level.
- **⚠️ NAME COLLISION WARNING (`townofhillcrestheights.com`):** this domain resolves but is a Spanish-language Adsense content farm called "TOHCH News" that is unrelated to the town. Future mapping passes must not mistake it for the town government. Detection: homepage `<title>TOHCH News</title>`, About page says *"Fundado en 2012"* and describes itself as a breaking-news site, categories include `/venezuela/` and `/noticia/`.
- **Polk County covers all downstream data surfaces:** parcel, court records, county-issued permits, code library (Municode would be at county level). See `polk-county-fl.md`.
- **Graveyard discipline:** 5 dead/placeholder vendor tenants documented for negative evidence.
- **Total HTTPS requests this run:** ~14.
