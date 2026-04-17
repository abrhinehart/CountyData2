# Madison County AL -- KCS ArcGIS Parcels Layer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Server (KCS / Keet Consulting Services, hosted) |
| Host | `web3.kcsgis.com` |
| Service | `kcsgis/rest/services/Madison/Madison_Public_ISV/MapServer` |
| Layer | Layer 185 -- "Parcels" (sublayer of parent group 180 "Data") |
| Geometry Type | `esriGeometryPolygon` |
| Source Spatial Reference | WKID 102100 / latestWkid 3857 (Web Mercator) |
| Max Record Count | 2000 |
| Auth | Anonymous (no token) |
| Registry entry | `county-registry.yaml` L544-570 (`madison-al.projects.bi`) |
| BI config | `seed_bi_county_config.py` L424-438 |

Madison's parcel layer is served from an ISV-branded ArcGIS Server deployment operated by KCS (a regional GIS vendor). Layer 185 is the assessor parcel polygons; the parent MapServer exposes many sibling layers (ownership, roads, zoning) which are **not** currently consumed by CountyData2.

## 2. Probe (2026-04-14)

```
GET https://web3.kcsgis.com/kcsgis/rest/services/Madison/Madison_Public_ISV/MapServer/185?f=json
-> HTTP 200  (content-type application/json, ~6.7 KB)
```

Field count: 33. `currentVersion` 11.0 (ArcGIS Server). `maxRecordCount` 2000 confirms the page-size cap enforced by `gis_max_records` in the BI config.

The registry-style endpoint (`web3.kcsgis.com/Madison_Public_ISV/MapServer/185?f=json`) returns HTTP 404 from IIS -- the path must include `/kcsgis/rest/services/Madison/` prefix. The short form in `county-registry.yaml` is a cosmetic label, not a callable URL.

## 3. Search / Query Capabilities

Query URL:

```
https://web3.kcsgis.com/kcsgis/rest/services/Madison/Madison_Public_ISV/MapServer/185/query
```

| Parameter | Used? | Value | Notes |
|-----------|-------|-------|-------|
| `where` | YES | `PropertyOwner LIKE '%alias%'` (OR-batched) | SQL WHERE clause against PropertyOwner |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons needed for BI map overlay |
| `outSR` | YES | `4326` | Reproject from Web Mercator (102100) to WGS84 |
| `resultOffset` | YES | 0, 2000, 4000, ... | Pagination cursor |
| `resultRecordCount` | YES | 2000 | Matches service max |
| `f` | YES | `json` | Esri REST JSON response |

Batched-OR owner searches go through `GISQueryEngine`. Millrose Properties (Lennar's land bank) is the single highest-parcel entity on this layer (~1044 parcels per the registry notes).

## 4. Field Inventory

All 33 fields from live `?f=json`:

| Field | Type | Mapped To | Notes |
|-------|------|-----------|-------|
| OBJECTID | OID | -- | Esri object id |
| TaxYear | Integer | -- | |
| PIN | String | -- | Short parcel id |
| PropertyAddress | String | gis_address_field | Situs address |
| ParcelNum | String | gis_parcel_field | Primary parcel number |
| PropertyOwner | String | gis_owner_field | Current owner |
| PreviousOwners | String | gis_previous_owner_field | Prior-owner string (semicolon-delimited) |
| AccountOwner | String | -- | Tax account owner (may differ from legal owner) |
| MailingAddress | String | -- | Owner mailing address |
| TaxDistrict | String | -- | |
| Abstract | String | -- | Abstract book reference |
| ExemptCode | String | -- | Homestead / other exemption |
| TotalLandValue | Double | -- | |
| TotalUseValue | Double | -- | |
| TotalBuildingValue | Double | gis_building_value_field | Primary BI value signal |
| TotalAppraisedValue | Double | gis_appraised_value_field | |
| TotalAssessedValue | Double | -- | |
| Acres | Double | gis_acreage_field | |
| NeighborhoodName | String | -- | |
| SubdivisionCode | String | -- | Numeric code |
| Subdivision | String | gis_subdivision_field | Full name; Millrose / Forestar matched here |
| SubLot | String | -- | |
| SubBlock | String | -- | |
| DeedType | String | -- | WD, TD, QC, etc. |
| DeedBook | String | -- | |
| DeedPage | String | -- | |
| DeedDate | Date | gis_deed_date_field | **Alabama non-disclosure: no sale price** |
| PropertyDescription | String | -- | Free-form legal description |
| OBJECTID_1 | Integer | -- | Duplicate OID artifact |
| ASSESS_NUM | String | -- | |
| Shape | Geometry | -- | |
| Shape.STArea() | Double | -- | |
| Shape.STLength() | Double | -- | |

## 5. What We Extract / What a Future Adapter Would Capture

Currently populated by `seed_bi_county_config.py` for Madison (the 9 fields prefixed `gis_*` above). `gis_use_field` is `None` -- there is no first-class PropertyUse / UseCode column on this layer, which is a gap compared to most FL counties where a `DOR_UC` or `UseCode` field drives zoning classification.

Non-disclosure state: `DeedDate` gives the recording date, but **no sale price is ever present on the deed record in Alabama**. Price is reconstructed downstream via the CountyGov CD2 mortgage cross-reference (see `madison-county-countygov-b2c.md`).

## 6. Auth Posture / Bypass Method

Anonymous. No token, no referer, no disclaimer handshake. CountyData2 sends plain REST GETs. The service does not rate-limit aggressively, but `GISQueryEngine` batches `WHERE` clauses to keep individual queries under the server's URL-length cap.

## 7. What We Extract vs What's Available

| Available in layer | Extracted by BI? |
|--------------------|:----------------:|
| Owner | YES |
| Parcel number | YES |
| Address | YES |
| Acreage | YES |
| Subdivision | YES |
| Deed date | YES |
| Previous owners | YES |
| Building value | YES |
| Appraised value | YES |
| Use / PropertyClass | NO (no such field) |
| Tax year | NO |
| Deed book / page / type | NO |
| Neighborhood | NO |
| Mailing address | NO |
| Exemption code | NO |

## 8. Known Limitations and Quirks

- Registry shorthand endpoint (`web3.kcsgis.com/Madison_Public_ISV/MapServer/185`) is NOT the real URL -- requires `/kcsgis/rest/services/Madison/` prefix. The `seed_bi_county_config.py` copy is canonical.
- No PropertyUse / UseCode field; `gis_use_field` intentionally `None`. Builder-inventory classification relies on owner alias matching alone for Madison.
- "L L C" spaced-out company names in assessor data (see `AL-ONBOARDING.md` L191-205) -- aliases MUST include both `LLC` and `L L C` variants or Millrose/Forestar/DR Horton matches will miss.
- Duplicate `OBJECTID_1` field present alongside `OBJECTID` -- likely a data-pipeline artifact. Ignore the _1 copy.
- Non-disclosure state: `DeedDate` exists but no sale price. See CD2 doc for mortgage cross-ref compensation.

Source of truth: `county-registry.yaml` (madison-al L544-570), `seed_bi_county_config.py` (L424-438), `AL-ONBOARDING.md`, live probe `https://web3.kcsgis.com/kcsgis/rest/services/Madison/Madison_Public_ISV/MapServer/185?f=json`.
