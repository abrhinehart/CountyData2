# Session Journal — 2026-04-15 Polk Accela Hardening + REST Probe

**Branch:** `main` (no feature branches this session)
**Commits pushed:** 10 commits from `1a3b12d` through `9ec88a8`
**Session pattern:** 6 triad-agent-v2 runs plus inline direct work for smaller pieces
**Date arc:** started late 2026-04-14 with `/project-reload`, rolled past midnight, wrapped 2026-04-15

## Session goal

Validate the Polk County scraper stack against the 54 api-maps that landed on the `county-api-maps-docs` branch that morning. Convert findings into concrete P0/P1 work and ship as much as possible in one session. The session expanded into six triads after the first one surfaced more issues than expected.

## Test count delta

- Start of session: **457 passing** (matched prior-session baseline after installing missing `python-multipart`)
- End of session: **461 passing** (+2 for Legistar retry tests in triad 3, +1 for owner regex unit test in triad 6)

Full suite passes with no skips or xfails introduced this session.

## Work log (chronological)

1. **Morning housekeeping.** Fast-forwarded local `main` to pick up the prior-session CR-YAML audit and a merge of 54 new api-maps for 21 FL counties (Polk + 20 others). Merged the `county-api-maps-docs` branch into main. Deleted four merged remote branches to clean up the branch list.

2. **Project-reload.** Full audit of CountyData2 state. 4/4 modules live and validated, 18,109 sales transactions, 12/98 CR jurisdictions actively validated, 7/7 PT jurisdictions scraped. Recommended starting point: Santa Rosa DNS fix or the lake-county-pz adapter bug.

3. **Triad 1 — Polk scrapers vs api-maps re-evaluation.** Ran the first triad against Polk. Surface coverage: Accela (POLKCO), ArcGIS (parcels), iWorQ (east-Polk cities), Legistar (BCC + P&Z + BOA-manual). Produced `docs/api-maps/polk-county-improvement-report.md` (372 lines, 43 gaps) with 3 P0 items (ARCGIS-00 drift, ACCELA-05 silent-None inspections, LEGISTAR-03 shipped-but-disabled event items) and 10+ P1/P2 items. The big strategic bullet at the top was ACCELA-02 — "migrate Accela adapters to v4 REST" — framed as P1/L/High-risk.

4. **User meta-question.** After triad 1, the user asked: what went wrong with the api-maps themselves? Three concrete errors had surfaced (inspection parser claim wrong, field count wrong for ArcGIS, Lake Hamilton blocker understated). Diagnosed root cause: maps were written portal-first, the "Extracted?" columns were a memory-based second pass rather than code-referenced. Prevention: write a drift-detection script.

5. **Triad 2 — Build the drift-audit tool.** Created `scripts/audit_api_maps.py` (1083 lines, stdlib-only — uses AST-parsing to read seed files without importing them, since import would trigger a DB connection). Nine check types covering: method-call negation claims, ArcGIS field-count mismatch, ArcGIS "not configured" vs seed, PT blocker undercount, adapter-class references that don't exist, citation staleness, URL host allowlist, YAML platform match, no-artefact-resolved. Runs in 0.33s across all 58 maps. First run surfaced 10 drift + 2 suspicious + 7 info — all 3 Polk errors reproduced plus **one bonus Citrus finding** the prior triad hadn't caught (same inspection drift as Polk).

6. **Triad 3 — Fix 3 api-map drifts surfaced by the audit.** Rewrote Citrus Accela §5, added a 19-edit "Status: Not Implemented" rewrite to Charlotte Accela (the adapter was intentionally deleted 2026-04-14), and corrected St. Lucie CivicClerk L17 (referenced non-existent `CivicClerkAdapter`; real class is `CivicClerkScraper`). Post-audit: 10 drift → 8 drift, 2 suspicious → 0 suspicious. Three commits pushed.

7. **LEGISTAR-03 YAML flip + defensive retry.** Simple two-line YAML change to enable `fetch_event_items: true` on Polk BCC and P&Z. The `_fetch_event_items` code path was shipped in `b16df13` but never enabled on any jurisdiction. Live validation against Polk BCC surfaced two `RemoteDisconnected` errors on vote fetches — memory-predicted "expect at least one compatibility issue on first live run." Added a `_get_json_with_retry` helper that retries once on `ConnectionError` with 1s backoff. Re-ran live validation: clean PASS, 0 errors. Also added `python-multipart` to requirements (was a pre-existing latent break that manifested as 12 test errors on fresh `.venv`).

8. **Triad 4 — ARCGIS-00 + ACCELA-05 (two P0s in one triad).** Shape A' design: added `inspections_on_separate_tab: bool = False` class attribute to the base Accela adapter; Polk and Citrus opt in via `True` (keeps Lake Alfred + Winter Haven at today's default-False behavior). Existing `None` returns from `_parse_inspections` normalized to `[]` via `or []` at the caller. The ARCGIS-00 DB check revealed the **seed/DB drift was real** — Polk's `bi_county_config` row had only 5 of 9 `gis_*_field` columns populated; ran `seed_bi_county_config.py` to reconcile. Three tests adjusted for envelope change (one was an extra — Lake Alfred's test asserted `is None` even though Lake Alfred defaults to `False`; needed updating for the `or []` normalization at the base level, not because of Shape A' specifically).

9. **Accela REST probe — first major strategic finding.** The user created an Accela developer account (initially as Agency App, then switched to Citizen App per my advice). Built `scripts/accela_rest_probe.py` to sweep 16 v4 endpoints with anonymous + client_credentials auth patterns. Three runs against POLKCO revealed:
   - Agency App doesn't support `client_credentials` grant (expects password grant with real staff creds, which we don't have)
   - Citizen App doesn't support `client_credentials` either (expects authorization_code with browser redirect — per-citizen flow)
   - All endpoints with just the App ID header return either `anonymous_user_unavailable` (agency-toggle not enabled) or `no_token` (endpoint always requires bearer token, regardless of agency config)
   - **Cross-agency probe confirmed systemic**: POLKCO, CITRUS, COLA, BOCC, BREVARD all have `anonymous_user_unavailable`. Not one FL agency we care about has the anonymous user toggle enabled.

   This materially contradicted the improvement report's ACCELA-02 framing that REST would be the strategic unlock. The HTML scraping path we already use is actually the correct mechanism — Accela's architecture separates the ACA citizen portal (anonymous HTML, what we use) from the v4 REST API (authorized integrations, which require agency cooperation we don't have).

10. **Triad 5 — REST probe findings + report reframing.** Created `docs/api-maps/accela-rest-probe-findings.md` (135 lines) capturing the probe methodology, evidence tables, 6 findings, and three theoretical unblock paths (agency enables anonymous user, agency provides staff creds, per-citizen OAuth — all out of reach). Made ~15 surgical edits to the improvement report: ACCELA-02 reclassified P1 → P3/BLOCKED, Executive Summary rewritten to promote the HTML-hardening sequence (ACCELA-06 + 03 + 04 + 01) as the new "highest strategic-value" bullet, 8 other ACCELA rows had their Recommended Action columns rewritten to center the HTML path, Theme 1 flipped from "REST is the strategic unlock" to "REST is NOT the strategic unlock". Two commits.

11. **Triad 6 — Path A: ACCELA-06 closed as blocked.** Intended to implement ACCELA-06 (fetch Inspections sub-tab HTML). The Planner did live recon before designing code and discovered the Inspections tab **is also blocked at the platform level**: not a separate page, just a hash-anchored `<div id="tab-inspections">` whose rows load via a `btnRefreshGridView` partial postback that returns an MS-AJAX delta with empty `panelsToRefreshIDs` for anonymous users. Tested on 10+ permits across POLKCO, BREVARD, and BOCC — all returned byte-identical "There are no completed inspections on this record." placeholder. Same gate as ACCELA-02. Pivoted to documentation: updated adapter comment (the ACCELA-05 comment had said "moves to REST API (ACCELA-06)" — wrong on both counts now), reclassified ACCELA-06 to P3/Blocked, rewrote §5 in Polk and Citrus api-maps, appended Finding 7 to the REST probe findings doc.

12. **Triad 6 — Path B: ACCELA-03 owner extraction shipped.** Live recon against Polk BR-2026-2894 validated the regex shape. Added three patterns (owner_name, owner_address, fallback for alternate layouts), migration 023 with two new TEXT columns (`raw_owner_name`, `raw_owner_address`), services.py wiring across 8 SQL sites, and a dedicated 4-case unit test. Live smoke extracted `LGI HOMES FLORIDA LLC` + `1450 LAKE ROBBINS DR STE 430 THE WOODLANDS TX 77380` as expected. Covers Polk / Citrus / Lake Alfred / Winter Haven (shared base adapter). REST `/v4/records/{id}/owners` remains blocked; HTML is the only path.

    Paths A and B landed as a single combined commit (`9ec88a8`) because they touched 5 shared files with non-overlapping but interleaved edits; splitting would have required hunk-by-hunk staging with real risk of error.

## Key findings worth remembering

1. **The REST v4 API is not a viable path for bulk anonymous extraction across Accela FL agencies.** Every tested agency has the anonymous-user toggle disabled at the Civic Platform level. Endpoints split into two classes: anonymous-eligible (only if agency enables the toggle, which none of ours do) and token-mandatory (always require a bearer token, regardless of agency config). Most of the data we want is in the token-mandatory class. HTML scraping via the ACA portal is the architecturally correct mechanism for our use case — REST is for authorized integrations, a different audience.

2. **Inspections are also platform-gated, not just token-gated.** The HTML tab-fetch alternative to REST `/inspections` turns out to be the same gate — anonymous users get a hardcoded empty placeholder regardless of permit state. Real inspections data requires either admin auth or agency-admin toggle enablement. Both ACCELA-02 and ACCELA-06 are now P3/Blocked for the same underlying reason.

3. **Seed-file edits don't retroactively apply to existing DB rows.** ARCGIS-00 was a real drift — Polk's `bi_county_config` row had 5 fields when the seed file had 9. This is the exact class of drift the audit tool was built to catch. Editing a seed and expecting the prod DB to reflect it is an easy mistake; worth building a runbook step: "after editing a seed file, re-run the seed script."

4. **The drift-audit tool caught a map error we didn't know about.** The Citrus Accela map had the same inspection-parser-claim drift as Polk's. The triad-1 audit of Polk would never have caught the Citrus case. One-pass automation across all 58 api-maps in 0.33s is meaningfully cheaper than per-county triads.

5. **API-map quality matters for the triad process.** Three of the four outliers the triad-1 QA found were the api-map being wrong about the code, not the code being wrong about the api-map. Future api-maps should be written code-referenced (with commit SHAs and line numbers) not portal-first. Or the "Extracted? YES/NO" sections should be auto-generated by a script like `audit_api_maps.py` instead of hand-maintained.

6. **Agency App vs Citizen App is a meaningful distinction in Accela.** Agency Apps expect password-grant authentication with real staff credentials; Citizen Apps expect authorization_code with a browser redirect per end user. Neither shape supports the "third-party systematically reading public data" pattern. Only the anonymous-user agency toggle does — and that's off everywhere we've tested.

7. **The combined-triad commit strategy (Path A + Path B) works when the work shares files.** Trying to split a narrative when 5 of 8 files have non-overlapping edits from both paths is error-prone. A single commit with a message that clearly structures both threads is the pragmatic call.

## Durable knowledge

- Audit tool at `scripts/audit_api_maps.py` runs in under 0.5s across all 58 api-maps and catches structural drift between maps and code. Should be re-run whenever new api-maps land.
- Probe tool at `scripts/accela_rest_probe.py` is reproducible — reads `.env` for `ACCELA_APP_ID` and `ACCELA_APP_SECRET`, sweeps 16 v4 endpoints per agency. Output is a markdown compatibility matrix.
- Polk BR-2026-2894 is a known-working Accela probe target (active residential new permit at 7118 CANOPY LN LAKELAND, owned by LGI HOMES FLORIDA LLC). Useful for future live-recon sessions.
- Legistar event-items flow has a defensive retry-on-ConnectionError wrapper now. If you add event-items to more jurisdictions, the scaffolding already handles transient Legistar API flakes.
- `inspections_on_separate_tab` class attribute is the pattern for "this agency's layout differs from the base" — follow the same shape for future agency-specific toggles.

## Items NOT done + why

- **ACCELA-04** (structured contact DOM parsing) — skipped for time; natural next ticket after ACCELA-03.
- **ACCELA-11** (lat/lon via existing `geocoding.py`) — skipped for time; one-line wire.
- **ACCELA-01** (34+ record-type iteration) — skipped for scope.
- **ACCELA-14** (monthly drift canary, now permanent since REST escape hatch is gone) — not started. Wants its own session to stand up the cron.
- **IWORQ-05** (Lake Hamilton api-map doc fix — the last remaining Polk drift in the audit) — left open as P2 cosmetic doc fix.
- **Audit run against the 10 new counties** that landed on remote today (Hernando, Marion, Pasco, Volusia, Duval, Seminole + 4 AL counties). The audit tool can scan them immediately; worth a run at start of next session to catch the same class of drift we caught on Polk/Citrus/Charlotte before building more scrapers.
- **Haines City iWorQ production throttling** — still on the deferred list from 2026-04-14 prior session. Not touched.
- **Santa Rosa DNS fix** — flagged in the project-reload report as a quick win; not started.
- **lake-county-pz scraper bug** (returns 0 when Events API has published events) — flagged in project-reload; not started.

## Commits pushed this session

```
9ec88a8 accela: close ACCELA-06 as blocked + ship ACCELA-03 owner extraction
5863232 docs(polk): reframe ACCELA-02 as blocked, promote HTML path
5315bdc docs(accela): record v4 REST probe findings — REST is not a bulk-extraction path
be5d02f feat(accela-adapter): skip inspections parse on separate-tab agencies (ACCELA-05)
e0493d5 docs(polk-arcgis): close ARCGIS-00 drift (seed maps 9 fields, not 5)
f6ee329 cr: retry Legistar API calls on transient ConnectionError
ce9a3f6 cr: enable Legistar event items + votes on Polk
dbdcf72 docs: fix 3 api-map drifts surfaced by audit
8564bac scripts: add api-map drift audit tool
1a3b12d docs: add Polk County scraper improvement report
```

## Suggested next session starting moves

1. Run `.venv/Scripts/python.exe scripts/audit_api_maps.py` against the 10 new-county api-maps that landed today. Expect the same class of errors we caught on Polk/Citrus/Charlotte. Fix any that surface.
2. Continue Polk P1 HTML-hardening: ACCELA-04 (structured contacts) is the natural next ticket. ACCELA-11 (lat/lon wire via `geocoding.py`) is a smaller alternative if you want a quick win.
3. If you have agency-partnership conversations in motion with Polk County IT, the REST path reopens — but only for that specific agency, and only if they flip the anonymous-user toggle in Civic Platform. Keep an eye on this but don't plan against it.
