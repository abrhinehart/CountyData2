# Resume Handoff — CR YAML category_id Audit (paused 2026-04-14)

Paste this into a fresh Claude Code session to continue the triad-v2 audit that was
paused mid-flight.

---

You are resuming a **triad-agent-v2** run that paused after the Planner finished but
before the Executor started. The plan below is complete and approved-to-execute — do
NOT re-plan. Go straight to Executor.

## Environment

- **Worktree:** `C:\Users\arhinehart\Code\CountyData2\.claude\worktrees\cr-yaml-audit`
- **Branch:** `claude/cr-yaml-audit` (based on `claude/silly-cohen` HEAD, commit `4a1513c`)
- **Expected baseline:** `pytest` = 457 passing. Confirm before running Wave 2.
- **No `.venv` in this worktree yet** — Wave 1 Step 1.1 creates it.

## Context (already discovered by Planner — do not re-discover)

- Real path is `modules/commission/config/jurisdictions/FL/*.yaml` (handoff said
  `modules/commission/configs/`; it was wrong).
- 100 YAMLs total in FL, but only **34 carry `category_id`**: 15 civicplus + 19 civicclerk.
  Legistar, granicus, novusagenda, and manual configs do NOT have `category_id` and are
  out of scope for this audit.
- `scripts/cr_live_validate.py` has no batch mode — drive it per-config via a bash loop.
- `tests/test_registry_code_consistency.py` is a **permit** registry drift test, not a
  commission-YAML drift test. Keeping pytest green is a hygiene gate only.
- Seed drifts: Sumter BCC already fixed (confirm-only); Lake Wales CC still pointing at
  P&Z (fix in Wave 3); Sumter P&Z has a `# TODO: verify category ID` comment and is a
  drift candidate.
- Bay County BCC is novusagenda, has no `category_id`, and is OUT OF SCOPE (deferred
  item 4 is a different session).

## Full plan from Planner (execute as-is)

### Wave 1: Bootstrap and baseline

1. **1.1 Create venv.** `cd` to worktree, run
   `python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements-dev.txt`.
   Verify: `.venv/Scripts/python.exe -c "import pytest, yaml, requests, bs4"` exits 0.

2. **1.2 Baseline pytest = 457 passing.**
   `.venv/Scripts/python.exe -m pytest -q --tb=no 2>&1 | tail -5` — must contain
   `457 passed`. If not, STOP and investigate.

3. **1.3 Confirm Sumter BCC fix is already present.**
   `grep -E "category_id:\s*3" modules/commission/config/jurisdictions/FL/sumter-county-bcc.yaml`
   must return the `Board of County Commissioners Regular Meeting` line. If it says `5`,
   STOP — branch is not based on the expected commit.

4. **1.4 Build in-scope manifest.** Loop over `modules/commission/config/jurisdictions/FL/*.yaml`,
   skip `_florida-defaults.yaml`, include only files containing `category_id`. Expect 34 lines
   total (15 civicplus + 19 civicclerk). Save to `/tmp/cr_audit_manifest.txt`.

5. **1.5 Create session journal skeleton** at
   `docs/sessions/2026-04-14-cr-yaml-audit.md` with per-config audit table, Drifts-fixed,
   Follow-ups sections (template in the Planner's full output above).

### Wave 2: Live validation sweep (batch over manifest)

Template per config (run concurrently across the 34-config manifest; add 2s outer sleep
between tenants):

- **2.T.1:** `.venv/Scripts/python.exe scripts/cr_live_validate.py <yaml-path> 2025-10-01 2026-04-14 > tmp/cr_audit/<slug>.json 2>&1`
- **2.T.2:** Parse each JSON. Classify as OK / DRIFT / EMPTY / FLAKE by cross-checking
  `first_three[].title` against the YAML's `detection_patterns.header_keywords`. OK =
  PASS + titles match keywords. DRIFT = PASS + titles do NOT match keywords (Lake Wales
  pattern). EMPTY = non-PASS + listings=0. FLAKE = non-PASS + network error.
- **2.T.3:** Write row to session-journal audit table.

Output: `tmp/cr_audit/summary.csv` + 34 per-slug JSONs + 34 rows in the journal table.

### Wave 3: Drift resolution (only for DRIFT/EMPTY entries)

Expected population ~2–6 (Lake Wales + Sumter P&Z minimum). For each:

- **3.T.1 civicplus recon:**
  `curl -sA "CommissionRadar/1.0" "<base_url>/" > tmp/cr_audit/<slug>_portal.html`
  then extract `aria-controls="category-panel-N"` + adjacent `<h2>` board names.
- **3.T.1 civicclerk recon:**
  `curl -sA "CommissionRadar/1.0" "https://<subdomain>.api.civicclerk.com/v1/EventCategories"`
  — parse `value[].id` + `value[].name`. If 404, fall back to guess-and-check over ids
  1..20 via the harness, classifying by `first_three` titles.
- **3.T.2:** Pick the id whose board name best matches YAML `name` / `commission_type` /
  `header_keywords`.
- **3.T.3:** `Edit` the YAML: change `category_id: <old>` to
  `category_id: <new>  # <board name> (portal panel id <new>; <old> was <wrong-board>)`.
- **3.T.4 Re-validate:** rerun harness; `status` must be PASS and first title must match
  `header_keywords`. Save to `tmp/cr_audit/<slug>.post.json`.
- **3.T.5 Recon note:** write/overwrite `docs/commission/live-validation/<slug>.md`
  mirroring `sumter-county-bcc.md`. Append row to
  `docs/commission/live-validation/INDEX.md`.

### Wave 4: Cleanup, regression, commit

- **4.1:** Strip `# TODO: verify category ID` from any YAML that classified OK in Wave 2.
- **4.2:** Re-run pytest — must stay at 457.
- **4.3:** Append this audit's summary section to `docs/commission/live-validation/INDEX.md`.
- **4.4:** Finalize `docs/sessions/2026-04-14-cr-yaml-audit.md` (table complete, Drifts-fixed
  populated, Follow-ups for anything unresolved).
- **4.5:** Single commit:
  ```
  git add docs/sessions/2026-04-14-cr-yaml-audit.md \
          docs/commission/live-validation/ \
          modules/commission/config/jurisdictions/FL/
  git commit -m "cr: audit FL category_id drift — <N> fixed, <M> deferred"
  ```
  Confirm `git status` is clean. Do NOT commit `.venv/` or `tmp/cr_audit/`.

## Manifest (34 in-scope configs)

**civicplus (15):** altamonte-springs-cc, fort-myers-cc, hialeah-cc, lake-alfred-cc,
**lake-wales-cc (known DRIFT)**, niceville-cc, north-miami-beach-cc, panama-city-cc,
panama-city-planning-board, pembroke-pines-cc, santa-rosa-county-bcc, santa-rosa-county-zb,
**sumter-county-bcc (confirm-only)**, **sumter-county-pz (likely DRIFT)**, winter-garden-cc

**civicclerk (19):** citrus-county-bcc, citrus-county-boa, citrus-county-pz,
collier-county-bcc, collier-county-boa, collier-county-ccpc, collier-county-hex,
escambia-county-bcc, escambia-county-pz, highlands-county-bcc, highlands-county-pz,
jackson-county-bcc, lake-county-bcc, lake-county-pz, lee-county-bcc,
pasco-county-bcc *(validated last session — confirm)*, pasco-county-pz,
st-lucie-county-bcc, st-lucie-county-pz

## Where to resume

After reading this file:

1. Verify worktree + branch + pytest baseline (5 min).
2. Skip straight to **Wave 1 execution** — plan is final, no Planner turn needed.
3. After Wave 4 commits, hand off to QA for sample review (first + last + one random
   middle item from the manifest, plus every item Executor flagged as an outlier).
4. QA rejection cap: 3 rounds. If QA rejects the plan itself (not execution), route
   back to Planner with feedback before 3rd Executor attempt.

## Guardrails (carry forward)

- Do NOT touch MS county configs.
- "BOCC" is ambiguous — verify Accela agency code before keying by abbreviation.
- Pytest must stay at 457 at every checkpoint.
- Do NOT fabricate `category_id` values. If recon can't find the right id, list it as a
  Follow-up in the session journal and leave the YAML untouched.
