# TODO — Open Work Backlog

<!-- Generated initially from session journals on 2026-04-16. Hand-edit freely.
     The tests/test_journal_discipline.py test only enforces that every new session
     journal with a pending-work section has at least one matching entry here. -->

## Commission Radar (CR)

- [ ] santa-rosa-county-bcc & santa-rosa-county-zb: base_url points at santarosafl.gov (no DNS); correct domain is santarosa.fl.gov
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, santa-rosa, yaml]
  - status: open

- [ ] collier-county-boa: Collier civicclerk has no dedicated Board of Adjustment category; cat 32 is Hearing Examiner. Decide remove vs re-point vs different portal
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, collier, yaml, boa]
  - status: open

- [ ] north-miami-beach-cc: NMB AgendaCenter has no City Commission category; CC agendas live on a different platform — identify correct portal
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, north-miami-beach, yaml, platform-discovery]
  - status: open

- [ ] pembroke-pines-cc: AgendaCenter hosts advisory boards only, no City Commission category — same situation as NMB, identify correct platform
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, pembroke-pines, yaml, platform-discovery]
  - status: open

- [ ] winter-garden-cc: category_id fixed to 6 but no new CC agendas since March 2025; confirm whether Winter Garden migrated to granicus/iQM2 or similar
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, winter-garden, yaml, platform-migration]
  - status: open

- [ ] lake-county-pz: adapter returns 0 listings despite civicclerk Events API having published events — scraper date/visibility filter bug
  - source: docs/sessions/2026-04-14-cr-yaml-audit.md
  - tags: [cr, lake-county, civicclerk, adapter-bug]
  - status: open

- [ ] HEAD/GET asymmetry detection pattern: build reusable portal-health utility (e.g. shared/portal_health.py) that GETs and sniffs body, then wire into CR uptime checks (Bay NovusAgenda trigger)
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [cr, platform, uptime]
  - status: open

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

## Permit Tracker (PT)

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

## Builder Inventory (BI)

- [ ] One-off UPDATE parcels SET geom = ST_MakeValid(geom) WHERE NOT ST_IsValid(geom) to backfill pre-existing Bay FL invalid parcel 07384-109-000
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [bi, bay-county, data-fix]
  - status: open

- [ ] FL Cadastral BI deprioritized per feedback_cadastral_deprioritized.md (annual resolution too low); confirm remove-entirely decision with user
  - source: commit:c0ab4ed
  - tags: [bi, cadastral]
  - status: open

## Sales / CD2

- [ ] Transactions.geom population: PostGIS ready but column still NULL across all rows
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [sales, postgis]
  - status: open

- [ ] Raw-land legal extraction productionization: tools/raw_land_legal_benchmark.py is manual/benchmark-only — needs pipeline integration
  - source: docs/sessions/2026-04-14-project-reload.md
  - tags: [sales, raw-land, extraction]
  - status: open

## Platform / Infra

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

- [x] Drift canary manual test-fire verification still pending: confirm no DRIFT_CANARY_FAILED_* marker from the 2026-04-15 test run before May 1 auto-fire
  - source: docs/sessions/2026-04-15-accela-p1-wrapup.md
  - tags: [platform, canary]
  - status: done 2026-04-16 — no failure marker at repo root; drift-canary-2026-04-15.md Status: PASS

- [x] Audit tool run against the 10 new counties that landed on remote (Hernando, Marion, Pasco, Volusia, Duval, Seminole + 4 AL counties) — catch same class of drift we caught on Polk/Citrus/Charlotte before building more scrapers
  - source: docs/sessions/2026-04-16-10-county-audit-sweep.md
  - tags: [platform, audit, api-maps]
  - status: done — 0 drift / 0 suspicious / 0 info across 21 scanned maps

- [ ] API-map authoring discipline: write maps code-referenced (with commit SHAs + line numbers) or auto-generate "Extracted? YES/NO" via audit_api_maps.py — portal-first second-pass drift has been the recurring root cause
  - source: docs/sessions/2026-04-15-polk-accela-hardening.md
  - tags: [platform, docs, process]
  - status: open

## Drift canary regressions
<!-- Managed by scripts/drift_canary_full.py --append-regressions. Do NOT hand-edit. -->
