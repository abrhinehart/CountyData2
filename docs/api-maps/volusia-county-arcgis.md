# Volusia County FL -- ArcGIS Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Enterprise (county-hosted) |
| Service name | `WebDataParcels` (MapServer layer 5 under MapIT) |
| Root URL | `https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer/5` |
| Parent service | `https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer` (layers 0–125 span addresses, highways, parcels, overlays) |
| Host | `maps2.vcgov.org` (Volusia County Government) |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | wkid 2881 (NAD83 HARN StatePlane Florida East FIPS 0901 Feet) |
| Current version | 10.91 (cimVersion 2.9.0) |
| Max record count | 1000 |
| Auth | Anonymous |
| Field count | 80 |
| Registry status | `bi: active` per `county-registry.yaml` L533-541 |

## 2. Probe (2026-04-14)

```
GET https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer/5?f=json
-> HTTP 200, 10,736 bytes, application/json
   currentVersion=10.91, id=5, name="WebDataParcels", type="Feature Layer",
   geometryType="esriGeometryPolygon", sourceSpatialReference.wkid=2881,
   maxRecordCount=1000, 80 fields.

GET https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer/5/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 9,946 bytes
   displayFieldName="PARID", one feature returned with all 80 attributes.

GET https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer?f=json
-> HTTP 200, 6,877 bytes
   MapIT parent service exposes multiple layers (0..125) including
   Address, Parcels, Parcel Text, Pending Parcels, WebDataParcels, etc.
```

## 3. Query Capabilities

Standard ArcGIS REST `/query`:

| Parameter | Used | Notes |
|-----------|------|-------|
| `where` | YES | `1=1` bulk or attribute filters |
| `outFields` | YES | Narrow subset or `*` |
| `resultRecordCount` | YES | Capped at 1000 (half of Hernando/Marion/Pasco) |
| `resultOffset` | YES | Pagination cursor |
| `returnGeometry` | Supported | |
| `f` | YES | `json` |

**Pagination:** page size 1000 × `resultOffset`. Volusia has ~260k parcels; a full sweep needs ~260 paginated calls.

**Date-range:** not used for BI attribute pulls.

## 4. Field Inventory (selected, BI-relevant subset of 80 total)

| Field | Type | Alias | Notes |
|-------|------|-------|-------|
| OBJECTID | OID | | |
| PARID | String | PARID | **displayField — parcel ID** |
| TAXDIST | String | TAXDIST | |
| NBHD / NBHD_DESC | String | | Neighborhood code + description |
| PC / PC_DESC | String | | Property class code + description |
| LEGAL1 / LEGAL2 / LEGAL3 | String | | Free-text legal description, 3 lines |
| ALT_ID | String | | Alternate parcel ID |
| DORPID | String | | FL DOR parcel ID |
| TOWNSHIP / RANGE | String | | PLSS (stored as strings) |
| **SUBDIVISION** | String | SUBDIVISION | **Structured subdivision name — rare among FL ArcGIS parcel services** |
| BLOCK | String | | |
| LOT | String | | |
| MKTAREA | String | | Market area |
| CRA | String | | Community Redevelopment Area flag |
| LANDJUST / IMPRJUST / TOTJUST | Double | | Just values (land / improvement / total) |
| LANDCLASS | Double | | Land class code |
| ADRPRE / ADRDIR / ADRSTR / ADRSUF | String | | Address components (prefix, direction, street, suffix) |
| Shape | Geometry | | |
| Shape.STArea() / STLength() | Double | | Computed |

50 additional fields cover owner mailing address block, homestead flags, multiple sale-history entries, and various overlay district flags.

**BI-registry field mapping gap:** `county-registry.yaml` L533-541 has `bi: active` but does NOT specify the 5-field column mapping inline (same situation as Pasco). Probable mapping based on column shape:

| BI canonical | Volusia field candidate |
|--------------|------------------------|
| owner | (owner column not visible in top 30 fields — likely `OWN1NAME` or `OWNERNAME` farther in the list) |
| parcel | **PARID** (displayField) |
| address | Composed from `ADRPRE` + `ADRDIR` + `ADRSTR` + `ADRSUF`, or a `SITUS` composite field farther in the 80-field list |
| use | PC or PC_DESC |
| acreage | (not observed in first 30; likely `ACRES` or computed from `Shape.STArea()/43560`) |

Final mapping `unverified — needs validation` against `seed_bi_county_config.py`.

## 5. What We Extract / What a Future Adapter Would Capture

**Current state:** registry marks `bi: active` without inline field mapping; defer to seed file. Typical 5-field canonical layout applies once the exact owner / acreage columns are identified on layer 5.

## 6. Bypass Method / Auth Posture

Anonymous. County-hosted ArcGIS Enterprise on `maps2.vcgov.org`. No tokens, no captcha. Standard `User-Agent` suffices.

## 7. What We Extract vs What's Available

| Category | Extracted (assumed) | Available in Layer 5 | Notes |
|----------|---------------------|----------------------|-------|
| Parcel ID | YES | PARID | displayField |
| DOR parcel ID | NO | DORPID | Florida DOR cross-reference |
| Alt ID | NO | ALT_ID | |
| Owner name | Likely YES | Farther in 80-field list | `unverified` — needs seed inspection |
| Situs address | Likely YES (composed) | ADRPRE/ADRDIR/ADRSTR/ADRSUF | Granular parts available |
| Property class | Possibly | PC / PC_DESC | Code + description both present |
| Legal description | NO | LEGAL1/LEGAL2/LEGAL3 | Three-line free text |
| **Structured subdivision** | NO | SUBDIVISION | **Rare: direct structured column** |
| Block / Lot | NO | BLOCK / LOT | Structured components |
| PLSS (Township/Range) | NO | TOWNSHIP / RANGE | Stored as strings |
| Valuations | NO | LANDJUST, IMPRJUST, TOTJUST | Just values only (not assessed or taxable) |
| Tax district / neighborhood / CRA | NO | TAXDIST, NBHD, CRA | |
| Geometry | Optional | YES | Polygon |

## 8. Known Limitations and Quirks

1. **Volusia exposes structured SUBDIVISION, BLOCK, and LOT columns.** Only Hernando's LandmarkWeb exposes Subdivision on the CD2 side; Volusia's GIS layer does it on the BI side. Useful for cross-referencing parcels to platted subdivisions without parsing legal text.
2. **`PARID` as the parcel ID column is unusual.** Most FL ArcGIS services use `PARCEL`, `PARCEL_NUMBER`, or `HPARCEL`. Volusia's `PARID` matches Tyler CAMA convention.
3. **`DORPID` separate from `PARID`.** FL Department of Revenue has a parallel parcel ID system; `DORPID` allows state-level joins.
4. **Max record count 1000 (low).** Volusia's ~260k parcels require ~260 paginated calls vs Marion's ~100 at the same scale.
5. **Spatial Reference wkid 2881.** The `latestWkid` matches `wkid` (both 2881) — the newer ArcGIS style of treating 2881 as canonical. No reprojection needed if consumer uses 2881 directly.
6. **Layer 5 of MapIT MapServer.** The parent MapIT service has ~125 layers. Parcels alone appears under multiple ids: layer 4 ("Parcel Text"), layer 5 ("WebDataParcels"), layer 125 ("Pending Parcels"). Use **layer 5** for canonical parcel geometry + attribute joins.
7. **Address stored in component parts.** `ADRPRE`, `ADRDIR`, `ADRSTR`, `ADRSUF` — concatenate with spaces to get a composed address; no single "SITUS_ADDRESS" column in the first 30 fields.
8. **`LANDJUST / IMPRJUST / TOTJUST` are "just values"** (FL just-value assessment), not taxable values. Separate from assessed/taxable which may be in the other 50 fields.
9. **Host is `maps2.vcgov.org`.** Volusia County Government hosts multiple GIS environments; `maps2` is the publicly-facing instance. `maps.vcgov.org` (no "2") may exist as an internal/legacy URL — do not substitute.
10. **No explicit confidentiality flag visible in the first 30 fields.** Any protected parcels are filtered at the source view; client code does not need per-row filtering logic.

Source of truth: `county-registry.yaml` L533-541 (`volusia-fl.projects.bi`), live probes of `https://maps2.vcgov.org/arcgis/rest/services/MapIT/MapServer/5?f=json` and `.../MapServer?f=json` (2026-04-14, HTTP 200). Final BI 5-field mapping `unverified — needs validation` against `seed_bi_county_config.py` (not inspected in this pass).
