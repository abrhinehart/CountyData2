# Putnam County FL -- ArcGIS FeatureServer API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Enterprise FeatureServer (county-hosted) |
| Endpoint | `https://pamap.putnam-fl.gov/server/rest/services/CadastralData/FeatureServer/2` |
| Layer Name | Parcels (ID 2) |
| Geometry Type | esriGeometryPolygon |
| Spatial Reference | WKID 102658 / latestWkid 2236 (NAD_1983_HARN_StatePlane_Florida_East_FIPS_0901_Feet) |
| Max Record Count | 1000 |
| Auth | Anonymous -- no authentication required |
| Query Formats | JSON, geoJSON |
| Display Field | CNVYNAME |
| ObjectId Field | OBJECTID |
| Global ID Field | GlobalID |
| Capabilities | `Query` |
| Service description | "Tax parcel polygons joined with CAMA data. Contains owner, address, and assessment information." |
| Hub site | `putnam-pcgis.hub.arcgis.com` |
| PA public map | `pamap.putnam-fl.gov/PropertyAppraiserPublicMap/` |
| Registry status | `bi` active (per `county-registry.yaml` L306-315) |
| Parser | `GISQueryEngine` / `ParsedParcel` |

### Putnam field mapping (from `seed_bi_county_config.py` L252-258)

| Purpose | Putnam Field |
|---------|--------------|
| Owner | `OWNERNME1` |
| Parcel | `PARCELID` |
| Address | `SITEADDRESS` |
| Use | `USEDSCRP` |
| Acreage | `STATEDAREA` |

**Note on `OWNERNME1`:** Putnam splits owners across `OWNERNME1` (primary, mapped) and `OWNERNME2` (secondary, unmapped). Multi-owner parcels silently drop the second owner today. See Quirks.

---

## 2. Other Layers at FeatureServer Root

The `CadastralData` FeatureServer hosts multiple cadastral layers. Layer 2 is the mapped Parcels layer. Adjacent layers support the PA public map (lot lines, section grids, neighborhood boundaries, commission districts). Only layer 2 is seeded into the BI pipeline.

---

## 3. Query Capabilities

Base query URL:

```
https://pamap.putnam-fl.gov/server/rest/services/CadastralData/FeatureServer/2/query
```

### Supported Query Parameters

| Parameter | Used by Us? | Our Value | Notes |
|-----------|-------------|-----------|-------|
| `where` | YES | `OWNERNME1 LIKE '%alias%'` (OR batched) | SQL WHERE clause |
| `outFields` | YES | `*` | All fields returned |
| `returnGeometry` | YES | `true` | Parcel polygons |
| `outSR` | YES | `4326` | Re-projects from StatePlane FL East (ft) to WGS84 |
| `resultOffset` | YES | Paginated starting at 0 | Pagination cursor |
| `resultRecordCount` | YES | up to 1000 (server max) | Page size |
| `f` | YES | `json` | Response format |
| `geometry` | NO | -- | Spatial filter |
| `orderByFields` | NO | -- | -- |

### Pagination

`exceededTransferLimit: true` advances `resultOffset`. Server max 1000 per page.

---

## 4. Field Inventory

Complete field catalog from live `?f=json` (64 fields -- richest schema after Polk / Okaloosa):

| Field Name | Type | Alias | Currently Mapped? | Maps To |
|------------|------|-------|-------------------|---------|
| OBJECTID | OID | OBJECTID | NO | -- |
| **PARCELID** | **String** | Parcel Identification Number | **YES** | **`parcel_number`** |
| LOWPARCELID | String | LOWPARCELID | NO | -- |
| BUILDING | String | Building Number | NO | -- |
| UNIT | String | Unit Number | NO | -- |
| **STATEDAREA** | **String** | Stated Area | **YES** | **`acreage`** (String -- requires coercion) |
| LGLSTARTDT | Date | Legal Start Date | NO | -- |
| CVTTXCD | String | Tax District Code | NO | -- |
| CVTTXDSCRP | String | Tax District Description | NO | -- |
| SCHLTXCD | String | School District Code | NO | -- |
| SCHLDSCRP | String | School District Description | NO | -- |
| USECD | String | Assessing Use Code | NO | -- |
| **USEDSCRP** | **String** | Assessing Use Description | **YES** | **`use_type`** |
| NGHBRHDCD | String | Assessing Neighborhood Code | NO | -- |
| CLASSCD | String | Property Class Code | NO | -- |
| CLASSDSCRP | String | Property Class | NO | -- |
| **SITEADDRESS** | **String** | Site Address | **YES** | **`site_address`** |
| PRPRTYDSCRP | String | Property Description | NO | -- |
| CNVYNAME | String | Sub or Condo Name | NO | Display field; unmapped |
| **OWNERNME1** | **String** | First Owner Name | **YES** | **`owner_name`** |
| OWNERNME2 | String | Second Owner Name | NO | -- |
| PSTLADDRESS | String | Postal Address | NO | -- |
| PSTLCITY | String | Postal City | NO | -- |
| PSTLSTATE | String | Postal State | NO | -- |
| PSTLZIP5 | String | Postal Zip 5 | NO | -- |
| PSTLZIP4 | String | Postal Zip +4 | NO | -- |
| FLOORCOUNT | Integer | Number of Floors | NO | -- |
| BLDGAREA | Double | Building Area | NO | -- |
| RESFLRAREA | Double | Residential Floor Area | NO | -- |
| RESYRBLT | Double | Residential Year Built | NO | (Double, not Integer) |
| RESSTRTYP | String | Residential Structure Type | NO | -- |
| STRCLASS | String | Structure Class | NO | -- |
| CLASSMOD | String | Structure Class Modifier | NO | -- |
| LNDVALUE | Double | Land Value | NO | -- |
| PRVASSDVAL | Double | Previous Assessed Value | NO | -- |
| CNTASSDVAL | Double | Current Assessed Value | NO | -- |
| ASSDVALYRCG | Double | Assessed Value Year Over Year Change | NO | -- |
| ASSDPCNTCG | Double | Assessed Value % Change | NO | -- |
| PRVTXBLVAL | Double | Previous Taxable Value | NO | -- |
| CNTTXBLVAL | Double | Current Taxable Value | NO | -- |
| TXBLVALYRCHG | Double | Taxable Value Year Over Year Change | NO | -- |
| TXBLPCNTCHG | Double | Taxable Value % Change | NO | -- |
| PRVWNTTXOD | Double | Previous Winter Taxes Owed | NO | (unusual in FL -- see Quirks) |
| PRVSMRTXOD | Double | Previous Summer Taxes Owed | NO | (unusual in FL -- see Quirks) |
| TOTPRVTXTOD | Double | Total Previous Taxes Owed | NO | -- |
| CNTWNTTXOD | Double | Current Winter Taxes Owed | NO | -- |
| CNTSMRTXOD | Double | Current Summer Taxes Owed | NO | -- |
| TOTCNTTXOD | Double | Total Current Taxes Owed | NO | -- |
| TXODYRCHG | Double | Taxes Owed Year Over Year Change | NO | -- |
| TXODPCNTCHG | Double | Taxes Owed % Change | NO | -- |
| WATERSERV | String | Water Service Provider | NO | -- |
| SEWERSERV | String | Sewer Service Provider | NO | -- |
| LASTUPDATE | Date | Last Update Date | NO | -- |
| COMMUNITY | String | Community Name | NO | -- |
| EXEMPTIONS | String | Exemption Code | NO | -- |
| LEGAL | String | Legal Description | NO | -- |
| CENSUSTRACT | String | US Census Tract | NO | -- |
| CENSUSBLOCK | String | US Census Block | NO | -- |
| NBRSTRUCT | Integer | Number of Structures | NO | -- |
| MOBILEHOME | Integer | Number of Mobile Homes | NO | -- |
| PARCELTRS | String | Township Range Section | NO | -- |
| PARCLTRSSBL | String | Parcel Id Township Range Section | NO | -- |
| PA_URL | String | Link to PA Website | NO | (one-click deep link) |
| GlobalID | GlobalID | GlobalID | NO | -- |

Plus geometry (Shape), returned when `returnGeometry=true`.

---

## 5. What We Query

### WHERE Clause Pattern

```sql
OWNERNME1 LIKE '%BUILDER NAME%'
```

Batched OR combines multiple aliases.

### Batching Rules

2000-char WHERE cap; 1000 records per page (server max).

### Adaptive Delay

Default `AdaptiveDelay` (base 0.3s, floor 0.2s, ceiling 3.0s).

---

## 6. Parsed Output

| ParsedParcel Field | Source Field | Notes |
|--------------------|-------------|-------|
| `parcel_number` | PARCELID | -- |
| `owner_name` | OWNERNME1 | `OWNERNME2` (secondary) silently dropped |
| `site_address` | SITEADDRESS | -- |
| `use_type` | USEDSCRP | Description (not numeric `USECD`) |
| `acreage` | STATEDAREA | **String** -- requires coercion to float |
| `geometry` | Shape | Polygons |

---

## 7. Diff vs Polk County (rich FeatureServer peer)

Both Polk and Putnam are county-hosted ArcGIS Enterprise FeatureServers with CAMA-joined parcels. Putnam exposes a more unusual schema with Michigan-style winter/summer taxes and condo/unit detail:

| Attribute | Putnam | Polk |
|-----------|--------|------|
| Endpoint | `pamap.putnam-fl.gov/.../CadastralData/FeatureServer/2` | `gis.polk-county.net/.../Map_Property_Appraiser/FeatureServer/1` |
| Field count | 64 | 55+ |
| Max record count | 1000 | 2000 |
| Acreage field type | String (STATEDAREA) | Double (TOT_ACREAGE) |
| Legal description | YES (`LEGAL` string column) | NO (not in schema) |
| Owner split | `OWNERNME1` + `OWNERNME2` | single `NAME` |
| Winter/summer taxes | YES (unusual in FL) | NO |
| Sub/condo name | YES (`CNVYNAME`) | NO (subdivision code only) |
| Mobile home count | YES (`MOBILEHOME`) | NO |
| Structures count | YES (`NBRSTRUCT`) | NO |
| PA deep-link URL | YES (`PA_URL`) | NO |
| Year-over-year deltas | YES (assessed/taxable/taxes-owed) | NO |
| Spatial reference | StatePlane FL East (ft) | Web Mercator |

---

## 8. What We Extract vs What's Available

| Data Category | Currently Extracted | Source Field | Available but Not Extracted | Source Field(s) |
|---------------|--------------------|--------------|-----------------------------|-----------------|
| Parcel ID | YES | PARCELID | Alt parcel id | LOWPARCELID |
| Building / unit | NO | -- | Building, unit numbers | BUILDING, UNIT |
| Owner | YES | OWNERNME1 | Second owner | OWNERNME2 |
| Mailing address | NO | -- | Full postal (address, city, state, zip) | PSTLADDRESS, PSTLCITY, PSTLSTATE, PSTLZIP5, PSTLZIP4 |
| Site address | YES | SITEADDRESS | -- | -- |
| Legal description | NO | -- | Full legal text | LEGAL, PRPRTYDSCRP |
| Subdivision / condo | NO | -- | Conveyance (sub/condo) name | CNVYNAME |
| Use | YES | USEDSCRP | Use code | USECD |
| Property class | NO | -- | Code + description | CLASSCD, CLASSDSCRP |
| Neighborhood | NO | -- | Code | NGHBRHDCD |
| Tax / school districts | NO | -- | Codes + descriptions | CVTTXCD, CVTTXDSCRP, SCHLTXCD, SCHLDSCRP |
| Stated area (acreage) | YES | STATEDAREA | -- | -- |
| Building area | NO | -- | Building area, residential floor area, floor count | BLDGAREA, RESFLRAREA, FLOORCOUNT |
| Structure count | NO | -- | Number of structures, mobile homes | NBRSTRUCT, MOBILEHOME |
| Structure classification | NO | -- | Year built, type, class, modifier | RESYRBLT, RESSTRTYP, STRCLASS, CLASSMOD |
| Land / assessed / taxable values | NO | -- | Current + previous + YoY + % change | LNDVALUE, PRV/CNT ASSDVAL, ASSDVALYRCG, ASSDPCNTCG, PRV/CNT TXBLVAL, TXBLVALYRCHG, TXBLPCNTCHG |
| Taxes owed (winter/summer split) | NO | -- | Current + previous + YoY + % change | PRV/CNT WNT/SMR TXOD, TOTPRVTXTOD, TOTCNTTXOD, TXODYRCHG, TXODPCNTCHG |
| Utility providers | NO | -- | Water, sewer | WATERSERV, SEWERSERV |
| Community | NO | -- | Community name | COMMUNITY |
| Exemption code | NO | -- | -- | EXEMPTIONS |
| Census tract / block | NO | -- | Full geography | CENSUSTRACT, CENSUSBLOCK |
| Township / range / section | NO | -- | Concatenated + parcel-concatenated | PARCELTRS, PARCLTRSSBL |
| PA deep-link URL | NO | -- | Direct link to PA record page | PA_URL |
| Legal start date | NO | -- | Date parcel legal description started | LGLSTARTDT |
| Last update | NO | -- | -- | LASTUPDATE |
| Geometry | YES | Shape | -- | -- |

Of 64 attribute fields, 5 are mapped (parcel, owner, address, use, acreage) plus geometry. The unmapped 59 include valuation deltas, tax delinquency by season, structure counts, and a direct PA URL -- the richest BI candidate in FL.

---

## 9. Geometry Handling

Standard `_arcgis_to_geojson` ring-based conversion.

### Coordinate Re-projection

Stored in NAD 1983 HARN StatePlane Florida East (US survey feet, WKID 102658). Request `outSR=4326` for WGS84.

### cos²(lat) Correction

Not triggered; `STATEDAREA` is a PA-sourced acreage attribute. The fact that it is typed `String` (not Double) is the operational hazard, not the area-correction path.

---

## 10. Known Limitations and Quirks

1. **`STATEDAREA` is typed as String, not Double.** Same shape as Okeechobee's `Acerage` -- values arrive as strings and must be coerced to float. Other Putnam numeric fields (`LNDVALUE`, `BLDGAREA`, ...) are properly Double.

2. **`CNVYNAME` (sub or condo name) is the display field.** If a name is missing, the feature renders with a blank label in ArcGIS apps. Unmapped in BI; consider adding if condo enrichment is needed.

3. **Two owner columns, only first is mapped.** `OWNERNME1` is extracted, `OWNERNME2` (secondary / co-owner) is silently dropped -- same pattern as Okeechobee's Owner1/Owner2.

4. **Winter-and-summer taxes-owed columns are unusual for FL.** `PRVWNTTXOD`, `PRVSMRTXOD`, `CNTWNTTXOD`, `CNTSMRTXOD` look like Michigan-style seasonal property-tax billing. Unusual and potentially misleading in a FL context; treat them as vendor-standard columns that may always be zero.

5. **Michigan-origin schema artifacts.** Many of the fields (YoY change, percent change, winter/summer split) suggest this schema was bootstrapped from a non-FL CAMA template. The schema is richer than typical FL PA layers as a result.

6. **`RESYRBLT` is Double, not Integer.** Year built is typed `Double`. Any consumer must cast explicitly (most ETLs expect `Integer`).

7. **`PA_URL` exists as a first-class column.** A ready-made deep link to the PA record page (`pamap.putnam-fl.gov/PropertyAppraiserPublicMap/...`) is stored per parcel -- unusual and useful, but unmapped.

8. **`LEGAL` column carries full legal description.** Unlike Polk (no legal) or Bay (inline), Putnam exposes the full text legal in a single String column. High value for CD2 cross-matching but currently unmapped.

9. **StatePlane FL East (ft) native SRS.** WKID 102658 -- different from Bay/Okaloosa (FL North) and Web Mercator counties. Server `outSR=4326` re-projects to WGS84.

10. **Layer 2 on the FeatureServer.** The `/FeatureServer/2` segment is required; do not copy Okeechobee's `/FeatureServer/2` by accident -- the tenant is different (Enterprise, not AGO). Both happen to live at layer 2 of their respective FeatureServers.

11. **Max record count 1000.** Pagination is frequent; a full county sweep takes many pages.

12. **`MOBILEHOME` and `NBRSTRUCT` are rare-for-FL enrichment columns.** Most FL PA feeds do not expose a structure count; Putnam does. Good candidates for future BI mapping.

**Source of truth:** `seed_bi_county_config.py` (Putnam block, lines 252-258), `county-registry.yaml` (`putnam-fl.projects.bi`, L306-315), live metadata from `https://pamap.putnam-fl.gov/server/rest/services/CadastralData/FeatureServer/2?f=json` (probed 2026-04-14, HTTP 200, 15.9 KB)
