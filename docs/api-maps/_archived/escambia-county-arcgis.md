# Escambia County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server 10.91, MapServer |
| Endpoint | `https://gismaps.myescambia.com/arcgis/rest/services/Individual_Layers/parcels/MapServer/0` |
| Layer Name | Parcels (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 2883 (NAD83 HARN Florida West, US Feet) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | REFERENCE |
| ObjectId Field | OBJECTID |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Escambia field mapping (from `seed_bi_county_config.py`)

| Purpose | Escambia Field |
|---------|---------------|
| Owner | `OWNER` |
| Parcel | `REFNUM` |
| Address | `SITEADDR` |
| Use | `LANDTYPE` |
| Acreage | `LANDSIZE` |

Service-level metadata (`.../parcels/MapServer?f=json`): `capabilities: Map,Query,Data`, service description "Escambia County Parcels - Updated Monthly".

---

## 2. Other Layers at MapServer Root

Only one layer on this MapServer:

| ID | Name | Geometry Type |
|----|------|---------------|
| **0** | **Parcels** | **Feature Layer (target)** |

(No sibling layers -- Escambia's parcels service is a single-purpose endpoint, unlike Bay's 31-layer BayView MapServer.)

---

## 3. Query Capabilities

Base query URL:

```
https://gismaps.myescambia.com/arcgis/rest/services/Individual_Layers/parcels/MapServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNER LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from FL West StatePlane to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |

### Advanced query capabilities (per service metadata)

- Pagination: YES
- HAVING clause: YES
- Order by: YES
- Distinct: YES
- Count distinct: YES
- Percentile stats: YES
- True curves: YES
- Query with distance: YES
- Supported spatial relationships: intersects, contains, crosses, envelope_intersects, index_intersects, overlaps, touches, within, relation

### Pagination

Standard `resultOffset` / `resultRecordCount`. Server sets `exceededTransferLimit: true` when more rows are available.

---

## 4. Field Inventory

48 attribute fields + geometry. Complete catalog from the live `?f=json` response:

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | OID | OBJECTID | -- | NO | -- |
| REFERENCE | String | REFERENCE | 16 | NO | -- |
| REFNUM | String | REFNUM | 30 | **YES** | `parcel_number` |
| OWNER | String | OWNER | 50 | **YES** | `owner_name` |
| MAILADDRESS1 | String | MAILING ADDRESS1 | 50 | NO | -- |
| MAILADDRESS2 | String | MAILING ADDRESS2 | 50 | NO | -- |
| MAILCITY | String | MAILING CITY | 50 | NO | -- |
| MAILSTATE | String | MAILING STATE | 2 | NO | -- |
| MAILZIP | String | MAILING ZIP | 10 | NO | -- |
| MAILCOUNTRY | String | MAILING COUNTRY | 50 | NO | -- |
| YEAR_ | String | YEAR | 4 | NO | -- |
| CONTROLNO | String | CONTROLNO | 23 | NO | -- |
| SITEADDR | String | SITE ADDRESS | 500 | **YES** | `site_address` |
| CITY | String | CITY | 100 | NO | -- |
| ZIP | String | ZIP | 50 | NO | -- |
| SUBDIVCONDO | String | SUBDIVCONDO | 15 | NO | -- |
| SUBDIVISION | String | SUBDIVISION | 50 | NO | -- |
| LEGAL1 | String | LEGAL1 | 50 | NO | -- |
| LEGAL2 | String | LEGAL2 | 50 | NO | -- |
| LEGAL3 | String | LEGAL3 | 50 | NO | -- |
| LEGAL4 | String | LEGAL4 | 50 | NO | -- |
| LEGAL5 | String | LEGAL5 | 50 | NO | -- |
| LEGAL6 | String | LEGAL6 | 50 | NO | -- |
| CONFCD | String | CONFCD | 1 | NO | -- |
| CITYCD | String | CITYCD | 6 | NO | -- |
| TIFCD | String | TIFCD | 10 | NO | -- |
| DORCD | String | DORCD | 16 | NO | -- |
| DELINQCD | String | DELINQCD | 1 | NO | -- |
| AGEXEMPT | String | AGEXEMPT | 1 | NO | -- |
| CURRASDLAND | Double | CURRASDLAND | -- | NO | -- |
| CURRASDBLDG | Double | CURRASDBLDG | -- | NO | -- |
| CURRASDXF | Double | CURRASDXF | -- | NO | -- |
| CURRMKT | Double | CURRMKT | -- | NO | -- |
| PREVASDLAND | Double | PREVASDLAND | -- | NO | -- |
| PREVASDBLDG | Double | PREVASDBLDG | -- | NO | -- |
| PREVASDXF | Double | PREVASDXF | -- | NO | -- |
| PREVMKT | Double | PREVMKT | -- | NO | -- |
| SOHYEAR | Integer | SOHYEAR | -- | NO | -- |
| CAPPEDVALUE | Double | CAPPEDVALUE | -- | NO | -- |
| OWNERSPLITPCT | Integer | OWNERSPLITPCT | -- | NO | -- |
| LANDAPPRAIS | String | LANDAPPRAIS | 30 | NO | -- |
| LANDTYPE | String | LANDTYPE | 50 | **YES** | `use_type` |
| LANDSIZE | Double | LANDSIZE | -- | **YES** | `acreage` |
| MAPNUM | String | MAPNUM | 50 | NO | -- |
| EXEMPTION | String | EXEMPTION | 50 | NO | -- |
| LINK | String | LINK | 75 | NO | -- |
| Shape | Geometry | Shape | -- | YES (via engine) | `geometry` |
| Shape.area | Double | Shape.area | -- | NO | -- |
| Shape.len | Double | Shape.len | -- | NO | -- |

---

## 5. What We Query

### WHERE Clause Pattern

Single alias:
```sql
OWNER LIKE '%BUILDER NAME%'
```

Batched OR:
```sql
OWNER LIKE '%BUILDER A%' OR OWNER LIKE '%BUILDER B%'
```

### Batching Rules

Same 2000-character WHERE limit as other FL counties. No county-specific alias cap.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | REFNUM | |
| `owner_name` | OWNER | 50-char truncated (source schema limit) |
| `site_address` | SITEADDR | Up to 500 chars -- unusually wide; accommodates multi-line addresses |
| `use_type` | LANDTYPE | Escambia's DOR-equivalent use description (text) |
| `acreage` | LANDSIZE | Double; already in acres |
| `subdivision_name` | -- | NOT mapped, though `SUBDIVISION` field exists |
| `building_value` | -- | NOT mapped, though `CURRASDBLDG` exists |
| `appraised_value` | -- | NOT mapped, though `CURRMKT` exists |
| `deed_date` | -- | NOT present in layer |
| `geometry` | Shape | Polygons |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | REFNUM | Alt reference, control number | REFERENCE, CONTROLNO |
| Owner | YES | OWNER | Mailing address (5 fields), owner split % | MAILADDRESS1-2, MAILCITY, MAILSTATE, MAILZIP, MAILCOUNTRY, OWNERSPLITPCT |
| Site address | YES | SITEADDR | City, ZIP | CITY, ZIP |
| Use | YES | LANDTYPE | DOR numeric code | DORCD |
| Acreage | YES | LANDSIZE | GIS-calculated area (sq-ft-ish) | Shape.area |
| Subdivision | NO | -- | Subdivision name + code + SUBDIVCONDO flag | SUBDIVISION, SUBDIVCONDO |
| Legal description | NO | -- | 6-part structured legal | LEGAL1 through LEGAL6 |
| Building value (current) | NO | -- | Current assessed building value | CURRASDBLDG |
| Land value (current) | NO | -- | Current assessed land value | CURRASDLAND |
| Extra features value | NO | -- | Current assessed extra features | CURRASDXF |
| Market value (current) | NO | -- | Current market value | CURRMKT |
| Previous values | NO | -- | Previous-year comparison | PREVASDLAND, PREVASDBLDG, PREVASDXF, PREVMKT |
| Save Our Homes year | NO | -- | Homestead "Save Our Homes" starting year | SOHYEAR |
| Capped value | NO | -- | Save-Our-Homes capped value | CAPPEDVALUE |
| Agricultural exemption | NO | -- | Ag classification flag | AGEXEMPT |
| Confidential flag | NO | -- | Owner confidentiality flag | CONFCD |
| Delinquency | NO | -- | Delinquency code | DELINQCD |
| TIF district | NO | -- | Tax increment financing district | TIFCD |
| City code | NO | -- | Incorporated-city code | CITYCD |
| Year | NO | -- | Assessment roll year | YEAR_ |
| Map number | NO | -- | Assessor map number | MAPNUM |
| Exemption description | NO | -- | Full exemption list | EXEMPTION |
| Land appraiser | NO | -- | Appraiser staff name/code | LANDAPPRAIS |
| Portal link | NO | -- | Link to PA detail page | LINK |

Of 48 attribute fields, we map 5. The remaining 43 include valuation (present + historical), 6-part structured legal description, subdivision, tax classification, and a direct link back to the Property Appraiser's detail page.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: ArcGIS rings -> GeoJSON Polygon / MultiPolygon via shoelace-based shell/hole classification, with Shapely for multi-exterior cases.

### Coordinate Re-projection

Source SRS is NAD83 HARN Florida West StatePlane (WKID 2883, US Feet). We request `outSR=4326`, and the server re-projects to WGS84 before returning coordinates.

### cos²(lat) Correction

Not triggered for Escambia because `LANDSIZE` is a Property-Appraiser acreage attribute, not a `Shape.area` / `Shape__Area` derivation.

---

## 9. Known Limitations and Quirks

1. **MapServer, not FeatureServer.** Like Bay, Escambia serves parcels from a MapServer. Read-only queries are identical; write operations unavailable (moot for BI).

2. **Dedicated parcels service (no sibling layers).** The `Individual_Layers/parcels/MapServer` contains only Layer 0 (Parcels). Future additions (zoning, flood, future land use) would require discovering separate services on `gismaps.myescambia.com`.

3. **No DOR-code mapping.** The layer has `DORCD` (DOR numeric code) and `LANDTYPE` (text description). We map the text, not the numeric code. Counties that want numeric DOR filtering would need to add the field.

4. **No deed date, building value, appraised value.** Escambia does NOT include a deed date column, and we do NOT map the valuation columns that ARE present (`CURRASDBLDG`, `CURRMKT`). Extending mapping to include these is trivially a config change in `seed_bi_county_config.py`.

5. **Acreage is `LANDSIZE`, not `ACRES`.** Do not copy a neighboring county's field name; Escambia uses the `LANDSIZE` column for the numeric acreage.

6. **`SITEADDR` is up to 500 chars.** That's extreme for a street-address field; Escambia uses it for multi-line or concatenated addresses in some records. Downstream geocoders may need to split on `;` or `\n`.

7. **Subdivision in two columns.** Escambia has both `SUBDIVISION` (name) and `SUBDIVCONDO` (a 15-char code or flag). The current config maps neither; when mapped, the `SUBDIVISION` name column is the right choice.

8. **Legal description is split across six fields.** `LEGAL1` through `LEGAL6`. Any future mapping must concatenate with space or newline separators.

9. **Updated monthly.** Per service description: "Escambia County Parcels - Updated Monthly". Data lag is up to ~30 days.

10. **Registry status: active.** `county-registry.yaml` (`escambia-fl.projects.bi`) says `status: active`. Live probe at doc-write time confirmed `HTTP 200` with sample rows.

**Source of truth:** `seed_bi_county_config.py` (Escambia block, lines 94-102), `county-registry.yaml` (`escambia-fl.projects.bi`), live metadata from `https://gismaps.myescambia.com/arcgis/rest/services/Individual_Layers/parcels/MapServer/0?f=json`
