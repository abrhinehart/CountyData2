# Seminole County FL -- ArcGIS Property Details API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | Esri ArcGIS Enterprise routed via `utility.arcgis.com` token server |
| Service name | `Property Details` (MapServer layer 1 under InformationKiosk) |
| Root URL | `https://utility.arcgis.com/usrsvcs/servers/9b9c9fd45bdc4c39a2bd518da39d1e1c/rest/services/InformationKiosk/MapServer/1` |
| Token-server token | `9b9c9fd45bdc4c39a2bd518da39d1e1c` (baked into URL path — NOT a query-string token) |
| Host | `utility.arcgis.com` (Esri-hosted token-proxy, not county-hosted) |
| Geometry | `esriGeometryPolygon` |
| Spatial Reference | wkid 102658 / latest 2236 (NAD83 HARN StatePlane Florida East FIPS 0901 Feet) |
| Current version | 10.91 (cimVersion 2.9.0) |
| Max record count | 1000 |
| Display field | `PlatName` |
| Auth | Anonymous — token is embedded in URL, acts as shared secret |
| Field count | 53 |
| Registry status | `bi: active` per `county-registry.yaml` L509-518 |
| Registry note | "Token-served private-but-public endpoint via utility.arcgis.com." |

## 2. Probe (2026-04-14)

```
GET https://utility.arcgis.com/usrsvcs/servers/9b9c9fd45bdc4c39a2bd518da39d1e1c/rest/services/InformationKiosk/MapServer/1?f=json
-> HTTP 200, 11,644 bytes, application/json
   currentVersion=10.91, cimVersion="2.9.0", id=1, name="Property Details",
   type="Feature Layer", geometryType="esriGeometryPolygon",
   sourceSpatialReference.wkid=102658, maxRecordCount=1000, 53 fields.

GET https://utility.arcgis.com/usrsvcs/servers/.../MapServer/1/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
-> HTTP 200, 8,372 bytes
   displayFieldName="PlatName", one feature returned.
```

**Token freshness:** responded 200 on 2026-04-14 — token is currently live. Per the registry note: "if 401/403, the token is stale" (per plan exception note 5).

## 3. Query Capabilities

Standard ArcGIS REST `/query` at the token-proxy path:

| Parameter | Used | Notes |
|-----------|------|-------|
| `where` | YES | `1=1` bulk or attribute filters |
| `outFields` | YES | `*` or narrow subset |
| `resultRecordCount` | YES | Capped at 1000 |
| `resultOffset` | YES | Pagination cursor |
| `returnGeometry` | Supported | |
| `f` | YES | `json` |

**Pagination:** 1000-record pages. Seminole has ~160k parcels; plan for ~160 paginated calls.

**Date-range:** `ApprovedZoning` and `ApprovedFLU` are Date type — can filter recent zoning/land-use approvals, but BI engine uses static snapshots.

## 4. Field Inventory (selected, 53 total)

| Field | Type | Alias | Notes |
|-------|------|-------|-------|
| OBJECTID | OID | | |
| **ParcelNumber** | String | ParcelNumber | Canonical parcel ID |
| GISAcres | Double | GISAcres | GIS-computed acreage |
| SubdivisionNumber | String | | |
| **PlatName** | String | PlatName | **displayField — subdivision/plat name** |
| CityName | String | CityName | Municipality |
| USCongressDistrict | SmallInteger | | |
| USCongressionalName | String | | |
| CommissionerDistrict | SmallInteger | District | (alias overrides name) |
| CommissionerName | String | | |
| ElementarySchoolDistrict / MiddleSchoolDistrict / HighSchoolDistrict | String | | School zones |
| PowerCompanyName / PhoneCompanyName | String | | Utility providers |
| WaterServiceArea / WaterDistrict | String | | |
| SewerServiceArea / SewerDistrict | String | | |
| Zoning | String | | Zoning code |
| ZoningOrdinanceNumber | String | | |
| ApprovedZoning | Date | | |
| PDName | String | PDname | (alias overrides case) Planned Development name |
| FutureLandUse | String | | |
| FutureLandUseOrdinanceNumber | String | | |
| ApprovedFLU | Date | | |
| FloodZone | String | | |
| ProtectionAreaName | String | | Environmental protection overlay |
| Seminole | String | | |
| StateHouseDistrict | SmallInteger | | |

23 additional fields include state senate / commissioner-district subdivisions, GIS geometry computations, and additional overlay / governance-district columns.

**Notable omissions:** This `Property Details` layer exposes zoning / overlay / district data but **does NOT expose owner name or street address** directly. Owner / address data for Seminole is served on a different layer (likely the Property Appraiser's separate service).

**BI-registry field mapping gap:** `county-registry.yaml` L509-518 has `bi: active` but does NOT specify the 5-field column mapping inline. Probable partial mapping:

| BI canonical | Seminole field candidate |
|--------------|-------------------------|
| owner | **NOT AVAILABLE on this layer** — must join from Property Appraiser service |
| parcel | **ParcelNumber** |
| address | **NOT AVAILABLE on this layer** — no street-level address columns |
| use | Zoning (code) — or FutureLandUse; neither is a FL DOR use code |
| acreage | **GISAcres** |

`unverified — needs validation` — Seminole BI likely pulls from a sibling layer for owner/address; this layer's role is primarily overlay/district metadata.

## 5. What We Extract / What a Future Adapter Would Capture

Current state: `bi: active` in registry but the layer 1 data alone does NOT cover the canonical 5 fields. Two likely scenarios:

1. The BI pipeline uses this layer for parcel + acreage + zoning + commissioner district, and joins owner/address from a separate Seminole Property Appraiser service.
2. The registry `bi: active` flag reflects the Property Appraiser service at a different URL, and `utility.arcgis.com/.../InformationKiosk/MapServer/1` is a secondary reference layer.

The registry's endpoint string `utility.arcgis.com/InformationKiosk/MapServer/1` matches this layer. If BI is using only this layer, owner / address columns are missing from the pipeline and would register as NULLs.

## 6. Bypass Method / Auth Posture

- **Embedded-token shared-secret scheme.** The URL hex string `9b9c9fd45bdc4c39a2bd518da39d1e1c` is an Esri `usrsvcs` server token — acts as both identifier and access credential.
- `utility.arcgis.com` is Esri's token-proxy fronting a private ArcGIS Enterprise instance. The token rewrites the request into the backend tenant context.
- Anonymous from the client POV; if the token is rotated by the county, 401 or 403 follows.
- No tokens in headers or query string — the URL path IS the authentication.

## 7. What We Extract vs What's Available

| Category | Extracted (assumed) | Available on Layer 1 | Notes |
|----------|---------------------|----------------------|-------|
| Parcel ID | YES | ParcelNumber | |
| Plat name | NO | PlatName | displayField |
| GIS acreage | YES | GISAcres | |
| Owner | **NO — not on this layer** | -- | Separate Property Appraiser service required |
| Address | **NO — not on this layer** | -- | Separate source required |
| Use code (traditional FL DOR) | NO | -- | Zoning code ≠ DOR use code |
| Zoning | NO | Zoning, ZoningOrdinanceNumber, ApprovedZoning | Structured zoning breakdown |
| Future land use | NO | FutureLandUse, ApprovedFLU | Comprehensive plan overlay |
| Commissioner / school / utility districts | NO | Multiple columns | District-level governance metadata |
| Flood zone | NO | FloodZone | |
| Planned Development name | NO | PDName | |
| Geometry | Optional | YES | Polygon |

## 8. Known Limitations and Quirks

1. **Token baked in URL path** — `9b9c9fd45bdc4c39a2bd518da39d1e1c`. This is a shared-secret that Seminole manages outside the client's control. If/when it rotates, every downstream consumer (CountyData2 BI, web maps, any other integration) simultaneously breaks with 401/403.
2. **`utility.arcgis.com` is Esri's token-proxy infrastructure** — requests traverse Esri's production routing even though the backend is the county's ArcGIS Enterprise. Outages on `utility.arcgis.com` affect this pipeline regardless of county network state.
3. **53 fields on Layer 1 — does NOT include owner / address.** Unique among the 6 counties in this batch: the layer chosen for BI does not naturally serve all 5 canonical columns. BI adapter for Seminole either joins sibling data or runs with NULL owner / address.
4. **`Property Details` naming** — the layer's purpose is overlay/governance metadata (zoning, school zones, districts, utility service areas), not parcel ownership. Compare to other counties' `Parcels` layers which bundle ownership + geometry.
5. **`PlatName` as displayField** — subdivision/plat name is the default label when the layer is rendered. Useful for cross-referencing parcels to subdivisions but not traditional owner-based identification.
6. **Commissioner district alias `District`** — column `CommissionerDistrict` (SmallInteger) has alias `District`. In outFields requests, use the column name, not the alias.
7. **`PDName` alias is `PDname`** — alias differs from column name only by case. Preserve column case in requests.
8. **Layer index = 1** — layer 0 of the same InformationKiosk service may hold sibling data. Only layer 1 ("Property Details") is catalogued by `county-registry.yaml`.
9. **ZoningOrdinanceNumber / FutureLandUseOrdinanceNumber** — lookups to the ordinance text itself live elsewhere; the layer exposes only the reference number.
10. **The registry's endpoint string `utility.arcgis.com/InformationKiosk/MapServer/1`** omits the intermediate `/usrsvcs/servers/<token>/rest/services/` segments. The canonical full URL is required for the adapter; registry's abbreviated form is for human reference only.
11. **Token liveness confirmed 2026-04-14** — `9b9c9fd45bdc4c39a2bd518da39d1e1c` returns HTTP 200. If future runs see 401/403 here, the first troubleshooting step is confirming token rotation with the county (not rewriting the adapter).
12. **County name `CityName`** may be literal "Seminole County" (for unincorporated parcels) or one of the municipalities (Altamonte Springs, Casselberry, Lake Mary, Longwood, Oviedo, Sanford, Winter Springs) — the field distinguishes incorporated-vs-unincorporated parcels cleanly.

Source of truth: `county-registry.yaml` L509-518 (`seminole-fl.projects.bi`), live probes of the token-proxy URL (2026-04-14, HTTP 200, 11,644 bytes metadata + 8,372 bytes one-record query, 53 fields). Owner/address field mapping `unverified — needs validation` against `seed_bi_county_config.py` (not inspected) — Seminole BI likely requires a sibling service join for full 5-field coverage.
