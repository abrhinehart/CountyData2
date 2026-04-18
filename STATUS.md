# CountyData2 — STATUS

_Generated: 2026-04-18T18:48:50Z_ — regenerate via `python scripts/status.py --write`.

## HEAD
- commit: f11fd277b6e66c9174aa85a026f3946368767905
- short: f11fd27
- date: 2026-04-18 12:33:55 -0400
- subject: fix(api-maps): Mulberry runs own Accela tenant (not paper/email)
- tag: v2.0.0-unified-validated-115-gf11fd27
- working tree: 4 modified / 1 untracked

## Test baseline
- pytest collected: 583
- last known passing: 573 + 23 subtests (updated on --write if pytest cache shows a green run)
- known warnings: SQLAlchemy legacy Query.get at modules/commission/routers/roster.py:164

## Commission Radar (CR)
- platform scrapers: 9 (civicclerk.py, civicplus.py, civicweb_icompass.py, escribe.py, granicus.py, granicus_viewpublisher.py, legistar.py, manual.py, novusagenda.py)
- FL jurisdiction configs (active, excl. BOA/ZBA and _florida-defaults): 79
- platforms represented: civicclerk, civicplus, civicweb_icompass, escribe, granicus, granicus_viewpublisher, legistar, manual, novusagenda

## Permit Tracker (PT)
- adapter modules: 19
- seed-declared jurisdictions: 16 (live: 13, fixture: 3)
- adapters with scrape_mode=live: bay-county, citrus-county, davenport, desoto-county-ms, haines-city, hernando-county, lake-alfred, marion-county, okeechobee, panama-city, panama-city-beach, polk-county, walton-county

## Drift canary
- last full-sweep run: docs/sessions/drift-canary-2026-04-16.md
- last status: DRY-RUN

## TODO
- open items: 24
- live risks: 10
- see [TODO.md](TODO.md)
