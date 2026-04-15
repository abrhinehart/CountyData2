# Walton County FL -- Tyler EnerGov Civic Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Tyler EnerGov Civic Access |
| Portal URL | `https://waltoncountyfl-energovweb.tylerhost.net/apps/SelfService` |
| Adapter | `modules.permits.scrapers.adapters.walton_county.WaltonCountyAdapter` |
| Base class | `modules.permits.scrapers.adapters.tyler_energov.TylerEnerGovAdapter` |
| Protocol | Three-endpoint REST (JSON). No authentication required. |
| Auth | Anonymous |
| Tenant ID | `1` (`"TenantName": "EnerGovProd"`, per live `/api/tenants/gettenantslist` 2026-04-14) |
| Registry status | `live` (per `walton-fl.projects.pt`, `county-registry.yaml` L373-377) |

**CRITICAL: The hostname uses a hyphen.** The correct FQDN is `waltoncountyfl-energovweb.tylerhost.net` -- the `waltoncountyfl` and `energovweb` segments are separated by a hyphen. `waltoncountyflenergovweb` (no hyphen) does NOT resolve. This is called out in three independent places in the repo: `county-registry.yaml` L377 ("Hostname uses hyphen (waltoncountyfl-energovweb)"), `modules/permits/data/source_research.json` L225 ("The hostname uses a hyphen"), and `modules/permits/scrapers/adapters/walton_county.py` L9 (the `base_url` literal).

The adapter is a minimal subclass:

```python
# modules/permits/scrapers/adapters/walton_county.py (verbatim)
from __future__ import annotations

from modules.permits.scrapers.adapters.tyler_energov import TylerEnerGovAdapter


class WaltonCountyAdapter(TylerEnerGovAdapter):
    slug = "walton-county"
    display_name = "Walton County"
    base_url = "https://waltoncountyfl-energovweb.tylerhost.net/apps/SelfService"
```

All scraping logic (tenant init, criteria template, paginated search) is inherited.

---

## 2. Three-Endpoint REST Flow

### Endpoint 1: Tenant init

```
GET {base_url}/api/tenants/gettenantslist
Headers:
  User-Agent: Mozilla/5.0 ... Chrome/123.0.0.0 ...
  Accept: application/json, text/plain, */*
  Accept-Language: en-US,en;q=0.9
  Referer: {base_url}/
```

Live response (probed 2026-04-14, HTTP 200, 1373 bytes):

```json
{
  "Result": [{
    "TenantID": 1,
    "TenantName": "EnerGovProd",
    "FriendlyTenantName": "",
    "TenantDetails": "EnerGovProd",
    "DateAdded": "2020-03-04T17:17:42.697",
    "TenantUrl": "home",
    "IsActive": true,
    "IsGoogleTranslateEnabled": false,
    "ArcGisTenantId": 1,
    "UseTylerPayments": false,
    ...
  }],
  "Success": true,
  "StatusCode": 200
}
```

The adapter stores `TenantID` and `TenantName` on the session and adds them as headers on every subsequent request:

```python
session.headers["tenantId"] = "1"
session.headers["tenantName"] = "EnerGovProd"
```

### Endpoint 2: Criteria template

```
GET {base_url}/api/energov/search/criteria
Headers: (same + tenantId + tenantName)
```

Live response (probed 2026-04-14, HTTP 200, 7533 bytes):

```
Result keys: Keyword, ExactMatch, SearchModule, FilterModule, SearchMainAddress,
             PlanCriteria, PermitCriteria, InspectionCriteria, CodeCaseCriteria,
             RequestCriteria, BusinessLicenseCriteria, ProfessionalLicenseCriteria,
             LicenseCriteria, ProjectCriteria, PlanSortList

PermitCriteria keys: PermitNumber, PermitTypeId, PermitWorkclassId, PermitStatusId,
             ProjectName, IssueDateFrom, IssueDateTo, Address, Description,
             ExpireDateFrom, ExpireDateTo, FinalDateFrom, FinalDateTo,
             ApplyDateFrom, ApplyDateTo, SearchMainAddress, ContactId, TypeId,
             WorkClassIds, ParcelNumber, ...
```

The adapter caches this template as `self._criteria_template` and deep-copies it before each search.

### Endpoint 3: Paginated search

```
POST {base_url}/api/energov/search/search
Headers: (same)
Body: deepcopy(self._criteria_template) with overrides:
  SearchModule: 1
  FilterModule: 2
  PageNumber: {page}
  PageSize: 100
  SortBy: "IssueDate"
  SortAscending: false
  PermitCriteria.IssueDateFrom: "MM/DD/YYYY"
  PermitCriteria.IssueDateTo:   "MM/DD/YYYY"
  PermitCriteria.PageNumber: {page}
  PermitCriteria.PageSize: 100
  PermitCriteria.SortBy: "IssueDate"
  PermitCriteria.SortAscending: false
```

### Response shape

```json
{
  "Result": {
    "EntityResults": [ /* permit entity objects */ ],
    "TotalPages": N
  }
}
```

Per-entity mapping (from `_map_entity_to_permit`):

| Field | Maps to |
|-------|---------|
| `CaseNumber` | `permit_number` |
| `AddressDisplay` | `address` |
| `MainParcel` | `parcel_id` |
| `IssueDate` | `issue_date` (first 10 chars of `YYYY-MM-DDTHH:MM:SS`) |
| `CaseStatus` | `status` |
| `CaseType` | `permit_type` |
| `ProjectName` | `raw_subdivision_name` |

---

## 3. Search Capabilities

Inherits from `TylerEnerGovAdapter`:

- `bootstrap_lookback_days = 120`
- `rolling_overlap_days = 14`
- `page_size = 100`
- `max_pages = 200`
- `sleep_between_pages = 0.25s`
- Residential type terms: `residential, new single family, new construction, new dwelling, single family, sfr, sfd`
- Excluded type terms: `demolition, demo , sign, pool, solar, roof, reroof, mechanical, electrical, plumbing, fence, dock, temp, temporary`

Results are sorted `IssueDate desc`; adapter stops on `saw_before_start` (a page contains a permit whose `IssueDate < start_date`).

Server may not honor the date range reliably; the adapter always applies a client-side `issue_date` filter.

---

## 4. Entity / Permit Fields (extracted)

| Output Field | Source | Notes |
|--------------|--------|-------|
| `permit_number` | `CaseNumber` | |
| `address` | `AddressDisplay` | Tyler's pre-joined address string |
| `parcel_id` | `MainParcel` | |
| `issue_date` | `IssueDate[:10]` | ISO `YYYY-MM-DD` |
| `status` | `CaseStatus` | |
| `permit_type` | `CaseType` | Used for type filtering |
| `valuation` | -- | Always `None` |
| `raw_subdivision_name` | `ProjectName` | Nullable |
| `raw_contractor_name` | -- | `None` |
| `raw_applicant_name` | -- | `None` |
| `raw_licensed_professional_name` | -- | `None` |
| `latitude` | -- | `None` |
| `longitude` | -- | `None` |

Fields visible in Tyler but NOT extracted: `CaseId`, `CaseTypeId`, `CaseStatusId`, `CaseWorkclassId`, `ApplyDate`, `ExpireDate`, `FinalDate`, structured `Address` object, `ContactName`, `ContactEmail`, `Valuation`, `SquareFootage`, `LicensedProfessional`, `Description`, `Jurisdiction`.

---

## 5. Diff vs Okeechobee Tyler EnerGov (closest peer)

Both subclass `TylerEnerGovAdapter`; only the base URL differs.

| Attribute | Walton | Okeechobee |
|-----------|--------|------------|
| Adapter class | `WaltonCountyAdapter` | `OkeechobeeAdapter` |
| Module path | `modules.permits.scrapers.adapters.walton_county` | `modules.permits.scrapers.adapters.okeechobee` |
| Base URL | `waltoncountyfl-energovweb.tylerhost.net/apps/SelfService` | `okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice` |
| `SelfService` case | **Capital S in `SelfService`** | Lowercase `selfservice` |
| TenantID | 1 | 1 |
| TenantName | `EnerGovProd` | `okeechobeecountyflprod` |
| DateAdded (tenant) | 2020-03-04 | 2024-05-16 |
| Status | `live` | `live` |

The key structural difference from Okeechobee is the `apps/SelfService` case -- Walton uses CamelCase (`SelfService`), Okeechobee lowercase (`selfservice`). Both paths resolve because tylerhost.net serves case-insensitive path routing, but keeping the canonical case in the adapter avoids subtle caching / referrer issues.

---

## 6. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Permit Number | YES | `CaseNumber` | Internal case ID (UUID) | `CaseId` |
| Address | YES | `AddressDisplay` | Structured components | `Address.*` |
| Parcel | YES | `MainParcel` | All linked parcels | `Parcels[]` |
| Issue Date | YES | `IssueDate` | Apply/expire/final/hold/complete dates | Various |
| Status | YES | `CaseStatus` | Status ID, workflow stage | `CaseStatusId`, workflow endpoint |
| Permit Type | YES | `CaseType` | Type ID, workclass | `CaseTypeId`, `CaseWorkclassId` |
| Project Name | YES | `ProjectName` | -- | -- |
| Valuation | NO (always null) | -- | `Valuation` when populated | Case detail endpoint |
| Square Footage | NO | -- | `SquareFootage` | Case detail |
| Contractor | NO | -- | `LicensedProfessional` object | Case detail |
| Applicant | NO | -- | `ContactName`, `ContactEmail`, `ContactPhone` | Case detail |
| Description | NO | -- | Free-text description | `Description` |
| Inspections | NO | -- | Full inspection list | Inspections endpoint |
| Fees | NO | -- | Fee line items | Fees endpoint |
| Documents | NO | -- | Attachments | Attachments endpoint |
| Coordinates | NO (always null) | -- | Possibly in `Address` | Case detail |

---

## 7. Unused / Additional Endpoints

| Endpoint | Used? |
|----------|-------|
| `GET /api/energov/case/{caseId}` | NO |
| `GET /api/energov/case/{caseId}/contacts` | NO |
| `GET /api/energov/case/{caseId}/fees` | NO |
| `GET /api/energov/case/{caseId}/inspections` | NO |
| `GET /api/energov/case/{caseId}/attachments` | NO |
| `GET /api/energov/case/{caseId}/workflow` | NO |
| `GET /api/energov/plan/{planId}` | NO |
| `GET /api/energov/inspections/schedule` | NO |
| `GET /api/energov/codecase/{id}` | NO |
| `GET /api/energov/businesslicense/{id}` | NO |

---

## 8. Known Limitations and Quirks

1. **Hostname uses a hyphen: `waltoncountyfl-energovweb`.** Not `waltoncountyflenergovweb` (no hyphen) and not `waltoncountyfl.energovweb` (with dot). Typos that drop the hyphen fail DNS resolution. The hyphen is called out verbatim in `county-registry.yaml` L377, `modules/permits/data/source_research.json` L225, and the `WaltonCountyAdapter.base_url` literal.

2. **`SelfService` (CamelCase) in the URL path.** Walton's canonical URL uses capital `S`: `/apps/SelfService`. Okeechobee uses lowercase `/apps/selfservice`. Both resolve (case-insensitive routing at tylerhost.net), but preserving case keeps the adapter consistent with `jurisdiction_registry.json` L57 and `source_research.json` L211.

3. **TenantName is a generic `EnerGovProd`.** Unlike Okeechobee's `okeechobeecountyflprod`, Walton's tenant name is the generic template `EnerGovProd`. This is a Tyler deployment artifact -- older EnerGov tenants often use the generic name, while newer ones use a county-prefixed one. Do NOT hardcode the tenant name -- the adapter dynamically pulls it from the tenants list.

4. **Tenant was added 2020-03-04** (older than most). Pre-dates many recent Tyler EnerGov deployments. Any schema drift from newer tenants to this tenant may exist (though the three-endpoint flow has been stable).

5. **Server may not honor the date range reliably.** Client-side `issue_date` filter is required. This is consistent across Tyler EnerGov tenants.

6. **Valuation is always null.** Not returned in search response; would need per-case detail fetches.

7. **Contractor / applicant / coordinates always null.** Hardcoded `None`s in `_map_entity_to_permit`. Per-case detail endpoint is not visited.

8. **Page size capped at 100; max 200 pages.** Max 20,000 permits per sweep before hitting the safety cap.

9. **0.25s inter-page delay** is fast (Tyler public API is lenient).

10. **Minimal subclass.** `WaltonCountyAdapter` has only 3 class attributes (`slug`, `display_name`, `base_url`). All logic is inherited. This is the cleanest possible Tyler EnerGov onboarding in this repo.

11. **`live-tyler-energov-adapter` status** per `source_research.json` L214. "Walton County uses the same Tyler EnerGov Civic Access portal pattern." Confirmed live.

12. **No YAML config analog.** Unlike the CR commission YAMLs, permit adapters are Python classes, not YAML. Registration happens via `modules/permits/data/jurisdiction_registry.json` L53-59.

**Source of truth:** `modules/permits/scrapers/adapters/walton_county.py` (lines 1-9), `modules/permits/scrapers/adapters/tyler_energov.py` (base class), `modules/permits/data/jurisdiction_registry.json` L53-59, `modules/permits/data/source_research.json` L208-233, `county-registry.yaml` (`walton-fl.projects.pt`, L373-377), live probes 2026-04-14 against `/api/tenants/gettenantslist` (HTTP 200, TenantID 1, TenantName `EnerGovProd`) and `/api/energov/search/criteria` (HTTP 200, 7.5 KB).
