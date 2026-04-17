# Jefferson County AL -- Pioneer LandmarkWeb (Probate) API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Jefferson County Probate Court (Alabama; Probate Judge, not Clerk of Court) |
| Portal URL | `https://landmarkweb.jccal.org/LandmarkWeb` |
| Companion site | `http://jeffcoprobatecourt.com/` (probate court informational site) |
| Vendor | Pioneer Technology Group LandmarkWeb |
| Version | 1.5.103 (seen in CSS asset query string) |
| UI | Bootstrap + jQuery DataTables (HTML form + AJAX DataTables) |
| Auth | Disclaimer click-through -> session cookie (no named account required) |
| Bypass | `captcha_hybrid` pattern already used for Bay / Escambia / St. Lucie LandmarkWeb deployments |
| Registry entry | `county-registry.yaml` L571-583 has BI only; **no `cd2:` block listed** |
| Client reuse | `county_scrapers.landmark_client.LandmarkSession` |

**Top-line quirk: Jefferson County Probate Court operates TWO recording divisions -- Birmingham and Bessemer.** Both offices record separately; the county-wide LandmarkWeb index appears to aggregate across divisions (visible `Division` attribute on ArcGIS parcels corresponds), but split-division filing behavior needs confirmation at first live pull. This is unique among the 4 counties in this batch.

## 2. Probe (2026-04-14)

```
GET https://landmarkweb.jccal.org/LandmarkWeb
-> HTTP 200  (HTML landing; title "Landmark Web Official Records Search"; Pioneer 1.5.103 asset tags)
```

Pioneer LandmarkWeb; same vendor/product as Bay County FL (`records2.baycoclerk.com/Recording`), Escambia County FL, St. Lucie County FL. The handshake + DataTables query shape documented in `docs/api-maps/bay-county-landmark.md` applies here directly.

The companion `jeffcoprobatecourt.com` site is a WordPress informational brochure, not a record-search surface; it links out to the LandmarkWeb portal for actual searches.

## 3. Search / Query Capabilities

Using the canonical Pioneer LandmarkWeb flow (URL suffix `/LandmarkWeb`, uppercase W):

```
GET  /LandmarkWeb/Home/Index                       (establishes session)
POST /LandmarkWeb/Search/SetDisclaimer             (X-Requested-With: XMLHttpRequest; accepts terms)
POST /LandmarkWeb/Search/RecordDateSearch          (form-encoded: beginDate, endDate, doctype, recordCount, ...)
POST /LandmarkWeb/Search/GetSearchResults          (DataTables pagination -- draw, start, length)
```

Doc-type filter: empty string returns all types; downstream filtering in `processors/` keeps conveyance docs only. Expected page size = 500 (inherited from `LandmarkSession.page_size`).

## 4. Field Inventory

Pioneer LandmarkWeb DataTables return (pre-normalization via `DEFAULT_COLUMN_MAP`):

| Logical field | Column |
|---------------|--------|
| Grantor (Direct Name) | 1 |
| Grantee (Reverse Name) | 2 |
| Record Date | 3 |
| Doc Type | 4 |
| Book | 5 |
| Page | 6 |
| Instrument Number | 7 |
| Legal | ~13 (DEFAULT_COLUMN_MAP variant) |

No mortgage-amount column on the deed search -- matches the Madison / general AL pattern. Mortgage cross-ref requires a second session in mortgage search mode (not yet confirmed for Jefferson's LandmarkWeb -- search-type toggling shape is vendor-consistent but the specific doc-type codes for MORT vs. REMORT in Jefferson's indexing standard need verification on first live pull).

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing**. No `cd2:` block in `county-registry.yaml` for Jefferson AL, no `counties.yaml` "Jefferson AL" mapping, no configs entry in `county_scrapers/configs.py` `COUNTYGOV_COUNTIES` or a LandmarkWeb counterpart. The adapter and session client both exist and are reusable -- this is a configuration gap, not a build gap.

Future adapter would extract grantor, grantee, record date, doc type, book/page, instrument number, and legal description via the same shape as Bay County FL. **Non-disclosure state: no sale price. Mortgage cross-ref, if added, would follow the Madison CountyGov pattern conceptually (same-day last-name match) though LandmarkWeb's mortgage search returns different column names than Kendo Grid.**

## 6. Auth Posture / Bypass Method

No named account. Session handshake only: GET Home -> POST disclaimer (sets cookie) -> search endpoints unlocked. Identical to Bay County FL. `captcha_hybrid` here is a misnomer -- no captcha is actually served, just a terms-agreement AJAX POST.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Grantor | NO (no CD2 config) |
| Grantee | NO |
| Record date | NO |
| Doc type | NO |
| Book/page | NO |
| Instrument | NO |
| Legal | NO |
| Mortgage amount | NO (requires second session) |
| Consideration | NOT PRESENT (non-disclosure) |
| Document image | NO (would require pay-per-view) |

## 8. Known Limitations and Quirks

- **Dual division: Birmingham + Bessemer.** Top-line quirk; both offices file deeds separately. Aggregation behavior in the county-wide LandmarkWeb index needs confirmation on first live pull. The ArcGIS `Division` field on parcels carries the split and may be useful for downstream reconciliation.
- URL suffix is `/LandmarkWeb` (uppercase W). Sibling FL deployments use `/Recording` or other suffixes per-county; Jefferson's is the product's default.
- Non-disclosure state: no sale price. Mortgage cross-ref is the 40%-ish price proxy per `AL-ONBOARDING.md`; needs per-county doc-type code confirmation here.
- Version 1.5.103 -- this is Pioneer's "current" line (as of probe), no extended-legal-column quirks reported for this vintage.
- The WordPress companion site `jeffcoprobatecourt.com` is a brochure; **do not** scrape it for records -- it links out to LandmarkWeb.
- `L L C` entity-name spacing applies (AL assessor data convention).
- `AL-ONBOARDING.md` L283 confirms Jefferson's deed portal was un-investigated when that doc was written; this map is the first CD2-side inventory pass.

Source of truth: `county-registry.yaml` (jefferson-al L571-583, BI-only), `AL-ONBOARDING.md`, `docs/api-maps/bay-county-landmark.md` (vendor reference), live probe `https://landmarkweb.jccal.org/LandmarkWeb`.
