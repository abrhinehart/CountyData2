# Okeechobee County FL -- Tyler EnerGov Civic Access API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | Tyler EnerGov Civic Access |
| Portal URL | `https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice` |
| Adapter | `modules.permits.scrapers.adapters.okeechobee.OkeechobeeAdapter` |
| Base class | `modules.permits.scrapers.adapters.tyler_energov.TylerEnerGovAdapter` |
| Protocol | Three-endpoint REST (JSON). No authentication required. |
| Auth | Anonymous |
| Migration | Migrated from TRAKiT / eTRAKiT to Tyler EnerGov in June 2025 |
| Tenant ID | `1` (`"TenantName": "okeechobeecountyflprod"`, per live `/api/tenants/gettenantslist`) |

The adapter is a minimal subclass of `TylerEnerGovAdapter`, overriding only the base URL:

```python
class OkeechobeeAdapter(TylerEnerGovAdapter):
    slug = "okeechobee"
    display_name = "Okeechobee County"
    base_url = "https://okeechobeecountyfl-energovweb.tylerhost.net/apps/selfservice"
```

All scraping logic (tenant init, criteria template, paginated search) is inherited from the base.

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

Live response (probed 2026-04-14):

```json
{
  "Result": [{
    "TenantID": 1,
    "TenantName": "okeechobeecountyflprod",
    "FriendlyTenantName": "okeechobeecountyflprod",
    "TenantDetails": "okeechobeecountyflprod",
    "DateAdded": "2024-05-16T15:49:21.603",
    "TenantUrl": "okeechobeecountyflprod",
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
session.headers["tenantName"] = "okeechobeecountyflprod"
```

### Endpoint 2: Criteria template

```
GET {base_url}/api/energov/search/criteria
Headers: (same + tenantId + tenantName)
```

Live response (probed 2026-04-14, excerpted):

```json
{
  "Result": {
    "Keyword": "",
    "ExactMatch": false,
    "SearchModule": 1,
    "FilterModule": 0,
    "SearchMainAddress": false,
    "PlanCriteria": { ... },
    "PermitCriteria": {
      "PermitNumber": null,
      "PermitTypeId": null,
      "PermitWorkclassId": null,
      "PermitStatusId": null,
      "ProjectName": null,
      "IssueDateFrom": null,
      "IssueDateTo": null,
      "Address": null,
      "Description": null,
      ...
      "PageNumber": 0,
      "PageSize": 0,
      "SortBy": null,
      "SortAscending": false
    },
    "InspectionCriteria": { ... },
    "CodeCaseCriteria": { ... },
    "RequestCriteria": { ... },
    "BusinessLicenseCriteria": { ... }
  }
}
```

The adapter caches this template as `self._criteria_template` and deep-copies it before each search (see `_build_search_body`).

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

Per-entity structure (from `_map_entity_to_permit`):

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

### Date-range sweep (the adapter's primary mode)

```python
end_date = end_date or date.today()
start_date = start_date or (end_date - timedelta(days=14))   # rolling_overlap_days
```

Bootstrap mode uses `bootstrap_lookback_days = 120`. Rolling mode uses `rolling_overlap_days = 14`.

Pages are requested sequentially. The adapter stops when:
- `page >= total_pages`, OR
- `page >= max_pages = 200`, OR
- A page contains a permit whose `IssueDate < start_date` (sorted desc by IssueDate, so this indicates the window is exhausted).

`sleep_between_pages = 0.25s` between pages.

### Client-side type filter

Residential terms (at least one must match):
```
residential, new single family, new construction, new dwelling, single family, sfr, sfd
```

Excluded terms (skip if any match):
```
demolition, demo , sign, pool, solar, roof, reroof, mechanical, electrical, plumbing,
fence, dock, temp, temporary
```

Matching is case-insensitive, applied to `CaseType` (the permit type text from Tyler).

### Client-side date filter

The server may not honor the date range reliably; the adapter re-filters each returned permit:

```python
if issue < start_iso: saw_before_start = True; continue
if issue > end_iso:   continue
```

Permits without an `IssueDate` (submitted but not issued) are skipped.

---

## 4. Entity / Permit Fields

### Extracted fields per permit

| Output Field | Source | Notes |
|--------------|--------|-------|
| `permit_number` | `CaseNumber` | |
| `address` | `AddressDisplay` | Tyler's pre-joined address string |
| `parcel_id` | `MainParcel` | Primary parcel linked to the case |
| `issue_date` | `IssueDate[:10]` | ISO `YYYY-MM-DD` |
| `status` | `CaseStatus` | e.g., "Issued", "Finaled" |
| `permit_type` | `CaseType` | Used for type filtering |
| `valuation` | -- | Always `None` (valuation not returned in search response) |
| `raw_subdivision_name` | `ProjectName` | Nullable |
| `raw_contractor_name` | -- | Always `None` |
| `raw_applicant_name` | -- | Always `None` |
| `raw_licensed_professional_name` | -- | Always `None` |
| `latitude` | -- | Always `None` |
| `longitude` | -- | Always `None` |

### Fields visible in Tyler but NOT extracted

The Tyler search response contains far more fields than the adapter consumes. Typical additional fields on `EntityResults` items include:
- `CaseId` (numeric UUID)
- `CaseTypeId`, `CaseStatusId`, `CaseWorkclassId`
- `ApplyDate`, `ExpireDate`, `FinalDate`, `HoldDate`, `CompleteDate`
- `Address` object (structured: StreetNumber, StreetName, etc.)
- `ContactName`, `ContactEmail`, `ContactPhone`
- `Valuation` (sometimes), `SquareFootage`
- `LicensedProfessional` object
- `Description` (free text)
- `Jurisdiction`

---

## 5. What We Extract

Emitted permit dict per `_map_entity_to_permit`:

```python
{
    "permit_number": entity.get("CaseNumber"),
    "address": entity.get("AddressDisplay"),
    "parcel_id": entity.get("MainParcel"),
    "issue_date": _parse_api_date(entity.get("IssueDate")),
    "status": entity.get("CaseStatus"),
    "permit_type": entity.get("CaseType"),
    "valuation": None,
    "raw_subdivision_name": project_name,
    "raw_contractor_name": None,
    "raw_applicant_name": None,
    "raw_licensed_professional_name": None,
    "latitude": None,
    "longitude": None,
}
```

Only permits passing BOTH the residential type filter AND the client-side date filter are emitted.

---

## 6. Type Filtering

`_is_target_permit_type` combines two lists (see Section 3):

1. If any excluded term is a substring of the lowercased `permit_type`, skip.
2. Otherwise, if any residential term is a substring, keep.
3. Otherwise, skip.

This is an allow-list-after-deny-list; a permit must both avoid exclusion AND include at least one residential term.

---

## 7. Unused / Additional Endpoints

Tyler EnerGov Civic Access exposes many more endpoints the adapter never calls:

| Endpoint | What it returns | Used? |
|----------|-----------------|-------|
| `GET /api/energov/case/{caseId}` | Full case detail | NO |
| `GET /api/energov/case/{caseId}/contacts` | Applicant, contractor, owner | NO |
| `GET /api/energov/case/{caseId}/fees` | Fee line items | NO |
| `GET /api/energov/case/{caseId}/inspections` | Inspection list | NO |
| `GET /api/energov/case/{caseId}/attachments` | Documents | NO |
| `GET /api/energov/case/{caseId}/workflow` | Workflow status | NO |
| `GET /api/energov/plan/{planId}` | Plan review detail | NO (Plans module unused) |
| `GET /api/energov/inspections/schedule` | Inspection scheduling | NO |
| `GET /api/energov/codecase/{id}` | Code enforcement case | NO |
| `GET /api/energov/businesslicense/{id}` | Business license | NO |

The criteria template also exposes `PlanCriteria`, `InspectionCriteria`, `CodeCaseCriteria`, `RequestCriteria`, `BusinessLicenseCriteria` (unused -- see Section 2 excerpted JSON).

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Permit Number | YES | `CaseNumber` | Internal case ID (UUID) | `CaseId` |
| Address | YES | `AddressDisplay` | Structured address components | `Address.*` |
| Parcel | YES | `MainParcel` | All linked parcels (multi-parcel cases) | `Parcels[]` |
| Issue Date | YES | `IssueDate` | Apply, expire, final, hold, complete dates | Various |
| Status | YES | `CaseStatus` | Status ID, workflow stage | `CaseStatusId`, workflow endpoint |
| Permit Type | YES | `CaseType` | Type ID, workclass | `CaseTypeId`, `CaseWorkclassId` |
| Project Name | YES (as subdivision) | `ProjectName` | -- | -- |
| Valuation | NO (always null) | -- | Often present as `Valuation` field | Case detail endpoint |
| Square Footage | NO | -- | `SquareFootage` when populated | Case detail |
| Contractor | NO | -- | `LicensedProfessional` object | Case detail / contacts |
| Applicant | NO | -- | `ContactName`, `ContactEmail`, `ContactPhone` | Case detail / contacts |
| Owner | NO | -- | Present on case detail | Case detail / contacts |
| Description | NO | -- | Free-text work description | `Description` |
| Inspections | NO | -- | Full inspection list | Inspections endpoint |
| Fees | NO | -- | Fee line items | Fees endpoint |
| Documents | NO | -- | Attachments list | Attachments endpoint |
| Workflow | NO | -- | Workflow task status | Workflow endpoint |
| Coordinates | NO (always null) | -- | Possibly in `Address` object | Case detail |

---

## 9. Known Limitations and Quirks

1. **No Polk analog in this repo.** Tyler EnerGov has no counterpart in the Polk County doc set. This template is custom; do NOT try to force it into the Polk-Accela 13-section shape.

2. **Server may not honor the date range.** The adapter always applies a client-side `issue_date` filter in case the Tyler search returns permits outside the requested `IssueDateFrom` / `IssueDateTo`. This is a documented behavior, not a bug.

3. **`saw_before_start` early-exit.** Results are sorted `IssueDate desc`. As soon as a permit with `issue_date < start_date` is seen on a page, the adapter stops pagination (the remaining pages must all be older). This saves a lot of page fetches on wide backfills.

4. **Valuation is always null.** The Tyler search response does not include the permit valuation dollar amount; the adapter sets `valuation: None`. To get valuation, the adapter would need to call the per-case detail endpoint for every permit -- not currently implemented.

5. **No contacts, no inspections, no fees, no documents.** The adapter only calls the search endpoint. Contacts / inspections / fees / documents are each separate endpoints and are NOT visited.

6. **Contractor, applicant, and licensed professional are always null.** Per the hardcoded `None`s in `_map_entity_to_permit`. If downstream code requires a contractor match, alternate data must be used.

7. **Coordinates are always null.** The adapter does not parse the structured `Address` object that may contain lat/lon.

8. **Page size capped at 100.** `PageSize = 100` and `max_pages = 200`, so a single run can return at most 20,000 permits before hitting the safety cap.

9. **0.25s inter-page delay is generous.** Unlike LandmarkWeb (1.0s) or Legistar (0.5s), Tyler's public API is quick. Pagination is fast at 0.25s sleep between pages.

10. **Migrated from TRAKiT June 2025.** Permits applied before the migration date may have reduced detail / different `CaseType` taxonomies. Long backfills should test both pre- and post-migration windows.

11. **Tenant ID is 1.** Single-tenant Tyler instance. The adapter dynamically pulls the tenant ID from `/api/tenants/gettenantslist` rather than hard-coding it, so migrations that renumber the tenant are handled automatically.

12. **Tyler hostname uses hyphenated form `okeechobeecountyfl-energovweb`.** Note the hyphen between `okeechobeecountyfl` and `energovweb`. The registry's `county-registry.yaml` captures this pattern for Walton too. Do NOT use `okeechobeecountyflenergovweb` (no hyphen) -- it does not resolve.

**Source of truth:** `modules/permits/scrapers/adapters/okeechobee.py` (lines 1-9), `modules/permits/scrapers/adapters/tyler_energov.py` (base class, lines 1-246), `modules/permits/data/source_research.json` (key `okeechobee`), `county-registry.yaml` (`okeechobee-fl.projects.pt`), live probes against `/api/tenants/gettenantslist` and `/api/energov/search/criteria`
