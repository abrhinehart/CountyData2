# Hendry County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Esri-hosted tenant) |
| Endpoint | `https://services7.arcgis.com/8l7Qq5t0CPLAJwJK/arcgis/rest/services/Hendry_County_Parcels/FeatureServer/0` |
| Layer Name | BaseMap (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 2881 / latestWkid 2881 (NAD_1983_HARN_Florida_GDL_Albers) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | `OWNAME` |
| ObjectId Field | `FID` |
| Capabilities | `Query` |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** (seeded only via `seed_bi_county_config.py` L121-129) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Hendry field mapping (from `seed_bi_county_config.py` L121-129)

| Purpose | Hendry Field |
|---------|--------------|
| Owner | `OWNAME` |
| Parcel | `PARCELNO` |
| Address | `LOCADD` |
| Use | **`None`** (no use field) |
| Acreage | **`None`** (no acreage field) |

**Most constrained FL county in the repo.** Hendry is the ONLY FL entry in `seed_bi_county_config.py` with BOTH `gis_use_field: None` AND `gis_acreage_field: None`. The Hendry layer has 9 total fields and does not expose a DOR use code, a use description, OR a pre-computed acreage column -- only geometry, identifiers, address, owner, and lat/lon.

---

## 2. Absence of Other Surfaces

Hendry is a BI-only county in the seed list; there is no entry in `county-registry.yaml` for Hendry at all.

| Project | State | Reason |
|---------|-------|--------|
| `bi` | Seeded (this doc) | `seed_bi_county_config.py` L121-129 |
| `cd2` | **No surface documented** | No LandmarkWeb / AcclaimWeb / Tyler Self-Service / BrowserView config |
| `pt` | **No surface documented** | No permit adapter, no `modules/permits/...` entry |
| `cr` | **No surface documented** | No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/` |

---

## 3. Query Capabilities

Base query URL:

```
https://services7.arcgis.com/8l7Qq5t0CPLAJwJK/arcgis/rest/services/Hendry_County_Parcels/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNAME LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All 9 fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from NAD83 HARN Albers to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size (matches server max) |
| `f` | YES | `json` | Response format |

---

## 4. Field Inventory

Complete field catalog from live `?f=json` -- only 9 fields total:

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| FID | OID | FID | -- | NO | -- |
| **PARCELNO** | **String** | PARCELNO | 26 | **YES** | **`parcel_number`** |
| PROP_ID | Double | PROP_ID | -- | NO | Numeric property ID |
| **LOCADD** | **String** | LOCADD | 254 | **YES** | **`site_address`** |
| **OWNAME** | **String** | OWNAME | 254 | **YES** | **`owner_name`** |
| LAT | Single | LAT | -- | NO | PA-computed centroid latitude |
| LON | Single | LON | -- | NO | PA-computed centroid longitude |
| Shape__Area | Double | Shape__Area | -- | NO | GIS-computed area (unused) |
| Shape__Length | Double | Shape__Length | -- | NO | GIS-computed perimeter |

**No use / DOR code column. No acreage column. No subdivision, lot, block, legal, valuation, sale, or audit columns.** The Hendry layer is effectively a minimal owner-search surface.

### Sample row (live 2026-04-14)

```
PARCELNO:  1 30 44 04 010 0009-002.2
OWNAME:    KEITH JERRY
LOCADD:    SEARS RD
Shape__Area: 580900.0061950684
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
OWNAME LIKE '%BUILDER NAME%'
```

### Batching Rules

2000-char WHERE cap.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PARCELNO | Space-delimited section/township/range (e.g., `1 30 44 04 010 0009-002.2`) |
| `owner_name` | OWNAME | Surname-first convention (e.g., `KEITH JERRY`) |
| `site_address` | LOCADD | Often street-only (e.g., `SEARS RD`) without house number |
| `use_type` | -- | **NO use field in this schema** (`gis_use_field: None`) |
| `acreage` | -- | **NO acreage field in this schema** (`gis_acreage_field: None`) |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Baker (shapefile-truncated peer) and Okeechobee (String-acreage peer)

All three counties are AGO-hosted FeatureServers but differ in how much they expose:

| Attribute | Hendry | Baker | Okeechobee |
|-----------|--------|-------|------------|
| Tenant ID | `8l7Qq5t0CPLAJwJK` | `HSWu3dhzHf7nZfIa` | `jE4lvuOFtdtz6Lbl` (Tyler Technologies) |
| Field count | **9 (minimal)** | 53 | 27 |
| Use field | **None** (`gis_use_field: None`) | `Use_Descri` (10-char truncated) | None (`gis_use_field: None`) |
| Acreage field | **None** (`gis_acreage_field: None`) | `GIS_Acreag` (Double, 10-char truncated) | `Acerage` sic (String) |
| Owner field | `OWNAME` | `Owner` | `Owner1` |
| ObjectId | `FID` | `FID` | `OBJECTID` |
| SRS | WKID 2881 (FL Albers) | WKID 102100 (Web Mercator) | WKID 102100 (Web Mercator) |
| Max record count | 2000 | 2000 | 2000 |
| Capabilities | `Query` | `Query` | `Query,Extract,Sync` |
| Lat/Lon pre-computed | YES (LAT/LON singles) | NO | NO |
| Registry entry | ABSENT | ABSENT | `bi: active` |

Hendry stands alone as the only FL county in the repo with BOTH use and acreage unavailable. Okeechobee has acreage (as a String typo `Acerage`) but no use code; Hendry has neither.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion.

### Coordinate Re-projection

Source SRS is NAD 1983 HARN Florida GDL Albers (WKID 2881) -- a statewide equal-area projection specific to Florida. Request `outSR=4326` for WGS84 re-projection. NAD83 Albers is unusual for parcel data (most FL counties use Web Mercator or StatePlane); this affects any direct coordinate arithmetic.

### cos²(lat) Correction

Not applicable. Since `gis_acreage_field: None`, no acreage is ever produced. If a future consumer wants to derive acreage from `Shape__Area`, the calculation depends on the Albers units (the projection is equal-area in square METERS -- divide by 4046.86 to get acres, no cos²(lat) correction needed because Albers is equal-area).

---

## 9. Known Limitations and Quirks

1. **`gis_use_field: None` AND `gis_acreage_field: None` -- the most constrained FL county in the seed list.** Hendry is the ONLY FL entry in `seed_bi_county_config.py` where BOTH the use and acreage fields are explicitly set to `None`. Downstream consumers expecting use-classification or acreage data must skip Hendry or derive acreage from `Shape__Area` (Albers sq meters).

2. **Only 9 fields total.** The Hendry layer exposes `FID`, `PARCELNO`, `PROP_ID`, `LOCADD`, `OWNAME`, `LAT`, `LON`, `Shape__Area`, `Shape__Length`. That's it. No valuations, no exemptions, no building attributes, no legal description, no subdivision, no lot/block, no sale history, no audit timestamps. Leanest schema in the repo.

3. **Parcel format is space-delimited, not dash-delimited.** Sample: `1 30 44 04 010 0009-002.2` -- spaces separating section/township/range/plat fields, with a dash only before the final sub-parcel qualifier. LIKE queries against `PARCELNO` must be space-aware.

4. **`LOCADD` is often street-only.** Sample returned `LOCADD = 'SEARS RD'` -- the street name without a house number, direction, or suffix. Many rural parcels do not have civic addresses. Downstream geocoding will fail for a meaningful fraction of rows.

5. **`LAT` and `LON` are `Single` (float32), not Double.** Hendry publishes pre-computed centroid coordinates on every row but uses float32 precision. Sufficient for map pins (~1-meter accuracy) but insufficient for survey-grade work. Not mapped.

6. **`OWNAME` is surname-first.** Sample: `KEITH JERRY` (first-name is `JERRY`). Alias-matching logic should handle surname-first order or use wildcard substring matching.

7. **SRS is NAD83 HARN FL Albers (WKID 2881), not Web Mercator.** Unusual for parcel data. `outSR=4326` re-projects server-side to WGS84. Direct coordinate arithmetic on the native Albers coordinates requires GDAL/PROJ.

8. **Tenant ID `8l7Qq5t0CPLAJwJK` is the Hendry PA's AGO org.** Esri-hosted; not county-hosted. Refresh cadence controlled by the PA's open-data publishing schedule.

9. **Registry absence.** Hendry is not in `county-registry.yaml`. Cross-project tooling reading the registry will skip Hendry entirely.

10. **BI-only county in the repo.** No CR YAML, no CD2 surface, no PT adapter. Documented absences below.

11. **Capabilities limited to `Query`.** No `Extract`, no `Sync`, no `Map`. Bulk export would require paginated queries.

12. **`PROP_ID` is a Double numeric, unused.** An alternate internal identifier (likely the legacy CAMA ROWID). Not mapped; `PARCELNO` is the human-readable parcel key.

### Related surfaces not yet documented

- **Hendry PT:** No permit adapter exists for Hendry.
- **Hendry CR:** No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/`.
- **Hendry CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES`.

**Source of truth:** `seed_bi_county_config.py` (Hendry block, lines 121-129), absence from `county-registry.yaml`, live metadata from `https://services7.arcgis.com/8l7Qq5t0CPLAJwJK/arcgis/rest/services/Hendry_County_Parcels/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, 9.2 KB; one-row query HTTP 200, 1.9 KB)
