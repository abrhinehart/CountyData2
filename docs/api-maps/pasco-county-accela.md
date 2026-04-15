# Pasco County FL -- Accela Citizen Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Accela Citizen Access (ACA) — shared SaaS |
| Portal URL | `https://aca-prod.accela.com/PASCO/Default.aspx` |
| Building search URL | `https://aca-prod.accela.com/PASCO/Cap/CapHome.aspx?module=Building` |
| Auth | Anonymous (public search) |
| Protocol | ASP.NET form POST + AngularJS SPA fragments (`ng-app="appAca"`) |
| Adapter posture | Research-only — no `county-registry.yaml` `pt:` row for Pasco (`pasco-fl` block only has `bi: active`) |
| Related known adapter | Polk uses the same Accela platform (`docs/api-maps/polk-county-accela.md`, `modules.permits.scrapers.adapters.accela.AccelaCitizenAccessAdapter`) |
| Tenant slug | `PASCO` (URL path segment, case-sensitive on some Accela instances) |

## 2. Probe (2026-04-14)

```
GET https://aca-prod.accela.com/PASCO/Default.aspx
-> HTTP 200, 19,025 bytes, text/html
   <title>Pasco County</title>
   <meta name="description" content="PASCO County Portal" />
   ASP.NET landing page, Bootstrap 5 chrome, Accela shared JS bundles.

GET https://aca-prod.accela.com/PASCO/Cap/CapHome.aspx?module=Building
-> HTTP 200, 255,643 bytes, text/html
   <title>Accela Citizen Access</title>
   ng-app="appAca" (AngularJS), module=Building search surface loaded.
```

Both pages render anonymously. The 255 KB Building search page includes the full search form, module selector, and standard Accela record-search controls.

## 3. Query Capabilities

Accela Citizen Access exposes record search through an ASP.NET postback flow with a server-side grid:

| Surface | Path | Method | Notes |
|---------|------|--------|-------|
| Landing | `/PASCO/Default.aspx` | GET | Portal splash |
| Module home | `/PASCO/Cap/CapHome.aspx?module=Building` | GET | Search form |
| Search postback | `/PASCO/Cap/CapHome.aspx` | POST | Form payload including `__VIEWSTATE`, date range, record type, etc. |
| Record detail | `/PASCO/Cap/CapDetail.aspx?Module=Building&capID1=...&capID2=...&capID3=...` | GET | Per-permit page |

**Pagination:** results grid is capped at 100 rows per page; further rows require paginated postbacks (shared ASP.NET grid). The adapter convention in Polk's doc is to **split the date window** when a single query hits the 100-row ceiling.

**Date-range semantics:** "Opened" date and "Issued" date selectors on the Building search form; the adapter typically uses Opened-date windows for new-permit discovery.

## 4. Field Inventory (from Accela Building search results grid, shared conventions)

Typical columns on the Building module results grid (per Polk's Accela doc and standard Accela shape):

| Column | Notes |
|--------|-------|
| Record Number | Permit number (e.g. `"BR-24-001234"`) |
| Record Type | e.g. `"Building Permit"`, `"Residential - New"`, `"Commercial - Alteration"` |
| Description | Free text of work |
| Address | Composed site address |
| Opened Date | Application filed |
| Status | e.g. `"Issued"`, `"Finaled"`, `"In Review"` |

Detail pages typically expose: applicant, contractor (name + license), parcel ID, valuation, fees, inspections, attachments, related records.

## 5. What We Extract / What a Future Adapter Would Capture

**Current state:** Pasco has NO `pt:` entry in `county-registry.yaml`. A future adapter would mirror the existing Polk Accela adapter (`polk-county-accela.md`) with the Pasco tenant slug:

| Canonical permit field | Accela source |
|------------------------|--------------|
| permit_number | Record Number |
| permit_type | Record Type |
| description | Description |
| address | Address (composed on listing; granular on detail) |
| opened_date | Opened Date |
| issued_date | Issued Date (detail only) |
| status | Status |
| applicant | Detail page |
| contractor + license | Detail page |
| parcel | Detail page |
| valuation | Detail page |
| fees | Detail page |
| inspections | Detail page |
| attachments | Detail page |

## 6. Bypass Method / Auth Posture

- Anonymous on the search page. No login, captcha, or Cloudflare observed on the 2026-04-14 probe.
- `__VIEWSTATE` / `__EVENTVALIDATION` tokens must be extracted from each form and included in subsequent POSTs (standard ASP.NET WebForms pattern).
- `aca-prod.accela.com` is the shared production Accela SaaS endpoint — same host as Polk, Brevard, Citrus, Charlotte, and ~dozens more FL / national jurisdictions.

## 7. What We Extract vs What's Available

**Not currently extracted (no Pasco PT adapter).** Full field set from the Building module would be available via the same adapter used for Polk; see `polk-county-accela.md` §5 for the field mapping template.

## 8. Known Limitations and Quirks

1. **No `pt:` row in `county-registry.yaml` for Pasco yet.** `pasco-fl` has only `bi: active`. Adding permit tracking would require a new `pt:` block with `portal: accela`, `url: https://aca-prod.accela.com/PASCO/Default.aspx`, and reuse of the existing Polk Accela adapter.
2. **100-row grid cap.** Any single Building-date-window query that would return >100 records gets truncated. The `AccelaCitizenAccessAdapter` pattern in Polk splits the window recursively until each slice is ≤100 rows.
3. **ASP.NET WebForms session.** `__VIEWSTATE` and `__EVENTVALIDATION` tokens mandatory on every postback. Standard `requests.Session` + BeautifulSoup token extraction pattern applies.
4. **AngularJS fragments (`ng-app="appAca"`) on the search surface.** The CapHome.aspx page mixes WebForms postbacks with Angular for filter rendering; scraping relies on the server-rendered result grid rather than Angular scope introspection.
5. **Tenant slug is case-sensitive on some Accela deployments.** `aca-prod.accela.com/PASCO/...` works; `aca-prod.accela.com/pasco/...` may 404. Always use the uppercase slug.
6. **No JSON API exposed on the anonymous surface.** Internal Accela backends speak JSON but are firewalled; the public-facing adapter must parse HTML tables or the ASP.NET-rendered grid.
7. **Shared host with other counties.** `aca-prod.accela.com` — any outage affects many FL counties simultaneously. Monitoring should differentiate "host down" from "Pasco-specific regression".
8. **Building module is one of several.** Pasco's ACA likely also exposes `module=Planning`, `module=Enforcement`, etc. Only Building is documented here; other modules are research-only and untested.
9. **Registry note:** registry lists Pasco's `pt:` as absent, but this doc establishes Accela ACA as the live public-facing permit surface. Document precedes any code change.
10. **Building permit search (255 KB response) loads with a landing banner and all search criteria UI.** No session cookie required beyond the ASP.NET form tokens. The 19 KB `Default.aspx` returns a thinner chrome-only splash.

Source of truth: `county-registry.yaml` L490-497 (`pasco-fl.projects` — only `bi` present, no `pt` row), live probes of `https://aca-prod.accela.com/PASCO/Default.aspx` (2026-04-14, HTTP 200, 19,025 bytes) and `https://aca-prod.accela.com/PASCO/Cap/CapHome.aspx?module=Building` (2026-04-14, HTTP 200, 255,643 bytes). Adapter contract sourced from `docs/api-maps/polk-county-accela.md` and `modules.permits.scrapers.adapters.accela` conventions.
