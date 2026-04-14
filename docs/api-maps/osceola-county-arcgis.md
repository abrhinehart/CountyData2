# Osceola County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server FeatureServer (county-hosted ArcGIS Hosting Server, hybrid) |
| Endpoint | `https://gis.osceola.org/hosting/rest/services/Parcels/FeatureServer/3` |
| Layer Name | Parcels (ID 3) |
| SDE Source | `OsceolaGIS.DATA.Parcels` (fully qualified SQL Server table name) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857), latestWkid 3857 |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | SubName |
| ObjectId Field | OBJECTID_1 (not `OBJECTID` -- see Quirks) |
| Capabilities | `Query,Create,Update,Delete,Uploads,Editing` |
| Current Version | 10.91 |
| Registry status | `bi: active` per `county-registry.yaml` L472-479 (`osceola-fl.projects.bi`) |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### Osceola field mapping (from `seed_bi_county_config.py` L388-394)

| Purpose | Osceola Field |
|---------|---------------|
| Owner | `Owner1` |
| Parcel | `PARCELNO` |
| Address | `StreetName` |
| Use | `DORDesc` |
| Acreage | `TotalAcres` |

---

## 2. Query Capabilities

Base query URL:

```
https://gis.osceola.org/hosting/rest/services/Parcels/FeatureServer/3/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `Owner1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

Server advertises `exceededTransferLimit: true` when more rows are available. Capabilities include `Editing` -- but the public layer is used read-only by the scraper.

---

## 3. Field Inventory

The live layer exposes **177 fields** -- an unusually rich schema that includes sales history, building characteristics, exemption codes, jurisdictional flags, and multi-land-line valuation. Below is the mapped subset and selected highlights; the full list is available from `?f=json` against the endpoint above.

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| OBJECTID_1 | OID | -- | NO | -- (layer OID) |
| OBJECTID | Integer | -- | NO | -- (secondary integer; NOT the OID) |
| **Owner1** | **String** | 255 | **YES** | **`owner_name`** |
| Owner2 | String | 255 | NO | -- |
| Owner3 | String | 255 | NO | -- |
| **PARCELNO** | **String** | 18 | **YES** | **`parcel_number`** |
| PIN | String | 18 | NO | -- (separate from PARCELNO) |
| Strap | String | 18 | NO | -- |
| Dsp_strap | String | 23 | NO | -- |
| StreetNumb | String | 5 | NO | -- |
| StreetPfx | String | 5 | NO | -- |
| **StreetName** | **String** | 23 | **YES** | **`site_address`** (street name only) |
| StreetSfx | String | 5 | NO | -- |
| StreetSfxD | String | 5 | NO | -- |
| LocCity | String | 17 | NO | -- |
| LocZip | String | 10 | NO | -- |
| DORCode | String | 4 | NO | -- |
| **DORDesc** | **String** | 50 | **YES** | **`use_type`** |
| **TotalAcres** | **Double** | -- | **YES** | **`acreage`** |
| SubName | String | 64 | NO | -- (subdivision; display field) |
| `OsceolaGIS.DATA.Parcels.AREA` | Double | -- | NO | -- (fully-qualified area) |
| SaleDate | Date | -- | NO | -- |
| SalePrice | Integer | -- | NO | -- |
| Shape__Area | Double | -- | NO | -- (alias `Shape.STArea()`) |
| Shape__Length | Double | -- | NO | -- (alias `Shape.STLength()`) |

(Additional fields include: `sec`/`twnshp`/`Range`/`Sub`/`Blk`/`Lot`; building detail (`YearBuilt`, `LivUnits`, `Bedrooms`, `Fullbaths`, `HalfBaths`, `RoofType`, `RoofCover`, `ExtWall`, `IntWall`, `AttachedGa`, `Pool`, etc.); exemption codes (`Exemptions`, `Exemption1`-`Exemption3`); current/previous valuations (`AssessedVa`, `CurrLand`, `CurrBldg`, `CurrJust`, `PrevFullLa`, `PrevBldg`, `PrevTaxabl`); and multi-land-line records (`Land1DOR`, `Land2DOR`, `Land3DOR`, with unit, FF, depth, and unit-price subfields).)

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
OBJECTID:      (null)
OBJECTID_1:    1
Owner1:        CENTRAL FLORIDA TOURISM OVERSIGHT DISTRICT
PARCELNO:      012527000000180000
StreetName:    WORLD
DORDesc:       RIGHT OF WAY-VAC
TotalAcres:    1.95
```

---

## 4. What We Query

### WHERE Clause Pattern

```sql
Owner1 LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 2000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | PARCELNO | 18-char string, e.g. `012527000000180000` |
| `owner_name` | Owner1 | Title-case; `Owner2`/`Owner3` unmapped |
| `site_address` | StreetName | Street name only -- full address requires `StreetNumb` + `StreetPfx` + `StreetName` + `StreetSfx` + `StreetSfxD` + `LocCity` + `LocZip` |
| `use_type` | DORDesc | FL DOR description text (e.g. `"RIGHT OF WAY-VAC"`, `"SINGLE FAMILY"`) |
| `acreage` | TotalAcres | PA-sourced Double acreage |
| `geometry` | Shape | Polygons |

---

## 6. Diff vs Putnam / Sarasota (county-hosted peers)

| Attribute | Osceola | Putnam | Sarasota |
|-----------|---------|--------|----------|
| Host | `gis.osceola.org` | `putnam-fl.com` ArcGIS (county-hosted) | `ags2.scgov.net` (county-hosted) |
| Path pattern | **`/hosting/rest/services/...`** (ArcGIS Hosting Server) | `/arcgis/rest/services/...` | `/arcgis/rest/services/...` |
| Service type | FeatureServer (hybrid -- see Quirks) | MapServer | MapServer |
| Fields on layer | **177** | ~30 | ~25 |
| Parcel field | `PARCELNO` | `PARCELNO` | `ID` |
| Owner field | `Owner1` | `OWNER` | `OWNER1` |
| Address field | `StreetName` (street only) | `SITUS_ADDRESS` | `SITUS_ADDR` |
| Use field | `DORDesc` (text) | `DOR_USE_CODE` (code) | `USE_CODE` |
| Acreage field | `TotalAcres` | `Acres` | `ACREAGE` |
| Capabilities | `Query,Create,Update,Delete,Uploads,Editing` | `Map,Query` | `Map,Query` |
| Commission YAMLs exist? | **NO (zero Osceola commission yamls)** | YES | YES |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PARCELNO | Alternate IDs | PIN, Strap, Dsp_strap |
| Owner | PARTIAL | Owner1 | Co-owners, billing address | Owner2, Owner3, BillingAdd, BillingA_1, BillingA_2, City, State, Zip |
| Site address | PARTIAL | StreetName | Full structured address | StreetNumb, StreetPfx, StreetSfx, StreetSfxD, LocCity, LocZip |
| Section/Township/Range | NO | -- | Full STR + sub/blk/lot | sec, twnshp, Range, Sub, Blk, Lot, SubName |
| Use | YES | DORDesc | 4-char code, jurisdiction | DORCode, Jurisdicti, JurisDesc |
| Acreage | YES | TotalAcres | GIS-computed area | Shape__Area (alias `Shape.STArea()`), `OsceolaGIS.DATA.Parcels.AREA` |
| Building characteristics | NO | -- | Year built, units, baths, roof, walls | YearBuilt, EffYr, GrossBldAr, LivUnits, Bedrooms, Fullbaths, HalfBaths, RoofType, ExtWall, IntWall, AttachedGa, Pool |
| Sale history | NO | -- | Current + previous sale | SaleDate, SalePrice, NAL, ORBkPg, Grantor, Stamps, Instrument, PrevSaleDa, PrevSalePr, PrevGranto, PrevStamps |
| Valuation | NO | -- | Current + previous | AssessedVa, CurrLand, CurrBldg, CurrJust, CurrExempt, PrevFullLa, PrevBldg, PrevAssess, PrevTaxabl |
| Exemptions | NO | -- | Homestead, other | Exemptions, Exemption1-3, Exemptio_1-_6 |
| Land lines | NO | -- | Up to 3 land records with DOR + units | Land1DOR, Land2DOR, Land3DOR (+ sibling units/depth/price) |
| CRA | NO | -- | Community Redevelopment Area | CRA |

Of 177 attribute fields, 5 are mapped (owner, parcel, street, use, acreage) plus geometry. The vast majority of rich parcel detail is unused.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is WKID 102100 (Web Mercator). We request `outSR=4326`.

### cos^2(lat) Correction

Not triggered for Osceola because `TotalAcres` is a PA-sourced Double acreage attribute.

---

## 9. Related surfaces (no standalone doc)

- **PT (permits)**: No `pt:` entry under `osceola-fl.projects` in `county-registry.yaml`; no `osceola*.py` adapter under `modules/permits/scrapers/adapters/`. Documented inline here -- no Osceola permits API map doc is produced.
- **CR (commission)**: **no commission yamls exist for Osceola** (i.e. No commission yamls exist for Osceola). `modules/commission/config/jurisdictions/FL/` does NOT contain any `osceola-county-*.yaml` (no BCC, no P&Z, no BOA). Osceola is explicitly absent from the CR side of this repo. No `osceola-county-*` CR doc is produced. If Osceola CR is onboarded in the future, the YAMLs need to be authored from scratch (model on `collier-county-bcc.yaml` or `lee-county-bcc.yaml`).
- **CD2 (clerk deeds)**: No `cd2:` entry. Documented inline here.

## 10. Known Limitations and Quirks

1. **County-hosted ArcGIS `/hosting/` path.** The endpoint path `https://gis.osceola.org/hosting/rest/services/Parcels/FeatureServer/3` uses an ArcGIS Hosting Server (on-prem equivalent of AGOL hosted feature services). The `/hosting/rest/services/` prefix is unusual -- most peers use `/arcgis/rest/services/` (MapServer) or `services{N}.arcgis.com/.../rest/services/` (AGOL). Hybrid: a FeatureServer running inside a county-hosted ArcGIS Hosting Server deployment.

2. **177 fields on a single parcel layer.** Unusually rich -- most FL parcel layers expose 9-45 fields. Building characteristics, multi-line land records, sales history, exemptions, and previous-roll valuations are all embedded. 172 of these are unmapped.

3. **ObjectId field is `OBJECTID_1` (not `OBJECTID`).** The layer carries BOTH `OBJECTID_1` (OID, the true primary key) and `OBJECTID` (a plain Integer). Esri tooling that defaults to `OBJECTID` will paginate on the wrong column and silently miss rows. The service metadata declares `objectIdField: OBJECTID_1`; honor that.

4. **Zero commission YAMLs exist for Osceola.** `modules/commission/config/jurisdictions/FL/` has no `osceola-*.yaml` files at all. BCC / P&Z / BOA are neither auto-scraped nor `manual` -- they are simply absent. This is unique among the six counties in this batch and is noted here explicitly so downstream readers do not look for a `osceola-county-civicclerk.md` or `osceola-county-legistar.md` doc (none is produced).

5. **`StreetName` is the street NAME only** -- no house number. To assemble a full street address, concatenate `StreetNumb` + `StreetPfx` + `StreetName` + `StreetSfx` + `StreetSfxD` + `LocCity` + `LocZip`. Geocoding with just `StreetName` will be ambiguous.

6. **`DORDesc` is the human description.** The 4-char DOR code lives in `DORCode` (unmapped). Different from Martin (`DOR_CODE` numeric Double) or Indian River (`DOR_DESC` already descriptive -- same pattern as Osceola's `DORDesc`).

7. **Fully-qualified SDE field `OsceolaGIS.DATA.Parcels.AREA`.** One field literally carries the fully-qualified SQL Server schema name as its ArcGIS field name (dots and all). This field name must be backtick- or bracket-escaped by most SQL-style clients. Unmapped.

8. **Capabilities include `Editing` and `Uploads`.** Even though the scraper treats the layer as read-only, the server advertises write capabilities. If an authentication token is ever exposed, those capabilities become a risk surface. Anonymous requests return 200 on Query but typically fail on Update/Delete without a token.

9. **Shape field has two aliases present.** `Shape__Area` (alias `Shape.STArea()`) and `Shape__Length` (alias `Shape.STLength()`) expose the SQL Server `geometry` STArea/STLength functions via ArcGIS-style underscore names. These are unused; `TotalAcres` is authoritative.

10. **Max record count is 2000.** Same as Santa Rosa / Indian River; higher than Bay / Escambia (1000).

11. **Multi-land-line structure (`Land1DOR`, `Land2DOR`, `Land3DOR` with siblings).** For parcels with multiple DOR-coded land records (e.g. a homestead + agricultural parcel on the same legal), up to three land lines are represented inline. Useful for accurate DOR classification but ignored by the seed.

12. **Previous-roll valuation columns (`PrevFullLa`, `PrevBldg`, `PrevAssess`, `PrevTaxabl`, `PrevExempt`) are aligned with FL's prior-year assessment roll.** Unmapped. Sibling `LatestPrev` SmallInteger signals which prior roll year is reflected.

**Source of truth:** `seed_bi_county_config.py` (Osceola block, lines 388-394), `county-registry.yaml` (`osceola-fl.projects.bi`, L472-479), confirmed absence of `osceola-county-*.yaml` under `modules/commission/config/jurisdictions/FL/`, live metadata from `https://gis.osceola.org/hosting/rest/services/Parcels/FeatureServer/3?f=json` (probed 2026-04-14, HTTP 200, ~36.8 KB, 177 fields) and live sample row from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~18.0 KB).
