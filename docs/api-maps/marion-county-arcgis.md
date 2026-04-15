# Marion County FL -- ArcGIS Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Enterprise (county-hosted) |
| Service name | `Parcels` (MapServer layer 0) |
| Root URL | `https://gis.marionfl.org/public/rest/services/General/Parcels/MapServer/0` |
| Host | `gis.marionfl.org` (county-hosted) |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | wkid 102659 / latest 2237 (NAD83 HARN StatePlane Florida East FIPS 0901 Feet) |
| Current version | 10.91 |
| Max record count | 2500 |
| Display field | `NAME` |
| Auth | Anonymous |
| Field count | 86 |
| Registry status | `bi: active` per `county-registry.yaml` L201-205 |
| Per-run column mapping | `owner: NAME`, `parcel: PARCEL`, `address: SITUS_1`, `use: FIC`, `acreage: ACRES` |

## 2. Probe (2026-04-14)

```
GET https://gis.marionfl.org/public/rest/services/General/Parcels/MapServer/0?f=json
-> HTTP 200, 11,639 bytes, application/json
   currentVersion=10.91, cimVersion="2.9.0", id=0, name="Parcels",
   type="Feature Layer", geometryType="esriGeometryPolygon",
   maxRecordCount=2500, 86 fields.

GET https://gis.marionfl.org/public/rest/services/General/Parcels/MapServer/0/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 9,114 bytes
   displayFieldName="NAME", one feature returned with all 86 attributes.
```

## 3. Query Capabilities

Standard ArcGIS REST `/query`:

| Parameter | Used | Notes |
|-----------|------|-------|
| `where` | YES | `1=1` for bulk, or owner/parcel filters |
| `outFields` | YES | 5-field narrow subset or `*` |
| `resultRecordCount` | YES | Capped at 2500 |
| `resultOffset` | YES | Pagination cursor |
| `returnGeometry` | Supported | BI engine typically omits geometry |
| `f` | YES | `json` |

**Pagination:** page size 2500 × `resultOffset`. Service returns `exceededTransferLimit: true` when more pages exist.

**Date-range:** not used — parcel service is a snapshot.

## 4. Field Inventory (selected, BI-relevant subset of 86 total)

| Field | Type | Alias | Notes |
|-------|------|-------|-------|
| OBJECTID | OID | OBJECTID | |
| PARCEL | String | PARCEL | **BI mapping: `parcel`** |
| NAME | String | NAME | **displayField, BI mapping: `owner`** |
| SITUS_1 | String | SITUS_1 | **BI mapping: `address`** (site address line 1) |
| FIC | String | FIC | **BI mapping: `use`** (Florida Income Classification use code) |
| ACRES | Double | ACRES | **BI mapping: `acreage`** |
| MAP_NBR | Integer | MAP_NBR | Map/page reference |
| TWP / RGE / SEC | String | -- | PLSS |
| USE_SF | Double | USE_SF | Square footage (living area) |
| STRY | Double | STRY | Stories |
| BLD1_SF | Double | BLD1_SF | Building 1 square footage |
| ASSD_VAL | Double | ASSD_VAL | Assessed value |
| TOT_VAL | Double | TOT_VAL | Total value |
| TOT_LND_VA | Double | TOT_LND_VA | Land value |
| TOT_BLD_VA | Double | TOT_BLD_VA | Building value |
| TOT_TAXES | Double | TOT_TAXES | Tax levy |
| BATHS | Double | BATHS | |
| MILL_GRP | SmallInteger | MILL_GRP | Millage group |
| MO1 / YR1 / Q1 / VI1 / INST1 | mixed | -- | Most-recent sale tuple (month / year / qualification / vacant-improved / instrument) |
| LND1 | String | LND1 | Land-use descriptor |
| GlobalID_1 | GlobalID | GlobalID_1 | |
| SHAPE.STArea() / SHAPE.STLength() | Double | -- | Geometry metrics |

56 additional fields include: additional building characteristics, owner mailing address block, multiple-sale history tuples, and drainage / flood overlays.

## 5. What We Extract / What a Future Adapter Would Capture

Per `county-registry.yaml` L205:

```yaml
fields: { owner: NAME, parcel: PARCEL, address: SITUS_1, use: FIC, acreage: ACRES }
```

| BI canonical | Marion field | Notes |
|--------------|-------------|-------|
| owner | NAME | displayField |
| parcel | PARCEL | |
| address | SITUS_1 | Situs line 1 only; SITUS_2 etc. (if present) not mapped |
| use | FIC | Florida property-appraiser use code |
| acreage | ACRES | Direct double, no conversion |

Sale-history tuples (`MO1 / YR1 / Q1 / VI1 / INST1`) are present but unused by the BI engine.

## 6. Bypass Method / Auth Posture

Anonymous. County-hosted ArcGIS Enterprise — no tokens, no cookies, no CDN layer. Standard `User-Agent` suffices.

## 7. What We Extract vs What's Available

| Category | Extracted | Available | Notes |
|----------|-----------|-----------|-------|
| Owner | YES | YES | NAME |
| Parcel ID | YES | YES | PARCEL |
| Situs address | Line 1 only | SITUS_1 + any SITUS_2 fields | |
| Use code | YES | YES | FIC |
| Acreage | YES | YES | ACRES |
| Most-recent sale | NO | YES | MO1/YR1/Q1/VI1/INST1 tuple |
| Building characteristics (SF, stories, baths) | NO | YES | BLD1_SF, STRY, BATHS |
| Valuation (assessed, total, land, building) | NO | YES | ASSD_VAL, TOT_VAL, TOT_LND_VA, TOT_BLD_VA |
| Tax levy | NO | YES | TOT_TAXES |
| PLSS location (TWP/RGE/SEC) | NO | YES | String fields |
| Geometry | Optional | YES | Polygon |

## 8. Known Limitations and Quirks

1. **`FIC` is the use-code column**, not a generic `USECODE`. Marion exposes the Florida Income Classification code as `FIC` — unique naming within the FL registry.
2. **`NAME` as the owner column is unusual.** Most FL ArcGIS parcel services expose owner via `OWNER_NAME`, `OwnerName`, or `LNAMEOWNER`. Marion uses the bare `NAME` — the parent class BI engine must handle the direct column reference.
3. **`SHAPE.STArea()` / `SHAPE.STLength()` fields appear in the service metadata as typed fields.** They are computed spatial metrics exposed as SQL Server geometry-column derivatives; they pass through ArcGIS JSON unchanged. Do not request them as `outFields` unless needed.
4. **Max record count 2500 (higher than many peers).** Pasco and Volusia cap at 1000–2000; Marion's 2500 means fewer round-trips for full-county pulls.
5. **Service version 10.91 (older ArcGIS Enterprise).** Feature-server-style `returnIdsOnly=true` paging is supported but some newer query features may be absent; stick to classic `resultOffset` pagination.
6. **Spatial Reference wkid 102659 (FL East zone).** Marion is in FL East despite being closer to FL Central geographically — verify reprojection if cross-county layers are being merged.
7. **Sale-history tuples are flattened (`MO1/YR1/...`).** Full deed history is NOT present — only the single most-recent sale. CountyData2 relies on BrowserView (see `marion-county-browserview.md`) for historical deeds.
8. **No `subdivision` column.** Legal-description decomposition (Subdivision, Lot, Block) is not split out on this layer — compare to Volusia which exposes `SUBDIVISION`, `BLOCK`, `LOT` directly.
9. **Host is `gis.marionfl.org`** — a county-owned subdomain, not `services*.arcgis.com`. Downtime risks are county IT rather than Esri cloud.
10. **No obvious confidentiality flag.** The service does not expose a per-row "protected" marker; any restricted addresses are filtered at the source SQL view, not labeled in the wire payload.

Source of truth: `county-registry.yaml` L201-205 (`marion-fl.projects.bi`), live probe of `https://gis.marionfl.org/public/rest/services/General/Parcels/MapServer/0?f=json` (2026-04-14, HTTP 200, 11,639 bytes, 86 fields).
