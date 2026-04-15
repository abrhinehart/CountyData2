# Session Journal — 2026-04-15 Accela P1 Wrap-up

**Branch:** `main` (no feature branches this session)
**Commits pushed:** 2 commits from `8ccf3d8` through `a04fcfd`
**Session pattern:** 2 triad-agent-v2 runs (ACCELA-04 standalone, then ACCELA-04a/01/11/14 batch) plus inline audit housekeeping
**Date arc:** 2026-04-15 afternoon, continuation of the morning Polk hardening session

## Session goal

Close out all remaining P1 tickets on the Polk improvement report (`docs/api-maps/polk-county-improvement-report.md`). Entered the session with ACCELA-03/05/06 already shipped and ACCELA-02 blocked; left with ACCELA-04/04a/01/11/14 all shipped. The P1 queue is now empty — only P2 opportunistic and P3 blocked items remain.

## Test count delta

- Start of session: **461 passing** (matched prior-session baseline)
- After ACCELA-04 triad: **462 passing** (+1 for `test_parse_contact_fields_from_flat_text`)
- End of session: **466 passing** (+4 total: +1 ACCELA-04 contact test, +1 ACCELA-04a subcontractor test, +1 ACCELA-01 multi-type iteration test, +1 ACCELA-01 per-type exception test)

Full suite passes with no skips or xfails introduced this session.

## Work log (chronological)

1. **Project reload.** Full audit of CountyData2 state — 4/4 modules live and validated, 18,109 sales transactions, 12/98 CR jurisdictions validated, 7/7 PT jurisdictions configured. Identified starting point: run `scripts/audit_api_maps.py` against the 10 new-county api-maps that landed earlier today.

2. **Api-map audit run.** Scanned 79 maps across 33 counties in <0.5s. Result: 0 drift on the 10 new-county maps (Hernando, Marion, Pasco, Volusia, Duval, Seminole, Madison AL, Jefferson AL, Baldwin AL, Montgomery AL). The worry that they'd have the same drift class as Polk/Citrus/Charlotte didn't pan out. One pre-known P2 drift survived: IWORQ-05 on Lake Hamilton. Fixed it inline — updated the table row and narrative §4 in `polk-county-iworq.md` to reflect the real blocker (reCAPTCHA + `scrape_mode='fixture'`) instead of the weaker "URL unverified." Re-ran audit: 0 drift confirmed.

3. **Triad 1 — ACCELA-04: Structured contacts DOM parse.** The first triad of the session. Planner designed a 3-wave plan: Wave 1 (discovery + fixture capture + migration draft), Wave 2 (6 regex patterns + services.py wiring across 8 SQL sites), Wave 3 (unit test with 4 cases + live smoke + ingestion round-trip + doc flips). Executor completed all waves. Key finding during Wave 1 recon: Polk's ACA renders no applicant address in the anonymous view, so `raw_applicant_address` is correctly NULL on Polk by design. QA approved on Round 1 — verified LP-link terminator regression guard uses strong equality (`== "CBC9999999"`) not weak (`!= None`), confirmed services.py index shifts, confirmed no sibling adapter edits. Deliverables: migration 024 (6 TEXT columns), 6 new regex patterns on `AccelaCitizenAccessAdapter`, services.py wired through all 8 SQL sites (INSERT cols 22→28), 1 new unit test, doc flips on `polk-county-accela.md` and improvement report. Live smoke coverage: phone 297/298, email 272/298, license 272/298, company 122/298 (corp-suffix gated).

4. **Triad 2 — ACCELA-04a/01/11/14 batch wrap-up.** The second triad tackled the four remaining P1 tickets. Planner produced a 3-wave plan with cross-cutting decisions: 9 curated record types for Polk (not all 27), scalar TEXT column for subcontractors (not a separate table), Windows Task Scheduler for the canary (not GitHub Actions). Executor completed all implementation and tests (466 passing) but exited mid-run during a long 9-type × 30-day live smoke without posting a clean summary. Main thread verified all files on disk, ran the test suite, ran the audit tool (0 drift), and dispatched QA. QA approved on Round 1 — verified type strings match live dropdown recon, services.py index shifts clean, schtasks registered correctly, no scope creep.

5. **Commit + push.** Two commits:
   - `8ccf3d8` — Lake Hamilton IWORQ-05 doc fix (1 file, 3+/3-)
   - `a04fcfd` — Accela P1 wrap-up: ACCELA-04/04a/01/11/14 (11 files, 911+/51-)
   Combined commit for the wrap-up was chosen over per-ticket hunk-staging because the adapter, services.py, test file, and improvement-report doc all have changes from 3+ tickets interleaved. Prior session precedent: "combined commit strategy works when the work shares files."

6. **Drift canary manual test-fire.** Kicked off `scripts/drift_canary.py` in background to verify end-to-end before the first scheduled fire on 2026-05-01. The 9-type × 30-day Polk fetch is long-running; result pending at time of journal entry. If it passes, the canary is fully validated. If it fails, investigate before the May 1 auto-fire.

## Per-ticket summary

### ACCELA-04 — Structured contacts DOM parse
- **Migration 024:** 6 TEXT columns (`raw_applicant_company`, `raw_applicant_address`, `raw_applicant_phone`, `raw_applicant_email`, `raw_contractor_license_number`, `raw_contractor_license_type`)
- **Parser:** 6 regex patterns on flattened CapDetail text, anchored on `Applicant:` / `Licensed Professional:` section labels
- **Known fuzzy field:** `raw_applicant_company` captures `"Jeff Cunningham LGI Homes"` (name + company combined) because there's no label delimiter between personal name and business name in the flat text. Documented in adapter docstring; downstream dedupe against `raw_applicant_name`
- **Live-recon target:** Polk BR-2026-2894 (LGI HOMES FLORIDA LLC)

### ACCELA-04a — Subcontractor list extraction
- **Migration 025:** 1 TEXT column (`raw_additional_licensed_professionals`)
- **Serialization:** `NAME|LICENSE_NUMBER|LICENSE_TYPE` per LP, joined by `; ` between LPs
- **Parser:** `additional_licensed_professionals_pattern` captures the segment after `View Additional Licensed Professionals>>`, then `_parse_additional_lps()` walks enumerated `\d+\)\s+` items
- **Live-recon target:** Polk BR-2026-2659 (4 subcontractors: Roofing CCC1336147, Plumbing CFC1431566, General CGC1526755, Electric EC13015339)

### ACCELA-01 — Iterate curated record types on Polk
- **Base adapter change:** `target_record_types: tuple[str, ...] = ()` on `AccelaCitizenAccessAdapter`; `_resolve_record_types()` falls back to `(target_record_type,)` when tuple is empty, preserving back-compat for Citrus/Lake Alfred/Winter Haven
- **Polk override:** 9 curated types — Residential New/Renovation/Accessory, Commercial New, Trades Re-Roof/Electrical/Plumbing/Mechanical/Pool. Live dropdown recon corrected the original estimate of 34+ to 27 actual types, and corrected type strings (e.g. `Building/Trades/Re-Roof/NA` not `Building/Trade/Roofing/NA`)
- **Safety:** `record_type_delay=2.0s` between iterations, `try/except` per type so a single 500 doesn't abort the batch

### ACCELA-11 — Lat/lon via geocoding.py
- **Finding:** wire was already routed. `services.py:_run_single_adapter` computes `missing_coordinate_addresses` post-ingest and calls `geocode_missing_permits`; `geocoding.py` has FL hints for all Polk-area jurisdictions
- **Smoke:** 2/3 Polk addresses geocoded (410 E ORANGE ST LAKELAND → 28.0418,-81.9540; 600 NORTH BROADWAY AVE BARTOW → 27.9006,-81.8433). Rural 7118 CANOPY LN LAKELAND misses due to Census-TIGER rural-road coverage gap — not a wiring bug
- **Outcome:** no code change; doc-only flip. ArcGIS-centroid fallback deferred to separate ticket

### ACCELA-14 — Monthly drift canary
- **Script:** `scripts/drift_canary.py` — three checks: audit subprocess, live Polk fetch with pinned-permit fallback, 5-field NotNull assert
- **Runbook:** `docs/permits/drift-canary-runbook.md` — copy-pasteable `schtasks /Create`, `/Query`, `/Run`, `/Delete` commands + manual fallback path
- **Scheduled:** Windows Task Scheduler, monthly day 1 at 09:00, task name `CountyData2-DriftCanary`. Registered and verified via `schtasks /Query`
- **First auto-fire:** 2026-05-01 09:00

## Key findings worth remembering

1. **The 10 new-county api-maps are clean.** The drift-audit tool (`scripts/audit_api_maps.py`) returned 0 drift / 0 suspicious against all 79 maps including the new counties. Writing scrapers against these maps is safe — no false-drift risk.

2. **ACCELA-11 was already done.** The geocoding pipeline was wired end-to-end during the Permit Tracker port (Phase 3 unification). The improvement report originally framed this as "latitude/longitude hard-coded None in the permit dict" but that's the adapter output — the ingest path calls `geocode_missing_permits` afterward. This is the kind of gap where improvement-report framing ("adapter outputs None") diverges from pipeline reality ("post-ingest geocoder fills it in"). Future improvement reports should trace the full ingest path, not just the adapter surface.

3. **Polk exposes 27 record types, not 34+.** The original estimate in the improvement report was wrong. Live dropdown recon corrected both the count and the exact type strings (e.g. `Building/Trades/Re-Roof/NA` vs the guessed `Building/Trade/Roofing/NA`). Recon is non-negotiable before writing type-iteration code — wrong strings return 0 rows silently, and try/except per type would have hidden the bug.

4. **The "View Additional Licensed Professionals" link is inline, not a separate page.** The subcontractor data is already in the flattened CapDetail text after a JavaScript DOM toggle (`DisplayAdditionInfo`). No extra GET needed. This made ACCELA-04a simpler than expected (single regex + helper vs. extra-request-per-permit).

5. **Combined commits are the right call when 3+ tickets share the same adapter/services/test files.** Hunk-staging across 5 tickets on a 230-line adapter diff would have been error-prone. A single commit with a ticket-structured message preserves traceability. The prior session's precedent held.

6. **Executor subagents can fail on long live-smoke steps.** The second triad's Executor exited mid-run during a 9-type × 30-day Polk scrape without posting a summary. All implementation was done — only the live-smoke verification was incomplete. Mitigation for future sessions: tell Executors upfront to keep live smoke bounded (1-day window or single-type spot-check) and let the drift canary catch prod regressions. The canary exists specifically so we don't need to run full production-scale smoke in the triad.

## Durable knowledge

- Polk dropdown values live at `https://aca-prod.accela.com/POLKCO/Cap/CapHome.aspx?module=Building&TabName=Building` — `<option>` tags under `ddlGSPermitType`. Recon cached in `tmp/dropdown_recon/` (not committed). Re-run if dropdown changes.
- `_resolve_record_types()` on the base adapter makes all Accela adapters multi-type-capable without per-subclass changes. To add record types for Citrus: add `target_record_types` override to `CitrusCountyAdapter`.
- `inspections_on_separate_tab` and `target_record_types` are the two agency-divergence patterns on the base adapter. Both use class-attribute opt-in — follow the same shape for future agency-specific toggles.
- The `raw_applicant_company` column carries fuzzy data (personal name + company merged). Any analytics query should dedupe against `raw_applicant_name` before using company for entity resolution.
- Drift canary uses a pinned-then-fallback permit selection strategy. If BR-2026-2894 ages out of the 30-day rolling window, the canary automatically falls back to the most-recent owner-bearing permit. No manual intervention needed.

## Items NOT done + why

- **Drift canary manual test-fire pending** — kicked off in background, result not yet available. If it fails, investigate before the May 1 auto-fire.
- **ACCELA-16 partial** (Winter Haven Enforcement-module HTML probe) — still open from prior session. P1 but requires live recon against COWH Enforcement module, which is a separate scope.
- **Haines City iWorQ production throttling** — deferred since 2026-04-14. Not touched.
- **Santa Rosa DNS fix** — deferred since 2026-04-14. Not touched.
- **lake-county-pz scraper bug** — returns 0 events when Events API has published events. Deferred since 2026-04-14. Not touched.
- **P2 bench items** (ACCELA-07/-08/-09/-10/-12/-13/-15) — out of scope for this session's P1 wrap-up.

## Commits pushed this session

```
8ccf3d8 docs(polk-iworq): harden IWORQ-05 Lake Hamilton blocker text
a04fcfd accela: wrap-up P1 tickets — ACCELA-04/04a/01/11/14
```

## Suggested next session starting moves

1. Verify drift canary manual test-fire completed successfully. If a `DRIFT_CANARY_FAILED_*.md` marker appeared at repo root, investigate before the May 1 auto-fire.
2. Fix the three deferred items that have been open since 2026-04-14: Santa Rosa DNS, lake-county-pz bug, Haines City throttling. All are small and have been deferred twice.
3. ACCELA-16 partial: probe Winter Haven's Enforcement-module HTML search. If it doesn't share the Building-module auth gate, a fixture-mode scraper with browser-cookie support (matching the Santa Rosa AcclaimWeb hybrid-captcha pattern) may unlock COWH permits.
4. Start scraper work against the 10 new-county api-maps — all confirmed drift-free. Hernando (Tyler EnerGov, already has adapter) and Marion (Tyler EnerGov + BrowserView) are natural first targets since both have existing adapter infrastructure.
