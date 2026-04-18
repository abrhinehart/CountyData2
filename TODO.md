# TODO — Open Work Backlog

<!-- Structural contract (enforced by tests/test_journal_discipline.py):

     Five canonical module sections: CR, PT, BI, Sales/CD2, Platform/Infra.
     Each module has three subsections:

       ### Open   — work to ship. Counted as "open items" in STATUS.md.
       ### Risks  — monitor-only. Action only when trigger fires. Counted
                    separately as "live risks" in STATUS.md.
       ### Done   — shipped work, staged for the next archive sweep. When
                    this subsection fills up or on quarterly cadence, move
                    entries to docs/todo-archive/TODO-YYYY-QN.md.

     Every `- [ ]` / `- [x]` entry must carry indented sub-bullets within
     5 lines:
       - source: <path-to-journal-or-commit-ref>
       - tags: [...]
       - status: open | risk | done [— free-text trailer allowed after done]

     Placement invariant: `[x]` only under `### Done`, `[ ]` only under
     `### Open` or `### Risks`.

     Every session journal under docs/sessions/ that has a pending-work
     section must be referenced by name in TODO.md OR in any file under
     docs/todo-archive/. Moving a done entry to the archive preserves
     the link. -->

## Commission Radar (CR)

### Open

- [ ] HEAD/GET asymmetry detection pattern: build reusable portal-health utility (e.g. shared/portal_health.py) that GETs and sniffs body, then wire into CR uptime checks (Bay NovusAgenda trigger)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [cr, platform, uptime]
  - status: open

### Risks

- [ ] eScribe JSON endpoint shape drift risk: integration may silently fail if MeetingsCalendarView envelope changes — monitor on quarterly releases
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, haines-city]
  - status: risk

- [ ] eScribe landing-page/panel fallback not implemented: no backup if JSON endpoint is blocked or rate-limited per tenant
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe]
  - status: risk

- [ ] eScribe MeetingType drift across tenants: each new tenant onboarding must run a one-shot probe before authoring YAML body_filter (exact-match by design)
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, onboarding]
  - status: risk

- [ ] eScribe FileStream.ashx may return HTML wrapper instead of PDF: no Content-Type sniff before download write — whole-pipeline concern, deferred
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, download-validation]
  - status: risk

- [ ] eScribe UUID format drift: if tenant serves uppercase or 32-char no-dash UUIDs, dedup still works but cross-tenant comparison may break
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe]
  - status: risk

- [ ] eScribe non-`pub-` tenant subdomain variants unverified: JSON endpoint path not confirmed across www.<slug>/<slug> prefixes — escalate at next non-Haines-City onboarding
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, onboarding]
  - status: risk

- [ ] eScribe CC Special Meetings vs Workshops: Workshops currently excluded by default; confirm with user whether they should be included
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, haines-city, product-decision]
  - status: risk

- [ ] eScribe Minutes extraction not in scope: PostMinutes PDFs visible but unharvested; ~15-line delta when pipeline wants minutes listings
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, feature]
  - status: risk

- [ ] eScribe Meeting.aspx HTML fallback unused: if future tenant serves JSON with empty MeetingDocumentLink (packets only in Meeting.aspx), two-pass design needed
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe]
  - status: risk

- [ ] eScribe Planning Commission inclusion: Session G ships both CC + PC YAMLs; one-file revert if user objects
  - source: docs/sessions/2026-04-16-session-g-haines-city-escribe-plan.md
  - tags: [cr, escribe, haines-city, product-decision]
  - status: risk

### Done

<!-- Entries land here on ship; sweep to docs/todo-archive/TODO-YYYY-QN.md quarterly. -->

## Permit Tracker (PT)

### Open

- [ ] Haines City iWorQ production throttling: adapter fires detail-page GET per row (no permit-type column); scales poorly, needs scheduler-level or adapter-level rate limiting
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [pt, haines-city, iworq, production]
  - status: open

- [ ] ACCELA-07: bench item (P2) — opportunistic Polk Accela improvement; scope deferred
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-08: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-09: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-10: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-12: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-13: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-15: bench item (P2) — opportunistic Polk Accela improvement
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, polk, accela, p2]
  - status: open

- [ ] ACCELA-16 (Winter Haven COWH Enforcement-module HTML probe): P1 still open from prior session; requires live recon against Enforcement module
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, winter-haven, accela, p1]
  - status: open

- [ ] ArcGIS-centroid fallback for rural addresses: Census-TIGER geocoder misses rural-road coverage (e.g. 7118 CANOPY LN LAKELAND) — separate ticket after ACCELA-11
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [pt, accela, geocoding]
  - status: open

- [ ] Build Clusters H, K-M: iCompass/CivicWeb (Walton FL CR — note iCompass now landed in Session F), MyGovernmentOnline (Santa Rosa FL PT), PermitTrax/Bitco (Okaloosa FL PT); new adapter builds per `tmp/priority1-portal-matrix.md`
  - source: commit:c0ab4ed
  - tags: [pt, cr, expansion]
  - status: open

- [ ] Okaloosa CD2 blocker re-resolve: LandmarkWeb decommissioned, Tyler self-service client needed (note: partial progress landed in Session E)
  - source: commit:dcd1789
  - tags: [cd2, okaloosa, sales]
  - status: open

### Risks

<!-- none tracked -->

### Done

<!-- Entries land here on ship; sweep to docs/todo-archive/TODO-YYYY-QN.md quarterly. -->

## Builder Inventory (BI)

### Open

- [ ] One-off UPDATE parcels SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom) to backfill pre-existing Bay FL invalid parcel 07384-109-000
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [bi, bay-county, data-fix]
  - status: open

- [ ] FL Cadastral BI deprioritized per feedback_cadastral_deprioritized.md (annual resolution too low); confirm remove-entirely decision with user
  - source: commit:c0ab4ed
  - tags: [bi, cadastral]
  - status: open

### Risks

<!-- none tracked -->

### Done

<!-- Entries land here on ship; sweep to docs/todo-archive/TODO-YYYY-QN.md quarterly. -->

## Sales / CD2

### Open

- [ ] Transactions.geom population: PostGIS ready but column still NULL across all rows
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [sales, postgis]
  - status: open

- [ ] Raw-land legal extraction productionization: tools/raw_land_legal_benchmark.py is manual/benchmark-only — needs pipeline integration
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [sales, raw-land, extraction]
  - status: open

### Risks

<!-- none tracked -->

### Done

<!-- Entries land here on ship; sweep to docs/todo-archive/TODO-YYYY-QN.md quarterly. -->

## Platform / Infra

### Open

- [ ] SQLAlchemy legacy Query.get warning at modules/commission/routers/roster.py:164 — migrate to Session.get (2.0 API)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [platform, sqlalchemy, warning]
  - status: open

- [ ] LDC (Land Development Code) module plan — not started; see docs/modules/CountyData2_LDC_Module_Build_Plan.md
  - source: commit:73e29be
  - tags: [ldc, module]
  - status: open

- [ ] Polk County 120-day production backfill: validation only ran 14d; production scheduler must do bootstrap on first deployment (off-hours)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [platform, polk, pt, bootstrap]
  - status: open

- [ ] Cross-module audit for other "re-query before flush" sites in modules/permits/ and modules/commission/ (Entry 2 follow-up)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [platform, audit]
  - status: open

- [ ] CR validation against jurisdictions outside FL: 98 FL YAMLs seeded; TX and VA folders empty
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [cr, multi-state]
  - status: open

- [ ] Step-3 keyword filter at routers/process.py:391 still reads YAML via load_jurisdiction_config (Entry 7 tech debt)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [platform, cr, tech-debt]
  - status: open

- [ ] API-map authoring discipline: write maps code-referenced (with commit SHAs + line numbers) or auto-generate "Extracted? YES/NO" via audit_api_maps.py — portal-first second-pass drift has been the recurring root cause
  - source: docs/sessions/2026-04-15-polk-accela-hardening.md
  - tags: [platform, docs, process]
  - status: open

### Risks

<!-- none tracked -->

### Done

<!-- Entries land here on ship; sweep to docs/todo-archive/TODO-YYYY-QN.md quarterly. -->

## Drift canary regressions
<!-- Managed by scripts/drift_canary_full.py --append-regressions. Do NOT hand-edit. -->
