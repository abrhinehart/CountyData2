# Martin County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted on `geoweb.martin.fl.us`) |
| Endpoint | `https://geoweb.martin.fl.us/arcgis/rest/services/Administrative_Areas/base_map/MapServer/10` |
| Layer Name | Parcel Polygons (ID 10) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857), latestWkid 3857 |
| Max Record Count | 5000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | PCN |
| ObjectId Field | (not declared at layer level; OBJECTID field is present with alias `ESRI_OID`) |
| Capabilities | `Map,Query,Data` |
| Current Version | ArcGIS Server 11.5 |
| Registry status | **ABSENT -- Martin is not in `county-registry.yaml` (no `martin-fl` block at all)** |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### Martin field mapping (from `seed_bi_county_config.py` L361-368)

| Purpose | Martin Field |
|---------|--------------|
| Owner | `OWNER` |
| Parcel | `PCN` (Property Control Number, NOT `PARCELNO`/`PARCEL_ID`) |
| Address | `SITUS_STREET` (street name only; no house number) |
| Use | `DOR_CODE` |
| Acreage | `AREA_ACRES` |

**PCN is Martin's canonical parcel-number field.** "Property Control Number" is the FL-standard 18-digit/dashed identifier, and Martin names the column `PCN` directly. Do NOT use `PARCELNO` or `PARCEL_ID` -- neither exists on this layer. `ACCOUNT` is a separate internal integer ID.

---

## 2. Query Capabilities

Base query URL:

```
https://geoweb.martin.fl.us/arcgis/rest/services/Administrative_Areas/base_map/MapServer/10/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNER LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 5000 | Page size (server max, unusually high) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Server advertises `exceededTransferLimit: true` when more rows are available. 5000 max-record-count is high for an FL parcel layer -- most peers cap at 1000-2000.

---

## 3. Field Inventory

Complete field catalog from the live `?f=json` response (29 fields):

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| **PCN** | **String** | 30 | **YES** | **`parcel_number`** |
| **OWNER** | **String** | 300 | **YES** | **`owner_name`** |
| MAIL_ADDRESS | String | 100 | NO | -- (owner mailing) |
| MAIL_CITY | String | 30 | NO | -- |
| MAIL_STATE | String | 3 | NO | -- |
| MAIL_ZIP | String | 10 | NO | -- |
| SITUS_HOUSE_ | String | 10 | NO | -- (house number; trailing underscore is literal) |
| SITUS_PREFIX | String | 2 | NO | -- (e.g. `N`, `S`) |
| **SITUS_STREET** | **String** | 40 | **YES** | **`site_address`** (street-name only) |
| SITUS_STREET_TYPE | String | 4 | NO | -- (e.g. `DR`, `ST`) |
| SITUS_POST_DIR | String | 2 | NO | -- (post-directional) |
| SITUS_SUITE | String | 10 | NO | -- |
| SITUS_CITY | String | 40 | NO | -- |
| SITUS_STATE | String | 2 | NO | -- |
| SITUS_ZIP | String | 10 | NO | -- |
| ACCOUNT | Integer | -- | NO | -- |
| **DOR_CODE** | **Double** | -- | **YES** | **`use_type`** (numeric code, e.g. `101.0`) |
| FEATURECODE | Integer | -- | NO | -- |
| LAST_REVISION | Date | 8 | NO | -- |
| **AREA_ACRES** | **Double** | -- | **YES** | **`acreage`** |
| AIN | Integer | -- | NO | -- (Assessor ID Number) |
| SHAPE | Geometry | -- | YES | `geometry` |
| OBJECTID | OID (alias `ESRI_OID`) | -- | NO | -- |
| BOOK | String | 20 | NO | -- (deed book) |
| PAGE | String | 20 | NO | -- (deed page) |
| TAX_DISTRICT_CODE | String | 20 | NO | -- |
| TAX_DISTRICT_DESC | String | 100 | NO | -- |
| SHAPE.AREA | Double | -- | NO | -- (GIS-computed) |
| SHAPE.LEN | Double | -- | NO | -- (GIS-computed) |

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
OBJECTID:     168350138
PCN:          013839001000002904
OWNER:        ELAINE A PEARSON LIVING TRUST
SITUS_STREET: STONES THROW
DOR_CODE:     101.0
AREA_ACRES:   0.54
```

---

## 4. What We Query

### WHERE Clause Pattern

```sql
OWNER LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 5000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | PCN | 18-digit, e.g. `013839001000002904` |
| `owner_name` | OWNER | Trailing whitespace observed (e.g. `"ELAINE A PEARSON LIVING TRUST "`) |
| `site_address` | SITUS_STREET | Street NAME only -- no house number, no prefix/type/post-dir. Reassembling a mailable street address requires concatenating `SITUS_HOUSE_` + `SITUS_PREFIX` + `SITUS_STREET` + `SITUS_STREET_TYPE` + `SITUS_POST_DIR` (+ `SITUS_SUITE`) |
| `use_type` | DOR_CODE | Double numeric DOR code (e.g. `101.0`), NOT a description |
| `acreage` | AREA_ACRES | Double, PA-sourced |
| `geometry` | SHAPE | Polygons |

---

## 6. Diff vs Bay / Okaloosa / Charlotte / Collier (MapServer peers)

| Attribute | Martin | Bay | Okaloosa | Charlotte | Collier |
|-----------|--------|-----|----------|-----------|---------|
| Host | `geoweb.martin.fl.us` | `gis.baycountyfl.gov` | `services.arcgis.com` (AGOL tenant) | `ccgis.charlottecountyfl.gov` | `maps.collierappraiser.com` |
| Service type | MapServer | MapServer | FeatureServer | MapServer | MapServer |
| Layer ID | 10 | 2 | 0 | (varies) | (varies) |
| Max record count | **5000** (unusual) | 1000 | 2000 | 2000 | 2000 |
| Parcel field | **`PCN`** | `A1RENUM` | `PARCEL_NUMBER` | `account_id` | `FOLIO` |
| Owner field | `OWNER` | `A2OWNAME` | `OWNER_NAME` | `OwnerName1` | `NAME1` |
| Address field | **`SITUS_STREET`** (street name only) | `DSITEADDR` | `SITE_ADDRESS` | `sitestreet` | `SITUS_ADDRESS_1` |
| Use field | **`DOR_CODE`** (numeric Double) | `DORAPPDESC` (text) | `PROPERTY_USE` (text) | `StateUseCode` | `USE_CODE` |
| Acreage field | `AREA_ACRES` | `DTAXACRES` | `ACRES` | `ACREAGE` | `Acreage` |
| Spatial reference | WKID 102100 Web Mercator | WKID 102660 StatePlane FL North ft | 102100 | 102100 | 102100 |
| Registry entry | **ABSENT** | `bay-fl.projects.bi active` | `okaloosa-fl` active | `charlotte-fl` active | `collier-fl` active |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|--------|-----------------------------|--------|
| Parcel ID | YES | PCN | Internal account / AIN | ACCOUNT, AIN |
| Owner | YES | OWNER | Owner mailing address | MAIL_ADDRESS, MAIL_CITY, MAIL_STATE, MAIL_ZIP |
| Site address (street only) | YES | SITUS_STREET | Full street: house#, prefix, type, post-dir, suite, city, state, zip | SITUS_HOUSE_, SITUS_PREFIX, SITUS_STREET_TYPE, SITUS_POST_DIR, SITUS_SUITE, SITUS_CITY, SITUS_STATE, SITUS_ZIP |
| Use code | YES | DOR_CODE (numeric) | -- | -- (no description field on this layer) |
| Feature code | NO | -- | Internal feature code | FEATURECODE |
| Acreage | YES | AREA_ACRES | GIS-computed area / perimeter | SHAPE.AREA, SHAPE.LEN |
| Geometry | YES | SHAPE | -- | -- |
| Last revision | NO | -- | Date of last parcel edit | LAST_REVISION |
| Deed reference | NO | -- | Book + page | BOOK, PAGE |
| Tax district | NO | -- | Code + description | TAX_DISTRICT_CODE, TAX_DISTRICT_DESC |

Of 29 attribute fields, 5 are mapped (parcel, owner, street, use, acreage) plus geometry.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is WKID 102100 (Web Mercator). We request `outSR=4326` so the server re-projects to WGS84 before returning coordinates.

### cos^2(lat) Correction

Not triggered for Martin because `AREA_ACRES` is a PA-sourced Double acreage attribute.

---

## 9. Related surfaces (no standalone doc)

- **PT (permits)**: Martin is not on the permits side of this repo -- there is no `martin_county.py` adapter under `modules/permits/scrapers/adapters/` and no `pt:` entry (Martin has no entry at all in `county-registry.yaml`). No Martin permits API map doc is produced.
- **CD2 (clerk deeds)**: No `cd2:` entry (no Martin entry anywhere in the registry); documented inline here rather than as a separate doc.

## 10. Known Limitations and Quirks

1. **Martin is absent from county-registry.yaml.** (Martin is ABSENT from `county-registry.yaml`.) Grep for `martin-fl` or `"Martin County"` under `counties:` returns no hits. The seed config in `seed_bi_county_config.py` (L361-368) is the only repo-level declaration of Martin's BI surface. Before running the seeder against production, a `martin-fl` block must be added to the registry.

2. **Parcel field is `PCN`, not `PARCELNO` / `PARCEL_ID`.** PCN = Property Control Number (the Florida DOR's 18-digit nomenclature). Do NOT "normalize" to `PARCELNO`; that field does not exist on this layer.

3. **`SITUS_STREET` is the street name only -- no house number.** The 40-character field holds just the street name (e.g. `"STONES THROW"`). To assemble a full street address, concatenate `SITUS_HOUSE_` (note the trailing underscore in the field name) + `SITUS_PREFIX` + `SITUS_STREET` + `SITUS_STREET_TYPE` + `SITUS_POST_DIR`, with `SITUS_SUITE` for units. Geocoding with just `SITUS_STREET` will often be ambiguous.

4. **Use code is numeric (`DOR_CODE` as Double), not a description.** Unlike Bay (`DORAPPDESC`, text) or Okaloosa (`PROPERTY_USE`, text), Martin's `DOR_CODE` is a floating-point number (e.g. `101.0`). Translating to a human-readable description requires a lookup against the FL DOR code table; this layer does not carry the text.

5. **Max record count is 5000.** Unusually high for an FL parcel layer. Pagination is rare unless a wide `LIKE '%...%'` hits tens of thousands of parcels.

6. **`SHAPE.AREA` / `SHAPE.LEN` are SQL Server geometry columns** (note the period in the field name, not `Shape__Area`). These names are SQL Server `geometry` type calculated columns and must be quoted/escaped in some client tooling. They are unmapped here; `AREA_ACRES` is authoritative.

7. **ObjectId at the layer level is declared `None` in metadata**, but an `OBJECTID` column exists in the field list with alias `ESRI_OID`. Esri tooling that queries the layer `objectIdField` property must fall back to detecting `OBJECTID` in the field list.

8. **Host is `geoweb.martin.fl.us` (county-hosted, with the `.fl.us` TLD).** Do NOT confuse with `martinfl.gov` (Martin County main website) or `martin.legistar.com` (commission agendas -- see `martin-county-legistar.md`).

9. **LPA, not P&Z.** Martin uses the Local Planning Agency (LPA) model -- see `martin-county-legistar.md`. The BI layer has no per-body filter; parcels are county-wide.

10. **BOA is `platform: manual`.** Covered in `martin-county-legistar.md`. This BI doc is concerned with parcels only.

11. **Capabilities are `Map,Query,Data` -- no `Extract`, no `Sync`, no `Editing`.** Read-only MapServer; bulk Extract is not available.

12. **Owner names carry trailing whitespace.** Example: `"ELAINE A PEARSON LIVING TRUST "` (space before the closing quote). Alias matching with `LIKE '%...%'` should trim / normalize.

**Source of truth:** `seed_bi_county_config.py` (Martin block, lines 361-368), confirmed absence of a `martin-fl` block in `county-registry.yaml`, live metadata from `https://geoweb.martin.fl.us/arcgis/rest/services/Administrative_Areas/base_map/MapServer/10?f=json` (probed 2026-04-14, HTTP 200, ~6.6 KB) and live sample row from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~4.3 KB).
