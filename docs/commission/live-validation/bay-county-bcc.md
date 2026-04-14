# bay-county-bcc — Live Validation

- **Status:** FAIL
- **Adapter:** novusagenda
- **Portal:** https://baycounty.novusagenda.com/agendapublic
- **Date window:** 2025-10-01 → 2026-04-14 (6 months)
- **Timestamp (UTC):** 2026-04-14T17:21Z
- **Validated via:** `scripts/cr_live_validate.py` + manual retry

## Results

- **Listings returned:** 0
- **Agenda listings:** 0
- **Status:** portal is serving an error page on both the initial `GET Meetings.aspx` and any follow-up POST. The scraper correctly treats this as an empty result rather than exploding.

## Portal response (first 2KB)

Both the GET and the POST to `/agendapublic/Meetings.aspx` return a 200 whose body is NovusAgenda's generic error template (`action="Error.aspx?handler=Application_Error+-Global.asax"`):

```html
<!DOCTYPE html>
<html lang ="en">
<head><title>NovusAGENDA</title>...</head>
<body>
<form method="post" action="Error.aspx?handler=Application_Error+-Global.asax" id="aspnetForm">
  ...
  <h2>Error:</h2>
  <span id="ctl00_ContentPlaceHolder1_FriendlyErrorMsg" style="color: red">
    An HTTP error occurred. . Please try again.
  </span>
  ...
</form>
</body>
</html>
```

The form on the page already targets `Error.aspx`, so the ASP.NET session is in a stuck/expired state before any user action. The `__VIEWSTATE` token returned on GET (VSG `B005743D`) is the error-page state, not a working Meetings search state.

## Traceback

No Python traceback — `fetch_listings` returned `[]` cleanly:

```
NovusAgenda scraper requires base_url in config   (not triggered; base_url present)
fetch_listings -> 0 listings -> validator: "no listings returned" -> FAIL
```

## Warnings / notes

- **Root cause is portal-side**, not scraper bug. No novusagenda fix attempted per task rules.
- Bay County is the only novusagenda jurisdiction in the config tree, so this family remains unvalidated in this pass. Revisit in a future pass (portal may recover) or if a second novusagenda jurisdiction is added.
- Response body (<1.4 KB) fully reproduced above — no need for a separate dump file.

## 2026-04-14 retry

- **Status:** still FAIL.
- `curl -I https://baycounty.novusagenda.com/agendapublic/Meetings.aspx` returns **HTTP/1.1 200 OK** (chunked, IIS 10.0, `GranicusServer: gasmp-novweb7`) — misleading, because a full `GET` of the same URL still returns the NovusAgenda error-template body (`form action="Error.aspx?handler=Application_Error+-Global.asax"`, same `Please try again.` text, `__VIEWSTATE` starts with `/wEPDwUKMTc5Njcx...`).
- `scripts/cr_live_validate.py` on `bay-county-bcc.yaml` again returns `listings_count: 0` with `error: "no listings returned"`.
- No change in content length category (still sub-2 KB error template). No scraper change needed; portal remains in the stuck error state observed earlier today. Revisit on the next pass.
