# Sumter County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted on `gis.sumtercountyfl.gov`) |
| Endpoint | `https://gis.sumtercountyfl.gov/sumtergis/rest/services/DevelopmentServices/DevServices_Parcel2/MapServer/0` |
| Layer Name | SUMTERGIS.DBO.Sumter_PA_Parcels (ID 0; fully qualified SQL Server table name) |
| Service name | `DevServices_Parcel2` (note the trailing `2` -- not `Parcel` or `DevServices_Parcels`) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | (not exposed at layer level in metadata; sample rows return coordinates consistent with Web Mercator) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | PIN |
| ObjectId Field | (not declared at layer level; `OBJECTID` present as first field) |
| Capabilities | -- (not enumerated at layer level; parent service supports `Map,Query,Data`) |
| Registry status | **ABSENT -- Sumter is not in `county-registry.yaml` (no `sumter-fl` block)** |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### Sumter field mapping (from `seed_bi_county_config.py` L415-422)

| Purpose | Sumter Field |
|---------|--------------|
| Owner | `Owners_Nam` (Esri 10-char truncation of `Owners_Name`) |
| Parcel | `PIN` |
| Address | `Physical_A` (truncation of `Physical_Address`) |
| Use | `PROP_USE_D` (truncation of `PROP_USE_DESC` or similar) |
| Acreage | `Acres_Lot_` (trailing underscore is literal; truncation of `Acres_Lot_Area` or similar) |

**Four of five field names are Esri 10-character shapefile truncations.** `Owners_Nam` (no trailing `e`), `Physical_A` (no trailing `ddress`), `PROP_USE_D` (no trailing `escription`), and `Acres_Lot_` (trailing underscore preserved). Only `PIN` is a full name. Do NOT "correct" these -- the ArcGIS field names are literal and case-sensitive; changing them breaks queries.

---

## 2. Query Capabilities

Base query URL:

```
https://gis.sumtercountyfl.gov/sumtergis/rest/services/DevelopmentServices/DevServices_Parcel2/MapServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `Owners_Nam LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 | Page size (server max) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

---

## 3. Field Inventory

The layer exposes ~101 fields. Below is the mapped subset and selected highlights.

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| OBJECTID | OID | -- | NO | -- |
| OBJECTID_1 | Integer | -- | NO | -- (second OID-like field) |
| **PIN** | **String** | 50 | **YES** | **`parcel_number`** |
| TWP | String | 16 | NO | -- |
| ParentNo | String | 20 | NO | -- |
| Deleted_Co | String | 25 | NO | -- |
| Label | String | 150 | NO | -- |
| Notes | String | 250 | NO | -- |
| City_Tax_C | String | 10 | NO | -- |
| COMM_RES | String | 25 | NO | -- |
| Subdivisio | String | 40 | NO | -- (truncated `Subdivision`) |
| CONDO_Unit | String | 50 | NO | -- |
| **Acres_Lot_** | **String** | 30 | **YES** | **`acreage`** (note: String type, trailing underscore literal) |
| X | Double | -- | NO | -- |
| Y | Double | -- | NO | -- |
| DEEDED_AC | String | 25 | NO | -- |
| LATITUDE | Double | -- | NO | -- |
| LONGITUDE | Double | -- | NO | -- |
| PropUseCod | Integer | -- | NO | -- (4-digit DOR code) |
| PropUseDes | String | 75 | NO | -- (DOR description -- see Quirks about `PROP_USE_D` vs `PropUseDes`) |
| **Owners_Nam** | **String** | 254 | **YES** | **`owner_name`** |
| Mailing_Ad | String | 254 | NO | -- (truncated `Mailing_Address`) |
| Mailing__1 | String | 254 | NO | -- (second mailing line) |
| City | String | 254 | NO | -- (owner city) |
| State | String | 254 | NO | -- (owner state) |
| Zip_4 | String | 254 | NO | -- |
| Short_Lega | String | 254 | NO | -- (short legal description) |
| **Physical_A** | **String** | 254 | **YES** | **`site_address`** |
| Physical_C | String | 254 | NO | -- (physical city) |
| Physical_Z | String | 254 | NO | -- (physical zip) |
| DOR_LUC | Integer | -- | NO | -- (DOR Land Use Code) |
| PA_LUC | Integer | -- | NO | -- (Property Appraiser LUC) |
| Roll_Type | String | 254 | NO | -- |
| Roll_Year | Integer | -- | NO | -- |
| Total_JV | Integer | -- | NO | -- (Total Just Value) |
| Land_Val | Integer | -- | NO | -- |
| Homestead | String | 50 | NO | -- |
| Shape | Geometry | -- | YES | `geometry` |
| `Shape.STArea()` | Double | -- | NO | -- |
| `Shape.STLength()` | Double | -- | NO | -- |
| GlobalID | String | 38 | NO | -- |

### On `PROP_USE_D` vs `PropUseDes`

The live layer metadata exposes the column `PropUseDes` (not `PROP_USE_D`) in the `fields` array. Sample rows returned by the `/query` endpoint include BOTH a field `PROP_USE_D` (value `"SINGLE FAMILY"`) and a field `PropUseDes` (with the same value). The seed config (`seed_bi_county_config.py` L420) uses **`PROP_USE_D`**, which corresponds to the sample-row serialization. This is preserved verbatim per the seed -- do NOT switch to `PropUseDes`.

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
OBJECTID:      1
PIN:           D26E013
Owners_Nam:    ALBINI ROBERT & KIM
Physical_A:    1093 REIDVILLE RD
PROP_USE_D:    SINGLE FAMILY
Acres_Lot_:    0.09
Subdivisio:    VOS RICHMOND VILLAS
Short_Lega:    LOT 13 THE VILLAGES OF SUMTER
LATITUDE:      28.89670577
LONGITUDE:     -81.97746702
```

---

## 4. What We Query

### WHERE Clause Pattern

```sql
Owners_Nam LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 1000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | PIN | Mixed alphanumeric (e.g. `"D26E013"`) |
| `owner_name` | Owners_Nam | 254-char String, truncated name |
| `site_address` | Physical_A | Full street (e.g. `"1093 REIDVILLE RD"`); `Physical_C` + `Physical_Z` hold city + zip |
| `use_type` | PROP_USE_D | Description text (e.g. `"SINGLE FAMILY"`) |
| `acreage` | Acres_Lot_ | **String** type (NOT Double). Parse as float downstream. |
| `geometry` | Shape | Polygons |

---

## 6. Diff vs Bay / Okaloosa / Charlotte / Collier (MapServer peers)

| Attribute | Sumter | Bay | Okaloosa | Charlotte | Collier |
|-----------|--------|-----|----------|-----------|---------|
| Host | `gis.sumtercountyfl.gov` | `gis.baycountyfl.gov` | AGOL tenant | `ccgis.charlottecountyfl.gov` | `maps.collierappraiser.com` |
| Service name | **`DevServices_Parcel2`** | `BayView/BayView` | varies | varies | varies |
| Max record count | 1000 | 1000 | 2000 | 2000 | 2000 |
| Parcel field | `PIN` | `A1RENUM` | `PARCEL_NUMBER` | `account_id` | `FOLIO` |
| Owner field | **`Owners_Nam`** (truncated) | `A2OWNAME` | `OWNER_NAME` | `OwnerName1` | `NAME1` |
| Address field | **`Physical_A`** (truncated) | `DSITEADDR` | `SITE_ADDRESS` | `sitestreet` | `SITUS_ADDRESS_1` |
| Use field | **`PROP_USE_D`** (truncated) | `DORAPPDESC` | `PROPERTY_USE` | `StateUseCode` | `USE_CODE` |
| Acreage field | **`Acres_Lot_`** (String, trailing underscore) | `DTAXACRES` (Double) | `ACRES` | `ACREAGE` | `Acreage` |
| Truncated field names | **4 of 5 mapped fields** | 0 | 0 | 0 | 0 |
| Registry entry | **ABSENT** | present (`bay-fl`) | present | present | present |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PIN | Parent parcel | ParentNo |
| Owner | YES | Owners_Nam | Owner mailing address | Mailing_Ad, Mailing__1, City, State, Zip_4 |
| Site address | YES | Physical_A | Physical city / zip | Physical_C, Physical_Z |
| Use | YES | PROP_USE_D | Short code, DOR LUC, PA LUC | PropUseCod, DOR_LUC, PA_LUC |
| Acreage | YES | Acres_Lot_ (String) | Deeded acreage | DEEDED_AC |
| Subdivision | NO | -- | Subdivision name | Subdivisio |
| Legal description | NO | -- | Short legal | Short_Lega |
| Coordinates | NO | -- | Native XY + lat/lon | X, Y, LATITUDE, LONGITUDE |
| Geometry | YES | Shape | GIS-computed area / length | `Shape.STArea()`, `Shape.STLength()` |
| Valuation | NO | -- | Total JV, school / county assessed, land value | Total_JV, School_Ass, County_Ass, Land_Val, AG_Land_JV, AG_Land_As |
| Taxes | NO | -- | County + school tax | County_Tax, School_Tax |
| Homestead | NO | -- | Homestead flag + percent | Homestead, Homestead_, Homestead1 |
| Exemptions / classifications | NO | -- | Classifications, 193.501 exemption | SP_Assess_, JV_193_501, Assess_Val, AG_Classed |
| Historical property flags | NO | -- | Historically commercial / significant | Hist_Com_J, Hist_Com_A, Hist_Sig_J, Hist_Sig_A |
| Building / construction | NO | -- | Years, quality, class, bldg count | EYB, AYB, Improved_Q, Constr_Cla, Number_Bld, Number_Res |
| Roll metadata | NO | -- | Roll type + year | Roll_Type, Roll_Year |
| Market / neighborhood | NO | -- | Market area / neighborhood code | Market_Are, Neighborho, MarketCode, NBHD_CODE |

Of ~101 attribute fields, 5 are mapped (owner, parcel, address, use, acreage) plus geometry.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Layer metadata does not expose a top-level `spatialReference` block in the same way peer services do; the LATITUDE/LONGITUDE columns carry WGS84 values directly. Queries pass `outSR=4326` for consistency with the rest of the pipeline.

### cos^2(lat) Correction

Not triggered for Sumter because `Acres_Lot_` is a (string-serialized) PA-sourced acreage attribute, not `Shape.STArea()`.

---

## 9. Related surfaces (no standalone doc)

- **PT (permits)**: No `pt:` entry in `county-registry.yaml` (no Sumter block at all); no Sumter-specific adapter under `modules/permits/scrapers/adapters/`. Documented inline here.
- **CR (commission)**: See `sumter-county-civicplus.md` for BCC + P&Z on the CivicPlus AgendaCenter; BOA is `manual` and documented in that doc.
- **CD2 (clerk deeds)**: No `cd2:` entry. Documented inline here.

## 10. Known Limitations and Quirks

1. **Four truncated Esri 10-character shapefile field names among the five mapped fields.** Owner = `Owners_Nam` (no trailing `e`), address = `Physical_A` (no trailing `ddress`), use = `PROP_USE_D` (no trailing `escription`), acreage = `Acres_Lot_` (trailing underscore literal). These are legacy shapefile-era truncations and MUST be preserved verbatim. "Correcting" any of them causes queries to fail -- ArcGIS field names are literal strings.

2. **`Acres_Lot_` is a STRING, not a Double.** Sample value is `"0.09"` (quoted). Downstream consumers must `float(value)` / `decimal(...)` rather than treat it as numeric at the source. The Double `Shape.STArea()` is available but represents shape area in the native SRS units, not acres.

3. **Sumter is absent from county-registry.yaml.** (Sumter is ABSENT from `county-registry.yaml`.) No `sumter-fl` block. BI is declared only via `seed_bi_county_config.py` (L415-422). Before running seed/registry workflows, a `sumter-fl` block must be authored.

4. **Service name `DevServices_Parcel2` -- trailing `2`, not `Parcel` or `Parcels`.** The `2` signals this is a second-generation parcel service deployed under the DevelopmentServices service folder. Do NOT assume `DevServices_Parcel` or `Parcels`.

5. **Two apparent "use description" surfaces (`PROP_USE_D` vs `PropUseDes`).** The metadata `fields` array lists `PropUseDes` (String, 75 chars). Sample-row JSON also includes `PROP_USE_D` with the same value. The seed uses `PROP_USE_D` (the shapefile-truncation form). Preserve that choice.

6. **Service name path is `sumtergis/rest/services`, not `arcgis/rest/services`.** Most peers put their ArcGIS services under `/arcgis/`; Sumter uses a custom `/sumtergis/` path on the same server. Copy verbatim from the seed.

7. **Capabilities not declared at the layer level.** The layer-level `capabilities` property is empty in metadata; `Map,Query,Data` is the parent service's advertised capability. Anonymous Query works; Edit/Sync attempts should not be made.

8. **Owner/physical/mailing address fields are all 254 chars.** The source appears to have been migrated from a system with generous 254-character column widths. Practical values are much shorter; downstream systems should not allocate 254-char buffers per record.

9. **Layer `displayField` is `PIN`.** Matches the mapped `parcel_number` surface. Default Esri label workflows will show parcel numbers, not owner names.

10. **Layer type metadata includes ~101 fields spanning parcel, building, land, valuation, exemption, and historical-property attributes.** Most are unmapped. Rich surface for future expansion; mapping more would let downstream analytics query taxes / assessed values / homestead directly.

11. **BOA is `platform: manual`.** Covered in `sumter-county-civicplus.md`. This BI doc is concerned with parcels only.

12. **`LATITUDE` / `LONGITUDE` columns are stored directly on the parcel row** (Double, WGS84). Useful for deterministic centroid extraction without re-projection. Unmapped currently.

**Source of truth:** `seed_bi_county_config.py` (Sumter block, lines 415-422), confirmed absence of a `sumter-fl` block in `county-registry.yaml`, live metadata from `https://gis.sumtercountyfl.gov/sumtergis/rest/services/DevelopmentServices/DevServices_Parcel2/MapServer/0?f=json` (probed 2026-04-14, HTTP 200, ~11.7 KB) and live sample row from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~8.5 KB, including both `PROP_USE_D: "SINGLE FAMILY"` and `Owners_Nam: "ALBINI ROBERT & KIM"`).
