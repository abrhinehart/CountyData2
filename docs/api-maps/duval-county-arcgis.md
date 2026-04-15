# Duval County FL -- ArcGIS Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Enterprise (consolidated Jacksonville, City of Jacksonville IT Department hosted) |
| Service name | `Parcels` (MapServer layer 0 under CityBiz/Parcels) |
| Root URL | `https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0` |
| Parent service | `https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer` |
| Service description | "Duval County Parcels" |
| Host | `maps.coj.net` (City of Jacksonville — consolidated city-county government) |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | wkid 102100 / latest 3857 (WebMercator) |
| Current version | 11.1 (cimVersion 3.1.0) |
| Max record count | Not advertised on layer 0 metadata (fields array is empty in MapServer/0 metadata, but `/query` returns 73 fields + `maxRecordCount` effectively 1000 per observed behaviour) |
| Display field (from query) | `ASH_NAME` |
| Auth | Anonymous |
| Field count | 73 (observed via `/query` response) |
| Registry status | `bi: active` per `county-registry.yaml` L408-415 |

## 2. Probe (2026-04-14)

```
GET https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0?f=json
-> HTTP 200, 11,335 bytes, application/json
   currentVersion=11.1, cimVersion="3.1.0", id=0, name="Parcels",
   type="Feature Layer", geometryType="esriGeometryPolygon",
   sourceSpatialReference.wkid=102100 (WebMercator).
   LABELING: "[STREET_NO]" (labels drawn from STREET_NO column).
   Metadata `fields` array is empty; layer is served as a dynamic layer.

GET https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 8,788 bytes
   displayFieldName="ASH_NAME"
   73 fields returned in response
   Sample row: RE="011550 0000", ACRES=0.51, etc.

GET https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer?f=json
-> HTTP 200, 2,228 bytes
   serviceDescription="Duval County Parcels", layers=[{id:0, name:"Parcels", ...}]
   singleFusedMapCache=false, supportsDynamicLayers=true
   spatialReference wkid=102113 / latestWkid=3785
```

## 3. Query Capabilities

Standard ArcGIS REST `/query` on a dynamic layer:

| Parameter | Used | Notes |
|-----------|------|-------|
| `where` | YES | `1=1` bulk or attribute filters |
| `outFields` | YES | `*` or narrow subset |
| `resultRecordCount` | YES | Server default suggests 1000 |
| `resultOffset` | YES | Pagination cursor |
| `returnGeometry` | Supported | |
| `f` | YES | `json` |

**Pagination:** dynamic layer responds to standard ArcGIS pagination. Duval has ~386k parcels per public-facing stats; plan for multi-page pulls.

**Date-range semantics:** not typically used; parcel service is a snapshot.

## 4. Field Inventory (73 fields observed via `/query`; selection below)

| Field | Type | Notes |
|-------|------|-------|
| OBJECTID | OID | |
| **RE** | String | **Real Estate parcel number — canonical Duval parcel ID (e.g. `"011550 0000"` — includes embedded space)** |
| STREET_NO | String | House number (labeling field) |
| ST_TYPE / ST_DIR / STNM_TYPE / STNM_TYPE2 | String | Address component parts |
| UNIT_NO | String | |
| ADDRCITY | String | Site city |
| LNAMEOWNER | String | Owner long name |
| LONGNAME | String | Composite owner/name |
| MAILADDR1 / MAILADDR2 / MAILADDR3 | String | Mailing address lines |
| MAILCITY / MAILSTATE / MAILZIP | String | Mailing |
| LEGAL1 / LEGAL2 / LEGAL3 / LEGAL4 / LEGAL5 | String | Five-line legal description |
| DESCPU | String | Primary use description |
| PUSE | String | Primary use code |
| ACRES | Double | Acreage |
| ZIPCODE | Integer | Site ZIP (stored as integer — loses leading zeros on some FL ZIPs if they start with 0) |
| SUB_BLK | String | Subdivision/block composite |
| OID_ | Integer | Secondary OID |
| RECORDID | Integer | |
| PARCELTYPE | Integer | |
| X / Y / X_WGS / Y_WGS | Double | Coordinates — two CRS variants |
| FLD_ZONE | String | FEMA flood zone |
| CAMA_VAL | Integer | CAMA valuation |
| SALESLDD / SALESLMM / SALESLYY | SmallInteger | **Last-sale date split into day / month / year fields** |
| WBID | String | Water body identifier |
| ASH_NAME | String | displayField (Ash tree overlay name? — ambiguous; displayField assignment may not reflect typical use) |
| EVAC_TYPE | String | Evacuation zone type |
| APZ | String | Accident Potential Zone (NAS Jacksonville nearby) |
| CVLSUR / CVLSCHZ / MLTSUR / MLTSCHZ | String | Civil / Military surround and school zone |
| OLFLITZ | String | Overlay field |
| ML_NOTICE / CV_NOTICE | String | Military / Civil notice flags |
| AICUZ | String | Air Installation Compatible Use Zone |
| BRF / EMP / ENT | String | Overlay codes |
| LND_LABEL / ZON_LABEL | String | Land use / zoning labels |
| DISTCODE / CODENUM | String | District / code designators |
| BASIN_1 | String | Drainage basin |
| MAP_PNL | String | Map panel number |

Remaining ~13 fields are additional overlay codes, map panel references, and owner-interest sub-fields.

## 5. What We Extract / What a Future Adapter Would Capture

`county-registry.yaml` L413-414 lists `bi: active` but does **not** specify a 5-field column mapping inline (same pattern as Pasco and Volusia). Probable mapping:

| BI canonical | Duval field |
|--------------|-------------|
| owner | LNAMEOWNER (or LONGNAME for composite) |
| parcel | **RE** (Real Estate parcel number — includes space, e.g. `"011550 0000"`) |
| address | Composed from STREET_NO + ST_DIR + ST_TYPE + STNM_TYPE (+ UNIT_NO + ADDRCITY) |
| use | PUSE (code) or DESCPU (description) |
| acreage | ACRES |

`unverified — needs validation` against `seed_bi_county_config.py`.

## 6. Bypass Method / Auth Posture

Anonymous. `maps.coj.net` is operated by the consolidated Jacksonville / Duval IT department. No tokens required.

`www.coj.net/` returned HTTP 503 on the 2026-04-14 probe — the www portal appears to have bot-protection or CDN throttling — but the ArcGIS REST host `maps.coj.net` itself responds cleanly.

## 7. What We Extract vs What's Available

| Category | Extracted (assumed) | Available | Notes |
|----------|---------------------|-----------|-------|
| Parcel ID (RE) | YES | YES | `RE` column, e.g. `"011550 0000"` |
| Owner | YES | YES | LNAMEOWNER, LONGNAME |
| Address | YES (composed) | YES | Granular parts available |
| Use code / description | YES | YES | PUSE / DESCPU |
| Acreage | YES | YES | ACRES |
| Legal description | NO | YES | LEGAL1-LEGAL5 (five-line) |
| Mailing address | NO | YES | MAILADDR1/2/3, MAILCITY/STATE/ZIP |
| CAMA valuation | NO | YES | CAMA_VAL |
| **Last sale date (day/month/year split)** | NO | YES | SALESLDD / SALESLMM / SALESLYY |
| Flood zone | NO | YES | FLD_ZONE |
| Military / Civil overlay zones | NO | YES | Multiple AICUZ/APZ/CV/ML fields |
| Subdivision / block composite | NO | YES | SUB_BLK |
| Geometry | Optional | YES | Polygon in WebMercator (wkid 3857) |

## 8. Known Limitations and Quirks

1. **Layer 0 metadata reports `fields: []`** (empty) even though `/query` returns 73 fields. The layer is served as a "dynamic layer" (`supportsDynamicLayers: true` on parent), which decouples the reported metadata from the runtime field set. Field inventory MUST be derived from a sample `/query?outFields=*` call, not from the MapServer/0 metadata alone.
2. **`RE` is the parcel ID column**, not `PARCEL`. The RE number includes an embedded space (e.g. `"011550 0000"`) — preserve or strip consistently depending on join target.
3. **Sale date is split across three fields** (SALESLDD / SALESLMM / SALESLYY, all SmallInteger). Recompose with `date(2000+SALESLYY, SALESLMM, SALESLDD)` or similar — note that `SALESLYY` is 2-digit year; decade disambiguation needed for pre-2000 sales.
4. **Spatial Reference is WebMercator (wkid 3857 / 102100).** Unusual for FL parcel services (most use wkid 2881/2237); Jacksonville publishes directly in WebMercator, matching the COJ web-map frontend convention.
5. **`ASH_NAME` as displayField is unusual.** Field name suggests "Ash tree overlay" or similar ecological annotation rather than an address/owner display column. This may reflect a dataset-builder choice that emphasizes environmental overlays; BI callers should NOT assume displayField is the canonical render label.
6. **Consolidated city-county.** Duval County and Jacksonville share the same government (consolidated in 1968). Jurisdiction field splits (`ADDRCITY`) differentiate Jacksonville proper from the four small independent municipalities inside Duval (Jacksonville Beach, Neptune Beach, Atlantic Beach, Baldwin).
7. **Heavy military overlay fields.** NAS Jacksonville and NS Mayport drive the APZ / AICUZ / ML_NOTICE / CV_NOTICE / MLTSUR / MLTSCHZ / CVLSUR / CVLSCHZ column family — unique among FL counties in the scope of military-zone overlay columns.
8. **`maps.coj.net` splits services by business area.** `/rest/services/` lists 35 folders (ADARamps, BridgesSufficiency, CityBiz, etc.). Parcels live under `CityBiz`. Other BI-adjacent data (land use, zoning) may live under sibling folders but outside this map's scope.
9. **`www.coj.net/` 503'd** on the 2026-04-14 probe, but `maps.coj.net` responded. Availability monitoring should distinguish the two hosts.
10. **ZIPCODE stored as Integer.** FL ZIPs beginning with 3 always survive integer coercion; any leading-zero ZIPs from non-FL mailing addresses (unusual but possible on owner records) will lose the leading zero.

Source of truth: `county-registry.yaml` L408-415 (`duval-fl.projects.bi`), live probes of `https://maps.coj.net/coj/rest/services/CityBiz/Parcels/MapServer/0?f=json`, `.../MapServer/0/query?...`, `.../MapServer?f=json`, `https://maps.coj.net/coj/rest/services/?f=json` (2026-04-14, HTTP 200). Field inventory harvested via `/query?outFields=*&resultRecordCount=1` since layer metadata is empty on this dynamic layer.
