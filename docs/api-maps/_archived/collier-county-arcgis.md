# Collier County FL -- ArcGIS MapServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server MapServer (county-hosted by Growth Management Dept) |
| Endpoint | `https://gmdcmgis.colliercountyfl.gov/server/rest/services/Parcels/MapServer/0` |
| Layer Name | Parcels (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102658 / latestWkid 2236 (NAD_1983_HARN_StatePlane_Florida_East_FIPS_0901_Feet) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | `SiteStreetName` |
| ObjectId Field | `OBJECTID` (service metadata `objectIdField` is `null`) |
| Capabilities | `Query,Map,Data` |
| Registry status | `bi: active` (per `county-registry.yaml` L395-406) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Collier field mapping (from `seed_bi_county_config.py` L333-341)

| Purpose | Collier Field |
|---------|---------------|
| Owner | `OwnerLine1` |
| Parcel | `Folio` |
| Address | `SiteStreetAddress` |
| Use | `UseCode` |
| Acreage | `TotalAcres` |

**Collier-specific naming:**

- **`Folio` is the Collier term for parcel number.** Unlike `PARCELNO` (Hendry/Baker), `PIN` (Baker/St. Johns), `ACCOUNT` (Charlotte/Sarasota), or `Name` (Lee), Collier uses `Folio` -- a term shared with Miami-Dade, Broward, and Hillsborough but not typical in the FL Panhandle.
- **`OwnerLine1` implies sibling `OwnerLine2`, `OwnerLine3`, etc.** Unlike single-owner fields (`OWNER`, `NAME`, `A2OWNAME`) or two-owner splits (`Owner1` / `Owner2`), Collier uses a **five-line** owner block (`OwnerLine1` through `OwnerLine5`). The seed config captures ONLY `OwnerLine1`. A separate `OwnerLineCombined` field joins all 5 into a single string (40,000-char length) but is unmapped.
- **Hostname `gmdcmgis` = Growth Management Department - Community Management GIS.** The prefix is an acronym, not a typo.

---

## 2. Other Layers at MapServer Root

Layer 0 is the only layer seeded from the `Parcels/MapServer`. Other layers on the same service are not surfaced in BI.

---

## 3. Query Capabilities

Base query URL:

```
https://gmdcmgis.colliercountyfl.gov/server/rest/services/Parcels/MapServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OwnerLine1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from StatePlane FL East (ft) to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size (matches server max) |
| `f` | YES | `json` | Response format |

---

## 4. Field Inventory (subset; full schema has 127 fields)

Only the mapped columns and their semantically important siblings are enumerated. The full Collier PA schema is the richest in the FL doc set.

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| OBJECTID | OID | -- | NO | -- |
| Shape | Geometry | -- | YES | `geometry` |
| ParcelId | Double | -- | NO | Secondary numeric id |
| **Folio** | **Double** | -- | **YES** | **`parcel_number`** |
| Is_County | String | 255 | NO | -- |
| PAO_Hyperlink | String | 3000 | NO | Link to PA detail page |
| AddressType | String | 8000 | NO | -- |
| **OwnerLine1** | **String** | 8000 | **YES** | **`owner_name`** |
| OwnerLine2 | String | 8000 | NO | Co-owner / suffix |
| OwnerLine3 | String | 8000 | NO | -- |
| OwnerLine4 | String | 8000 | NO | -- |
| OwnerLine5 | String | 8000 | NO | -- |
| OwnerLineCombined | String | 40000 | NO | All 5 owner lines concatenated |
| Legal | String | 1200 | NO | Legal description |
| Sale1Date / Sale1BookPage / Sale1Amount | Double / String / Double | -- | NO | 4 sale-history rows available (Sale1-Sale4) |
| OwnerCountry / OwnerCity / OwnerState / OwnerZip | String | 8000 | NO | Owner mailing address (5 lines) |
| OwnerZipPlus4 | Double | -- | NO | -- |
| **UseCode** | **Double** | -- | **YES** | **`use_type`** (numeric DOR-style code) |
| ClassCode | Double | -- | NO | Secondary use code |
| StrapNumber | String | 8000 | NO | Alternate parcel identifier |
| SiteStreetNumber | Double | -- | NO | -- |
| SiteStreetName | String | 8000 | NO | -- |
| SiteStreetType | String | 8000 | NO | -- |
| SiteStreetOrdinal | String | 8000 | NO | -- |
| SiteUnit / SiteCity / SiteZipCode | String / String / Double | -- | NO | -- |
| SiteStreet | String | 8000 | NO | -- |
| **SiteStreetAddress** | **String** | 8000 | **YES** | **`site_address`** |
| SubdivisionCondoNumber | Double | -- | NO | -- |
| BlockBldg / LotUnit | String / Double | -- | NO | -- |
| Section / Township / Range | Double | -- | NO | -- |
| **TotalAcres** | **Double** | -- | **YES** | **`acreage`** |
| TaxYear / RollType | Double / String | -- | NO | -- |
| LandJustValue / ImprovementsJustValue / TotalJustValue | Double | -- | NO | Valuation triple |
| SohBenefit / NonSchool10PctBenefit / AgriculturalClassBenefit | Double | -- | NO | -- |
| CountyAssessedValue / SchoolAssessedValue / MunicipalAssessedValue / OtherAssessedValue | Double | -- | NO | 4-bucket assessed values |
| HmstdExemptAmount + 20+ other exemption / tax columns | Double | -- | NO | Full homestead / exemption / millage / tax bundle |
| created_us / created_da / last_edite / last_edi_1 | String / Date / String / Date | -- | NO | Audit columns |
| GlobalID | String | 36 | NO | -- |
| FLN / PARCELTYPE / FLN_NUM | String / Double / Double | -- | NO | Parcel-type identifiers |
| Shape_Length | Double | -- | NO | -- |
| Shape_Area | Double | -- | NO | GIS-computed area (sq ft) |

**127 fields total.** The Collier schema includes a complete PA dataset: 4 sale histories, full valuation breakdown (just / assessed / taxable for County/School/Municipal/Other), ~25 exemption columns (homestead, senior, veteran, disabled, deployed, affordable housing, etc.), and 10+ millage / tax columns. Five fields are mapped.

### Sample row (live 2026-04-14)

```
Folio:             64760001
OwnerLine1:        FLORIDA POWER & LIGHT COMPANY
OwnerLine2:        700 UNIVERSE BLVD
UseCode:           66
TotalAcres:        217.9706923894803
SiteStreetAddress: (null)
Shape_Area:        9494803.360485759
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
OwnerLine1 LIKE '%BUILDER NAME%'
```

### Batching Rules

2000-char WHERE cap, max record count 2000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | Folio | Double numeric; typically 8+ digits |
| `owner_name` | OwnerLine1 | Primary line only; OwnerLine2-5 silently dropped |
| `site_address` | SiteStreetAddress | Can be NULL (e.g., FPL utility parcels); no fallback to `SiteStreet` / `SiteStreetName` |
| `use_type` | UseCode | Numeric Double (e.g., `66`); no text description |
| `acreage` | TotalAcres | Double acres; PA-sourced |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Lee (MapServer peer) and Okaloosa (Patriot MapServer peer)

| Attribute | Collier | Lee | Okaloosa |
|-----------|---------|-----|----------|
| Hosting | Collier County (`gmdcmgis.colliercountyfl.gov`) | Lee PA (`gissvr.leepa.org`) | Okaloosa County (`gis.myokaloosa.com`) |
| Service kind | MapServer | MapServer | MapServer |
| Parcel field | `Folio` (Double) | `Name` (String overload) | `PATPCL_PIN` (String) |
| Owner field | `OwnerLine1` (+ 2-5) | `OwnerName` | `PATPCL_OWNER` |
| Use field | `UseCode` (Double numeric) | `LandUseDesc` (160-char text) | `PATPCL_USEDESC` (text) |
| Acreage field | `TotalAcres` (Double) | `PlatAcres` (Double, can be NULL) | `PATPCL_LGL_ACRE` (Double) |
| Field count | **127 (widest)** | 106 | 77 |
| SRS | WKID 102658 StatePlane FL East (ft) | WKID 102659 StatePlane FL West (ft) | WKID 102660 StatePlane FL North (ft) |
| Max record count | 2000 | 1000 | 1000 |

Collier's schema is the widest in the doc set; Lee has the most survey-provenance metadata.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion.

### Coordinate Re-projection

Source SRS is NAD 1983 HARN StatePlane Florida East (WKID 102658, latestWkid 2236), US feet. Request `outSR=4326` for WGS84 re-projection.

### cos²(lat) Correction

Not triggered. `TotalAcres` is a PA-sourced Double acreage, not `Shape_Area`. The unmapped sibling `Shape_Area` (sq ft) would require a 43560-divide AND cos²(lat) correction if ever substituted.

---

## 9. Known Limitations and Quirks

1. **`Folio` is the Collier parcel-identifier term.** Unlike most FL counties (`PARCELNO`, `PIN`, `ACCOUNT`), Collier uses `Folio`. Shared with Miami-Dade and Broward. Typed as `Double` (numeric), not `String`.

2. **`OwnerLine1` through `OwnerLine5` -- five-line owner block.** Only `OwnerLine1` is mapped. Co-owners, trust/entity suffixes, and C/O mailing continuations all live in `OwnerLine2-5`. A `OwnerLineCombined` field (40,000-char String) concatenates all five -- unmapped. For comprehensive owner matching, a future consumer would read `OwnerLineCombined` instead of `OwnerLine1`.

3. **Hostname `gmdcmgis` = Growth Management Dept / Community Management GIS.** Not a typo. `https://gmdcmgis.colliercountyfl.gov` is the Growth Management Department's GIS server, distinct from any PA-side hosting.

4. **Registry-vs-YAML conflict: registry says `legistar`, YAMLs say `civicclerk` -- YAML wins.** Per `county-registry.yaml` L395-406, Collier's `cr` slot reports `platform: legistar, slug: collier-county-bcc, status: usable_seed`. But all four jurisdiction YAMLs (`collier-county-bcc.yaml`, `-boa.yaml`, `-ccpc.yaml`, `-hex.yaml`) explicitly set `scraping.platform: civicclerk` with `base_url: https://colliercofl.portal.civicclerk.com`. **YAML wins** -- the registry entry is stale. Do NOT modify `county-registry.yaml`; this doc flags the conflict. See `collier-county-civicclerk.md` for the full CR surface.

5. **Service metadata `objectIdField` is `null` and `spatialReference` is `null`.** Same pattern as Charlotte and Lee. Query responses fill in the values.

6. **`UseCode` is numeric Double, not a text description.** Unlike Lee's `LandUseDesc` (160-char text) or Okaloosa's `PATPCL_USEDESC`, Collier stores only the numeric code. A downstream consumer needing text must maintain a code-to-description lookup externally (or read the unmapped `ClassCode` / `DisabledExemptDesc` / `WhollyExemptDesc` for tangential descriptions).

7. **127 fields -- richest PA dataset in the FL doc set.** Includes 4 sale histories (`Sale1Date` through `Sale4Amount`), complete 4-bucket assessed values (County/School/Municipal/Other), ~25 exemption columns, and 10+ millage / tax columns. All unmapped.

8. **`SiteStreetAddress` can be NULL on utility / unaddressed parcels.** Sample row (FPL, Folio 64760001) returned `SiteStreetAddress: null`. Downstream geocoding must handle NULL without falling back to owner mailing address.

9. **Max record count 2000, matches server max.** Higher than Lee (1000). Pagination less frequent.

10. **Field alias lengths are 8000 characters.** Every String field in the Collier schema has `length: 8000` -- unusual. Most schemas cap at 30-250 chars. This suggests the layer was built without length optimization and may contain long owner strings.

11. **Sale-history columns use Double for dates** (`Sale1Date`, `Sale2Date`, etc.) -- integer-packed date values (likely `yyyymmdd`). Not mapped; requires unpacking.

12. **Per registry `county-registry.yaml` L395-406, Collier's BI status is `active`.** Confirmed at probe time. The `cr` slot's `legistar` label is stale (see §9.4).

### Related surfaces not yet documented

- **Collier PT:** No permit adapter exists for Collier under `modules/permits/scrapers/adapters/`.
- **Collier CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES`.

**Source of truth:** `seed_bi_county_config.py` (Collier block, lines 333-341), `county-registry.yaml` (`collier-fl.projects.bi`, L395-406), live metadata from `https://gmdcmgis.colliercountyfl.gov/server/rest/services/Parcels/MapServer/0?f=json` (probed 2026-04-14, HTTP 200, 16.1 KB; one-row query HTTP 200, 18.8 KB)
