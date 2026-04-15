# Sarasota County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Online FeatureServer (Esri-hosted tenant) |
| Endpoint | `https://services3.arcgis.com/icrWMv7eBkctFu1f/arcgis/rest/services/ParcelHosted/FeatureServer/0` |
| Layer Name | ParcelHosted (ID 0) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 2882 / latestWkid 2882 (NAD_1983_HARN_Florida_GDL_Albers; confirmed both in service metadata and in query response) |
| Max Record Count | 2000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | `NAME1` |
| ObjectId Field | `OBJECTID` |
| Capabilities | `Query,Extract` |
| Registry status | **ABSENT -- no entry in `county-registry.yaml`** (seeded only via `seed_bi_county_config.py` L269-277) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Sarasota field mapping (from `seed_bi_county_config.py` L269-277)

| Purpose | Sarasota Field |
|---------|----------------|
| Owner | `NAME1` |
| Parcel | `ID` |
| Address | `FULLADDRESS` |
| Use | `STCD` |
| Acreage | `MeasuredAcreage` |

**Sarasota-specific naming:**

- **`ID` is the PARCEL field.** Bare `ID` -- not `PARCELID`, not `PIN`, not `Folio`. Unusually terse; sample value is `2034042008` (10-digit string). Do NOT assume this is an ObjectId or a row counter; it is the canonical parcel number.
- **`NAME1` is the OWNER field.** Implies sibling `NAME_ADD2` through `NAME_ADD5` (observed in the field inventory). The seed config picks only `NAME1`.
- **`STCD` is the USE field.** 5-char STATE CODE, not a DOR use code or a use description. Distinct from Lee's `DORCode` (2-char), Santa Rosa's `PRuse` (use code), and Bay's `DORAPPDESC` (text description). Sample value: `0403`.
- **`MeasuredAcreage` is the unique acreage field name.** No other FL county in the seed list uses the word "Measured" in the acreage column -- it implies a surveyor-measured (not PA-computed) acreage.

---

## 2. Absence of Other Surfaces

Sarasota is a BI-only county in the seed list; there is no entry in `county-registry.yaml`.

| Project | State | Reason |
|---------|-------|--------|
| `bi` | Seeded (this doc) | `seed_bi_county_config.py` L269-277 |
| `cd2` | **No surface documented** | No LandmarkWeb / AcclaimWeb / Tyler Self-Service / BrowserView config |
| `pt` | **No surface documented** | No permit adapter |
| `cr` | **No surface documented** | No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/` |

---

## 3. Query Capabilities

Base query URL:

```
https://services3.arcgis.com/icrWMv7eBkctFu1f/arcgis/rest/services/ParcelHosted/FeatureServer/0/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `NAME1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from NAD83 HARN FL Albers to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 2000 | Page size (matches server max) |
| `f` | YES | `json` | Response format |

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (66 fields). Mapped fields bolded.

| Field Name | Type | Alias | Length | Currently Mapped? | Maps To |
|------------|------|-------|--------|-------------------|---------|
| OBJECTID | OID | OBJECTID | -- | NO | -- |
| ACCOUNT | String | ACCOUNT | 10 | NO | (10-digit alternate parcel id) |
| **ID** | **String** | ID | 13 | **YES** | **`parcel_number`** |
| STATUS_CODE | Integer | STATUS_CODE | -- | NO | -- |
| **NAME1** | **String** | NAME1 | 100 | **YES** | **`owner_name`** |
| NAME_ADD2 | String | NAME_ADD2 | 56 | NO | Co-owner line 2 |
| NAME_ADD3 | String | NAME_ADD3 | 56 | NO | Co-owner line 3 |
| NAME_ADD4 | String | NAME_ADD4 | 41 | NO | Co-owner line 4 |
| NAME_ADD5 | String | NAME_ADD5 | 40 | NO | Co-owner line 5 |
| CITY | String | CITY | 26 | NO | Owner mailing city |
| STATE | String | STATE | 8 | NO | Owner mailing state |
| ZIP | String | ZIP | 13 | NO | Owner mailing zip |
| COUNTRY | String | COUNTRY | 20 | NO | -- |
| LOCN | String | LOCN | 11 | NO | Site number |
| LOCN_SUFFIX | String | LOCN_SUFFIX | 3 | NO | -- |
| LOCD | String | LOCD | 3 | NO | Site predirection |
| LOCS | String | LOCS | 29 | NO | Site street name |
| LOCT | String | LOCT | 10 | NO | Site street type |
| LOCD_SUFFIX | String | LOCD_SUFFIX | 3 | NO | Site postdirection |
| UNIT | String | UNIT | 11 | NO | -- |
| LOCCITY | String | LOCCITY | 13 | NO | Site city |
| LOCSTATE | String | LOCSTATE | 3 | NO | -- |
| LOCZIP | String | LOCZIP | 10 | NO | -- |
| **FULLADDRESS** | **String** | FullAddress | 150 | **YES** | **`site_address`** (concatenated form of LOCN-LOCD-LOCS-LOCT-LOCD_SUFFIX + LOCCITY + LOCSTATE + LOCZIP) |
| **STCD** | **String** | STCD | 5 | **YES** | **`use_type`** (5-char STATE CODE) |
| SUBD | String | SUBD | 30 | NO | Subdivision |
| TXCD | String | TXCD | 4 | NO | Tax code |
| MUNICIPALITY | String | MUNICIPALITY | 30 | NO | -- |
| SECT / TWSP / RANG | String | -- | 4 | NO | -- |
| BLOCK / LOT | String | -- | 5 / 9 | NO | -- |
| CENSUS | String | CENSUS | 20 | NO | -- |
| JUST | Double | JUST | -- | NO | Just (market) value |
| ASSD | Double | ASSD | -- | NO | Assessed value |
| TXBL | Integer | TXBL | -- | NO | Taxable value |
| EXEMPTIONS | Double | EXEMPTIONS | -- | NO | Exemption total |
| HOMESTEAD | String | HOMESTEAD | 2 | NO | -- |
| IMPROVEMT | Double | IMPROVEMT | -- | NO | -- |
| EXEMPT1 | SmallInteger | EXEMPT1 | -- | NO | -- |
| LNVS_N | Double | LNVS_N | -- | NO | -- |
| ZONING | String | ZONING | 5 | NO | -- |
| SALE_AMT / SALE_DATE / OR_BOOK / OR_PAGE / LEGALREFER | Double / String / String / String / String | -- | -- | NO | Sale history |
| POOL | String | POOL | 2 | NO | -- |
| GRND_AREA / LIVING / BEDR / BATH / LIVUNITS / YRBL | Integer | -- | -- | NO | Building attributes |
| LEGAL1 / LEGAL2 / LEGAL3 / LEGAL4 | String | -- | 50 each | NO | 4-line legal description |
| LSQFT | Integer | LSQFT | -- | NO | Lot square feet |
| HYPERLINK | String | HYPERLINK | 75 | NO | PA detail URL |
| NOTES | String | NOTES | 100 | NO | -- |
| **MeasuredAcreage** | **Double** | MeasuredAcreage | -- | **YES** | **`acreage`** |
| LastUpdate | Date | LastUpdate | -- | NO | -- |
| Shape__Area | Double | Shape__Area | -- | NO | GIS-computed area |
| Shape__Length | Double | Shape__Length | -- | NO | -- |

### Sample row (live 2026-04-14)

```
ACCOUNT:         0000008267
ID:              2034042008
NAME1:           COOPER ELEANOR DOWNEY MARTINEZ
FULLADDRESS:     2121 WOOD ST 204, SARASOTA FL, 34237
STCD:            0403
MeasuredAcreage: 2.8430001137475265
Shape__Area:     123840.58969116211
```

---

## 5. What We Query

### WHERE Clause Pattern

```sql
NAME1 LIKE '%BUILDER NAME%'
```

### Batching Rules

2000-char WHERE cap, max record count 2000.

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | ID | 13-char string (e.g., `2034042008`) |
| `owner_name` | NAME1 | Primary only; NAME_ADD2-5 unmapped |
| `site_address` | FULLADDRESS | Server-side concatenation of `LOCN-LOCD-LOCS-LOCT-LOCD_SUFFIX + LOCCITY + LOCSTATE + LOCZIP` |
| `use_type` | STCD | 5-char state code (e.g., `0403`), NOT a text description |
| `acreage` | MeasuredAcreage | Double acres; "Measured" connotes surveyor-sourced |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Santa Rosa (FeatureServer peer, flipped case convention)

Both are AGO-hosted FeatureServers but differ materially in schema.

| Attribute | Sarasota | Santa Rosa |
|-----------|----------|------------|
| Tenant ID | `icrWMv7eBkctFu1f` | `Eg4L1xEv2R3abuQd` |
| Service name | `ParcelHosted` | `ParcelsOpenData` |
| Parcel field | `ID` (bare) | `ParcelDisp` |
| Owner field | `NAME1` | `OwnerName` |
| Use field | `STCD` (5-char state code) | `PRuse` (short use code) |
| Acreage field | `MeasuredAcreage` | `CALC_ACRE` |
| ObjectId | `OBJECTID` | `FID` |
| Field count | 66 | 32 |
| SRS | WKID 2882 (NAD83 HARN FL Albers) | WKID 103024 (StatePlane FL North ft) |
| Max record count | 2000 | 2000 |
| Capabilities | `Query,Extract` | `Query,Extract` |
| Registry entry | **ABSENT** | `bi: active` |

Sarasota's schema is about twice as wide as Santa Rosa's and exposes valuations, sale history, building attributes, and a 4-line legal description -- none mapped.

---

## 8. Geometry Handling

Standard `_arcgis_to_geojson` conversion.

### Coordinate Re-projection

Source SRS is NAD 1983 HARN Florida GDL Albers (WKID 2882), an equal-area statewide projection (shares the Albers family with Hendry's WKID 2881). Request `outSR=4326` for WGS84 re-projection.

### cos²(lat) Correction

Not triggered. `MeasuredAcreage` is a PA/surveyor-sourced Double acreage, not `Shape__Area`. Because the source projection is equal-area, Albers-computed `Shape__Area` would NOT need cos²(lat) correction (only a 4046.86 sq-meter-to-acre divide) -- but the seed config uses `MeasuredAcreage` anyway.

---

## 9. Known Limitations and Quirks

1. **Parcel field is bare `ID`, not `PARCELID` / `PIN` / `Folio`.** Unusually terse column name. Sample value `2034042008` is a 13-char-length String (actually ~10 digits). A reader may mistake `ID` for a row identifier; it is the canonical parcel number.

2. **Owner field is `NAME1`, implying `NAME_ADD2` through `NAME_ADD5`.** Five-line owner block similar to Collier's `OwnerLine1-5`. Only `NAME1` is mapped; co-owners / mailing continuations are dropped.

3. **Use field is `STCD` -- a 5-char STATE CODE, not a DOR code or description.** Sample value `0403`. Downstream consumers comparing against the standard FL DOR code table (which uses 2-4 digit codes like `01`, `0100`, `0501`) must normalize the extra padding.

4. **`MeasuredAcreage` -- unique wording.** No other FL county in the seed list uses the word "Measured" in its acreage column name. Implies surveyor-sourced (not GIS-computed) acreage. Typed as Double.

5. **Registry absence.** Sarasota is not in `county-registry.yaml`. Cross-project tooling that reads the registry will skip Sarasota. Given Sarasota's population (~450k, a top-10 FL county), this is a notable gap.

6. **AGO tenant `icrWMv7eBkctFu1f`** -- Sarasota's Esri-hosted open-data org ID. Stable opaque identifier.

7. **NAD83 HARN FL Albers (WKID 2882) native SRS.** Same Albers family as Hendry (WKID 2881). Unusual for parcel data (most FL counties use Web Mercator or StatePlane). `outSR=4326` re-projects server-side.

8. **66 fields; 5 mapped.** The unmapped set includes the full 4-line legal description (`LEGAL1-4`), valuation bundle (`JUST`, `ASSD`, `TXBL`, `EXEMPTIONS`, `IMPROVEMT`), sale history (`SALE_AMT`, `SALE_DATE`, `OR_BOOK`, `OR_PAGE`, `LEGALREFER`), building attributes (`GRND_AREA`, `LIVING`, `BEDR`, `BATH`, `LIVUNITS`, `YRBL`), and lot size (`LSQFT`).

9. **Separate ALL-CAPS `ACCOUNT` column exists (10-char)**, distinct from the ID mapping. `ACCOUNT` is a secondary parcel identifier (sample: `0000008267`). Unmapped; if a future consumer needs a zero-padded account form, this is the column.

10. **Full address concatenation available server-side.** `FULLADDRESS` (alias `FullAddress`, 150 chars) holds a comma-delimited pre-joined site address (e.g., `2121 WOOD ST 204, SARASOTA FL, 34237`). Prefer over re-concatenating `LOCN` / `LOCD` / `LOCS` / etc. client-side.

11. **Max record count 2000**, matches server max.

12. **`Shape__Area` and `MeasuredAcreage` will not agree exactly on small parcels** because `MeasuredAcreage` is surveyor-stated and `Shape__Area` (Albers sq meters -> acres) is GIS-computed. Seed config uses the PA-sourced value.

### Related surfaces not yet documented

- **Sarasota PT:** No permit adapter exists.
- **Sarasota CR:** No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/`.
- **Sarasota CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES`.

**Source of truth:** `seed_bi_county_config.py` (Sarasota block, lines 269-277), absence from `county-registry.yaml`, live metadata from `https://services3.arcgis.com/icrWMv7eBkctFu1f/arcgis/rest/services/ParcelHosted/FeatureServer/0?f=json` (probed 2026-04-14, HTTP 200, 41.4 KB; one-row query HTTP 200, 31.7 KB)
