# Baker County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Esri-hosted tenant) |
| Endpoint | `https://services6.arcgis.com/HSWu3dhzHf7nZfIa/arcgis/rest/services/parcels_web/FeatureServer/0` |
| Layer Name | parcels_web (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102100 / latestWkid 3857 (Web Mercator) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | (none advertised) |
| ObjectId Field | FID |
| Capabilities | `Query` |
| Registry status | **Not listed in `county-registry.yaml`** (BI-only county; no CD2 / PT / CR surfaces) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Baker field mapping (from `seed_bi_county_config.py` L31-39)

| Purpose | Baker Field |
|---------|-------------|
| Owner | `Owner` |
| Parcel | `PIN` |
| Address | `Site_Addre` |
| Use | `Use_Descri` |
| Acreage | `GIS_Acreag` |

**Truncated 10-character shapefile-legacy names.** Baker's underlying data originated as an Esri shapefile, which limits attribute names to 10 characters. When the shapefile was hosted to AGO, the truncated forms `Site_Addre`, `Use_Descri`, `GIS_Acreag` (instead of `Site_Address`, `Use_Description`, `GIS_Acreage`) were preserved verbatim. **Do NOT "complete" these names -- the field literally ends at the 10th character.** Similarly Subdivisio, Descriptio, Fractional, Creation_1, GlobalID_2, Land_Type, Land_Value, and many others.

---

## 2. Absence of Other Surfaces

Baker is a BI-only county in this registry. There is no entry in `county-registry.yaml` for Baker at all -- it lives exclusively in `seed_bi_county_config.py`. Consequently:

| Project | State | Reason |
|---------|-------|--------|
| `bi` | Seeded (this doc) | `seed_bi_county_config.py` L31-39 |
| `cd2` | **No surface documented** | No LandmarkWeb / AcclaimWeb / Tyler Self-Service / BrowserView config for Baker |
| `pt` | **No surface documented** | No permit adapter, no `modules/permits/...` entry for Baker |
| `cr` | **No surface documented** | No jurisdiction YAML for Baker under `modules/commission/config/jurisdictions/FL/` |

---

## 3. Query Capabilities

Base query URL:

```
https://services6.arcgis.com/HSWu3dhzHf7nZfIa/arcgis/rest/services/parcels_web/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `Owner LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from Web Mercator to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size (matches server max) |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (53 fields). Shapefile-truncated names preserved verbatim:

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| FID | OID | FID | NO | -- |
| PIN | String | PIN | **YES** | `parcel_number` |
| Type | String | Type | NO | -- |
| Block | String | Block | NO | -- |
| Lot | String | Lot | NO | -- |
| **Descriptio** | **String (sic, 10-char)** | Descriptio | NO | (truncated from `Description`) |
| **Subdivisio** | **String (sic, 10-char)** | Subdivisio | NO | (truncated from `Subdivision`) |
| Fractional | String | Fractional | NO | -- |
| **GIS_Acreag** | **Double (sic, 10-char)** | GIS_Acreag | **YES** | **`acreage`** |
| Deed_Acrea | Double | Deed_Acrea | NO | (truncated from `Deed_Acreage`) |
| Zoning | String | Zoning | NO | -- |
| Shape__Are | Double | Shape__Are | NO | -- |
| Shape__Len | Double | Shape__Len | NO | -- |
| GlobalID | String | GlobalID | NO | -- |
| CreationDa | Date | CreationDa | NO | (truncated) |
| Creator | String | Creator | NO | -- |
| EditDate | Date | EditDate | NO | -- |
| Editor | String | Editor | NO | -- |
| GlobalID_2 | String | GlobalID_2 | NO | (duplicate; from a join) |
| Creation_1 | Date | Creation_1 | NO | -- |
| Creator_1 | String | Creator_1 | NO | -- |
| EditDate_1 | Date | EditDate_1 | NO | -- |
| Editor_1 | String | Editor_1 | NO | -- |
| PARCELNO | String | PARCELNO | NO | (alt parcel id) |
| Parcel_Id | Integer | Parcel_Id | NO | (numeric id) |
| PIN_1 | String | PIN_1 | NO | (duplicate from join) |
| **Owner** | **String** | Owner | **YES** | **`owner_name`** |
| **Site_Addre** | **String (sic, 10-char)** | Site_Addre | **YES** | **`site_address`** |
| City | String | City | NO | -- |
| Use_Code | Integer | Use_Code | NO | (numeric DOR code) |
| **Use_Descri** | **String (sic, 10-char)** | Use_Descri | **YES** | **`use_type`** |
| Section | Integer | Section | NO | -- |
| Township | String | Township | NO | -- |
| Range | Integer | Range | NO | -- |
| Building_C | Integer | Building_C | NO | (building count?) |
| Building_D | String | Building_D | NO | (building description) |
| Heated_Are | Integer | Heated_Are | NO | (heated area sqft) |
| Effective_ | Integer | Effective_ | NO | (effective year built) |
| Year_Built | Integer | Year_Built | NO | -- |
| Land_Units | Double | Land_Units | NO | -- |
| Land_Type | String | Land_Type | NO | -- |
| Mass_Adjus | Integer | Mass_Adjus | NO | (mass adjustment) |
| Land_Rate | Integer | Land_Rate | NO | -- |
| Land_Value | Integer | Land_Value | NO | -- |
| Ag_Value | Integer | Ag_Value | NO | -- |
| **Bulding_Va** | **Integer (sic, 10-char)** | Bulding_Va | NO | (truncated from `Building_Va`, which was truncated from `Building_Value`) |
| Extra_Feat | Integer | Extra_Feat | NO | -- |
| Total_Just | Integer | Total_Just | NO | -- |
| Cap_Value | Integer | Cap_Value | NO | -- |
| Exemption_ | Integer | Exemption_ | NO | -- |
| Taxable_Va | Integer | Taxable_Va | NO | -- |
| Shape__Area | Double | Shape__Area | NO | -- |
| Shape__Length | Double | Shape__Length | NO | -- |

Both `Shape__Area` (Double) and the truncated `Shape__Are` (Double) exist; AGO added the non-truncated versions when it auto-computed geometry attributes.

---

## 5. What We Query

### WHERE Clause Pattern

```sql
Owner LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases into a single WHERE. Single quotes doubled.

### Batching Rules

2000-char WHERE cap.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PIN | -- |
| `owner_name` | Owner | -- |
| `site_address` | Site_Addre (sic, 10-char) | Truncated from `Site_Address` |
| `use_type` | Use_Descri (sic, 10-char) | Truncated from `Use_Description` |
| `acreage` | GIS_Acreag (sic, 10-char) | Truncated from `GIS_Acreage` |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Okeechobee (AGO peer with typo)

Both Baker and Okeechobee are AGO-hosted FeatureServers that preserve quirky column names verbatim. Okeechobee's typo (`Acerage` sic) arose from a data-entry mistake; Baker's oddities (`Site_Addre`, `Use_Descri`, `GIS_Acreag`) arose from 10-character shapefile truncation.

| Attribute | Baker | Okeechobee |
|-----------|-------|------------|
| Tenant ID | `HSWu3dhzHf7nZfIa` (county/Esri) | `jE4lvuOFtdtz6Lbl` (Tyler Technologies) |
| Service | `parcels_web/FeatureServer/0` | `Tyler_Technologies_Display_Map/FeatureServer/2` |
| Field count | 53 | 27 |
| Acreage name | `GIS_Acreag` (sic, truncated) | `Acerage` (sic, typo) |
| Acreage type | Double | String (requires coercion) |
| Use field | `Use_Descri` (truncated) | (none in schema) |
| ObjectId field | `FID` | `OBJECTID` |
| Other registry slots | NONE (BI-only county) | CD2 (LandmarkWeb), PT (Tyler EnerGov), CR (Granicus) |
| Capabilities | `Query` | `Query,Extract,Sync` |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PIN | Alt identifiers | PARCELNO, Parcel_Id, PIN_1 |
| Owner | YES | Owner | -- | -- |
| Site address | PARTIAL | Site_Addre | City | City |
| Use (description) | YES | Use_Descri | Use code (numeric) | Use_Code |
| Lot / Block | NO | -- | Explicit columns | Lot, Block |
| Subdivision | NO | -- | Truncated column | Subdivisio |
| Legal description | NO | -- | Truncated column | Descriptio |
| Fractional legal | NO | -- | -- | Fractional |
| Zoning | NO | -- | -- | Zoning |
| Section / Township / Range | NO | -- | -- | Section, Township, Range |
| Acreage | YES | GIS_Acreag | Deed acreage, Shape area | Deed_Acrea, Shape__Area, Shape__Are |
| Building attrs | NO | -- | Count, description, heated area | Building_C, Building_D, Heated_Are |
| Building year | NO | -- | Year built, effective year | Year_Built, Effective_ |
| Valuation | NO | -- | Land, bldg (sic `Bulding_Va`), ag, extra features, just, cap, taxable | Land_Value, Bulding_Va, Ag_Value, Extra_Feat, Total_Just, Cap_Value, Taxable_Va |
| Exemptions | NO | -- | Exemption col | Exemption_ |
| Audit timestamps | NO | -- | Creation, edit dates (two sets from join) | CreationDa, EditDate, Creation_1, EditDate_1 |
| Geometry | YES | Shape | Perimeter | Shape__Length |

Of 53 attribute fields (many duplicated from a join), 5 are mapped. Baker has richer valuation / building detail than Okeechobee but none are pulled into BI today.

---

## 9. Known Limitations and Quirks

1. **Truncated 10-character shapefile names preserved verbatim.** `Site_Addre`, `Use_Descri`, `GIS_Acreag`, `Subdivisio`, `Descriptio`, `Deed_Acrea`, `CreationDa`, `Building_C`, `Building_D`, `Heated_Are`, `Effective_`, `Mass_Adjus`, `Bulding_Va` (itself a further truncation of the already-typo'd `Building_Va`), `Extra_Feat`, `Total_Just`, `Cap_Value`, `Exemption_`, `Taxable_Va`. Do NOT rewrite the config to use "Site_Address" / "Use_Description" / "GIS_Acreage" etc. -- those fields do not exist in the layer.

2. **`Bulding_Va` is doubly mangled.** The shapefile originally had `Building_Value`, truncated to `Building_Va` (10 chars), but was then typo-copied again to `Bulding_Va` (note the missing "i"). This is the single most brittle column name in the Baker schema.

3. **BI-only county; no other registry surfaces exist.** No LandmarkWeb / AcclaimWeb / Tyler Self-Service for CD2. No permit adapter for PT. No jurisdiction YAML for CR. Any cross-project workflow must account for these absences.

4. **Baker is NOT in `county-registry.yaml`.** Unlike most other counties, Baker appears only in the BI seed list. Treat `seed_bi_county_config.py` L31-39 as the single source of truth.

5. **Join artifacts double many audit fields.** `GlobalID_2`, `Creation_1`, `EditDate_1`, `Editor_1`, `PIN_1`, `Creator_1` are duplicates produced by a secondary table join. Keep `GlobalID`, `CreationDa`, `EditDate`, `PIN`, and `Creator` when choosing which column to read.

6. **Web Mercator native.** Source SRS is WKID 102100. `outSR=4326` for WGS84 re-projection.

7. **Max record count 2000.** Matches server max; pagination only when a page is full.

8. **Capabilities are limited to `Query`.** No `Extract`, no `Sync`, no `Map`. Only runtime queries are supported.

9. **Shape has both truncated AND non-truncated pairs.** `Shape__Are` (10-char) and `Shape__Area` both exist; same for `Shape__Len` and `Shape__Length`. AGO auto-added the non-truncated names. Prefer `Shape__Area` / `Shape__Length` when reading geometry attributes.

10. **`GIS_Acreag` is a Double.** Unlike Okeechobee's `Acerage` (String), Baker's truncated acreage column is properly typed Double -- no coercion needed.

11. **53 fields include ~15 join-audit duplicates.** Effective attribute count is closer to 35-40 distinct columns of real parcel data.

12. **`Use_Descri` is the short description.** Any downstream DOR-use normalization should map the 10-char-truncated label back to the canonical DOR use description externally.

**Source of truth:** `seed_bi_county_config.py` (Baker block, lines 31-39), live metadata from `https://services6.arcgis.com/HSWu3dhzHf7nZfIa/arcgis/rest/services/parcels_web/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, 18.9 KB), absence from `county-registry.yaml`.
