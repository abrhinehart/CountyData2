# Duval County FL -- OnCore Public Records Search (Clerk) API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | **OnCore** (Jacksonville / Duval Clerk's official records viewer — legacy ASP.NET WebForms application) |
| Portal URL | `https://oncore.duvalclerk.com/` |
| Page title | "Duval County Public Records Search" |
| Auth | Anonymous |
| Protocol | ASP.NET WebForms (`__VIEWSTATE` / `__EVENTVALIDATION` form postbacks); `iso-8859-1` charset declared |
| Browser compat markers | `<meta http-equiv="X-UA-Compatible" content="IE=9" />` and IE9-specific stylesheet (`<!--[if IE 9]>...<![endif]-->`) |
| Adapter status | **`unverified — needs validation`** — no adapter exists in this repo for OnCore. This is a new portal type not previously catalogued. |
| Registry status | **No `cd2:` row in `county-registry.yaml` for Duval** — `duval-fl` has only `bi: active` and `cr: partial_or_outlier` (L408-419) |

## 2. Probe (2026-04-14)

```
GET https://oncore.duvalclerk.com/
-> HTTP 200, 18,377 bytes, text/html (charset=iso-8859-1)
   <title>Duval County Public Records Search</title>
   <meta http-equiv="X-UA-Compatible" content="IE=9" />
   <!--[if IE 9]><link rel="stylesheet" type="text/css"
       media="screen" href="/Content/ie9specific.css" /><![endif]-->
   ASP.NET WebForms landing page. No Angular, no React. No __VIEWSTATE
   visible in first 2500 bytes (deeper into markup).

GET https://www.duvalclerk.com/
-> HTTP 200, 136,797 bytes, text/html
   Duval Clerk of Courts homepage. Normal public-sector CMS. Links from here
   lead to oncore.duvalclerk.com for official records search.
```

Other clerk-subdomain probes returned DNS failures or were not attempted.

## 3. Query Capabilities

**`unverified — needs validation`** — the OnCore search surface has not been reverse-engineered in this pass. The platform is a legacy ASP.NET WebForms application with the following likely characteristics based on the `oncore` platform family (Harris Govern / Tyler acquired OnCore in 2023):

- Search types typically include: Name (grantor/grantee), Book/Page, Document Type, Record Date range, Instrument Number, Legal Description, Parcel ID, Consideration amount.
- Pagination: server-side WebForms grid, typically 25–100 rows per page, driven by `__EVENTTARGET` / `__EVENTARGUMENT` postbacks.
- Date-range search returns all document types by default; filtering to deeds happens via doc-type code selection.
- Deed document type codes must be extracted from the search form's dropdown (values unknown without a live session).

**No endpoint URLs have been enumerated for this OnCore tenant in this pass.** A working adapter would require:

1. Fetch landing page; extract `__VIEWSTATE` / `__EVENTVALIDATION` tokens.
2. Navigate to Date Range search form (follow internal link / tab control).
3. POST search criteria with required tokens.
4. Parse tabular result HTML; paginate via WebForms event postbacks.

## 4. Field Inventory

**Not captured** — requires a working search postback. Expected deed-row fields per OnCore convention:

| Canonical field | Expected OnCore column |
|-----------------|------------------------|
| Grantor | Grantor (name, indexed) |
| Grantee | Grantee |
| Record date | Record Date |
| Doc type | Doc Type (code + description) |
| Book / page | Book / Page |
| Instrument number | Instrument # |
| Legal description | Legal (free text) |
| Consideration | Consideration (sale price — FL is full-disclosure) |
| Document image | Per-doc viewer (click-through) |

## 5. What We Extract / What a Future Adapter Would Capture

Nothing currently. A future adapter would deliver the standard CD2 canonical row (grantor / grantee / record_date / doc_type / instrument / book / page / legal / consideration) once OnCore's search / pagination protocol is characterized.

## 6. Bypass Method / Auth Posture

- Landing page returns HTTP 200 anonymously.
- ASP.NET WebForms session typically requires `__VIEWSTATE` tokens on every postback.
- **No captcha or Cloudflare observed on the landing page.** Consistent with other FL OnCore tenants, search may still be throttled server-side.
- Use of an `IE=9` X-UA-Compatible hint suggests the app may render poorly in modern browsers' strict modes but is still served HTML-first; JS is not required for form postbacks.

## 7. What We Extract vs What's Available

**Nothing extracted; full availability pending reverse-engineering.**

## 8. Known Limitations and Quirks

1. **OnCore is a distinct platform** — not AcclaimWeb, not LandmarkWeb, not BrowserView, not Tyler Self-Service, not Accela. No existing adapter in CountyData2 (`county_scrapers/*.py`) handles OnCore; this is a greenfield adapter if Duval CD2 is scoped.
2. **OnCore was acquired by Tyler in 2023** (formerly Harris Govern). Future OnCore instances may migrate to Tyler's unified recorder platform, but `oncore.duvalclerk.com` currently runs the legacy OnCore skin.
3. **Legacy IE9 compatibility markers** suggest the UI was frozen circa 2012-2015. Any automated client emulating a modern browser must tolerate older HTML patterns (e.g. table-based layout, inline JS).
4. **`charset=iso-8859-1`** declared on the page. Latin-1 decoding required for any scraped text — UTF-8 assumption will corrupt non-ASCII characters in names / legal descriptions.
5. **No `cd2:` row in `county-registry.yaml` for Duval.** Adding Duval CD2 coverage requires both a new registry row (platform `oncore`, URL `https://oncore.duvalclerk.com/`) and a new adapter.
6. **Duval is consolidated** — deed coverage via OnCore spans the entire consolidated Jacksonville/Duval jurisdiction. The four small independent municipalities share this deed repository (county-level clerk, not municipal).
7. **No Accela / AcclaimWeb / LandmarkWeb / Tyler Self-Service equivalents** for Duval deeds. OnCore is the only confirmed live deed portal.
8. **`www.duvalclerk.com` and `oncore.duvalclerk.com`** are related but serve different purposes — the main clerk website (136 KB landing) links to OnCore for records search. Don't crawl the main clerk site for deed data.
9. **OnCore tenants elsewhere in FL** — e.g. Pinellas, Hillsborough — may share the same URL pattern (`oncore.{county}clerk.com`). If Duval is added, pattern-match probes on other OnCore counties would be a cheap follow-on research task.
10. **Full-disclosure state.** FL requires sale prices on deeds; OnCore typically exposes a "Consideration" column on the search grid or detail page. Verify in the first live validation run that Duval's OnCore exposes this column.

Source of truth: live probes 2026-04-14 of `https://oncore.duvalclerk.com/` (HTTP 200, 18,377 bytes, ASP.NET WebForms page titled "Duval County Public Records Search") and `https://www.duvalclerk.com/` (HTTP 200, 136,797 bytes, clerk homepage). `county-registry.yaml` L408-415 (`duval-fl.projects` — no `cd2` row present). **Search protocol and field contract `unverified — needs validation` — no reverse-engineering of search postbacks was attempted in this research pass.**
