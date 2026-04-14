# Session Journal — 2026-04-14 Project Reload

**Branch:** `claude/silly-cohen`
**Working directory:** `C:\Users\arhinehart\Code\CountyData2\.claude\worktrees\silly-cohen`
**Session pattern:** `triad-agent-v2` skill (Planner -> Executor -> QA) plus single-agent variants.

## Session goal

Start with a full project reload of CountyData2 (what's here, what's broken, what's in-flight), then
work a progressive recommendation list of cleanups, validations, and coverage improvements against
the Commission Roster (CR) and Permit Tracker (PT) modules and shared infrastructure.

## Test count delta

- **Start of session:** 0 passing (pytest not installed; `.venv` absent).
- **End of session:** 457 passing.

## Work log (chronological)

1. **Test suite baseline.** Created `.venv`, installed `requirements.txt`, ran full pytest: 336 passed
   on the first green run. Surfaced that `beautifulsoup4` and `lxml` were imported by 12+ production
   modules but missing from `requirements.txt`.

2. **Added `bs4` + `lxml`** to `requirements.txt`.

3. **CR router TODO sweep.** Audited 12 `TODO: verify schema` comments across
   `modules/commission/routers/`. Each was classified REMOVE (code correct), HARDEN (drop
   `try/except ImportError` fallback now that the module exists), or KEEP-AS-DOC (rewrite as
   explanatory comment). Files touched: `dashboard.py`, `helpers.py`, `review.py`, `roster.py`,
   `scrape.py`. Zero query/SQL changes.

4. **Davenport PT adapter validation.** Live-scraped iWorQ portal, captured 25 permits + 31 trace
   artifacts. Created `tests/test_davenport_adapter.py` (4 tests, anonymized fixture). Validated
   PT count 3 -> 4.

5. **Madison County AL honesty pass.** Planner discovered the registry metadata lied:
   `jurisdiction_registry.json`, `source_research.json`, and `seed_pt_jurisdiction_config.py` all
   claimed the adapter was "live" with a `fragile_note`, while the actual code was a 25-line stub
   silently returning `demo_permits.json`. Fix: adapter now raises `NotImplementedError` with a
   credential message; all three metadata files flipped to blocked state. New test pins the
   behavior. New checklist at `docs/permits/madison-county-al-cityview-todo.md`.

6. **Plan checkbox reconciliation.** 49 unchecked `- [ ]` boxes across two superpowers plan files
   audited against shipped code. 48 marked done with mandatory evidence comments. One real skip:
   `ui/src/components/DrillDownTable.tsx` exists as 445 lines of dead code (shipped but never
   imported; `InventoryPage.tsx` ships an inline drill-down instead).

7. **CR router test coverage.** 13 new tests in `tests/test_commission_routers.py` using FastAPI
   `TestClient` plus SQLite in-memory. Hardest part: `geoalchemy2` registers
   `RecoverGeometryColumn` DDL event listeners per table that had to be `event.remove`d, not just
   patching the column type. Built a minimal FastAPI app in `conftest.py` because `api.app` was
   eagerly opening a Postgres pool at import.

8. **CR jurisdiction activation batch 1** (3 -> 7). 4/5 PASS: Okeechobee BCC (Granicus), Altamonte
   Springs CC (CivicPlus), Okaloosa BCC (Granicus), Polk BCC (Legistar). Bay County BCC FAILED:
   NovusAgenda portal returns its own error-page template (portal-side, not a scraper bug).
   Reusable harness added at `scripts/cr_live_validate.py`; recon notes under
   `docs/commission/live-validation/`.

9. **Split `requirements.txt`.** Moved `pytest` to a new `requirements-dev.txt` with
   `-r requirements.txt` include. README step 4 updated.

10. **PT adapter validation batch 2** (4 -> 7). Validated Haines City (iWorQ), Lake Alfred
    (Accela COLA), Citrus County (Accela CITRUS). All three PASS first try. Operational finding:
    Haines City has no permit-type column in its grid, so the adapter fires a detail-page GET per
    row. Scales poorly in production.

11. **Registry drift audit.** Fixed two seed-file drifts: Winter Haven and Lake Hamilton had
    `scrape_mode="live"` in seed while the registry correctly said blocked. Surfaced three
    follow-ups: Charlotte County orphan, unvalidated Tyler subclasses, potential drift-prevention
    test.

12. **Snapshot-runner UI verification.** Discovered the feature was already fully shipped. Added a
    "Status: Shipped (2026-04-14)" section to
    `docs/superpowers/specs/2026-04-13-snapshot-runner-ui-design.md` with a 12-row implementation
    map.

13. **`DrillDownTable.tsx` deleted.** 445 lines of dead code removed. Zero imports confirmed by
    grep before and after. Inline implementation in `InventoryPage.tsx` is strictly richer (search,
    sort, freshness indicator, multi-expand, totals footer).

14. **PT adapter/registry cluster (Pairing A).**
    - Tyler validations: Hernando (6), Marion (34), Walton (4), Okeechobee (27) -- 4/4 PASS. New
      tests under `tests/test_tyler_*_adapter.py`; fixtures at `tests/fixtures/tyler_*/`.
    - Charlotte County deleted: mis-coded `agency_code="BOCC"` (memory-flagged ambiguous
      abbreviation; Charlotte FL actually uses `CHARLOTTEFL`). File was an orphan in all three
      metadata sources.
    - Drift-prevention test at `tests/test_registry_code_consistency.py`: 6 parametrized checks, 78
      test invocations. Check #3 weakened to directional (admin-disabled case); check #5 strict
      set-equality backstops it.
    - Surfaced: `pypdf` missing from `requirements.txt` (chain-imported via the registry).

15. **CR activation batch 2 + Bay follow-up (Pairing B).** 5/5 PASS: Pasco BCC (civicclerk),
    Brevard BCC (legistar), Sumter BCC (civicplus), Hialeah CC (civicplus), Lake Wales CC
    (civicplus). YAML fix for Sumter: `category_id 5 -> 3` (portal showed 5=Budget Workshop,
    3=Regular Meeting). Caveat for Lake Wales: `category_id=3` actually returns Planning and Zoning
    Board, not City Commission. Bay retry: still failing. Discovered the portal's HEAD returns 200
    but GET returns an error page -- HEAD is not a reliable uptime signal. CR count 7 -> 12.

16. **`pypdf` + Hernando fixture cleanup.** Added `pypdf` to `requirements.txt`; scrubbed a
    real-looking parcel/road description in Hernando fixture entity 1.

17. **Lazy DB pool init.** Refactored `shared/database.py` to lazy-init the psycopg2 pool via a
    `_LazyPool` proxy class. Zero consumer changes. `tests/conftest.py` simplified to import the
    real `api.app` directly; minimal-app scaffolding removed.

## Key findings

- **Registry metadata can silently lie.** Madison County AL was the canonical example: three
  separate sources of truth agreed the adapter was live when the code returned demo data. The new
  drift-prevention test (`tests/test_registry_code_consistency.py`) catches structural drift, but
  periodic manual audits of YAML configs (CR) and JSON metadata (PT) are still worth it.
- **HEAD/GET asymmetry on portals is a real failure mode.** Bay NovusAgenda returns 200 on HEAD
  while the GET body is an error template. Future uptime monitoring should GET, not HEAD.
- **`geoalchemy2` installs DDL event listeners per table that survive column-type monkey-patching.**
  Any SQLite test infrastructure must `event.remove` them.
- **Abbreviations in this codebase map to multiple entities.** "BOCC" is generic; Charlotte
  County's actual Accela agency code is `CHARLOTTEFL`, not `BOCC`. (Matches the user-memory note.)
- **Portal operational quirks deserve adapter-level notes.** Haines City forcing detail-page GETs
  per row and Lake Wales `category_id=3` pointing at the wrong board are both the kind of drift
  that quietly breaks later.

## Durable knowledge worth remembering

- Full pytest suite lands at **457 passing** as of this session.
- Reusable live-validation harness: `scripts/cr_live_validate.py`.
- YAML `category_id` labels may not match portal reality (Sumter confirmed; Lake Wales partial).
  One audit candidate for a future session.
- Tyler subclass validation pattern established: live scrape + anonymized fixture + adapter test +
  registry drift check all land together.

## Items NOT done + why

- **Haines City production throttling.** Detail-page fan-out concern surfaced in item 10 but not
  fixed. Needs scheduler-level or adapter-level rate limiting.
- **YAML `category_id` audit across 97 FL configs.** Genuinely large task; Sumter was one confirmed
  drift and Lake Wales has partial drift. Deferred to a fresh session.
- **Lake Wales CC `category_id` refinement.** Currently pulls Planning and Zoning Board instead of
  City Commission. Small fix once the right ID is identified via portal recon.
- **HEAD/GET asymmetry detection pattern.** No reusable helper added; the Bay recon note
  documents the finding but the portal-health check utility is still a thought.
