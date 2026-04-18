# Highland Park, FL — API Map

> Last surveyed: 2026-04-18. Seed: (none — town has no website). One-file scope: Town of Highland Park, Polk County, FL.
>
> **Stub-class record** — Planner granted stub permission upfront. Every candidate domain fails DNS. Highland Park is among Florida's smallest incorporated municipalities (population well under 200); a zero-digital-footprint result is expected.
>
> Crawl in **degraded mode** (curl-only). ~8 HTTPS requests; all either DNS-failed or vendor-placeholder.

## Summary

- **Jurisdiction:** Town of Highland Park, Polk County, FL. Population ≈230 (per most recent census — one of the smallest incorporated municipalities in Florida, comparable to Hillcrest Heights).
- **City CMS platform: NONE (no town website identified).**
- **Candidate domain discovery (all failed):**
  - `highlandparkfl.gov` — DNS fails.
  - `townofhighlandparkfl.gov` — DNS fails.
  - `highlandparkfl.org` — DNS fails.
  - `townofhighlandpark.com` — DNS fails.
  - `townofhighlandpark.net` — DNS fails.
  - `highlandparkpolk.com` — DNS fails.
- **Permit / agenda / utility / code posture:** **NONE observed.** All town functions presumably handled via paper/in-person through town hall or via Polk County at the county level, matching the Hillcrest Heights pattern.
- **Meeting-vendor graveyard:** not enumerated this run — with no CMS fingerprint to anchor vendor-slug candidates, graveyard checking would be speculative. If an official site is ever discovered, run the standard Bartow-pattern vendor probes at that point.
- **Polk County parent infrastructure:** see `polk-county-fl.md`. All public-records access for Highland Park rides Polk County.

**Totals:** ~8 HTTPS requests, 0 × 429, 0 × captcha; 0 APIs; 0 scrape targets; 0 platforms.

---

## Platform Fingerprint

| Host | Platform | Status | Fingerprint |
|---|---|---|---|
| `highlandparkfl.gov`, `townofhighlandparkfl.gov`, `highlandparkfl.org`, `townofhighlandpark.com`, `townofhighlandpark.net`, `highlandparkpolk.com` | — | DNS FAILS | No A records on any candidate domain. |

No new platforms added to `docs/api-maps/_platforms.md` this run.

---

## APIs

(None — town has no digital presence.)

---

## Scrape Targets

(None — town has no digital presence.)

---

## Coverage Notes

- **⚠️ GAP (no official website):** Highland Park does not publish a town website at any plausible domain. Matches the Hillcrest Heights pattern — both are tiny Polk County towns (~230 pop) with no digital footprint. Not unusual for municipalities this small; state-mandated town functions are handled at the county level.
- **Polk County covers all downstream data surfaces.** See `polk-county-fl.md`.
- **Re-probe policy:** on each subsequent mapping pass, run the same DNS probe against the 6 candidate domains to catch the day (if ever) the town stands up a site. No graveyard-vendor probing is warranted until a CMS fingerprint exists.
- **Total HTTPS requests this run:** ~8.
