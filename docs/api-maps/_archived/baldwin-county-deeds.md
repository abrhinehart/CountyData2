# Baldwin County AL -- Kofile PublicSearch Probate Deeds API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Baldwin County Probate Court (Alabama; Probate Judge, not Clerk of Court) |
| Portal URL | `https://baldwin.al.publicsearch.us/` |
| Vendor | Kofile Technologies (publicsearch.us platform) |
| UI | React SPA (Source Sans Pro / custom design tokens); server-side rendered skeleton |
| Auth | Anonymous browse; "Property Alert" subscription requires a named account |
| Registry entry | `county-registry.yaml` L585-598 has BI only; **no `cd2:` block** |
| Client reuse | None existing in this repo (new vendor family) |

Baldwin's Probate office operates multiple physical locations (Bay Minette, Fairhope, Foley; Robertsdale closed for renovations per their public page). The PublicSearch portal serves as the unified online index across all divisions.

## 2. Probe (2026-04-14)

```
GET https://baldwincountyal.gov/government/probate-office/recording
-> HTTP 200  (Baldwin County Probate Recording page; links out to baldwin.al.publicsearch.us)

GET https://baldwin.al.publicsearch.us/
-> HTTP 200  (Kofile PublicSearch React SPA; ~95 KB of CSS-in-JS payload; GoogleTagManager embedded)
```

PublicSearch is also used by other jurisdictions (the domain `*.publicsearch.us` is Kofile's multi-tenant host). In FL, Putnam County uses `landmark.putnam-fl.com` (Pioneer) not publicsearch; the PublicSearch family is a different vendor line. No existing adapter in this repo targets this platform -- new client/adapter would be required.

## 3. Search / Query Capabilities

PublicSearch exposes a typed search UI with:

- Text query (grantor / grantee / description).
- Date range.
- Document type filter.
- Result grid (sortable, paginated).

The underlying API (inferred from the SPA shell; not probed for endpoints here) is a JSON-RPC-style service hit from the React bundle -- a future adapter would need DevTools-driven network inspection to enumerate it. `unverified -- needs validation` for specific endpoint paths and request body shape; no adapter has yet walked this portal.

## 4. Field Inventory

Expected (typical PublicSearch return shape, Kofile default):

- Grantor, Grantee, Record Date.
- Document Type (DE, MO, etc.).
- Book / Page / Instrument Number.
- Legal description (truncated).
- Consideration: **non-disclosure state, not published.**

Exact field names and API JSON keys are unverified at probe time -- the React client obfuscates them behind the bundled JS.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No CD2 config, no adapter, no client. A future adapter would extract grantor / grantee / record date / doc type / book / page / instrument / legal. **Non-disclosure: no sale price. Mortgage cross-reference same-day last-name pattern** (per `AL-ONBOARDING.md`) would be the price proxy; achievable match rate is ~40% empirically in Madison AL and presumed similar for Baldwin subject to validation on first pull.

## 6. Auth Posture / Bypass Method

Anonymous browse + search. Named account only required for property-alert email subscriptions (not needed for scraping).

Rate-limit behavior is not observed (single probe only). Kofile's React client does lazy-load result pagination; adapters should respect the `debounce`/polling windows the UI uses to avoid looking like abuse traffic. `unverified -- needs validation` for specific rate thresholds.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Grantor / Grantee | NO |
| Record date | NO |
| Doc type | NO |
| Book / page / instrument | NO |
| Legal | NO |
| Mortgage amount (cross-ref) | NO |
| Consideration | NOT PRESENT (non-disclosure) |
| Document image | NO (pay-per-view typical for Kofile; unverified here) |

## 8. Known Limitations and Quirks

- **Non-disclosure state**: no sale price on deeds. Mortgage cross-ref (~40% match rate in Madison, extrapolated) is the only price proxy.
- Kofile PublicSearch is a **new vendor family** for this repo -- no existing CD2 adapter can be reused. Client implementation would be greenfield.
- React SPA -- endpoint enumeration requires DevTools or headless-browser tracing; raw HTML GETs will not reveal the JSON API.
- Multi-division county (Bay Minette / Fairhope / Foley physical offices; Robertsdale temporarily closed). Online index aggregates; division-specific fee waivers and record timing may vary.
- `L L C` spacing entity-name convention applies (AL assessor data).
- **Coast cities (Gulf Shores, Orange Beach, Fairhope, Foley) file deeds through the county Probate Court**, not through city offices -- the county Probate handles all real-property recording for all Baldwin jurisdictions. Deeds are NOT split the way permits are.

Source of truth: `county-registry.yaml` (baldwin-al L585-598, BI-only), `AL-ONBOARDING.md`, Baldwin County Recording page `https://baldwincountyal.gov/government/probate-office/recording`, live probe `https://baldwin.al.publicsearch.us/`.
