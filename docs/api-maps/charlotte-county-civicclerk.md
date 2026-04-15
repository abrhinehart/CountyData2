# Charlotte County FL -- CivicClerk API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicClerk (CivicPlus portal for agendas / minutes) |
| Portal base URL | `https://charlottecountyfl.portal.civicclerk.com` |
| CivicClerk subdomain | `charlottecountyfl` |
| Protocol | CivicClerk public web UI (React SPA); underlying REST calls to CivicClerk's public events endpoints |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** |
| Jurisdiction YAML | **ABSENT -- no `charlotte-county-*.yaml` under `modules/commission/config/jurisdictions/FL/`** |

### Wave 1 probe (2026-04-14)

Candidate platforms were probed in order; the Charlotte CR surface was determined as follows:

| Platform | Probe URL | HTTP | Size | Outcome |
|----------|-----------|------|------|---------|
| Legistar | `https://charlottefl.legistar.com/` | 200 | **19 bytes** | `Invalid parameters!` -- Legistar router error; tenant does not exist |
| **CivicClerk** | `https://charlottecountyfl.portal.civicclerk.com/web/home` | **200** | **~1.1 KB** | **Authentic CivicClerk React SPA shell (`<title>Public Portal • CivicClerk</title>`, references `/static/js/main.2acd9b93.js` and `/static/css/main.671d2fa5.css`)** |
| Granicus | `https://charlotte-fl.granicus.com/` | 404 | 949 | Not a Granicus tenant |
| CivicPlus | `https://www.charlottecountyfl.gov/AgendaCenter` | 404 | ~55 KB | County website 404 page |
| NovusAgenda | `https://charlottecountyfl.novusagenda.com/agendapublic/` | 200 | 1453 | Returns `An HTTP error occurred. . Please try again.` error shell -- not a valid tenant |

**Winner: CivicClerk.** The CivicClerk probe returned the identical SPA shell observed for known-good CivicClerk tenants (Citrus, Escambia, Lee, Collier) -- the same main.js / main.css fingerprint and the same `root`, `clerk-embed-*` mount-point divs.

```
GET https://charlottecountyfl.portal.civicclerk.com/web/home
-> HTTP 200, ~1.1 KB shell HTML with React app mount points
(body references /static/js/main.2acd9b93.js and /static/css/main.671d2fa5.css)
```

---

## 2. Bodies / Categories

**No jurisdiction YAML exists for Charlotte under `modules/commission/config/jurisdictions/FL/`.** Consequently no `category_id` values are configured; the BCC, Planning Commission, and any Board of Adjustment or Zoning Board categories have not been identified. A future engineer onboarding Charlotte CR would need to:

1. Open the SPA at `https://charlottecountyfl.portal.civicclerk.com/web/home` in a browser with DevTools.
2. Inspect the XHR traffic to `/api/v1/Events` to discover the `categories` array that backs each body (BCC, P&Z, BOA, HEX if any).
3. Author `charlotte-county-bcc.yaml` (+ `-pz.yaml` / `-boa.yaml` as needed), copying the shape of `collier-county-bcc.yaml` or `lee-county-bcc.yaml`.

Until then, the CR surface is **discovered but not wired** -- the CivicClerk tenant exists, but the scraper has no config to iterate.

---

## 3. Events Endpoint (platform default, not yet bound to Charlotte)

Based on the peer CivicClerk tenants (Citrus, Escambia, Lee, Collier) documented in this repo, the platform uses this request shape:

```
GET https://charlottecountyfl.portal.civicclerk.com/api/v1/Events?$filter=categories/any(c: c eq {category_id})&$orderby=startDate desc&$top=100&$skip=0
Headers:
  User-Agent: CommissionRadar/1.0
  Accept: application/json
```

### OData-style query parameters

| Parameter | Usage |
|-----------|-------|
| `$filter` | `categories/any(c: c eq {category_id})` plus optional date filter |
| `$orderby` | `startDate desc` |
| `$top` | 100 per page |
| `$skip` | Offset for pagination |

### Pagination

Page through 100 events at a time until empty or `recordsTotal` reached. 0.5s delay between paginated requests (matches the Legistar / peer CivicClerk cadence).

---

## 4. Event Fields (CivicClerk platform convention)

| Field | Type | Notes |
|-------|------|-------|
| `id` | integer | CivicClerk event ID |
| `startDate` | datetime | Meeting start (ISO 8601) |
| `endDate` | datetime | Meeting end |
| `title` | string | Meeting title |
| `location` | string | Meeting location |
| `categories` | array of integer | Body / category IDs |
| `body` | string | Body display name |
| `agendaPdfUrl` | string | URL to agenda PDF when published |
| `minutesPdfUrl` | string | URL to minutes PDF when published |
| `videoUrl` | string (nullable) | Meeting video |
| `isPublished` | boolean | Visibility flag |

Field names vary slightly per CivicClerk version; the platform adapter normalizes via a field-mapping layer.

---

## 5. What We Extract

**Nothing today.** No Charlotte YAML -> no scraper run. Once a YAML is authored, each event would yield 0/1/2 `DocumentListing` records (agenda + minutes) with the standard shape documented in `citrus-county-civicclerk.md` §5.

---

## 6. Diff vs Citrus (active CivicClerk) + Putnam (custom, no YAML)

Charlotte is a CivicClerk tenant with NO YAML -- a state not seen elsewhere in the FL doc set.

| Attribute | Charlotte | Citrus | Putnam |
|-----------|-----------|--------|--------|
| Platform | CivicClerk (tenant confirmed) | CivicClerk (tenant confirmed) | Custom / website (NO standard platform) |
| CivicClerk subdomain | `charlottecountyfl` | `citrusclerk` | n/a |
| Portal URL | `https://charlottecountyfl.portal.civicclerk.com` | `https://citrusclerk.portal.civicclerk.com` | `https://www.putnam-fl.gov` |
| Jurisdiction YAML(s) | **NONE** | 3 (`bcc`, `pz`, `boa`) | NONE |
| Category IDs identified | **NONE (not yet inspected)** | 26 (BCC), 33 (P&Z), 28 (BOA) | n/a |
| Registry status | ABSENT | `live` | `research_done` |
| Auto-scraper | NO (discovery-only) | YES | NO |
| Manual workflow | YES | NO | YES |

---

## 7. Endpoints That Are (or Are NOT) Available

Negative findings from the Wave 1 probe:

| Vendor check | Result |
|--------------|--------|
| Legistar (`charlottefl.legistar.com`) | `Invalid parameters!` (19-byte router error) -- NO |
| **CivicClerk (`charlottecountyfl.portal.civicclerk.com`)** | **HTTP 200 ~1.1 KB SPA shell -- YES** |
| Granicus (`charlotte-fl.granicus.com`) | HTTP 404 -- NO |
| CivicPlus AgendaCenter (`www.charlottecountyfl.gov/AgendaCenter`) | HTTP 404 -- NO |
| NovusAgenda (`charlottecountyfl.novusagenda.com/agendapublic/`) | HTTP 200 but error page -- NO |

---

## 8. Known Limitations and Quirks

1. **CivicClerk tenant exists but no jurisdiction YAML does.** The subdomain `charlottecountyfl.portal.civicclerk.com` returns a valid CivicClerk SPA shell (same fingerprint as Citrus/Escambia/Lee/Collier), but there is no `charlotte-county-bcc.yaml` (or pz/boa) under `modules/commission/config/jurisdictions/FL/`. The scraper has nothing to iterate. This is the same state as Putnam CR -- tenant discovered, YAML absent.

2. **Category IDs not yet inspected.** Unlike Citrus (26/33/28) or Collier (26/28/32), Charlotte's CivicClerk category IDs for BCC / P&Z / BOA have not been identified. Onboarding requires opening the SPA and inspecting XHR traffic.

3. **Registry absence.** Charlotte is not in `county-registry.yaml` for CR (or any other project slot). Cross-project tooling that reads the registry will skip Charlotte entirely.

4. **Legistar candidate path returns router error, not 404.** The `charlottefl.legistar.com` probe returns HTTP 200 with the 19-byte body `Invalid parameters!` -- this is Legistar's default response when the tenant does not exist. A client that checks for HTTP 200 alone would false-positive; body-content inspection is required.

5. **NovusAgenda candidate also returns HTTP 200 with an error page.** The `charlottecountyfl.novusagenda.com/agendapublic/` probe returns HTTP 200, but the body contains the ASP.NET error `An HTTP error occurred. Please try again.` -- again, HTTP 200 alone is not a sufficient signal.

6. **CivicClerk subdomain is `charlottecountyfl`, not `charlottecofl`.** Unlike Lee (`leecofl`) or Collier (`colliercofl`) which use the `-cofl` convention, Charlotte's subdomain is the full county name concatenated (`charlottecountyfl`).

7. **Same React SPA blind-spot as other CivicClerk portals.** The probed response is the SPA shell (~1.1 KB). All meaningful data is fetched via XHR after mount. Future scraper changes must re-inspect network traffic to confirm the current `/api/v1` path shape.

8. **Document format for agendas and minutes: PDF.** Consistent with every other CivicClerk tenant in this repo.

9. **Accela adapter is already wired for Charlotte PT** (see `charlotte-county-accela.md`). Onboarding CR independently requires a new YAML but does not block PT.

10. **`has_duplicate_page_bug` status unknown.** Other CivicClerk tenants in this repo set this explicitly to `false` (Citrus, Lee, Collier). Charlotte's behavior can only be tested once pagination is exercised against live category IDs.

11. **BCC cadence and P&Z cadence unknown.** No registry notes or YAML cadence fields exist. A future engineer must discover these from the live portal.

12. **This doc flags the gap but does NOT create YAML** (same discipline as `putnam-county-custom-cr.md`).

### Related surfaces not yet documented

- **Charlotte CD2:** No clerk-recording surface documented. Clerks are not in `LANDMARK_COUNTIES` and no AcclaimWeb / BrowserView / Tyler Self-Service config exists.

**Source of truth:** Wave 1 live probe matrix against `https://charlottefl.legistar.com/`, `https://charlottecountyfl.portal.civicclerk.com/web/home`, `https://charlotte-fl.granicus.com/`, `https://www.charlottecountyfl.gov/AgendaCenter`, and `https://charlottecountyfl.novusagenda.com/agendapublic/` (all probed 2026-04-14); absence of `charlotte-county-*.yaml` under `modules/commission/config/jurisdictions/FL/`; absence of `charlotte-fl` from `county-registry.yaml`
