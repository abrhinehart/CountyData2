# Okaloosa County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted) |
| Endpoint | `https://gis.myokaloosa.com/arcgis/rest/services/BaseMap_Layers/MapServer/111` |
| Layer Name | PARCELS (ID 111) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102660 / latestWkid 2238 (NAD_1983_HARN_StatePlane_Florida_North_FIPS_0903_Feet) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Export Formats | (MapServer only; no FeatureServer-style extracts) |
| Display Field | PATPCL_PIN |
| ObjectId Field | OBJECTID (not advertised in `objectIdField`; see Quirks) |
| Global ID Field | (none) |
| Capabilities | `Map,Query,Data` |
| Registry status | `bi` active; `cd2: needs_client`; `cr: pending_validation` (per `county-registry.yaml` L227-240) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Okaloosa field mapping (from `seed_bi_county_config.py` L203-210)

| Purpose | Okaloosa Field |
|---------|----------------|
| Owner | `PATPCL_OWNER` |
| Parcel | `PATPCL_PIN` |
| Address | `PATPCL_ADDR1` |
| Use | `PATPCL_USEDESC` |
| Acreage | `PATPCL_LGL_ACRE` |

**All mapped fields carry the `PATPCL_` prefix.** This is the Patriot AppraisalVision attribute-table naming convention -- rare in FL (used by a handful of PAs). Most other FL counties use shorter, less vendor-specific column names.

---

## 2. Other Layers at MapServer Root

Layer 111 is one of many in the `BaseMap_Layers` MapServer. The parent service is a composite PA/GIS map (abstract: "The Composite Land Records (CLRMN) theme consists of various arc attributes, seven logical region subclass layers..."). Only layer 111 (`PARCELS`) is seeded. Adjacent layers include addressing, zoning, flood, and district layers indexed by small integer IDs.

---

## 3. Query Capabilities

Base query URL:

```
https://gis.myokaloosa.com/arcgis/rest/services/BaseMap_Layers/MapServer/111/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `PATPCL_OWNER LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from StatePlane FL North (ft) to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 (server max) | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Uses `resultOffset` / `resultRecordCount`. `exceededTransferLimit: true` drives advance. Server max is 1000 per page.

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (77 fields including OBJECTID, Shape, and legacy SDE-qualified column):

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| OBJECTID | OID | OBJECTID | NO | -- |
| SDE.GIS.PARCELSPCLP.AREA | Double | AREA | NO | (SDE-qualified; see Quirks) |
| PERIMETER | Double | PERIMETER | NO | -- |
| PCLP_ | Integer | PCLP_ | NO | -- |
| PCLP_ID | Integer | PCLP_ID | NO | -- |
| **PATPCL_PIN** | **String** | PIN | **YES** | **`parcel_number`** |
| PATPCL_STRAP | String | PATPCL_STRAP | NO | -- |
| PATPCL_FRONT | Integer | PATPCL_FRONT | NO | -- |
| PATPCL_DEPTH | Integer | PATPCL_DEPTH | NO | -- |
| PATPCL_BACK | Integer | PATPCL_BACK | NO | -- |
| PATPCL_GIS_ACRE | Double | PATPCL_GIS_ACRE | NO | (GIS-computed; sibling of `PATPCL_LGL_ACRE`) |
| **PATPCL_LGL_ACRE** | **Double** | PATPCL_LGL_ACRE | **YES** | **`acreage`** |
| **PATPCL_OWNER** | **String** | OWNER | **YES** | **`owner_name`** |
| **PATPCL_ADDR1** | **String** | PATPCL_ADDR1 | **YES** | **`site_address`** |
| PATPCL_ADDR2 | String | PATPCL_ADDR2 | NO | -- |
| PATPCL_ADDR3 | String | PATPCL_ADDR3 | NO | -- |
| PATPCL_CITY | String | PATPCL_CITY | NO | -- |
| PATPCL_STATE | String | PATPCL_STATE | NO | -- |
| PATPCL_ZIPCODE | String | PATPCL_ZIPCODE | NO | -- |
| PATPCL_CNTRY | String | PATPCL_CNTRY | NO | -- |
| PATPCL_LEGL1 | String | PATPCL_LEGL1 | NO | Legal description line 1 |
| PATPCL_LEGL2 | String | PATPCL_LEGL2 | NO | Legal description line 2 |
| PATPCL_LEGL3 | String | PATPCL_LEGL3 | NO | Legal description line 3 |
| PATPCL_XFCODE1/2/3 | String | -- | NO | Extra-feature codes |
| PATPCL_XFEYB1/2/3 | Integer | -- | NO | Extra-feature effective years |
| PATPCL_XFUTPRIC1/2/3 | Double | -- | NO | Extra-feature unit prices |
| PATPCL_BLDGAYB / BLDGEYB / BLDGEQUAL | SmallInt | -- | NO | Building AYB / EYB / quality |
| PATPCL_AGVAL | Double | -- | NO | Ag value |
| PATPCL_ASSEDVAL | Double | -- | NO | Assessed value |
| PATPCL_BLDGVAL | Double | -- | NO | Building value |
| PATPCL_EFFRATE1/2/3 | Double | -- | NO | Effective rates |
| PATPCL_EXCODE | String | -- | NO | Exemption code |
| PATPCL_EXMPTVAL | String | -- | NO | Exemption value (String -- see Quirks) |
| PATPCL_JUSTVAL | String | -- | NO | Just value (String -- see Quirks) |
| PATPCL_MKTLAND | Double | -- | NO | Market land value |
| PATPCL_QUAL1/2/3 | String | -- | NO | Sale qualifier codes |
| PATPCL_SALE1/2/3 | Integer | -- | NO | Sale amounts |
| PATPCL_SALEDT1/2/3 | Integer | -- | NO | Sale dates (Integer, yyyymmdd packed) |
| PATPCL_SALEBK1/2/3 | Integer | -- | NO | Sale book |
| PATPCL_SALEPG1/2/3 | Integer | -- | NO | Sale page |
| PATPCL_TAXDIST | SmallInt | -- | NO | Tax district |
| PATPCL_TAXVAL | Double | -- | NO | Tax value |
| PATPCL_TOTALAPPR | Double | -- | NO | Total appraised value |
| PATPCL_USECODE | String | -- | NO | Use code |
| **PATPCL_USEDESC** | **String** | PATPCL_USEDESC | **YES** | **`use_type`** |
| PATPCL_XFOBVAL | Integer | -- | NO | Extra-feature observed value |
| PATPCL_SEC_NO / TS_NO / RG_NO | String | -- | NO | Section/Township/Range |
| PATPCL_SUB_NO / BLK_NO / PCL_NO | String | -- | NO | Subdivision/Block/Parcel number |
| PATPCL_SUB_KEY / BLK_KEY | String | -- | NO | Sub/block keys |
| Shape | Geometry | Shape | YES | Polygon source |
| SPLIT_DT | Date | Split Date | NO | -- |
| CENSUS_CD | String | CENSUS_CD | NO | -- |

---

## 5. What We Query

### WHERE Clause Pattern

```sql
PATPCL_OWNER LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE.

### Batching Rules

2000-char WHERE cap; max record count 1000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PATPCL_PIN | -- |
| `owner_name` | PATPCL_OWNER | -- |
| `site_address` | PATPCL_ADDR1 | ADDR2/ADDR3, city, state, zip, country all separate |
| `use_type` | PATPCL_USEDESC | String description (not the USECODE numeric) |
| `acreage` | PATPCL_LGL_ACRE | Legal (deeded) acreage, Double |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Bay County (MapServer peer)

Both Okaloosa and Bay are MapServer (not FeatureServer) endpoints on county-hosted StatePlane FL North infrastructure. Schemas and capabilities differ:

| Attribute | Okaloosa (`gis.myokaloosa.com`) | Bay (`gis.baycountyfl.gov`) |
|-----------|----------------------------------|------------------------------|
| Service | `BaseMap_Layers/MapServer/111` | `BayView/BayView/MapServer/2` |
| Layer name | PARCELS (ID 111) | Parcels (ID 2) |
| Field prefix | `PATPCL_` (Patriot AppraisalVision) | (none; e.g., `A2OWNAME`, `A1RENUM`) |
| Field count | 77 | ~60 |
| Max record count | 1000 | 1000 |
| Spatial reference | WKID 102660 / 2238 (StatePlane FL North ft) | WKID 102660 / 2238 (StatePlane FL North ft) |
| Capabilities | `Map,Query,Data` | `Map,Query,Data` |
| objectIdField advertised | NO (null in metadata) | YES (OBJECTID) |
| CAMA legal lines | YES (PATPCL_LEGL1/2/3) | YES (inline in separate fields) |
| PT surface in registry | NO (`needs_client` on Tyler Self-Service) | Independent track |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel PIN | YES | PATPCL_PIN | STRAP (alt parcel number) | PATPCL_STRAP |
| Owner | YES | PATPCL_OWNER | -- | -- |
| Site address | PARTIAL | PATPCL_ADDR1 | ADDR2, ADDR3, city, state, zip, country | PATPCL_ADDR2, PATPCL_ADDR3, PATPCL_CITY, PATPCL_STATE, PATPCL_ZIPCODE, PATPCL_CNTRY |
| Use (description) | YES | PATPCL_USEDESC | Use code (numeric) | PATPCL_USECODE |
| Legal description | NO | -- | 3-line legal | PATPCL_LEGL1, PATPCL_LEGL2, PATPCL_LEGL3 |
| Acreage (legal) | YES | PATPCL_LGL_ACRE | GIS-computed acreage | PATPCL_GIS_ACRE |
| Parcel dimensions | NO | -- | Front, depth, back (feet) | PATPCL_FRONT, PATPCL_DEPTH, PATPCL_BACK |
| Building attributes | NO | -- | AYB, EYB, quality | PATPCL_BLDGAYB, PATPCL_BLDGEYB, PATPCL_BLDGEQUAL |
| Values | NO | -- | Just, assessed, taxable, building, market land, ag | PATPCL_JUSTVAL, PATPCL_ASSEDVAL, PATPCL_TAXVAL, PATPCL_BLDGVAL, PATPCL_MKTLAND, PATPCL_AGVAL |
| Sale history (up to 3) | NO | -- | Date, amount, book, page, qualifier | PATPCL_SALEDT{1,2,3}, PATPCL_SALE{1,2,3}, PATPCL_SALEBK{1,2,3}, PATPCL_SALEPG{1,2,3}, PATPCL_QUAL{1,2,3} |
| Extra features (up to 3) | NO | -- | Code, EYB, unit price, obs. value | PATPCL_XFCODE{1,2,3}, PATPCL_XFEYB{1,2,3}, PATPCL_XFUTPRIC{1,2,3}, PATPCL_XFOBVAL |
| Legal S/T/R | NO | -- | Section, township, range | PATPCL_SEC_NO, PATPCL_TS_NO, PATPCL_RG_NO |
| Legal sub/block | NO | -- | Subdivision, block, parcel, keys | PATPCL_SUB_NO, PATPCL_BLK_NO, PATPCL_PCL_NO, PATPCL_SUB_KEY, PATPCL_BLK_KEY |
| Exemptions | NO | -- | Code and value | PATPCL_EXCODE, PATPCL_EXMPTVAL |
| Tax district | NO | -- | -- | PATPCL_TAXDIST |
| Parcel split date | NO | -- | -- | SPLIT_DT |
| Census code | NO | -- | -- | CENSUS_CD |
| Geometry | YES | Shape | Perimeter | PERIMETER |

Of 77 attribute fields, 5 are mapped. The unmapped attributes include complete valuation, 3-line legal description, legal section/township/range, 3-sale history, and extra-feature bundles -- the richest PA dataset of any FL BI county.

---

## 9. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon.

### Coordinate Re-projection

Stored in WKID 102660 (NAD 1983 HARN StatePlane FL North, US survey feet). Request `outSR=4326` to have the server re-project to WGS84.

### cos²(lat) Correction

Not triggered; `PATPCL_LGL_ACRE` is a PA-sourced Double, not `Shape__Area`. The sibling `PATPCL_GIS_ACRE` (unmapped) is the GIS-computed alternative.

---

## 10. Known Limitations and Quirks

1. **PATPCL_ prefix = Patriot AppraisalVision.** This vendor's column naming convention is rare in FL. Any helper that strips or normalizes column names must not collapse the prefix, because `PATPCL_OWNER` and a hypothetical `OWNER` alias exist -- the alias of `PATPCL_OWNER` is literally `OWNER`, which could cause an alias collision if the adapter keys on alias instead of name.

2. **Endpoint is MapServer, not FeatureServer.** Do NOT copy Clay's FeatureServer URL pattern by mistake -- MapServer requires the `/MapServer/111` path exactly. Capabilities are `Map,Query,Data` (no `Extract`, no `Sync`).

3. **`objectIdField` is null in service metadata.** The `?f=json` response does not advertise an `objectIdField`, yet `OBJECTID` exists in the attribute table. Some ArcGIS clients error out when `objectIdField` is absent; our engine falls back to `OBJECTID` literally.

4. **SDE-qualified column name `SDE.GIS.PARCELSPCLP.AREA`.** One attribute retains the fully-qualified Oracle / SDE schema prefix. Quoting in WHERE clauses must handle the dots correctly if this field is ever queried (it is not currently mapped).

5. **`PATPCL_EXMPTVAL` and `PATPCL_JUSTVAL` are String-typed.** Despite holding dollar amounts, these two fields are `String`, not `Double`. Any downstream consumer must coerce before arithmetic. Other value fields (`PATPCL_ASSEDVAL`, `PATPCL_BLDGVAL`, `PATPCL_TAXVAL`) are proper Doubles.

6. **Sale dates are Integer, not Date.** `PATPCL_SALEDT1/2/3` are integer-packed dates (e.g., `20250403`). Interpreting as dates requires splitting into year/month/day segments.

7. **Registry status split across projects.** `bi: active` works; `cd2: needs_client` (LandmarkWeb decommissioned, Tyler Self-Service client missing -- see `okaloosa-county-tyler-selfservice.md`); `cr: pending_validation` (Granicus IQM2 adapter added but not yet fully validated).

8. **No PT track.** Okaloosa does not have a `pt` entry in `county-registry.yaml` -- permit data pipeline not set up for this county.

9. **Server max record count 1000.** Half of Santa Rosa (2000) / Okeechobee (2000). Pagination kicks in sooner.

10. **StatePlane FL North (ft) native.** Same SRS as Bay County. `outSR=4326` re-projects to WGS84.

11. **77 fields is the largest BI schema in FL after Putnam (65).** The full Patriot-driven CAMA dataset is exposed; Okaloosa carries more context per parcel than any other FL MapServer layer we've onboarded.

12. **`PATPCL_LGL_ACRE` vs `PATPCL_GIS_ACRE`.** Seed config uses the legal (deeded) acreage. Downstream consumers needing a GIS-measured alternative would switch to `PATPCL_GIS_ACRE` and would trigger the cos²(lat) correction only if they then swapped to `Shape__Area`.

**Source of truth:** `seed_bi_county_config.py` (Okaloosa block, lines 203-210), `county-registry.yaml` (`okaloosa-fl.projects.bi`, L232-236), live metadata from `https://gis.myokaloosa.com/arcgis/rest/services/BaseMap_Layers/MapServer/111?f=json` (probed 2026-04-14, HTTP 200, 12 KB)
