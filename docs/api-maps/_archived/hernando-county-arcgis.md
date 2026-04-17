# Hernando County FL -- ArcGIS Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Online (hosted FeatureServer) |
| Service name | `gis.V_PARCELS` (Parcels) |
| Root URL | `https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer/0` |
| Tenant GUID | `x5zvhhxfUuRDntRe` |
| Service Item Id | `50dac409cf664b98aa845d01c9283288` |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | wkid 103023 / latest 6443 (US Feet) |
| Current version | 12 |
| Max record count | 2000 |
| Cache max age | 30 s |
| Display field | `OWNER_NAME` |
| Auth | Anonymous (no token required) |
| Field count | 204 |
| Registry status | `bi: active` per `county-registry.yaml` L175-180 (`hernando-fl.projects.bi`) |
| Per-run column mapping | `owner: OWNER_NAME`, `parcel: PARCEL_NUMBER`, `address: SITUS_ADDRESS`, `use: CER_DOR_CODE`, `acreage: ACRES` |

## 2. Probe (2026-04-14)

```
GET https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer/0?f=json
-> HTTP 200, 47,795 bytes, application/json
   currentVersion=12, id=0, name="gis.V_PARCELS", type="Feature Layer",
   serviceItemId="50dac409cf664b98aa845d01c9283288", maxRecordCount=2000,
   displayField="OWNER_NAME", 204 fields returned.
   Copyright: "Parcel polygons and data obtained from the Hernando County Property Appraiser's office."

GET https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 34,447 bytes
   objectIdFieldName="OBJECTID", geometryType="esriGeometryPolygon",
   spatialReference.wkid=103023, one feature returned with all 204 attributes.

GET https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer?f=json
-> HTTP 200, 3,212 bytes
   serviceDescription: "Parcel polygons and information, excluding protected addresses".
   maxRecordCount=2000. Supports export formats: csv,shapefile,sqlite,geoPackage,
   filegdb,featureCollection,geojson,kml,excel.
```

Protected-address parcels are filtered out of the public view (per `copyrightText`).

## 3. Query Capabilities

The FeatureServer `/query` endpoint supports standard ArcGIS REST parameters:

| Parameter | Used by BI engine | Notes |
|-----------|------------------|-------|
| `where` | YES | Typical usage: `1=1` for bulk, or attribute filters |
| `outFields` | YES | Often `*` for full row, or a narrow column list per `seed_bi_county_config.py` mapping |
| `resultRecordCount` | YES | Page size; capped at 2000 by service `maxRecordCount` |
| `resultOffset` | YES | Cursor for pagination |
| `geometry` / `geometryType` / `spatialRel` | Supported | Not typically used by BI |
| `outSR` | Supported | Default is source CRS (wkid 103023) |
| `returnGeometry` | Supported | BI engine usually passes `false` for attribute-only sweeps |
| `f` | YES | `json` preferred |

**Pagination model:** page size 2000 × `resultOffset`; service returns `exceededTransferLimit: true` when more pages exist.

**Date-range semantics:** not used for BI attribute pulls (dataset is a snapshot, not incremental).

## 4. Field Inventory (partial, BI-relevant subset of 204 total)

| Field | Type | Alias | Notes |
|-------|------|-------|-------|
| PARCEL_KEY | Integer | PARCEL_KEY | Internal surrogate key |
| PARCEL_NUMBER | String | PARCEL_NUMBER | **BI mapping: `parcel`** |
| PARCEL_SHORTNUM | String | PARCEL_SHORTNUM | Short form |
| PARCEL_TYPE | String | PARCEL_TYPE | |
| LOT | String | LOT | Structured legal component |
| BLOCK | String | BLOCK | Structured legal component |
| SECTION | Integer | SECTION | PLSS |
| TOWNSHIP | Integer | TOWNSHIP | PLSS |
| RANGE | Integer | RANGE | PLSS |
| SITUS_ADDRESS | String | SITUS_ADDRESS | **BI mapping: `address`** |
| SITUS_HOUSENO | Integer | SITUS_HOUSENO | |
| SITUS_STREET | String | SITUS_STREET | |
| SITUS_CITY | String | SITUS_CITY | |
| SITUS_ZIP5 | String | SITUS_ZIP5 | |
| LEGAL1 / LEGAL2 / LEGAL3 / LEGAL4 | String | -- | Free-text legal lines |
| OWNER_NAME | String | OWNER_NAME | **displayField, BI mapping: `owner`** (per `county-registry.yaml` L179) |
| CER_DOR_CODE | String | CER_DOR_CODE | **BI mapping: `use` (coerced to string in f259d87)** |
| ACRES | Double | ACRES | **BI mapping: `acreage`** |
| CONFIDENTIAL | String | CONFIDENTIAL | Likely "Y" flag hiding confidential rows; source view already filters protected addresses |
| BUILDING_LEASE | String | BUILDING_LEASE | |
| MINERAL_RIGHTS | String | MINERAL_RIGHTS | |

Full inventory available via `GET /0?f=json`; 204 fields span property appraiser columns (sales, values, building characteristics, PLSS decomposition, extensive `SITUS_*` address components).

## 5. What We Extract / What a Future Adapter Would Capture

The BI engine maps a narrow slice of the full schema. Per `county-registry.yaml` L179:

```yaml
fields: { owner: OWNER_NAME, parcel: PARCEL_NUMBER, address: SITUS_ADDRESS, use: CER_DOR_CODE, acreage: ACRES }
```

| BI canonical | Hernando field | Notes |
|--------------|----------------|-------|
| owner | OWNER_NAME | displayField |
| parcel | PARCEL_NUMBER | Not PARCEL_KEY (internal) |
| address | SITUS_ADDRESS | Already composed; SITUS_* components available if needed |
| use | CER_DOR_CODE | **Integer coercion fix lives in commit `f259d87`** — parcel classifier now coerces to `str` before use-code normalization |
| acreage | ACRES | Double; no unit conversion required (acres on wire) |

## 6. Bypass Method / Auth Posture

Anonymous — ArcGIS Online FeatureServer exposes this view to the public without token or API-key headers. No Cloudflare or captcha interstitials. The standard BI user agent (`CountyData2/bi`) is sufficient.

## 7. What We Extract vs What's Available

| Category | Extracted | Available | Notes |
|----------|-----------|-----------|-------|
| Owner name | YES | YES | OWNER_NAME |
| Parcel ID | YES | YES | PARCEL_NUMBER (plus internal PARCEL_KEY) |
| Situs address | YES (composed) | YES | SITUS_ADDRESS composed; granular parts available |
| Use code | YES | YES | CER_DOR_CODE (integer → coerced to str) |
| Acreage | YES | YES | ACRES |
| Legal description | NO | YES | LEGAL1-LEGAL4 text + structured LOT/BLOCK/SECTION/TOWNSHIP/RANGE |
| Assessed / just / sale values | NO | YES | ~170 other fields include property-appraiser valuation columns |
| Geometry | Optional | YES | Polygon; typically omitted on BI attribute pulls |
| Confidentiality flag | NO | YES | CONFIDENTIAL column (protected rows already filtered server-side) |

## 8. Known Limitations and Quirks

1. **Integer use-code crash fixed in `f259d87`.** Per `county-registry.yaml` L180: "Integer use_type crash fixed in f259d87 — parcel classifier now coerces CER_DOR_CODE to str." The field is dual-typed in practice (number-shaped string); the classifier expects `str`.
2. **204 fields but most BI runs request 5.** The endpoint is wide; only the 5-field mapping under `county-registry.yaml` is used. `outFields=*` doubles payload size with no downstream benefit.
3. **Hernando uniquely has a structured Subdivision column in its deed portal (LandmarkWeb v1.5.87).** This does NOT carry across to ArcGIS — LOT/BLOCK are present on the parcel layer but the Subdivision-name column lives on the Clerk side only. See `hernando-county-landmark.md`.
4. **Protected addresses are pre-filtered.** The source is `gis.V_PARCELS` (a SQL view). Rows marked confidential in the underlying table are excluded. BI runs therefore never return "suppressed" parcels; no filtering logic is needed.
5. **Max record count is 2000.** Pagination required for any bulk pull (Hernando has ~94k taxable parcels). Use `resultOffset` + `resultRecordCount=2000` with `exceededTransferLimit` as the continuation signal.
6. **Spatial Reference is NAD 1983 HARN FL West (wkid 103023 / 6443).** Units are US Feet. Reprojection to WebMercator or WGS84 requires `outSR=3857` or `outSR=4326` at query time.
7. **cacheMaxAge=30.** Downstream caches may hold responses for 30 seconds; do not treat the endpoint as strictly real-time for change detection.
8. **PARCEL_NUMBER vs PARCEL_SHORTNUM vs PARCEL_KEY.** Three related columns; only `PARCEL_NUMBER` matches the public-facing Hernando PIN format and is the correct join key for CD2 deed records.
9. **No dedicated BI adapter file in repo for Hernando.** Config lives via `county-registry.yaml` only; the generic `bi` pipeline (`seed_bi_county_config.py`, field mapping dict) is sufficient.
10. **Endpoint uses ArcGIS Online (services2.arcgis.com), not county-hosted.** Any outage on `services2.arcgis.com` is an Esri-cloud outage, not a Hernando County ops issue.

Source of truth: `county-registry.yaml` L164-190 (`hernando-fl` entry, `projects.bi`), commit `f259d87` ("Integer use_type crash fixed"), live probe of `https://services2.arcgis.com/x5zvhhxfUuRDntRe/arcgis/rest/services/Parcels/FeatureServer/0` (2026-04-14, HTTP 200).
