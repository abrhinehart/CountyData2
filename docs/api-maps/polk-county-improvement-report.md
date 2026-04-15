# Polk County Scrapers vs API Maps — Improvement Report

Last updated: 2026-04-15

Source api-maps:
- [polk-county-accela.md](polk-county-accela.md)
- [polk-county-arcgis.md](polk-county-arcgis.md)
- [polk-county-iworq.md](polk-county-iworq.md)
- [polk-county-legistar.md](polk-county-legistar.md)

Related findings:
- [accela-rest-probe-findings.md](accela-rest-probe-findings.md) — April 2026 probe establishing REST is not a viable path for bulk public extraction. Materially revises the ACCELA-02 recommendation below.

Source scrapers:
- `modules/permits/scrapers/adapters/polk_county.py`, `accela_citizen_access.py`, `lake_alfred.py`, `winter_haven.py`
- `modules/permits/scrapers/adapters/iworq.py`, `davenport.py`, `haines_city.py`, `lake_hamilton.py`
- `modules/commission/scrapers/legistar.py` + `modules/commission/config/jurisdictions/FL/polk-county-{bcc,pz,boa}.yaml`
- `seed_bi_county_config.py` (Polk row lines 238-250), `seed_pt_jurisdiction_config.py` (Polk rows lines 28-75)

## Legend

- **Priority:** `P0` = correctness / data-integrity / drift; `P1` = high-value coverage expansion; `P2` = nice-to-have
- **Effort:** `S` < 1 day · `M` 1-3 days · `L` > 3 days
- **Risk:** `Low` · `Med` · `High` — risk of breakage to current flows when making the change

## Executive Summary

- **Highest-ROI single change (P0, S):** Fix the api-map / seed drift for the Polk ArcGIS (BI) surface. `seed_bi_county_config.py` already maps **9 fields** for Polk (parcel, owner, address, use, acreage, subdivision, building_value, appraised_value, deed_date), but the api-map states only 5 are mapped. Either the seed has not been run against the production DB, or the api-map is stale. A one-row DB check + api-map correction removes a false "gap" and unblocks correct prioritization of the other BI gaps. See `ARCGIS-00`.
- **Highest strategic-value multi-session project (P1, L):** Harden and expand the Accela HTML extraction path — specifically, wire the Inspections-tab sub-page fetch (ACCELA-06), add structured contact/owner DOM parsing (ACCELA-03, ACCELA-04), and iterate over the 34+ record types (ACCELA-01). An April 2026 v4 REST probe across POLKCO, CITRUS, COLA, BOCC, and BREVARD established that Accela v4 REST is designed for authorized integrations, not bulk anonymous extraction: no tested Florida agency has the "anonymous user" toggle enabled (all return `anonymous_user_unavailable`), and ~half of the relevant endpoints require a bearer token even when it is enabled. The ACA citizen-portal HTML path is the mechanism Accela designed for our use case. See [accela-rest-probe-findings.md](accela-rest-probe-findings.md) and ACCELA-02 below for the full reframing.
- **Most urgent drift / correctness concern (P0, S):** `AccelaCitizenAccessAdapter._parse_inspections` returns silently `None` for Polk because Polk's inspection data lives on a separate "Record Info > Inspections" tab, not inline on CapDetail.aspx. The unit tests use synthetic HTML with a direct `<h3>Inspections</h3>` + `<table>` and therefore cannot catch this. The adapter populates `permit["inspections"] = None` while emitting no warning, giving the illusion of a feature that silently produces no data. See `ACCELA-05`.

---

## Surface 1 — Polk Accela (PT)

### Current State

`PolkCountyAdapter(AccelaCitizenAccessAdapter)` (5 lines) sets `agency_code="POLKCO"`, `module_name="Building"`, `target_record_type="Building/Residential/New/NA"`. All work happens in the shared base `accela_citizen_access.py`. The same base also drives `LakeAlfredAdapter` (agency `COLA`) and `WinterHavenAdapter` (agency `COWH`, marked fixture-mode because the portal requires login).

Extraction is 100% HTML scraping:
- Search: ASP.NET `__VIEWSTATE` postback against `CapHome.aspx`, submitting date range + single `ddlGSPermitType`.
- Pagination: `__doPostBack(...)` on Next link; binary date-range splitting when `total >= search_result_cap=100`.
- Detail: `CapDetail.aspx` GET; `soup.get_text(" ").split()` flattened into a single string, then 6 regex patterns (`parcel_pattern`, `subdivision_pattern`, `applicant_pattern`, `licensed_professional_pattern`, `project_description_pattern`, inline Job Value regex).
- Inspections: `_parse_inspections` searches the detail HTML for a heading containing "inspection" then the next `<table>`, or div-based patterns. No separate tab fetch.
- Address: FL-only regex (`^street, city FL zip$`). No lat/lon.
- `detail_request_delay = 0.0`. No per-agency override on Polk.

### API Map Reveals

1. ~30+ fields are visible on `CapDetail.aspx` and NOT extracted: full owner, applicant/contractor phone/email/company/mailing address/license type+number/fax, all 15+ ASI custom form fields (gate code, NOC, FS 119 status, disposal equipment, plan-submission method, private provider, work type, property type, mechanical mini-split flags), Power Provider ASI (provider/type/release date/release by), Block/Lot.
2. Accela exposes 4 publicly-relevant tabs (Inspections, Attachments, Fees, Processing Status, Related Records, Conditions) — all reachable without login but NONE fetched by the adapter.
3. The portal supports 6 search modes (General / Address / Licensed Professional / Record Information / Trade Name / Contact). We only use General, single `ddlGSPermitType`, missing ~30 other record types across Building, Enforcement, and Land Dev modules.
4. A public Accela v4 REST API (`https://apis.accela.com`) with 15+ relevant endpoints exists, but an April 2026 probe (see [accela-rest-probe-findings.md](accela-rest-probe-findings.md)) established it is NOT available for bulk anonymous extraction: all tested FL agencies have `anonymous_user_unavailable`, and half the endpoints (contacts, owners, inspections, fees, documents, workflow, related) require a bearer token regardless. The REST path becomes a possibility only if a specific agency admin enables the anonymous-user toggle on their end — not a roadmap item we can drive.
5. Charlotte County (same platform) rate-limits aggressively (0.5s detail delay); POLKCO does not yet but is the same software.
6. Winter Haven's auth wall is an agency-level toggle in Civic Platform. The April 2026 REST probe rules out REST as a bypass route — COWH's anonymous-user toggle will be off like every other tested FL agency. Winter Haven remains fixture-mode pending either HTML-side login work or direct outreach to the agency.

### Gaps

| ID | Category | Current | API Map Offers | Recommended Action | Effort | Risk | Priority |
|----|----------|---------|----------------|--------------------|--------|------|----------|
| ACCELA-01 | Coverage Gap | Only `Building/Residential/New/NA` record type extracted | 4 residential + 9 single-trade + 6 commercial + mobile-home + Land Dev (34+ record types) | Parametrize `target_record_type` as a list; iterate and dedup; optionally introduce sibling adapter slugs for Commercial/Trade splits (needed because analytics is residential-centric) | M | Low | P1 |
| ACCELA-02 | Endpoint/Protocol | 100% HTML+regex via ASP.NET postback | Accela v4 REST API exists but April 2026 probe shows it is NOT usable for bulk anonymous extraction (see [accela-rest-probe-findings.md](accela-rest-probe-findings.md)). | **BLOCKED — deferred.** External dependency: agency admin must enable anonymous-user toggle in Civic Platform. Not a project we can schedule. Keep as aspirational / opportunistic — if an agency ever contacts us and offers REST credentials, reopen. Until then: invest in the HTML path (ACCELA-01, 03, 04, 06, 11). | L | High | P3 (blocked) |
| ACCELA-03 | Field Mapping | Owner name/address not extracted | Owner section on detail page (Name, full address) and `/v4/records/{id}/owners` | Add `owner_pattern` regex/DOM parser in the HTML path. REST owners endpoint unreachable without agency cooperation (see ACCELA-02). | S | Low | P1 |
| ACCELA-04 | Field Mapping | Applicant/contractor = flattened-text regex, frequently null; only name captured | Full name, company, license type+number, phone, email, fax, mailing address; "View Additional Licensed Professionals" subcontractor list | Structured DOM parsing against the detail page's stable per-section anchors. REST `/contacts` + `/professionals` require a bearer token even when anonymous user is enabled (see ACCELA-02), so the HTML path is the only actionable route. | M | Med | P1 |
| ACCELA-05 | Robustness | `_parse_inspections` runs on detail HTML but Polk's Inspections live on a separate `Record Info > Inspections` sub-page. Returns `None` silently on Polk; emits `permit["inspections"] = None` with no warning. Unit tests use synthetic inline HTML and do not catch this. | Inspections tab URL + REST `/v4/records/{id}/inspections` (60+ fields per inspection) | Either (a) fetch the Inspections sub-tab explicitly and parse it, or (b) remove the `inspections` key from Polk output until wired properly, or (c) log a DEBUG warning when the field is None on agencies that have inspections. See also ACCELA-06. | S | Low | P0 |
| ACCELA-06 | Coverage Gap | Inspections tab never fetched | Full inspection list with type/date/status/result/inspector (public; no login for viewing) | Fetch the Inspections sub-tab URL and parse it into the per-permit dict. (The prior recommendation favored REST — deprecated by April 2026 probe findings; REST `/inspections` is token-gated. HTML tab fetch is the only actionable route.) | M | Low | P1 |
| ACCELA-07 | Coverage Gap | Fees tab never fetched | Fee line items, invoice numbers, amounts, dates (Outstanding section is public) | Fetch the Fees tab URL. REST `/records/{id}/fees` requires a bearer token (see ACCELA-02). | M | Low | P2 |
| ACCELA-08 | Coverage Gap | Attachments tab never fetched | Document filenames, types, dates, download URLs (public list + public downloads) | Fetch the Attachments tab URL. REST `/records/{id}/documents` requires a bearer token (see ACCELA-02). Storage cost is the main decision. | M | Med | P2 |
| ACCELA-09 | Coverage Gap | Processing Status tab never fetched | Workflow task names, statuses, assignees, due dates | HTML Processing Status tab fetch. REST `/workflowTasks` is token-gated (see ACCELA-02) so the HTML tab is the only actionable route. | M | Low | P2 |
| ACCELA-10 | Coverage Gap | Related Records tab never fetched | Parent/child permit tree (e.g., Residential New → trade permits) | HTML Related Records tab fetch. REST `/related` is token-gated (see ACCELA-02). Valuable for de-duplicating trade-permit noise against the main residential permit. | M | Low | P2 |
| ACCELA-11 | Field Mapping | `latitude`/`longitude` hard-coded `None` in the permit dict | REST `/v4/geo/geocode/reverse`, or `xCoordinate`/`yCoordinate` on address object | Chain through existing `modules/permits/geocoding.py` (already hints `", FL"` for Polk County / Lake Alfred / Winter Haven). REST `/geo/geocode/reverse` was the original preferred path but is blocked by ACCELA-02; `geocoding.py` is the only actionable route. | S | Low | P1 |
| ACCELA-12 | Field Mapping | ASI (Application Specific Info) sections ignored — gate code, NOC, FS 119, disposal equipment, mechanical mini-split, private-provider flag, Work Type, Property Type, Power Provider table | REST `/records/{id}/customForms` and `/customTables`; or expand regex set in HTML path | Capture a small subset in the HTML path (gate code, Work Type, Property Type) — most other ASI is not analytically useful for our residential-leads use case. Full-ASI capture would have required REST `/customForms`, which is blocked (ACCELA-02). | M | Low | P2 |
| ACCELA-13 | Performance | Binary date-range splitting on `total >= 100`. Every split re-submits the full search with a fresh session in the recursion; each call re-fetches the ~100KB VIEWSTATE page. For wide date ranges with many permits this is O(n log n) network hits. | REST supports straight `$offset`/`$limit` pagination with no ViewState | ACCELA-02 (formerly expected to make this moot) is now blocked, so this mitigation becomes the actual fix: skip the initial `_submit_search` per recursion and reuse the existing page payload for the split halves. Re-scope to P2 (was P2) but raise engagement odds since the REST workaround is off the table. | S | Med | P2 |
| ACCELA-14 | Robustness | No fixture-drift guardrail. `tests/test_accela_citizen_access_adapter.py` uses synthetic HTML only. Any ACA markup change breaks regex extraction silently (all fields return None). | Deterministic JSON via REST would have removed this risk, but REST is blocked (ACCELA-02); HTML-side canary is the only mitigation. | Add a monthly cron that runs the adapter against one known permit number and asserts parcel/contractor/valuation are non-null. (The "until ACCELA-02 lands" escape hatch is no longer available — ACCELA-02 is blocked per the April 2026 probe; this canary becomes permanent.) | S | Low | P1 |
| ACCELA-15 | Config/Registry | `permit_type_filter = ()` but `target_record_type` locks extraction to one record type at the search layer, making the filter field dead code on Polk. | — | Remove or repurpose `permit_type_filter` for the record types where the grid returns a mixed set. Low urgency. | S | Low | P2 |
| ACCELA-16 | Coverage Gap | Winter Haven (COWH) = 0 permits; listed as `fixture` mode in `seed_pt_jurisdiction_config.py` because HTML search requires login. | REST probe closed this door (see ACCELA-02 / probe findings). HTML Land Dev / Enforcement modules remain the open lead. | The REST-probe half of this gap is now resolved negatively: COWH will have the same `anonymous_user_unavailable` posture as every other tested FL agency (see [accela-rest-probe-findings.md](accela-rest-probe-findings.md)). Remaining actionable work: test the Enforcement-module HTML search against COWH — it may not share the Building-module auth gate — and consider a fixture-mode authenticated scraper that re-uses browser cookies. | M | Med | P1 |

### Prioritized Action List (this surface)

1. **P0**: ACCELA-05 — close the inspections drift bug (1-2 hours). _[already shipped in commit `be5d02f`; leave as-is unless Executor discovers it still open]_
2. **P1 / strategic pivot**: ACCELA-06 + ACCELA-03 + ACCELA-04 — fetch the Inspections sub-tab, add owner extraction, add structured contact/professional DOM parsing. This is the new "foundation" replacing the blocked ACCELA-02.
3. **P1 / quick wins**: ACCELA-11 (geocoding.py wire), ACCELA-14 (monthly drift canary — now permanent since REST fallback is gone).
4. **P1 / expansion**: ACCELA-01 (34+ record-type iteration). ACCELA-16 partial (Enforcement-module HTML probe for Winter Haven).
5. **P2 / opportunistic**: ACCELA-07, ACCELA-08, ACCELA-09, ACCELA-10, ACCELA-12, ACCELA-13, ACCELA-15.
6. **P3 / blocked**: ACCELA-02 — deferred pending agency-side anonymous-user toggle or staff-credential grant. See [accela-rest-probe-findings.md](accela-rest-probe-findings.md).

---

## Surface 2 — Polk ArcGIS (BI)

### Current State

Polk is row-driven in `seed_bi_county_config.py` (lines 238-250). The row specifies 9 `gis_*_field` mappings consumed by the generic `GISQueryEngine` in `modules/inventory/services/gis_query.py`. No adapter file exists; Polk shares the engine with every other county BI row.

`GISQueryEngine._query_with_where` issues `outFields="*"`, `returnGeometry="true"`, `outSR="4326"`, `resultOffset`/`resultRecordCount=1000` (config default; server max 2000), `f=json`. Pagination loops while `exceededTransferLimit` is true. `AdaptiveDelay(base=0.3, floor=0.2, ceiling=3.0)` governs pacing. Batched OR WHERE clauses cap at `MAX_WHERE_LENGTH=2000` chars; no Polk-specific `max_aliases_per_batch` override.

### API Map Reveals

1. 55 attribute fields exist on Layer 1 (Parcels). Even with the current 9-field mapping, 46 are ignored — notably HMSTD / HMSTD_VAL, YR_CREATED / YR_IMPROVED, MAIL_ADDR_1..3 + MAIL_ZIP, NH_CD / NH_DSCR, PROP_ADRDIR/PROP_ADRNO/PROP_ADRSUF/PROP_UNITNO/PROP_CITY/PROP_ZIP, SECTION/TOWNSHIP/RANGE.
2. Layer 3 (Subdivision) has subdivision polygons that could be spatially joined to parcels to enrich `subdivision_name` with full names (not the 6-char SUBDIVISION code).
3. `outFields="*"` sends ~55 columns per row back; a batch of 1000 rows becomes tens of thousands of unused cells.
4. The cos²(lat) Web-Mercator correction is **correctly** not triggered for Polk (`TOT_ACREAGE` doesn't match any of `shapestarea|shapearea|shape__area`), so acreage is authoritative PA-sourced data.
5. The layer has no lat/lon fields, but geometry in `outSR=4326` gives us a polygon ring we can centroid for a point coordinate (useful for map-ping parcels without rendering polygons).
6. Polk has both `TOT_ACREAGE` (PA-sourced) and `GIS_ACREAGE` (GIS-computed). We correctly use the PA source. Also `ASSESSVAL` is mapped — good choice given the map-documented total value alternatives (TOTALVAL, TAXVAL).

### Gaps

| ID | Category | Current | API Map Offers | Recommended Action | Effort | Risk | Priority |
|----|----------|---------|----------------|--------------------|--------|------|----------|
| ARCGIS-00 | Config/Registry | **DRIFT**: api-map §3 and §5 say Polk maps only 5 fields; `seed_bi_county_config.py` lines 238-250 maps 9 (adds `subdivision`, `building_value`, `appraised_value`, `deed_date`). One of the two is out of sync with DB state. | — | Run a one-row DB check against `bi_county_config` for Polk; if 9 rows present, update the api-map §3/§5/§6 tables. If 5 rows present, re-run `seed_bi_county_config.py` to push the extra 4 mappings. | S | Low | P0 |
| ARCGIS-01 | Performance | `outFields="*"` unconditional | outFields can be a comma-separated list | Build outFields from the actually-mapped `gis_*_field` columns + OBJECTID + Shape__Area for geometry conversion; reduces row payload by ~5-10x for Polk. | S | Low | P1 |
| ARCGIS-02 | Field Mapping | No mapping for homestead flag / value | `HMSTD` + `HMSTD_VAL` | Add `gis_homestead_field` + `gis_homestead_val_field` to `seed_bi_county_config.py` and `GISFieldMapping`. Homestead presence is signal for "existing resident" vs "builder/speculator" parcels. | S | Low | P1 |
| ARCGIS-03 | Field Mapping | No mapping for year built / year improved | `YR_CREATED` + `YR_IMPROVED` | Analogous to ARCGIS-02. Enables "new construction" detection directly on the parcel surface even when permit data is missing or delayed. | S | Low | P1 |
| ARCGIS-04 | Field Mapping | Owner mailing address not captured | `MAIL_ADDR_1`, `MAIL_ADDR_2`, `MAIL_ADDR_3`, `MAIL_ZIP` | Add to schema; enables "owner lives out-of-state / out-of-county" detection. High value for flagging speculator/builder ownership. | M | Low | P1 |
| ARCGIS-05 | Field Mapping | Site address is street-only (`PROP_ADRSTR`) | `PROP_ADRNO`, `PROP_ADRDIR`, `PROP_ADRSTR`, `PROP_ADRSUF`, `PROP_UNITNO`, `PROP_CITY`, `PROP_ZIP` | Concatenate in the engine, or add structured sub-fields. Current `site_address` cannot be matched against permit addresses without fuzzy logic. | M | Med | P1 |
| ARCGIS-06 | Coverage Gap | Subdivision is 6-char code only (`SUBDIVISION`); Layer 3 (Subdivision polygons) never queried | Layer 3 polygons contain full subdivision names | Add a one-shot ingest of Layer 3 into `subdivision_geo` table (already exists in `modules/permits/subdivision_geo.py`) or spatial-join parcels → layer-3 via `geometry` parameter on query. | M | Med | P2 |
| ARCGIS-07 | Field Mapping | No neighborhood code | `NH_CD` + `NH_DSCR` | Low priority; adds demographic stratification potential. | S | Low | P2 |
| ARCGIS-08 | Field Mapping | No legal description components | `SECTION`, `TOWNSHIP`, `RANGE`, `PR_STRAP` | Useful for matching parcels to county legal descriptions (e.g., plat reviews). | S | Low | P2 |
| ARCGIS-09 | Robustness | No fixture-drift guardrail for the Polk BI surface. Field schema can change silently. | Layer metadata endpoint (`/server/rest/services/.../FeatureServer/1?f=json`) returns the current schema. | Monthly cron that fetches layer metadata, asserts presence of the mapped field names (PARCELID, NAME, PROP_ADRSTR, TOT_ACREAGE, etc.), alerts on drift. | S | Low | P1 |

### Prioritized Action List (this surface)

1. **P0**: ARCGIS-00 — reconcile seed vs api-map.
2. **P1 / one session**: ARCGIS-01, ARCGIS-02, ARCGIS-03, ARCGIS-05, ARCGIS-09 together — all are schema additions + a drift canary.
3. **P1 / separate session**: ARCGIS-04 — mailing address adds a new analytical dimension (owner geography).
4. **P2 / opportunistic**: ARCGIS-06 (Layer 3), ARCGIS-07, ARCGIS-08.

---

## Surface 3 — Polk iWorQ (PT, east-Polk cities)

### Current State

`IworqAdapter` is the shared base. Three east-Polk subclasses exist: `DavenportAdapter`, `HainesCityAdapter`, `LakeHamiltonAdapter`. Lake Alfred and Winter Haven use Accela (Surface 1), despite appearing on the same "east Polk" geographic list.

- **Davenport**: 10-column override in `davenport.py` (cells 1=contractor, 3=address, 5=description/type, 6=project cost, 7=status). Live, unit-tested.
- **Haines City**: 10-column override in `haines_city.py` (cells 2=app-status, 5+6=address parts, no contractor, no type). Live, unit-tested. Type filter deferred to detail page.
- **Lake Hamilton**: Pure subclass (3 lines). Inherits the base `_extract_row_fields` 6-column default. `seed_pt_jurisdiction_config.py` marks it `fixture` with note: "iWorQ portal uses reCAPTCHA and has no date-range search. Needs browser-based scraper." The api-map says only "URL unverified" — missing the reCAPTCHA blocker.
- `IworqAdapter.fetch_permits` has no inter-page or inter-detail delay, unlike the Accela, GIS, and Legistar paths.
- `latitude`/`longitude` hard-coded `None`.
- `_is_target_permit_type` is shared across all iWorQ counties (not Polk-specific), so the 19 excluded and 9 residential terms apply to all cities. For Haines City (no type column), detail-page fetches happen on EVERY row before the filter runs.

### API Map Reveals

1. iWorQ has no REST API. HTML scraping is the only option (no migration path analogous to Accela's REST).
2. Each city's grid layout differs. The base class is essentially unused — every live city override includes its own `_extract_row_fields`. The 6-column default is therefore dead code.
3. `fields` dict in `_fetch_detail_fields` captures EVERY `div.row > div.col:col` pair as a label-value map, but only ~10 specific labels are consumed. The detail-page is already silently collecting Owner, Lot, Block, Subdivision, Square Footage, Number of Stories, Bedrooms, Bathrooms — they just aren't pulled from `fields` into the output dict.
4. The `WinterHavenAdapter` appears in the iWorQ map only as a footnote — it's actually Accela and duplicates Surface 1 gap ACCELA-16.
5. Lake Hamilton's reCAPTCHA blocker means the current subclass will 403/captcha-fail on any real call. The seed correctly marks it `fixture`; the api-map's "URL unverified" wording understates this.
6. `geocoding.py` already has Polk-state hints for all three iWorQ cities ("Davenport", "Haines City", "Lake Hamilton") — lat/lon enrichment is ONE pipeline-stage away.

### Gaps

| ID | Category | Current | API Map Offers | Recommended Action | Effort | Risk | Priority |
|----|----------|---------|----------------|--------------------|--------|------|----------|
| IWORQ-01 | Field Mapping | Detail-page `fields` dict captures everything but only 10 labels are promoted to output | Owner, Lot, Block, Subdivision, Square Footage, Bedrooms, Bathrooms | Promote Owner → `raw_owner_name`, Lot → `lot_number`, Square Footage → `square_footage` in `_parse_search_results`. No extra network cost — already fetched. | S | Low | P1 |
| IWORQ-02 | Performance / Robustness | No delay between page fetches or detail fetches | Legistar uses 0.5s; GIS uses adaptive 0.3s base | Add a 0.3s default between detail fetches in `IworqAdapter._parse_search_results`. Guards against future rate-limiting and is inconsequential at current volumes. | S | Low | P2 |
| IWORQ-03 | Performance | Haines City fetches detail page for EVERY grid row before the type filter runs (because grid has no type column) | — | Add an early-exit heuristic on the grid cells that Haines City has (e.g., skip rows whose `Project Name` is obviously commercial), OR widen the residential-term list to cover Haines City's specific naming conventions from historical data. Low priority — ticket only if volume becomes painful. | M | Low | P2 |
| IWORQ-04 | Field Mapping | `latitude`/`longitude` always `None` | `modules/permits/geocoding.py` already configured with `", FL"` hint for Davenport, Haines City, Lake Hamilton | Wire a post-scrape geocoding pass in the permit pipeline (if not already done at aggregation layer) rather than in the adapter. One-time ingestion pass. | S | Low | P1 |
| IWORQ-05 | Coverage Gap | Lake Hamilton subclass is 3 lines; inherits 6-column default; SEED marks it fixture/reCAPTCHA-blocked; api-map says only "URL unverified" | — | **Flag api-map as understated** (api-map §8 item 4-5 discusses layout, not the reCAPTCHA). Update the api-map to match the seed. Separately: hybrid-captcha pattern (per user memory) is a viable workaround — human solves captcha in browser, script re-uses cookies. | S / M for captcha work | Med | P2 (API-map fix is P1) |
| IWORQ-06 | Robustness | Base class's 6-column default is dead code (no live city uses it) | — | Either remove the default `_extract_row_fields` (force every subclass to override, fails loud on new cities) OR keep it as fixture-mode scaffolding. Document either way. | S | Low | P2 |
| IWORQ-07 | Robustness | Date-format assumption hard-coded to `MM/DD/YYYY`; silent string fallback on ValueError | — | Add a second strptime try for `YYYY-MM-DD`; warn on unknown format instead of silent fallback. | S | Low | P2 |
| IWORQ-08 | Robustness | No fixture-drift guardrail. HTML column indices per city are hard-coded; any layout change breaks extraction silently. | — | Add a weekly live-fetch-one-permit test per city that asserts `permit_number`, `address`, `issue_date` are non-null. | S | Low | P1 |
| IWORQ-09 | Field Mapping | Valuation label hunt covers only `Valuation` + `NSFR Construction Cost` | Field name varies by city; Davenport grid says "Project Cost" | Fix: add `Project Cost` to the detail-page valuation fallback hunt. Davenport has `valuation_hint` from the grid, so this is mostly belt-and-braces, but Haines City has no grid hint and may surface as "Project Cost" on the detail page. | S | Low | P2 |

### Prioritized Action List (this surface)

1. **P1**: IWORQ-01 + IWORQ-04 + IWORQ-08 — promote already-fetched fields; wire geocoding; add drift canary. Can all be one session.
2. **P2**: IWORQ-05 api-map fix (session-local, no code change); IWORQ-06/07/09 cleanups.
3. **Separate initiative**: IWORQ-03 / IWORQ-05 reCAPTCHA workaround — defer until volume demand justifies.

---

## Surface 4 — Polk Legistar (CR)

### Current State

Generic `LegistarScraper` in `modules/commission/scrapers/legistar.py` is driven by three YAMLs:
- `polk-county-bcc.yaml` — `body_names: ["Board of County Commissioners"]` (BodyId 138 implicitly).
- `polk-county-pz.yaml` — `body_names: ["Planning Commission"]` (BodyId 228 implicitly).
- `polk-county-boa.yaml` — `platform: manual` (intentional).

The scraper has **already been upgraded** (commit b16df13) with `_fetch_event_items` and `_fetch_item_votes` behind a `fetch_event_items` config flag. Tests at `tests/test_legistar_scraper.py` cover the new paths. However, **no Polk YAML sets `fetch_event_items: true`** — the feature is dark on Polk.

Extraction output per event: agenda PDF URL, minutes PDF URL (when non-null), `EventId`, `EventBodyName`, `EventDate[:10]`. Optionally `structured_items` list (event items + votes) when the flag is on.

Request cadence: `$top=100`, `$skip+=100`, 0.5s sleep between paginated pages. Same 0.5s between `_fetch_event_items` item-level vote requests.

### API Map Reveals

1. 12 bodies on the Polk instance; we track 2 (BCC 138, P&Z 228). Untracked:
   - BodyId 140 — Polk County Land Use Hearing Officer (LUHO) → **the actual equivalent of a BOA for Polk**. Api-map §7 item 1 says LUHO "may not have consistent agenda/minutes uploads" but also notes the body IS active on Legistar.
   - BodyId 139 — Polk Regional Water Cooperative (PRWC).
   - BodyIds 239/240/241 — BCC Organizational / Tentative Budget / Final Budget variants.
   - BodyIds 246/251/252 — TPO Board and committees.
   - BodyId 258 — Citizen's Healthcare Oversight Committee.
2. Per-event field inventory has ~21 fields; we extract 3 (EventId, EventDate, EventBodyName) + two URLs (EventAgendaFile, EventMinutesFile). Unused valuable fields: EventLocation, EventTime, EventComment, EventInSiteURL, EventAgendaStatusName, EventAgendaLastPublishedUTC, EventMinutesStatusName, EventVideoPath.
3. `fetch_event_items` infrastructure exists end-to-end (scraper, tests, DocumentListing.structured_items) but is not enabled on Polk.
4. `/matters`, `/persons`, `/bodies`, `/codefiles` endpoints are unused across the codebase (not just Polk).
5. Request delay is fixed at 0.5s — no adaptive controller. Not a problem at Polk's volume.

### Gaps

| ID | Category | Current | API Map Offers | Recommended Action | Effort | Risk | Priority |
|----|----------|---------|----------------|--------------------|--------|------|----------|
| LEGISTAR-01 | Config/Registry | `polk-county-boa.yaml` is `platform: manual` | BodyId 140 "Polk County Land Use Hearing Officer" exists on Legistar with MeetFlag=1 and ActiveFlag=1 | Convert BOA YAML to `platform: legistar` with `body_names: ["Polk County Land Use Hearing Officer"]`; keep the extraction_notes explaining it replaces a traditional BOA. Config-only change. Monitor for empty agenda uploads per api-map note. | S | Low | P1 |
| LEGISTAR-02 | Coverage Gap | BCC covers BodyId 138 only | BodyIds 239 (Organizational), 240 (Tentative Budget), 241 (Final Budget) are separate BCC variants | Add to `polk-county-bcc.yaml`: `body_names: ["Board of County Commissioners", "BCC (Organizational)", "BCC (Budget)", "BCC (Final Budget)"]`. Exact body names must be verified against live `/bodies` endpoint. | S | Low | P1 |
| LEGISTAR-03 | Coverage Gap | `fetch_event_items: true` not set in any Polk YAML, despite the feature landing in b16df13 and passing tests | `/events/{id}/eventitems` + `/eventitems/{id}/votes` produce motions, mover/seconder, passed-flag, matter references, per-member vote values | Add `fetch_event_items: true` to `polk-county-bcc.yaml` and `polk-county-pz.yaml`. Immediate value with zero adapter code. | S | Low | P0 |
| LEGISTAR-04 | Field Mapping | `EventInSiteURL`, `EventLocation`, `EventTime`, `EventComment`, `EventAgendaStatusName`, `EventAgendaLastPublishedUTC` not captured | Same fields on every event response | Extend `DocumentListing` (or add a metadata side-channel) to capture these. `EventInSiteURL` is especially useful for citation UI. Requires a small schema/model change on the commission side. | M | Med | P2 |
| LEGISTAR-05 | Coverage Gap | TPO (BodyId 246), TPO TAC (251), TPO TD LCB (252), Citizen's Healthcare Oversight (258), PRWC (139) not tracked | — | Decision needed: are these within our CR product scope? If yes, add YAMLs. TPO in particular carries transportation-funding decisions of high civic interest. Probably a P1 for TPO, P2 for healthcare/water co-op. | M (per body) | Low | P2 |
| LEGISTAR-06 | Coverage Gap | `/matters` and `/persons` endpoints never called | Matter lifecycle (introductions, amendments, votes); member roster with terms | Strategic roadmap item, not a Polk-specific gap. Flag cross-surface. | L | Med | P2 |
| LEGISTAR-07 | Robustness | 0.5s fixed delay; OData datetime format hard-coded to v3 literal | Legistar doesn't document rate limits, but adaptive delay would self-correct | Optional: port `AdaptiveDelay` from GIS engine. Low urgency. | S | Low | P2 |
| LEGISTAR-08 | Robustness | `EventAgendaFile` nullness on upcoming meetings silently drops the event from our pipeline, even when the agenda has items (they're visible via `/eventitems`) | EventAgendaStatusName tells us "Closed" vs "Draft" | Emit a listing even when `EventAgendaFile` is null if `structured_items` are present. Pairs with LEGISTAR-03. | S | Low | P2 |

### Prioritized Action List (this surface)

1. **P0**: LEGISTAR-03 — flip the `fetch_event_items` flag on BCC and P&Z (zero adapter code, feature already shipped and tested).
2. **P1**: LEGISTAR-01 (BOA → LUHO) + LEGISTAR-02 (BCC variants) — both YAML-only.
3. **P2**: LEGISTAR-04, LEGISTAR-05, LEGISTAR-06, LEGISTAR-07, LEGISTAR-08.

---

## Cross-Surface / Meta Recommendations

### Theme 1 — REST is NOT the strategic unlock for Accela (revised April 2026)

Original hypothesis (v1 of this report, 2026-04-14): ACCELA-02 (migrate to v4 REST) would collapse Section 1's gap backlog into one project.

Probe result (2026-04-15): v4 REST is designed for authorized integrations, not bulk anonymous extraction. No tested FL agency (POLKCO, CITRUS, COLA, BOCC, BREVARD) has the "anonymous user" toggle enabled, and ~half of the relevant endpoints require a bearer token regardless. See [accela-rest-probe-findings.md](accela-rest-probe-findings.md).

Revised strategy: treat the HTML ACA portal as the primary extraction mechanism, harden it (ACCELA-03, 04, 06, 11, 14), and iterate coverage (ACCELA-01). The REST path remains on the backlog as P3/blocked — reopen only if a specific agency offers the anonymous-user toggle or staff credentials.

### Theme 2 — Drift guardrails are absent on all three HTML surfaces

ACCELA-14, IWORQ-08, and (to a lesser extent) ARCGIS-09 all describe the same missing primitive: a lightweight monthly live-fetch canary that asserts the adapter can still pull a known record with non-null fields. None of these are individually expensive (S effort each); clustering them into one "drift-canary framework" session produces a reusable capability. The Legistar surface is naturally protected by its stable JSON API — only HTML surfaces need this.

### Theme 3 — Geocoding is already wired; use it

`modules/permits/geocoding.py` already has Polk County + 3 iWorQ cities + 2 Accela cities (Lake Alfred, Winter Haven) configured with `", FL"` hints. Closing ACCELA-11 and IWORQ-04 is plumbing, not net new capability. This should be a pipeline-stage decision rather than an adapter-by-adapter change.

### Theme 4 — Polk permit topology

Polk County's permit data is fragmented across 6 jurisdictions on 2 platforms:
- **Polk County proper (unincorporated + small municipalities): Accela POLKCO** (our polk_county adapter).
- **Davenport / Haines City / Lake Hamilton: iWorQ** (east-Polk, city-issued).
- **Lake Alfred: Accela COLA** (east-Polk, city-issued).
- **Winter Haven: Accela COWH** (east-Polk, city-issued, AUTH-BLOCKED).

All 6 are dependent on the same underlying platform decisions. ACCELA-02 (REST migration) was originally expected to affect 3 of 6 (POLKCO + COLA + COWH); the April 2026 probe established that REST is blocked at all three. ARCGIS field additions remain the cross-cutting enrichment path — county-wide parcel data underpins analysis across all 6 regardless of permit source.

### Theme 5 — Data already present in responses but dropped on the floor

Two separate gaps surface the same pathology:
- `IworqAdapter._fetch_detail_fields` already builds a full `fields` dict, then throws away 10+ labels.
- Legistar `_fetch_page` returns full event objects with 21 fields, then keeps 3.

Both are S-effort field-mapping tickets with zero additional network cost.

### Theme 6 — `docs/commission/live-validation/polk-county-bcc.md` not found

The plan referenced this file; the directory does not contain it (not found under `docs/commission/`). Indeterminate — potentially a live-validation file planned but not yet written. Flag as a documentation gap.

---

## Consolidated Priority Matrix

Sorted by Priority (P0 first) → Effort (S first) → Risk (Low first).

| ID | Surface | Category | Priority | Effort | Risk | Short Description |
|----|---------|----------|----------|--------|------|-------------------|
| ACCELA-05 | Accela | Robustness | P0 | S | Low | Fix silent-None inspections drift on Polk detail pages |
| ARCGIS-00 | ArcGIS | Config/Registry | P0 | S | Low | Reconcile api-map (5 fields) vs seed (9 fields) for Polk BI |
| LEGISTAR-03 | Legistar | Coverage Gap | P0 | S | Low | Enable `fetch_event_items: true` on BCC + P&Z YAMLs |
| ACCELA-03 | Accela | Field Mapping | P1 | S | Low | Add owner name/address regex extraction |
| ACCELA-11 | Accela | Field Mapping | P1 | S | Low | Populate lat/lon via existing geocoding.py (REST geocode blocked by ACCELA-02) |
| ACCELA-14 | Accela | Robustness | P1 | S | Low | Monthly drift canary against a known permit |
| ARCGIS-01 | ArcGIS | Performance | P1 | S | Low | Replace `outFields="*"` with mapped-field list |
| ARCGIS-02 | ArcGIS | Field Mapping | P1 | S | Low | Add HMSTD + HMSTD_VAL |
| ARCGIS-03 | ArcGIS | Field Mapping | P1 | S | Low | Add YR_CREATED + YR_IMPROVED |
| ARCGIS-09 | ArcGIS | Robustness | P1 | S | Low | Monthly layer-metadata drift canary |
| IWORQ-01 | iWorQ | Field Mapping | P1 | S | Low | Promote already-fetched Owner / Lot / Sq Ft from `fields` dict |
| IWORQ-04 | iWorQ | Field Mapping | P1 | S | Low | Wire existing geocoding.py for Davenport/Haines City/Lake Hamilton |
| IWORQ-08 | iWorQ | Robustness | P1 | S | Low | Per-city live-fetch drift canary |
| LEGISTAR-01 | Legistar | Config/Registry | P1 | S | Low | Convert BOA YAML to `platform: legistar` (BodyId 140 LUHO) |
| LEGISTAR-02 | Legistar | Coverage Gap | P1 | S | Low | Add BCC Organizational / Budget / Final Budget body names |
| ACCELA-01 | Accela | Coverage Gap | P1 | M | Low | Iterate over multiple record types (34+ available) |
| ACCELA-04 | Accela | Field Mapping | P1 | M | Med | Structured contact parsing instead of flattened regex |
| ACCELA-06 | Accela | Coverage Gap | P1 | M | Low | Fetch Inspections sub-tab HTML (REST /inspections blocked by ACCELA-02) |
| ACCELA-16 | Accela | Coverage Gap | P1 | M | Med | Test Winter Haven Enforcement-module HTML (REST probe closed negatively — see ACCELA-02) |
| ARCGIS-04 | ArcGIS | Field Mapping | P1 | M | Low | Capture MAIL_ADDR_1..3 + MAIL_ZIP |
| ARCGIS-05 | ArcGIS | Field Mapping | P1 | M | Med | Concatenate full site address from structured sub-fields |
| ACCELA-07 | Accela | Coverage Gap | P2 | M | Low | Fetch Fees tab HTML (REST /fees blocked by ACCELA-02) |
| ACCELA-09 | Accela | Coverage Gap | P2 | M | Low | Fetch Processing Status tab HTML (REST /workflowTasks blocked by ACCELA-02) |
| ACCELA-10 | Accela | Coverage Gap | P2 | M | Low | Fetch Related Records tab HTML (REST /related blocked by ACCELA-02) |
| ACCELA-12 | Accela | Field Mapping | P2 | M | Low | Capture ASI custom forms (gate code, work type, property type) |
| ACCELA-08 | Accela | Coverage Gap | P2 | M | Med | Fetch Attachments tab HTML (REST /documents blocked by ACCELA-02) |
| ACCELA-13 | Accela | Performance | P2 | S | Med | Optimize binary date-range split (reuse VIEWSTATE) |
| ACCELA-15 | Accela | Config/Registry | P2 | S | Low | Remove dead `permit_type_filter` or repurpose |
| ARCGIS-06 | ArcGIS | Coverage Gap | P2 | M | Med | Query Layer 3 for full subdivision names |
| ARCGIS-07 | ArcGIS | Field Mapping | P2 | S | Low | Capture NH_CD + NH_DSCR |
| ARCGIS-08 | ArcGIS | Field Mapping | P2 | S | Low | Capture SECTION / TOWNSHIP / RANGE / PR_STRAP |
| IWORQ-02 | iWorQ | Performance | P2 | S | Low | Add 0.3s detail-fetch delay |
| IWORQ-03 | iWorQ | Performance | P2 | M | Low | Reduce Haines City per-row detail fetches |
| IWORQ-05 | iWorQ | Coverage Gap | P2 | S + M | Med | Update api-map to match seed's reCAPTCHA note; consider hybrid-captcha pattern |
| IWORQ-06 | iWorQ | Robustness | P2 | S | Low | Remove dead 6-column default `_extract_row_fields` |
| IWORQ-07 | iWorQ | Robustness | P2 | S | Low | Broader date-format tolerance with warning |
| IWORQ-09 | iWorQ | Field Mapping | P2 | S | Low | Add "Project Cost" to valuation fallback list |
| LEGISTAR-04 | Legistar | Field Mapping | P2 | M | Med | Capture EventInSiteURL / EventLocation / EventTime / EventComment / status fields |
| LEGISTAR-05 | Legistar | Coverage Gap | P2 | M | Low | Track TPO / Citizen's Healthcare / PRWC if in scope |
| LEGISTAR-06 | Legistar | Coverage Gap | P2 | L | Med | Use /matters and /persons endpoints (cross-surface) |
| LEGISTAR-07 | Legistar | Robustness | P2 | S | Low | Port adaptive delay to Legistar |
| LEGISTAR-08 | Legistar | Robustness | P2 | S | Low | Emit upcoming-event listing when agenda null but items present |

### P3 / Blocked by external dependency

| ID | Surface | Category | Priority | Effort | Risk | Short Description |
|----|---------|----------|----------|--------|------|-------------------|
| ACCELA-02 | Accela | Endpoint/Protocol | P3 | L | High | **BLOCKED** — v4 REST migration. Requires agency-side enablement of anonymous-user toggle or staff creds. See [accela-rest-probe-findings.md](accela-rest-probe-findings.md). |

---

## Appendix: Verification Notes

### Confirmed

1. **Accela §1**: `agency_code="POLKCO"`, `module_name="Building"`. Confirmed in `polk_county.py` lines 7-8.
2. **Accela §1**: `target_record_type="Building/Residential/New/NA"`. Confirmed in `polk_county.py` line 9.
3. **Accela §2**: Search submits via `__EVENTTARGET=ctl00$PlaceHolderMain$btnNewSearch`. Confirmed in `accela_citizen_access.py` lines 124-127.
4. **Accela §2**: Search result cap 100 + binary date-range split. Confirmed lines 33 and 101-105.
5. **Accela §2**: Grid ID `ctl00_PlaceHolderMain_dgvPermitList_gdvPermitList`. Confirmed line 194.
6. **Accela §2**: `__doPostBack` pagination. Confirmed lines 431-440.
7. **Accela §3**: Only one `target_record_type` is submitted (no iteration). Confirmed.
8. **Accela §4**: 6 regex patterns (parcel, subdivision, applicant, licensed_professional, project_description, job_value inline). Confirmed lines 36-52 + 305.
9. **Accela §4**: Owner section NOT extracted. Confirmed — no `owner_pattern` exists.
10. **Accela §4**: All ASI fields NOT extracted. Confirmed — no regexes for gate code, NOC, FS 119, etc.
11. **Accela §5**: Inspections tab NOT visited as a separate page. Confirmed — `_parse_inspections(soup)` runs on the CapDetail response only.
12. **Accela §5 (OUTLIER)**: api-map says "adapter does not visit the Inspections tab or parse any inspection data." In fact, adapter DOES run `_parse_inspections` on the detail HTML and emits `permit["inspections"]` (lines 280-281). For Polk, the inline-heading+table structure isn't present so it returns None, but the claim "does not parse any inspection data" is technically false. Revising this claim is part of ACCELA-05.
13. **Accela §4**: `latitude`/`longitude` hard-coded None. Confirmed lines 278-279.
14. **Accela §8**: No `detail_request_delay` override on Polk. Confirmed — base class defaults to `0.0`.
15. **Accela §13**: Address regex is FL-only. Confirmed lines 53-56 — requires literal "FL" between city and zip.
16. **Accela §11**: No REST API usage anywhere in the adapter. Confirmed.
17. **Accela §1**: 5-line `PolkCountyAdapter` subclass. Confirmed.
18. **Accela §1**: Shared base with Lake Alfred (COLA) and Winter Haven (COWH). Confirmed.
19. **Accela §13**: Winter Haven auth-blocked; `fixture` mode. Confirmed in `seed_pt_jurisdiction_config.py` lines 59-62 and comment in `winter_haven.py` lines 10-13.
20. **ArcGIS §1**: Polk endpoint `https://gis.polk-county.net/server/rest/services/Map_Property_Appraiser/FeatureServer/1`. Confirmed in seed line 240.
21. **ArcGIS §2**: `outFields="*"` unconditional, `outSR="4326"`, `f="json"`. Confirmed in `gis_query.py` lines 212-215.
22. **ArcGIS §2**: `resultOffset`/`resultRecordCount`. Confirmed lines 216-217.
23. **ArcGIS §4**: `MAX_WHERE_LENGTH=2000`. Confirmed line 202.
24. **ArcGIS §4**: Polk has no `max_aliases_per_batch` override. Confirmed — `_batch_rules_for_county` only overrides Jefferson AL (lines 429-433).
25. **ArcGIS §4**: AdaptiveDelay base=0.3, floor=0.2, ceiling=3.0. Confirmed line 123.
26. **ArcGIS §7**: cos²(lat) correction triggered only on `shapestarea|shapearea|shape__area`. Confirmed line 20, `_is_geo_area_field` lines 26-30.
27. **ArcGIS §7**: Polk's `TOT_ACREAGE` does not trigger the correction. Confirmed by normalization test (`tot_acreage` not in the token tuple).
28. **ArcGIS §3 / §5 (OUTLIER)**: api-map claims Polk maps 5 fields (parcel, owner, address, use, acreage). Seed actually maps 9 (adds subdivision, building_value, appraised_value, deed_date). Api-map §3 table "Currently Mapped?" column is stale OR the seed hasn't been applied. Tracked as ARCGIS-00.
29. **iWorQ §3 / Davenport**: Cell indices 0=date, 1=contractor, 3=address, 5=type, 6=cost, 7=status. Confirmed in `davenport.py`. Matches api-map.
30. **iWorQ §3 / Haines City**: Cell indices 0=date, 2=app-status, 5+6=address, no type column. Confirmed in `haines_city.py`. Matches api-map.
31. **iWorQ §3 / Lake Hamilton**: No override of `_extract_row_fields`; uses base 6-column default. Confirmed — `lake_hamilton.py` is 9 lines. Matches api-map.
32. **iWorQ §5**: excluded_type_terms (19 terms) + residential_type_terms (9 terms). Confirmed in `iworq.py` lines 36-68. Matches api-map.
33. **iWorQ §6**: No delays between page fetches. Confirmed — `fetch_permits` loops without sleep (lines 86-88).
34. **iWorQ §6**: `latitude`/`longitude` hard-coded `None`. Confirmed lines 226-227.
35. **iWorQ §4**: `Parcel #` regex + div.row>div.col extraction. Confirmed lines 245-257.
36. **iWorQ §4**: `fields` dict keeps ALL label-value pairs but output only uses named labels. Confirmed lines 245-253 (capture-all) vs lines 207-229 (consume-subset).
37. **Legistar §1**: 12 bodies on Polk instance (NOT directly verified without a live API call — taken from api-map). Indeterminate.
38. **Legistar §1**: BCC bound to BodyId 138 via `body_names: ["Board of County Commissioners"]`. Confirmed in bcc.yaml line 13.
39. **Legistar §1**: P&Z bound to BodyId 228 via `body_names: ["Planning Commission"]`. Confirmed in pz.yaml line 13.
40. **Legistar §1**: BOA is `platform: manual`. Confirmed in boa.yaml line 9.
41. **Legistar §2**: `$top=100`, `$skip+=100`, 0.5s sleep. Confirmed in `legistar.py` lines 21-23, 87-91.
42. **Legistar §4 (OUTLIER)**: api-map says scraper extracts only EventAgendaFile/EventMinutesFile/EventDate. **In fact, `_fetch_event_items` + `_fetch_item_votes` are implemented and tested** (commit b16df13). The feature is gated behind `config["fetch_event_items"]`; no Polk YAML enables it. So the claim is true *for Polk as configured* but false for the scraper generally. Tracked as LEGISTAR-03.
43. **Legistar §5**: `/matters`, `/persons`, `/bodies`, `/codefiles` endpoints never called. Confirmed — no `requests.get` for these in `legistar.py`.
44. **Legistar §7**: body_names list supports multi-body in one YAML. Confirmed — `_fetch_body_events` iterates `for body_name in body_names`.
45. **Legistar §7**: BCC variants (239/240/241) not tracked. Confirmed — only "Board of County Commissioners" appears in bcc.yaml.

### Refuted (see "OUTLIER" tags above)

- §5 "does not parse any inspection data" (Accela): technically false — `_parse_inspections` runs but silently returns None on Polk detail pages. See #12.
- §3 / §5 "Polk maps 5 fields" (ArcGIS): refuted by `seed_bi_county_config.py` mapping 9 fields. See #28.
- §4 "extracts only EventAgendaFile/EventMinutesFile/EventDate" (Legistar): true for Polk YAMLs as written, false for the scraper's current capability. See #42.

### Indeterminate

- Whether 12 bodies really exist on the live Polk Legistar instance (not verified without a live API call). Taken on trust from api-map §1.
- Whether `seed_bi_county_config.py` has been applied to the production DB for Polk (reconciliation task ARCGIS-00).
- ~~Whether POLKCO exposes anonymous v4 REST endpoints to an arbitrary registered App ID. Requires a probe (part of ACCELA-02).~~ **Resolved 2026-04-15: No.** POLKCO returns `anonymous_user_unavailable` for all endpoints; the probe also confirmed CITRUS, COLA, BOCC, and BREVARD share the same posture. See [accela-rest-probe-findings.md](accela-rest-probe-findings.md).
- Whether `docs/commission/live-validation/polk-county-bcc.md` exists — file not found at the referenced path.
- Lake Hamilton's actual live HTML layout — seed marks it reCAPTCHA-blocked, adapter inherits default 6-column assumption; neither has been validated against a real render.
- Whether Winter Haven Enforcement-module HTML search requires the same auth gate as the Building module (module-level auth is agency-configurable in Civic Platform).
