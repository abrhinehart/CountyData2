# Polk County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server 11.5, FeatureServer |
| Endpoint | `https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1` |
| Layer Name | Parcels (ID 1) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Export Formats | SQLite, FileGDB, Shapefile, CSV, GeoJSON |
| Display Field | NAME |
| ObjectId Field | OBJECTID |

### Other Layers at FeatureServer Root

| ID | Name | Geometry Type | Notes |
|----|------|---------------|-------|
| 1 | **Parcels** | esriGeometryPolygon | Our query target |
| 2 | Parcel Labels | esriGeometryPolygon | Label layer, not queried |
| 3 | Subdivision | esriGeometryPolygon | Subdivision boundaries |
| 4 | Lots | esriGeometryPolygon | Visible at scale 1:2,257 |
| 5 | Parcel Dimension | esriGeometryPolyline | Visible at scale 1:2,257 |
| 6 | Parcel Misc | esriGeometryPolyline | Visible at scale 1:2,257 |

Service-level capabilities include datum transformation (WGS_1984 to NAD_1983), async apply-edits, sync with per-layer/replica control, and append operations.

---

## 2. Query Capabilities

Base query URL:
```
https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `NAME LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygon shapes |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | `1000` (config default) | Page size (server max is 2000) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter envelope/polygon |
| `geometryType` | NO | -- | Type of geometry filter |
| `spatialRel` | NO | -- | Spatial relationship (intersects, contains, etc.) |
| `orderByFields` | NO | -- | Sort order |
| `groupByFieldsForStatistics` | NO | -- | Aggregate queries |
| `returnCountOnly` | NO | -- | Count-only mode |
| `returnIdsOnly` | NO | -- | ID-only mode |
| `returnDistinctValues` | NO | -- | Distinct values |

### Pagination

The engine uses `resultOffset` / `resultRecordCount` for server-side pagination. When the response includes `exceededTransferLimit: true`, it advances the offset by the number of features returned and issues another request. The server's max record count is 2000; our config defaults to 1000 per page.

---

## 3. Field Inventory

Complete field catalog from the layer metadata (55 attribute fields + OBJECTID):

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | esriFieldTypeOID | OBJECTID | -- | NO | -- |
| PARCELID | esriFieldTypeString | PARCEL_ID | 25 | **YES** | `parcel_number` |
| SECTION | esriFieldTypeString | SECTION | 2 | NO | -- |
| TOWNSHIP | esriFieldTypeString | TOWNSHIP | 2 | NO | -- |
| RANGE | esriFieldTypeString | RANGE | 6 | NO | -- |
| SUBDIVISION | esriFieldTypeString | SUB | 6 | **YES** | `subdivision_name` |
| PARCEL | esriFieldTypeString | PARCEL | 6 | NO | -- |
| DOR_CD | esriFieldTypeString | DORUS_CODE | 16 | NO | -- |
| DORDESC | esriFieldTypeString | DORDESC | 10 | NO | -- |
| DOR_USE_CODE_DESC | esriFieldTypeString | DORDESC1 | 100 | **YES** | `use_type` |
| NH_CD | esriFieldTypeDouble | NH_CD | -- | NO | -- |
| NH_DSCR | esriFieldTypeString | NH_DSCR | 50 | NO | -- |
| HMSTD_VAL | esriFieldTypeInteger | HOMESTEAD | -- | NO | -- |
| OTHEREX | esriFieldTypeInteger | OTHEREX | -- | NO | -- |
| EXCODE | esriFieldTypeString | EXCODE | 100 | NO | -- |
| EXDESC | esriFieldTypeString | EXDESC | 250 | NO | -- |
| PORT_VAL | esriFieldTypeDouble | PORT_VAL | -- | NO | -- |
| CLS_LND_VAL | esriFieldTypeInteger | CLS_LND_VAL | -- | NO | -- |
| AG_CLASS | esriFieldTypeString | AG_CLASS | 1 | NO | -- |
| VALUETYPE | esriFieldTypeString | VALUETYPE | 2 | NO | -- |
| VALUEDESC | esriFieldTypeString | VALUEDESC | 50 | NO | -- |
| TOT_LND_VAL | esriFieldTypeInteger | TOT_LND_VAL | -- | NO | -- |
| TOT_BLD_VAL | esriFieldTypeInteger | TOT_BLD_VAL | -- | **YES** | `building_value` |
| TOT_XF_VAL | esriFieldTypeInteger | TOT_XF_VAL | -- | NO | -- |
| TOTALVAL | esriFieldTypeInteger | TOTALVAL | -- | NO | -- |
| RECONCILE | esriFieldTypeString | RECONCILE | 6 | NO | -- |
| ASSESSVAL | esriFieldTypeDouble | ASSESSVAL | -- | **YES** | `appraised_value` |
| TAXVAL | esriFieldTypeDouble | TAXVAL | -- | NO | -- |
| CURTAXDIST | esriFieldTypeString | CURTAXDIST | 16 | NO | -- |
| TAXDIST | esriFieldTypeString | TAXDIST | 16 | NO | -- |
| AMTDUE | esriFieldTypeDouble | AMTDUE | -- | NO | -- |
| MILLRATE | esriFieldTypeDouble | MILLRATE | -- | NO | -- |
| YR_CREATED | esriFieldTypeInteger | YR_CREATED | -- | NO | -- |
| YR_IMPROVED | esriFieldTypeInteger | YR_IMPROVED | -- | NO | -- |
| LAST_INSP_DT | esriFieldTypeDate | LAST_INSP_DT | 8 | NO | -- |
| TOT_ACREAGE | esriFieldTypeDouble | TOT_ACREAGE | -- | **YES** | `acreage` |
| PR_STRAP | esriFieldTypeString | PR_STRAP | 25 | NO | -- |
| HMSTD | esriFieldTypeString | HMSTD | 1 | NO | -- |
| GIS_ACREAGE | esriFieldTypeDouble | GIS_ACREAGE | -- | NO | -- |
| NAME | esriFieldTypeString | NAME | 100 | **YES** | `owner_name` |
| MAIL_ADDR_1 | esriFieldTypeString | MAIL_ADDR_1 | 50 | NO | -- |
| MAIL_ADDR_2 | esriFieldTypeString | MAIL_ADDR_2 | 50 | NO | -- |
| MAIL_ADDR_3 | esriFieldTypeString | MAIL_ADDR_3 | 101 | NO | -- |
| MAIL_ZIP | esriFieldTypeString | MAIL_ZIP | 10 | NO | -- |
| BLD_NUM | esriFieldTypeInteger | BLD_NUM | -- | NO | -- |
| PROP_ADRSTR | esriFieldTypeString | PROP_ADRSTR | 50 | **YES** | `site_address` |
| PROP_ADRDIR | esriFieldTypeString | PROP_ADRDIR | 2 | NO | -- |
| PROP_ADRNO | esriFieldTypeInteger | PROP_ADRNO | -- | NO | -- |
| PROP_ADRNO_SFX | esriFieldTypeString | PROP_ADRNO_SFX | 3 | NO | -- |
| PROP_ADRSUF | esriFieldTypeString | PROP_ADRSUF | 10 | NO | -- |
| PROP_ADRSUF2 | esriFieldTypeString | PROP_ADRSUF2 | 2 | NO | -- |
| PROP_UNITNO | esriFieldTypeString | PROP_UNITNO | 15 | NO | -- |
| PROP_ZIP | esriFieldTypeString | PROP_ZIP | 10 | NO | -- |
| PROP_CITY | esriFieldTypeString | PROP_CITY | 50 | NO | -- |
| Shape__Area | esriFieldTypeDouble | Shape.STArea() | -- | NO | -- |
| Shape__Length | esriFieldTypeDouble | Shape.STLength() | -- | NO | -- |

---

## 4. What We Query

### WHERE Clause Pattern

Single-alias query:
```sql
NAME LIKE '%BUILDER NAME%'
```

Batch OR query (multiple aliases combined):
```sql
NAME LIKE '%BUILDER A%' OR NAME LIKE '%BUILDER B%' OR NAME LIKE '%BUILDER C%'
```

Single quotes in alias names are escaped by doubling (`'` becomes `''`).

### Batching Rules

The `GISQueryEngine` batches multiple builder aliases into a single OR WHERE clause. If the combined WHERE string exceeds `MAX_WHERE_LENGTH` (2000 characters) or a county-specific alias cap is reached, the batch is split into multiple queries. Polk County has no county-specific alias cap override.

### Adaptive Delay

The engine uses an `AdaptiveDelay` controller between paginated and batched requests:
- **Base delay:** 0.3s
- **Floor:** 0.2s
- **Ceiling:** 3.0s
- Backs off (+0.2s) when response time exceeds 5 seconds
- Recovers (-0.1s) after 3 consecutive fast (<2s) responses
- Doubles delay on errors (up to ceiling)

---

## 5. Parsed Output

Each feature is parsed into a `ParsedParcel` dataclass:

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PARCELID | Required; rows without a parcel number are dropped |
| `owner_name` | NAME | Raw owner string from the Property Appraiser |
| `site_address` | PROP_ADRSTR | Street address only (no city, state, zip) |
| `use_type` | DOR_USE_CODE_DESC | FL DOR use code description (e.g., "SINGLE FAMILY") |
| `acreage` | TOT_ACREAGE | Pre-computed acreage from the PA; no unit conversion needed |
| `subdivision_name` | SUBDIVISION | Subdivision code (6-char) from the parcel layer |
| `building_value` | TOT_BLD_VAL | Total building value (integer, USD) |
| `appraised_value` | ASSESSVAL | County assessed value (double, USD) |
| `deed_date` | DEED_DT | Deed date from the Property Appraiser |
| `previous_owner` | -- | Not configured for Polk County |
| `geometry` | Feature geometry | Converted from ArcGIS JSON rings to GeoJSON Polygon/MultiPolygon |

---

## 6. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|--------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PARCELID | -- | -- |
| Owner Name | YES | NAME | -- | -- |
| Site Address (street) | YES | PROP_ADRSTR | Direction, suffix, unit, city, zip | PROP_ADRDIR, PROP_ADRSUF, PROP_UNITNO, PROP_CITY, PROP_ZIP |
| DOR Use Code | YES | DOR_USE_CODE_DESC | Numeric DOR code | DOR_CD |
| Acreage | YES | TOT_ACREAGE | GIS-computed acreage | GIS_ACREAGE |
| Geometry | YES | rings | -- | -- |
| Subdivision code | YES | SUBDIVISION | Subdivision boundary polygon (Layer 3) | Spatial join to Layer 3 |
| Section/Township/Range | NO | -- | Legal description components | SECTION, TOWNSHIP, RANGE |
| Homestead status | NO | -- | Homestead flag and value | HMSTD, HMSTD_VAL |
| Exemption info | NO | -- | Code and description | EXCODE, EXDESC |
| Land value | NO | -- | Total land value | TOT_LND_VAL |
| Building value | YES | TOT_BLD_VAL | -- | -- |
| Extra features value | NO | -- | Total extra features value | TOT_XF_VAL |
| Total value | NO | -- | Total assessed value | TOTALVAL |
| Assessed value | YES | ASSESSVAL | -- | -- |
| Deed date | YES | DEED_DT | Previous owner | (not mapped) |
| Taxable value | NO | -- | Tax value and amount due | TAXVAL, AMTDUE |
| Tax district | NO | -- | Current and historical | CURTAXDIST, TAXDIST |
| Mill rate | NO | -- | Current mill rate | MILLRATE |
| Portability value | NO | -- | Save-Our-Homes portability | PORT_VAL |
| Ag classification | NO | -- | Agricultural classification flag | AG_CLASS |
| Year built / improved | NO | -- | Year created and year improved | YR_CREATED, YR_IMPROVED |
| Last inspection date | NO | -- | Property Appraiser inspection | LAST_INSP_DT |
| Neighborhood | NO | -- | Neighborhood code and description | NH_CD, NH_DSCR |
| Mailing address | NO | -- | Owner mailing address (3 lines + zip) | MAIL_ADDR_1, MAIL_ADDR_2, MAIL_ADDR_3, MAIL_ZIP |
| Building count | NO | -- | Number of buildings on parcel | BLD_NUM |
| Parcel strap number | NO | -- | Alternate parcel identifier | PR_STRAP |
| Value type | NO | -- | Valuation method code + description | VALUETYPE, VALUEDESC |
| Classified land value | NO | -- | Classified land value | CLS_LND_VAL |

Of 55 attribute fields, we currently map 9. The remaining 46 include valuation, tax, mailing address, legal description, homestead, and neighborhood data.

---

## 7. Geometry Handling

### ArcGIS to GeoJSON Conversion

The `_arcgis_to_geojson` method converts ArcGIS JSON geometry (array of rings) to GeoJSON:

1. **Single ring** -- fast path, emits a GeoJSON `Polygon`
2. **Multiple rings** -- classified by the shoelace formula:
   - Clockwise (negative signed area) = exterior shell
   - Counter-clockwise (positive signed area) = hole
3. **Single exterior + holes** -- `Polygon` with holes
4. **Multiple exteriors** -- uses Shapely to assign each hole to its containing exterior; emits `MultiPolygon`

### Coordinate Re-projection

The query requests `outSR=4326`, so the server re-projects from Web Mercator (WKID 102100) to WGS84 (EPSG:4326) before returning coordinates. No client-side re-projection is needed.

### cos²(lat) Correction

When a county's acreage field is a geometry-computed area (e.g., `Shape__Area`), the engine applies a cos²(latitude) correction to convert Web Mercator square meters to true acres. This is **not triggered for Polk County** because `TOT_ACREAGE` is a pre-computed field from the Property Appraiser, not a geometry-derived value. The tokens that trigger this correction are: `shapestarea`, `shapearea`, `shape__area`.

---

## 8. Known Limitations and Quirks

1. **outFields=\* is inefficient.** We request all 55+ fields but only use 5. Specifying the needed fields would reduce response size significantly, especially for large batch queries.

2. **Subdivision code only (no boundary join).** Subdivision code is mapped via `SUBDIVISION`; the subdivision BOUNDARY polygon on Layer 3 is still not joined.

3. **Partial valuation mapping.** Building value (`TOT_BLD_VAL`) and assessed value (`ASSESSVAL`) are mapped; `TOTALVAL` and `TAXVAL` remain unmapped.

4. **Address is street-only.** `PROP_ADRSTR` gives the street address but omits direction, suffix, city, and zip. A full address would require concatenating `PROP_ADRNO`, `PROP_ADRDIR`, `PROP_ADRSTR`, `PROP_ADRSUF`, `PROP_UNITNO`, `PROP_CITY`, `PROP_ZIP`.

5. **WHERE length limit.** The engine limits WHERE clauses to 2000 characters. With typical alias lengths, this allows roughly 15-20 aliases per batch before splitting.

6. **Server max record count is 2000.** Our config uses 1000 per page, so pagination always kicks in before hitting the server limit. The `exceededTransferLimit` flag drives pagination.

7. **Web Mercator native SRS.** The data is stored in WKID 102100 (Web Mercator). We request `outSR=4326` for WGS84, which the server handles via datum transformation (WGS_1984 to NAD_1983).

8. **No previous owner.** Previous owner is not mapped. Deed date (`DEED_DT`) is now mapped.

9. **Layer 3 (Subdivision) is separate.** Subdivision boundary polygons live on Layer 3, not on the Parcels layer. A spatial join could theoretically enrich parcels with subdivision names, but this is not implemented.

10. **GIS_ACREAGE vs TOT_ACREAGE.** The layer has both a GIS-computed acreage field and a Property Appraiser-sourced acreage field. We use `TOT_ACREAGE` (PA source), which is more authoritative. The GIS-computed value may differ due to projection or digitization artifacts.
