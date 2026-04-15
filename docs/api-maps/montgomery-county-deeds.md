# Montgomery County AL -- Ingenuity Probate Records API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Montgomery County Probate Court (Alabama; Probate Judge J C Love, III) |
| Brand entry URL | `https://pjo.mc-ala.org/license/` |
| Live portal | `https://www.ingprobate.com/Montgomery_Probate/` |
| Vendor | Ingenuity, Inc. (in-house platform branded "ingprobate") |
| UI | ASP.NET Web Forms with `__doPostBack` navigation + Bootstrap modal disclaimers |
| Auth | Disclaimer / terms modal click-through required before record viewing |
| Registry entry | `county-registry.yaml` L600-613 has BI only; **no `cd2:` block** |
| Client reuse | None existing in this repo (new vendor family: Ingenuity / ingprobate.com) |

Montgomery's probate portal is a **different vendor line** from all the other 3 counties in this batch:
- Madison: CountyGovServices + Azure B2C.
- Jefferson: Pioneer LandmarkWeb.
- Baldwin: Kofile PublicSearch.
- **Montgomery: Ingenuity Inc. (ingprobate.com).**

The county redirects `pjo.mc-ala.org/license/` (branded subdomain) to `www.ingprobate.com/Montgomery_Probate/` where the actual application lives.

## 2. Probe (2026-04-14)

```
GET https://www.mc-ala.org/
-> HTTP 403  (Akamai edgesuite shield; county website inaccessible to curl UA)

GET https://web.archive.org/web/2025/https://www.mc-ala.org/government/probate-judge/probate-divisions/records-recording
-> HTTP 200  (archived Montgomery Probate page; links out to pjo.mc-ala.org/license/)

GET https://pjo.mc-ala.org/license/
-> 200 with redirect (via form action) -> https://www.ingprobate.com/Montgomery_Probate/
-> HTTP 200  (Ingenuity ASP.NET form; "Legal Disclaimer" modal; three buttons: "Look up Land Records", "Look up Probate Case Records", "Look up Marriage Records")
```

The ingprobate portal exposes three action buttons as `__doPostBack` anchors (`ctl00$ContentPlaceHolder2$btnRecording` etc.) gated behind a disclaimer modal. Full endpoint walk behind the disclaimer is `unverified -- needs validation` (not performed in this probe per task constraint "do NOT attempt login").

## 3. Search / Query Capabilities

Inferred from the buttons visible on the portal home:

- **Look up Land Records** (`btnRecording`) -- deed index search.
- **Look up Probate Case Records** (`btnProbate`) -- estate / guardianship / conservatorship cases.
- **Look up Marriage Records** (`btnMarriage`) -- marriage licenses.

Search UI post-disclaimer is inaccessible without interactive session bootstrap (the disclaimer click writes a session cookie via `__doPostBack`). ASP.NET ViewState + anti-forgery + disclaimer session are expected to be required on every search request.

## 4. Field Inventory

Expected (inferred -- actual field names behind the disclaimer are not verified):

- Grantor, Grantee, Record Date, Doc Type, Book, Page, Instrument.
- Legal description.
- Consideration: **non-disclosure state, not published.**

`unverified -- needs validation` -- exact field shape requires a post-disclaimer crawl which was out of scope for this probe.

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing.** No CD2 config, no adapter, no client for Ingenuity. A new adapter would need to handle:

1. Initial GET to set ASP.NET session cookie.
2. POST disclaimer-accept postback (ViewState + EVENTTARGET + EVENTARGUMENT).
3. Record-search form submission.
4. Result page scraping (HTML table or grid).
5. Per-record detail follow-up if document details are on a separate page.

**Non-disclosure state: no sale price on deeds.** Mortgage cross-reference would be the only price proxy (same-day last-name pattern), requiring parallel sessions if the portal separates mortgages from deeds under different search modes. Whether the Ingenuity portal supports distinct "search modes" or bundles all recording types under a single interface is `unverified -- needs validation`.

## 6. Auth Posture / Bypass Method

Anonymous post-disclaimer. The Legal Disclaimer click-through is a session-scoped terms-agreement flow, not a captcha and not a named account. A future adapter's `bypass` classification would be `disclaimer_handshake` (similar semantics to Bay County FL's `captcha_hybrid`).

The portal aggressively warns about automated activity: the HTML literally contains text about actively monitoring and logging page views and indicating that accounts engaging in automated activity may be immediately suspended or subject to legal action. A future adapter implementation should honor rate-limits, use a realistic User-Agent, and handle retry/backoff gracefully. This is a **higher-risk scraping target** than vendor-hosted portals like Pioneer LandmarkWeb or Kofile PublicSearch.

## 7. What We Extract vs What's Available

| Available | Extracted? |
|-----------|:----------:|
| Land record grantor / grantee / date / doc type / book / page / instrument / legal | NO |
| Probate case records | NO |
| Marriage records | NO |
| Mortgage amount (same-day cross-ref) | NO |
| Consideration | NOT PRESENT (non-disclosure) |
| Document image | NO (typically pay-per-view where available; unverified here) |

## 8. Known Limitations and Quirks

- **Non-disclosure state**: no sale price on deeds. Mortgage cross-ref is the ~40% match proxy (per `AL-ONBOARDING.md`; match rate unverified for Montgomery specifically).
- **Ingenuity Inc. is a new vendor family** for this repo -- greenfield adapter required.
- Portal text includes an aggressive auto-abuse warning (active monitoring, account-suspension language, possible legal action). Adapter design must be conservative on rate-limits and be honest about identity (no UA spoofing, honest purpose header, modest throughput).
- `pjo.mc-ala.org/license/` redirects to `ingprobate.com/Montgomery_Probate/`; use the Ingenuity canonical URL in adapter config to avoid a hop.
- Montgomery County main site (`www.mc-ala.org`) is behind Akamai and returns 403 to curl UAs; the Web Archive was used to read the probate division pages during this probe. Production adapters will either need a browser-like UA with request throttling or direct probate-portal access (which is not Akamai-shielded).
- Probate Judge is the recording authority (not Clerk of Court) -- standard for AL.
- `L L C` spacing applies.

Source of truth: `county-registry.yaml` (montgomery-al L600-613, BI-only), `AL-ONBOARDING.md`, archived Montgomery Probate Records page (web.archive.org capture of `www.montgomeryprobatecourtal.gov/divisions/records-recording/probate-records-search`), live probe `https://pjo.mc-ala.org/license/` -> `https://www.ingprobate.com/Montgomery_Probate/`.
