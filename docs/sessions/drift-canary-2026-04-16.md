# Drift Canary — 2026-04-16

Status: DRY-RUN

## Summary
- CR configs exercised: 79
- PT adapters exercised: 16
- PASS: 0, PARTIAL: 0, FAIL: 0, SKIPPED: 3

## Commission Radar
| slug | platform | status | note |
|---|---|---|---|
| altamonte-springs-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| bartow-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| bartow-pz | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| bay-county-bcc | novusagenda | DRY-RUN | factory=OK, constructor=OK (NovusAgendaScraper) |
| bay-county-pc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| brevard-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| brevard-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| broward-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| broward-county-lpa | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| citrus-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| citrus-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| collier-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| collier-county-ccpc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| collier-county-hex | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| desoto-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| desoto-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| duval-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| duval-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| escambia-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| escambia-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| flagler-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| flagler-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| fort-myers-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| haines-city-cc | escribe | DRY-RUN | factory=OK, constructor=OK (EscribeScraper) |
| haines-city-pc | escribe | DRY-RUN | factory=OK, constructor=OK (EscribeScraper) |
| hernando-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| hernando-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| hialeah-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| highlands-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| highlands-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| indian-river-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| indian-river-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| jackson-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| jackson-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| lake-alfred-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| lake-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| lake-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| lake-wales-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| lee-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| lee-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| marion-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| marion-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| martin-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| martin-county-lpa | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| monroe-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| monroe-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| nassau-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| nassau-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| niceville-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| north-miami-beach-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| okaloosa-county-bcc | granicus | DRY-RUN | factory=OK, constructor=OK (GranicusScraper) |
| okaloosa-county-pz | granicus | DRY-RUN | factory=OK, constructor=OK (GranicusScraper) |
| okeechobee-county-bcc | granicus | DRY-RUN | factory=OK, constructor=OK (GranicusScraper) |
| orange-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| orange-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| palm-beach-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| palm-beach-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| panama-city-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| panama-city-planning-board | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| pasco-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| pasco-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| pembroke-pines-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| pinellas-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| polk-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| polk-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| polk-county-tpo | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| seminole-county-bcc | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| seminole-county-pz | legistar | DRY-RUN | factory=OK, constructor=OK (LegistarScraper) |
| st-lucie-county-bcc | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| st-lucie-county-pz | civicclerk | DRY-RUN | factory=OK, constructor=OK (CivicClerkScraper) |
| sumter-county-bcc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| sumter-county-pz | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| wakulla-county-bcc | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| wakulla-county-pz | manual | DRY-RUN | factory=OK, constructor=OK (ManualScraper) |
| walton-county-bcc | civicweb_icompass | DRY-RUN | factory=OK, constructor=OK (CivicWebIcompassScraper) |
| walton-county-pz | civicweb_icompass | DRY-RUN | factory=OK, constructor=OK (CivicWebIcompassScraper) |
| winter-garden-cc | civicplus | DRY-RUN | factory=OK, constructor=OK (CivicPlusScraper) |
| winter-haven-cc | granicus_viewpublisher | DRY-RUN | factory=OK, constructor=OK (ViewPublisherScraper) |
| winter-haven-pc | granicus_viewpublisher | DRY-RUN | factory=OK, constructor=OK (ViewPublisherScraper) |

## Permit Tracker
| adapter_slug | portal_type | status | note |
|---|---|---|---|
| bay-county | cityview | DRY-RUN | factory=OK, constructor=OK (BayCountyAdapter) |
| panama-city | cloudpermit | DRY-RUN | factory=OK, constructor=OK (PanamaCityAdapter) |
| panama-city-beach | iworq | DRY-RUN | factory=OK, constructor=OK (PanamaCityBeachAdapter) |
| polk-county | accela | DRY-RUN | factory=OK, constructor=OK (PolkCountyAdapter) |
| okeechobee | tyler-energov | DRY-RUN | factory=OK, constructor=OK (OkeechobeeAdapter) |
| hernando-county | tyler-energov | DRY-RUN | factory=OK, constructor=OK (HernandoCountyAdapter) |
| marion-county | tyler-energov | DRY-RUN | factory=OK, constructor=OK (MarionCountyAdapter) |
| walton-county | tyler-energov | DRY-RUN | factory=OK, constructor=OK (WaltonCountyAdapter) |
| desoto-county-ms | tyler-energov | DRY-RUN | factory=OK, constructor=OK (DeSotoCountyMsAdapter) |
| citrus-county | accela | DRY-RUN | factory=OK, constructor=OK (CitrusCountyAdapter) |
| madison-county-al | cityview | SKIPPED | scrape_mode=fixture |
| winter-haven | accela | SKIPPED | scrape_mode=fixture |
| lake-alfred | accela | DRY-RUN | factory=OK, constructor=OK (LakeAlfredAdapter) |
| haines-city | iworq | DRY-RUN | factory=OK, constructor=OK (HainesCityAdapter) |
| davenport | iworq | DRY-RUN | factory=OK, constructor=OK (DavenportAdapter) |
| lake-hamilton | iworq | SKIPPED | scrape_mode=fixture |
