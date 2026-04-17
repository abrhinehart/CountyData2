# Glades County FL -- ArcGIS (Absent / Not Onboarded) API Map (BI)

Last updated: 2026-04-14

## 1. Service Overview

| Property | Value |
|----------|-------|
| Platform | ArcGIS (NONE configured; no public REST surface identified) |
| Endpoint | n/a (no county-hosted or AGO-hosted REST service with parcel attributes is configured) |
| Registry status | **ABSENT -- not in `county-registry.yaml` at all** |
| Seed config status | **ABSENT -- Glades is NOT in `seed_bi_county_config.py`** |
| Database-seed presence | `counties` table only -- `migrations/011_counties_and_subdivision_geometry.sql` L22 includes `('Glades')` in the 67 FL county name seed list |
| Parser | (not configured) |
| Reason documented | Glades has NOT been onboarded in BI. It is the ONLY FL county name in this doc set that appears neither in the seed list nor in the registry -- only as a county-name row in the migration. |

---

## 2. Why This Is a Stub

Glades County is absent from both of the two canonical BI configuration sources in this repo:

1. **`seed_bi_county_config.py`** -- `COUNTY_GIS_CONFIGS` includes every seeded FL county (Bay, Charlotte, Collier, Hendry, Lee, Okeechobee, Santa Rosa, Sarasota, etc.). Glades has NO entry. There is no `gis_endpoint`, no field mapping, no adapter wiring for Glades parcel data.
2. **`county-registry.yaml`** -- the three-project registry (bi/pt/cr/cd2) has no `glades-fl` key. No `projects.bi`, no `notes`, no status.

The ONLY presence of the string `Glades` in the data-layer repo files is at `migrations/011_counties_and_subdivision_geometry.sql` L22, where the 67 FL county names are seeded into the `counties` table as part of the initial migration:

```sql
-- Seed all 67 Florida counties (uses NOT EXISTS to work before and after 013 constraint change)
INSERT INTO counties (name)
SELECT name FROM (VALUES
    ('Alachua'), ('Baker'), ('Bay'), ('Bradford'), ('Brevard'),
    ('Broward'), ('Calhoun'), ('Charlotte'), ('Citrus'), ('Clay'),
    ('Collier'), ('Columbia'), ('DeSoto'), ('Dixie'), ('Duval'),
    ('Escambia'), ('Flagler'), ('Franklin'), ('Gadsden'), ('Gilchrist'),
    ('Glades'), ('Gulf'), ('Hamilton'), ('Hardee'), ('Hendry'),
    ...
```

Glades has a row in the `counties` table (for referential integrity), but nothing more. Any BI pipeline that iterates the registry or the seed list will silently skip Glades.

---

## 3. Diff vs Walton (registry-inactive) and Hendry (seed-only)

Glades is the leanest BI stub in the doc set -- even leaner than Walton (which at least has a `walton-fl.projects.bi` block flagged `inactive`) or Hendry (which is seeded in `seed_bi_county_config.py` despite being absent from the registry).

| Attribute | Glades | Walton (registry-inactive) | Hendry (seed-only) |
|-----------|--------|----------------------------|--------------------|
| In `seed_bi_county_config.py`? | **NO** | NO | YES (L121-129) |
| In `county-registry.yaml`? | **NO** | YES (L369-372, `status: inactive`) | NO |
| BI status | **absent -- not onboarded** | `inactive` (qPublic UI only) | active (seeded) |
| Has an identified public REST? | **NO (none searched / documented)** | NO (qPublic is UI-only) | YES (`services7.arcgis.com/8l7Qq5t0CPLAJwJK/...`) |
| Adapter to scrape | none | would require qPublic HTML scraping | `GISQueryEngine` (standard) |
| DB row in `counties` | YES (via migration 011 L22) | YES (standard) | YES (standard) |
| Other registry slots (pt, cr, cd2) | NONE | tracked (CR manual, CD2 LandmarkWeb, PT Tyler EnerGov) | NONE |

---

## 4. What Would an Onboarding Look Like

Not in scope for this doc, but a future engineer onboarding Glades BI would need to:

1. Identify whether the Glades Property Appraiser publishes a public ArcGIS REST endpoint. Glades is a small, rural south-central FL county (pop. ~12k); many small counties lack a dedicated GIS server and instead rely on qPublic / Schneider or a regional data-sharing arrangement.
2. If an endpoint exists, add a new block to `seed_bi_county_config.py` with `name`, `gis_endpoint`, `gis_owner_field`, `gis_parcel_field`, `gis_address_field`, `gis_use_field`, `gis_acreage_field`.
3. Optionally add a `glades-fl.projects.bi` block to `county-registry.yaml`.
4. Write a doc (`glades-county-arcgis.md`) with the live metadata matrix.

**This doc does NOT create any of the above.** Per Planner's directive, this is a gap flag only.

---

## 5. Endpoints That Are NOT Configured

| Surface | Configured? |
|---------|-------------|
| ArcGIS FeatureServer / MapServer | NO |
| qPublic PA UI (Schneider Geospatial) | Unknown -- not investigated in this pass |
| CAMA export / flat file | NO |
| AGO open-data tenant | NO |

---

## 6. Known Limitations and Quirks

1. **Glades is ABSENT from `seed_bi_county_config.py`.** Not a single line. The seed list covers every other FL county treated in this doc set (Charlotte, Lee, Hendry, Collier, Sarasota); Glades alone has no entry.

2. **Glades is ABSENT from `county-registry.yaml`.** No `glades-fl` key. No projects declared. No `notes` field.

3. **Glades row exists ONLY in `migrations/011_counties_and_subdivision_geometry.sql` L22** as part of the 67-county VALUES list inserted into the `counties` table. This ensures referential integrity for any FK that references `counties.name = 'Glades'`, but grants zero functional BI capability.

4. **Leanest stub in the FL doc set.** Walton has a registry entry (inactive); Hendry has a seed entry (active). Glades has neither. This doc is the thinnest BI absence-flag in the repo.

5. **Small county / low priority.** Glades' population (~12,000) and rural character likely drove the deprioritization. Many larger FL counties with AGO tenants have been seeded first.

6. **No adapter, no parser, no query machinery.** Even a `GISQueryEngine`-based generic probe would have nothing to point at -- the `gis_endpoint` key is missing from the config dict, so any loop over `COUNTY_GIS_CONFIGS` cannot encounter Glades.

7. **Any cross-project pipeline must skip Glades gracefully.** Workflows that iterate `county-registry.yaml` keys or `COUNTY_GIS_CONFIGS` entries naturally do (Glades is not there). Workflows that iterate the `counties` SQL table (which DOES have a Glades row) must join against one of the config sources and handle the NULL.

8. **No known PA REST surface.** Unlike Hendry (which has an AGO tenant) or Charlotte (which has a county-hosted MapServer), no public Glades parcel REST endpoint has been identified in the repo. This research step has NOT been performed as part of this doc -- the absence is a reflection of the repo's current state, not a definitive statement that no surface exists.

9. **Migration 011 is where Glades lives in the codebase.** Any code tracing the source of the Glades entry will arrive at `migrations/011_counties_and_subdivision_geometry.sql` L22 as the sole mention.

### Related surfaces not yet documented

- **Glades PT:** No permit adapter exists.
- **Glades CR:** No jurisdiction YAML under `modules/commission/config/jurisdictions/FL/`.
- **Glades CD2:** No clerk-recording surface documented. Clerk not in `LANDMARK_COUNTIES`.

**Source of truth:** absence from `seed_bi_county_config.py` (`COUNTY_GIS_CONFIGS` list -- no Glades block), absence from `county-registry.yaml` (no `glades-fl` key), sole presence at `migrations/011_counties_and_subdivision_geometry.sql` L22 in the 67-county seed VALUES list
