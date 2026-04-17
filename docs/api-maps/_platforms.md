# API Mapping — Platforms Registry

Living list of county-government web platforms observed across all mapped jurisdictions. Used as the source of truth for platform fingerprinting (see county-api-mapping-instructions.md §5). Fingerprint once per hostname — if a hostname appears here, skip re-discovery and jump to probing the known endpoint patterns.

When a new platform is discovered during a mapping run, add a row. Do not delete rows: if a platform is no longer used anywhere, leave it — the entry documents the signatures that would still identify it if it reappears.

## Columns

- **Platform** — product name as the vendor brands it.
- **Vendor** — parent company (often different from the product name).
- **Hostnames** — observed URL patterns (subdomains, root domains). Wildcards welcome.
- **Signatures** — HTML/header/cookie markers that fingerprint the platform in seconds.
- **Known endpoint patterns** — paths worth probing even when the front-end UI doesn't link to them.
- **Adapter in repo** — path (relative to repo root) of the scraper / client module, if we have one.

## Registry

| Platform | Vendor | Hostnames | Signatures | Known endpoint patterns | Adapter in repo |
|---|---|---|---|---|---|
| **Legistar** | Granicus | `*.legistar.com` | "Meeting Portal" branding, `WebSessionID` cookie | `/View.ashx`, `/Calendar.aspx`, `/DepartmentDetail.aspx`, `/MeetingDetail.aspx`, `/LegislationDetail.aspx` | `cr/adapters/legistar.py` |
| **CivicClerk** | Diligent / CivicPlus | `*.civicclerk.com` | `civicclerk` in script srcs, `/Web/GenericHooks` | `/Web/GenericHooks`, `/api/v1/Meetings`, `/api/v1/Events` | `cr/adapters/civicclerk.py` |
| **CivicWeb / iCompass** | iCompass (Diligent) | `*.civicweb.net` | `CivicWeb` footer, ASP.NET viewstate | `/Documents/Filings`, `/Documents/GenericGrid`, RSS at `/Documents.aspx?rss` | `cr/adapters/civicweb.py` |
| **eScribe** | eSCRIBE Software | `pub-*.escribemeetings.com` | `escribe` in URL, JSON POSTs to `/MeetingsCalendarView.aspx/GetCalendarMeetings` | `/MeetingsCalendarView.aspx/GetCalendarMeetings`, `/Meetings.aspx?Id=…` | `cr/adapters/escribe.py` |
| **NovusAgenda** | Novus Systems | `*.novusagenda.com` | `DisplayAgendaPDF.ashx` anchor pattern, `agendapublic/` path | `/agendapublic/`, `/agendapublic/DisplayAgendaPDF.ashx?…`, `/agendapublic/meetingsearch.aspx` | `cr/adapters/novusagenda.py` |
| **iQM2 / MinutesOnDemand** | Granicus | `*.iqm2.com` | `iqm2` in URL, "MinutesOnDemand" branding | `/Citizens/Board.aspx`, `/Citizens/Meeting.aspx`, RSS feeds | `cr/adapters/iqm2.py` |
| **CivicPlus Agenda Center** | CivicPlus | `*.civicplus.com`, customer domains with `/AgendaCenter/` | "Powered by CivicPlus" footer, `/AgendaCenter/ViewFile/Agenda/…` | `/AgendaCenter/`, `/AgendaCenter/Search/`, `/ArchiveCenter/` | `cr/adapters/civicplus.py` |
| **Granicus ViewPublisher** | Granicus | `*.granicus.com`, customer domains | `ViewPublisher.php`, "powered by Granicus" | `/ViewPublisher.php`, `/MediaPlayer.php`, `/api/` | `cr/adapters/granicus.py` |
| **BoardDocs** | Diligent | `go.boarddocs.com`, `*.boarddocs.com` | `boarddocs` in URL, iframe-embedded portal | `/public/` JSON endpoints (undocumented, discovered via XHR) | _(none yet)_ |
| **PeakAgenda** | Peak Democracy / OpenGov | `*.peakagenda.com` | `peakagenda` in URL | `/api/meetings`, `/api/agenda-items` | _(none yet)_ |
| **OnBase** | Hyland | `onbase` in URL | Hyland branding, `/AppNet/`, `/OnBaseHttp/` | `/AppNet/`, `/OnBaseHttp/` | _(none yet)_ |
| **ArcGIS REST** | Esri | `*.arcgis.com`, `/arcgis/rest/services/` | any `?f=json` response, FeatureServer / MapServer | `/arcgis/rest/services/?f=json`, `/FeatureServer/`, `/MapServer/` | `bi/clients/arcgis.py` |
| **OpenGov** | OpenGov | `*.opengov.com` | "Powered by OpenGov", `/budget/`, `/checkbook/` | `/api/v2/`, budget and checkbook endpoints | _(none yet)_ |
| **Tyler EnerGov (SelfService)** | Tyler Technologies | customer domains with `/EnerGovProd/SelfService/` or `/energovpub/selfservice/` | "Powered by Tyler Technologies", EnerGov in URL | `/EnerGovProd/SelfService/#/home`, `/energovpub/selfservice/api/energov/`, case-search JSON POSTs | `pt/adapters/tyler_energov.py` |
| **Tyler Munis SelfServe** | Tyler Technologies | `*.tylertech.com`, `selfservice.*` | MUNIS branding, session cookies with `MUNIS` prefix | `/MSS/`, `/api/public/` | _(none yet)_ |
| **Accela Citizen Access** | Accela | `aca.*`, `aca-prod.accela.com`, `*.accela.com` | "Accela Citizen Access" banner, `/apo/` path | `/portlets/cap/global/`, `/apo/`, `/v4/agency/` | `pt/adapters/accela_html.py` (REST v4 blocked anon, see `accela-rest-probe-findings.md`) |
| **AcclaimWeb** | Acclaim Imaging | `acclaimweb.com`, `acclaim-*.` | "Acclaim Web" header, `/AcclaimWeb/search/` | `/AcclaimWeb/search/SearchTypeName`, `/AcclaimWeb/Image/Thumbnail` | `pt/adapters/acclaimweb.py` |
| **OnCore Solutions (Landmark/Clerk)** | OnCore Solutions | `oncoreweb.*`, `*.oncoresolutions.com`, `*.landmarkweb.net`, `landmark.*` | "Landmark Web" branding, `/OnCoreWeb/` path | `/OnCoreWeb/SearchAvailable`, `/OnCoreWeb/Home` | `cd2/adapters/oncore_landmark.py` |
| **MGO-Connect** | MGO | `*.mgoconnect.com` | "MGO Connect" branding | varies per tenant, usually `/api/` | _(none yet)_ |
| **PermitTrax** | ePermit Solutions | `permittrax.*` | "PermitTrax" branding | `/PermitTrax/`, `/api/permit` | _(none yet)_ |
| **BITCO (BS&A style)** | Bitco Software | `bitco.net`, customer domains | "BITCO" footer | `/apps/`, per-customer variations | _(none yet)_ |
| **CityView** | Harris Computer | `*.cityview.com`, customer domains with `/CityViewPortal/` | "CityView Portal" branding | `/CityViewPortal/`, `/CityViewPortal/services/` | `pt/adapters/cityview.py` |
| **Municode Library (Codes)** | CivicPlus | `library.municode.com`, `api.municode.com` | `library.municode.com` URL, `api.municode.com` JSON | `api.municode.com/codes/{client_id}/nodes`, `IsUpdated`, `IsAmended`, `HasAmendedDescendant` flags | `cd2/adapters/municode.py` |
| **American Legal Publishing** | American Legal | `codelibrary.amlegal.com`, `*.amlegal.com` | "American Legal" footer | `/nxt/gateway.dll/`, `/api/` | _(none yet)_ |
| **Catalis GovOffice** | Catalis | customer domains with `/repository/designs/templates/GO_*` | classic ASP (`.asp`), `ASPSESSIONID*` cookies, `/vertical/sites/%7B<guid>%7D/uploads/` | `/index.asp?SEC=<GUID>`, `/index.asp?SEC=<GUID>&DE=<GUID>` | _(ad-hoc, see `davenport-fl.md`)_ |
