# Charlotte County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted) |
| Endpoint | `https://agis3.charlottecountyfl.gov/arcgis/rest/services/Essentials/CCGISLayers/MapServer/27` |
| Layer Name | Ownership (ID 27) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 / latestWkid 3857 (Web Mercator) -- advertised only in query response; layer `?f=json` does NOT advertise `spatialReference` (returns `null`) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | `ownersname` |
| ObjectId Field | `OBJECTID` (service metadata `objectIdField` is `null`; OBJECTID is present in attributes) |
| Capabilities | `Map,Query,Data` |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** (seeded only via `seed_bi_county_config.py` L324-332) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Charlotte field mapping (from `seed_bi_county_config.py` L324-332)

| Purpose | Charlotte Field |
|---------|-----------------|
| Owner | `ownersname` |
| Parcel | `ACCOUNT` |
| Address | `FullPropertyAddress` |
| Use | `landuse` |
| Acreage | `Shape.STArea()` |

**Critical: acreage is a computed area expression, NOT a PA-sourced Double.** Unlike Bay (`DTAXACRES`), Santa Rosa (`CALC_ACRE`), or Collier (`TotalAcres`), Charlotte's seed config points `gis_acreage_field` at `Shape.STArea()` -- the server-side SQL area computation. Units are **square feet** (Web Mercator projection is in meters but Shape.STArea() on polygons returns the area in the layer's native projected units which, for Charlotte, resolve to square feet via the source datum). The cos²(lat) correction is relevant here (see §8).

**Owner field is lowercase `ownersname`.** Case-sensitive ArcGIS field name. Do NOT rewrite to `OWNERSNAME` / `OwnersName` / `OwnerName` -- none of those exist.

---

## 2. Other Layers at MapServer Root

Layer 27 is one of the `Essentials/CCGISLayers` composite MapServer's feature layers. Only layer 27 (Ownership) is seeded. The parent service advertises only standard `Map,Query,Data` capabilities.

---

## 3. Query Capabilities

Base query URL:

```
https://agis3.charlottecountyfl.gov/arcgis/rest/services/Essentials/CCGISLayers/MapServer/27/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `ownersname LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 (server max) | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Uses `resultOffset` / `resultRecordCount`. `exceededTransferLimit: true` drives advance.

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (52 fields including OBJECTID and SHAPE):

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | OID | OBJECTID | -- | NO | -- |
| SHAPE | Geometry | SHAPE | -- | YES | `geometry` |
| **ACCOUNT** | **String** | ACCOUNT | 14 | **YES** | **`parcel_number`** |
| **ownersname** | **String** | ownersname | 75 | **YES** | **`owner_name`** |
| mailingaddress | String | mailingaddress | 55 | NO | Owner mailing line 1 |
| suite | String | suite | 25 | NO | -- |
| mailingaddress2 | String | mailingaddress2 | 55 | NO | Owner mailing line 2 |
| city | String | city | 75 | NO | Owner mailing city |
| state | String | state | 2 | NO | -- |
| country | String | country | 30 | NO | -- |
| zipcode | String | zipcode | 10 | NO | -- |
| streetnumber | String | streetnumber | 10 | NO | Site street number |
| propertyaddress | String | propertyaddress | 50 | NO | Site address (short) |
| mapnumber | String | mapnumber | 5 | NO | -- |
| twprngsec | String | twprngsec | 6 | NO | Township/Range/Section |
| taxdistrict | String | taxdistrict | 4 | NO | -- |
| marketarea | String | marketarea | 2 | NO | -- |
| neighborhood | String | neighborhood | 5 | NO | -- |
| subneighborhood | String | subneighborhood | 5 | NO | -- |
| interest | String | interest | 6 | NO | -- |
| **landuse** | **String** | landuse | 30 | **YES** | **`use_type`** |
| zoningcode | String | zoningcode | 25 | NO | -- |
| utilities | String | utilities | 15 | NO | -- |
| roads | String | roads | 15 | NO | -- |
| water | String | water | 10 | NO | -- |
| parentaccount | String | parentaccount | 14 | NO | -- |
| exemcode | String | exemcode | 8 | NO | -- |
| totlandvalue | String (sic) | totlandvalue | 10 | NO | -- |
| totagcllandvalue | String (sic) | totagcllandvalue | 10 | NO | -- |
| totlandimpvalue | String (sic) | totlandimpvalue | 10 | NO | -- |
| totbuildvalue | String (sic) | totbuildvalue | 10 | NO | -- |
| totvalue | String (sic) | totvalue | 10 | NO | -- |
| totagclvalue | String (sic) | totagclvalue | 10 | NO | -- |
| correlatedvalue | String (sic) | correlatedvalue | 10 | NO | -- |
| assessedvalue | String (sic) | assessedvalue | 10 | NO | -- |
| prioryearcertjv | String (sic) | prioryearcertjv | 10 | NO | -- |
| prioryearasscv | String (sic) | prioryearasscv | 10 | NO | -- |
| prioryearexemamt | String (sic) | prioryearexemamt | 10 | NO | -- |
| prioryeartaxvalue | String (sic) | prioryeartaxvalue | 10 | NO | -- |
| usecode | String | usecode | 4 | NO | Numeric use code |
| description | String | description | 120 | NO | Long description |
| shortlegal | String | shortlegal | 50 | NO | Short legal |
| AccountLink | String | AccountLink | 105 | NO | PA detail URL |
| CONDOID | String | CONDOID | 10 | NO | -- |
| PKEY | Integer | PKEY | -- | NO | -- |
| FullMailingAddr | String | FullMailingAddr | 248 | NO | -- |
| **FullPropertyAddress** | **String** | Full Property Address | 61 | **YES** | **`site_address`** |
| SRC_OID | String | SRC_OID | 255 | NO | -- |
| SHAPE_Length | Double | SHAPE_Length | -- | NO | -- |
| SHAPE_Area | Double | SHAPE_Area | -- | NO | Precomputed Shape area (sq ft, Web Mercator) |
| ishomestead | SmallInteger | ishomestead | -- | NO | -- |
| lastsaleno70cent | Date | saledate | 8 | NO | -- |

Note the `SHAPE_Area` Double attribute also exists alongside the `Shape.STArea()` expression the seed config uses. Both are Web-Mercator-projected areas in source units.

### Sample row (live 2026-04-14)

From `query?where=1=1&outFields=*&resultRecordCount=1&f=json`:

```
ACCOUNT:             412716100001
ownersname:          EVANS PROPERTIES INC
landuse:             Agricultural
FullPropertyAddress: (null)
SHAPE_Area:          3338549.020309215
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
ownersname LIKE '%BUILDER NAME%'
```

Case-sensitive: `ownersname` MUST be lowercase.

### Batching Rules

2000-char WHERE cap, max record count 1000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | ACCOUNT | 14-char ID (e.g., `412716100001`) |
| `owner_name` | ownersname | Right-padded with spaces (field length 75) |
| `site_address` | FullPropertyAddress | Often NULL in rural / agricultural parcels; falls back to `propertyaddress` / `streetnumber` if used (not currently) |
| `use_type` | landuse | PA use description string (right-padded to 30 chars) |
| `acreage` | Shape.STArea() | **Computed sq ft via server SQL expression**, requires cos²(lat) correction + 43560 divide |
| `geometry` | SHAPE | Polygons |

---

## 7. Diff vs Sarasota (AGO peer) and Collier (MapServer peer)

| Attribute | Charlotte | Sarasota | Collier |
|-----------|-----------|----------|---------|
| Hosting | County (`agis3.charlottecountyfl.gov`) | AGO tenant `icrWMv7eBkctFu1f` | County (`gmdcmgis.colliercountyfl.gov`) |
| Service kind | MapServer | FeatureServer | MapServer |
| Parcel field | `ACCOUNT` (String) | `ID` (String) | `Folio` (Double, numeric) |
| Owner field | `ownersname` (all-lowercase) | `NAME1` | `OwnerLine1` (+ `OwnerLine2-5`) |
| Use field | `landuse` (lowercase) | `STCD` (5-char state code) | `UseCode` (Double numeric) |
| Acreage field | `Shape.STArea()` (expression, sq ft) | `MeasuredAcreage` (Double acres) | `TotalAcres` (Double acres) |
| Registry status | **ABSENT** | ABSENT (not in registry) | `bi: active` (L400-402) |
| Field count | 52 | 66 | 127 |
| Capabilities | `Map,Query,Data` | `Query,Extract` | `Query,Map,Data` |

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace-based shell/hole classification.

### Coordinate Re-projection

Source SRS is Web Mercator (WKID 102100 / EPSG:3857). Layer metadata does NOT advertise `spatialReference` (returns `null`), but the query response includes `spatialReference: {wkid: 102100, latestWkid: 3857}`. Requesting `outSR=4326` re-projects server-side to WGS84.

### cos²(lat) Correction

**Triggered.** Because `gis_acreage_field = "Shape.STArea()"` is a GIS-computed area (not a PA-sourced Double acreage), and the source projection is Web Mercator (which distorts area by cos²(lat) north of the equator), the adapter must apply a cos²(lat) correction after dividing by 43560 (sq ft -> acres). Charlotte is at ~26.9°N so the correction factor is approximately cos²(26.9°) ≈ 0.794 -- a ~20% reduction from the raw Web-Mercator square-foot area.

---

## 9. Known Limitations and Quirks

1. **Acreage is `Shape.STArea()`, NOT a PA-sourced Double.** Unlike every other MapServer county in this doc set, Charlotte's `gis_acreage_field` is a SQL area expression. Values arrive as square feet (Web Mercator native units), and the engine must divide by 43560 AND apply cos²(lat) correction. The `SHAPE_Area` Double attribute is equivalent but the seed config uses the expression form.

2. **Owner field is lowercase `ownersname`.** ArcGIS field names are case-sensitive here -- `OWNERSNAME`, `OwnersName`, and `OwnerName` all fail. The display field, alias, and underlying column are all lowercase `ownersname`.

3. **Parcel field is `ACCOUNT`, not `PARCELNO` / `PIN` / `FOLIO`.** Charlotte uses the CAMA "account" term for its parcel key. 14-char string. Do NOT copy a neighbor's config.

4. **Registry status: ABSENT from `county-registry.yaml`.** Unlike most FL counties, Charlotte has no entry in the three-project registry. The only source of truth is `seed_bi_county_config.py` L324-332. Any cross-project workflow that reads from `county-registry.yaml` will silently skip Charlotte.

5. **Layer metadata `spatialReference` is `null`; `objectIdField` is `null`.** The MapServer layer does not advertise either. The query-response payload fills in `spatialReference: {wkid: 102100}`. Clients that key on `objectIdField` from service metadata must fall back to the literal `OBJECTID` attribute.

6. **All valuation fields are String-typed.** `totlandvalue`, `totbuildvalue`, `totvalue`, `assessedvalue`, and six other value columns are `String`, length 10 -- despite holding numeric dollar amounts. Any downstream consumer must coerce before arithmetic.

7. **`FullPropertyAddress` is often NULL.** Observed in rural agricultural parcels (e.g., `EVANS PROPERTIES INC` -- agricultural, no situs address). Use-case code must handle nulls without falling back to the mailing address (which is the OWNER's address, not site).

8. **Parent/child parcel relationships exposed via `parentaccount` and `CONDOID`.** Condominium units and split parcels reference their parent; none of this is mapped.

9. **Homestead flag is SmallInteger.** `ishomestead` is a 1/0 int. Exemption details would require joining `exemcode` (8-char string) -- not queried.

10. **`lastsaleno70cent` is the last non-70%-cent sale date.** Oddly named column (alias `saledate`) stores the most recent arm's-length deed filtered to exclude the Florida 70% documentary-stamp indicator. Not mapped.

11. **Max record count 1000.** Pagination kicks in for any sweep over 1000 parcels.

12. **Both `SHAPE_Area` Double and `Shape.STArea()` expression return the same Web-Mercator square-foot value.** Seed config uses the expression form; the `SHAPE_Area` Double attribute is equivalent and could be substituted without changing semantics.

### Related surfaces not yet documented

- **Charlotte CD2:** No clerk-recording surface documented. Clerks are not in `LANDMARK_COUNTIES` and no AcclaimWeb / BrowserView / Tyler Self-Service config exists.

**Source of truth:** `seed_bi_county_config.py` (Charlotte block, lines 324-332), absence from `county-registry.yaml`, live metadata from `https://agis3.charlottecountyfl.gov/arcgis/rest/services/Essentials/CCGISLayers/MapServer/27?f=json` (probed 2026-04-14, HTTP 200, 7.1 KB; one-row query HTTP 200, 8.0 KB)
