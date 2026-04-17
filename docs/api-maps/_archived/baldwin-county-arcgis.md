# Baldwin County AL -- ArcGIS Server (utility.arcgis.com proxy) Parcels API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS Server behind Esri `utility.arcgis.com` secure-usrsvcs proxy |
| Host | `utility.arcgis.com` |
| Service | `usrsvcs/servers/c6d99b6b381f4851be35a045e2adb7a8/rest/services/Baldwin/Permitting_MS/MapServer` |
| Layer | Layer 75 -- "Parcels Planning App" |
| Geometry Type | `esriGeometryPolygon` |
| Source Spatial Reference | WKID 102100 / latestWkid 3857 (Web Mercator) |
| Max Record Count | **10000** (the highest of any AL county BI layer in the registry) |
| Auth | Anonymous via the Esri-provided usrsvcs proxy (see Auth Posture) |
| Registry entry | `county-registry.yaml` L585-598 (`baldwin-al.projects.bi`) |
| BI config | `seed_bi_county_config.py` L454-470 |

Baldwin's parcel service is fronted by Esri's `utility.arcgis.com/usrsvcs/servers/<guid>/...` secure-token-handling proxy. The proxy resolves our anonymous request to an upstream token-authed origin; AGOL-token pattern is handled transparently on Esri's side. 793 DR Horton / 292 Lennar / 200 DSLD / 182 Adams Homes parcels are currently on this layer per registry notes -- Baldwin is the highest-volume AL county for our primary tracked builders.

## 2. Probe (2026-04-14)

```
GET https://utility.arcgis.com/usrsvcs/servers/c6d99b6b381f4851be35a045e2adb7a8/rest/services/Baldwin/Permitting_MS/MapServer/75?f=json
-> HTTP 200  (application/json, ~56 KB)
```

Field count: **135** -- the largest of the 4 AL counties in this batch, by a wide margin. `currentVersion` 10.71. `maxRecordCount` 10000. **Anonymous probe succeeded**; the `usrsvcs` proxy handles AGO token acquisition on Esri's side, so callers do not need to present a token themselves.

The task plan anticipated a 401/403 response here. In practice, the `usrsvcs/servers/<guid>/rest/services/...` URL returned 200 directly. If the upstream AGO item's sharing is ever tightened, the proxy could start returning 401 and this assumption would need re-validation.

## 3. Search / Query Capabilities

Query URL:

```
https://utility.arcgis.com/usrsvcs/servers/c6d99b6b381f4851be35a045e2adb7a8/rest/services/Baldwin/Permitting_MS/MapServer/75/query
```

| Parameter | Used? | Value | Notes |
|-----------|-------|-------|-------|
| `where` | YES | `Owner LIKE '%alias%'` (OR-batched) | Mixed-case Owner field |
| `outFields` | YES | `*` | |
| `returnGeometry` | YES | `true` | |
| `outSR` | YES | `4326` | |
| `resultOffset` | YES | Paginated | |
| `resultRecordCount` | YES | up to 10000 | Matches service max |
| `f` | YES | `json` | |

## 4. Field Inventory

135 fields total. Highlights that drive BI extraction + FST-prefix trust-parcel quirk:

| Field | Type | Mapped To | Notes |
|-------|------|-----------|-------|
| OBJECTID | OID | -- | |
| PIN | String | -- | |
| PINPAD | String | -- | |
| PID | String | -- | |
| State | String | -- | Usually "AL" |
| PreviousOwner | String | gis_previous_owner_field | |
| Owner | String | gis_owner_field | **Trust-held parcels use `FST` prefix** (see quirks) |
| PARCELID | String | gis_parcel_field | Primary parcel key |
| MailAdd1/2/3, MailCity, MailState, MailZip1, MailZip2 | String | -- | Owner mailing |
| SitusAddName, SitusAddNumber, SitusAddCity | various | -- | Situs components |
| Full_Address | String | gis_address_field | Concatenated form |
| CalcAcres | Double | gis_acreage_field | |
| CalcAcre, DeededAcres, TimberAcres | Double | -- | Alternate acreage forms |
| Subdivision | String | gis_subdivision_field | |
| SubdivisionCode | String | -- | |
| SubLot, SubBlock | String | -- | |
| Neighborhood, NeighborhoodSub | String | -- | |
| LegalDescription | String | -- | |
| PropertyClass | String | gis_use_field | |
| PropertySubClass | String | -- | |
| ZoningCode, ZoningDesc | String | -- | |
| CImpValue | Double | gis_building_value_field | |
| CLandValue | Double | gis_appraised_value_field | |
| TTV, TAV | Double/Int | -- | Total taxable / assessed value |
| AssessedRate | String | -- | |
| DeedBook, DeedPage | String | -- | |
| DeedRecorded | Date | gis_deed_date_field | Primary deed-date column |
| DeedSigned | Date | -- | Alternate deed-date (signed vs recorded) |
| CurrentUseValue, HasCurrentUse | Double/String | -- | Agricultural/timber current-use assessment |
| FLAG1..FLAG6 | String | -- | Internal flags |
| Lat, Long, Elev | Double/Int | -- | Parcel centroid (redundant with geometry but convenient) |
| (addressing components St_PreDir, St_PreTyp, St_Name, St_PosDir, St_PosMod, etc.) | String | -- | Fine-grained NENA-style address breakdown |
| created_date, last_edited_date, DateUpdate, Effective, Expire | Date | -- | Provenance |
| Created_User, Last_Edited_User | String | -- | |
| Anomoly [sic] | String | -- | Misspelled in source; preserve literally |
| Shape + SHAPE.STArea() + SHAPE.STLength() | Geometry + Doubles | -- | |

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted (9 fields per `seed_bi_county_config.py` L454-470):

- `Owner`, `PARCELID`, `Full_Address`, `PropertyClass`, `CalcAcres`, `Subdivision`, `CImpValue`, `CLandValue`, `DeedRecorded`, `PreviousOwner`.

Baldwin is the most feature-complete AL layer for BI -- unlike Jefferson it has building value and deed date; unlike Madison it has a proper property-class field.

Non-disclosure state: `DeedRecorded` is a date only; no consideration/sale-price column exists here (or elsewhere in AL), matching the other three counties.

## 6. Auth Posture / Bypass Method

Anonymous from the caller's perspective. The `utility.arcgis.com/usrsvcs/servers/<guid>/` proxy is Esri's "secure service access" relay -- it holds an AGO token upstream and presents the service anonymously to the outside world. CountyData2 does not need to present or rotate a token.

If the upstream item's sharing tightens (e.g., removed from the org's "everyone" audience), this anonymous proxy would start returning 401 / 403. **No such 401 observed in the 2026-04-14 probe.** If it appears in future, it means the county or the hosting group rotated the item's share settings.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Owner / PreviousOwner | YES |
| Parcel | YES |
| Full address | YES |
| Property class / subclass | YES (class) / NO (subclass) |
| Calc acres | YES |
| Deeded acres | NO |
| Subdivision | YES |
| Subdivision code | NO |
| Lot / Block | NO |
| Neighborhood | NO |
| Legal description | NO |
| Zoning code + desc | NO |
| Building value (CImpValue) | YES |
| Land value (CLandValue) | YES |
| TTV / TAV / current-use value | NO |
| Deed book / page | NO |
| DeedRecorded | YES |
| DeedSigned | NO |
| Provenance dates | NO |
| Lat/Long centroid | NO (use geometry) |

## 8. Known Limitations and Quirks

- **`FST` owner-name prefix for trust-held parcels**: Baldwin's data convention prefixes owner names with `FST` (Family Savings Trust / First Surviving Trust style abbreviation conventions -- varies by county). Alias lists for DR Horton / Lennar / DSLD / Adams Homes should anticipate `FST`-wrapped trust forms if they ever hold parcels in trust. The registry notes `"Uses FST prefix for trust-held parcels"` under `baldwin-al.projects.bi.notes`.
- **135 fields** -- 3x the count of most counties. Most unextracted columns are NENA-style addressing components and provenance dates; extract-worthiness is low unless a downstream consumer needs them.
- **`Anomoly` field is misspelled** in the source; preserve the spelling verbatim if the field is ever extracted.
- `maxRecordCount = 10000` -- largest page size of any AL BI layer. Still paginate to avoid runaway URL lengths in batched-OR WHERE clauses.
- `usrsvcs` proxy is anonymous today but is token-mediated upstream; **token model could change** if the AGO item's sharing is tightened. **unverified upstream** -- we only see what the proxy serves.
- Non-disclosure state applies (no sale price). Four builders (DR Horton, Lennar, DSLD, Adams Homes) hold ~1450 parcels combined in Baldwin per the registry notes -- the highest-volume AL county for tracked builders.
- `L L C` spacing applies (AL assessor convention).

Source of truth: `county-registry.yaml` (baldwin-al L585-598), `seed_bi_county_config.py` (L454-470), `AL-ONBOARDING.md`, live probe `https://utility.arcgis.com/usrsvcs/servers/c6d99b6b381f4851be35a045e2adb7a8/rest/services/Baldwin/Permitting_MS/MapServer/75?f=json`.
