# Brevard County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted on `gis.brevardfl.gov`) |
| Endpoint | `https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Parcel_New_WKID2881/MapServer/5` |
| Layer Name | Parcel Property (ID 5) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | **WKID 2881 / latestWkid 2881 -- NAD83(HARN) Florida East (ft)** (NOT Web Mercator) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | TaxAcct |
| ObjectId Field | (not declared at layer level; `OBJECTID` field present with indexes `FDO_OBJECTID`, `FDO_Shape`) |
| Capabilities | `Map,Query,Data` |
| Current Version | 10.91 |
| Registry status | **ABSENT -- Brevard is not in `county-registry.yaml` (no `brevard-fl` block)** |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### Brevard field mapping (from `seed_bi_county_config.py` L50-57)

| Purpose | Brevard Field |
|---------|---------------|
| Owner | `OWNER_NAME1` |
| Parcel | `PARCEL_ID` |
| Address | `STREET_NAME` (street name only) |
| Use | `USE_CODE` (code, not description) |
| Acreage | `ACRES` |

---

## 2. State Plane Coordinate System (EPSG:2881)

The service-name literally contains `WKID2881` -- `.../Base_Map/Parcel_New_WKID2881/MapServer/5` -- signaling the native spatial reference is **EPSG:2881 (NAD83/HARN Florida East, US survey feet)**, NOT Web Mercator (WKID 102100 / EPSG:3857). The `extent` block in `?f=json` confirms: `spatialReference: { wkid: 2881, latestWkid: 2881 }`.

Queries MUST explicitly request `outSR=4326` to get WGS84 lat/lon back -- otherwise the server returns coordinates in FL East State Plane feet (very large numeric values, no direct mapping to lat/lon). Writing `outSR=102100` would give Web Mercator, which is also not WGS84.

---

## 3. Query Capabilities

Base query URL:

```
https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Parcel_New_WKID2881/MapServer/5/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNER_NAME1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | **`4326`** | **MANDATORY re-projection from EPSG:2881 to WGS84** |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 | Page size (server max) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

---

## 4. Field Inventory

Complete field catalog from the live `?f=json` response (61 fields):

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| OBJECTID | OID | -- | NO | -- |
| Shape | Geometry | -- | YES | `geometry` |
| TaxAcct | Integer | -- | NO | -- (display field; alias `TaxAcct`, also the layer's `displayField`) |
| Name | String | 125 | NO | -- (alias `PID`) |
| AcreageLot | String | 7 | NO | -- (alias `Acreage Lot`) |
| ParcelType | SmallInteger | -- | NO | -- |
| Descriptn | String | 50 | NO | -- (alias `Description`) |
| OfficialRc | String | 250 | NO | -- (alias `Official Record`) |
| LegStartDt | Date | 8 | NO | -- |
| LegEndDt | Date | 8 | NO | -- |
| ANNO | String | 7 | NO | -- |
| **PARCEL_ID** | **String** | 100 | **YES** | **`parcel_number`** |
| PROPERTY_ID | Integer | -- | NO | -- |
| PLAT_BOOK | String | 20 | NO | -- |
| PLAT_PAGE | String | 20 | NO | -- |
| LEGAL_DESC | String | 2000 | NO | -- |
| **ACRES** | **Double** | -- | **YES** | **`acreage`** |
| BLDG_VALUE | Double | -- | NO | -- |
| LAND_VALUE | Double | -- | NO | -- |
| HOMESTEAD_VALUE | Double | -- | NO | -- |
| OTHER_EXEMPTION_VALUE | Double | -- | NO | -- |
| MILLAGE_CODE | String | 10 | NO | -- |
| **USE_CODE** | **String** | 20 | **YES** | **`use_type`** |
| USE_CODE_DESCRIPTION | String | 100 | NO | -- |
| PARENT_PARCEL_ID | String | 100 | NO | -- |
| CONDO_NUMBER | String | 10 | NO | -- |
| CONDO_NAME | String | 100 | NO | -- |
| LIV_AREA | Integer | -- | NO | -- |
| BLDG2_FLAG | String | 5 | NO | -- |
| BLDG3_FLAG | String | 5 | NO | -- |
| USE_CODE3 | String | 20 | NO | -- |
| EXEMPTION_CODE | String | 50 | NO | -- |
| SOLID_WASTE_UNITS | Single | -- | NO | -- |
| DRAIN_CODE | String | 100 | NO | -- |
| SUBDIVISION_NAME | String | 100 | NO | -- |
| STREET_NUMBER | String | 9 | NO | -- |
| STREET_DIRECTION_PREFIX | String | 9 | NO | -- |
| **STREET_NAME** | **String** | 40 | **YES** | **`site_address`** (street name only) |
| STREET_TYPE | String | 6 | NO | -- |
| CITY | String | 32 | NO | -- |
| STATE | String | 2 | NO | -- |
| ZIP_CODE | String | 10 | NO | -- |
| TOWNSHIP | String | 20 | NO | -- |
| RANGE | String | 20 | NO | -- |
| SECTION | String | 20 | NO | -- |
| SUBDIVISION | String | 2 | NO | -- (note: 2-char code, not name) |
| BLOCK | String | 20 | NO | -- |
| LOT | String | 30 | NO | -- |
| CONDONUMBER | SmallInteger | -- | NO | -- |
| **OWNER_NAME1** | **String** | 255 | **YES** | **`owner_name`** |
| OWNER_NAME2 | String | 255 | NO | -- |
| OWNER_STREET_NAME | String | 255 | NO | -- |
| OWNER_ADDRESS2 | String | 255 | NO | -- |
| OWNER_CITY | String | 50 | NO | -- |
| OWNER_STATE | String | 50 | NO | -- |
| OWNER_ZIP5 | String | 10 | NO | -- |
| OWNER_ZIP4 | String | 10 | NO | -- |
| Shape_Length | Double | -- | NO | -- |
| Shape_Area | Double | -- | NO | -- |
| OWNER_PARCEL_ID | String | 100 | NO | -- |
| OWNER_RENUMBER | Integer | -- | NO | -- |

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
OBJECTID:    1
OWNER_NAME1: WICKS, JOYCE J TRUST
PARCEL_ID:   21 3529-02-*-11
STREET_NAME: DONNA
USE_CODE:    0110
ACRES:       0.19
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
OWNER_NAME1 LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 1000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | PARCEL_ID | Spaced / hyphenated / asterisked format (e.g. `"21 3529-02-*-11"`) |
| `owner_name` | OWNER_NAME1 | `OWNER_NAME2` unmapped |
| `site_address` | STREET_NAME | Street NAME only -- no house number; concatenation required for full street |
| `use_type` | USE_CODE | 4-char code (e.g. `"0110"`); `USE_CODE_DESCRIPTION` has the text |
| `acreage` | ACRES | PA-sourced Double acreage |
| `geometry` | Shape | Polygons (re-projected to WGS84 via `outSR=4326`) |

---

## 7. Diff vs Bay / Okaloosa / Charlotte / Collier (MapServer peers)

| Attribute | Brevard | Bay | Okaloosa | Charlotte | Collier |
|-----------|---------|-----|----------|-----------|---------|
| Host | `gis.brevardfl.gov` | `gis.baycountyfl.gov` | AGOL tenant | `ccgis.charlottecountyfl.gov` | `maps.collierappraiser.com` |
| Service name | **`Parcel_New_WKID2881`** (SRS embedded in name) | `BayView/BayView` | varies | varies | varies |
| Spatial reference | **WKID 2881 / EPSG:2881 (NAD83/HARN Florida East, ft)** | WKID 102660 (StatePlane FL North HARN ft; latestWkid 2238) | 102100 (Web Mercator) | 102100 | 102100 |
| Max record count | 1000 | 1000 | 2000 | 2000 | 2000 |
| Parcel field | `PARCEL_ID` | `A1RENUM` | `PARCEL_NUMBER` | `account_id` | `FOLIO` |
| Owner field | `OWNER_NAME1` | `A2OWNAME` | `OWNER_NAME` | `OwnerName1` | `NAME1` |
| Address field | `STREET_NAME` (street only) | `DSITEADDR` | `SITE_ADDRESS` | `sitestreet` | `SITUS_ADDRESS_1` |
| Use field | `USE_CODE` (code) | `DORAPPDESC` (text) | `PROPERTY_USE` (text) | `StateUseCode` | `USE_CODE` |
| Acreage field | `ACRES` | `DTAXACRES` | `ACRES` | `ACREAGE` | `Acreage` |
| Registry entry | **ABSENT** | present (`bay-fl`) | present | present | present |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PARCEL_ID | Internal property ID, parent parcel | PROPERTY_ID, PARENT_PARCEL_ID |
| Owner | YES | OWNER_NAME1 | Co-owner, owner mailing address | OWNER_NAME2, OWNER_STREET_NAME, OWNER_ADDRESS2, OWNER_CITY, OWNER_STATE, OWNER_ZIP5, OWNER_ZIP4, OWNER_PARCEL_ID, OWNER_RENUMBER |
| Site address (street only) | YES | STREET_NAME | Full structured address | STREET_NUMBER, STREET_DIRECTION_PREFIX, STREET_TYPE, CITY, STATE, ZIP_CODE |
| Legal description | NO | -- | Long legal text | LEGAL_DESC |
| Plat book / page | NO | -- | Plat reference | PLAT_BOOK, PLAT_PAGE |
| Subdivision | NO | -- | Code + name + block + lot | SUBDIVISION (2-char code), SUBDIVISION_NAME, BLOCK, LOT |
| Section/Township/Range | NO | -- | STR references | SECTION, TOWNSHIP, RANGE |
| Condo | NO | -- | Condo references | CONDO_NUMBER, CONDO_NAME, CONDONUMBER |
| Use | YES | USE_CODE | Description, secondary use | USE_CODE_DESCRIPTION, USE_CODE3 |
| Valuation | NO | -- | Building + land + exemptions | BLDG_VALUE, LAND_VALUE, HOMESTEAD_VALUE, OTHER_EXEMPTION_VALUE, EXEMPTION_CODE |
| Millage / drainage / waste | NO | -- | Classification codes | MILLAGE_CODE, DRAIN_CODE, SOLID_WASTE_UNITS |
| Building | NO | -- | Living area, 2nd/3rd building flags | LIV_AREA, BLDG2_FLAG, BLDG3_FLAG |
| Acreage | YES | ACRES | GIS-computed area / perimeter | Shape_Area, Shape_Length, AcreageLot |
| Official record | NO | -- | Deed reference + annotation | OfficialRc, ANNO |
| Descriptive | NO | -- | Description, type, legal start/end dates | Descriptn, ParcelType, LegStartDt, LegEndDt |

Of 61 attribute fields, 5 are mapped (owner, parcel, street, use, acreage) plus geometry.

---

## 9. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is **EPSG:2881 (NAD83/HARN Florida East, US survey feet)** -- NOT Web Mercator. `outSR=4326` causes the server to re-project to WGS84 before returning coordinates.

Do NOT ask for `outSR=102100`; that would give Web Mercator, which is not what this repo uses (WGS84 is the canonical coordinate system for downstream geospatial work).

### cos^2(lat) Correction

Not triggered for Brevard because `ACRES` is a PA-sourced Double acreage attribute, not `Shape_Area`.

---

## 10. Related surfaces (no standalone doc)

- **PT (permits)**: See `brevard-county-accela.md`. The `BOCC` Accela agency code = Brevard (not Escambia). A separate permits doc covers that surface.
- **CR (commission)**: See `brevard-county-legistar.md`. BCC + P&Z on Legistar; BOA is `manual`.
- **CD2 (clerk deeds)**: No `cd2:` entry in the registry (Brevard has no registry block at all). Documented inline here.

## 11. Known Limitations and Quirks

1. **Service name literally contains `WKID2881`.** `.../Base_Map/Parcel_New_WKID2881/MapServer/5`. This is a Brevard convention where the native spatial reference is baked into the service name so consumers cannot miss it. EPSG:2881 = NAD83(HARN) Florida East (US survey feet). Do NOT assume Web Mercator / EPSG:3857 / WKID 102100.

2. **`outSR=4326` is MANDATORY for geographic output.** Omitting `outSR` returns coordinates in Florida East State Plane (feet), which are huge numbers with no direct lat/lon mapping. Always pass `outSR=4326` unless you specifically want State Plane feet.

3. **Brevard is absent from county-registry.yaml.** (Brevard is ABSENT from `county-registry.yaml`.) Grep returns no hits for `brevard-fl` under `counties:`. BI is registered only via `seed_bi_county_config.py` (L50-57). Before running seed/registry workflows, a `brevard-fl` block with `bi.portal: arcgis`, `bi.status: active` must be authored.

4. **Owner name is `OWNER_NAME1` -- with the numeric suffix.** Not `OWNER_NAME`, not `OwnerName`. The `1` suffix is literal. `OWNER_NAME2` holds a second owner and is unmapped.

5. **Use code is the 4-char code (`USE_CODE`), not the description.** A sibling `USE_CODE_DESCRIPTION` field holds the text but is unmapped. Choose one; do not swap the seed mid-flight.

6. **`STREET_NAME` is the street NAME only.** House number is in `STREET_NUMBER`, directional in `STREET_DIRECTION_PREFIX`, suffix in `STREET_TYPE`, locality in `CITY`/`STATE`/`ZIP_CODE`. Downstream geocoding with just `STREET_NAME` will be ambiguous.

7. **ObjectId not declared at the layer level.** Metadata reports `objectIdField: None`, but an `OBJECTID` column exists with indexes `FDO_OBJECTID` and `FDO_Shape` (the `FDO_` prefix is an older Esri File Geodatabase index naming). Esri tooling should detect `OBJECTID` from the field list.

8. **`SUBDIVISION` is a 2-character CODE, not the name.** The full subdivision name lives in `SUBDIVISION_NAME`. Both are unmapped.

9. **Capabilities are `Map,Query,Data` -- read-only.** No `Extract`, no `Sync`, no `Editing`.

10. **Max record count is 1000** -- low for an FL parcel layer. Pagination kicks in sooner than Santa Rosa / Indian River (2000) or Martin (5000).

11. **Sample `PARCEL_ID` format is unusual.** `"21 3529-02-*-11"` -- spaces, dashes, and literal asterisks all appear in the parcel ID. Downstream matching must treat PARCEL_ID as an opaque string, not parse it as a numeric identifier.

12. **`OWNER_STATE` is 50 chars, not 2.** The field is sized to hold the spelled-out state name, not just the USPS abbreviation. The two-letter abbreviation is more common in practice but the column accommodates either.

**Source of truth:** `seed_bi_county_config.py` (Brevard block, lines 50-57), confirmed absence of a `brevard-fl` block in `county-registry.yaml`, live metadata from `https://gis.brevardfl.gov/gissrv/rest/services/Base_Map/Parcel_New_WKID2881/MapServer/5?f=json` (probed 2026-04-14, HTTP 200, ~21.1 KB, 61 fields) and live sample row from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~8.4 KB).
