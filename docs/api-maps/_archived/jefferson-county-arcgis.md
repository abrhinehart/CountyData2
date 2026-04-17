# Jefferson County AL -- ArcGIS Server Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Server (Jefferson County self-hosted) |
| Host | `jccgis.jccal.org` |
| Service | `server/rest/services/Basemap/Parcels/MapServer` |
| Layer | Layer 0 -- "Parcels" |
| Geometry Type | `esriGeometryPolygon` |
| Source Spatial Reference | WKID 102630 / StatePlaneALWest (US Feet) |
| Max Record Count | 2000 |
| Auth | Anonymous (no token) |
| Registry entry | `county-registry.yaml` L571-583 (`jefferson-al.projects.bi`) |
| BI config | `seed_bi_county_config.py` L439-453 |

Service description (from the live `?f=json`): the layer is regenerated nightly from the assessor source of truth, exposes property lines + owner/address attributes. 369 DR Horton parcels currently on this layer per the registry notes. Birmingham metro market; non-disclosure state.

## 2. Probe (2026-04-14)

```
GET https://jccgis.jccal.org/server/rest/services/Basemap/Parcels/MapServer/0?f=json
-> HTTP 200  (application/json, ~11.2 KB)
```

Field count: 77. `currentVersion` 11.3. `maxRecordCount` 2000. Same short-path 404 pattern as Madison: the `jccgis.jccal.org/Parcels/MapServer/0` form in the registry is a label only; the real URL has the `server/rest/services/Basemap/` prefix shown in `seed_bi_county_config.py`.

## 3. Search / Query Capabilities

Query URL:

```
https://jccgis.jccal.org/server/rest/services/Basemap/Parcels/MapServer/0/query
```

| Parameter | Used? | Value | Notes |
|-----------|-------|-------|-------|
| `where` | YES | `OWNERNAME LIKE '%alias%'` (OR-batched) | All-caps owner field |
| `outFields` | YES | `*` | |
| `returnGeometry` | YES | `true` | |
| `outSR` | YES | `4326` | Reproject from StatePlaneALWest to WGS84 |
| `resultOffset` | YES | Paginated | |
| `resultRecordCount` | YES | 2000 | |
| `f` | YES | `json` | |

## 4. Field Inventory

77 fields total. Selected highlights (full list available via live probe):

| Field | Type | Mapped To | Notes |
|-------|------|-----------|-------|
| OBJECTID | OID | -- | |
| Unique_ID | Integer | -- | |
| PID | String | -- | |
| PARCELID | String | gis_parcel_field | Primary parcel key |
| TAX_TOWNSH, SEC, QSECTION, BLOCK, PARCEL | String | -- | PLSS + local grid components |
| ADDR_APR | String | gis_address_field | Appraiser-maintained situs address |
| Bldg_Number, Street_Name, Street_Type, Street_Dir, APARTMENT | String | -- | Component pieces |
| ADDR_PSPR | String | -- | Alternate address form |
| OWNERNAME | String | gis_owner_field | All-caps |
| PROP_MAIL, CITYMAIL, ZIP_MAIL, STATE_Mail | String | -- | Owner mailing |
| Legal_Desc | String | -- | |
| SUBDIV_NAME | String | gis_subdivision_field | Subdivision |
| NEIGHBOR_N, NbhName, NbhdCd | String | -- | Neighborhood variants |
| Cls | String | gis_use_field | Class / use code |
| ACRES_APR | Double | gis_acreage_field | |
| GIS_ACRES | Double | -- | GIS-calculated acreage (differs from appraiser) |
| AssdValue | Double | gis_appraised_value_field | Assessed value |
| TotalMHValue | Double | -- | Mobile-home value |
| PrevParcelLand, PrevParcelImp, PrevParcelTotal | Double | -- | Prior-period values |
| Plat_Book, Plat_Book2, Plat_Page, Plat_Page2 | String | -- | |
| ZONING_BOE | String | -- | |
| Water, Sewer, Gas | String | -- | Utility indicators |
| Division | String | -- | **Birmingham vs Bessemer Division marker** |
| RecordYear | Integer | -- | |
| Sqft | Double | -- | |
| SchDist, FireDist, FIREDEPTNAME, PriMunCode, SecMunCode | String | -- | Overlay districts |
| Shape + Shape.STArea() + Shape.STLength() | Geometry + Doubles | -- | |

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted per `seed_bi_county_config.py` L439-453:

- `OWNERNAME`, `PARCELID`, `ADDR_APR`, `Cls`, `ACRES_APR`, `SUBDIV_NAME`, `AssdValue`.
- **No building value field** (`gis_building_value_field` = `None`). Only land/assessed value. This is a real BI limitation compared to Madison or Baldwin.
- **No deed date field** (`gis_deed_date_field` = `None`). Last-transaction timing must come from the CD2 (LandmarkWeb) side.
- **No previous owner field**. PID-history chaining not possible from BI alone.

Non-disclosure state: again, no sale price is recoverable from the parcel layer (or from deeds). Jefferson has the additional wrinkle of dual probate divisions (Birmingham + Bessemer) on the CD2 side -- see `jefferson-county-deeds.md`.

## 6. Auth Posture / Bypass Method

Anonymous. Plain GETs. No referer or token requirements observed.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Owner | YES |
| Parcel | YES |
| Address | YES |
| Class/Use | YES |
| Acreage (appraiser) | YES |
| Subdivision | YES |
| Assessed value | YES |
| Building value | NO (field doesn't exist) |
| Deed date | NO (field doesn't exist) |
| Previous owner | NO (field doesn't exist) |
| Division (Birmingham/Bessemer) | NO (not currently harvested, though present) |
| Plat book/page | NO |
| Prior-period values | NO |
| Zoning | NO |

## 8. Known Limitations and Quirks

- Registry shorthand endpoint is NOT a real URL -- actual path is `server/rest/services/Basemap/Parcels/MapServer/0`.
- **No building value**, **no deed date**, **no previous owner** in this layer. Compared to Madison/Baldwin/Montgomery, Jefferson is the most feature-poor AL layer on the BI side.
- `ACRES_APR` (appraiser acreage) and `GIS_ACRES` (computed from geometry) disagree per parcel -- we use `ACRES_APR`.
- Spatial reference is **StatePlaneALWest** (WKID 102630), not Web Mercator. `outSR=4326` is required to return WGS84.
- 77 fields is 2x Madison's count -- most extras are overlay codes (fire/school/municipal) and component address pieces that we don't currently consume.
- "L L C" spaced-out entity name issue applies here too (see `AL-ONBOARDING.md`).
- `Division` field marks Birmingham vs. Bessemer; relevant for the CD2 recording-venue split but not yet consumed in BI.

Source of truth: `county-registry.yaml` (jefferson-al L571-583), `seed_bi_county_config.py` (L439-453), `AL-ONBOARDING.md`, live probe `https://jccgis.jccal.org/server/rest/services/Basemap/Parcels/MapServer/0?f=json`.
