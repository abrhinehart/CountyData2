# Collier County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://colliercofl.portal.civicclerk.com` |
| CivicClerk subdomain | `colliercofl` (exact) |
| Protocol | CivicClerk public web UI (React SPA); underlying REST calls to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | **Conflict:** `county-registry.yaml` L403-406 reports `platform: legistar, status: usable_seed`, but YAMLs say `civicclerk` -- YAML wins (see §8.1) |
| Bodies configured | **4** (BCC, BOA, CCPC, HEX) -- more than any other FL CivicClerk tenant in this doc set |

### Probe (2026-04-14)

```
GET https://colliercofl.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML
(standard CivicClerk React SPA; same fingerprint as Citrus / Lee / Escambia)
```

---

## 2. Bodies / Categories

Collier County has four bodies configured under `modules/commission/config/jurisdictions/FL/`:

| Slug | Body | `commission_type` | `category_id` | YAML inline comment |
|------|------|-------------------|---------------|---------------------|
| `collier-county-bcc` | Board of County Commissioners | `bcc` | **26** | -- |
| `collier-county-ccpc` | Collier County Planning Commission | `planning_board` | **28** | -- |
| `collier-county-boa` | Board of Adjustment | `board_of_adjustment` | **32** | `category_id: 32  # Hearing Examiner` |
| `collier-county-hex` | Hearing Examiner | `board_of_adjustment` | **32** | -- |

**BOA and HEX share `category_id: 32`** -- both bodies pull events from the same CivicClerk category. The `collier-county-boa.yaml` file carries the verbatim inline comment `category_id: 32  # Hearing Examiner`, which documents the overlap explicitly at the YAML level. The `collier-county-hex.yaml` sets `category_id: 32` without the comment. Scraper-side de-duplication by event `id` is necessary when iterating both slugs.

All four YAMLs share `base_url: https://colliercofl.portal.civicclerk.com` and `civicclerk_subdomain: colliercofl`.

### Detection patterns

| Slug | header_keywords | require_also | header_zone |
|------|-----------------|---------------|-------------|
| `collier-county-bcc` | `COUNTY COMMISSIONERS`, `BOARD OF COUNTY COMMISSIONERS` | `COLLIER COUNTY` | wide |
| `collier-county-ccpc` | `PLANNING` | `COLLIER COUNTY` | wide |
| `collier-county-boa` | `ADJUSTMENT`, `APPEALS` | `COLLIER COUNTY` | wide |
| `collier-county-hex` | `HEARING EXAMINER` | `COLLIER COUNTY` | wide |

---

## 3. Events Endpoint

### Request (CivicClerk public REST)

```
GET https://colliercofl.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq {category_id})&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

The scraper iterates across `category_id` values 26 (BCC), 28 (CCPC), and 32 (BOA + HEX combined), using a `seen_ids` set to de-duplicate events that would otherwise appear twice between BOA and HEX.

### OData-style query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq {category_id})` plus optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

100 events per page. All four YAMLs set `has_duplicate_page_bug: false`.

---

## 4. Event Fields

Standard CivicClerk event JSON (same shape as Citrus / Lee):

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | CivicClerk event ID |
| `startDate` | datetime | Meeting start (ISO 8601) |
| `endDate` | datetime | Meeting end |
| `title` | string | Meeting title |
| `location` | string | Meeting location |
| `categories` | array of integer | Body / category IDs (26, 28, 32) |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | URL to agenda PDF when published |
| `minutesPdfUrl` | string | URL to minutes PDF when published |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

---

## 5. What We Extract

Each event -> 0, 1, or 2 `DocumentListing` records (agenda + minutes). Same pattern as Citrus / Lee BCC.

When a `category_id: 32` event appears during BOA iteration and again during HEX iteration (which happens by design since both query category 32), the `seen_ids` deduplication keeps only the first-seen record.

---

## 6. Diff vs Citrus (3-body all-auto) and Lee (3-body mixed-platform)

| Attribute | Collier | Citrus | Lee |
|-----------|---------|--------|-----|
| CivicClerk subdomain | `colliercofl` | `citrusclerk` | `leecofl` |
| Bodies (YAMLs) | **4** (BCC, BOA, CCPC, HEX) | 3 (BCC, P&Z, BOA) | 3 (BCC, BOA, P&Z) |
| Bodies auto-scraped | **4** (all on CivicClerk) | 3 (all on CivicClerk) | 1 (only BCC; BOA/P&Z manual) |
| BCC `category_id` | 26 | 26 | 26 |
| Planning `category_id` | **28** (CCPC) | 33 (P&Z) | n/a |
| BOA `category_id` | **32** (shared with HEX) | 28 | n/a (`platform: manual`) |
| HEX `category_id` | **32** (shared with BOA) | -- | -- |
| Registry-vs-YAML conflict | **YES (legistar vs civicclerk -- YAML wins)** | NO | NO (registry has no CR slot at all) |
| Shared-category bodies | **YES (BOA + HEX share 32)** | NO | NO |

Collier is the only FL CivicClerk tenant in the repo with (a) 4 configured bodies, (b) a shared `category_id` across two bodies, (c) a registry-vs-YAML platform conflict.

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Notes |
|---------------|--------------------|--------|-------|
| BCC / CCPC / BOA / HEX Event ID | YES | `id` | Iterated across 3 distinct category_ids |
| Meeting Date | YES | `startDate` | -- |
| Agenda PDF URL | YES | `agendaPdfUrl` | -- |
| Minutes PDF URL | YES | `minutesPdfUrl` | -- |
| Meeting Title / Location | NO | -- | -- |
| Video URL | NO | -- | -- |
| Individual agenda items / votes | NO | `/api/v1/Events/{id}/Items` | Added for Legistar in commit `b16df13`, not yet wired for CivicClerk |
| BOA / HEX disambiguation | **De-dup by `id`** | `seen_ids` | Events in category 32 appear under both slugs |

---

## 8. Known Limitations and Quirks

1. **Registry-vs-YAML conflict: registry reports `platform: legistar`, YAMLs report `platform: civicclerk`. YAML wins.** `county-registry.yaml` L395-406 has Collier's `cr` slot as `platform: legistar, slug: collier-county-bcc, status: usable_seed`. But every Collier YAML (`-bcc`, `-boa`, `-ccpc`, `-hex`) explicitly sets `scraping.platform: civicclerk` with `base_url: https://colliercofl.portal.civicclerk.com`. Live probe of `colliercofl.portal.civicclerk.com/web/home` returns HTTP 200 with the standard CivicClerk SPA shell -- the tenant is genuinely CivicClerk. **Do NOT modify `county-registry.yaml`; this doc flags the conflict.** Per Planner's directive, YAMLs are the authoritative source of platform truth.

2. **BOA and HEX share `category_id: 32`.** The `collier-county-boa.yaml` file carries the verbatim inline comment `category_id: 32  # Hearing Examiner`, which confirms the overlap was intentional. Both bodies fetch the same events from CivicClerk category 32; the scraper must de-duplicate by event `id`.

3. **Four configured bodies -- most in any FL CivicClerk tenant in this doc set.** Citrus and Lee each have 3; Collier's additional CCPC + HEX split brings it to 4.

4. **`collier-county-ccpc` uses `commission_type: planning_board`.** CCPC = Collier County Planning Commission. The YAML notes "recommendations only, not final authority on legislative items."

5. **`collier-county-hex` uses `commission_type: board_of_adjustment`.** HEX = Hearing Examiner, a quasi-judicial officer. Despite being conceptually distinct from a BOA, the YAML classifies HEX under the `board_of_adjustment` type because both handle quasi-judicial land-use matters.

6. **Subdomain is `colliercofl`, NOT `colliercountyfl` or `colliercty`.** Copy verbatim from the YAMLs: `civicclerk_subdomain: "colliercofl"`.

7. **All four YAMLs share `has_duplicate_page_bug: false`.** The CivicClerk pagination for `colliercofl` is considered reliable.

8. **Header zone `wide` for all four bodies.** Standard CivicClerk pattern.

9. **Extraction notes mention "Generic Florida county. Flag sparse items for review." on all four YAMLs.** Boilerplate.

10. **`collier-county-bcc.yaml` has the inline comment `# County body -- cannot annex.`** Standard BCC-only note.

11. **HEX YAML extraction note explicitly says: "Hearing Examiner (HEX) -- quasi-judicial officer handling conditional uses, variances, and appeals."** Distinguishes HEX from CCPC (legislative recommendations) and BOA (variance hearings).

12. **BI surface is separate (`gmdcmgis.colliercountyfl.gov`, MapServer, WKID 102658).** See `collier-county-arcgis.md`. No cross-dependency.

### Related surfaces not yet documented

- **Collier PT:** No permit adapter exists for Collier under `modules/permits/scrapers/adapters/`.
- **Collier CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES`.

**Source of truth:** `modules/commission/config/jurisdictions/FL/collier-county-bcc.yaml`, `collier-county-boa.yaml` (with verbatim inline comment `category_id: 32  # Hearing Examiner`), `collier-county-ccpc.yaml`, `collier-county-hex.yaml`, `county-registry.yaml` (`collier-fl.projects.cr`, L403-406 -- stale `legistar` label), live probe against `https://colliercofl.portal.civicclerk.com/web/home` (HTTP 200, 1.1 KB SPA shell, 2026-04-14)
