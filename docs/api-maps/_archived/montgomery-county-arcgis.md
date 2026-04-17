# Montgomery County AL -- ArcGIS FeatureServer Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Server (Montgomery County self-hosted) |
| Host | `gis.montgomeryal.gov` |
| Service | `server/rest/services/Parcels/FeatureServer` |
| Layer | Layer 0 -- "DBO.Parcels" |
| Geometry Type | `esriGeometryPolygon` |
| Source Spatial Reference | (not declared on root response; `outSR=4326` works for reprojection) |
| Max Record Count | 2000 |
| Auth | Anonymous (no token) |
| Registry entry | `county-registry.yaml` L600-613 (`montgomery-al.projects.bi`) |
| BI config | `seed_bi_county_config.py` L471-487 |

Montgomery is a state-capital county; the GIS division publishes parcels via a FeatureServer (not MapServer -- same shape, different service variant). 111 DR Horton parcels currently on this layer per registry notes.

## 2. Probe (2026-04-14)

```
GET https://gis.montgomeryal.gov/server/rest/services/Parcels/FeatureServer/0?f=json
-> HTTP 200  (application/json, ~11.8 KB)
```

Field count: 38. `currentVersion` 11.3. `maxRecordCount` 2000. `DBO.Parcels` prefix in the layer name indicates SQL Server-backed origin. Same short-path 404 pattern as Madison / Jefferson -- registry's `gis.montgomeryal.gov/Parcels/FeatureServer/0` short-form is a cosmetic label, actual URL requires the `server/rest/services/` path.

## 3. Search / Query Capabilities

Query URL:

```
https://gis.montgomeryal.gov/server/rest/services/Parcels/FeatureServer/0/query
```

| Parameter | Used? | Value | Notes |
|-----------|-------|-------|-------|
| `where` | YES | `OwnerName LIKE '%alias%'` (OR-batched) | Mixed-case OwnerName |
| `outFields` | YES | `*` | |
| `returnGeometry` | YES | `true` | |
| `outSR` | YES | `4326` | |
| `resultOffset` | YES | Paginated | |
| `resultRecordCount` | YES | 2000 | |
| `f` | YES | `json` | |

## 4. Field Inventory

All 38 fields from live `?f=json`:

| Field | Type | Mapped To | Notes |
|-------|------|-----------|-------|
| OBJECTID | OID | -- | |
| ParcelNo | String | gis_parcel_field | |
| Calc_Acre | Double | gis_acreage_field | |
| RecordYear | Integer | -- | |
| OwnerName | String | gis_owner_field | Primary owner |
| OwnerName2 | String | -- | Co-owner |
| MailAddress1, MailAddress2, MailCity, MailState, MailZip | String | -- | Owner mailing |
| Neighborhood | String | -- | |
| AssessmentClass | String | gis_use_field | |
| SubDiv1 | String | gis_subdivision_field | Primary subdivision |
| SubDiv2 | String | -- | Secondary (joint / overlay) |
| Book1, Book2, Page1, Page2 | String | -- | Dual book/page -- unusual pattern |
| Lot1, Lot2, Block1, Block2 | String | -- | Dual lot/block |
| MunicipalityCode | String | -- | |
| PropertyAddr1 | String | -- | Situs address (gis_address_field but note: field not currently mapped explicitly in `seed_bi_county_config.py`) |
| PropertyCity, PropertyState, PropertyZip | String | -- | |
| ForestAcreage | Double | -- | Current-use timber assessment |
| TotalLandValue | Double | -- | |
| TotalImpValue | Double | gis_building_value_field | |
| TotalValue | Double | gis_appraised_value_field | |
| PID | String | -- | |
| FireDist | String | -- | |
| InstNbr | String | -- | Instrument number of latest deed |
| InstDate | Date | gis_deed_date_field | Latest deed recording date |
| Shape__Area | Double | -- | |
| Shape__Length | Double | -- | |

Note: the live layer includes `Shape__Area` / `Shape__Length` (ArcGIS 10.9+ style, not the older `Shape.STArea()` / `Shape.STLength()` Madison/Jefferson flavors).

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted per `seed_bi_county_config.py` L471-487:

- `OwnerName`, `ParcelNo`, `PropertyAddr1` (address field), `AssessmentClass`, `Calc_Acre`, `SubDiv1`, `TotalImpValue`, `TotalValue`, `InstDate`.
- **No previous-owner field** (`gis_previous_owner_field` = `None`).

**Non-disclosure state**: `InstDate` gives the latest recording date, but no sale price. The dual Book/Page/Lot/Block columns suggest a historical-records design where secondary legal descriptions can be attached -- not currently consumed.

## 6. Auth Posture / Bypass Method

Anonymous. No token. No referer / CORS gating observed.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| OwnerName | YES |
| OwnerName2 (co-owner) | NO |
| Parcel | YES |
| PropertyAddr1 | YES |
| Mailing address | NO |
| Assessment class | YES |
| Calc_Acre | YES |
| Forest acreage | NO |
| Subdivision 1 | YES |
| Subdivision 2 | NO |
| Book/Page 1 and 2 | NO |
| Lot/Block 1 and 2 | NO |
| Total imp / total / land values | 2 of 3 (land NO) |
| Neighborhood | NO |
| MunicipalityCode | NO |
| InstNbr | NO |
| InstDate | YES |
| Record year | NO |

## 8. Known Limitations and Quirks

- Registry shorthand endpoint isn't the real URL. Use the full path from `seed_bi_county_config.py`.
- **Dual Book/Page/Lot/Block/OwnerName/SubDiv columns** (`*1` and `*2`) -- Montgomery's data model supports two concurrent legal descriptions per parcel. BI currently only uses the `*1` forms.
- **No previous-owner field** -- owner-chain history is not available from this layer alone. Deed-side CD2 integration (Ingenuity probate portal) is required for that.
- `Shape__Area` / `Shape__Length` style instead of `Shape.STArea()` -- adapter code that normalizes across counties must handle both.
- Non-disclosure state (no sale price). `L L C` spacing applies.
- Montgomery is AL's state capital; BI field shape is closer to Madison's (normal ESRI layer) than Baldwin's (usrsvcs-proxied token layer) or Jefferson's (77-field super-wide layer).

Source of truth: `county-registry.yaml` (montgomery-al L600-613), `seed_bi_county_config.py` (L471-487), `AL-ONBOARDING.md`, live probe `https://gis.montgomeryal.gov/server/rest/services/Parcels/FeatureServer/0?f=json`.
