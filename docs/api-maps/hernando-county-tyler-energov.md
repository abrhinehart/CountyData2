# Hernando County FL -- Tyler EnerGov Civic Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Tyler EnerGov Civic Access |
| Portal URL | `https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice` |
| Protocol | Three-endpoint REST (JSON). No authentication required. |
| Auth | Anonymous |
| Tenant ID | `1` (`"TenantName": "hernandocountyflprod"`, per live probe) |
| Tenant URL | `hernandocountyflprod` |
| Friendly name | `"Hernando County, FL"` |
| Date added | `2025-03-20T19:55:20.327` (per `/api/tenants/gettenantslist`) |
| Adapter base | `modules.permits.scrapers.adapters.tyler_energov.TylerEnerGovAdapter` (inferred) |
| Registry status | `pt: live` per `county-registry.yaml` L181-185 |

## 2. Probe (2026-04-14)

### Tenant init

```
GET https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice/api/tenants/gettenantslist
-> HTTP 200, 1,428 bytes, application/json
```

Live response:

```json
{
  "Result": [{
    "TenantID": 1,
    "TenantName": "hernandocountyflprod",
    "FriendlyTenantName": "Hernando County, FL",
    "TenantDetails": "hernandocountyflprod",
    "DateAdded": "2025-03-20T19:55:20.327",
    "TenantUrl": "hernandocountyflprod",
    "IsActive": true,
    "IsGoogleTranslateEnabled": false,
    "SupportEmail": null,
    "CountryTypeId": 1,
    "ServiceUrl": null,
    ...
  }],
  "Success": true,
  "ErrorMessage": null,
  "StatusCode": 200,
  "BrokenRules": null
}
```

## 3. Query Capabilities

Tyler EnerGov Civic Access uses the standard three-endpoint REST pattern documented for Okeechobee, Marion, and Walton Tyler tenants:

1. **Tenant init** — `GET /api/tenants/gettenantslist` → tenant ID / friendly name / URL slug (verified above).
2. **Search** — `POST /api/cap/search` (or similar, under `/api/`) with a paginated criteria body. Typical criteria shape (per `TylerEnerGovAdapter` base): permit number, date range, module ("Building"), status, address components. Returns paginated row set.
3. **Detail** — per-permit GET using the record ID(s) from step 2.

**Pagination model:** standard page-size + page-number; results include `TotalRecords`. Inter-request delay governed by adapter base.

**Date-range semantics:** search criteria accept `IssueDate` / `ApplicationDate` ranges; adapter typically uses issue date for new-permit sweeps and client-side filters on the returned page.

**No authentication** on search or detail endpoints for a `Civic Access` public tenant.

## 4. Field Inventory (tenant-list envelope)

| Field | Type | Notes |
|-------|------|-------|
| Result | array | Wraps the tenant object(s) |
| Success | bool | `true` on normal response |
| ErrorMessage | string/null | |
| ValidationErrorMessage | string/null | |
| ConcurrencyErrorMessage | string/null | |
| StatusCode | int | HTTP-style 200/4xx |
| BrokenRules | array/null | Tyler validation payload |
| Result[].TenantID | int | `1` for Hernando |
| Result[].TenantName | string | `"hernandocountyflprod"` |
| Result[].FriendlyTenantName | string | `"Hernando County, FL"` |
| Result[].TenantUrl | string | `"hernandocountyflprod"` |
| Result[].IsActive | bool | `true` |
| Result[].DateAdded | ISO datetime | `"2025-03-20T19:55:20.327"` |
| Result[].CountryTypeId | int | `1` (US) |
| Result[].SupportEmail | string/null | `null` |

Per-permit field inventory is not captured in this probe (requires search/detail calls). Compare with Okeechobee and Walton docs — both use the same base adapter and expose `PermitNumber`, `PermitType`, `ApplicationDate`, `IssueDate`, `StatusDescription`, address block, applicant, contractor, valuation, and associated fees.

## 5. What We Extract / What a Future Adapter Would Capture

The `TylerEnerGovAdapter` base class (shared with Okeechobee, Walton, Marion) maps the EnerGov row shape to CountyData2's permit schema:

| Canonical permit field | Tyler source | Notes |
|------------------------|--------------|-------|
| permit_number | PermitNumber | |
| permit_type | PermitType / WorkClass | |
| application_date | ApplicationDate | |
| issue_date | IssueDate | Primary date for bucketing |
| status | StatusDescription | |
| address | SiteAddress / full address block | Composed client-side |
| parcel_id | ParcelNumber | Where present; can be blank on residential |
| applicant | Applicant | |
| contractor | Contractor (with license number) | |
| valuation | Valuation | Dollar amount as double |
| description | Description / WorkDescription | Free text |

Hernando-specific notes: tenant hostname is `hernandocountyfl-energovweb.tylerhost.net` (note the hyphen between `countyfl` and `energovweb`) and the path prefix is `/apps/selfservice`, matching the FL Tyler convention used by Okeechobee and Walton.

## 6. Bypass Method / Auth Posture

Fully anonymous. No token, API key, session cookie, or header ceremony required for the tenant init. Search and detail endpoints expected to be equally open (`Civic Access` defines "public self-service" as its core posture).

No Cloudflare or captcha observed on the probe. Standard `User-Agent` and `Accept: application/json, text/plain, */*` suffice.

## 7. What We Extract vs What's Available

| Data Category | Extracted (planned/current) | Available | Notes |
|---------------|----------------------------|-----------|-------|
| Permit number | YES | YES | PermitNumber |
| Permit type | YES | YES | PermitType |
| Issue date / application date | YES | YES | |
| Status | YES | YES | StatusDescription |
| Address block | YES (composed) | YES | Multiple sub-fields available (house, street, suffix, city, zip) |
| Parcel ID | YES where present | YES | Sparse on residential |
| Applicant | YES | YES | |
| Contractor (name + license) | YES | YES | |
| Valuation | YES | YES | |
| Description / work class | YES | YES | |
| Inspections | NO | YES (separate endpoint) | See `/api/inspections` family on Tyler tenants; typically not scraped |
| Fees | NO | YES (detail page) | Present on per-permit detail |
| Documents / attachments | NO | YES | Attached files on detail record |

## 8. Known Limitations and Quirks

1. **Hostname hyphen pattern.** `hernandocountyfl-energovweb.tylerhost.net` uses a hyphen between `hernandocountyfl` and `energovweb`. Walton matches this pattern (`waltoncountyfl-energovweb.tylerhost.net`). Okeechobee does too (`okeechobeecountyfl-energovweb.tylerhost.net`). Any new Tyler-EnerGov FL onboarding should follow `{county}countyfl-energovweb.tylerhost.net`.
2. **`TenantID = 1` per tenant.** Tyler tenants are single-tenant environments; the `gettenantslist` response always returns exactly one entry. Do not assume multi-tenant discovery.
3. **`TenantUrl` doubles as the internal slug** (`hernandocountyflprod`). Used in some per-tenant URL path segments inside the app; not surfaced by the `gettenantslist` wrapper beyond this property.
4. **`DateAdded: 2025-03-20`.** The Hernando EnerGov tenant is relatively new (March 2025). Any historical data before that date is not available in this portal — historical permits may be stored in a legacy TRAKiT / eTRAKiT shell.
5. **`Success: true` + `StatusCode: 200` is the envelope contract.** Downstream code should key off `Success` / `ErrorMessage`, not HTTP status alone (Tyler returns HTTP 200 with `Success: false` on validation errors).
6. **No robots.txt restriction was observed on the probe.** Still respect the 2s delay convention between requests.
7. **Migration context matches Okeechobee.** Both migrated from TRAKiT to Tyler EnerGov; fields and endpoint paths are identical; this cuts Hernando's adapter down to a single-line URL override of the base.
8. **Search endpoint not re-probed in this run.** `/api/tenants/gettenantslist` confirms platform identity; full criteria/search/detail trio was not hit (would require constructing a valid criteria payload). Behavior is mirrored from the Okeechobee and Walton live experience.
9. **No Google Translate integration.** `IsGoogleTranslateEnabled: false` — the Civic Access UI runs in English only.
10. **Null `SupportEmail`.** Hernando has not populated a support email in the tenant record; contact must come from county staff rather than the portal response.

Source of truth: `county-registry.yaml` L181-185 (`hernando-fl.projects.pt`), live probe of `https://hernandocountyfl-energovweb.tylerhost.net/apps/selfservice/api/tenants/gettenantslist` (2026-04-14, HTTP 200, 1,428 bytes), comparison against `docs/api-maps/okeechobee-county-tyler-energov.md` and `docs/api-maps/walton-county-tyler-energov.md` (shared `TylerEnerGovAdapter` base).
