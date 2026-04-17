# Bay County FL -- CityView Permits API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | CityView (Municipal Software) + monthly PDF reports |
| Live portal URL | `https://portal.baycountyfl.gov/` |
| PDF report index | `https://www.baycountyfl.gov/155/Permits` |
| Protocol | PDF download + `pypdf` layout-mode text extraction (no live API) |
| Auth | Anonymous PDF download; live portal is CAPTCHA-gated |
| Adapter | `modules.permits.scrapers.adapters.bay_county.BayCountyAdapter` |
| Parser | `pypdf.PdfReader.extract_text(extraction_mode="layout")` + fixed-column splitter |
| Target prefix | `PRSF` (1-and-2-family dwellings) |

The official CityView locator at `portal.baycountyfl.gov` enforces a CAPTCHA on the public permit search UI. Instead of automating the CAPTCHA, the adapter consumes the **public monthly permit report PDFs** that Bay County publishes at `baycountyfl.gov/155/Permits`. These PDFs contain the same data (application date, permit type, permit number, address, owner, contractor, issued date, status, valuation) in a fixed-width tabular layout.

### Report Types

| Label pattern | Parser regex | Kind |
|---------------|-------------|------|
| `{Month} {YYYY} Permit Report` | `^(?P<month>[A-Za-z]+)\s+(?P<year>\d{4})\s+Permit Report$` | monthly |
| `{YYYY} Permit Report` | `^(?P<year>\d{4})\s+Permit Report$` | annual |

Both kinds are discovered from the Permits page HTML via BeautifulSoup scanning `<a href>` link text for the substring `"Permit Report"`.

---

## 2. Monthly PDF Pipeline

### Discovery

```
GET https://www.baycountyfl.gov/155/Permits
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
```

The HTML is parsed with `BeautifulSoup(html, "html.parser")`. Every `<a href>` whose text contains `"Permit Report"` is captured; the text is matched against the monthly and annual regexes, then bucketed by `(year, month)` (monthly wins over annual for the same month).

### Selection

Given a requested `(start_date, end_date)` window:

- If both are `None`, selects only the most recent report.
- Otherwise, walks month-by-month from `start_date.replace(day=1)` through `end_date.replace(day=1)`, preferring the matching monthly report and falling back to the year's annual report.

### Download & Parse

```
GET {report.url}
(streamed into pypdf.PdfReader via BytesIO)
```

Each page's text is extracted with `extract_text(extraction_mode="layout")`. The layout-mode output preserves column positions as leading whitespace, which the adapter keys on to assign each token to a field.

---

## 3. PDF Field Layout (Fixed Columns)

The adapter declares a default fixed-column layout in `BayCountyAdapter._field_starts`. Column offsets are the minimum starting character position at which each token belongs to the named field:

| Field | Starting column (chars from left edge) |
|-------|----------------------------------------|
| `application_date` | 33 |
| `building_use` | 63 |
| `permit_meta` | 99 |
| `address` | 166 |
| `owner_name` | 199 |
| `contractor_name` | 223 |
| `issued_date` | 250 |
| `finalled_date` | 280 |
| `permit_status` | 310 |
| `valuation` | 362 |

Tokens are extracted via a regex that captures each non-whitespace-bounded run:

```python
_token_pattern = re.compile(r"\S(?:.*?\S)?(?=(?:\s{2,}|$))")
```

Each token's start index is compared against the table above; the largest column start `<=` token start wins.

### Adaptive Column Inference

When a report's columns drift (variant templates across years), `_infer_field_starts` re-computes the starts from the first data row:

1. Find the token whose text matches `_permit_number_pattern` (`(PR[A-Z]{2,}\d{6,})`).
2. Fix `application_date`, `building_use`, `permit_meta` to the first three token starts.
3. Assign the next three tokens (after the permit number) to `address`, `owner_name`, `contractor_name`.
4. Scan the tail for two `MM/DD/YYYY` date positions (issued, finalled), one `$`-prefixed valuation token, and one non-date / non-dollar status token.
5. Fallback arithmetic (`+28`, `+28`, `+48`) for any missing tail columns.

### Header / Footer Filters

- `_is_header_line` skips the literal `"January"` token, any line starting with `"dateEntered"`, `"PERMITS ISSUED BY DATE AND TYPE"`, `"Permit Type Permit Number"`, or a bare `MM/DD/YYYY` date.
- `_is_footer_line` skips lines starting with `=`, `"Count "`, `"Subtotal "`, or `"Total "` (these flush and finalize the current row).

---

## 4. Permit Number Format

Captured by `_permit_number_pattern = re.compile(r"(PR[A-Z]{2,}\d{6,})")`.

Known prefixes observed in Bay's monthly reports:

| Prefix | Meaning | Kept? |
|--------|---------|-------|
| `PRSF` | Single-Family (1-and-2-family dwelling) | **YES** -- only accepted |
| `PRCM` | Commercial | no |
| `PRMH` | Mobile Home | no |
| `PRMF` | Multi-Family | no |
| `PRTR` | Trade (sub-permit) | no |
| (other `PR*` variants) | misc | no |

The adapter's prefix filter is hard-coded:

```python
if not permit_number.startswith("PRSF") or issued_date is None:
    return None
```

If the `issued_date` cannot be parsed (not `MM/DD/YYYY` at positions 0-10 of the token), the row is dropped.

---

## 5. What We Extract

Emitted `dict` per permit from `_row_to_permit`:

| Output Field | Source | Notes |
|--------------|--------|-------|
| `permit_number` | `permit_meta` (regex-extracted) | Must start with `PRSF` |
| `address` | `address` column | Raw PDF column text, whitespace-collapsed |
| `parcel_id` | -- | Always `None` (PDF does not include parcel) |
| `issue_date` | `issued_date` column | Parsed to `YYYY-MM-DD` ISO |
| `status` | `permit_status` column | Raw text (e.g., "Issued", "Finaled") |
| `permit_type` | derived from `permit_meta` minus the permit number | Falls back to `"One and Two Family Dwelling"` |
| `valuation` | `valuation` column | `$` and `,` stripped, coerced to float |
| `raw_subdivision_name` | -- | Always `None` |
| `raw_contractor_name` | `contractor_name` or `owner_name` fallback | Owner fallback when contractor column is blank |
| `latitude` | -- | Always `None` |
| `longitude` | -- | Always `None` |

Dedup is per-run: a `seen` set on `permit_number` prevents duplicate emissions when the same permit appears across overlapping reports (monthly + annual).

---

## 6. Live Portal Search (Not Used)

`https://portal.baycountyfl.gov/` hosts the CityView-style locator. Observed behavior from research notes (`modules/permits/data/source_research.json`, key `bay-county`):

> Official permit search still runs through CityView and now prompts for CAPTCHA at the public locator, which makes direct live scraping brittle.

The adapter therefore treats the live portal as **off-limits** and uses the PDF pipeline as the canonical source.

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Available but Not Extracted | Source |
|---------------|--------------------|---------|-----------------------------|--------|
| Permit Number | YES | PDF `permit_meta` | -- | -- |
| Address | YES | PDF `address` | Full structured address | Live portal (CAPTCHA-gated) |
| Issue Date | YES | PDF `issued_date` | -- | -- |
| Finalled Date | NO | -- | Completion date | PDF `finalled_date` column |
| Application Date | NO | -- | Date submitted | PDF `application_date` column |
| Status | YES | PDF `permit_status` | -- | -- |
| Permit Type | YES | PDF `permit_meta` tail | Machine-parsable CityView type codes | Live portal |
| Valuation | YES | PDF `valuation` | -- | -- |
| Owner Name | PARTIAL (used as contractor fallback only) | PDF `owner_name` | Dedicated owner output field | PDF `owner_name` column |
| Contractor | YES | PDF `contractor_name` | -- | -- |
| Building Use (1st column) | NO | -- | e.g., "Single Family Dwelling" | PDF `building_use` column |
| Parcel ID | NO (always None) | -- | Via live portal detail page | CityView locator |
| Subdivision | NO | -- | Not in PDF; live portal only | CityView locator |
| Inspections | NO | -- | Inspection list | Live portal (CAPTCHA-gated) |
| Fees | NO | -- | Fee table | Live portal |
| Coordinates (lat/lon) | NO (always None) | -- | Not in PDF | -- |

---

## 8. Known Limitations and Quirks

1. **PDF is the source, not the live portal.** Bay County's live CityView locator is CAPTCHA-protected. The adapter deliberately avoids it and instead downloads the monthly / annual `Permit Report` PDFs from the county website. Any PDF layout change breaks the fixed-column splitter.

2. **Fixed-column offsets are brittle.** `_field_starts` uses hard-coded character offsets (33, 63, 99, 166, 199, 223, 250, 280, 310, 362). If Bay re-templates the report (e.g., adds a column, widens a field), the splitter will silently misassign tokens. `_infer_field_starts` attempts to recover by re-keying off the permit-number token position, but this only works when the first data row follows the standard layout.

3. **Only `PRSF` permits are kept.** The adapter hard-codes `permit_number.startswith("PRSF")`. Any other prefix (`PRCM`, `PRMH`, `PRMF`, `PRTR`, etc.) is dropped on entry. Widening the filter requires code change.

4. **No parcel ID.** The PDFs do not contain parcel numbers; `parcel_id` is always `None`. Cross-referencing to GIS requires downstream joining on address, which is fragile due to Bay's legal-fragment-style `DSITEADDR` values.

5. **No coordinates.** `latitude` and `longitude` are always `None`. Bay County does not publish geocoded permits in PDF form.

6. **Report discovery is label-based.** Discovery of reports relies on matching link text (`"{Month} {YYYY} Permit Report"` or `"{YYYY} Permit Report"`). A renamed link (e.g., "2026 Bay County Residential Permits") would be missed.

7. **Monthly vs annual precedence.** When both a monthly report and that year's annual report overlap, the monthly report wins (monthly dict is checked first in `_select_reports`).

8. **Report page fetch timeout.** The outer fetch (`permits_page_url`) uses a 30s timeout; each PDF fetch uses 60s. Very slow responses from the Bay County web server return empty list silently.

9. **Owner column used as contractor fallback.** When the `contractor_name` column is blank, the adapter falls back to `owner_name` for `raw_contractor_name`. This inflates the contractor match rate at the cost of correctness on owner-builder permits.

10. **Valuation must start with `$` to be detected by the adaptive splitter.** `_infer_field_starts` detects the valuation column by finding a token that `.startswith("$")`. If a report is generated without a leading `$` (e.g., raw number), the inference will misalign the tail columns.

11. **Status normalization is the PDF text.** No mapping layer; whatever the PDF prints (`"Issued"`, `"Finaled"`, `"Void"`, etc.) is passed straight through as `status`.

12. **Default permit type fallback is a literal.** When the inferred `permit_type` is empty (all text consumed by the permit number), the adapter emits the literal string `"One and Two Family Dwelling"`.

**Source of truth:** `modules/permits/scrapers/adapters/bay_county.py` (lines 16-50 for the adapter, `_field_starts` at line 31-42), `modules/permits/data/source_research.json` (key `bay-county`), `county-registry.yaml` (`bay-fl.projects.pt`)
