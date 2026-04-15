# Bay County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server 10.81, MapServer |
| Endpoint | `https://gis.baycountyfl.gov/arcgis/rest/services/BayView/BayView/MapServer/2` |
| Layer Name | Parcels (ID 2) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102660 (NAD_1983_HARN_StatePlane_Florida_North_FIPS_0903_Feet; latestWkid 2238) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | A2OWNAME |
| ObjectId Field | OBJECTID |
| Parser | `GISQueryEngine` / `ParsedParcel` |

Service-level root (`.../BayView/MapServer`) exposes 31 layers for the Bay View public map. Capabilities: `Map,Query,Data`.

### Bay County Field Mapping (from `seed_bi_county_config.py`)

| Purpose | Bay Field |
|---------|-----------|
| Owner | `A2OWNAME` |
| Parcel | `A1RENUM` |
| Address | `DSITEADDR` |
| Use | `DORAPPDESC` |
| Acreage | `DTAXACRES` |

---

## 2. Other Layers at MapServer Root

Only Layer 2 is queried. Sibling layers on the same MapServer:

| ID | Name | Geometry Type |
|----|------|---------------|
| 0 | Addresses | Feature Layer |
| 1 | Roads | Feature Layer |
| **2** | **Parcels** | **Feature Layer (target)** |
| 3 | Hydrants | Feature Layer |
| 4 | futurelanduse | Feature Layer |
| 5 | Zoning | Feature Layer |
| 6 | MunicipalBoundaries | Feature Layer |
| 7 | OneFootContours | Feature Layer |
| 8 | Easements | Feature Layer |
| 9 | FEMAFloodways | Feature Layer |
| 10 | FEMAcobraOPA | Feature Layer |
| 11 | FEMAFloodZones | Feature Layer |
| 12 | FEMAFIRMIndex | Feature Layer |
| 13 | Wetlands | Feature Layer |
| 14 | Soils | Feature Layer |
| 15 | EvacuationZones | Feature Layer |
| 16 | CoastalHighHazardArea | Feature Layer |
| 17 | StormSurge | Feature Layer |
| 18 | EcosystemManagementAreas | Feature Layer |
| 19 | PlannedUnitDevelopments | Feature Layer |
| 20 | CommunityRedevAgencies | Feature Layer |
| 21 | CountyCommissionerDistricts | Feature Layer |
| 22 | ServiceAreas | Feature Layer |
| 23 | BeachAccess | Feature Layer |
| 24 | BoatRamps | Feature Layer |
| 25 | Libraries | Feature Layer |
| 26 | RecycleSites | Feature Layer |
| 27 | Schools | Feature Layer |
| 28 | Parks | Feature Layer |
| 29 | LOMAs | Feature Layer |
| 30 | CCCL | Feature Layer |

---

## 3. Query Capabilities

Base query URL:

```
https://gis.baycountyfl.gov/arcgis/rest/services/BayView/BayView/MapServer/2/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `A2OWNAME LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygon shapes |
| `outSR` | YES | `4326` | Re-projects from NAD83 StatePlane to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 (server max) | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Uses `resultOffset` / `resultRecordCount`. Server advertises `exceededTransferLimit: true` when more rows are available; the engine advances the offset and re-queries.

---

## 4. Field Inventory

Complete field catalog from the live layer metadata (9 fields including OBJECTID and Shape):

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | esriFieldTypeOID | OBJECTID | -- | NO | -- |
| A1RENUM | esriFieldTypeString | Parcel ID | 15 | **YES** | `parcel_number` |
| A2OWNAME | esriFieldTypeString | A2OWNAME | 30 | **YES** | `owner_name` |
| DORAPPDESC | esriFieldTypeString | Current Use | 20 | **YES** | `use_type` |
| DSITEADDR | esriFieldTypeString | Address | 40 | **YES** | `site_address` |
| DTAXACRES | esriFieldTypeDouble | Acres | -- | **YES** | `acreage` |
| Shape | esriFieldTypeGeometry | Shape | -- | YES | `geometry` |
| Shape.STArea() | esriFieldTypeDouble | Shape.STArea() | -- | NO | -- |
| Shape.STLength() | esriFieldTypeDouble | Shape.STLength() | -- | NO | -- |

Indexed fields (from service metadata): `OBJECTID` (pk), `A1RENUM` (non-unique), `A2OWNAME` (non-unique), `Shape` (spatial).

### Sample row (live)

From `query?where=1=1&outFields=*&resultRecordCount=1&f=json`:

```
OBJECTID:       82520055
A1RENUM:        03007-000-000
A2OWNAME:       WADSWORTH, BRENT C       ETAL
DORAPPDESC:     TIMBERLAND 90+
DSITEADDR:      19 2N 12W -6-
DTAXACRES:      40.0
```

---

## 5. What We Query

### WHERE Clause Pattern

Single alias:
```sql
A2OWNAME LIKE '%BUILDER NAME%'
```

Batched OR:
```sql
A2OWNAME LIKE '%BUILDER A%' OR A2OWNAME LIKE '%BUILDER B%'
```

Single quotes in the alias are escaped by doubling.

### Batching Rules

Same `GISQueryEngine` logic as other counties. Combined WHERE limited to 2000 characters. No county-specific alias cap override for Bay.

### Adaptive Delay

Inherits the default adaptive pacing: base 0.3s, floor 0.2s, ceiling 3.0s, back-off on slow responses and error doubling.

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | A1RENUM | e.g., `03007-000-000` |
| `owner_name` | A2OWNAME | May contain whitespace runs (e.g., `"WADSWORTH, BRENT C       ETAL"`) |
| `site_address` | DSITEADDR | Often legal-ish fragments (e.g., `"19 2N 12W -6-"`) rather than a street |
| `use_type` | DORAPPDESC | FL DOR use-description text |
| `acreage` | DTAXACRES | Pre-computed acres from the Property Appraiser |
| `subdivision_name` | -- | Not mapped for Bay |
| `building_value` | -- | Not mapped for Bay |
| `appraised_value` | -- | Not mapped for Bay |
| `deed_date` | -- | Not mapped for Bay |
| `geometry` | Feature geometry | Converted to GeoJSON Polygon/MultiPolygon |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|--------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | A1RENUM | -- | -- |
| Owner Name | YES | A2OWNAME | -- | -- |
| Site Address | YES | DSITEADDR | -- | -- |
| Use (DOR) | YES | DORAPPDESC | -- | -- |
| Acreage | YES | DTAXACRES | GIS-computed area | Shape.STArea() |
| Geometry | YES | Shape | -- | -- |
| Shape perimeter | NO | -- | Polygon perimeter | Shape.STLength() |
| Valuation | NO | -- | None in this layer | -- |
| Homestead / exemption | NO | -- | None in this layer | -- |
| Sibling data (zoning, FLU, flood) | NO | -- | Zoning, futurelanduse, FEMAFloodZones layers on the same MapServer (IDs 4, 5, 11) | -- |

Of 9 attribute fields on the Parcels layer, we map 5 (plus geometry).

---

## 8. Geometry Handling

The `_arcgis_to_geojson` method converts ArcGIS JSON rings to GeoJSON:

1. Single ring -- GeoJSON `Polygon`
2. Multiple rings classified by shoelace signed area (CW = exterior, CCW = hole)
3. One exterior + holes -- `Polygon` with holes
4. Multiple exteriors -- Shapely assigns holes to containing exteriors, emits `MultiPolygon`

### Coordinate Re-projection

Source SRS is NAD83 StatePlane FL North (WKID 102660 / 2238). We request `outSR=4326` so the server re-projects to WGS84 before returning coordinates. No client-side re-projection is needed.

### cos²(lat) Correction

Not triggered for Bay because `DTAXACRES` is an attribute acreage (PA-sourced), not a `Shape__Area` / `Shape.STArea()` derivation.

---

## 9. Known Limitations and Quirks

1. **MapServer, not FeatureServer.** Unlike Polk (FeatureServer) or Okeechobee (FeatureServer), Bay serves parcels from a MapServer. Query semantics are equivalent for read-only workflows, but MapServer does not support FeatureServer-only operations such as `applyEdits` or `addFeatures`.

2. **Bay uses StatePlane, not Web Mercator.** Source SRS is WKID 102660 (NAD83 HARN Florida North, US Feet). We always request `outSR=4326` to get lat/lon back.

3. **`DSITEADDR` is legal-fragment-ish.** The sample row returned `"19 2N 12W -6-"` rather than a street address. Bay's address field often contains section-township-range fragments instead of a true situs street address. Downstream geocoding may fail for rural parcels.

4. **Owner names contain compressed whitespace.** Example: `"WADSWORTH, BRENT C       ETAL"` (runs of spaces are padding from the source system). Alias matching with `LIKE '%...%'` should normalize whitespace or use wildcards around internal spaces.

5. **Minimal schema.** Only 9 columns exposed. No valuations, no homestead, no DOR numeric code, no mailing address, no legal description -- those fields do not exist on this layer.

6. **No subdivision layer exposed in this service.** Other counties (Polk, Jackson MS) expose a subdivision polygon as a sibling layer; Bay does not. Subdivision names must come from deed records.

7. **Max record count is 1000.** Lower than the common 2000; pagination kicks in sooner.

8. **Sibling layers are minScale-gated.** Parcels are visible at `minScale: 9030`. At small scales the Parcel layer is hidden in the Bay View web map, but the REST query endpoint ignores min/max scale, so this only matters for a visual workflow.

9. **Related BI registry says `status: active`.** Registry (`county-registry.yaml`, key `bay-fl.projects.bi`) lists this endpoint as active. Live probe at doc-write time confirmed `HTTP 200` with sample rows returning.

10. **Field names differ from every neighboring county.** The `A1RENUM` / `A2OWNAME` / `DSITEADDR` / `DTAXACRES` / `DORAPPDESC` naming is unique to Bay among seeded FL counties. Config must not be copied from a neighbor.

**Source of truth:** `seed_bi_county_config.py` (Bay block, lines 40-48), `county-registry.yaml` (`bay-fl.projects.bi`), live metadata from `https://gis.baycountyfl.gov/arcgis/rest/services/BayView/BayView/MapServer/2?f=json`
