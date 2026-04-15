# Jefferson County AL -- Accela Citizen Access (ePermitJC) API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Jefferson County, AL Department of Land Development (unincorporated permits) |
| Portal public URL | `https://permits.jccal.org/citizenaccess/Default.aspx` |
| Canonical (after redirect) | `https://aca-prod.accela.com/JCCAL/Default.aspx` |
| Vendor | Accela (Civic Platform + Citizen Access / ACA) |
| Agency slug | `JCCAL` |
| UI | ASP.NET WebForms (ACA; heavy ViewState) |
| Auth | Anonymous browse / named account for apply-filing; reads are public |
| Registry entry | `county-registry.yaml` L571-583 has BI only; **no `pt:` block** |
| Scope | Unincorporated Jefferson County AL only |

**Out-of-scope note -- City of Birmingham.** This portal covers unincorporated Jefferson County AL. The City of Birmingham issues permits separately through its own system (not Accela on this subdomain). All Birmingham city-limits permit activity is **explicitly out of scope** for this doc; only county-level ePermitJC data is covered here. Smaller cities inside Jefferson County (Hoover, Vestavia Hills, Mountain Brook, Homewood, etc.) likewise operate their own permit offices and are similarly out of scope.

## 2. Probe (2026-04-14)

```
GET https://permits.jccal.org/citizenaccess/Default.aspx
-> 301 -> https://aca-prod.accela.com/JCCAL/Default.aspx
-> HTTP 200  (Accela "Citizen Access" landing; walkMeData + accelaVariables JS bootstrap; 62 KB)
```

`permits.jccal.org` is a CNAME-style wrapper; the live ACA tenant is `aca-prod.accela.com/JCCAL/`. Body confirms the Accela Citizen Access product by presence of `accelaVariables.userId`, `walkMeData`, and the `/JCCAL/bundles/accela-common` script bundle.

County landing page copy at `jccal.org/Default.asp?ID=1993&pg=ePermit` confirms the same target portal for residential, commercial, sewer, and zoning permit applications in the unincorporated county and for the Erosion and Sediment Control permit.

## 3. Search / Query Capabilities

Standard Accela ACA pattern; no public REST API. Searches go through ASP.NET WebForms postbacks with ViewState:

- Generic search: `Cap/CapHome.aspx?module=Building` (and other modules: Planning, Engineering, LandDevelopment).
- Per-record detail: `Cap/CapDetail.aspx?Module=Building&capID=<capId>`.
- Date-range permit search supported within a selected module.

This matches the pattern documented in other Accela ACA tenants in the repo (Brevard FL Accela, Charlotte FL Accela, Polk FL Accela) -- the platform is uniform; per-agency customization is limited to visible record types and searchable modules.

## 4. Field Inventory

Expected (pending live crawl; consistent with Accela ACA record-detail output):

- Permit number / CAP ID.
- Address + parcel.
- Application date, issued date, status.
- Record type (BLD, ELE, ESC, etc.).
- Description of work, valuation (where disclosed).
- Applicant / contractor.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing.** No PT adapter exists under `modules/permits/scrapers/adapters/` for Jefferson AL. An adapter would mirror the existing Accela-family adapters (`accela_citizen_access_adapter` / `accela_accessor_adapter` conventions in the repo), then register a `pt_jurisdiction_config` row and a `county-registry.yaml` `pt:` block pointing at `https://aca-prod.accela.com/JCCAL/Default.aspx`.

## 6. Auth Posture / Bypass Method

Anonymous read for public permit search. A named user account is required for apply-filing (fees, attachments) but **not** for browsing issued permit records. No captcha observed on the landing page. Accela typically gates full result exports behind account tiers but the per-record detail pages are readable without login.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Permit number / CAP ID | NO |
| Address + parcel | NO |
| Dates (applied, issued) | NO |
| Status | NO |
| Record type | NO |
| Valuation | NO |
| Applicant | NO |
| Contractor | NO |
| Description | NO |

## 8. Known Limitations and Quirks

- **City of Birmingham permits are NOT in this portal** -- they are handled by the City separately and are explicitly out of scope.
- Other incorporated Jefferson County cities (Hoover, Vestavia Hills, Mountain Brook, Homewood, Bessemer-city proper, etc.) likewise operate their own permit offices; this portal covers the unincorporated county only.
- `permits.jccal.org` is a branded alias; canonical Accela tenant URL is `https://aca-prod.accela.com/JCCAL/`. Use the canonical form in adapter config so that the 301 hop is avoided.
- Accela ACA's heavy ViewState makes scraping brittle; adapters in the repo use session + postback-with-eventtarget patterns rather than plain GETs.
- Non-disclosure state applies to deeds, not permits; permit valuations (when published by the applicant) are legitimate data, though not sale prices.

Source of truth: `county-registry.yaml` (jefferson-al L571-583, BI-only -- no PT config), live probe `https://permits.jccal.org/citizenaccess/Default.aspx` -> `https://aca-prod.accela.com/JCCAL/Default.aspx`, Jefferson County ePermit page at `https://www.jccal.org/Default.asp?ID=1993&pg=ePermit`.
