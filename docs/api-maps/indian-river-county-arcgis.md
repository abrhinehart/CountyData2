# Indian River County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Esri-hosted tenant on `services9.arcgis.com`) |
| Endpoint | `https://services9.arcgis.com/M0DpVhTwTZ42jNsw/arcgis/rest/services/IRCPA_Parcels/FeatureServer/0` |
| Layer Name | IRCGIS_PUB.IRCPA.TaxParcels_SpatialView_FC (database-style name) |
| Service Name | `IRCPA_Parcels` (IRC Property Appraiser parcels) |
| Tenant ID | `M0DpVhTwTZ42jNsw` |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857), latestWkid 3857 |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | OWNER_NAME |
| ObjectId Field | OBJECTID |
| Capabilities | `Query` (read-only) |
| Current Version | 12 |
| Registry status | `bi: active`, `cr: usable_seed` per `county-registry.yaml` L431-442 (`indian-river-fl.projects`) |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### Indian River field mapping (from `seed_bi_county_config.py` L352-359)

| Purpose | Indian River Field |
|---------|---------------------|
| Owner | `OWNER_NAME` |
| Parcel | `PP_PIN` (note the unusual `PP_` prefix) |
| Address | `SITE_ADDR` |
| Use | `DOR_DESC` |
| Acreage | `LAND_ACRES` |

**The parcel field is `PP_PIN`** -- "PP" for Property Parcel (Property Appraiser PIN). This `PP_` prefix is unique among FL counties tracked in this repo. Do NOT normalize to `PIN`, `PARCELNO`, or `PARCEL_ID` -- none of those field names exists on this layer.

---

## 2. Query Capabilities

Base query URL:

```
https://services9.arcgis.com/M0DpVhTwTZ42jNsw/arcgis/rest/services/IRCPA_Parcels/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNER_NAME LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Server advertises `exceededTransferLimit: true` when more rows are available. 2000 is the server max.

---

## 3. Field Inventory

Complete field catalog from the live `?f=json` response (42 fields):

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| OBJECTID | OID | -- | NO | -- |
| NEW_PROP_ID | Integer | -- | NO | -- |
| **PP_PIN** | **String** | 22 | **YES** | **`parcel_number`** |
| **OWNER_NAME** | **String** | 100 | **YES** | **`owner_name`** |
| **SITE_ADDR** | **String** | 50 | **YES** | **`site_address`** |
| PROPUSE_CD | String | 4 | NO | -- (4-char code) |
| **DOR_DESC** | **String** | 255 | **YES** | **`use_type`** |
| LINK_TO_PA | String | 261 | NO | -- |
| AD_FROM | String | 15 | NO | -- |
| AD_PREDIR | String | 10 | NO | -- |
| AD_STNAME | String | 50 | NO | -- |
| AD_UNIT | String | 5 | NO | -- |
| AD_CITY | String | 30 | NO | -- |
| AD_ZIP | String | 10 | NO | -- |
| MILLG_CODE | String | 4 | NO | -- |
| SUBDIV_NME | String | 70 | NO | -- |
| SALE_VI_CD | String | 1 | NO | -- |
| SALE_YEAR | SmallInteger | -- | NO | -- |
| SALE_MONTH | SmallInteger | -- | NO | -- |
| SALE_PRICE | Integer | -- | NO | -- |
| **LAND_ACRES** | **Double** | -- | **YES** | **`acreage`** |
| LAND_VALUE | Integer | -- | NO | -- |
| BLDG_VALUE | Integer | -- | NO | -- |
| MISC_VALUE | Integer | -- | NO | -- |
| CAMA_VALUE | Integer | -- | NO | -- |
| ACT_YEAR | SmallInteger | -- | NO | -- |
| EFF_YEAR | SmallInteger | -- | NO | -- |
| OWN_LNAME | String | 50 | NO | -- |
| OWN_FNAME1 | String | 50 | NO | -- |
| OWN_FNAME2 | String | 50 | NO | -- |
| OWN_ADDR1 | String | 60 | NO | -- |
| OWN_ADDR2 | String | 60 | NO | -- |
| OWN_ADDR3 | String | 60 | NO | -- |
| OWN_CITY | String | 50 | NO | -- |
| OWN_STATE | String | 2 | NO | -- |
| OWN_ZIP | String | 10 | NO | -- |
| TAXES | Double | -- | NO | -- |
| RES_UNITS | String | 4 | NO | -- |
| UPD_DATE | Date | 8 | NO | -- |
| LINK_TO_PA2 | String | 262 | NO | -- |
| Shape__Area | Double | -- | NO | -- |
| Shape__Length | Double | -- | NO | -- |

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
OBJECTID:    1
PP_PIN:      31382500001365000029.0
OWNER_NAME:  FOSTER, DONALD W JR & RACHEL R
SITE_ADDR:   509 JOY HAVEN DR
DOR_DESC:    Single Family-Improved
LAND_ACRES:  0.23
```

---

## 4. What We Query

### WHERE Clause Pattern

```sql
OWNER_NAME LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 2000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | PP_PIN | 22-char string; sample returns a decimal like `31382500001365000029.0` |
| `owner_name` | OWNER_NAME | Full first+last; structured `OWN_LNAME`/`OWN_FNAME1`/`OWN_FNAME2` also exist unmapped |
| `site_address` | SITE_ADDR | Complete street (e.g. `"509 JOY HAVEN DR"`); a structured breakdown lives in `AD_FROM`/`AD_PREDIR`/`AD_STNAME`/`AD_UNIT`/`AD_CITY`/`AD_ZIP` |
| `use_type` | DOR_DESC | Human-readable description (e.g. `"Single Family-Improved"`); the 4-char code is in `PROPUSE_CD` |
| `acreage` | LAND_ACRES | PA-sourced Double acreage |
| `geometry` | Shape | Polygons |

---

## 6. Diff vs Santa Rosa / Okeechobee / Baker / Hendry (ArcGIS Online peers)

| Attribute | Indian River | Santa Rosa | Okeechobee | Baker | Hendry |
|-----------|--------------|------------|------------|-------|--------|
| Services subdomain | `services9.arcgis.com` | `services.arcgis.com` | `services3.arcgis.com` | `services6.arcgis.com` | `services.arcgis.com` |
| Tenant ID | `M0DpVhTwTZ42jNsw` | `Eg4L1xEv2R3abuQd` | `jE4lvuOFtdtz6Lbl` (Tyler) | (varies) | (varies) |
| Service name | **`IRCPA_Parcels`** | `ParcelsOpenData` | `Tyler_Technologies_Display_Map` | varies | varies |
| Parcel field | **`PP_PIN`** | `ParcelDisp` | `ParcelID` | `PARCEL_ID` | `PARCELNO` |
| Owner field | `OWNER_NAME` | `OwnerName` | `Owner1` | `OWNER1` | `OWNER_NAME` |
| Address field | `SITE_ADDR` | `Addr1` | `StreetName` | `SITE_ADDR` | `SITEADDRESS` |
| Use field | `DOR_DESC` (text) | `PRuse` (short code) | (not present) | `DOR_USE_CD` | `DORCODE` |
| Acreage field | `LAND_ACRES` | `CALC_ACRE` | `Acerage` (sic typo) | `ACRES` | `ACRES` |
| Capabilities | `Query` only | `Query,Extract` | `Query,Extract,Sync` | varies | varies |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PP_PIN | Internal property ID | NEW_PROP_ID |
| Owner | YES | OWNER_NAME | Structured owner, mailing | OWN_LNAME, OWN_FNAME1, OWN_FNAME2, OWN_ADDR1/2/3, OWN_CITY, OWN_STATE, OWN_ZIP |
| Site address | YES | SITE_ADDR | Structured components | AD_FROM, AD_PREDIR, AD_STNAME, AD_UNIT, AD_CITY, AD_ZIP |
| Use | YES | DOR_DESC | 4-char use code, millage code | PROPUSE_CD, MILLG_CODE |
| Acreage | YES | LAND_ACRES | GIS-computed area | Shape__Area |
| Subdivision | NO | -- | Subdivision name | SUBDIV_NME |
| Sale history | NO | -- | Year, month, price, valid-invalid code | SALE_YEAR, SALE_MONTH, SALE_PRICE, SALE_VI_CD |
| Values | NO | -- | Land, building, misc, CAMA | LAND_VALUE, BLDG_VALUE, MISC_VALUE, CAMA_VALUE |
| Year built | NO | -- | Actual / effective | ACT_YEAR, EFF_YEAR |
| Taxes | NO | -- | Annual tax bill | TAXES |
| Residential units | NO | -- | -- | RES_UNITS |
| PA deep link | NO | -- | Two link fields | LINK_TO_PA, LINK_TO_PA2 |
| Last update | NO | -- | Date of last parcel edit | UPD_DATE |

Of 42 attribute fields, 5 are mapped (owner, parcel, address, use, acreage) plus geometry.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is WKID 102100 (Web Mercator). We request `outSR=4326`.

### cos^2(lat) Correction

Not triggered for Indian River because `LAND_ACRES` is a PA-sourced Double acreage attribute.

---

## 9. Related surfaces (no standalone doc)

- **PT (permits)**: No `pt:` entry under `indian-river-fl.projects` in `county-registry.yaml`; no Indian-River-specific adapter under `modules/permits/scrapers/adapters/`. Documented inline here.
- **CD2 (clerk deeds)**: No `cd2:` entry in the registry block. Documented inline here.

## 10. Known Limitations and Quirks

1. **Parcel field is `PP_PIN`** -- "PP" stands for Property Parcel (Property Appraiser PIN). The `PP_` prefix is unique to Indian River among FL counties in this repo. Do NOT normalize to `PIN` or `PARCELNO`.

2. **Sample `PP_PIN` values include a trailing `.0`** (e.g. `31382500001365000029.0`). Despite the String field type, values appear to have been numerically rounded at ingest. Downstream normalization should strip the trailing `.0` before matching against clerk-side parcel IDs.

3. **Tenant ID `M0DpVhTwTZ42jNsw` is stable and Esri-hosted.** Treat as an opaque identifier; do not infer semantics from the string. The IRC PA org owns this AGOL tenant.

4. **Capabilities are `Query` only.** No `Extract`, no `Sync`, no `Editing`. Read-only, pagination-only.

5. **Service name `IRCPA_Parcels` (IRC Property Appraiser).** Underlying layer name is a fully-qualified SDE view name `IRCGIS_PUB.IRCPA.TaxParcels_SpatialView_FC` -- leave as-is; do not try to simplify.

6. **CR registry status is `usable_seed`** (preserve verbatim). Per `county-registry.yaml` L439-442, Indian River's CR slot carries `platform: legistar`, `slug: indian-river-county-bcc`, `status: usable_seed`. See `indian-river-county-legistar.md` for the CR detail.

7. **DOR_DESC is text, not a code.** Unlike Martin (`DOR_CODE` numeric Double) or Santa Rosa (`PRuse` short code), Indian River stores the human-readable description directly (e.g. `"Single Family-Improved"`). The 4-char code is in `PROPUSE_CD` -- unmapped.

8. **Two PA deep-link fields (`LINK_TO_PA`, `LINK_TO_PA2`).** Both point into the Property Appraiser's public property card. Unmapped; useful for UI handoff.

9. **Structured owner-name fields exist but are unmapped.** `OWN_LNAME` + `OWN_FNAME1` + `OWN_FNAME2` would allow cleaner matching against ownership records than the concatenated `OWNER_NAME` string.

10. **BOA is `platform: manual`.** Covered in `indian-river-county-legistar.md`. This BI doc is concerned with parcels only.

11. **Max record count is 2000.** Same as Santa Rosa / Okeechobee; higher than Bay / Escambia (1000).

12. **`services9.arcgis.com` subdomain is stable for IRC's tenant.** Do not guess at `services.arcgis.com` (Santa Rosa) or `services3.arcgis.com` (Okeechobee Tyler).

**Source of truth:** `seed_bi_county_config.py` (Indian River block, lines 352-359), `county-registry.yaml` (`indian-river-fl.projects`, L431-442 -- `bi: active`, `cr: usable_seed`), live metadata from `https://services9.arcgis.com/M0DpVhTwTZ42jNsw/arcgis/rest/services/IRCPA_Parcels/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, ~15.5 KB) and live sample from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~7.5 KB).
