# Citrus County FL -- ArcGIS (Research Only) API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | No active endpoint in `seed_bi_county_config.py` for Citrus |
| Registry status | `bi.portal: arcgis`, **status: inactive** (per `county-registry.yaml`) |
| Registry note | "SWFWMD-hosted endpoint unreliable. 6AM-10PM only." |
| Auth | Anonymous (for any candidate endpoint) |
| Probed candidate #1 | `https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer/2` |
| Probed candidate #2 | `https://www.citruspa.org` (Citrus Property Appraiser) |

This doc captures what was **attempted** during research. No endpoint is currently seeded. Builder Inventory does NOT run against Citrus today.

```
# seed_bi_county_config.py has NO Citrus entry as of 2026-04-14
# county-registry.yaml citrus-fl.bi:
#   portal: arcgis
#   status: inactive
#   notes: "SWFWMD-hosted endpoint unreliable. 6AM-10PM only."
```

---

## 2. Candidate #1 -- SWFWMD parcel_search (regional aggregator)

The Southwest Florida Water Management District (SWFWMD) publishes a regional parcel search MapServer that aggregates parcels for 17 counties, including Citrus.

### Reachability (probed 2026-04-14)

```
GET https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer?f=json
-> HTTP 200, "capabilities": "Map,Query,Data", 17 layers
```

### Layer inventory at that MapServer

| ID | Name |
|----|------|
| 0 | Property Appraiser Parcels |
| 1 | Charlotte County Parcels |
| **2** | **Citrus County Parcels** |
| 3 | DeSoto County Parcels |
| 4 | Hardee County Parcels |
| 5 | Hernando County Parcels |
| 6 | Highlands County Parcels |
| 7 | Hillsborough County Parcels |
| 8 | Lake County Parcels |
| 9 | Levy County Parcels |
| 10 | Manatee County Parcels |
| 11 | Marion County Parcels |
| 12 | Pasco County Parcels |
| 13 | Pinellas County Parcels |
| 14 | Polk County Parcels |
| 15 | Sarasota County Parcels |
| 16 | Sumter County Parcels |

### Layer 2 (Citrus County Parcels) metadata

| Property | Value |
|----------|-------|
| `maxRecordCount` | 1000 |
| `capabilities` | `Map,Query,Data` |
| Total fields | 95 |

### Field sample (SWFWMD Layer 2)

Key fields likely useful for BI. Field names are shared across all 17 SWFWMD county layers (this is a regional-schema roll-up).

| Field | Type | Alias |
|-------|------|-------|
| OBJECTID | OID | OBJECTID |
| PARNO | String | Local Parcel Number |
| NPARNO | String | National Parcel Number |
| OWNNAME | String | Full Owner Name |
| SITEADD | String | Full Site Address |
| SCITY | String | Site Address City |
| SZIP | String | Site Address Zip Code |
| PARUSECODE | String | Tax Parcel Use Code |
| PARUSEDESC | String | Tax Parcel Use Code Description |
| ACRES | Double | Acres from Deed |
| AREANO | Double | Area of Parcel as Number |
| SUBDIV_ID | String | Subdivision ID |
| SUBDIV_NM | String | Subdivision Name |
| LEGDECFULL | String | Full Legal Description |
| LEGAL2 | String | Second Legal Description |
| SOURCEDATE | Date | Source Document Date |
| SALE1_AMT | Integer | Most Recent Sale Amount |
| SALE1_DATE | String | Most Recent Sale Date |
| ASSD_TOT | Integer | Market Total Value |
| MRKT_BLD | Integer | Market Building Value |
| YRBLT_ACT | SmallInteger | Year Built Actual |
| TOT_LVG_AREA | Integer | Total living or usable area |
| PARCELID | String | Parcel ID |
| SITUSADD1 | String | Situs Address Line 1 |
| OWNERNAME | String | Owner Name |
| PALINK | String | Link to county Property Appraiser |
| WPARNO | String | Web Format Parcel Number |
| (other fields) | ... | ... |

Why it's listed as **inactive**: the `county-registry.yaml` note calls the SWFWMD endpoint "unreliable" with a "6AM-10PM only" uptime. Although the probe at doc-write time returned HTTP 200, the operator has historically observed dropouts and decided not to seed this endpoint into `seed_bi_county_config.py`.

---

## 3. Candidate #2 -- Citrus Property Appraiser

### Reachability (probed 2026-04-14)

```
GET https://www.citruspa.org
-> HTTP 200, 117 KB (human-facing PA site)
```

```
GET https://arcgis.citruspa.org/arcgis/rest/services
-> DNS failure: Could not resolve host: arcgis.citruspa.org
```

The Citrus PA operates a public search site at `citruspa.org` (HTML / proprietary UI), but an ArcGIS REST endpoint under an `arcgis.citruspa.org` subdomain does **not** exist. Any PA-hosted ArcGIS service would need to be discovered via the `citruspa.org` HTML (e.g., embedded ESRI JS API URLs), which was not done during this research pass.

---

## 4. Query Capabilities (SWFWMD candidate, not adopted)

If SWFWMD Layer 2 were adopted, the query surface would be identical to other SWFWMD-hosted Florida counties (e.g., Levy, which IS seeded via the same aggregator at layer 9):

```
GET https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer/2/query
    ?where=OWNNAME LIKE '%BUILDER%'
    &outFields=*
    &resultRecordCount=1000
    &f=json
```

Supported parameters: `where`, `outFields`, `returnGeometry`, `outSR`, `resultOffset`, `resultRecordCount`, `orderByFields`, `f` (JSON, geoJSON). Max record count is 1000.

---

## 5. Field Inventory

See Section 2 for the 26-field sample from the SWFWMD layer. The full layer has 95 fields covering parcel identity, ownership, address, use code, acreage, valuation, sale history, legal description, and construction metadata.

The **observed field mapping** that Builder Inventory would probably use (if seeded) is modeled on the SWFWMD-hosted Levy entry in `seed_bi_county_config.py`:

```python
{
    "name": "Levy", "state": "FL",
    "gis_endpoint": "https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer/9",
    "gis_owner_field": "OWNERNAME",
    "gis_parcel_field": "PARCELID",
    "gis_address_field": "SITUSADD1",
    "gis_use_field": "DORUSECODE",
    "gis_acreage_field": None,
}
```

A plausible Citrus entry (NOT seeded) would be:

| Purpose | SWFWMD Field |
|---------|--------------|
| Owner | `OWNERNAME` or `OWNNAME` |
| Parcel | `PARCELID` or `PARNO` |
| Address | `SITUSADD1` or `SITEADD` |
| Use | `PARUSEDESC` |
| Acreage | `ACRES` (deed acreage, not GIS-calculated) |
| Subdivision | `SUBDIV_NM` |
| Sale amount | `SALE1_AMT` |

---

## 6. What We Query

**Nothing.** `seed_bi_county_config.py` has no Citrus row. The BI pipeline skips Citrus entirely.

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available (if SWFWMD adopted) | SWFWMD Field |
|---------------|--------------------|---------|-------------------------------|--------------|
| Parcel ID | NO (not seeded) | -- | YES | `PARCELID`, `PARNO`, `NPARNO` |
| Owner | NO | -- | YES | `OWNNAME`, `OWNERNAME` |
| Address | NO | -- | YES | `SITEADD`, `SITUSADD1` |
| Subdivision name | NO | -- | YES (rare FL coverage) | `SUBDIV_NM`, `SUBDIV_ID` |
| Acreage | NO | -- | YES | `ACRES`, `AREANO` |
| Use code + description | NO | -- | YES | `PARUSECODE`, `PARUSEDESC`, `DORUSECODE` |
| Sale amount | NO | -- | YES | `SALE1_AMT` |
| Sale date | NO | -- | YES (string format) | `SALE1_DATE` |
| Market total value | NO | -- | YES | `ASSD_TOT`, `PARVAL` |
| Full legal description | NO | -- | YES | `LEGDECFULL`, `LEGAL2` |
| Geometry | NO | -- | YES (polygons) | `Shape` |

---

## 8. Geometry Handling

Not applicable -- no active geometry extraction for Citrus.

If adopted, the standard `_arcgis_to_geojson` path would convert SWFWMD's polygon rings to GeoJSON Polygon / MultiPolygon. SWFWMD stores geometry in Web Mercator; request `outSR=4326` to get WGS84.

---

## 9. Known Limitations and Quirks

1. **No seeded endpoint.** `seed_bi_county_config.py` does NOT contain a Citrus entry. The BI pipeline has never extracted Citrus parcels in production.

2. **Registry says `status: inactive`.** `county-registry.yaml` (`citrus-fl.projects.bi`) explicitly flags the SWFWMD candidate as unreliable with "6AM-10PM only" uptime. This is the documented reason the endpoint was never seeded, despite layer 2 being reachable at probe time.

3. **SWFWMD is a regional roll-up, not county-hosted.** If adopted, data freshness depends on SWFWMD's refresh cadence, which is not aligned to the Citrus PA's edit stream. Other counties in the same MapServer (e.g., Polk, Pasco) prefer county-native endpoints for exactly this reason.

4. **Citrus PA (`citruspa.org`) does not expose an ArcGIS REST subdomain.** The obvious `arcgis.citruspa.org` hostname does NOT resolve. A county-native ArcGIS service was not discovered during research. Any future discovery pass should inspect `citruspa.org` HTML for embedded service URLs.

5. **SWFWMD field naming has duplicates.** The layer exposes both `PARCELID` and `PARNO`, both `OWNNAME` and `OWNERNAME`, both `SITEADD` and `SITUSADD1`. Seeding Citrus would require choosing a canonical pair (the Levy seeded row uses `PARCELID` + `OWNERNAME` + `SITUSADD1`).

6. **No acreage-free seeding pattern.** SWFWMD has `ACRES` (deed acreage) and `AREANO` (calculated area as double). The Levy seeded row sets `gis_acreage_field: None` because that author chose not to trust either. Citrus would need the same decision.

7. **`6AM-10PM only` constraint.** Per the registry note, SWFWMD's parcel_search MapServer has been observed offline outside business hours. Any scheduled builder-inventory run for Citrus would need day-part scheduling.

8. **Do NOT fabricate a county-hosted Citrus endpoint.** No `gis.citruspa.org`, `maps.citrusbocc.com`, or similar endpoint was discovered during this research pass. Future researchers should confirm by URL discovery (browser dev tools against `citruspa.org`) rather than by guessing URL conventions.

9. **Citrus PA URL moved.** The `county-registry.yaml` `citrus-fl` entry contains a `citrus-county-pz.yaml` reference for CivicClerk under the subdomain `citrusclerk.portal.civicclerk.com` (note `citrusclerk`, not `citruspa`). The clerk and the property appraiser are separate organizations; only the clerk's CivicClerk is seeded.

10. **Accela permits are live; ArcGIS is not.** Citrus's PT project runs against Accela (`aca-prod.accela.com/CITRUS/`) and is `status: live`. The BI project is specifically noted as inactive pending a better parcel endpoint.

**Source of truth:** `county-registry.yaml` (`citrus-fl.projects.bi`), `seed_bi_county_config.py` (confirmed absence of Citrus row), live probe against `https://www45.swfwmd.state.fl.us/arcgis12/rest/services/BaseVector/parcel_search/MapServer/2?f=json` (HTTP 200, 95 fields), live DNS check against `arcgis.citruspa.org` (NXDOMAIN)
