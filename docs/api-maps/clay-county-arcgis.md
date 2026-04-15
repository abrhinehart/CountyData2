# Clay County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server FeatureServer (county-hosted) |
| Endpoint | `https://maps.claycountygov.com/server/rest/services/Parcel/FeatureServer/0` |
| Layer Name | Parcel Data (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 / latestWkid 3857 (Web Mercator) |
| Max Record Count | **200000** (highest of any FL county in this doc set) |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Export Formats | (FeatureServer; supports Extract) |
| Display Field | Name |
| ObjectId Field | OBJECTID |
| Capabilities | `Query,Extract` |
| Registry status | **Not listed in `county-registry.yaml`** (BI-only county; no CD2 / PT / CR surfaces) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Clay field mapping (from `seed_bi_county_config.py` L58-66)

| Purpose | Clay Field |
|--------|------------|
| Owner | `Name` |
| Parcel | `PIN` |
| Address | `StreetName` |
| Use | `Usedesc` |
| Acreage | `GISACRES` |

**Note on field naming:** Clay's field names mix case inconsistently (`Name`, `PIN`, `StreetName`, `Usedesc`, `GISACRES`). The alias for `Name` is `Owner Name`, for `Usedesc` is `UseDesc`, and for `GISACRES` is `GISACRES`. Field names, not aliases, are what queries must reference.

---

## 2. Absence of Other Surfaces

Clay is a BI-only county in this registry. There is no entry in `county-registry.yaml` for Clay. Consequently:

| Project | State | Reason |
|---------|-------|--------|
| `bi` | Seeded (this doc) | `seed_bi_county_config.py` L58-66 |
| `cd2` | **No surface documented** | No LandmarkWeb / AcclaimWeb / Tyler Self-Service config for Clay |
| `pt` | **No surface documented** | No permit adapter under `modules/permits/scrapers/adapters/` for Clay |
| `cr` | **No surface documented** | No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/` for Clay |

---

## 3. Query Capabilities

Base query URL:

```
https://maps.claycountygov.com/server/rest/services/Parcel/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `Name LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 200000 (server max) | Unusually large page size (see Quirks) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (28 fields):

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| OBJECTID | OID | OBJECTID | NO | -- |
| PIN | String | PIN | **YES** | `parcel_number` (via seed) |
| **Name** | **String** | Owner Name | **YES** | **`owner_name`** |
| ParcelDisp | String | Parcel | NO | (display-formatted parcel; unmapped) |
| HouseNo | String | HouseNo | NO | -- |
| HouseNoSuffix | String | HouseNoSuffix | NO | -- |
| **StreetName** | **String** | StreetName | **YES** | **`site_address`** |
| StreetDir | String | StreetDir | NO | -- |
| StreetMd | String | StreetMd | NO | -- |
| StreetUnit | String | StreetUnit | NO | -- |
| StreetCity | String | StreetCity | NO | -- |
| StreetZip5 | String | StreetZip5 | NO | -- |
| Streetzip4 | String | Streetzip4 | NO | (note: lowercase 'z' in field) |
| **Usedesc** | **String** | UseDesc | **YES** | **`use_type`** |
| TaxDistCode | String | TaxDistCode | NO | -- |
| LegalLines1 | String | LegalLines1 | NO | -- |
| LegalLines2 | String | LegalLines2 | NO | -- |
| LegalLines3 | String | LegalLines3 | NO | -- |
| Address1 | String | MailingAddress1 | NO | (mailing) |
| Address2 | String | MailingAddress2 | NO | (mailing) |
| Address3 | String | MailingAddress3 | NO | (mailing) |
| City | String | MailingCity | NO | -- |
| StateProvince | String | MailingStateProvince | NO | -- |
| ZipCode | String | MailingZipCode | NO | -- |
| Country | String | MailingCountry | NO | -- |
| MailZip | String | MailZip5 | NO | (redundant with ZipCode) |
| **GISACRES** | **Double** | GISACRES | **YES** | **`acreage`** |
| Facility_Name | String | Facility_Name | NO | -- |

---

## 5. What We Query

### WHERE Clause Pattern

```sql
Name LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases. Single quotes doubled.

### Batching Rules

2000-char WHERE cap.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PIN | (not ParcelDisp, which is the display form) |
| `owner_name` | Name | alias "Owner Name" |
| `site_address` | StreetName | Street name only (no number, direction, unit, city, zip) |
| `use_type` | Usedesc | Description string |
| `acreage` | GISACRES | Double; GIS-computed |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Okaloosa / Bay (MapServer counties) and Baker (AGO peer)

Clay's `/FeatureServer/0` endpoint differs structurally from both the MapServer-based Okaloosa and the AGO-hosted Baker. Critical: do **NOT** substitute Okaloosa's MapServer URL style into a Clay config.

| Attribute | Clay | Okaloosa | Baker |
|-----------|------|----------|-------|
| Host | `maps.claycountygov.com/server/rest/...` (county-hosted) | `gis.myokaloosa.com/arcgis/rest/...` (county-hosted) | `services6.arcgis.com/HSWu3dhzHf7nZfIa/...` (AGO) |
| Endpoint type | **FeatureServer** | **MapServer** | FeatureServer |
| Path suffix | `/FeatureServer/0` | `/MapServer/111` | `/FeatureServer/0` |
| Capabilities | `Query,Extract` | `Map,Query,Data` | `Query` |
| Max record count | **200000** | 1000 | 2000 |
| Field count | 28 | 77 | 53 |
| SRS | Web Mercator (102100) | StatePlane FL North ft (102660) | Web Mercator (102100) |
| Acreage type | Double (GISACRES) | Double (PATPCL_LGL_ACRE) | Double (GIS_Acreag, sic) |
| Field-name convention | Mixed case (`Name`, `Usedesc`) | `PATPCL_` prefix everywhere | Truncated 10-char (`Site_Addre`) |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PIN | Display-formatted | ParcelDisp |
| Owner | YES | Name | -- | -- |
| Site street (name only) | YES | StreetName | House number, direction, mid, unit, city, zip | HouseNo, HouseNoSuffix, StreetDir, StreetMd, StreetUnit, StreetCity, StreetZip5, Streetzip4 |
| Mailing address | NO | -- | 3-line mailing + city/state/zip/country | Address1, Address2, Address3, City, StateProvince, ZipCode, Country, MailZip |
| Use (description) | YES | Usedesc | -- | -- |
| Legal description | NO | -- | 3-line legal | LegalLines1, LegalLines2, LegalLines3 |
| Tax district | NO | -- | -- | TaxDistCode |
| Facility name | NO | -- | -- | Facility_Name |
| Acreage | YES | GISACRES | -- | -- |
| Geometry | YES | Shape | -- | -- |

Of 28 attribute fields, 5 are mapped. Mailing address, legal description (3 lines), tax district, and structured street components are ignored.

---

## 9. Geometry Handling

Standard `_arcgis_to_geojson` ring-based conversion.

### Coordinate Re-projection

Stored in Web Mercator (WKID 102100). Request `outSR=4326` for WGS84.

### cos²(lat) Correction

Not triggered; `GISACRES` is a Double acreage attribute directly.

---

## 10. Known Limitations and Quirks

1. **FeatureServer, not MapServer.** The URL ends in `/FeatureServer/0`. Okaloosa's config uses MapServer -- do NOT copy that pattern by mistake. A `/MapServer/0` URL against `maps.claycountygov.com` will fail.

2. **Max record count is 200000.** Unusually generous -- two orders of magnitude larger than Okaloosa (1000) and Bay (1000). A single paginated request can return the entire county in one shot. The engine still requests 1000-2000 at a time for consistency.

3. **`Streetzip4` has lowercase 'z'** in the field name (while `StreetZip5` uses uppercase). Do NOT normalize -- field names are case-sensitive at query time.

4. **`Name` is a reserved-sounding column** but works fine. Some SQL dialects treat `Name` as a keyword; ArcGIS's REST WHERE parser handles it transparently here.

5. **`ParcelDisp` vs `PIN`.** Two parcel identifiers exist: `PIN` (the raw PIN) and `ParcelDisp` (a display-formatted version). The seed config uses `PIN`. `ParcelDisp` is unmapped.

6. **Three-line legal description unused.** `LegalLines1/2/3` carry the full legal but are unmapped. Useful for CD2 cross-matching if/when a Clay CD2 track is added.

7. **Separate mailing vs site address.** `Address1/2/3` + `City` + `StateProvince` + `ZipCode` + `Country` are all the OWNER mailing address, while `HouseNo`/`StreetName`/... are the SITE address. Easy to confuse if relying on aliases alone.

8. **BI-only county; no other registry surfaces exist.** No CD2, PT, or CR for Clay. Any cross-project workflow must account for these absences.

9. **Web Mercator native.** Source SRS is WKID 102100. `outSR=4326` for WGS84 re-projection.

10. **Capabilities include `Extract`.** Unlike Baker (`Query` only), Clay allows bulk `Extract` operations (e.g., to CSV/shapefile) via the FeatureServer.

11. **28 fields -- smallest schema in FL BI doc set.** Lean and well-curated; most columns have an obvious purpose.

12. **`MailZip` alias `MailZip5` duplicates `ZipCode`.** Two columns for mailing ZIP5 appear to exist; behavior may be to keep both in sync. Treat as redundant and pick one consistently if ever mapping.

**Source of truth:** `seed_bi_county_config.py` (Clay block, lines 58-66), live metadata from `https://maps.claycountygov.com/server/rest/services/Parcel/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, 10.3 KB), absence from `county-registry.yaml`.
