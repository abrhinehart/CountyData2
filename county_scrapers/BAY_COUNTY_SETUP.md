# Bay County FL — Automated Record Pulling

Bay County uses LandmarkWeb (same as Hernando and Okeechobee) but enforces reCAPTCHA v3 on all search endpoints. This means pure HTTP automation doesn't work — a human needs to pass the captcha once per session, then the script takes over.

## How it works

1. The script opens a Chrome window to Bay County Official Records
2. You do one manual search (takes ~15 seconds)
3. The script steals the browser's session cookies
4. Chrome closes, and the script pulls all records via fast HTTP requests

The captcha-validated session lasts 20-30 minutes, which is plenty for a full month of records.

## Running a pull

```bash
python -m county_scrapers.pull_records --county Bay --begin 03/01/2026 --end 03/31/2026
```

A Chrome window will open. Follow the on-screen instructions:

1. **Accept the disclaimer** — click the button or wait for it to auto-accept
2. **Switch to "Record Date" search** — select it from the search type dropdown
3. **Run one search** — enter any date range and click Search. You should see results appear in the table.
4. **Go back to the terminal** and press Enter

The script handles everything from there: pulls all deed records for the requested date range, filters for builder/land banker entities, and writes a CSV to `output/`.

## What's happening under the hood

- `county_scrapers/cookie_session.py` opens Chrome with anti-detection flags (same setup as `bay_price_extract.py`) and waits for you to interact
- After you press Enter, it reads all cookies from the Selenium-controlled browser via `driver.get_cookies()`
- Those cookies are injected into a `requests.Session` on the existing `LandmarkSession` adapter
- The adapter then calls `RecordDateSearch` and `GetSearchResults` (DataTables JSON) exactly like it does for Hernando and Okeechobee — just with the stolen cookies carrying the captcha validation
- Entity filtering uses the same builder/land banker alias lists as every other county

## Prerequisites

- **Chrome** installed on the machine
- **Selenium + webdriver-manager** installed (`pip install selenium webdriver-manager`)
- ChromeDriver is auto-downloaded and cached by webdriver-manager on first run

## Troubleshooting

| Issue | Fix |
|---|---|
| `No module named 'selenium'` | Run `pip install selenium webdriver-manager` |
| Chrome doesn't open | Confirm Chrome is installed; check that no other ChromeDriver process is stuck |
| "Invalid Captcha" after pressing Enter | You need to actually complete a search in the browser, not just load the page. reCAPTCHA v3 scores the full interaction. |
| Session expired / 0 results | The session cookies last ~20-30 minutes. If the pull takes longer, re-run the command. |
| Different results than expected | Bay uses `DEFAULT_COLUMN_MAP` (legal at column 13). If the portal changes its layout, the column map may need updating in `configs.py`. |

## Future: UI dashboard integration

When this runs from the web UI, the flow would be:

1. User clicks "Pull Bay County" on the Pipeline page
2. API opens a new browser tab to the Bay County portal (via a WebSocket message or redirect)
3. User does the manual search in that tab
4. User clicks "I'm done" back on the Pipeline page
5. Backend reads the session cookies (via a browser extension, shared cookie jar, or the user pasting a cookie string) and runs the pull

The key constraint is that the captcha validation happens in a real browser session, so the human-in-the-loop step can't be fully eliminated — only made smoother.
