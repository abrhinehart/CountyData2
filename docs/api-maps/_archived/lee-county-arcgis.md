# Lee County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (hosted by the **Lee County Property Appraiser**, NOT the county directly) |
| Endpoint | `https://gissvr.leepa.org/gissvr/rest/services/ParcelRoads2/MapServer/12` |
| Layer Name | Parcels Near (ID 12) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102659 / latestWkid 2237 (NAD_1983_HARN_StatePlane_Florida_West_FIPS_0902_Feet) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | `Name` (the parcel identifier column) |
| ObjectId Field | `OBJECTID` (service metadata `objectIdField` is `null`) |
| Capabilities | `Map,Query,Data` |
| Registry status | `bi: active` (per `county-registry.yaml` L444-451) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Lee field mapping (from `seed_bi_county_config.py` L148-156)

| Purpose | Lee Field |
|---------|-----------|
| Owner | `OwnerName` |
| Parcel | `Name` (semantic overload -- this is NOT a personal name) |
| Address | `Address1` |
| Use | `LandUseDesc` |
| Acreage | `PlatAcres` |

**Critical naming quirks:**

- **`Name` is the PARCEL identifier, not an owner name.** Display field is `Name`; semantic column for owner is `OwnerName`. A reader glancing at the schema will see `Name`, `OwnerName`, `Others`, `CareOf` and may be tempted to assume `Name` is the primary person name -- it is not. Sample row: `Name = '344725B40480C00CE'`.
- **Hosted by `leepa.org`, not `leegov.com`.** The endpoint is served by the Lee Property Appraiser (`gissvr.leepa.org`), not the county government. This is an authority split: BI lives with the PA, while CR (meetings) lives on `leegov.com`-adjacent infrastructure.

---

## 2. Other Layers at MapServer Root

Layer 12 is one of multiple layers in the `ParcelRoads2` MapServer. Only layer 12 (`Parcels Near`) is seeded. Adjacent road and parcel-variant layers exist at other layer IDs on the same MapServer.

---

## 3. Query Capabilities

Base query URL:

```
https://gissvr.leepa.org/gissvr/rest/services/ParcelRoads2/MapServer/12/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OwnerName LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from StatePlane FL West (ft) to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 (server max) | Page size |
| `f` | YES | `json` | Response format |

---

## 4. Field Inventory (subset)

The Lee PA schema is unusually wide at 106 fields. Only the mapped columns and their semantically important siblings are enumerated here.

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | OID | OBJECTID | -- | NO | -- |
| **Name** | **String** | Name | 50 | **YES** | **`parcel_number`** (sic: semantic overload) |
| Type | Integer | Type | -- | NO | -- |
| StatedArea | String | Stated Area | 50 | NO | Stored acreage text |
| LegalStartDate | Date | LegalStartDate | 8 | NO | -- |
| LegalEndDate | Date | LegalEndDate | 8 | NO | -- |
| ConveyanceType | String | Sub or Condo Type | 50 | NO | -- |
| ConveyanceDesignator | String | Sub or Condo Number | 10 | NO | -- |
| BlockDesignator | String | Block Number | 10 | NO | -- |
| Lot | String | Lot | 4 | NO | -- |
| TownshipNumber / TownshipFraction / TownshipDirection | String | -- | 3/1/1 | NO | -- |
| RangeNumber / RangeDirection / RangeFraction | String | -- | 3/1/1 | NO | -- |
| SectionNumber | String | SectionNumber | 2 | NO | -- |
| Legal | String | Legal | 210 | NO | Legal description |
| DORCode | String | DORCode | 2 | NO | 2-char DOR use code |
| **OwnerName** | **String** | OwnerName | 30 | **YES** | **`owner_name`** |
| Others | String | Others | 120 | NO | Co-owner string |
| CareOf | String | CareOf | 30 | NO | "C/O" mailing line |
| **Address1** | **String** | Address1 | 30 | **YES** | **`site_address`** |
| Address2 | String | Address2 | 30 | NO | -- |
| City | String | City | 30 | NO | -- |
| State | String | State | 3 | NO | -- |
| ZIP | String | ZIP | 12 | NO | -- |
| Country | String | Country | 30 | NO | -- |
| TimeShare | String | TimeShare | 1 | NO | -- |
| TaxingDistrict | String | TaxingDistrict | 3 | NO | -- |
| LandUseCode | String | LandUseCode | 25 | NO | -- |
| **LandUseDesc** | **String** | LandUseDesc | 160 | **YES** | **`use_type`** |
| Zoning | String | Zoning | 25 | NO | -- |
| ZoningDesc | String | Zoning | 160 | NO | -- |
| **PlatAcres** | **Double** | PlatAcres | -- | **YES** | **`acreage`** |
| Shape | Geometry | Shape | -- | YES | `geometry` |
| Shape.area | Double | Shape.area | -- | NO | GIS-computed area |
| Shape.len | Double | Shape.len | -- | NO | -- |
| Longitude / Latitude | Double | -- | -- | NO | PA-computed centroid coords |

The remaining ~70 fields carry survey/plat-provenance metadata (misclose, rotation, scale, accuracy, etc.) and condo/unit detail (BldgNumber, UnitNumber, FloorDesignator, PhaseNum, CondoName).

### Sample row (live 2026-04-14)

```
Name:         344725B40480C00CE
OwnerName:    NCH BONITA PARK INC
PlatAcres:    (null)
Shape.area:   5641.658086322716
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
OwnerName LIKE '%BUILDER NAME%'
```

### Batching Rules

2000-char WHERE cap, max record count 1000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | **Name** | Lee PA's parcel identifier (e.g., `344725B40480C00CE`) |
| `owner_name` | OwnerName | Primary owner only; co-owners in `Others` unmapped |
| `site_address` | Address1 | Address2, City/State/ZIP, Country separate |
| `use_type` | LandUseDesc | Long-form description; 2-char `DORCode` sibling unmapped |
| `acreage` | PlatAcres | Platted (surveyed) acreage, Double; can be NULL on condo units |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Collier (MapServer peer) and Bay (StatePlane peer)

| Attribute | Lee | Collier | Bay |
|-----------|-----|---------|-----|
| Hosting | Lee PA (`gissvr.leepa.org`) | Collier County (`gmdcmgis.colliercountyfl.gov`) | Bay County (`gis.baycountyfl.gov`) |
| Hosting authority | Property Appraiser | County Growth Management Dept | County |
| Service kind | MapServer | MapServer | MapServer |
| Parcel field | `Name` (semantic overload) | `Folio` (Double numeric) | `A1RENUM` (dash-delimited) |
| Owner field | `OwnerName` | `OwnerLine1` (+ 2-5) | `A2OWNAME` |
| Acreage field | `PlatAcres` (Double, can be NULL) | `TotalAcres` (Double) | `DTAXACRES` (Double) |
| Field count | 106 | 127 | ~60 |
| SRS | WKID 102659 StatePlane FL West (ft) | WKID 102658 StatePlane FL East (ft) | WKID 102660 StatePlane FL North (ft) |
| Max record count | 1000 | 2000 | 1000 |
| Registry `bi` status | `active` | `active` | `active` |

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion.

### Coordinate Re-projection

Source SRS is NAD 1983 HARN StatePlane Florida West (WKID 102659, latestWkid 2237), US feet. Request `outSR=4326` for WGS84 re-projection.

### cos²(lat) Correction

Not triggered. `PlatAcres` is a PA-sourced Double acreage, not `Shape__Area` / `Shape.area`. (The unmapped sibling `Shape.area` in source units would trigger the correction if ever substituted.)

---

## 9. Known Limitations and Quirks

1. **Hosted by Lee Property Appraiser (`leepa.org`), NOT Lee County (`leegov.com`).** The `gissvr.leepa.org` hostname is operated by the PA. Scraping activity appears in PA-side logs, not county-side logs. Refresh cadence is controlled by the PA's data release schedule. This is an authority split unique to Lee in this doc set.

2. **`Name` is the parcel identifier, not an owner name.** The display field and primary column for parcel IDs is literally `Name` (e.g., `344725B40480C00CE`). A reader or engineer unfamiliar with the Lee schema may misinterpret this column -- always confirm against `ParcelDisp`-equivalent semantics before joining. `OwnerName` is the correct column for the person/entity.

3. **`PlatAcres` can be NULL on condominium units.** The sample live row (`Name = 344725B40480C00CE`) returned `PlatAcres: null` because the row is a condo unit with no platted acreage. Downstream consumers must guard against NULL before arithmetic. The `Shape.area` sibling (in source sq ft) exists but is unmapped.

4. **Schema is 106 columns wide.** Lee PA exposes more plat-provenance detail (misclose, rotation, accuracy, PLSSID, principal meridian) than any other BI county in this doc set. Five columns are mapped; the other ~100 carry parcel-geometry survey metadata.

5. **`LandUseCode` and `DORCode` are both unmapped.** The seed config picks the long-form `LandUseDesc` (160 chars). A future consumer comparing against a DOR classification table must use `DORCode` (2 chars) instead.

6. **`Others` column is an unmapped co-owner string.** When a parcel has multiple owners, `OwnerName` holds the primary and `Others` holds the rest. The adapter silently drops `Others`.

7. **Max record count 1000.** Matches server max. Pagination engaged when a page fills.

8. **StatePlane FL West (ft), not North or East.** WKID 102659 -- different StatePlane zone from Bay (North, 102660), Collier (East, 102658), Santa Rosa (North, 103024). `outSR=4326` for WGS84 re-projection.

9. **Layer metadata `objectIdField` is `null` and `spatialReference` is `null`.** Same pattern as Charlotte and Collier -- the MapServer layer does not advertise either; they are filled in the query response.

10. **Condo / unit columns present but unmapped.** `BldgNumber`, `UnitNumber`, `FloorDesignator`, `CondoName`, `CondoDesc`, `PhaseNum`, `MaxFloor`, `ImageHyperlink` are all available. A condo-aware downstream consumer could read these directly.

11. **`Longitude` and `Latitude` Double columns carry PA-computed centroid coordinates.** Unlike most FL counties where lat/lon must be derived from geometry, Lee publishes pre-computed centroids. Not mapped.

12. **Registry status `bi: active` is the ONLY project slot Lee has in `county-registry.yaml`** (L444-451). No `cr:`, `cd2:`, or `pt:` entries -- Lee is BI-only in the registry, but the CR surface DOES exist separately (see `lee-county-civicclerk.md`, which is YAML-only, not registry).

### Related surfaces not yet documented

- **Lee PT:** No permit adapter exists for Lee. Permits not in `modules/permits/scrapers/adapters/`.
- **Lee CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES` and no AcclaimWeb / BrowserView / Tyler Self-Service config exists.

**Source of truth:** `seed_bi_county_config.py` (Lee block, lines 148-156), `county-registry.yaml` (`lee-fl.projects.bi`, L444-451), live metadata from `https://gissvr.leepa.org/gissvr/rest/services/ParcelRoads2/MapServer/12?f=json` (probed 2026-04-14, HTTP 200, 26.2 KB; one-row query HTTP 200, 14.4 KB)
