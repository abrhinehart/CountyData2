# Marion County FL -- Tyler EnerGov Civic Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Tyler EnerGov Civic Access (custom-domain deployment) |
| Portal URL | `https://selfservice.marionfl.org/energov_prod/selfservice` |
| Protocol | Three-endpoint REST (JSON). No authentication required. |
| Auth | Anonymous |
| Tenant ID | `1` (`"TenantName": "Marion County EnerGov_Prod"`, per live probe) |
| Tenant URL slug | `home` |
| Friendly name | `"MCBCC Civic Access"` |
| Date added | `2021-11-11T10:04:02.597` |
| Adapter base | `modules.permits.scrapers.adapters.tyler_energov.TylerEnerGovAdapter` (inferred) |
| Registry status | `pt: live` per `county-registry.yaml` L206-210 |
| Registry note | "Tyler EnerGov Civic Access portal. Custom domain (selfservice.marionfl.org). Public REST API, no auth." |

## 2. Probe (2026-04-14)

```
GET https://selfservice.marionfl.org/energov_prod/selfservice/api/tenants/gettenantslist
-> HTTP 200, 381,403 bytes, application/json
```

Live response (head):

```json
{
  "Result": [{
    "TenantID": 1,
    "TenantName": "Marion County EnerGov_Prod",
    "FriendlyTenantName": "MCBCC Civic Access",
    "TenantDetails": "home",
    "DateAdded": "2021-11-11T10:04:02.597",
    "TenantUrl": "home",
    "IsActive": true,
    "IsGoogleTranslateEnabled": false,
    "SupportEmail": "",
    "CountryTypeId": 1,
    ...
    "TenantFavicon": "data:image/png;base64,iVBORw0KGgoAAAAN..."
  }],
  "Success": true,
  "ErrorMessage": null,
  "StatusCode": 200,
  "BrokenRules": null
}
```

Response body is large (~381 KB) because the tenant record embeds a base64-encoded favicon PNG.

## 3. Query Capabilities

Standard three-endpoint REST flow shared with other Tyler EnerGov FL tenants (Hernando, Okeechobee, Walton):

1. **Tenant init** — `GET /api/tenants/gettenantslist` → confirmed above.
2. **Search** — `POST /api/cap/...` with paginated criteria (permit number, date range, module, status). Returns rows + `TotalRecords`.
3. **Detail** — per-permit GET by record ID.

**Pagination:** page-size + page-number. **Date-range:** via search criteria. **Auth:** anonymous on all three.

## 4. Field Inventory (tenant envelope)

| Field | Type | Notes |
|-------|------|-------|
| Result | array | One element (single-tenant) |
| Success | bool | `true` on normal response |
| ErrorMessage / ValidationErrorMessage / ConcurrencyErrorMessage | string/null | |
| StatusCode | int | |
| BrokenRules | array/null | |
| Result[].TenantID | int | `1` |
| Result[].TenantName | string | `"Marion County EnerGov_Prod"` — note trailing `_Prod` suffix unique to Marion |
| Result[].FriendlyTenantName | string | `"MCBCC Civic Access"` — "MCBCC" = Marion County Board of County Commissioners |
| Result[].TenantUrl / Result[].TenantDetails | string | Both `"home"` (unusual — most tenants repeat the slug) |
| Result[].IsActive | bool | `true` |
| Result[].DateAdded | ISO datetime | `"2021-11-11T10:04:02.597"` — Marion has been on Tyler EnerGov since late 2021 |
| Result[].TenantFavicon | data URL | Base64 PNG, ~380 KB of the envelope |
| Result[].SupportEmail | string | `""` (empty string, not null) |

Per-permit row fields are not captured in this probe. Per the shared base adapter contract (mirrored from Okeechobee / Hernando / Walton): `PermitNumber`, `PermitType`, `WorkClass`, `ApplicationDate`, `IssueDate`, `StatusDescription`, address block, `ParcelNumber`, `Applicant`, `Contractor`, `Valuation`, `Description`.

## 5. What We Extract / What a Future Adapter Would Capture

Same canonical mapping as other Tyler EnerGov FL tenants:

| Canonical permit field | Tyler source | Notes |
|------------------------|--------------|-------|
| permit_number | PermitNumber | |
| permit_type | PermitType / WorkClass | |
| application_date | ApplicationDate | |
| issue_date | IssueDate | Primary bucketing date |
| status | StatusDescription | |
| address | SiteAddress (composed) | Granular components also available |
| parcel_id | ParcelNumber | Often sparse on residential |
| applicant | Applicant | |
| contractor | Contractor (name + license) | |
| valuation | Valuation | Double |
| description | Description / WorkDescription | Free text |

## 6. Bypass Method / Auth Posture

Anonymous — no token, no login, no captcha. Standard `User-Agent` and `Accept: application/json, text/plain, */*` suffice.

No Cloudflare on the custom domain (`selfservice.marionfl.org`).

## 7. What We Extract vs What's Available

| Data Category | Extracted (planned/current) | Available | Notes |
|---------------|----------------------------|-----------|-------|
| Permit number | YES | YES | PermitNumber |
| Permit type / work class | YES | YES | |
| Dates (application, issue) | YES | YES | |
| Status | YES | YES | |
| Address block | YES (composed) | YES | |
| Parcel ID | YES | YES | Sparse on residential |
| Applicant | YES | YES | |
| Contractor | YES | YES | |
| Valuation | YES | YES | |
| Description | YES | YES | |
| Inspections | NO | YES (separate endpoint) | Not scraped |
| Fees | NO | YES (detail page) | |
| Attachments | NO | YES | |

## 8. Known Limitations and Quirks

1. **Custom domain (`selfservice.marionfl.org`).** Unique among the 6 counties in this batch. Other FL Tyler EnerGov deployments use the `{county}countyfl-energovweb.tylerhost.net` pattern; Marion's Clerk/IT published it under a county-owned subdomain. DNS resolves to Tyler's infra (unverified) but from the client POV it's just a different hostname.
2. **Path includes `/energov_prod/` segment.** The URL template is `https://selfservice.marionfl.org/energov_prod/selfservice/api/...` — this is Marion's Tyler instance slug embedded in the path. Other tenants omit this prefix.
3. **`TenantName` includes a trailing `_Prod`.** `"Marion County EnerGov_Prod"` — the production-environment marker is part of the internal tenant name, unique to Marion.
4. **`TenantUrl = "home"` + `TenantDetails = "home"`.** Most tenants repeat a county slug here; Marion uses the literal string `"home"`, suggesting the tenant slug is derived from the URL path rather than the internal label.
5. **Favicon embedded as data URL inflates envelope.** The `/gettenantslist` response is 381 KB because the tenant favicon is inlined. Downstream code should NOT attempt to re-fetch the favicon; it's already in the envelope.
6. **`SupportEmail = ""`** (empty string, not null). A null vs. empty-string difference if downstream logic checks support-email presence.
7. **Legacy Marion system migration.** Date added 2021-11-11 means Marion has four years of permit history in the Civic Access portal. Older history may be in archived legacy format (not verified).
8. **`MCBCC` = Marion County Board of County Commissioners.** The `FriendlyTenantName` choice is a county-internal initialism, not a generic "Marion County" label — relevant if a future UI surfaces the friendly name to end users.
9. **Same envelope contract as other Tyler tenants.** `Success` / `StatusCode` / `ErrorMessage` — key off these, not HTTP status alone.
10. **Per-permit search/detail endpoints not re-probed in this run.** `/api/tenants/gettenantslist` confirms platform identity; the full search/detail round-trip is inherited from the base `TylerEnerGovAdapter` behavior verified on peer tenants.

Source of truth: `county-registry.yaml` L206-210 (`marion-fl.projects.pt`), live probe of `https://selfservice.marionfl.org/energov_prod/selfservice/api/tenants/gettenantslist` (2026-04-14, HTTP 200, 381,403 bytes), cross-reference with `docs/api-maps/walton-county-tyler-energov.md` and `docs/api-maps/okeechobee-county-tyler-energov.md` (shared `TylerEnerGovAdapter` base).
