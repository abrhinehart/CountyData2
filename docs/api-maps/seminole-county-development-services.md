# Seminole County FL -- Development Services (Building Division) API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | **`unverified — needs validation`** — Seminole County Development Services, Building Division publishing surface |
| County CMS page | `https://www.seminolecountyfl.gov/departments-services/development-services/` |
| Building Division page | `https://www.seminolecountyfl.gov/departments-services/development-services/building-division/` |
| Permit portal host | **Not identified by probe** |
| Auth | Unknown |
| Protocol | Unknown |
| Adapter status | **`unverified — needs validation`** — no adapter for Seminole permits exists in this repo |
| Registry status | **No `pt:` row in `county-registry.yaml` for Seminole** — `seminole-fl` has only `bi: active` and `cr: partial_or_outlier` (L509-522) |

## 2. Probe (2026-04-14)

### Seminole County main website

```
GET https://www.seminolecountyfl.gov/departments-services/development-services/
-> HTTP 200, 202,670 bytes, text/html
   Standard HTML5 page, Font Awesome 6.2.1 + Bootstrap + custom county CMS.
   Landing page for the Development Services department.

GET https://www.seminolecountyfl.gov/departments-services/development-services/building-division/
-> HTTP 200, 376,031 bytes, text/html
   Building Division landing. Larger page (extensive reference content / fee schedules / forms).
```

### Negative-result probes (Seminole is NOT on these patterns)

```
GET https://citizenaccess.seminolecountyfl.gov/                      -> URLError (DNS fail)
GET https://buildingpermits.seminolecountyfl.gov/                    -> URLError (DNS fail)
GET https://permits.seminolecountyfl.gov/                            -> URLError (DNS fail)
GET https://permits.seminolecountyfl.gov/apps/selfservice/           -> URLError (DNS fail)
GET https://seminolecountyfl-energovweb.tylerhost.net/apps/selfservice/api/tenants/gettenantslist -> URLError (DNS fail)
GET https://seminolecountyfl.tylerhost.net/apps/selfservice/         -> URLError (DNS fail)
GET https://aca-prod.accela.com/SEMINOLE/Default.aspx                -> HTTP 404 Not Found
GET https://aca-prod.accela.com/SCFL/Default.aspx                    -> HTTP 404 Not Found
```

All predictable permit-portal hostnames and common vendor slugs fail. Seminole is **not** on a standard-pattern Tyler EnerGov, Accela ACA, or county-owned `citizenaccess.*` surface that a URL-guess probe can find.

## 3. Query Capabilities

**`unverified — needs validation`.** The actual permit portal must be discovered by inspecting the Building Division page HTML (376 KB — likely contains prominent links to the online permit system). Candidate platforms (not ruled out by this pass but not directly probed either): Citizenserve (third-party SaaS at `www4.citizenserve.com/SEMINOLE/...` or similar), CityView (Harris), or an internal county-hosted ASP.NET application.

Next steps for discovery:

1. Parse `seminolecountyfl.gov/departments-services/development-services/building-division/` HTML for anchor tags with text containing "Apply", "Online", "Permit", "Inspect", or similar action words.
2. Follow any outbound links to vendor-hosted portals.
3. Probe the resulting host for `/api/tenants/gettenantslist` (Tyler) or `/Default.aspx` (Accela-style) or `/Portal/PortalController` (Citizenserve) to fingerprint the platform.

## 4. Field Inventory

**Not available** — platform not yet identified.

## 5. What We Extract / What a Future Adapter Would Capture

Nothing currently. A future adapter would deliver the standard permit canonical fields (permit number, type, dates, status, address, parcel, applicant, contractor, valuation, description) once the platform is identified.

## 6. Bypass Method / Auth Posture

- Both probed pages (Development Services + Building Division) respond HTTP 200 anonymously with standard TLS (no cert issues here, unlike `seminoleclerk.org`).
- Authentication / session posture of the actual permit portal (once found) is unknown.

## 7. What We Extract vs What's Available

**Nothing extracted; API shape unknown.**

## 8. Known Limitations and Quirks

1. **No `pt:` row in `county-registry.yaml` for Seminole.** Only `bi: active` and `cr: partial_or_outlier`. Adding permit tracking requires both a new registry row and a new (or reused) adapter.
2. **Seminole's domain structure is split.** Clerk on `seminoleclerk.org` (`.org`), County on `seminolecountyfl.gov` (`.gov`). Deeds belong to the Clerk, permits belong to the County — two different domain spaces to probe separately.
3. **Not on Accela ACA under common slugs.** `SEMINOLE` and `SCFL` both 404'd. A differently-named Accela slug is possible but was not guessed.
4. **Not on Tyler EnerGov under the common pattern.** `seminolecountyfl-energovweb.tylerhost.net` DNS-fails. An alternate pattern (`seminoleco-energovweb`, `seminolefl-energovweb`, `scfl-energovweb`) may exist but was not probed.
5. **No county-owned permit-portal subdomain DNS-resolves.** `citizenaccess.`, `buildingpermits.`, `permits.` all fail on `seminolecountyfl.gov`. Rules out self-hosted portals at predictable names.
6. **Building Division page is 376 KB** — large enough to contain significant reference content. A follow-up HTML-parser probe would likely extract a direct link to the online permit portal.
7. **Seminole cities** (Altamonte Springs, Casselberry, Lake Mary, Longwood, Oviedo, Sanford, Winter Springs) each run their own permit intake. Countywide permit coverage would need per-city portal research as well.
8. **No `epermits.` or `eplan.` variant probed on either `.gov` or `.org` zones** — room for further discovery.
9. **Seminole's Commissioner District is tracked on ArcGIS** (see `seminole-county-arcgis.md`) — so parcel → commissioner district lookups are already available even without a permit feed.
10. **This document exists to prevent re-probing the DNS-failed candidates.** Future runs should harvest the portal URL from the Building Division HTML rather than guess subdomains.

Source of truth: live probes 2026-04-14 of `https://www.seminolecountyfl.gov/departments-services/development-services/` (HTTP 200, 202,670 bytes), `https://www.seminolecountyfl.gov/departments-services/development-services/building-division/` (HTTP 200, 376,031 bytes), and DNS-failed probes of 8 predictable permit-portal hostname patterns plus 2 Accela slug variants. `county-registry.yaml` L509-522 (`seminole-fl.projects` — no `pt` row). **Permit portal host `unverified — needs validation`; platform `unverified — needs validation`.**
