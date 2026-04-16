# Session G — Haines City eScribe Adapter Plan

**Date:** 2026-04-16
**Status:** Plan (Planner output). Supersedes `2026-04-16-session-g-haines-city-civicplus-calendar-plan.md` — that premise was falsified; Haines City publishes agendas via eScribe, not CivicPlus Calendar.
**Working directory:** `C:\Users\abrhi\Code\CountyData2`
**Scope:** one new platform adapter (`escribe`), one new jurisdiction YAML (`haines-city-cc.yaml`), one new test module, factory registration, one live-validation script.

Pivot rationale: today's live recon confirmed `pub-hainescity.escribemeetings.com` returns HTTP 200 with no auth, and exposes a clean JSON endpoint `POST /MeetingsCalendarView.aspx/GetCalendarMeetings` that returns the full meeting list with agenda-PDF `FileStream.ashx?DocumentId=<int>` URLs already attached per meeting. Scraping Meeting.aspx HTML is unnecessary for the happy path — the JSON API is the primary path, and Meeting.aspx is an optional fallback.

---

## 1. Recon summary (verified live 2026-04-16)

### Tenant
- **Subdomain:** `pub-hainescity.escribemeetings.com` — HTTP 200, no auth, no captcha, no Cloudflare challenge, no strict UA filtering.
- **Stack:** ASP.NET Web Forms + Syncfusion JS (EJ2 20.1.58) + jQuery 3.4.1 + FullCalendar 3.0.1 + Datadog RUM (Datadog doesn't gate access).
- **TLS:** valid cert (verify=True works fine on dev machines with a proper cert bundle; this repo's other scrapers don't pass `verify=False` and we won't either).
- **CDN/anti-bot:** none observed. Datadog RUM is passive client-side analytics, not a gate.

### Primary API (preferred scraping path)
- `POST https://pub-hainescity.escribemeetings.com/MeetingsCalendarView.aspx/GetCalendarMeetings`
- Headers: `Content-Type: application/json; charset=utf-8`
- Body: `{"calendarStartDate":"YYYY-MM-DD","calendarEndDate":"YYYY-MM-DD"}`
- Response: `{"d":[ {meeting}, ... ]}` — one JSON object per meeting across ALL bodies in the range.
- Inverted range returns `{"d":[]}` (HTTP 200). Empty range returns `{"d":[]}`. Single-day returns day-scoped results. Tested 180-day, 3-year, and single-day windows — all well-behaved.

#### Meeting object shape (verified)
```
{
  "ID": "9c192bb8-9f27-41cb-b7cc-359e7644fa25",   // UUID, stable meeting id
  "MeetingName": "City Commission Meeting",
  "MeetingType": "City Commission Meeting",       // AUTHORITATIVE body label
  "StartDate": "2026/02/05 19:00:00",             // YYYY/MM/DD HH:MM:SS (24h)
  "FormattedStart": "Thursday, February 05, 2026 @ 7:00 PM",
  "EndDate": "2026/02/05 20:30:00",
  "Description": "City Hall Commission Chambers<br/>620 E. Main Street, Haines City, FL 33844<br/>Phone: 863-421-9921     Web: hainescity.com",
  "Url": "https://pub-hainescity.escribemeetings.com/MeetingsCalendarView.aspx/Meeting?Id=9c192bb8-...",
  "Location": "City Hall Commission Chambers",
  "ShareUrl": "Sharing.aspx?u=https%3A%2F%2F...",
  "ClassName": "mt-26-26",
  "LanguageName": "English",
  "HasAgenda": true,
  "Sharing": true,
  "HasLiveVideo": false,
  "MeetingDocumentLink": [                        // array of per-meeting docs
    {"Type":"AgendaCover","Format":".pdf","Title":"Agenda Cover Page (PDF)","Url":"FileStream.ashx?DocumentId=27358", ...},
    {"Type":"Agenda","Format":".pdf","Title":"Agenda (PDF)","Url":"FileStream.ashx?DocumentId=27357", ...},
    {"Type":"Agenda","Format":"HTML","Title":"Agenda (HTML)","Url":"Meeting.aspx?Id=9c192bb8-...&Agenda=Agenda&lang=English", ...},
    {"Type":"PostMinutes","Format":".pdf","Title":"Minutes (PDF)","Url":"FileStream.ashx?DocumentId=22976", ...},
    {"Type":"PostAgenda","Format":"HTML","Title":"Post Agenda (HTML)","Url":"Meeting.aspx?Id=...&Agenda=PostAgenda&lang=English", ...},
    {"Type":"Video","Format":"Video","Title":"Video","Url":"./Players/ISIStandAlonePlayer.aspx?Id=...", ...}
  ]
}
```

- The doc we want is the one with `Type == "Agenda"` AND `Format == ".pdf"`. That is the packet-sized agenda PDF (13 MB for Feb 5 2026 CC — confirmed). `AgendaCover` is a thin cover sheet, `PostMinutes` is the Minutes PDF, `Video` is the ISI player, `HTML` entries point at Meeting.aspx viewers.
- Upcoming meetings without a posted agenda may omit the `Type=Agenda, Format=.pdf` entry (e.g. Red Light Camera 2026-05-20 has only 1 doc, no Agenda PDF). These must be silently skipped, matching ViewPublisher behavior.
- `FileStream.ashx?DocumentId=27357` returns `Content-Type: application/pdf`, `Content-Disposition: inline;filename="Agenda Package - CCRM_Feb05_2026.pdf"`, body starts with `%PDF-1.7`. Confirmed as a direct PDF stream, not an HTML wrapper.

### Body manifest (from the 3-year window 2024-01-01..2026-12-31, 240 meetings)
All `MeetingType` values observed on this tenant:
- **City Commission Meeting** (56) — in scope
- **City Commission Workshop** (28) — marginal; skip (workshops don't carry final votes)
- **City Commission Special Meeting** (2) — include (special meetings DO carry final votes); merge under CC
- **Planning Commission** (19) — in scope as a second body (per task scope: confirm and add)
- **Code Compliance** (32) — skip (BOA/ZBA-analog per 2026-04-16 rule)
- **Red Light Camera** (31) — skip (enforcement hearings, not land use)
- **CRA Meeting** (27), **CRA Workshop** (4), **CRA Citizens Advisory Council** (9) — skip for Session G; CRA meetings occasionally matter for tax-increment-financed development deals but aren't the primary entitlement path. Defer to a follow-up session.
- **Lakes Advisory Board** (16), **Parks and Recreation Board** (6), **Community Engagement** (4), **Canvassing Board** (4), **Bid Opening** (2) — skip.

**Decision for Session G:** ship `haines-city-cc.yaml` (City Commission + Special Meeting rollup) AND `haines-city-pc.yaml` (Planning Commission). Workshops are excluded by default; if the user later wants them they're a one-line YAML extension. The scraper's `body_filter` is a list of exact-match `MeetingType` strings — the YAML supplies whichever set the user wants.

### Landing-page (HTML) structure — fallback only
- `/` root lists 15 meeting-type accordions under `lvPastMeetingTypes` — the accordion **bodies are empty until an expand-click fires an AJAX `POST /MeetingsCalendarView.aspx/PastMeetings` with `{type: "City Commission Meeting", pageNumber: 1}`**. So the landing page itself is not a viable source of historical meetings without driving the expand AJAX — which is essentially the same endpoint surface.
- Upcoming meetings section is rendered by the calendar, which populates from `GetCalendarMeetings` (the same primary endpoint).
- Landing-page UUID enumeration from today's recon: `24f031d5-e06a-49e4-a520-f45fb402eefa`, `2822b6dc-30ce-4130-9ae1-7d174b2957c7`, `a6965b3e-59f2-4211-808e-7faadb524172`, `b196f3db-c354-4488-8c5f-7267c83926b6`, `e8f69d08-6029-4798-9221-64fbb3cbb0c9`, `fec20f91-2b99-4513-a8ab-bc4a1b5b0bf1` — these are the 6 hardcoded upcoming meetings inlined on the rendered landing page. The calendar JSON returns far more (54 in a 7-month window).
- **Conclusion:** the JSON endpoint is the primary path; there's no point parsing landing-page HTML as a separate surface.

### Meeting.aspx (agenda viewer)
- `GET https://pub-hainescity.escribemeetings.com/Meeting.aspx?Id=<uuid>&Agenda=Agenda&lang=English` returns a ~150KB HTML viewer.
- References to `FileStream.ashx?DocumentId=<numeric>` appear inline. For the Feb 5 2026 CC meeting the Meeting.aspx HTML referenced DocumentId=27356 — note: **this is a DIFFERENT DocumentId than the one in the JSON endpoint (27357)**. That's because Meeting.aspx links to a per-section agenda item, not the packet PDF. The JSON endpoint's `Type=Agenda, Format=.pdf` is the canonical packet — Meeting.aspx is not a substitute.
- No need to parse Meeting.aspx in the main path. Listed as optional fallback only.

### iCal / other feeds
- No iCal feed. No `Calendar.aspx?ics=1`, `/Api/Meetings`, `/Meetings.ashx`, `/Api/Public/Meetings` endpoints respond — only the ASMX-style `/MeetingsCalendarView.aspx/<Method>` JSON endpoints.
- The RSS/subscription feature is email-only (OTP subscription flow, not a public feed).

### Known quirks
1. Response `StartDate` is `YYYY/MM/DD HH:MM:SS` (slashes, not dashes). Parse with `%Y/%m/%d %H:%M:%S`.
2. `FileStream.ashx?DocumentId=...` URLs in `MeetingDocumentLink` are **relative** — join against `https://pub-hainescity.escribemeetings.com/` before use.
3. One meeting can have 2+ `Type=Agenda` entries with different `Format` values. Only `.pdf` format is the downloadable packet.
4. `MeetingType` is the authoritative body label. Do NOT rely on `MeetingName` (it's the "friendly" rendered name, usually equal to `MeetingType` but may drift).
5. For "Special Meeting" rollup: `City Commission Special Meeting` is a distinct `MeetingType` — if we want it folded under CC, the YAML lists both types in `body_filter`.
6. Tenant-subdomain pattern across eScribe customers: `pub-<slug>.escribemeetings.com`. The scraper must accept an arbitrary `tenant_host` so reuse for future eScribe tenants (many municipalities use this — Chelan County WA, several Canadian tenants, etc.) is just a new YAML.

---

## 2. Wave-grouped step plan

### Wave A — adapter module (Executor writes byte-for-byte)

**Step A.1** Create file `modules/commission/scrapers/escribe.py` with the verbatim content below.

```python
"""eSCRIBE (Diligent) meeting portal scraper.

Distinct from Granicus, CivicPlus, CivicClerk, Legistar, NovusAgenda,
and iCompass CivicWeb. eSCRIBE tenants are hosted at
``pub-<slug>.escribemeetings.com`` and expose an ASMX-style JSON
endpoint ``POST /MeetingsCalendarView.aspx/GetCalendarMeetings`` that
returns the full meeting list for a date range with per-meeting document
links already attached. Agenda packets are served as direct PDF streams
at ``FileStream.ashx?DocumentId=<numeric>`` relative to the tenant root.

Reference portal: https://pub-hainescity.escribemeetings.com/
"""

import json
import logging
import os
from datetime import datetime

import requests

from modules.commission.constants import (
    FILE_READ_CHUNK_SIZE,
    SCRAPE_DOWNLOAD_TIMEOUT,
    SCRAPE_SEARCH_TIMEOUT,
)
from modules.commission.scrapers.base import DocumentListing, PlatformScraper

logger = logging.getLogger("commission_radar.scrapers.escribe")

USER_AGENT = "CommissionRadar/1.0"

# eSCRIBE StartDate format: "YYYY/MM/DD HH:MM:SS" (24-hour).
ESCRIBE_DT_FMT = "%Y/%m/%d %H:%M:%S"


class EscribeScraper(PlatformScraper):
    """Scraper for eSCRIBE (Diligent) tenants.

    YAML config shape:
      platform: escribe
      tenant_host: pub-hainescity.escribemeetings.com
      body_filter:                       # list of exact MeetingType strings
        - "City Commission Meeting"
        - "City Commission Special Meeting"
      body_label: "City Commission"      # canonical title on DocumentListing
    """

    def fetch_listings(
        self, config: dict, start_date: str, end_date: str
    ) -> list[DocumentListing]:
        tenant_host = (config.get("tenant_host") or "").strip().rstrip("/")
        body_filter_raw = config.get("body_filter")
        body_label = (config.get("body_label") or "").strip()
        if not tenant_host or not body_filter_raw or not body_label:
            logger.warning(
                "eSCRIBE: missing tenant_host/body_filter/body_label "
                "(got host=%r filter=%r label=%r)",
                tenant_host, body_filter_raw, body_label,
            )
            return []
        # Accept either a list or a single string for body_filter.
        if isinstance(body_filter_raw, str):
            body_filter = [body_filter_raw.strip()]
        else:
            body_filter = [str(x).strip() for x in body_filter_raw if str(x).strip()]
        if not body_filter:
            logger.warning("eSCRIBE: body_filter is empty after normalization")
            return []

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning(
                "eSCRIBE: bad date range %r..%r", start_date, end_date
            )
            return []
        if start_dt > end_dt:
            return []

        url = f"https://{tenant_host}/MeetingsCalendarView.aspx/GetCalendarMeetings"
        payload = json.dumps(
            {"calendarStartDate": start_date, "calendarEndDate": end_date}
        )
        try:
            resp = requests.post(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/json; charset=utf-8",
                    "Accept": "application/json",
                },
                data=payload,
                timeout=SCRAPE_SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("eSCRIBE: fetch %s failed: %s", url, exc)
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.warning("eSCRIBE: %s returned non-JSON", url)
            return []

        items = data.get("d") if isinstance(data, dict) else None
        if not isinstance(items, list):
            logger.warning("eSCRIBE: unexpected JSON shape at %s", url)
            return []

        listings: list[DocumentListing] = []
        seen_ids: set[str] = set()
        allowed_types = {t for t in body_filter}
        for item in items:
            if not isinstance(item, dict):
                continue
            meeting_type = (item.get("MeetingType") or "").strip()
            if meeting_type not in allowed_types:
                continue
            date_iso = self._parse_start_date(item.get("StartDate"))
            if not date_iso:
                logger.debug(
                    "eSCRIBE: unparseable StartDate %r on meeting %r",
                    item.get("StartDate"), item.get("ID"),
                )
                continue
            try:
                row_dt = datetime.strptime(date_iso, "%Y-%m-%d")
            except ValueError:
                continue
            if row_dt < start_dt or row_dt > end_dt:
                continue

            agenda_doc = self._pick_agenda_pdf(item.get("MeetingDocumentLink"))
            if not agenda_doc:
                continue
            rel_url = (agenda_doc.get("Url") or "").strip()
            if not rel_url:
                continue
            pdf_url = f"https://{tenant_host}/{rel_url.lstrip('/')}"

            meeting_uuid = (item.get("ID") or "").strip()
            if not meeting_uuid or meeting_uuid in seen_ids:
                continue
            seen_ids.add(meeting_uuid)

            document_id = self._extract_document_id(rel_url) or meeting_uuid
            filename = f"Agenda_{date_iso}_{document_id}.pdf"

            listings.append(
                DocumentListing(
                    title=body_label,
                    url=pdf_url,
                    date_str=date_iso,
                    document_id=document_id,
                    document_type="agenda",
                    file_format="pdf",
                    filename=filename,
                )
            )
        return listings

    @staticmethod
    def _parse_start_date(raw) -> str | None:
        if not raw or not isinstance(raw, str):
            return None
        try:
            return datetime.strptime(raw.strip(), ESCRIBE_DT_FMT).strftime(
                "%Y-%m-%d"
            )
        except ValueError:
            # Tolerate dash-separated variants: "YYYY-MM-DD HH:MM:SS".
            try:
                return datetime.strptime(
                    raw.strip(), "%Y-%m-%d %H:%M:%S"
                ).strftime("%Y-%m-%d")
            except ValueError:
                return None

    @staticmethod
    def _pick_agenda_pdf(docs) -> dict | None:
        """Return the first doc dict where Type=='Agenda' AND Format=='.pdf'."""
        if not isinstance(docs, list):
            return None
        for d in docs:
            if not isinstance(d, dict):
                continue
            if (d.get("Type") or "").strip() != "Agenda":
                continue
            if (d.get("Format") or "").strip().lower() != ".pdf":
                continue
            return d
        return None

    @staticmethod
    def _extract_document_id(rel_url: str) -> str | None:
        """Pull the numeric DocumentId out of FileStream.ashx?DocumentId=<n>."""
        import re
        m = re.search(r"DocumentId=(\d+)", rel_url or "")
        return m.group(1) if m else None

    def download_document(self, listing: DocumentListing, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, listing.filename)
        resp = requests.get(
            listing.url,
            stream=True,
            timeout=SCRAPE_DOWNLOAD_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
        resp.raise_for_status()
        with open(filepath, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=FILE_READ_CHUNK_SIZE):
                if chunk:
                    fh.write(chunk)
        return filepath
```

### Wave B — factory registration

**Step B.1** Edit `modules/commission/scrapers/base.py`. In `PlatformScraper.for_platform`:

1. Add import (alphabetical — slots between `civicweb_icompass` and `granicus`):
```python
from modules.commission.scrapers.escribe import EscribeScraper
```
2. Add `"escribe": EscribeScraper,` into the `scrapers` dict, alphabetically between `"civicweb_icompass"` and `"granicus"`.

Resulting dict order:
```python
scrapers = {
    "civicclerk": CivicClerkScraper,
    "civicplus": CivicPlusScraper,
    "civicweb_icompass": CivicWebIcompassScraper,
    "escribe": EscribeScraper,
    "granicus": GranicusScraper,
    "granicus_viewpublisher": ViewPublisherScraper,
    "legistar": LegistarScraper,
    "manual": ManualScraper,
    "novusagenda": NovusAgendaScraper,
}
```

### Wave C — jurisdiction YAML (create new files, byte-for-byte)

**Step C.1** Create `modules/commission/config/jurisdictions/FL/haines-city-cc.yaml`:

```yaml
slug: haines-city-cc
name: "City of Haines City CC"
state: FL
county: Polk
municipality: "Haines City"
commission_type: city_commission

scraping:
  platform: escribe
  base_url: "https://pub-hainescity.escribemeetings.com/"
  tenant_host: "pub-hainescity.escribemeetings.com"
  body_filter:
    - "City Commission Meeting"
    - "City Commission Special Meeting"
  body_label: "City Commission"
  document_formats: [pdf]
  has_duplicate_page_bug: false

detection_patterns:
  header_keywords:
    - "CITY COMMISSION"
  require_also:
    - "HAINES CITY"
  header_zone: wide

extraction_notes:
  - "Generic Florida jurisdiction. Flag sparse items for review."
  - "eSCRIBE (Diligent) portal — agenda packets fetched via POST /MeetingsCalendarView.aspx/GetCalendarMeetings JSON endpoint; PDFs stream from FileStream.ashx?DocumentId=<numeric>."
  - "City Commission Special Meetings rolled under CC. Workshops excluded by default."
```

**Step C.2** Create `modules/commission/config/jurisdictions/FL/haines-city-pc.yaml`:

```yaml
slug: haines-city-pc
name: "City of Haines City PC"
state: FL
county: Polk
municipality: "Haines City"
commission_type: planning_commission

scraping:
  platform: escribe
  base_url: "https://pub-hainescity.escribemeetings.com/"
  tenant_host: "pub-hainescity.escribemeetings.com"
  body_filter:
    - "Planning Commission"
  body_label: "Planning Commission"
  document_formats: [pdf]
  has_duplicate_page_bug: false

detection_patterns:
  header_keywords:
    - "PLANNING COMMISSION"
  require_also:
    - "HAINES CITY"
  header_zone: wide

extraction_notes:
  - "Generic Florida jurisdiction. Flag sparse items for review."
  - "eSCRIBE (Diligent) portal — same tenant as haines-city-cc; selector is MeetingType == 'Planning Commission'."
```

Keywords will auto-merge from `_florida-defaults.yaml` at load time (confirmed by reading `config_loader._apply_defaults`).

### Wave D — unit tests

**Step D.1** Create `tests/test_escribe_scraper.py` following the Session F / ViewPublisher shape. See the Test manifest section below for the full list; Executor writes the file following that exact structure, with module-top fixtures and `unittest.TestCase` classes grouped by concern. All tests patch `modules.commission.scrapers.escribe.requests.post` or `.requests.get` on the adapter module namespace.

### Wave E — local verification

**Step E.1** Run the unit suite:
```bash
cd C:/Users/abrhi/Code/CountyData2
python -m pytest tests/test_escribe_scraper.py -v
```
Expected: 100% green, ~22 tests.

**Step E.2** Run the full commission suite to catch regressions:
```bash
python -m pytest tests/test_escribe_scraper.py tests/test_civicweb_icompass_scraper.py tests/test_granicus_viewpublisher_scraper.py tests/test_granicus_scraper.py tests/test_civicplus_scraper.py tests/test_civicclerk_scraper.py tests/test_legistar_scraper.py tests/test_novusagenda_scraper.py tests/test_manual_scraper.py -v
```

**Step E.3** Full-repo sanity:
```bash
python -m pytest --quiet
```
Full suite size: 546 currently → ≥566 with new tests (Session F baseline plus ≥20 new).

### Wave F — live validation

**Step F.1** Create `tmp/verify_haines_city_cc.py` (see Section 4 below).
**Step F.2** Run it. Exit non-zero if <3 agenda PDFs returned.
**Step F.3** If PC config is also desired, re-run with `haines-city-pc` slug (PC meets less frequently so only require ≥2 over 180 days).

---

## 3. Test manifest — `tests/test_escribe_scraper.py`

Total target: **22 tests** across 10 categories. All tests patch the `requests.post` symbol on the `modules.commission.scrapers.escribe` module namespace; the one download test patches `requests.get` on the same namespace. No live network.

### Fixture constants (module top, triple-quoted / literal JSON strings)
Declare Python-literal JSON dicts that match the verified live JSON shape. Pattern:

- `JSON_MULTI_BODY` — one response `{"d":[...]}` containing 4 meetings:
  - 1 City Commission Meeting (2026-02-05, Agenda PDF + Cover + HTML + Minutes)
  - 1 City Commission Special Meeting (2026-03-10, Agenda PDF + HTML)
  - 1 Planning Commission (2026-03-12, Agenda PDF + Cover + HTML)
  - 1 Code Compliance (2026-02-15, Agenda PDF) — must be filtered out under CC body_filter
- `JSON_NO_AGENDA_PDF` — 1 meeting with `MeetingDocumentLink=[{"Type":"Agenda","Format":"HTML",...}]` only (no `.pdf` format). Must yield zero listings.
- `JSON_EMPTY_DOCS` — 1 CC meeting with `MeetingDocumentLink: []`. Zero listings.
- `JSON_NULL_DOCS` — 1 CC meeting with `MeetingDocumentLink: None`. Zero listings.
- `JSON_DUPLICATE_UUID` — 2 CC entries with identical `ID` (defensive: eSCRIBE shouldn't do this, but we must dedup by UUID).
- `JSON_BAD_DATE` — 1 CC meeting with `StartDate` = "not a date".
- `JSON_DASH_DATE` — 1 CC meeting with `StartDate` = `"2026-02-05 19:00:00"` (dash-separated) — must still parse.
- `JSON_EMPTY_D` — `{"d":[]}`. Zero listings.
- `JSON_BAD_SHAPE` — `{"d":"not a list"}`. Zero listings + warning.
- `JSON_MISSING_D` — `{}`. Zero listings.

### Test classes

**1. `FactoryRegistrationTests` (2 tests)**
- `test_factory_returns_escribe_scraper` — `PlatformScraper.for_platform("escribe")` returns an `EscribeScraper`.
- `test_factory_raises_for_unknown_platform` — unknown key → `ValueError`.

**2. `MissingConfigTests` (5 tests)**
- `test_missing_tenant_host_returns_empty` — pop `tenant_host`, expect `[]`.
- `test_missing_body_filter_returns_empty` — pop `body_filter`, expect `[]`.
- `test_missing_body_label_returns_empty` — pop `body_label`, expect `[]`.
- `test_empty_body_filter_list_returns_empty` — `body_filter: []`, expect `[]`.
- `test_bad_date_range_returns_empty` — `start_date="nope"`, expect `[]`, no HTTP call made.

Optional 6th: `test_inverted_date_range_returns_empty_without_network` — assert `requests.post` was not called when `start > end`.

**3. `BodyFilterTests` (2 tests)**
- `test_cc_filter_returns_only_cc_rows` — with `JSON_MULTI_BODY` and `body_filter=["City Commission Meeting","City Commission Special Meeting"]`, expect 2 listings (CC + Special), no PC, no Code Compliance.
- `test_pc_filter_excludes_cc` — with `JSON_MULTI_BODY` and `body_filter=["Planning Commission"]`, expect exactly 1 listing (PC), no CC leakage.

**4. `DocumentSelectionTests` (3 tests)**
- `test_only_agenda_pdf_doc_selected` — the returned listing's `url` resolves to the `Type=Agenda, Format=.pdf` doc, not the Cover, HTML, or Minutes doc.
- `test_no_agenda_pdf_returns_no_listing` — `JSON_NO_AGENDA_PDF` → `[]`.
- `test_null_or_empty_docs_list_skipped` — `JSON_EMPTY_DOCS` and `JSON_NULL_DOCS` both → `[]`. (One combined test with two asserts is fine; or split into two.)

**5. `DateParsingTests` (2 tests)**
- `test_slash_format_parses` — `StartDate="2026/02/05 19:00:00"` → `date_str="2026-02-05"`.
- `test_dash_format_parses_defensively` — `StartDate="2026-02-05 19:00:00"` → `date_str="2026-02-05"`.

One additional test merged into `DocumentSelectionTests` or a sibling:
- `test_bad_start_date_skipped` — `JSON_BAD_DATE` → `[]`.

**6. `DateWindowingTests` (2 tests)**
- `test_rows_before_start_excluded` — with `JSON_MULTI_BODY`, call `fetch_listings(cfg, "2026-03-01", "2026-12-31")`. Expect 1 listing (the Special Meeting 2026-03-10), NOT the 2026-02-05 CC.
- `test_rows_after_end_excluded` — with `JSON_MULTI_BODY`, call `fetch_listings(cfg, "2026-01-01", "2026-02-28")`. Expect 1 listing (2026-02-05 CC), NOT 2026-03-10.

**7. `DocumentListingFieldTests` (1 test)**
- `test_listing_fields_populated` — for the CC-only 2026-02-05 row, assert:
  - `title == "City Commission"` (the body_label, not MeetingType)
  - `document_type == "agenda"`
  - `file_format == "pdf"`
  - `date_str == "2026-02-05"`
  - `url == "https://pub-hainescity.escribemeetings.com/FileStream.ashx?DocumentId=27357"`
  - `document_id == "27357"` (extracted from URL, not the UUID)
  - `filename == "Agenda_2026-02-05_27357.pdf"`

**8. `DeduplicationTests` (1 test)**
- `test_duplicate_meeting_uuids_collapsed` — `JSON_DUPLICATE_UUID` → exactly 1 listing.

**9. `NetworkFailureTests` (2 tests)**
- `test_network_exception_returns_empty` — mock `requests.post` to raise `requests.RequestException`. Expect `[]`.
- `test_bad_json_shape_returns_empty` — `JSON_BAD_SHAPE` and `JSON_MISSING_D` both yield `[]`. (Two asserts in one test, or split; planner suggests split for symmetry.)

**10. `DownloadDocumentTests` (2 tests)**
- `test_download_writes_file` — patched `requests.get` returns PDF bytes; assert file on disk matches `listing.filename` and content round-trips.
- `test_download_creates_nested_output_dir` — `output_dir` points into a not-yet-existent nested dir; assert `makedirs` behavior.

### Helper shape

```python
def _mock_post_response(d=None, status_code=200, raise_for_status=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value={"d": d if d is not None else []})
    if raise_for_status is None:
        resp.raise_for_status = MagicMock()
    else:
        resp.raise_for_status = raise_for_status
    return resp


def _cfg(
    tenant_host="pub-hainescity.escribemeetings.com",
    body_filter=("City Commission Meeting", "City Commission Special Meeting"),
    body_label="City Commission",
):
    return {
        "platform": "escribe",
        "tenant_host": tenant_host,
        "body_filter": list(body_filter),
        "body_label": body_label,
    }
```

### Patch target
`@patch("modules.commission.scrapers.escribe.requests.post")` for fetch tests; `@patch("modules.commission.scrapers.escribe.requests.get")` for the download test.

---

## 4. Live-validation script

**File:** `tmp/verify_haines_city_cc.py`

```python
"""Live validation for the Haines City CC eSCRIBE adapter.

Run from repo root:
    python tmp/verify_haines_city_cc.py

Exits non-zero if fewer than 3 agenda PDFs were fetched over a 180-day
window ending today, or if the YAML fails to load.
"""

import sys
from datetime import date, timedelta

from modules.commission.config_loader import load_jurisdiction_config
from modules.commission.scrapers.base import PlatformScraper


def main() -> int:
    slug = "haines-city-cc"
    cfg = load_jurisdiction_config(slug)
    if cfg is None:
        print(f"FAIL: no jurisdiction config found for slug={slug!r}", file=sys.stderr)
        return 2

    scraping = cfg.get("scraping") or {}
    platform = scraping.get("platform")
    if platform != "escribe":
        print(
            f"FAIL: expected platform='escribe', got {platform!r}",
            file=sys.stderr,
        )
        return 3

    end = date.today()
    start = end - timedelta(days=180)
    start_s = start.strftime("%Y-%m-%d")
    end_s = end.strftime("%Y-%m-%d")

    scraper = PlatformScraper.for_platform(platform)
    listings = scraper.fetch_listings(scraping, start_s, end_s)

    print(f"slug={slug}")
    print(f"window={start_s}..{end_s}")
    print(f"total_listings={len(listings)}")
    for l in listings[:10]:
        print(
            f"  {l.date_str} | {l.document_id:>10s} | {l.title} | {l.filename} | {l.url}"
        )

    if len(listings) == 0:
        print("FAIL: zero listings", file=sys.stderr)
        return 1
    if len(listings) < 3:
        print(
            f"FAIL: expected >=3 listings over 180 days, got {len(listings)}",
            file=sys.stderr,
        )
        return 4

    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**Expected behavior on today's data:** 10 CC agenda PDFs (counted today during recon) → exit 0.

**Optional companion script** (only if Executor wants a quick PC sanity check): `tmp/verify_haines_city_pc.py` identical but with `slug = "haines-city-pc"` and `< 2` as the failure threshold (PC meets roughly monthly — 6 meetings in 180 days).

---

## 5. Risks / open questions (escalate, don't improvise)

1. **JSON endpoint shape drift.** eSCRIBE could update the ASMX endpoint to e.g. REST-with-query-string or change the `{"d":[...]}` envelope to a flat list. Detection: integration failure on next quarterly release. Mitigation: the scraper's `resp.json()` + `isinstance(data,dict)` + `isinstance(items,list)` guards return `[]` gracefully; log shows "unexpected JSON shape". **Escalate** to a new scraper version rather than papering over with heuristics.

2. **Landing-page/panel fallback not implemented.** If the JSON endpoint is ever blocked or rate-limited per tenant, we have no fallback. The panel AJAX `/MeetingsCalendarView.aspx/PastMeetings` is the obvious next surface but requires per-type pagination and HTML parsing. **Do not implement in Session G** — escalate when a tenant breaks.

3. **`MeetingType` drift across tenants.** Different eSCRIBE customers may use different `MeetingType` strings ("City Council" vs "Council Meeting" vs "Regular Meeting"). The scraper's `body_filter` is exact-match by design — each new tenant needs a per-YAML audit. **Escalate** on future tenant onboarding to run a one-shot probe before authoring the YAML.

4. **`FileStream.ashx` returning HTML wrapper instead of PDF.** eSCRIBE could (theoretically) start serving an interstitial page for large packets. Confirmed today that Feb 5 2026 CC returns `%PDF-1.7` directly; the Executor's verification script downloads one real PDF to catch this at commit time. If it breaks: the scraper still emits a listing but `download_document` would write HTML bytes to `.pdf`. **Mitigation:** Session-G scope does NOT add a Content-Type sniff before write — that's a whole-pipeline concern worth a separate session. Flag in session notes.

5. **UUID format drift.** The `ID` field is currently a canonical lowercase 36-char UUID. If a tenant serves uppercase or 32-char no-dash format, the dedup set still works (exact-match), but future cross-tenant comparisons may break. Not a Session G blocker.

6. **Tenant subdomain variants across eSCRIBE.** `pub-<slug>.escribemeetings.com` is the dominant pattern; a handful of older tenants use `www.<slug>.escribemeetings.com` or `<slug>.escribemeetings.com` (no `pub-` prefix). The adapter takes an arbitrary `tenant_host` in YAML so that's already handled — but the Planner has not verified the JSON endpoint lives at the same `/MeetingsCalendarView.aspx/GetCalendarMeetings` path on non-`pub-` variants. **Escalate** at next non-Haines-City tenant onboarding.

7. **CC Special Meetings vs Workshops.** Workshops are currently excluded. If the user later decides Workshops matter, add `"City Commission Workshop"` to the YAML `body_filter`. **Open question for the user:** confirm workshops are out of scope. Defaulting to out.

8. **Minutes extraction not in scope.** `Type=PostMinutes, Format=.pdf` is visible on the JSON endpoint and could be harvested into `document_type="minutes"` listings for free. Session G ships agenda-only parity with other scrapers. **Escalate** if the pipeline needs a minutes-listing feature — it's a 15-line delta.

9. **Meeting.aspx HTML fallback not used.** The JSON endpoint's `Type=Agenda, Format=.pdf` is the canonical path; Meeting.aspx references a different `DocumentId` (per-agenda-item, not packet). The scraper intentionally never parses Meeting.aspx. Flag: if a future tenant serves the JSON but with an empty `MeetingDocumentLink` array because packets are only linked from Meeting.aspx, we'd need a two-pass design. Not observed in Haines City.

10. **Planning Commission inclusion decision.** Session G ships both `haines-city-cc.yaml` and `haines-city-pc.yaml` based on recon confirming PC is on the same tenant with 10 meetings in the last 2 years. If the user objects to auto-shipping PC, it's a one-file revert. Planning decision: **ship both** — the additional file has zero marginal engineering cost because the adapter is body-filter-driven.

---

## Appendix — reference log of recon commands

All run on 2026-04-16 against `https://pub-hainescity.escribemeetings.com/`:

1. `GET /` — HTTP 200, 355 KB HTML, Syncfusion/ASP.NET.
2. `POST /MeetingsCalendarView.aspx/GetCalendarMeetings` with `{"calendarStartDate":"2025-10-18","calendarEndDate":"2026-04-16"}` → 48 items across all bodies, 10 CC agenda PDFs.
3. `GET /FileStream.ashx?DocumentId=27357` → HTTP 200, Content-Type `application/pdf`, Content-Disposition `inline;filename="Agenda Package - CCRM_Feb05_2026.pdf"`, first 8 bytes `%PDF-1.7`, 13.9 MB body.
4. `GET /Meeting.aspx?Id=9c192bb8-9f27-41cb-b7cc-359e7644fa25&Agenda=Agenda&lang=English` → HTTP 200, 150 KB HTML, references `FileStream.ashx?DocumentId=27356` (different from the packet ID — per-section, not canonical).
5. `POST /MeetingsCalendarView.aspx/GetCalendarMeetings` inverted range → HTTP 200, `{"d":[]}`.
6. `POST /MeetingsCalendarView.aspx/GetCalendarMeetings` far-future range → HTTP 200, `{"d":[]}`.

Full body manifest across the 3-year recon window:
`City Commission Meeting (56), Code Compliance (32), Red Light Camera (31), City Commission Workshop (28), CRA Meeting (27), Planning Commission (19), Lakes Advisory Board (16), CRA Citizens Advisory Council (9), Parks and Recreation Board (6), Community Engagement (4), CRA Workshop (4), Canvassing Board (4), Bid Opening (2), City Commission Special Meeting (2)`.

End of plan.
