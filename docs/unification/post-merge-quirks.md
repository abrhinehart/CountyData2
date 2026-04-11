# Post-Merge Quirks

A running log of quirks, drifts, and gotchas discovered while porting and operating the unified CountyData2 platform after the four-project merge (commit `346fb95`, 2026-04-10). This document is **transient**: it exists to help whoever ports the next module or onboards the next county skip the research phase on problems that have already been seen once.

Each entry follows the same schema (Status, Category, First observed, Symptom, Root cause, Seen in, Fix pattern) so an LLM can scan the file mechanically and a human can skim it by eye. When you hit a new quirk, **just append a new entry to the bottom under `## Entries` using the same fields** — don't reorganize, don't sort, don't consolidate. If you fix one of the "latent" or "monitored" sites, update the `Seen in` bullet for that location rather than rewriting the entry.

**Related docs** (authoritative, not transient):
- `docs/unification/schema-reconciliation.md` — the design-of-record for the unified schema
- `docs/unification/phase2-handoff.md` — Builder Inventory port notes
- `docs/unification/phase3-handoff.md` — Permit Tracker port notes
- `docs/unification/phase4-handoff.md` — Commission Radar port notes

This doc will be archived manually by the user when it has outlived its usefulness. Do not add retirement criteria.

## Entries

### Entry 1: Subdivisions.county NOT NULL drift

- **Status**: `fixed` (exercised live 2026-04-10)
- **Category**: SQLAlchemy model drift from legacy NOT NULL columns on the shared spine
- **First observed**: 2026-04-10, Bay County FL, BI snapshot triad

**Symptom**
ORM `INSERT` into `subdivisions` raises `psycopg2.errors.NotNullViolation` on the `county` column the first time a ported module actually tries to create a row. The crash does not fire in unit tests that only read; it fires on the first real INSERT in the code path, which means it can hide behind config gates (see Seen-in note on Bay FL).

**Root cause**
The shared `subdivisions` table pre-dates the unification and has a legacy `county TEXT NOT NULL` column that was retained in migration 013 so existing CD2 data could be migrated without loss. `shared/models.py` preserves the constraint (`county = Column(Text, nullable=False)` at line 60). When a module is ported, the SQLAlchemy constructor is typically written by matching the new FK columns (`county_id`, `canonical_name`, etc.) against migration 014/015/016 — the legacy spine column from migration 013 gets overlooked. This is a **class of drift**, not a one-off bug: any ORM writer targeting a shared spine table needs to pass both the new FK *and* the legacy text alongside it. Raw-SQL writers may also depend on the column being populated, so silently relaxing the NOT NULL constraint via a new migration is higher-blast-radius than fixing the call sites.

**Seen in**
- `modules/commission/record_inserter.py:382-390` — **fixed** — CR port caught this during Phase 4 and added `county=county_text` to the `Project(...)` (alias for Subdivision) constructor. Reference pattern for future fixes. Live-validated for CR on 2026-04-10 via the Entry 10 fix triad — Pasco P&Z created 6 CR subdivisions with `county='Pasco'` populated, no NotNullViolation.
- `modules/inventory/services/snapshot_runner.py:148` — **fixed** — `_resolve_subdivision` now takes a `county_name` parameter and passes `county=county_name` to the `Subdivision(...)` constructor. `run_snapshot` threads `county.name` (already loaded at line 214) through both call sites. Fix applied 2026-04-10 in the BI NOT NULL drift triad; follows the CR `record_inserter.py:382-390` pattern. Acceptance evidence: Madison AL BI snapshot (county_id=135) run on 2026-04-10 created 4042 parcels and 166 new subdivision rows, all with `county='Madison'` populated. Runtime 61.7s. No NotNullViolation. Both call sites (new-parcel and existing-parcel backfill paths) exercised under real data.
- `modules/inventory/routers/subdivisions.py:155` — **fixed** — `import_geojson` handler now passes `county=county.name` to the `Subdivision(...)` constructor. The `county` local was already fetched at line 119 with a 404 guard, so no new lookup was needed. Fix applied 2026-04-10 in the BI NOT NULL drift triad; follows the CR pattern.

**Fix pattern**
Pass the legacy text column alongside the FK. The canonical example lives in `modules/commission/record_inserter.py:382-390`:

```python
# modules/commission/record_inserter.py (fixed, Phase 4)
subdivision = Project(
    canonical_name=project_name,
    county=county_text,          # <-- legacy TEXT NOT NULL, resolved via _resolve_jurisdiction_county
    county_id=county_id,
    entitlement_status="in_progress",
    location_description=item.get("address"),
    platted_acreage=item.get("acreage"),
    source="commission",
)
```

`county_text` is looked up once per batch via `_resolve_jurisdiction_county` (defined at `modules/commission/record_inserter.py:119`), which joins `County` → `Jurisdiction` and returns `(county_id, county.name)`. For the BI path, the equivalent resolution is trivial because `run_snapshot` already holds the `County` row (loaded at `snapshot_runner.py:214` via `db.get(County, county_id)`); the fix is to thread `county.name` into `_resolve_subdivision` and pass it to the constructor:

```python
# modules/inventory/services/snapshot_runner.py:148 (suggested fix)
sub = Subdivision(name=name, county_id=county_id, county=county_name)
```

Alternative (**not recommended without cross-module review**): relax the NOT NULL constraint via a new migration. Any raw-SQL writer elsewhere in the platform may still assume the column is populated, so this is a higher-blast-radius change.

### Entry 2: Snapshot summary_text off-by-one from ORM flush timing

- **Status**: `cosmetic` (not yet reproduced conclusively; fix not applied)
- **Category**: ORM timing assumption — re-query before flush
- **First observed**: 2026-04-10, Bay County FL, BI snapshot triad

**Symptom**
The stored `bi_snapshots.summary_text` is off by one from the live DB for the same snapshot. On the Bay FL first run, the stored summary said `+143 Clayton Properties Group` but an identical query against the live DB one minute later returned 144. All other counters — `bi_snapshots.new_count`, the `bi_parcel_snapshots` row count for that snapshot_id, and the `parcels` table count — were internally consistent. Only the one cached summary string disagreed.

**Root cause**
`_build_summary_text` (at `modules/inventory/services/snapshot_runner.py:155-207`) re-queries the DB at the end of a snapshot run to build the human-readable change summary. It joins `BiParcelSnapshot` → `Parcel` → `Builder` and groups by builder + change_type. The most likely explanation is that SQLAlchemy had not flushed all pending INSERTs to Postgres at the moment the query ran, so one row was still sitting in the session's identity map and never made it into the aggregate. Has not been conclusively reproduced — it may also be the case that one parcel had a NULL `builder_id` at query time and was dropped by the inner join, then got its `builder_id` populated by a later step before the one-minute-later re-check. Either way, this is a class of "re-query assumed to see everything the current session just wrote" bug, which probably exists in other ported code.

**Seen in**
- `modules/inventory/services/snapshot_runner.py:155-207` — **monitored** — `_build_summary_text` function; the re-query is at lines 162-173. Fix not yet applied.

**Fix pattern** (not yet applied; documented for future work)
Two options, either acceptable:

1. **Compute from in-memory counters**: track the new/removed/changed tallies per builder as the snapshot walks parcels, and hand a dict to `_build_summary_text` instead of letting it re-query. This also removes the need for a Builder join entirely.
2. **Force a flush before the query**: add `db.flush()` immediately before the `.query(...)` call at `snapshot_runner.py:162`. Cheapest fix; preserves the existing DB-query shape.

Whichever is chosen, **also grep the rest of `modules/inventory/` and `modules/permits/` for other "re-query to build summary" patterns** — the same assumption likely exists in other ported code paths where a function re-queries data the same transaction just wrote.

### Entry 3: Invalid source geometry accepted silently

- **Status**: `source-data` (tech-debt category; not unification drift)
- **Category**: Source-data quality — writer does not validate GIS polygons
- **First observed**: 2026-04-10, Bay County FL, BI snapshot triad

**Symptom**
After a BI snapshot, `ST_IsValid(geom)` returns false for one or more `parcels.geom` rows. For Bay FL, 1 of 2334 parcels (`07384-109-000`) failed with `Ring Self-intersection at (-85.515, 30.128)`. The remaining 2333 were valid. Downstream PostGIS spatial queries (subdivision linking by point-in-polygon, permit geocoding, intersection joins) may error out or return incorrect results when they touch an invalid row.

**Root cause**
**This is not a unification bug.** The county's source GIS layer served an invalid polygon — the ring self-intersected in the source data. `_geojson_to_wkb` in `modules/inventory/services/snapshot_runner.py:32-45` calls `shapely.geometry.shape(geojson_dict)`, normalizes Polygon → MultiPolygon, and hands the WKB to PostGIS with **no validation step**. Any county with imperfect source GIS will produce invalid parcels at approximately the same low rate (1 in ~2k for Bay). This is tech-debt category — it will keep happening — and the fix belongs in the writer, not in any individual county onboarding.

**Seen in**
- `modules/inventory/services/snapshot_runner.py:32-45` — **monitored** — `_geojson_to_wkb` accepts whatever shapely produces and returns WKB. No `ST_IsValid` / `ST_MakeValid` / `buffer(0)` pass.

**Fix pattern** (not yet applied; documented for future work)
Add a validity check at write time. Two acceptable approaches:

1. **Heal silently in the writer**: run `shapely.validation.make_valid(geom)` (or PostGIS `ST_MakeValid(geom)` inside the INSERT) before converting to WKB. Preserves row count but may silently reshape the geometry.
2. **Flag for manual review**: add an `is_valid BOOLEAN` column to `parcels` (or reuse an existing `geom_issue` text column if one exists), populate it with the shapely `is_valid` result, and skip invalid rows from downstream spatial joins until a human reviews them.

**Importantly for the next porter**: if you see spurious spatial-query failures, do NOT chase this as a CRS bug, a migration bug, or a shapely version bug. Run `SELECT parcel_id, ST_IsValid(geom), ST_IsValidReason(geom) FROM parcels WHERE NOT ST_IsValid(geom)` first. Invalid source polygons are expected at a low rate on every county; the fix is writer-side, not onboarding-side. (QA initially flagged the Bay FL case as suspicious, traced it to source data in one query.)

### Entry 4: PT first-real-scrape clean run (schema adaptation only)

- **Status**: `cleared (schema adaptation only)`
- **Category**: Triad validation — PT raw-SQL path vs shared spine
- **First observed**: 2026-04-10, Bay County FL, PT scrape triad

**Symptom**
No schema-adaptation drift. PT's raw-SQL writes to `pt_permits`, `subdivisions`, and `builders` all succeeded on first real run against the unified schema. Ingested 82 permits from Bay County FL covering 2026-03-13 through 2026-04-09 (latest monthly PRSF PDF). Scrape run completed in ~75 seconds with `permits_found=82, permits_new=82, permits_updated=0`, no exceptions, no schema errors in the log. NOT NULL constraints on `builders.type`/`builders.scope` and `subdivisions.county` were all satisfied. This clears the Phase 3 schema-adaptation risk only — a separate pre-existing content-logic bug in builder deduplication surfaced during QA audit and is tracked in Entry 5.

**Root cause**
PT port already threaded the legacy `subdivisions.county TEXT NOT NULL` column via subquery at both INSERT sites (services.py:1292, services.py:1471), pre-empting the drift that hit BI (Entry 1). Builder INSERT at services.py:1492 passes `type='builder'` and `scope='national'` explicitly. `pt_permits` column list at services.py:148-181 matches migration 015 exactly. The optional parcel backfill path (services.py:2300-2314) also ran cleanly against `pt_parcel_lookup_cache`.

**Seen in**
- `modules/permits/services.py:1471` — **validated** — `_ensure_subdivision_id` INSERT was exercised this run (55 of 82 permits matched to existing Bay subdivisions via `_ensure_subdivision_id`/geometry lookup; `subdivisions WHERE county_id=3` count unchanged at 1512, so no new subdivisions were minted this run — but the INSERT path was on the code path and did not crash). Pattern confirmed safe against Entry 1 drift.
- `modules/permits/services.py:1492` — **validated for schema** (not for content) — `_ensure_builder_id` INSERT was exercised this run and created 10 new builder rows (ids 451-460) all with correct `type='builder'`, `scope='national'` (NOT NULL constraints satisfied — Phase 3 schema-adaptation concern cleared). **However, 2 of those 10 rows are duplicates of pre-existing builders** (id=454 "Wjh Fl" shadows id=6 "Century (W J H)"; id=459 "Lennar Homes" shadows id=3 "Lennar"), affecting 19/82 permits on this run. This is a pre-existing content-logic bug in `_ensure_builder_id`, not unification drift — see Entry 5.
- `modules/permits/services.py:148-181` — **validated** — 82 `pt_permits` INSERTs succeeded; every row has non-null `permit_number` (all `PRSF%`), `issue_date`, `status`, `permit_type`, `address`.
- `modules/permits/services.py:2300-2314` — **validated** — optional `pt_parcel_lookup_cache` UPSERT path ran against 10 Bay addresses; all 10 rows written with `match_status='No_Match'` (Bay parcel API soft-failed by design on rows without lat/lon), no crash.
- `modules/permits/services.py:96-100` — **validated** — scrape-time `jurisdictions`/`counties` lookup resolved Bay County successfully during ingest. (Note: `services.py:892` is a separate `jurisdictions.is_active` SELECT inside `get_bootstrap_payload`, the UI bootstrap route — that is NOT the ingest-time jurisdiction lookup and was not exercised by the scrape.)

**Fix pattern**
No schema-adaptation fix needed. Reference for future porters: raw-SQL writers to shared spine tables need the same `county TEXT NOT NULL` awareness as ORM writers; PT handled it via `(SELECT name FROM counties WHERE id = %s)` subquery. The `pt_scraper_artifacts` table was not touched on this run (Bay adapter doesn't call `record_trace`) — that risk point is still cold-path for Bay but should be re-validated on the first Cloudpermit-family adapter run (Lynn Haven, Callaway, Panama City Beach, Panama City), which do call `record_trace`. For the builder-dedup content-logic bug surfaced by this same run, see Entry 5.

### Entry 5: PT builder-dedup bypasses builder_aliases table

- **Status**: `fixed` (exercised live 2026-04-10)
- **Category**: Pre-existing content-logic tech debt (not unification drift)
- **First observed**: 2026-04-10, Bay County FL, PT scrape triad (round 2 rejection surfaced it)

**Symptom**
When a PT scrape ingests a permit whose contractor name canonicalizes (via `canonicalize_builder_name` / `KNOWN_BUILDER_PATTERNS`) to a form that is NOT a close SequenceMatcher match (>= 0.88) to an existing row in `builders.canonical_name`, `_ensure_builder_id` silently mints a new builder row even if the correct target exists in `builders` under a different (typically shorter) canonical_name and/or has the matching variant listed in `builder_aliases`. Result: duplicate builder rows, split permit attribution, silent data quality degradation. On the 2026-04-10 Bay County scrape, this caused 2 of 10 newly-minted builder rows to shadow pre-existing rows, affecting 19/82 permits (23%) on that run alone.

**Root cause**
`_ensure_builder_id` at `modules/permits/services.py:1482-1497` queries only `builders.canonical_name` and never joins or consults `builder_aliases`, even though `builder_aliases` has 45+ rows of known name variants specifically to handle this. The match then falls through to `names_match()` which uses a `SequenceMatcher.ratio() >= 0.88` threshold — that threshold is too tight for pairs like ("Lennar", "Lennar Homes") where the longer canonicalized form emitted by `KNOWN_BUILDER_PATTERNS` is substantially longer than the shorter pre-existing canonical row.

Two compounding factors make this worse:
1. ~20 pre-existing `type='builder'` rows have `canonical_name` shorter than what `KNOWN_BUILDER_PATTERNS` emits for matching contractor names: `Lennar` vs "Lennar Homes", `LGI` vs "LGI Homes", `Starlight` vs "Starlight Homes", `Maronda` vs "Maronda Homes", `Pulte`, `Meritage`, `NVR` vs "Ryan Homes", etc. Every one of these will mint a duplicate the first time a matching full-name contractor appears in a scrape.
2. The `builder_aliases` table already contains the correct variants (e.g. "WJH LLC", "WJHFL LLC" pointing to id=6 "Century (W J H)") but the lookup path doesn't use them.

**Seen in**
- `modules/permits/services.py:1482-1497` — **fixed** — `_ensure_builder_id` now runs a primary `builders LEFT JOIN builder_aliases` lookup with `LOWER(TRIM(...))` exact match against both `canonical_name` and `alias`, then falls back to the legacy `names_match` fuzzy scan, before minting a new row. Fix applied 2026-04-10 in the Entry 5 PT builder-dedup triad. Acceptance evidence: live synthetic probe confirmed `_ensure_builder_id(conn, "LENNAR HOMES, LLC")` now returns builder_id=3 (existing "Lennar") instead of minting a new row, a novel contractor string still mints a new row, and the existing `canonical_name`-exact-match path (tested with "D R HORTON INC" → "DR Horton") is unchanged. The 19 mis-attributed Bay County permits were re-pointed and the 2 duplicate rows deleted in the same triad (see bullets below).
- `builders.id=454` ("Wjh Fl") — **cleaned up 2026-04-10** — 15 Bay County permits re-pointed from builder_id=454 to builder_id=6 ("Century (W J H)"); builder row 454 deleted. Note: the code fix's LOWER(TRIM) alias lookup alone would NOT have prevented this recurring on the next Bay scrape because `canonicalize_builder_name("WJH FL LLC")` emits `"Wjh Fl"` which does not match any of id=6's pre-existing aliases ("WJH LLC", "WJHFL LLC", "WJH LLC DBA", "WJHFL LLC DBA") under LOWER(TRIM). As part of the triad, a new alias row `(builder_id=6, alias='Wjh Fl')` was also inserted so the code fix is durable for the next scrape. Same-canonicalized-string pairs across the rest of the 20-ish short-canonical rows flagged in the Fix pattern section remain latent until similar alias seeding or canonical_name rewrites are applied.
- `builders.id=459` ("Lennar Homes") — **cleaned up 2026-04-10** — 4 Bay County permits re-pointed from builder_id=459 to builder_id=3 ("Lennar"); builder row 459 deleted. Code fix is durable for this case because `builder_aliases` id=14 (`builder_id=3, alias='Lennar Homes'`) already existed pre-fix — the primary LOWER(TRIM) alias lookup catches the match on the next scrape.

**Fix pattern**
Two complementary fixes; apply either or both:

1. **Code fix (preferred)**: extend `_ensure_builder_id` to JOIN `builder_aliases` on a normalized alias match before falling back to the `names_match` scan. Pseudocode:
   ```
   cur.execute("""
       SELECT b.id FROM builders b
       LEFT JOIN builder_aliases ba ON ba.builder_id = b.id
       WHERE LOWER(TRIM(b.canonical_name)) = LOWER(TRIM(%s))
          OR LOWER(TRIM(ba.alias)) = LOWER(TRIM(%s))
       LIMIT 1
   """, (canonical_name, canonical_name))
   ```
   Then fall back to the existing `names_match` loop for fuzzy matches. This mirrors the lookup pattern used in the ETL layer (see `utils/lookup.py::BuilderMatcher`).

2. **Data fix (shallow)**: for the 20-ish short-canonical-name rows, UPDATE `builders.canonical_name` to the longer form that `canonicalize_builder_name` emits, so the existing `names_match` scan would find them exactly. Lower-effort but doesn't address the underlying `builder_aliases` bypass, so latent on any future alias-only pair.

**Data cleanup for the 2 known duplicates** (do NOT run until the code fix above is applied, otherwise the next scrape will just recreate them):
```
UPDATE pt_permits SET builder_id = 6 WHERE builder_id = 454;
UPDATE pt_permits SET builder_id = 3 WHERE builder_id = 459;
DELETE FROM builders WHERE id IN (454, 459);
```

### Entry 6: CR first-real-ingest partial (steps 1-3 validated, steps 4-8 deferred)

- **Status**: `cleared` (full 8-step CR pipeline validated end-to-end 2026-04-10 via the Entry 10 fix triad; all steps 4-8 exercised on Pasco P&Z after the Entry 9 and Entry 10 fixes landed)
- **Category**: Triad validation — CR pipeline vs shared spine (partial coverage)
- **First observed**: 2026-04-10, Panama City CC, CR first-ingest triad

**Symptom**
First CR document ingest under the unified schema ran through steps 1-3 (convert → detect → keyword filter) cleanly but short-circuited at step 3 because the selected agenda (Panama City CC 2026-03-24, `civicplus` document_id=835, 59,895 bytes) was a routine administrative meeting with no development signals. Pipeline correctly wrote one `cr_source_documents` row with `processing_status='filtered_out'`, `keyword_filter_passed=false`, `extraction_attempted=false`. Claude API was NOT called (zero cost incurred). Steps 4-8 (Claude extract, threshold filter, packet enrichment, record_inserter, matcher agenda↔minutes, lifecycle refresh) not yet exercised under the unified schema.

**Root cause**
Expected/intentional behavior of the keyword filter — step 3 correctly rejects documents without development signals per the `modules/commission/keyword_filter.py` gating logic and the Panama City CC YAML keyword list (22 terms including DSAP, PUD, DRI, annexation, rezoning, FLUM, subdivision, plat, etc.). This is NOT drift. However, the run did validate several positive signals worth documenting:
1. The `has_duplicate_page_bug=TRUE` dedup code path in the converter (step 1) fired for the first time under the unified schema. 5 pages → 1 page after dedup (80% reduction), 7673 chars extracted. Warning logged: "Duplicate-page cleanup removed a large share of pages." The dedup may be over-aggressive for short agendas — worth monitoring on future runs.
2. Step 2 jurisdiction + date override path ran cleanly with `jurisdiction_slug='panama-city-cc'` and `override_date='2026-03-24'`.
3. The `cr_source_documents` INSERT path succeeded — migration 016 column list matches the SQLAlchemy model exactly for this code path.
4. No Entry 1 regression: `subdivisions WHERE county IS NULL` count was 0 before and after the run.

**Seen in**
- `modules/commission/converters/pdf_converter.py` — **validated (step 1)** — PDF converter ran successfully with `deduplicate_pages=True`. 5 pages → 1 page, 7673 chars, `page_count` persisted to `cr_source_documents.page_count=5` and `extracted_text_length=7673`. First time the duplicate-page-bug handling fired under the unified schema. Non-dedup path (`has_duplicate_page_bug=FALSE`) validated on Pasco P&Z 2026-04-10 triad — 3 PDFs processed with no pages removed (2→2, 4→4, 5→5), confirming the non-dedup branch runs cleanly. (Panama City CC validated the TRUE/dedup path; Pasco validated the FALSE/non-dedup path.)
- `modules/commission/auto_detect.py` — **validated (step 2)** — step 2 accepted jurisdiction + date overrides without error.
- `modules/commission/keyword_filter.py` — **validated (step 3)** — keyword filter correctly rejected the document as lacking development signals. Pipeline short-circuited as designed, wrote `processing_status='filtered_out'`. Also exercised 2026-04-10 on Pasco P&Z — 1 agenda filtered out (score 3/4, below threshold) and 2 agendas passed (score 23/4 and 29/4 on strong `rezoning` matches), confirming both pass and fail branches under the unified schema.
- `modules/commission/extractor.py` — **fully validated 2026-04-10 (Entry 9 + Entry 10 both cleared)** — after dropping `"strict": True` from the tool spec, Pasco P&Z Agenda_2026-04-09_1879.pdf ran cleanly through Claude extraction: request accepted, 7 items returned, `_validate_items` enforced value sets, 7 items remained after threshold filter. First successful step-4 run under the unified schema.
- `modules/commission/threshold_filter.py` — **validated 2026-04-10** — step 5 exercised on Pasco P&Z Agenda_2026-04-09_1879.pdf: 7 of 7 items passed filters. First live run under the unified schema.
- `modules/commission/packet_fetcher.py:307-358` — **validated (both branches) 2026-04-11** — civicclerk early-return branch validated 2026-04-10 on Pasco P&Z. Civicplus enrichment branch validated 2026-04-11 via `tmp/run_cr_civicplus_packet.py` against Panama City Planning Board (id=79, civicplus, planning_board), exercising both `Agenda_03092026-847.pdf` and `Agenda_02092026-837.pdf`. The function entered past all three early returns at lines 323-328, walked extracted items, called `parse_item_fields_from_html` per item, located matching `div.item` blocks via `_find_matching_item`, and parsed `.desc` structured fields. Live runs reported `enriched_count=0` for both agendas because the LLM extractor had already populated every FIELD_MAP slot (`acreage`, `applicant_name`, `address`, `parcel_ids`) before merge ran — `filled_any` correctly stayed False under the "never overwrite LLM data" rule. Strict positive evidence captured via offline probe with all FIELD_MAP fields nulled: against the Feb 9 agenda (`source_doc.id=9`, case `CPC-PLN-2026-0176`), `parse_item_fields_from_html` returned `{'acreage': 2.324, 'applicant_name': 'Robert Carroll', 'address': '218 BUNKERS COVE ROAD', 'owner': 'ST. ANDREW BAY YACHT CLUB'}` from 7 parsed `.desc` keys (`application type`, `owner`, `applicant`, `address/location`, `acreage (+/-)`, `planning board public hearing date`, `city commission public hearing date (s)`) — proving the parser, the matcher, the field map, and the merge loop all work end-to-end. The civicplus branch is no longer NOT EXERCISED — Entry 6's CR acceptance surface is FULLY CLOSED. Execution log preserved at `cr_civicplus_packet.log`. **Caveat**: a separate parser-fragility drift class was surfaced by the Mar 9 agenda (`source_doc.id=8`, cases `CPC-PLN-2026-0626` / `0633`) where `_parse_desc_fields` returns 0 keys despite a matching `div.item` and present `.desc` block — see new Entry 11.
- `modules/commission/record_inserter.py:382-390` — **validated 2026-04-10** — the Entry 1 reference pattern is now live-validated for CR: 6 subdivisions created with `county='Pasco'` populated (ids 55042-55047), 7 `cr_entitlement_actions` rows inserted, no NotNullViolation. First live validation of the CR `record_inserter` under the unified schema.
- `modules/commission/matcher.py` — **validated 2026-04-10** — step 7 exercised on Pasco P&Z: 0 agenda-minutes links created (no matching minutes document in the batch), but the matcher path ran cleanly without error.
- `modules/commission/lifecycle.py` — **validated 2026-04-10** — step 8 exercised on Pasco P&Z: 6 projects had lifecycle updated; 4 of 6 landed with `lifecycle_stage='planning_board'`. First live run under the unified schema.

**Fix pattern**
No fix needed for this outcome — the filtered_out result is expected behavior for a routine admin meeting and validates that the keyword filter is working correctly. Follow-up triad against a jurisdiction likely to have development items (planned: Alachua County BCC/planning commission) will exercise steps 4-8 and close the remaining ~63% of the CR acceptance surface. Two latent drift findings surfaced during the Planner research phase for this triad and are tracked separately as Entry 7 (jurisdiction config nested-YAML drift) and Entry 8 (`.env` loading drift). Both were worked around in the Executor driver script without modifying module code — the driver lives at `tmp/run_cr_panama_city_cc.py` and the execution log is preserved at `cr_panama_city_cc.log` for reference.

The Pasco P&Z follow-up triad (2026-04-10) advanced the CR validation surface through steps 1-3 on a second jurisdiction (civicclerk, non-dedup) and surfaced Entry 9 at step 4. Steps 5-8 remain untested under the unified schema.

### Entry 7: CR jurisdiction config nested-YAML drift

- **Status**: `fixed` (in-module fix landed 2026-04-11 in the Entry 7/8 scheduled fix triad; live exercise evidence stands from the Panama City CC first-ingest triad whose workaround dict matched the fix's output)
- **Category**: CR intake/router drift — nested YAML config fields not surfaced via helper or DB path
- **First observed**: 2026-04-10, Panama City CC, CR first-ingest triad (Planner research phase)

**Symptom**
Two sites where CR code reads jurisdiction config fields that are stored as NESTED keys under `scraping.*` in the YAML (and mirrored into `cr_jurisdiction_config.config_json`), but the reader code either looks at the wrong level or only reads the YAML. For the `category_id` site, `build_scrape_config()` returns `category_id=None` which makes `CivicPlusScraper.fetch_listings()` silently return `[]` — the scrape fetches zero documents with no visible error. For the `has_duplicate_page_bug` site, any jurisdiction where DB and YAML disagree would silently skip the dedup path.

**Root cause**
CR's port from the standalone Commission Radar app retained two access patterns that predated migration 016 adding the `cr_jurisdiction_config` table:
1. `build_scrape_config()` at `modules/commission/intake.py:267-272` builds a scraper config dict from a `JurisdictionView` but only checks top-level fields (`agenda_category_id`), never descending into `config["scraping"]["category_id"]` where the actual YAML stores it.
2. `routers/process.py:135,179` reads `has_duplicate_page_bug` via `load_jurisdiction_config(slug).get("scraping", {}).get("has_duplicate_page_bug", False)` — YAML-only. The `JurisdictionView.has_duplicate_page_bug` property exists as a DB-backed accessor (sourced from `cr_jurisdiction_config.has_duplicate_page_bug`) but is never called by the pipeline.

Both sites assume the YAML is the source of truth, but post-unification `cr_jurisdiction_config` is intended to be the DB-backed source of truth with YAML as the seed input. Verified live during Planner research: `build_scrape_config(juris).get("category_id")` returns `None` for `panama-city-cc` despite the YAML storing `scraping.category_id: 1`.

**Seen in**
- `modules/commission/intake.py:267-281` — **fixed 2026-04-11** — `build_scrape_config` now merges all nested `scraping.*` fields into the top level via `scraping = config.get("scraping") or {}; for key, value in scraping.items(): config.setdefault(key, value)`, preserving any pre-existing top-level keys. The legacy `agenda_category_id → category_id` alias is kept as a fallback. Fix applied 2026-04-11 in the Entry 7/8 scheduled fix triad. Offline probes: (a) Panama City CC-shaped config returns `category_id=1`, (b) legistar-shaped config returns `legistar_client="brevardfl"` and `body_names=["Planning & Zoning"]`, (c) legacy `agenda_category_id` alias still fires when no nested `scraping.category_id` is present. The Panama City CC triad's manual `{"base_url": juris.agenda_source_url, "category_id": 1}` driver workaround in `tmp/run_cr_panama_city_cc.py` is now redundant and should be removed on the next touch of that driver (left intact by this triad per scope). The audit also confirmed that `civicclerk_subdomain`, `legistar_client`, and `body_names` were silently dropped the same way — they are now all surfaced, closing the latent breakage for civicclerk and legistar jurisdictions that would have fired on their first ingest.
- `modules/commission/routers/process.py:131-134,174-187` — **fixed 2026-04-11** — both `has_duplicate_page_bug` reads now wrap the resolved `Jurisdiction` row into a `JurisdictionView` via the already-imported `_wrap_jurisdiction` helper and read `view.has_duplicate_page_bug` (DB-backed via `cr_jurisdiction_config`). The override branch reuses `provided_jurisdiction`; the auto-detect branch does a small `session.query(Jurisdiction).filter(slug|name)` lookup before wrapping. The YAML-backed `load_jurisdiction_config(slug).get("scraping", {}).get("has_duplicate_page_bug", False)` path is gone at both sites. Live DB probe confirmed the fix reads correctly: Panama City CC returns `True` and Pasco County P&Z returns `False`, matching the `cr_jurisdiction_config` rows. Panama City CC's DB and YAML already agreed (`true`/`true`), so this fix is behavior-preserving for the Panama City CC 2026-04-10 live run — the drift risk for any future jurisdiction where DB and YAML disagree is closed. Fix applied 2026-04-11 in the Entry 7/8 scheduled fix triad. Planner note: the quirks doc's original "use the already-resolved JurisdictionView that process_document holds in scope" was aspirational — no JurisdictionView is in scope at these sites, so the fix constructs one on the fly via the already-imported `_wrap_jurisdiction` helper.

**Fix pattern**
Two fixes needed, both surgical:

1. **`build_scrape_config` nested-field merge**: Extend the helper to merge nested `scraping.*` values into the top-level result. Rough shape:
   ```python
   # modules/commission/intake.py:267-272 (suggested)
   config = juris.config_json or {}
   scraping = config.get("scraping", {})
   return {
       "base_url": juris.agenda_source_url,
       "category_id": config.get("agenda_category_id") or scraping.get("category_id"),
       # ... other fields
   }
   ```
   Audit all nested `scraping.*` fields to ensure nothing else is being dropped the same way.

2. **`has_duplicate_page_bug` DB-first read**: Switch `routers/process.py` from `load_jurisdiction_config(slug).get("scraping", {}).get("has_duplicate_page_bug", False)` to `juris.has_duplicate_page_bug` (the DB-backed `JurisdictionView` property), using the already-resolved `JurisdictionView` that `process_document` holds in scope. Keeps the pipeline reading from one source of truth.

Follow-up triad should audit all other `load_jurisdiction_config(...).get("scraping", {}).get(...)` sites in `modules/commission/` — there may be additional fields with the same YAML-only pattern that will silently drift the first time the DB and YAML disagree.

Follow-up note (2026-04-11): the audit for other `load_jurisdiction_config(...).get("scraping", {}).get(...)` sites was deferred from this triad. One known site remains at `routers/process.py:391` where the step-3 keyword filter still reads `load_jurisdiction_config(juris.slug)` — this is intentionally out of scope for the Entry 7 fix because the keyword filter also relies on `_apply_defaults` merging Florida-default keyword lists into the YAML config (see Entry 9 secondary note), and that merge path does not exist in the DB-backed `CrJurisdictionConfig.config_json`. Migrating the keyword filter to DB-first would require porting the defaults-merge logic first — tracked as follow-up tech debt.

### Entry 8: CR `.env` loading drift — `load_dotenv(override=False)` vs shell-shadowed empty key

- **Status**: `fixed` (in-module fix landed 2026-04-11 in the Entry 7/8 scheduled fix triad; Option A selected — `override=True`)
- **Category**: Environment loading — empty pre-existing shell var shadows `.env` file
- **First observed**: 2026-04-10, Panama City CC, CR first-ingest triad (Executor pre-flight phase)

**Symptom**
User correctly adds `ANTHROPIC_API_KEY=sk-ant-...` (len=108) to `C:\Users\abrhi\Code\CountyData2\.env`, but the CR pipeline still crashes at step 4 with `RuntimeError: ANTHROPIC_API_KEY is required...` from `modules/commission/extractor.py:874` via `require_anthropic_api_key()`. The user's key is never loaded into `os.environ` despite being correctly present in the file.

**Root cause**
`modules/commission/config.py:23` calls `load_dotenv(PROJECT_ROOT / ".env", override=False)`. The `override=False` flag means `python-dotenv` will NOT overwrite any environment variable that is already set in the parent shell. If the user's shell already has `ANTHROPIC_API_KEY=""` exported (e.g., from a prior session, an IDE run config, a `.zshrc`/`.bashrc` leftover, or a VS Code `env` block), the empty string takes precedence over the correctly-populated `.env` value. `get_anthropic_api_key()` then returns `None` because the `os.environ` lookup returns the empty string and the check at `config.py:48` treats it as missing.

Verified live during Planner research: the planning-shell `env` command showed `ANTHROPIC_API_KEY=""` (empty) pre-set alongside `ANTHROPIC_BASE_URL=https://api.anthropic.com`. After loading `.env` with `override=True`, the key became a valid 108-char `sk-ant-api...` string.

**Seen in**
- `modules/commission/config.py:26` — **fixed 2026-04-11** — `load_dotenv(PROJECT_ROOT / ".env", override=True)`. Selected Option A from the Fix pattern (one-word flip of `override=False` → `override=True`). Rationale: the `.env` file is the source of truth for secrets in development; a stale or empty shell export (e.g. `ANTHROPIC_API_KEY=""` left over from a prior session) should not shadow the file value. Option B as originally described in this entry ("change the check at `config.py:48`") didn't cleanly map onto the actual code — `get_anthropic_api_key` at lines 39-47 already does a strip-and-nullify on the env value; the problem is on the LOAD side, not the READ side. Line shift from `config.py:23` → `config.py:26` is from a 3-line explanatory comment added above the call. Fix applied 2026-04-11 in the Entry 7/8 scheduled fix triad. The early `load_dotenv(PROJECT_ROOT / ".env", override=True)` workaround in `tmp/run_cr_pasco_pz.py` (and similar in `tmp/run_cr_panama_city_cc.py`) is now redundant with the in-module fix and is harmless (load_dotenv is idempotent); left intact by this triad per scope.
- `config.py:11` (root bootstrap) — **fixed 2026-04-11** — `load_dotenv(_PROJECT_ROOT / ".env", override=True)` replacing the bare `load_dotenv()` (default `override=False`). Added an explicit `dotenv_path` argument anchored to `Path(__file__).resolve().parent` (the project root) so the load is independent of CWD, matching the dotenv_path shape already used by `modules/commission/config.py`. Rationale: root `config.py` is the canonical platform bootstrap imported by every CLI entry point (`etl.py`, `export.py`, `apply_migrations.py`, seed scripts, migration runners, tools) and by `shared/database.py` which every API module transitively depends on. The bare `load_dotenv()` call would silently let a stale empty `POSTGRES_PASSWORD=""` / `DATABASE_URL=""` shell export shadow the `.env` value and produce a broken connection string at startup. Fix surface is the same shell-shadow class as Entry 8's ANTHROPIC_API_KEY — flipped for symmetry even though no live incident has surfaced here yet. Fix applied 2026-04-11 in the cross-module `.env` loading audit mini-triad.
- `county_scrapers/pull_records.py:30` — **fixed 2026-04-11** — `load_dotenv(_PROJECT_ROOT / ".env", override=True)` replacing the bare `load_dotenv()`. Added an explicit `dotenv_path` derived from `Path(__file__).resolve().parents[1]` (the project root — `pull_records.py` lives one level deep under `county_scrapers/`) so the load is independent of CWD. Rationale: `pull_records.py` is the `python -m county_scrapers.pull_records` entry point and it does NOT import the root `config.py`, so its `load_dotenv()` is the only env-bootstrap that runs for that entry point. The file reads `MADISON_PORTAL_EMAIL` and `MADISON_PORTAL_PASSWORD` at `pull_records.py:311-312` for Madison County portal login; a stale empty shell export of either would silently defeat the correctly-populated `.env` value. Same shell-shadow class as Entry 8. Fix applied 2026-04-11 in the cross-module `.env` loading audit mini-triad.

**Fix pattern**
Change the `override=False` to `override=True` in `modules/commission/config.py:23`. Rationale: `.env` is intended to be the source of truth for secrets in development; silent override by a stale shell value is a footgun. Any deployment that legitimately needs to override `.env` from the parent environment (e.g., Docker secrets, CI variables) should set a non-empty value in the parent environment — an empty string is never a legitimate override case.

Alternative (broader fix): change the check at `config.py:48` from "is it set?" to "is it set and non-empty?" so an empty-string environment variable falls through to the `.env` lookup. This is safer than just flipping `override=True` because it handles both the shell-shadow case AND any deployment that pre-sets empty strings.

Follow-up triad should also audit `shared/database.py` and other modules' `.env` loading paths for the same pattern — if BI, PT, or sales use `load_dotenv(override=False)` and the same shell-shadow pattern could affect their credentials loading, the fix belongs in the shared bootstrap rather than per-module.

Follow-up note (2026-04-11): the broader audit of `shared/database.py` and other modules' `.env` loading paths for the same `load_dotenv(override=False)` pattern ran as a mini-triad later the same day. Findings: the platform has exactly three runtime `load_dotenv` sites — `modules/commission/config.py:26` (this entry, already fixed in the Entry 7/8 triad), `config.py:11` (root bootstrap, fixed in the mini-triad), and `county_scrapers/pull_records.py:30` (fixed in the mini-triad). `shared/database.py` itself does NOT call `load_dotenv`; it depends on the root `config.py` having already run, which is now safe. BI, PT, and sales modules do NOT have their own `load_dotenv` calls and route all env access through the fixed root `config.py`. The BI/PT/sales bootstrap concern raised above turned out to be moot — there was nothing to fix in those modules. See the two new "Seen in" bullets above for the exact fix sites.

### Entry 9: CR extractor tool schema rejected by Anthropic API (step 4 drift)

- **Status**: `fixed (schema validation only)` (exercised live 2026-04-10 via Pasco P&Z retry triad — the three `anyOf` restructures land cleanly and the `tools.0.custom` 400 no longer fires; however a distinct new drift class surfaced immediately downstream at the same step 4 — see Entry 10)
- **Category**: Anthropic API tool-use schema drift — nullable enum field declaration no longer accepted
- **First observed**: 2026-04-10, Pasco County Planning Commission, CR first-ingest validation triad (follow-up to Entry 6)

**Symptom**
Claude API returns HTTP 400 on the extractor's tool-use request with error `tools.0.custom: Invalid schema: Enum value 'approved' does not match declared type '['string', 'null']'`. The pipeline catches the exception, marks `cr_source_documents.processing_status='extraction_failed'`, `failure_stage='extraction'`, and writes the full error text into `processing_notes`. Affects every CR ingest that reaches step 4, not just Pasco — the tool schema is static, global, and built unconditionally inside `EXTRACTION_TOOL` at module load time. Panama City CC's prior Entry 6 partial never hit this because it short-circuited at step 3. Pasco P&Z surfaced it on 2 separate documents (doc_id=1879_10418 and doc_id=1868_10384) with identical error text but distinct Anthropic request IDs (`req_011CZw8DqqXJfRcKWemDJb4R` and `req_011CZw8DwrvEgz5mWWn7t94s`), confirming the failure is deterministic and schema-level, not a transient API issue.

**Root cause**
The extractor constructs a tool-use JSON schema with fields declared as `{"type": ["string", "null"], "enum": [...]}` — a 2024-era nullable-with-enum pattern that Anthropic's current API validator rejects. The validator requires nullable enum fields to be structured either as `{"type": "string", "enum": [...]}` (non-nullable) or as `anyOf: [{"type": "string", "enum": [...]}, {"type": "null"}]`. The specific offending field that surfaced in the 400 error is `outcome` at `modules/commission/extractor.py:146-149`:

```python
"outcome": {
    "type": ["string", "null"],
    "enum": sorted(v for v in OUTCOME_VALUES if v is not None) + [None],
},
```

`OUTCOME_VALUES` (defined at line 34-45) contains `{None, "recommended_approval", "recommended_denial", "approved", "denied", "tabled", "deferred", "withdrawn", "modified", "remanded"}` — the `"approved"` value in the error message is the alphabetically-first non-null entry that the validator chose to fail on, but the validator would reject the entire declaration regardless of which value it picked first.

**Two other fields in the same schema have the identical anti-pattern** and will fire on the follow-up fix triad once `outcome` is fixed:
1. `reading_number` at `extractor.py:152-155`:
   ```python
   "reading_number": {
       "type": ["string", "null"],
       "enum": ["first", "second_final", None],
   },
   ```
2. `land_use_scale` at `extractor.py:174-177`:
   ```python
   "land_use_scale": {
       "type": ["string", "null"],
       "enum": ["small_scale", "large_scale", None],
   },
   ```

Both use the same `type: [x, null]` + `enum` shape and will need the same structural fix. The schema is built dynamically via `_build_extraction_item_schema()` (`extractor.py:133-181`), which is called from the module-level `EXTRACTION_TOOL` constant (`extractor.py:184-203`). The bulk of the other nullable fields use the helper `_nullable_string_schema()` / `_nullable_number_schema()` (lines 107-112) which emit `{"type": ["string", "null"]}` without an `enum` — those do NOT fire the validator because the offense is specifically the combination of `type: [..., "null"]` AND `enum` in the same field declaration.

**Seen in**
- `modules/commission/extractor.py:146-151` — **fixed 2026-04-10** — `outcome` field restructured to `anyOf: [{"type": "string", "enum": [...]}, {"type": "null"}]`. The Pasco P&Z retry triad (2026-04-10) confirmed the `tools.0.custom` 400 no longer fires — both re-run attempts (doc_id=1879_10418 and doc_id=1868_10384) reached the Anthropic API with fresh request IDs `req_011CZwAYGa3aNPfqV4KQ9AYh` and `req_011CZwAYPBQdMAD7LYQavZVv` and were rejected on a DIFFERENT error class (`'claude-sonnet-4-20250514' does not support strict tools.`, tracked as Entry 10), proving the schema-validation layer accepted the restructured declaration. The original `Invalid schema: Enum value 'approved' does not match declared type '['string', 'null']'` error is no longer present in the log.
- `modules/commission/extractor.py:152-157` — **fixed 2026-04-10** — `reading_number` field restructured to the same `anyOf` shape. Same Pasco P&Z retry triad; no `tools.0.custom` 400 fired.
- `modules/commission/extractor.py:176-181` — **fixed 2026-04-10** — `land_use_scale` field restructured to the same `anyOf` shape. Same Pasco P&Z retry triad; no `tools.0.custom` 400 fired.
- Helper functions `_nullable_string_schema()` at `extractor.py:107-108` and `_nullable_number_schema()` at `extractor.py:111-112` were confirmed safe (no `enum` constraint) and were NOT modified. Grep probe `type.*string.*null` and `type.*number.*null` over `extractor.py` returns exactly 1 hit each, both at those helper lines.
- Impact radius: every CR ingest that reaches step 4 on the current Anthropic API version. Panama City CC's Entry 6 partial did not surface this because it short-circuited at step 3 on the keyword filter. The schema-validation fix is global (single static `EXTRACTION_TOOL` constant at module load), so the fix is also global.
- Attempt cost: original Entry 9 $0 + Pasco retry triad $0 — all four 400s (2 original + 2 retry) rejected at the Anthropic gateway before token processing. Neither `cr_pasco_pz.log` nor `cr_pasco_pz_retry.log` contains `usage` / `input_tokens` / `output_tokens` entries for the failed attempts.

**Acceptance evidence (Pasco P&Z retry triad, 2026-04-10)**
- Layer 1 offline schema inspection: all three fields restructured, no stale top-level `type` or `enum` keys, exactly one `anyOf` enum branch with `type: "string"` and no `None` leaked into the enum list. `LAYER 1 PASS` printed.
- Layer 2 grep sanity: `type.*string.*null` returns 1 hit (line 108, safe helper); `type.*number.*null` returns 1 hit (line 112, safe helper). No fourth offending site.
- Python import check: `python -c "import modules.commission.extractor"` succeeds.
- Pre-run DB cleanup: deleted `cr_source_documents` rows id=3 and id=4 from original Entry 9 run; only id=2 (filtered_out) remained pre-retry.
- Pre-run Entry 1 probe: `SELECT COUNT(*) FROM subdivisions WHERE county IS NULL` = 0.
- Driver run: `tmp/run_cr_pasco_pz.py` exit code 0, wall time 30 seconds.
- Post-run result: 2 new `cr_source_documents` rows (id=5 Agenda_2026-04-09_1879, id=6 Agenda_2026-03-19_1868) both with `processing_status='extraction_failed'`, `failure_stage='extraction'`, `extraction_attempted=true`, `extraction_successful=false`. Failure text confirms the NEW Entry 10 drift class, not the original `tools.0.custom` schema drift.
- Post-run Entry 1 probe: `SELECT COUNT(*) FROM subdivisions WHERE county IS NULL` = 0. No regression.
- Log: `cr_pasco_pz_retry.log` (30 lines), contains `strict tools` error text and fresh request IDs.

**Fix pattern** (not yet applied; documented for follow-up triad)
Three acceptable approaches, in preferred order:

1. **Restructure as `anyOf`** (preserves nullability at the schema level):
   ```python
   "outcome": {
       "anyOf": [
           {"type": "string", "enum": sorted(v for v in OUTCOME_VALUES if v is not None)},
           {"type": "null"},
       ],
   },
   ```
   Cleanest match for the validator's current requirements. Apply the same shape to `reading_number` and `land_use_scale`. No post-processing changes needed because `_validate_items` (extractor.py:793-795 and related) already enforces the value set against `OUTCOME_VALUES`, `READING_NUMBER_VALUES`, and `LAND_USE_SCALE_VALUES`.

2. **Drop the nullable type, keep the enum non-nullable**:
   ```python
   "outcome": {"type": "string", "enum": sorted(v for v in OUTCOME_VALUES if v is not None)},
   ```
   Smaller diff but requires the extractor prompt to guarantee a value for every item, which contradicts current prompt guidance (rule 6: "For county/city commission first readings: set outcome to null") and rule 9 ("set outcome to null unless the agenda explicitly states a recommendation"). **Not recommended** — would force the prompt to invent values or refuse items that legitimately have no recorded outcome.

3. **Drop the `enum` constraint and rely on post-processing**:
   ```python
   "outcome": _nullable_string_schema(),
   ```
   Smallest surgical change. Loses schema-level enum validation but `_validate_items` already enforces the value set in Python (extractor.py:795). Acceptable if Option 1 turns out to conflict with some other validator rule.

**Preferred**: Option 1 (`anyOf`) — it matches the current validator, preserves all existing semantics, and aligns with the hand-written literal-dict style of the rest of the schema. Apply to all three offending fields (`outcome`, `reading_number`, `land_use_scale`) in the same PR.

The follow-up triad should also grep the rest of `modules/commission/` and `modules/permits/` for any other tool-use schema construction that uses the `type: [..., "null"]` + `enum` pattern — this drift class may exist elsewhere. A fast probe: `Grep 'type.*null.*enum|enum.*type.*null' modules/`.

**Secondary note** (keyword filter scoring discovery): During the Pasco P&Z triad, attempt 1's agenda (doc_id=1898_10425) was filtered out at step 3 with score 3/4 despite the jurisdiction's `cr_jurisdiction_config.config_json.keywords=[]` being empty. The Planner's pre-run research predicted that an empty keyword list would mean step 3 auto-passes — this was wrong for two compounding reasons:
1. The pipeline's step-3 path (`routers/process.py:391`) calls `check_keywords(document_text, load_jurisdiction_config(juris.slug) or {})`, which reads the jurisdiction YAML file via `config_loader.load_jurisdiction_config`, NOT the `cr_jurisdiction_config` DB row. The YAML file (`modules/commission/config/jurisdictions/FL/pasco-county-pz.yaml`) also has no `keywords:` key, but `_apply_defaults` at `config_loader.py:62-86` then merges the 25-term keyword list from `_florida-defaults.yaml` into the config. So even though both the DB and the jurisdiction YAML look "empty", the merged config used by the filter has 25 Florida-default terms.
2. `keyword_filter.py:419-423` passes only if ANY of: (a) at least one strong match, (b) two or more medium matches, or (c) total score ≥ 4. The attempt-1 agenda had exactly one medium match (resulting in score 3/4 after weights and bonuses), which satisfies none of the three pass conditions.

This is documentation drift (the Planner's mental model was wrong — the filter has additional scoring logic beyond the YAML keyword list, and the DB `cr_jurisdiction_config.config_json.keywords` value is not what the filter reads), not code drift. No fix needed; just worth knowing for future triads. The related Entry 7 latent finding (`cr_jurisdiction_config` DB table not consistently read) explains why the DB's empty-keywords row is misleading — the seed script populates the table, but the live read path still goes through the YAML loader.

### Entry 10: CR extractor `strict: True` tool flag rejected by sonnet-4 (step 4 drift, second class)

- **Status**: `fixed` (exercised live 2026-04-10 via Pasco P&Z Entry 10 fix triad — dropped `"strict": True` from `EXTRACTION_TOOL` top-level dict; Claude API now accepts the request and the full 8-step CR pipeline runs end-to-end for the first time under the unified schema)
- **Category**: Anthropic API tool-use model-capability drift — `strict` flag on custom tool not supported by `claude-sonnet-4-20250514`
- **First observed**: 2026-04-10, Pasco County Planning Commission, CR first-ingest validation triad retry (follow-up to Entry 9)

**Symptom**
After the Entry 9 `anyOf` restructure landed and the schema validator was cleared, the same Pasco P&Z retry run re-submitted both agendas (doc_id=1879_10418 and doc_id=1868_10384) and immediately hit a different HTTP 400:

```
Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': "'claude-sonnet-4-20250514' does not support strict tools."}, 'request_id': 'req_011CZwAYGa3aNPfqV4KQ9AYh'}
```

Fresh Anthropic request IDs (`req_011CZwAYGa3aNPfqV4KQ9AYh` and `req_011CZwAYPBQdMAD7LYQavZVv`) prove the request crossed the schema-validation layer this time — Entry 9 is definitively fixed — but the specific Claude model configured for CR extraction does not accept the `strict: True` flag on custom tools. The pipeline catches the exception the same way as Entry 9: `cr_source_documents.processing_status='extraction_failed'`, `failure_stage='extraction'`, full error text in `processing_notes`. Both rejections returned $0 in usage (no `input_tokens`/`output_tokens`/`usage` entries in `cr_pasco_pz_retry.log`); Anthropic bills nothing for 400 request-validation rejections.

**Root cause**
The `EXTRACTION_TOOL` constant at `modules/commission/extractor.py:184-203` declares `"strict": True` as a top-level tool field. The `strict` flag is a relatively new OpenAI-style tool-use feature; on the Anthropic Messages API only certain models support it. As of 2026-04-10, `claude-sonnet-4-20250514` — the model CR is currently configured to call — does NOT support strict tools. The request-validation layer rejects the request before the model ever runs, emitting the error text above. The CR port inherited the `strict: True` flag from the standalone Commission Radar app where it was apparently running against a different model (likely a Claude 3.5 sonnet variant that did support it).

The model choice is wired at `modules/commission/extractor.py:874` or in the `require_anthropic_api_key()` / client bootstrap path — see the CR extractor's Anthropic client construction for the exact site. This is a model-capability mismatch, not a schema drift: the tool-schema itself (now `anyOf`-shaped after Entry 9) is valid; the problem is the combination of `strict: True` + a non-strict-capable model.

**Seen in**
- `modules/commission/extractor.py:208` — **fixed** — `"strict": True` removed from the `EXTRACTION_TOOL` top-level dict. Live-validated 2026-04-10: Claude API (claude-sonnet-4-20250514) accepts the request, extraction returns 7 items, `_validate_items` cleanly validates them against `APPROVAL_TYPES`/`OUTCOME_VALUES`/`READING_NUMBER_VALUES`/`LAND_USE_SCALE_VALUES` value sets with no malformed output slipping through. Confirms the Option 1 hypothesis: the post-hoc Python validator is sufficient to enforce semantic correctness without the schema-level strict gate. Line shift from doc's original 202 → actual 208 is residual from Entry 9's 6-line expansion of `_build_extraction_item_schema()`.
- `modules/commission/extractor.py` (client / model selection site — exact line TBD by follow-up triad) — the configured model is `claude-sonnet-4-20250514`. Either the flag or the model must change.
- Impact radius: same as Entry 9 — every CR ingest that reaches step 4 under the current configuration. The Entry 9 fix removed the schema blocker; this drift is now the new step-4 blocker.

**Fix pattern** (not yet applied; documented for follow-up triad)
Three possible approaches; all require follow-up research before the Executor commits to one:

1. **Drop `strict: True` from the tool declaration**. Smallest-possible diff — one line removed. The extractor's post-processing already enforces per-field validation (`_validate_items` checks `OUTCOME_VALUES`, `READING_NUMBER_VALUES`, `LAND_USE_SCALE_VALUES`, and other constraint sets in Python), so the schema-level `strict` flag is largely redundant for correctness. Risk: if `strict: True` was also gating some refusal behavior (e.g., the model being more cautious about emitting fields outside the schema), removing it may widen the surface of malformed output the post-processor has to handle. The post-processor already tolerates this, so this risk is low but should be spot-checked.

2. **Switch the model to one that supports strict tools**. Check Anthropic's current model capability matrix (search for "strict tools" in the model card docs) and switch to a supported model — likely a `claude-opus-*` or a newer `claude-sonnet-*` variant released after 2025-05-14. Larger blast radius because model switches can change extraction quality, token pricing, and context window limits. Requires a re-validation pass on representative agendas.

3. **Keep `strict` but flip it based on model at runtime**. Introduce a small helper that reads the configured model name and sets `strict` accordingly before building `EXTRACTION_TOOL`. Defensive but over-engineered for a single-model deployment; recommend only if CR is expected to be multi-model in the near future.

**Preferred**: Option 1 (drop `strict: True`) for the follow-up triad, because it is surgical, reversible, and does not change the extraction model. Confirm on the follow-up run that `_validate_items` catches any malformed output the model emits without the strict gate.

The follow-up triad should also grep `modules/commission/` and `modules/permits/` for any other `"strict": True` tool-use flags (`Grep '"strict".*True' modules/`) — this drift class may exist elsewhere. The CR port is the only known site so far.

### Entry 11: CR `_parse_desc_fields` fragile to bare-text-after-strong CivicPlus content shape

- **Status**: `open` (surfaced by validation triad 2026-04-11; civicplus packet-enrichment validation followup to Entry 6)
- **Category**: Commission Radar port drift — HTML parser assumes a structural pattern the source content does not always emit
- **First observed**: 2026-04-11, Panama City Planning Board, civicplus packet-enrichment validation triad

**Symptom**
For some CivicPlus planning-board agendas, `merge_html_fields_into_items` enters past all three early returns, finds the matching `div.item` for an LLM-extracted case_number, finds a present `.desc` block with content visible to the eye — but `_parse_desc_fields` returns 0 keys, and the merge loop produces 0 enrichments. The pipeline does not crash; the failure is silent and the enrichment opportunity is lost. Confirmed for Panama City Planning Board `Agenda_03092026-847.pdf` (`source_doc.id=8`, cases `CPC-PLN-2026-0626` "SweetBay Town Center" and `CPC-PLN-2026-0633` "230 McKENZIE AVE"). The same jurisdiction's prior month agenda `Agenda_02092026-837.pdf` (`source_doc.id=9`, case `CPC-PLN-2026-0176` "218 BUNKERS COVE ROAD") parses correctly with 7 keys returned, proving the parser works on the expected shape — the drift is per-paragraph content-authoring variance, not a jurisdiction-wide issue.

**Root cause**
`_parse_desc_fields` at `modules/commission/packet_fetcher.py:146-169` assumes the CivicPlus admin tool produces structured HTML in this shape:
```html
<p><strong><span>Label:</span></strong><span>Value</span></p>
```
The parser walks each `<p>` inside `.desc`, calls `strong.find_next_sibling("span")` to locate the value, and falls back to `p.find_all("span")[1]` if no sibling span is found. **Both lookups fail when the value is a NavigableString text node directly after `</strong>` instead of being wrapped in a `<span>`.** Verified live at `Agenda_03092026-847.pdf`:
```html
<p data-pasted="true"><strong>Application Type</strong>: Conceptual Plan</p>
<p><strong>Owner:&nbsp;</strong>SWEETBAY TOWNCENTER PH 1, LLC</p>
<p><strong>Applicant:&nbsp;</strong>Richard Pfuntner, Dewberry Engineers, Inc.</p>
```
For each `<p>`: `strong.find_next_sibling("span")` returns None (no span sibling), and `p.find_all("span")` returns `[]` (zero spans inside the `<p>`). The parser silently `continue`s on every paragraph, returning `{}`.

The CivicPlus admin tool appears to support both shapes interchangeably depending on how the content was authored — paste-from-Word vs. native-typed produce different HTML. The Feb 9 agenda (matching shape) has `data-pasted="true"` AND span-wrapped values; the Mar 9 agenda has `data-pasted="true"` AND bare text after `</strong>`. So the `data-pasted` attribute is not the determinant — it is per-paragraph content-authoring variance the original parser was never tested against under the unified schema.

**Seen in**
- `modules/commission/packet_fetcher.py:146-169` — **open** — `_parse_desc_fields` returns `{}` when value text is a bare NavigableString after `</strong>`. Surfaced by `tmp/run_cr_civicplus_packet.py` against Panama City Planning Board `Agenda_03092026-847.pdf` (cases `CPC-PLN-2026-0626` and `CPC-PLN-2026-0633`). Execution log at `cr_civicplus_packet.log`. Driver did NOT work around this — the validation outcome stands as "branch entered, parser fragile" rather than "branch broken." The Feb 9 agenda from the same jurisdiction parses correctly and confirms the parser's happy-path works.
- `modules/commission/packet_fetcher.py:307-358` — see also Entry 6's `packet_fetcher.py:307-358` bullet which now references this entry as a caveat to its "FULLY CLOSED" status.

**Fix pattern** (deferred to a separate fix triad — validation triad scope)
Extend `_parse_desc_fields` to handle the bare-text shape by reading the text content of the `<p>` after the `<strong>` element when no value-span is found. Rough shape:
```python
def _parse_desc_fields(desc_div):
    fields = {}
    for p_tag in desc_div.find_all("p"):
        strong = p_tag.find("strong")
        if not strong:
            continue
        label = strong.get_text().strip().rstrip(":")

        # Try sibling span first (legacy structured shape)
        value_span = strong.find_next_sibling("span")
        if value_span:
            value = value_span.get_text().strip()
        else:
            # Try second span inside the <p>
            all_spans = p_tag.find_all("span")
            if len(all_spans) > 1:
                value = all_spans[1].get_text().strip()
            else:
                # NEW: bare-text-after-strong shape — read remaining text
                # of the <p> after the <strong>, stripped of the strong's
                # own text and any leading colon/whitespace.
                full_text = p_tag.get_text()
                strong_text = strong.get_text()
                idx = full_text.find(strong_text)
                if idx >= 0:
                    value = full_text[idx + len(strong_text):].lstrip(": \xa0").strip()
                else:
                    continue
        if value:
            fields[label.lower()] = value
    return fields
```
Test against both Mar 9 (bare-text shape) and Feb 9 (span-wrapped shape) agendas to confirm both branches still parse correctly. Add a unit test capturing both HTML shapes as fixtures.

Alternative (broader, more invasive): switch the entire `_parse_desc_fields` implementation to a "split on `</strong>` per `<p>`" approach using BeautifulSoup `Tag.contents` walking, treating any `<strong>` followed by anything as a label/value pair. Lower risk of future drift but a larger diff.

**Why not fixed in this triad**
Validation-triad discipline: the goal of the 2026-04-11 civicplus packet-enrichment triad was to exercise the civicplus branch end-to-end and surface drift. Drift was found and documented; fixing it is the next triad's job. The Mar 9 agenda's two affected actions (`SweetBay Town Center`, `230 McKENZIE AVE`) were already populated with `address`, `applicant_name`, `acreage`, and `parcel_ids` by the LLM extractor during the validation run, so the immediate data-quality impact of this drift is bounded — packet_fetcher's role is fallback enrichment, and the LLM was thorough enough to make that fallback unnecessary on this particular agenda. Fix priority is therefore "moderate" — real, silent, but not data-blocking under typical conditions.

**Follow-up note**
Once the fix lands, re-run `tmp/run_cr_civicplus_packet.py` against the Mar 9 agenda (will require deleting `cr_source_documents` row id=8 first since the duplicate-check will skip it otherwise), and verify the strict acceptance criterion (`enriched_count >= 1`) is met. With the fix in place, the merge loop should still return 0 because LLM fields are pre-populated — to actually exercise the fix's effect end-to-end, the test needs an offline probe like the one this triad used in the planner-research phase, which blanks all FIELD_MAP slots before calling `merge_html_fields_into_items`. The probe code lives in the Executor's session log and can be lifted into a permanent test fixture if desired.
