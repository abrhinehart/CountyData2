# CountyData2 — STATUS

_Generated: 2026-04-16T22:05:58Z_ — regenerate via `python scripts/status.py --write`.

## HEAD
- commit: 73e29be994cd0a7aed18916bfab5201ffd1b16e5
- short: 73e29be
- date: 2026-04-16 16:21:52 -0400
- subject: docs: Session G paper trail + LDC module plan + drift canary
- tag: v2.0.0-unified-validated-91-g73e29be
- working tree: 1 modified / 7 untracked

## Test baseline
- pytest collected: 576
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
- open items: 42
- see [TODO.md](TODO.md)
