# Okeechobee County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Tyler Technologies-hosted tenant) |
| Endpoint | `https://services3.arcgis.com/jE4lvuOFtdtz6Lbl/arcgis/rest/services/Tyler_Technologies_Display_Map/FeatureServer/2` |
| Layer Name | Parcels (ID 2) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | ParcelID |
| ObjectId Field | OBJECTID |
| Global ID Field | GlobalID |
| Service description | "This service is for Okeechobee County's Tyler Technology permitting system. This data contains parcel and address point information to be updated on a monthly basis." |
| Capabilities | `Query,Extract,Sync` |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Okeechobee field mapping (from `seed_bi_county_config.py`)

| Purpose | Okeechobee Field |
|---------|------------------|
| Owner | `Owner1` |
| Parcel | `ParcelID` |
| Address | `StreetName` |
| Use | (none configured) |
| Acreage | `Acerage` |

**The source schema has the typo `Acerage` (sic), not `Acreage`.** This typo is preserved verbatim in the seeded config; do NOT "correct" it -- the field name in the actual ArcGIS layer is literally `Acerage`, and changing the config causes queries to fail.

---

## 2. Other Layers at FeatureServer Root

The Tyler_Technologies_Display_Map service hosts 18 layers (0-17):

| ID | Name | Geometry Type |
|----|------|---------------|
| 0 | Okeechobee County Boundary | esriGeometryPolygon |
| 1 | Address Points | esriGeometryPoint |
| **2** | **Parcels** | **esriGeometryPolygon (target)** |
| 3 | Fire Hydrants | esriGeometryPoint |
| 4 | Water Management Districts | esriGeometryPolygon |
| 5 | Commission_Districts | esriGeometryPolygon |
| 6 | Electric Service Areas | esriGeometryPolygon |
| 7 | FEMA Flood Zones | esriGeometryPolygon |
| 8 | Future Land Use | esriGeometryPolygon |
| 9 | Zoning | esriGeometryPolygon |
| 10 | Opportunity Zones | esriGeometryPolygon |
| 11 | Okeechobee City Limits | esriGeometryPolygon |
| 12 | Spatial_Collections_Point | esriGeometryPoint |
| 13 | Spatial_Collections_Lines | esriGeometryPolyline |
| 14 | Spatial_Collections_Polygons | esriGeometryPolygon |
| 15 | History_Writer_Points | esriGeometryPoint |
| 16 | History_Writer_Lines | esriGeometryPolyline |
| 17 | History_Writer_Polygons | esriGeometryPolygon |

---

## 3. Query Capabilities

Base query URL:

```
https://services3.arcgis.com/jE4lvuOFtdtz6Lbl/arcgis/rest/services/Tyler_Technologies_Display_Map/FeatureServer/2/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `Owner1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |
| `returnCountOnly` | NO | -- | -- |

### Advanced capabilities (per service metadata)

- Pagination, full-text search, spatial aggregation (Envelope, Centroid, ConvexHull)
- Percentile stats, HAVING clause, true curves
- Query with distance / datum transformation
- Query bins (date, interval, classification)

---

## 4. Field Inventory

Complete field catalog from the live `?f=json` response (27 fields including OBJECTID, GlobalID, and Shape):

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| OBJECTID | OID | OBJECTID | NO | -- |
| ParcelID | String | ParcelID | **YES** | `parcel_number` |
| StreetPredirection | String | StreetPredirection | NO | -- |
| StreetNumber | String | StreetNumber | NO | -- |
| StreetName | String | StreetName | **YES** | `site_address` |
| StreetSuffix | String | StreetSuffix | NO | -- |
| StreetPostDirection | String | StreetPostDirection | NO | -- |
| City | String | City | NO | -- |
| Zip | String | Zip | NO | -- |
| State | String | State | NO | -- |
| Owner1 | String | Owner1 | **YES** | `owner_name` |
| Owner2 | String | Owner2 | NO | -- |
| OwnerAddress1 | String | OwnerAddress1 | NO | -- |
| OwnerAddress2 | String | OwnerAddress2 | NO | -- |
| OwnerCity | String | OwnerCity | NO | -- |
| OwnerState | String | OwnerState | NO | -- |
| OwnerZip | String | OwnerZip | NO | -- |
| OwnerCountry | String | OwnerCountry | NO | -- |
| TaxValue | String | TaxValue | NO | -- |
| confidential | String | confidential | NO | -- |
| GlobalID | GlobalID | GlobalID | NO | -- |
| Shape__Area | Double | Shape__Area | NO | -- |
| Shape__Length | Double | Shape__Length | NO | -- |
| LastSale | Date | LastSale | NO | -- |
| **Acerage** | **String (sic)** | **Acerage** | **YES** | **`acreage`** |
| Exemptions | Integer | Exemptions | NO | -- |
| gis_int_bxcm_val | Integer | bxcm_val | NO | -- |

**Note on `Acerage`:** The typo is in the source schema. Field type is `String`, not `Double` -- values arrive as strings and need numeric coercion in the adapter.

---

## 5. What We Query

### WHERE Clause Pattern

```sql
Owner1 LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-char WHERE cap, same as other FL counties.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | ParcelID | |
| `owner_name` | Owner1 | Second owner (`Owner2`) not mapped |
| `site_address` | StreetName | Street name ONLY -- no number, predirection, suffix, or postdirection |
| `use_type` | -- | NO use field in this schema |
| `acreage` | **Acerage** (sic) | String-typed; adapter coerces to float |
| `subdivision_name` | -- | Not in schema |
| `building_value` | -- | Not mapped (TaxValue exists) |
| `appraised_value` | -- | Not mapped (TaxValue exists as string) |
| `deed_date` | -- | Not mapped (LastSale exists as Date) |
| `geometry` | Shape | Polygons |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | ParcelID | -- | -- |
| Owner | YES | Owner1 | Second owner | Owner2 |
| Owner mailing address | NO | -- | 6-field mailing address | OwnerAddress1/2, OwnerCity, OwnerState, OwnerZip, OwnerCountry |
| Site address (full) | PARTIAL | StreetName | Street number, predirection, suffix, postdirection, city, zip, state | StreetNumber, StreetPredirection, StreetSuffix, StreetPostDirection, City, Zip, State |
| Tax value | NO | -- | Assessed tax value (string) | TaxValue |
| Last sale date | NO | -- | Most recent sale date | LastSale |
| Acreage | YES | **Acerage** (sic) | GIS-computed area | Shape__Area |
| Exemption count | NO | -- | Integer count | Exemptions |
| Confidentiality flag | NO | -- | Owner confidentiality marker | confidential |
| County-internal tracking value | NO | -- | Unknown purpose | gis_int_bxcm_val |
| Global ID | NO | -- | Cross-service GUID | GlobalID |
| Use code | NO | -- | NOT IN SCHEMA | -- |
| Geometry | YES | Shape | Shape perimeter | Shape__Length |

Of 27 attribute fields, we map 4 (parcel, owner, street name, acreage) plus geometry. Owner mailing address, full situs address, tax value, sale date, and exemptions are all ignored.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace-based shell/hole classification.

### Coordinate Re-projection

Source SRS is Web Mercator (WKID 102100 / EPSG:3857). We request `outSR=4326` so the server re-projects to WGS84.

### cos²(lat) Correction

Not triggered for Okeechobee because `Acerage` (sic) is a PA-sourced acreage attribute (despite being typed as `String`). `Shape__Area` exists but is not our acreage source.

---

## 9. Known Limitations and Quirks

1. **`Acerage` typo is preserved verbatim.** The source ArcGIS layer has a misspelled field named `Acerage` (not `Acreage`). The seed config in `seed_bi_county_config.py` uses this exact spelling: `"gis_acreage_field": "Acerage"`. **Do NOT "correct" this** -- changing it to `Acreage` breaks the query (field does not exist). This is the single most important quirk for Okeechobee.

2. **`Acerage` is typed as String, not Double.** Unlike Bay (`DTAXACRES` Double) or Polk (`TOT_ACREAGE` Double), Okeechobee stores acreage as a String. The adapter must coerce to float before arithmetic. Empty strings or non-numeric contents will cause conversion errors downstream.

3. **No use-code column.** The schema has no DOR use-code equivalent. The `seed_bi_county_config.py` Okeechobee entry sets `gis_use_field=None`. Downstream code that expects a use classification must skip this county or provide its own.

4. **Tyler Technologies-hosted tenant.** The endpoint is on ArcGIS Online (`services3.arcgis.com`) under the `jE4lvuOFtdtz6Lbl` org (Tyler Technologies). Unlike county-hosted servers (Bay, Escambia, Polk), this is NOT served from an `*.okeechobeecountyfl.gov` domain. Data refresh cadence is controlled by Tyler, not the county directly -- service description says "updated on a monthly basis".

5. **Site address is StreetName only.** The adapter maps `site_address -> StreetName`, which is just the street NAME (e.g., `"MAIN ST"`) without the number, predirection, suffix, postdirection, or city/state/zip. Full-address reconstruction requires concatenating 7 fields: `StreetNumber StreetPredirection StreetName StreetSuffix StreetPostDirection City State Zip`.

6. **`Owner1` / `Owner2` split.** Unlike Bay's `A2OWNAME` (single field), Okeechobee splits owners across two columns. Only `Owner1` is mapped. For multi-owner parcels, `Owner2` is silently dropped.

7. **Web Mercator native.** Source SRS is WKID 102100. Requesting `outSR=4326` re-projects server-side to WGS84.

8. **Tax value is String.** `TaxValue` is typed as `String`, not a numeric type. Parsing requires stripping `$` / `,` and coercing. Not currently mapped.

9. **LastSale is Date.** `LastSale` is a proper `esriFieldTypeDate`. If mapped in the future, no string parsing is needed -- just an ISO date conversion.

10. **Sibling layers expose rich geospatial context.** The same FeatureServer includes Zoning (9), Future Land Use (8), FEMA Flood Zones (7), Opportunity Zones (10), Commission Districts (5), and Electric Service Areas (6). None are currently queried by BI, but they are available for spatial joins if enrichment is desired.

11. **18 layers total, but only layer 2 is seeded.** The other 17 layers (boundaries, hydrants, flood, zoning, etc.) are not part of the BI pipeline.

12. **Max record count is 2000.** Higher than Bay or Escambia (1000), so pagination is less frequent.

**Source of truth:** `seed_bi_county_config.py` (Okeechobee block, lines 378-386 -- preserves the `Acerage` typo), `county-registry.yaml` (`okeechobee-fl.projects.bi`), live metadata from `https://services3.arcgis.com/jE4lvuOFtdtz6Lbl/arcgis/rest/services/Tyler_Technologies_Display_Map/FeatureServer/2?f=json`
