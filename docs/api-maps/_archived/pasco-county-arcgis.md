# Pasco County FL -- ArcGIS Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Enterprise (county-hosted) |
| Service name | `Parcels` (MapServer layer 7 under PascoMapper/Parcels) |
| Root URL | `https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer/7` |
| Host | `pascogis.pascocountyfl.net` (county-hosted) |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | NAD_1983_HARN_StatePlane_Florida_West_FIPS_0902_Feet (per WKT2 returned) |
| Current version | 11.5 (cimVersion 3.5.0) |
| Max record count | 2000 |
| Display field | `HPARCEL` |
| Auth | Anonymous |
| Field count | 97 |
| Registry status | `bi: active` per `county-registry.yaml` L490-497 |

## 2. Probe (2026-04-14)

```
GET https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer/7?f=json
-> HTTP 200, 19,339 bytes, application/json
   currentVersion=11.5, cimVersion="3.5.0", id=7, name="Parcels",
   type="Feature Layer", geometryType="esriGeometryPolygon",
   maxRecordCount=2000, 97 fields, displayField="HPARCEL".

GET https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer/7/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 30,774 bytes
   displayFieldName="HPARCEL", one feature returned.
```

## 3. Query Capabilities

Standard ArcGIS REST `/query`:

| Parameter | Used | Notes |
|-----------|------|-------|
| `where` | YES | `1=1` bulk or attribute filters |
| `outFields` | YES | Narrow subset or `*` |
| `resultRecordCount` | YES | Capped at 2000 |
| `resultOffset` | YES | Pagination cursor |
| `returnGeometry` | Supported | |
| `f` | YES | `json` |

**Pagination:** page size 2000 × `resultOffset`; service returns `exceededTransferLimit: true` when more pages exist. Pasco has ~300k+ parcels, so plan for ~150 paginated calls per full sweep.

**Date-range:** `CREATE_DATE` field is a Date type — could filter recent parcel creations, but BI engine uses static snapshots.

## 4. Field Inventory (selected, BI-relevant subset of 97 total)

| Field | Type | Alias | Notes |
|-------|------|-------|-------|
| HPARCEL | String | HPARCEL | **displayField — canonical Parcel ID** |
| BLOCK | String | BLOCK | |
| FEMA | String | FEMA | FEMA flood zone |
| FUTURELANDUSE | String | Future Landuse | Alias contains space |
| EVACZONES | String | EVACZONES | |
| COMMISSIONDISTRICT | String | COMMISSIONDISTRICT | BCC district |
| JURISDICTION_NAME | String | JURISDICTION_NAME | Municipality if inside incorporated city |
| ACTUAL_YEAR_BUILT | String | ACTUAL_YEAR_BUILT | Note: stored as STRING not Integer |
| EFFECTIVE_YEAR_BUILT | String | EFFECTIVE_YEAR_BUILT | Same |
| AG_LAND_VALUE | Double | AG_LAND_VALUE | |
| ASSD_VAL_COUNTY | Double | ASSD_VAL_COUNTY | |
| ASSD_VAL_SCHOOL | Double | ASSD_VAL_SCHOOL | |
| BUILDING_REPLACE_VALUE | Double | BUILDING_REPLACE_VALUE | |
| BUILDING_VALUE | Double | BUILDING_VALUE | |
| IMPROVED_VALUE | Double | IMPROVED_VALUE | |
| EXEMPT_AMOUNT_COUNTY / SCHOOL | Double | -- | Homestead exemption amounts |
| EXTRA_FEATURE_VALUE | Double | -- | Pool, dock, etc. |
| GROSS_AREA | Integer | GROSS_AREA | |
| HAS_HOMESTEAD | String | HAS_HOMESTEAD | `"Y"`/`"N"` |
| HAS_POOL | String | HAS_POOL | `"Y"`/`"N"` |
| CREATE_DATE | Date | CREATE_DATE | Parcel creation timestamp |
| CENTROID_X / CENTROID_Y | Double | -- | |
| CENSUS_BLOCK_GROUP / CENSUS_TRACT | String | -- | |
| BENEFITDISTRICTS | String | -- | |
| BLDGINSP | String | BLDGINSP | Building inspector code |
| CODEENFORCEMENT | String | CODEENFORCEMENT | |
| CONNECTEDCITIES | String | -- | |

67 additional fields cover taxing districts, school zones, overlay districts, owner mailing address block, multiple sale-history tuples, land class, etc.

**BI-registry field mapping gap:** `county-registry.yaml` L490-497 has `bi: active` but does NOT currently specify the 5-field mapping (`fields: {...}`) that Hernando/Marion/Polk have. This is a prospective configuration. Likely mapping based on column shape:

| BI canonical | Pasco field candidate |
|--------------|----------------------|
| owner | (not observed in this layer — owner data may be on a joined layer or a sibling service) |
| parcel | **HPARCEL** (displayField) |
| address | (not observed; address may be on a joined layer) |
| use | (not observed; look for `PROPUSE` / `DOR_USE_CODE` on sibling layer) |
| acreage | **GROSS_AREA / 43560** or a dedicated `ACRES` field (not in first 30 columns) |

The BI seed file `seed_bi_county_config.py` should be consulted for Pasco's canonical mapping. `unverified — needs validation` — the specific owner / use-code / address columns may live on a different layer of `PascoMapper` (MapServer exposes many layers; layer 7 is "Parcels" but parcel attributes may be split across several joined feature classes).

## 5. What We Extract / What a Future Adapter Would Capture

**Current state:** registry marks `bi: active` but field mapping is not in the YAML. A future adapter should either:

1. Consult `seed_bi_county_config.py` for Pasco's mapping (likely already present).
2. Enumerate sibling layers at `https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer?f=json` to find owner/address/use-code tables.

## 6. Bypass Method / Auth Posture

Anonymous. County-hosted ArcGIS Enterprise on `pascogis.pascocountyfl.net`. No tokens, no captcha.

## 7. What We Extract vs What's Available

| Category | Extracted | Available in Layer 7 | Notes |
|----------|-----------|----------------------|-------|
| Parcel ID | Likely YES | HPARCEL | displayField |
| Owner | Unknown from layer 7 alone | Probably via sibling layer | `unverified — needs validation` |
| Address | Unknown from layer 7 alone | Probably via sibling layer | `unverified — needs validation` |
| Use code | Unknown from layer 7 alone | Probably via sibling layer | `unverified — needs validation` |
| Acreage | Computable | GROSS_AREA (if SF, divide by 43560) | |
| Building metrics | Available | BUILDING_VALUE, IMPROVED_VALUE, BUILDING_REPLACE_VALUE, GROSS_AREA | |
| Homestead / pool flags | Available | HAS_HOMESTEAD, HAS_POOL | |
| Valuations (county/school/agricultural/improvement) | Available | ASSD_VAL_COUNTY, ASSD_VAL_SCHOOL, AG_LAND_VALUE, IMPROVED_VALUE | |
| FEMA flood / evac zones | Available | FEMA, EVACZONES | |
| Census geography | Available | CENSUS_BLOCK_GROUP, CENSUS_TRACT | |
| Geometry | Optional | YES | Polygon |

## 8. Known Limitations and Quirks

1. **97 fields, 5 canonical columns (owner/parcel/address/use/acreage) not all observable on layer 7.** Layer 7 ("Parcels") in Pasco's MapServer is geometry + valuation / overlays. Owner name and street address likely join from a separate table. Final BI mapping must be verified against the actual seed in `seed_bi_county_config.py` or via live `outFields` probe using the seed column names.
2. **`ACTUAL_YEAR_BUILT` and `EFFECTIVE_YEAR_BUILT` are STRINGS, not integers.** Any numeric comparison on year-built requires `CAST` or Python-side coercion.
3. **`HPARCEL` is the parcel ID column.** Unlike neighbors (`PARCEL`, `PARID`, `PARCEL_NUMBER`) the column is `HPARCEL` — a Pasco-specific convention. Not to be confused with `OBJECTID` (system OID).
4. **Max record count 2000.** Pasco has ~350k parcels; a full sweep requires ~175+ paginated calls.
5. **`FUTURELANDUSE` field alias has a space** (`Future Landuse`). Use the bare column name `FUTURELANDUSE` in `outFields`, not the alias.
6. **Host is county-owned (`pascogis.pascocountyfl.net`).** No Esri-cloud fallback; any ArcGIS Enterprise outage is a Pasco IT issue.
7. **Service URL path includes `giswebs`** not the standard `rest/services` prefix. Full path: `/giswebs/rest/services/PascoMapper/Parcels/MapServer/7`. The `giswebs` segment is a Pasco-specific site instance; do not rewrite.
8. **Spatial Reference uses WKT2 (newer)**, not a bare wkid. `"NAD_1983_HARN_StatePlane_Florida_West_FIPS_0902_Feet"` — reprojection clients must handle either wkid lookup or full WKT parsing.
9. **Pasco registry entry is minimal (`bi: active` only).** Unlike Hernando (which lists the 5-field mapping in-line), Pasco's registry row does not specify the column mapping. Seed file is the source of truth; this doc notes the gap.
10. **Layer index = 7.** The parent MapServer at `/PascoMapper/Parcels/MapServer` exposes multiple layers (see `?f=json` for the list). The "Parcels" layer specifically is layer 7 — verify the layer index if the seed changes. 

Source of truth: `county-registry.yaml` L490-497 (`pasco-fl.projects.bi`), live probe of `https://pascogis.pascocountyfl.net/giswebs/rest/services/PascoMapper/Parcels/MapServer/7?f=json` (2026-04-14, HTTP 200, 19,339 bytes, 97 fields). Final BI 5-field mapping `unverified — needs validation` against `seed_bi_county_config.py` contents (not inspected in this pass).
