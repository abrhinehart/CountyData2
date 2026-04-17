# Walton County FL -- ArcGIS (Inactive / No Public REST) API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS (NONE exposed publicly with owner data) |
| Endpoint | n/a (no county-hosted REST service with parcel owner attributes) |
| Registry status | `bi: inactive` (per `county-registry.yaml` L369-372) |
| Registry note (verbatim) | "No county-hosted ArcGIS REST with owner data." |
| PA public viewer | qPublic (Schneider Geospatial), not a REST surface |
| Parser | (not configured) |
| Reason documented | Scraping Walton BI from a REST FeatureServer / MapServer is not possible; the county's parcel records are locked behind a qPublic UI without an exposed layer URL |

---

## 2. Why This Is a Stub

Walton County is the only Florida county in the three-project registry where the `bi` slot is marked **`inactive`**. Every other FL county the BI pipeline has considered exposes one of:

- An AGO (ArcGIS Online) hosted FeatureServer tenant (Santa Rosa, Baker, Putnam variants)
- A county-hosted MapServer or FeatureServer (Polk, Bay, Okaloosa, Clay, Escambia)

Walton has neither. The Property Appraiser (`waltonpa.com`) presents a qPublic-branded parcel search that does not expose a discoverable ArcGIS REST endpoint with owner, address, or use data. A geocoding basemap may exist on `waltoncountyfl.gov`, but it does NOT back an owner-level parcel query API.

```
# What does NOT exist:
https://gis.waltoncountyfl.gov/arcgis/rest/services/Parcels/FeatureServer/0   -> not published
https://services*.arcgis.com/<waltonOrg>/arcgis/rest/services/Parcels/...     -> no public tenant
```

```
# What DOES exist (non-REST, UI-only):
https://qpublic.schneidercorp.com/Application.aspx?App=WaltonCountyFLPA        -> qPublic HTML UI
```

---

## 3. Diff vs Okeechobee (active AGO peer)

The gap is most visible compared to a small peer like Okeechobee whose parcel data is fully queryable.

| Attribute | Walton | Okeechobee |
|-----------|--------|------------|
| BI status | **`inactive`** | `active` |
| Public REST endpoint | **none** | `services3.arcgis.com/jE4lvuOFtdtz6Lbl/...` |
| Parcel schema | not exposed | 27 fields (Owner1, ParcelID, StreetName, Acerage...) |
| PA front door | qPublic HTML (JS-rendered) | Tyler Technologies map + FeatureServer |
| Adapter to scrape | **would require HTML scraping of qPublic** | standard `GISQueryEngine` |
| Refresh cadence | unknown (no REST to probe) | Monthly (per Tyler tenant service desc) |

---

## 4. Known Limitations and Quirks

1. **`status: inactive` in `county-registry.yaml` L369-372.** Walton is flagged inactive for BI explicitly. Any attempt to spin up a scraper against a hypothetical Walton FeatureServer will fail because the URL does not exist.

2. **qPublic is UI-only.** The Walton PA uses Schneider's qPublic HTML application. Unlike Esri-based front ends, qPublic does not back a documented public REST API for batch parcel queries. Scraping it requires driving the HTML UI with a browser (Playwright / Selenium).

3. **No `seed_bi_county_config.py` entry.** Unlike Santa Rosa, Okaloosa, Putnam, Baker, Clay, etc., Walton does not appear in the `COUNTY_GIS_CONFIGS` list. This is intentional: there is no endpoint to seed.

4. **The other two Walton surfaces ARE active.** CR is live via manual AgendaCenter workflow (`walton-county-civicplus.md`); CD2 is live via LandmarkWeb with Cloudflare TLS impersonation (`walton-county-landmark.md`); PT is live via Tyler EnerGov (`walton-county-tyler-energov.md`). Only BI is blocked.

5. **No alternate public Walton owner data source has been identified** as of 2026-04-14 other than the qPublic UI. The registry `notes:` field explicitly documents this: "No county-hosted ArcGIS REST with owner data."

**Source of truth:** `county-registry.yaml` (`walton-fl.projects.bi` block, lines 369-372 -- entire block is `portal: arcgis`, `status: inactive`, `notes: "No county-hosted ArcGIS REST with owner data."`), absence of any Walton entry in `seed_bi_county_config.py`.
