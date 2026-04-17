# Duval County FL -- Jax EPICS (Building Inspections) API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | **Jax EPICS** — City of Jacksonville Building Inspections SPA (Electronic Permits / Inspections / Compliance System) |
| Portal URL | `https://buildinginspections.coj.net/` |
| Architecture | Angular SPA (`<title>Jax EPICS</title>`, Angular runtime / router loaded at boot) |
| Auth | Anonymous for public search surfaces (landing page public; some features may require login) |
| Protocol | SPA loads JSON from internal Jax EPICS API (endpoint pattern not surveyed in this pass) |
| Registry status | **No `pt:` row in `county-registry.yaml` for Duval** — `duval-fl` has only `bi: active` and `cr: partial_or_outlier` (L408-419) |
| Adapter status | **`unverified — needs validation`** — no adapter built; platform is custom to COJ and does NOT match Tyler EnerGov / Accela / CityView / Citizenserve shapes |

## 2. Probe (2026-04-14)

```
GET https://buildinginspections.coj.net/
-> HTTP 200, 72,789 bytes, text/html
   <title>Jax EPICS</title>
   <base href="/">
   Angular SPA — Roboto font stack loaded from fonts.gstatic.com,
   SweetAlert2 / Angular material / standard Angular bootstrap markers.

GET https://buildinginspections.coj.net/api/tenants/gettenantslist
-> HTTP 200, 72,789 bytes  (SAME Angular SPA shell — NOT a Tyler EnerGov API
   response. The /api/* path is served as the SPA fallback, meaning Jax EPICS
   does NOT implement the Tyler tenant-discovery endpoint pattern.)

GET https://maps.coj.net/jaxgis
-> HTTP 200, 246 bytes  (redirect to JaxGIS map viewer via meta refresh)
```

Additional negative-result probes (Duval is NOT on these):

```
GET https://jaxcoj-energovweb.tylerhost.net/apps/selfservice/api/tenants/gettenantslist  -> URLError (DNS fail)
   (Rules out a standard Tyler EnerGov tenant pattern for COJ.)

GET https://aca-prod.accela.com/JAX/Default.aspx  -> HTTP 404
   (Rules out Accela Citizen Access under the `JAX` slug. A differently-named
   Accela slug is possible but was not guessed.)

GET https://citizenaccess.coj.net/  -> URLError (DNS fail)
GET https://buildingpermits.coj.net/  -> URLError (DNS fail)
```

## 3. Query Capabilities

**`unverified — needs validation`.** The Jax EPICS SPA loads its data via internal JSON endpoints that were not probed in this pass (the naive `/api/tenants/gettenantslist` attempt fell through to the SPA fallback, confirming it's not a Tyler EnerGov tenant). A working adapter would require:

1. Opening `https://buildinginspections.coj.net/` in a browser / headless Chromium.
2. Capturing XHR / Fetch traffic to identify the actual API host + endpoint layout (likely `/api/<module>/<verb>` or similar).
3. Extracting bearer token / session cookie requirements (if any).
4. Modeling the search criteria contract.

Public records hint that Jax EPICS is a COJ-custom application built on the City's Microsoft stack; the codebase itself is not reachable from this research pass.

## 4. Field Inventory

**Not available** — requires live browser-inspection of Jax EPICS XHR traffic.

## 5. What We Extract / What a Future Adapter Would Capture

Nothing currently. A future adapter would deliver the standard permit canonical fields (permit number, type, dates, status, address, parcel, applicant, contractor, valuation, description) but the field-level mapping depends on the Jax EPICS schema, which is undocumented publicly.

## 6. Bypass Method / Auth Posture

- Landing page is anonymous (HTTP 200 with no redirect).
- Whether search surfaces require an account (common on COJ permit-tracking tools) is **`unverified`**. Many COJ resident-facing portals allow anonymous read-only search with authenticated write (filing new permits).
- `buildinginspections.coj.net` did NOT 503 on the 2026-04-14 probe, unlike `www.coj.net/` which did 503 — bot mitigation applies to the main COJ portal but not to the Jax EPICS subdomain.

## 7. What We Extract vs What's Available

**Nothing extracted; API shape unknown.**

## 8. Known Limitations and Quirks

1. **Jax EPICS is a COJ-custom application, NOT Tyler EnerGov / Accela / CityView.** The subdomain naming (`buildinginspections.coj.net`) and the SPA title (`Jax EPICS`) are COJ-specific. Any adapter must be written against Jax EPICS endpoints, not copied from existing Tyler/Accela code.
2. **Angular SPA with client-side routing** — the `<base href="/">` tag and the behavior of `/api/tenants/gettenantslist` falling through to the SPA shell both indicate the Angular router catches unmatched paths and serves index.html. This is a common pattern that complicates HTTP probing: HTTP 200 responses may not mean "endpoint exists" but "SPA fallback served".
3. **`www.coj.net/` returns HTTP 503** with bot-mitigation; `buildinginspections.coj.net` returns HTTP 200 cleanly. Operational monitoring must distinguish the two.
4. **Registry has no `pt:` row for Duval.** `county-registry.yaml` L408-415 has only `bi: active` and a `cr:` row. Adding permit tracking would require a new `pt:` block with `portal: jax-epics` (new platform value) and a custom adapter.
5. **Jacksonville consolidated city-county** means "Duval permits" and "Jacksonville permits" are the same dataset. There is no separate county-level permit surface outside the four small independent municipalities (Jacksonville Beach, Neptune Beach, Atlantic Beach, Baldwin) which have their own building departments.
6. **The small independent municipalities are NOT on Jax EPICS.** If/when permit coverage expands to those four municipalities, each is a separate portal discovery task:
   - Jacksonville Beach — `jacksonvillebeach.org`
   - Neptune Beach — `neptune-beach.com`
   - Atlantic Beach — `coab.us`
   - Baldwin — `baldwinfl.us`
7. **Not on Accela ACA.** `aca-prod.accela.com/JAX/Default.aspx` 404'd on probe; if a JAX Accela exists, it's under an unguessed slug.
8. **Not on Tyler EnerGov.** `jaxcoj-energovweb.tylerhost.net` DNS failed.
9. **No `citizenaccess.coj.net` or `buildingpermits.coj.net` hostnames.** Both DNS-fail. `buildinginspections.coj.net` is the correct subdomain.
10. **`maps.coj.net/jaxgis`** is an ArcGIS map viewer (not a permit portal); referenced here only to prevent confusion — it is a GIS visualization, not a permit search.

Source of truth: live probes 2026-04-14 of `https://buildinginspections.coj.net/` (HTTP 200, 72,789 bytes, Angular SPA titled "Jax EPICS"), `https://maps.coj.net/jaxgis` (HTTP 200, 246 bytes, redirect), and ruled-out variants (`jaxcoj-energovweb.tylerhost.net`, `aca-prod.accela.com/JAX/Default.aspx`, `citizenaccess.coj.net`, `buildingpermits.coj.net`). `county-registry.yaml` L408-415 (`duval-fl.projects` — `pt` row absent). **All endpoint behavior beyond the landing-page fetch is `unverified — needs validation`.**
