# St. Lucie County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (county-authored tenant on `services1.arcgis.com`) |
| Endpoint | `https://services1.arcgis.com/oDRzuf2MGmdEHAbQ/arcgis/rest/services/ParcelBoundaries/FeatureServer/0` |
| Layer Name | ParcelBoundaries (ID 0) |
| Layer Type | Feature Layer |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 (Web Mercator / EPSG:3857), latestWkid 3857 |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON, PBF |
| Display Field | (empty string in metadata) |
| ObjectId Field | FID |
| Global ID Field | GlobalID (esriFieldTypeGlobalID) |
| Capabilities | `Query,Sync` |
| Current Version | 12 |
| Registry status | `bi: active` per `county-registry.yaml` L524-531 (`st-lucie-fl.projects.bi`) |
| Adapter / Parser | `GISQueryEngine` / `ParsedParcel` |

### St. Lucie field mapping (from `seed_bi_county_config.py` L406-413)

| Purpose | St. Lucie Field |
|---------|-----------------|
| Owner | `Owner1` |
| Parcel | `Parcel_Num` |
| Address | `SiteAddres` |
| Use | `LandUseDes` |
| Acreage | `Acre` |

**Quirk: four of five field names are Esri 10-character shapefile truncations.** The address field is `SiteAddres` (no trailing `s`), the use description is `LandUseDes` (no trailing `c` or full `LandUseDescription`), and the acreage field is the singular `Acre` (not `Acres` or `Acreage`). The parcel field uses an underscore: `Parcel_Num` (not `ParcelNum` or `PARCEL_NUM`). The case and spelling must be preserved verbatim -- "correcting" any of them breaks queries because ArcGIS field names are case- and spelling-sensitive.

---

## 2. Query Capabilities

Base query URL:

```
https://services1.arcgis.com/oDRzuf2MGmdEHAbQ/arcgis/rest/services/ParcelBoundaries/FeatureServer/0/query
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

Server advertises `exceededTransferLimit: true` when more rows are available. The engine advances `resultOffset` by `resultRecordCount` until the truncation flag clears.

---

## 3. Field Inventory

Complete field catalog from the live `?f=json` response (44 fields):

| Field Name | Type | Length | Currently Mapped? | Maps To |
|------------|------|--------|-------------------|---------|
| FID | OID | -- | NO | -- (OID) |
| AccountNum | Integer | -- | NO | -- |
| Hyphen_PID | String | 20 | NO | -- |
| **Parcel_Num** | **String** | 16 | **YES** | **`parcel_number`** |
| **Acre** | **Double** | -- | **YES** | **`acreage`** |
| CurrentRes | String | 25 | NO | -- |
| **SiteAddres** | **String** | 50 | **YES** | **`site_address`** |
| SiteCSZ | String | 50 | NO | -- |
| LotActivit | String | 15 | NO | -- |
| **Owner1** | **String** | 100 | **YES** | **`owner_name`** |
| Owner2 | String | 100 | NO | -- |
| Owner3 | String | 100 | NO | -- |
| OwnerAdd1 | String | 60 | NO | -- |
| OwnerAdd2 | String | 60 | NO | -- |
| OwnerCSZ | String | 60 | NO | -- |
| OrdNum | String | 15 | NO | -- |
| AnnexDate | Date | 8 | NO | -- |
| RezoneOrd | String | 20 | NO | -- |
| RezoneDate | Date | 8 | NO | -- |
| Zoning | String | 10 | NO | -- |
| ZoningDesc | String | 80 | NO | -- |
| FutureLand | String | 10 | NO | -- |
| **LandUseDes** | **String** | 80 | **YES** | **`use_type`** |
| LegalDescr | String | 254 | NO | -- |
| XCoord | Double | -- | NO | -- |
| YCoord | Double | -- | NO | -- |
| Latitude | String | 70 | NO | -- |
| Longitude | String | 70 | NO | -- |
| Notes | String | 254 | NO | -- |
| PASLC | String | 77 | NO | -- (PA-of-St-Lucie link) |
| SLC_Create | Date | 8 | NO | -- |
| SLC_Modify | Date | 8 | NO | -- |
| SLC_Zoning | String | 15 | NO | -- |
| Place_Name | String | 90 | NO | -- |
| CorporateL | String | 50 | NO | -- |
| FLUMA_Ordi | String | 20 | NO | -- |
| FLUMA_OrdD | Date | 8 | NO | -- |
| created_us | String | 254 | NO | -- |
| created_da | Date | 8 | NO | -- |
| last_edite | String | 254 | NO | -- |
| last_edi_1 | Date | 8 | NO | -- |
| Shape__Area | Double | -- | NO | -- |
| Shape__Length | Double | -- | NO | -- |
| GlobalID | GlobalID | 38 | NO | -- |

### Sample row (live)

From `query?where=1=1&resultRecordCount=1&outFields=*&f=json` (2026-04-14):

```
FID:         1
Owner1:      Kyle Quoc Ha Phan
Parcel_Num:  131350200840007
SiteAddres:  (empty)
LandUseDes:  (empty)
Acre:        0.96732925
```

---

## 4. What We Query

### WHERE Clause Pattern

```sql
Owner1 LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes are escaped by doubling.

### Batching Rules

2000-character WHERE cap. Max record count per page is 2000 (server limit).

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 5. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|--------------|-------|
| `parcel_number` | Parcel_Num | 15-digit numeric, e.g. `131350200840007` |
| `owner_name` | Owner1 | Title-case; additional co-owners live in `Owner2`/`Owner3` (unmapped) |
| `site_address` | SiteAddres | Frequently empty on unimproved / ROW parcels |
| `use_type` | LandUseDes | Land-use description text (e.g. "SINGLE FAMILY"); can be empty |
| `acreage` | Acre | Double, singular field name; `Shape__Area` is GIS-computed and unmapped |
| `geometry` | Shape | Polygons |

---

## 6. Diff vs Okeechobee (ArcGIS Online peer) and Santa Rosa

St. Lucie, Okeechobee, and Santa Rosa all ride `services{N}.arcgis.com` (Esri-hosted tenants), but the schemas differ materially.

| Attribute | St. Lucie (`services1.arcgis.com/oDRzuf2MGmdEHAbQ`) | Okeechobee (`services3.arcgis.com/jE4lvuOFtdtz6Lbl`) | Santa Rosa (`services.arcgis.com/Eg4L1xEv2R3abuQd`) |
|-----------|-----------------------------------------------------|-------------------------------------------------------|------------------------------------------------------|
| Service name | `ParcelBoundaries` | `Tyler_Technologies_Display_Map` | `ParcelsOpenData` |
| Layer count | 1 (standalone) | 18 (0-17) | 1 |
| ObjectId field | `FID` | `OBJECTID` | `FID` |
| Owner field | `Owner1` | `Owner1` (+ unused `Owner2`) | `OwnerName` |
| Parcel field | `Parcel_Num` | `ParcelID` | `ParcelDisp` |
| Address field | **`SiteAddres`** (no trailing `s`) | `StreetName` | `Addr1` |
| Use field | **`LandUseDes`** (truncated) | (not present) | `PRuse` |
| Acreage field | **`Acre`** (singular) | **`Acerage`** (sic typo) | `CALC_ACRE` |
| Spatial reference | WKID 102100 Web Mercator | WKID 102100 Web Mercator | WKID 103024 StatePlane FL North (ft) |
| Capabilities | `Query,Sync` | `Query,Extract,Sync` | `Query,Extract` |
| Hosted by | County-authored AGOL tenant (`oDRzuf2MGmdEHAbQ`) | Tyler Technologies tenant (`jE4lvuOFtdtz6Lbl`) | Esri-hosted county open-data tenant (`Eg4L1xEv2R3abuQd`) |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | Parcel_Num | Hyphenated parcel ID, tax account number | Hyphen_PID, AccountNum |
| Owner | PARTIAL | Owner1 | Co-owners, mailing address | Owner2, Owner3, OwnerAdd1/2, OwnerCSZ |
| Site address | PARTIAL | SiteAddres | City/state/zip | SiteCSZ |
| Use | YES | LandUseDes | Zoning, future land use | Zoning, ZoningDesc, FutureLand |
| Acreage | YES | Acre | GIS-computed area, perimeter | Shape__Area, Shape__Length |
| Geometry | YES | Shape | -- | -- |
| Legal description | NO | -- | Full legal text | LegalDescr |
| Lot activity | NO | -- | -- | LotActivit |
| Ordinance / annexation | NO | -- | Annex ordinance + date | OrdNum, AnnexDate |
| Rezone history | NO | -- | Rezone ordinance + date | RezoneOrd, RezoneDate |
| FLUMA | NO | -- | FLU map amendment | FLUMA_Ordi, FLUMA_OrdD |
| Coordinates | NO | -- | Native XY + lat/lon | XCoord, YCoord, Latitude, Longitude |
| Notes | NO | -- | Free-text notes | Notes |
| PA link | NO | -- | Deep link to PA property card | PASLC |
| Audit trail | NO | -- | Created / last-edited timestamps & users | created_us, created_da, last_edite, last_edi_1 |

Of 44 attribute fields, 5 are mapped (owner, parcel, address, use, acreage) plus geometry.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion: rings -> GeoJSON Polygon / MultiPolygon via shoelace shell/hole classification.

### Coordinate Re-projection

Source SRS is WKID 102100 (Web Mercator). We request `outSR=4326` so the server re-projects to WGS84 before returning coordinates.

### cos^2(lat) Correction

Not triggered for St. Lucie because `Acre` is a PA-sourced Double acreage attribute, not `Shape__Area`.

---

## 9. Related surfaces (no standalone doc)

- **PT (permits)**: St. Lucie is not tracked on the permits side -- there is no `modules/permits/scrapers/adapters/st_lucie*.py` file and no `pt:` entry under `st-lucie-fl.projects` in `county-registry.yaml`. No standalone permits API map doc is produced.
- **CD2 (clerk deeds)**: No `cd2:` entry in the registry block for `st-lucie-fl`; documented inline here rather than as a separate doc.

## 10. Known Limitations and Quirks

1. **Four truncated Esri 10-character shapefile field names.** The address field is `SiteAddres` (no trailing `s`), the use-description field is `LandUseDes`, and the acreage field is `Acre` (singular, not `Acres`). Other truncated names include `CurrentRes`, `LotActivit`, `LegalDescr`, `SLC_Create`, `SLC_Modify`, `created_us`, `last_edite`, and `last_edi_1`. Do NOT "correct" these -- ArcGIS field names are literal and case-sensitive.

2. **Parcel field is `Parcel_Num`, not `PARCEL_NUM` or `ParcelNo`.** Mixed case with an underscore. Copy verbatim from the seed.

3. **Owner field is `Owner1` -- do NOT confuse with `OwnerName` (Santa Rosa) or `OWNER_NAME` (Indian River / Hernando).** Multiple `OwnerN` fields exist (`Owner1`, `Owner2`, `Owner3`); the seed only maps `Owner1`.

4. **`SiteAddres` is frequently empty.** Unimproved parcels, road right-of-way segments, and newly platted lots often return an empty string rather than null. Downstream geocoding should branch on empty-string (not just None).

5. **Spatial reference is Web Mercator (WKID 102100), not StatePlane.** Unlike Santa Rosa (StatePlane FL North ft) or Bay (StatePlane FL North ft), St. Lucie stores parcel geometry in Web Mercator. `outSR=4326` returns WGS84.

6. **Capabilities advertise `Query,Sync` -- no `Extract` or `Editing`.** Bulk-download via `Extract` is not available; pagination via `resultOffset` is the only option.

7. **Empty `displayField` in metadata.** The layer metadata reports `displayField: ""` (literal empty string). Esri tooling that auto-picks a label will fall back to the OID; label workflows must pick a field explicitly.

8. **ObjectId is `FID`, not `OBJECTID`.** Matches Santa Rosa; differs from Okeechobee / Bay. Esri tooling that defaults to `OBJECTID` will paginate incorrectly.

9. **St. Lucie PT and CD2 are not in the registry.** Only `bi` has a `status: active` entry under `st-lucie-fl.projects`. Permits and clerk-deed surfaces are out of scope for this repo.

10. **BOA is `platform: manual`.** Covered in `st-lucie-county-civicclerk.md`. BCC and P&Z run on CivicClerk; the Board of Adjustment is not auto-scraped.

11. **`PASLC` field is a deep link to the PA property card.** Could be used for one-click handoff to the Property Appraiser's public website, but is not currently mapped.

12. **Max record count is 2000.** Higher than Bay (1000) and Brevard (1000); pagination is less frequent.

**Source of truth:** `seed_bi_county_config.py` (St. Lucie block, lines 406-413), `county-registry.yaml` (`st-lucie-fl.projects.bi`, L524-531), live metadata from `https://services1.arcgis.com/oDRzuf2MGmdEHAbQ/arcgis/rest/services/ParcelBoundaries/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, ~17.3 KB) and live sample row from `/query?where=1=1&resultRecordCount=1&outFields=*&f=json` (HTTP 200, ~8.1 KB).
