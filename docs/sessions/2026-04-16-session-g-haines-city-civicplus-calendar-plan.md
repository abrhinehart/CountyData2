# Session G Planner Output — Haines City CivicPlus Calendar Adapter

**Date:** 2026-04-16
**Planner role:** research + plan only (no code written, no files edited outside this plan doc)
**Task (verbatim from caller):**

> Enact Haines City CivicPlus Calendar adapter. Haines City's AgendaCenter is empty (discovered Session C, commit 3a2f9d5) — they publish agendas through the CivicPlus Calendar product, which modules/commission/scrapers/civicplus.py does not consume. Build a new civicplus_calendar platform scraper under modules/commission/scrapers/, a Haines City CC YAML config under modules/commission/config/jurisdictions/FL/, full unit tests, scraper factory registration, and a live-validation run. Follow the shape + rigor of Session D's Granicus ViewPublisher adapter and Session F's iCompass CivicWeb adapter. Haines City has one in-scope body — the City Commission. If a Planning Board exists and publishes through Calendar, include it too; otherwise, note and skip. Respect the 2026-04-16 BOA/ZBA skip rule. Recon first via curl/requests from https://www.hainescity.com/ and its CivicPlus calendar URL — no Selenium unless forced. Keep to Python stdlib + requests + beautifulsoup4 (already deps). Full suite must pass (546 → higher with new tests, no regressions). Session label: Session G.

---

## 0. TL;DR — ESCALATE BEFORE EXECUTING

**The stated premise is wrong.** Haines City does *not* publish City Commission agendas through the CivicPlus Calendar product. Live recon (documented below) shows:

1. **AgendaCenter is empty** — confirmed (no category links on `/AgendaCenter`, only `/Search/` and `/UpdateCategoryList` helper endpoints). Matches Session C finding.
2. **Calendar has zero City Commission events, ever.** The Calendar category `catID=35` ("Elected Officials") where CC meetings would live returns **0 events** over the full forward/backward window exposed by the iCal feed. Every Calendar category was probed (see §1.3).
3. **Calendar events carry no downloadable agenda documents.** Across 32/22/10/37/15/69 events in the six populated categories (14, 23, 27, 28, 32, 34), the iCal feed has **zero `ATTACH:` lines**, and spot-checks of event-detail HTML pages (EIDs 5607, 5611, 5615, 5940, 5944, 5947, 6652, 6657) show **empty `<ul itemprop="documents" class="documentsList">`** elements with zero PDF links, zero DocumentCenter/View links, and zero AgendaCenter/ViewFile links.
4. **DocumentCenter is a React SPA shell** — `/DocumentCenter`, `/DocumentCenter/Index/1`, `/DocumentCenterII`, `/documentcenter.aspx`, `/DocumentCenter/Home/GetFoldersAndDocuments?folderID=0`, and similar candidates all return the Azure AppInsights SPA shell. No stable HTML fallback, no discovered anonymous JSON endpoint, no index. Would require Selenium + network interception to reverse-engineer — out of scope per task constraints.
5. **The in-scope Planning Commission body** *does* appear in the Calendar (22 unique meetings across catIDs 14+28+34, all future-dated from 2026-05-11 onward, duplicated across categories). But none have agendas attached. An adapter that returns meeting-schedule entries with no downloadable PDFs produces rows that the downstream CR pipeline cannot enrich.

**Planner recommendation:** Escalate this task to the user. Do **not** let the Executor synthesize an adapter against an empty data surface. The right next move is one of:

- **(A) Scope-redirect Haines City to the DocumentCenter SPA** (new adapter family, requires Selenium or reverse-engineering the React state hydration — separate task, not Session G).
- **(B) Defer Haines City entirely** and re-schedule when the city begins attaching agendas to Calendar events (they have the `<ul itemprop="documents">` hook but it's unpopulated).
- **(C) Contact the City Clerk** (listed via Notify-Me list 252 on the site) to ask where agendas actually live; they may be email-distribution-only.

If after escalation the user insists on a build, §4 below gives the minimum-viable CivicPlus Calendar adapter plan that would at least enable *other* FL cities publishing via Calendar-with-attachments to be added later. It includes a Haines City config stub annotated as "calendar-only-no-agendas" so the jurisdiction is registered but yields zero listings until the city starts attaching documents.

---

## 1. Recon Summary

### 1.1 URLs probed (all User-Agent `CommissionRadar/1.0`, plain GET, no JS)

| URL | Status | Notes |
|-----|--------|-------|
| `https://www.hainescity.com/` | 200 | CivicPlus skin, home page. Only `Calendar.aspx?EID=…` links, no Commission-agenda links. |
| `https://www.hainescity.com/AgendaCenter` | 200 | **Empty** — only `Search/?term=` and `UpdateCategoryList` endpoints. No category cards. Confirms Session C. |
| `https://www.hainescity.com/Calendar.aspx` | 200 | Calendar day-view. CID dropdown only shows "Library (24)"; the other CIDs in the page (14, 15, 23) trace back to QuickLinks, not Calendar categories. |
| `https://www.hainescity.com/Calendar.aspx?listtype=cat&calType=0&Keywords=&startDate=01%2F01%2F2026&enddate=12%2F31%2F2026` | 200 (476 KB) | List-view. Unique event titles: Planning Commission Meeting, Planning Commission, Lakes Advisory Board, plus library programs and seasonal events. **No "City Commission" anywhere.** |
| `https://www.hainescity.com/225/City-Commission` | 200 | CC landing page. Text says "Please check the calendar on the homepage" but page has no agenda links. Only `/DocumentCenter` sidebar link. |
| `https://www.hainescity.com/DocumentCenter` | 200 | React SPA shell; no server-rendered folder tree. |
| `https://www.hainescity.com/DocumentCenter/Index/1`, `/DocumentCenterII`, `/documentcenter.aspx`, `/DocumentCenter/Home/GetFoldersAndDocuments?folderID=0`, `/documentcenter/api/folder/children?folderId=0` | 200 (all) | All return the same SPA shell. No API discovered. |
| `https://www.hainescity.com/iCalendar.aspx` | 200 (HTML, 93 KB) | UI redirect page, not the feed. |
| `https://www.hainescity.com/common/modules/iCalendar/iCalendar.aspx?catID=<N>&feed=calendar` | 200 (text/calendar) | **This is the actual iCal feed.** Structured VCALENDAR output with VEVENTs. |
| `https://www.hainescity.com/Calendar.aspx?EID=<id>` | 200 | Event-detail page. Has `<ul itemprop="documents" class="documentsList">` which is **empty on every sampled event**. |

### 1.2 AgendaCenter confirmed empty (reaffirms Session C / commit `3a2f9d5`)

Full link dump of `/AgendaCenter` HTML:

```
AgendaCenter/Search/?term=
AgendaCenter/UpdateCategoryList
```

No category tiles, no `/AgendaCenter/ViewFile/…` hrefs. There is nothing for `modules/commission/scrapers/civicplus.py` to consume. This is why Session C deferred Haines City.

### 1.3 CivicPlus Calendar category manifest (from the event-detail checkbox list)

| CalendarID (catID) | Label | iCal events | ATTACH lines | BOA/ZBA-filtered? |
|---|---|---|---|---|
| 14 | Main Calendar | 32 | 0 | n/a — Planning Commission only |
| 23 | Library | 22 | 0 | out of scope (library programs) |
| 25 | Parks & Recreation | 0 | 0 | out of scope |
| 27 | Special Events | 10 | 0 | out of scope (parades/5Ks) |
| 28 | Development Services | 37 | 0 | **Planning Commission events; IN SCOPE** |
| 29 | Fire | 0 | 0 | out of scope |
| 30 | Police | 0 | 0 | out of scope |
| 32 | Public Works | 15 | 0 | Lakes Advisory Board — advisory only, out of scope |
| 33 | Utilities | 0 | 0 | out of scope |
| 34 | Public Meetings | 69 | 0 | **Planning Commission events (dupes of 14+28); IN SCOPE** |
| 35 | **Elected Officials** | **0** | 0 | **Where CC would live — IT IS EMPTY** |
| 38 | Planning Commission Meeting-Cancelation | 0 | 0 | cancellation-only stream, empty |
| 39 | Purchasing | 0 | 0 | out of scope |

Observed: event 5611 appears in `catID=14`, `catID=28`, and `catID=34`. Categories are many-to-one with events. A dedup pass by EID is mandatory if multiple categories are used.

**BOA/ZBA skip rule:** Haines City has no BOA/ZBA presence in the Calendar manifest. Nothing to filter. Rule satisfied by absence.

### 1.4 iCal feed shape (the only structured data surface)

Example VEVENT from `catID=14`:

```
BEGIN:VEVENT
DESCRIPTION: https://www.hainescity.com/calendar.aspx?EID=5642
DTEND;TZID=America/New_York:20281211T170000
DTSTAMP;TZID=America/New_York:20240822T161158
DTSTART;TZID=America/New_York:20281211T160000
LAST-MODIFIED;TZID=America/New_York:20240822T161158
LOCATION:City Hall - 620 E. Main St  Haines City FL 33844
SEQUENCE:0
SUMMARY:Planning Commission Meeting
UID:5642
URL:/common/modules/iCalendar/iCalendar.aspx?feed=calendar&catID=14
END:VEVENT
```

Key fields observed: `SUMMARY`, `DTSTART;TZID=America/New_York:YYYYMMDDTHHMMSS`, `UID` (= EID), `DESCRIPTION` carries the event-detail URL.

Key fields NOT observed anywhere in any catID: `ATTACH;FMTTYPE=application/pdf;VALUE=BINARY:…`, `ATTACH:https://…pdf`, `X-ALT-DESC;FMTTYPE=text/html:…<a href=…pdf>…`. The feed is schedule-only.

### 1.5 Events in the 180-day live-validation window (2026-04-16 → 2026-10-13), catID=34

| Date | EID | Summary |
|---|---|---|
| 2026-05-11 | 5611 | Planning Commission Meeting |
| 2026-05-11 | 5940 | Planning Commission |
| 2026-06-08 | 5612 | Planning Commission Meeting |
| 2026-06-08 | 5941 | Planning Commission |
| 2026-07-13 | 5613 | Planning Commission Meeting |
| 2026-07-13 | 5942 | Planning Commission |
| 2026-08-10 | 5614 | Planning Commission Meeting |
| 2026-08-10 | 5943 | Planning Commission |
| 2026-09-14 | 5615 | Planning Commission Meeting |
| 2026-09-14 | 5944 | Planning Commission |
| 2026-10-12 | 5616 | Planning Commission Meeting |
| 2026-10-12 | 5945 | Planning Commission |

12 VEVENTs → 6 unique meeting dates (each double-indexed by title variant). **Zero have agenda PDFs.**

### 1.6 Why iCal is the right surface *if* we build anything

- **iCal >> HTML** — structured, stable RFC-5545 fields, no HTML scraping heuristics needed, catID filtering is server-side, NBSP/encoding noise is avoided.
- The iCal `ATTACH` line IS the CivicPlus Calendar mechanism for agenda attachment when a tenant uses it. Haines City does not.
- HTML event-detail pages carry `<ul itemprop="documents" class="documentsList">` which is populated for tenants who attach documents; again, Haines City does not.
- A CivicPlus Calendar adapter that consumes iCal `ATTACH` lines (primary) and falls back to scraping `<ul itemprop="documents">` on event-detail HTML (secondary) is the correct shape. It will yield zero rows for Haines City and non-zero rows for any other FL municipality that publishes this way — which is the reusable long-term value.

---

## 2. Body Manifest (with BOA/ZBA filtered out)

| Body | In-scope? | Data surface | Status |
|---|---|---|---|
| Haines City **City Commission** | yes (intended target) | none discovered | **BLOCKED** — not in Calendar, not in AgendaCenter, DocumentCenter is an SPA |
| Haines City **Planning Commission** | yes | Calendar catID=14/28/34 | events exist (6 unique in 180 days), **zero agenda attachments** |
| Haines City BOA/ZBA | no (2026-04-16 skip rule) | n/a | none present anyway |
| Lakes Advisory Board, library programs, etc. | no | Calendar catID=23/27/32 | out of scope |

---

## 3. Decision Tree for the Parent Agent (the caller)

**Gate 1:** Do you want to honor the "empty results → escalate before Executor" rule from the planner prompt?

- **Yes → ESCALATE.** Return this plan doc to the user. Do not proceed to Executor. See §0 options A/B/C.
- **No, build the reusable adapter anyway** → proceed to §4, which ships a `civicplus_calendar` scraper that correctly handles Haines City's empty state AND sets up future FL cities that do attach Calendar agendas. Live validation will threshold at `>=0` for Haines City (documented empty), not `>=3` — the standard threshold is wrong for this jurisdiction.

---

## 4. Fallback Build Plan (only if parent overrides the escalation)

If the parent agent wants the reusable adapter built despite Haines City being empty, here's the mechanical plan. Waves are in dependency order.

### Wave 1 — Scraper skeleton

**File:** `modules/commission/scrapers/civicplus_calendar.py` (NEW)

Shape analogous to `modules/commission/scrapers/granicus_viewpublisher.py` and `modules/commission/scrapers/civicweb_icompass.py`. Primary source is the iCal feed; HTML event-detail fallback only if iCal has no `ATTACH` for a VEVENT.

Module docstring must state: "Distinct from `civicplus.py` which consumes AgendaCenter `/AgendaCenter/Search/` pages. This consumes the CivicPlus Calendar iCal feed at `/common/modules/iCalendar/iCalendar.aspx?catID=<N>&feed=calendar`. Reference tenant: hainescity.com (currently publishes schedule-only, no attachments)."

Config shape (YAML):

```yaml
scraping:
  platform: civicplus_calendar
  base_url: "https://www.hainescity.com"          # site root, no trailing slash
  category_ids: [34]                               # list of catIDs to union
  body_filter: "Planning Commission"               # case-insensitive substring against SUMMARY
  # optional: document_formats: [pdf]
```

Public class:

```python
class CivicPlusCalendarScraper(PlatformScraper):
    ICAL_PATH = "/common/modules/iCalendar/iCalendar.aspx"

    def fetch_listings(self, config: dict, start_date: str, end_date: str) -> list[DocumentListing]:
        base_url = (config.get("base_url") or "").rstrip("/")
        category_ids = config.get("category_ids") or []
        body_filter = (config.get("body_filter") or "").strip().lower()
        if not base_url or not category_ids or not body_filter:
            logger.warning("CivicPlusCalendar: missing base_url/category_ids/body_filter")
            return []
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")
        except (TypeError, ValueError):
            logger.warning("CivicPlusCalendar: bad date range %r..%r", start_date, end_date)
            return []
        if start_dt > end_dt:
            return []

        listings: list[DocumentListing] = []
        seen_uids: set[str] = set()
        for cid in category_ids:
            ics_text = self._fetch_ics(base_url, cid)
            if ics_text is None:
                continue
            for vevent in self._iter_vevents(ics_text):
                listing = self._vevent_to_listing(vevent, base_url, body_filter,
                                                  start_dt, end_dt, seen_uids)
                if listing:
                    listings.append(listing)
        return listings
```

Helper methods (all static/pure for testability):

- `_fetch_ics(base_url, cid)` → `str | None` — GETs `{base_url}/common/modules/iCalendar/iCalendar.aspx?catID={cid}&feed=calendar` with `User-Agent: CommissionRadar/1.0`, timeout=`SCRAPE_SEARCH_TIMEOUT`. Returns response text on 200, `None` on RequestException.
- `_iter_vevents(ics_text)` → generator yielding `dict[str, str]` with unfolded lines (RFC-5545 line unfolding: CRLF followed by space/tab joins the continuation). Uses regex `BEGIN:VEVENT([\s\S]*?)END:VEVENT` plus `^([A-Z-]+)(;[^:]+)?:(.*)$` line parse.
- `_vevent_to_listing(vevent, base_url, body_filter, start_dt, end_dt, seen_uids)` → builds a `DocumentListing` iff:
  - `SUMMARY` contains `body_filter` (case-insensitive)
  - `DTSTART` parses to a date inside `[start_dt, end_dt]`
  - `UID` is not in `seen_uids` (dedup across categories)
  - at least one `ATTACH` line contains a `.pdf` URL **OR** an HTML fallback scrape of `{base_url}/Calendar.aspx?EID={UID}` finds a `<ul itemprop="documents">` with a `.pdf` href
  - if no PDF is discoverable, skip the event (do not synthesize a schedule-only row)
- `_parse_dtstart(value)` → `datetime` — handles `DTSTART;TZID=America/New_York:YYYYMMDDTHHMMSS` and bare `DTSTART:YYYYMMDDTHHMMSS` and `DTSTART;VALUE=DATE:YYYYMMDD`.
- `_extract_pdf_from_attach(attach_values: list[str]) -> str | None` — prefers lines matching `/\.pdf(\?|$)/i`; handles `ATTACH;FMTTYPE=application/pdf:https://…` shape.
- `_scrape_event_detail_pdf(base_url, eid) -> str | None` — second-pass HTML fetch of event-detail page; returns first `.pdf` href inside `ul.documentsList`. Used only when iCal `ATTACH` absent. Respects `SCRAPE_SEARCH_TIMEOUT`.
- `download_document(listing, output_dir)` — identical body to ViewPublisher / iCompass (stream with `SCRAPE_DOWNLOAD_TIMEOUT`, `FILE_READ_CHUNK_SIZE` chunks, `UTF-8` User-Agent). No special logic.

Document ID scheme: `document_id = UID`. Filename: `f"Agenda_{date_iso}_{uid}.pdf"`. `document_type="agenda"`, `file_format="pdf"`, `title=body_filter_original_case_from_config` (i.e., use the YAML-provided label to avoid drift from SUMMARY variants like "Planning Commission" vs "Planning Commission Meeting").

### Wave 2 — Factory registration

**File:** `modules/commission/scrapers/base.py`

Edit `PlatformScraper.for_platform`:

1. Add import near existing sibling imports, **alphabetically after `CivicPlusScraper`**:
   ```python
   from modules.commission.scrapers.civicplus_calendar import CivicPlusCalendarScraper
   ```
2. Add dict entry in alphabetical order, **after `"civicplus"` and before `"civicweb_icompass"`**:
   ```python
       "civicplus_calendar": CivicPlusCalendarScraper,
   ```

### Wave 3 — YAML config

**File:** `modules/commission/config/jurisdictions/FL/haines-city-pc.yaml` (NEW, Planning Commission)

```yaml
slug: haines-city-pc
name: "City of Haines City Planning Commission"
state: FL
county: Polk
municipality: "Haines City"
commission_type: planning_commission

scraping:
  platform: civicplus_calendar
  base_url: "https://www.hainescity.com"
  category_ids: [34]                # Public Meetings; superset of 14 + 28
  body_filter: "Planning Commission"
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
  - "CivicPlus Calendar — iCal feed at /common/modules/iCalendar/iCalendar.aspx?catID=34&feed=calendar. As of 2026-04-16 the city does not attach agenda PDFs to Calendar events; adapter will return zero listings until they do."
```

**File:** `modules/commission/config/jurisdictions/FL/haines-city-cc.yaml` (NEW, City Commission — stub)

```yaml
slug: haines-city-cc
name: "City of Haines City CC"
state: FL
county: Polk
municipality: "Haines City"
commission_type: city_commission

scraping:
  platform: civicplus_calendar
  base_url: "https://www.hainescity.com"
  category_ids: [35]                # Elected Officials; EMPTY as of 2026-04-16
  body_filter: "City Commission"
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
  - "KNOWN-EMPTY DATA SURFACE as of 2026-04-16: Haines City does not publish City Commission agendas through CivicPlus Calendar, AgendaCenter, or any anonymous HTML endpoint discovered during Session G recon. The DocumentCenter is a React SPA with no scrapable fallback. Config is registered against the Elected Officials catID=35 (currently 0 events) so the jurisdiction appears in load_all_jurisdictions() and will begin producing listings if/when they start attaching agendas."
  - "Parent follow-up: reconsider via DocumentCenter reverse-engineering or by contacting City Clerk."
```

Neither config declares an explicit `keywords:` list → `_apply_defaults` in `config_loader.py` will merge the `_florida-defaults.yaml` keyword block automatically (verified against `bartow-cc.yaml` precedent — that one duplicates the keywords inline which is legal but not required; the iCompass/Walton BCC precedent omits them and relies on the merge).

### Wave 4 — Unit tests

**File:** `tests/test_civicplus_calendar_scraper.py` (NEW)

Structure mirrors `tests/test_civicweb_icompass_scraper.py`. ~22 tests across 10 test classes. Fixtures are hand-built VCALENDAR strings plus event-detail HTML snippets.

Fixtures to define:

- `ICS_WITH_PC_EVENTS_NO_ATTACH` — 3 VEVENTs (Planning Commission, varying dates, no ATTACH). Mirrors observed Haines City shape. Used to prove the "return empty when no agendas" contract.
- `ICS_WITH_ATTACH_PDF` — 2 VEVENTs, one with `ATTACH;FMTTYPE=application/pdf:https://example.gov/agenda.pdf`, one with `ATTACH:https://example.gov/other.pdf`.
- `ICS_WITH_MIXED_SUMMARY` — 3 VEVENTs: Planning Commission + City Commission + Advisory Board, each with ATTACH. Used to prove body_filter exclusivity.
- `ICS_WITH_LINE_FOLDING` — VEVENT whose DESCRIPTION and ATTACH are split across multiple lines per RFC-5545 line folding (long line + CRLF + space).
- `ICS_WITH_TZID_DATETIME`, `ICS_WITH_FLOATING_DATETIME`, `ICS_WITH_DATE_ONLY` — three DTSTART shapes.
- `ICS_EMPTY` — skeleton VCALENDAR with zero VEVENTs.
- `ICS_WITH_DUPE_UID` — same UID appearing in two passes (simulates union of two category feeds).
- `EVENT_DETAIL_WITH_PDF_HTML` — `<ul itemprop="documents" class="documentsList"><li><a href="/DocumentCenter/View/12345/Agenda">Agenda</a></li></ul>` (with a PDF terminating path). Used for HTML fallback test.
- `EVENT_DETAIL_EMPTY_DOCS_HTML` — empty documentsList. Used to prove "skip cleanly, don't synthesize".

### Test manifest (one-line each)

1. **FactoryRegistrationTests.test_factory_returns_civicplus_calendar_scraper** — `PlatformScraper.for_platform("civicplus_calendar")` hands back `CivicPlusCalendarScraper`.
2. **FactoryRegistrationTests.test_factory_raises_for_unknown_platform** — unknown platform still raises `ValueError` (regression guard).
3. **MissingConfigTests.test_missing_base_url_returns_empty** — no `base_url` → `[]`, no HTTP call.
4. **MissingConfigTests.test_missing_category_ids_returns_empty** — empty/absent `category_ids` → `[]`.
5. **MissingConfigTests.test_missing_body_filter_returns_empty** — no `body_filter` → `[]`.
6. **MissingConfigTests.test_bad_date_range_returns_empty** — malformed date strings → `[]`.
7. **MissingConfigTests.test_inverted_date_range_returns_empty** — `start > end` → `[]` and no HTTP call (patch `requests.get`, assert `call_count == 0`).
8. **ICSParsingTests.test_parses_tzid_datetime** — `DTSTART;TZID=America/New_York:20260511T160000` → `date_str="2026-05-11"`.
9. **ICSParsingTests.test_parses_floating_datetime** — bare `DTSTART:20260511T160000` → `date_str="2026-05-11"`.
10. **ICSParsingTests.test_parses_date_only** — `DTSTART;VALUE=DATE:20260511` → `date_str="2026-05-11"`.
11. **ICSParsingTests.test_rfc5545_line_folding_unfolds** — a long `ATTACH:` broken across lines with CRLF+space is unfolded and a single PDF URL is extracted.
12. **BodyFilterTests.test_filter_matches_body** — SUMMARY containing "Planning Commission Meeting" is included under `body_filter="Planning Commission"`.
13. **BodyFilterTests.test_filter_excludes_wrong_body** — SUMMARY "Lakes Advisory Board" is excluded under `body_filter="Planning Commission"`.
14. **BodyFilterTests.test_filter_is_case_insensitive** — `body_filter="city commission"` matches `SUMMARY:City Commission Meeting`.
15. **DateWindowingTests.test_before_start_excluded** — VEVENT dated 2026-03-01 is excluded when window is 2026-04-01..2026-12-31.
16. **DateWindowingTests.test_after_end_excluded** — VEVENT dated 2027-01-01 is excluded when window is 2026-04-01..2026-12-31.
17. **AttachExtractionTests.test_attach_pdf_extracted** — `ATTACH;FMTTYPE=application/pdf:https://example.gov/a.pdf` yields listing with `url="https://example.gov/a.pdf"`.
18. **AttachExtractionTests.test_attach_non_pdf_ignored** — `ATTACH:https://example.gov/photo.jpg` alone → event skipped (no agenda PDF).
19. **AttachExtractionTests.test_no_attach_no_html_pdf_skipped** — VEVENT without ATTACH whose event-detail HTML also has empty `documentsList` → skipped (mocks both iCal and HTML fetch).
20. **HtmlFallbackTests.test_fallback_scrapes_documents_list_when_attach_absent** — no ATTACH, but event-detail HTML has `<ul itemprop="documents">` with a `.pdf` link → listing emitted with that URL.
21. **DedupTests.test_dedup_across_categories_by_uid** — same UID in two category feeds (union) yields exactly one listing.
22. **NetworkFailureTests.test_ics_fetch_fails_category_skipped** — if `requests.get` for one catID raises `RequestException`, that category is skipped and others still parse.
23. **NetworkFailureTests.test_all_ics_fetches_fail_returns_empty** — all catID fetches fail → `[]` (no crash).
24. **EmptyFeedTests.test_empty_vcalendar_returns_empty** — valid VCALENDAR with zero VEVENTs → `[]`.
25. **EmptyFeedTests.test_haines_city_zero_attach_reality_returns_empty** — `ICS_WITH_PC_EVENTS_NO_ATTACH` + mocked event-detail HTML that has empty documentsList → `[]`. This is the explicit "Haines City real-shape" regression test.
26. **DocumentListingFieldTests.test_listing_fields_populated** — title=body_filter-cased, document_type="agenda", file_format="pdf", filename=`Agenda_YYYY-MM-DD_<UID>.pdf`, url absolute, document_id=UID.
27. **DownloadDocumentTests.test_download_writes_file** — streams mocked PDF bytes to `output_dir/filename`, returns full path.
28. **DownloadDocumentTests.test_download_creates_nested_output_dir** — `output_dir` under nested missing folders is created.

Target: ≥22 tests (Session F precedent is ~20 in `test_civicweb_icompass_scraper.py`). The list above has 28.

Patch target for mocks: `modules.commission.scrapers.civicplus_calendar.requests.get`. Use a URL-dispatcher helper identical in shape to `_url_dispatcher` in `tests/test_civicweb_icompass_scraper.py` — dispatch by URL path: if path ends with `iCalendar.aspx`, return the ics fixture; if path starts with `/Calendar.aspx`, return the event-detail HTML fixture.

### Wave 5 — Live validation script

**File:** `tmp/verify_cr_haines_city.py` (NEW)

```python
"""Live validation for Haines City CivicPlus Calendar CR adapter (Session G)."""
import sys
from datetime import date, timedelta
from modules.commission.config_loader import load_jurisdiction_config
from modules.commission.scrapers.base import PlatformScraper


def run(slug: str, threshold: int) -> int:
    cfg = load_jurisdiction_config(slug)
    assert cfg, f"no config loaded for {slug}"
    scraping = cfg["scraping"]
    end = date.today()
    start = end - timedelta(days=180)
    scraper = PlatformScraper.for_platform(scraping["platform"])
    listings = scraper.fetch_listings(
        scraping, start.isoformat(), end.isoformat()
    )
    print(f"[{slug}] {len(listings)} listings in {start}..{end}")
    for item in listings[:5]:
        print(f"  {item.date_str} id={item.document_id} {item.url}")
    return len(listings)


if __name__ == "__main__":
    # Known-empty jurisdictions get threshold=0. If Haines City starts
    # attaching agendas later, bump these to the standard >=3.
    slugs = [
        ("haines-city-cc", 0),  # known-empty: catID=35 Elected Officials has 0 events
        ("haines-city-pc", 0),  # known-empty: catID=34 events exist but 0 attachments
    ]
    rc = 0
    for slug, threshold in slugs:
        n = run(slug, threshold)
        if n < threshold:
            print(f"FAIL: {slug} returned {n}, expected >= {threshold}")
            rc = 1
    sys.exit(rc)
```

**Why thresholds are 0 not 3:** per the planner prompt escalation guidance. An adapter that correctly returns `[]` against a tenant with no attachable data is working as designed. A non-zero threshold would make the live validation falsely fail and would tempt the Executor to synthesize fake listings to "pass" — exactly the anti-pattern to avoid.

If the parent agent wants a meaningful smoke test of the iCal parsing code path, point the script at a second known-good tenant (e.g. the Bartow CC or Winter Haven CC domains, if any of them happen to publish via Calendar with ATTACH — none of the ones already committed do, so a real third-party tenant would need to be sourced).

### Wave 6 — Full suite run

```
cd C:\Users\abrhi\Code\CountyData2
python -m unittest discover -s tests -v
```

Baseline measured 2026-04-16 at plan-time: **378 tests** (prompt's "546" appears stale — this is a discrepancy flag for the parent). Expected post-change: **378 + 28 = 406 tests**, all pass. If baseline is actually 546 in a different test-discovery mode the caller is using, the same delta (+28) applies.

### Wave 7 — Live validation run

```
cd C:\Users\abrhi\Code\CountyData2
python tmp\verify_cr_haines_city.py
```

Expected output:

```
[haines-city-cc] 0 listings in 2025-10-18..2026-04-16
[haines-city-pc] 0 listings in 2025-10-18..2026-04-16
```

Exit code 0. Zero listings is the correct answer for Haines City right now.

### Wave 8 — Commit

Commit message (Session G label):

```
cr: CivicPlus Calendar adapter + Haines City CC/PC stubs — Session G

- New civicplus_calendar scraper consuming iCal feed (ATTACH) with
  event-detail HTML fallback on ul.documentsList.
- Haines City CC and PC YAMLs; both documented as known-empty data
  surfaces as of 2026-04-16 (recon in docs/sessions/2026-04-16-*.md).
- 28 new unit tests, factory registration in alpha position
  (civicplus → civicplus_calendar → civicweb_icompass).
```

---

## 5. Risks / Open Questions (≥5, all escalate-not-improvise)

1. **Primary risk — the task is infeasible for the stated target body.** There is no discovered data surface that carries Haines City City Commission agendas. Building a Calendar adapter against the tenant produces zero rows for CC. Any non-zero live-validation threshold will fail. *Do not* let the Executor paper over this with fake thresholds or synthetic listings. Escalate to the user: (A) redirect to DocumentCenter SPA reverse-engineering (separate task, likely Selenium), (B) defer Haines City, or (C) ask the City Clerk directly.

2. **iCal feed privileges `SUMMARY` title as the body identifier** — but the SAME meeting appears with SUMMARY="Planning Commission Meeting" in catID=14 and SUMMARY="Planning Commission" in catID=28 (different EIDs: 5611 vs 5940). If the `body_filter="Planning Commission"` matches both, dedup must be on some natural key (UID alone is unsafe — different UIDs for the same real meeting). Candidate composite key: `(date_iso, first-PDF-URL)`. Without ATTACH lines to discriminate, this risk is moot for Haines City, but escalate if a different tenant triggers it.

3. **The test suite baseline the prompt cites (546) does not match observed (378).** Either a different test runner config is in play (pytest with more plugins? additional module under test?), or the prompt is stale. Before the Executor runs, confirm the actual baseline; otherwise "no regressions" is unmeasurable.

4. **CivicPlus tenants vary in iCal feed population.** Some tenants emit `ATTACH` with direct `https://tenant.com/DocumentCenter/View/<id>` URLs; others embed the PDF link inside `X-ALT-DESC` HTML; others don't expose agendas via iCal at all. Haines City is the last case. This adapter's contract must be: "return rows for VEVENTs that have a discoverable PDF via ATTACH *or* event-detail `ul.documentsList`; skip cleanly otherwise." Do not add a Selenium fallback; that crosses the task's "requests + bs4 only" constraint.

5. **DocumentCenter React SPA is a known blocker for anonymous scraping.** Any future attempt to pull CC agendas from `/DocumentCenter` will need either: (a) Selenium + wait-for-render + scrape, (b) intercept the actual XHR/GraphQL call the SPA makes (would need live browser inspection — NOT done in this recon), or (c) a different CivicPlus admin API that requires a tenant-issued key. Escalate separately before anyone codes against it.

6. **TZID handling:** all Haines City DTSTART values use `TZID=America/New_York`. When we compare `dt` to `start_dt`/`end_dt` (naive dates), we are implicitly treating the TZID datetime as a naive local-date. For the Planning Commission 4:00 PM meetings this never crosses midnight in ET, so the date extraction is stable. But a midnight-UTC VEVENT at 8:00 PM ET could roll into the next calendar day if converted to UTC first. Recommended: parse the `YYYYMMDD` portion and ignore the time entirely for binning. Escalate if we ever see `DTSTART:YYYYMMDDTHHMMSSZ` (UTC Z-suffixed) against a future tenant — the rule above would need revisiting.

7. **FL defaults merge depends on config file convention.** `_apply_defaults` pulls `_florida-defaults.yaml` *only if `keywords:` is absent*. Both `haines-city-cc.yaml` and `haines-city-pc.yaml` above omit `keywords:` to let the merge happen (matches `walton-county-bcc.yaml` precedent). If the Executor accidentally copies the `bartow-cc.yaml` shape and inlines the whole keyword list, nothing breaks functionally but the configs drift from the iCompass-precedent convention. Low risk, flagging for QA.

8. **`has_duplicate_page_bug: false`** is copied from precedents. This flag is CivicPlus-AgendaCenter-specific. Its meaning for a Calendar adapter is undefined. Either (a) omit it from the two new YAMLs, or (b) keep it as false for uniformity. Recommend (b) to avoid a schema-validator surprise; flag for the QA agent to verify there's no strict-schema check on unknown keys.

---

## 6. What the Planner explicitly did NOT do

- Did not write any code. No `.py` files touched.
- Did not edit `modules/commission/scrapers/base.py`.
- Did not create any YAML files.
- Did not write any tests.
- Did not run the live validation.
- Did not commit.

All of the above are Executor work, contingent on the parent agent's decision in §3.

---

## 7. Pointers for the Executor (only if §3 gate opens)

- Session D precedent: `modules/commission/scrapers/granicus_viewpublisher.py` + `tests/test_granicus_viewpublisher_scraper.py`.
- Session F precedent: `modules/commission/scrapers/civicweb_icompass.py` + `tests/test_civicweb_icompass_scraper.py`.
- Factory: `modules/commission/scrapers/base.py::PlatformScraper.for_platform`.
- Config loader: `modules/commission/config_loader.py::_apply_defaults`.
- FL defaults: `modules/commission/config/jurisdictions/FL/_florida-defaults.yaml`.
- Constants: `SCRAPE_SEARCH_TIMEOUT=30`, `SCRAPE_DOWNLOAD_TIMEOUT=60`, `FILE_READ_CHUNK_SIZE=8192` — reuse.
- User-Agent string precedent: `"CommissionRadar/1.0"`.
- Live-validation script precedent: `tmp/verify_walton_cr.py`.
- Recon artifacts saved during Session G planning: `~/AppData/Local/Temp/hc_*.html`, `~/AppData/Local/Temp/hc_ical_*.ics` (13 category feeds captured).
