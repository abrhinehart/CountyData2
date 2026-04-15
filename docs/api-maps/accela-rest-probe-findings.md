# Accela v4 REST API — Probe Findings (April 2026)

Probed: 2026-04-15
Probe script: [`scripts/accela_rest_probe.py`](../../scripts/accela_rest_probe.py)
Raw outputs: `tmp/accela_probe_polkco.md`, `tmp/accela_probe_polkco_v2.md`, `tmp/accela_probe_polkco_v3.md`
Related: [polk-county-improvement-report.md](polk-county-improvement-report.md) (ACCELA-02)

## Context

The April 2026 merge of the Polk County improvement report flagged ACCELA-02 (migrate the Polk / Lake Alfred / Winter Haven Accela adapters from HTML+regex to the v4 REST API) as the "highest strategic-value multi-session project" — large effort, high risk, but collapsing most of the Section 1 gap backlog into a single roadmap item. That recommendation was contingent on the assumption that Accela v4 REST would accept anonymous traffic from a free Citizen App registration at `developer.accela.com`.

This probe session was the prerequisite to scoping that project. The headline finding contradicts the assumption: Accela v4 REST is not available for bulk anonymous public-data extraction. It is designed for authorized integrations and gated at the agency-configuration layer, independent of App ID.

## TL;DR

- Accela v4 REST is designed for authorized integrations, not anonymous bulk extraction.
- No tested Florida agency (POLKCO, CITRUS, COLA, BOCC, BREVARD) has the "anonymous user" feature enabled.
- Even endpoints that *could* work anonymously (search-records, record-detail, addresses, parcels, custom-forms, record-types) are blocked at the agency-config layer.
- Endpoints that *always* require a bearer token (contacts, professionals, owners, inspections, fees, documents, workflow-tasks, related, inspection-types) are unreachable regardless of agency config.
- HTML scraping via the ACA citizen portal (`aca-prod.accela.com/POLKCO/...`) — which we already use — remains the correct mechanism for our bulk public-data use case.

## Methodology

- Registered a Citizen App at `developer.accela.com` after first trying an Agency App. Agency Apps expect real agency-staff credentials for the password/client_credentials grant; Citizen Apps use `authorization_code` with a browser redirect on behalf of a specific citizen.
- Built `scripts/accela_rest_probe.py` to sweep 16 v4 endpoints with two auth patterns (anonymous header-only; `client_credentials` bearer from the registered Citizen App).
- Three probe runs against POLKCO (see raw outputs) plus single-run sweeps against CITRUS, COLA, BOCC, BREVARD.
- Known probe record: altId `BR-2026-2894` on POLKCO.

## Evidence

### Table A — POLKCO endpoint matrix (v3 Citizen App run)

| Endpoint | Method | Auth | Status | Error |
|---|---|---|---|---|
| `oauth2-token` | `POST` | client_credentials | 400 | `bad_request — Invalid username or password.` |
| `search-records` | `POST` | anonymous | -- | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `record-detail` | `GET` | anonymous | 401 | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `addresses` | `GET` | anonymous | 401 | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `parcels` | `GET` | anonymous | 401 | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `contacts` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `professionals` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `owners` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `inspections` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `fees` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `documents` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `workflow-tasks` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `related` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |
| `custom-forms` | `GET` | anonymous | 401 | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `record-types` | `GET` | anonymous | 401 | `anonymous_user_unavailable — The requested anonymous user is not available.` |
| `inspection-types` | `GET` | anonymous | 401 | `no_token — Token is required but not passed in the request.` |

### Table B — Agency coverage matrix

| Agency | Code | Valid? | Anonymous User | Search-Records Result |
|---|---|---|---|---|
| Polk County | POLKCO | yes | disabled | 401 anonymous_user_unavailable |
| Citrus County | CITRUS | yes | disabled | 401 anonymous_user_unavailable |
| Lake Alfred (Polk) | COLA | yes | disabled | 401 anonymous_user_unavailable |
| Charlotte County | BOCC | yes | disabled | 401 anonymous_user_unavailable |
| Brevard County | BREVARD | yes | disabled | 401 anonymous_user_unavailable |
| Brevard (alt code tried) | BREVARDFL | no | — | 400 "Agency BREVARDFL does not exist" |

## Findings

### Finding 1 — App type distinctions matter

The probe exercised both Accela App types. The literal errors differ:

- Agency App + `client_credentials` + dummy creds: `invalid_userid_or_password`
- Citizen App + `client_credentials`: `bad_request — Invalid username or password.`

Conclusion: Agency Apps expect real agency-staff credentials in the password grant; Citizen Apps do not support `client_credentials` at all — they expect `authorization_code` with a browser redirect on behalf of a specific citizen. Neither App type yields a bearer token usable for bulk anonymous read-through.

### Finding 2 — No tested FL agency has the anonymous user enabled

With only `x-accela-appid` + `x-accela-agency` + `x-accela-environment=PROD` headers and no bearer token, all five valid agencies returned:

> `anonymous_user_unavailable — The requested anonymous user is not available.`

The error code is consistent across POLKCO, CITRUS, COLA, BOCC, and BREVARD. The "anonymous user" is a per-agency toggle an admin flips inside Civic Platform; no App-ID-side registration can substitute for it.

### Finding 3 — Two-tier endpoint behavior

| Class | Anonymous-eligible (when toggle is on) | Token-mandatory (always) |
|---|---|---|
| Endpoints | search-records, record-detail, addresses, parcels, custom-forms, record-types | contacts, professionals, owners, inspections, fees, documents, workflow-tasks, related, inspection-types |
| Gate error | `anonymous_user_unavailable` | `no_token — Token is required but not passed in the request.` |

The token-mandatory class is unreachable regardless of agency config. Even the counties most likely to enable the anonymous toggle would only unlock roughly the first-column endpoints. Contacts, owners, inspections, fees, documents, workflow, and related records stay out of reach without a real user bearer token.

### Finding 4 — v4 REST is not the right tool for third-party bulk extraction

Accela's design explicitly separates tiers:

- **ACA citizen portal** — anonymous public HTML access; this is what we already scrape.
- **v4 REST** — authorized integrations, requires one of: real agency-staff credentials, citizen per-user consent via `authorization_code`, or agency-admin-enabled anonymous user.

None of these paths yield bulk anonymous read access across Florida counties without agency-side cooperation.

### Finding 5 — HTML scraping remains the correct mechanism

The ACA portal is what Accela designed for anonymous public access. REST is designed for a different audience (authorized integrations — title companies, inspection vendors, contractors consuming their own records). Treating REST as a drop-in replacement for our HTML scrapers was the wrong mental model. Our HTML adapters against `aca-prod.accela.com/POLKCO/...` are already aligned with the tier Accela intends for our use case; the brittleness of HTML extraction is a real cost but it is not solved by switching tiers.

### Finding 6 — Even a legitimate Citizen user's token would not unlock bulk extraction

Accela's citizen-authorization model scopes access to records the user is personally tied to (as applicant, owner, or contact). A per-user `authorization_code` or `password` grant token cannot see other citizens' public permits — it sees only the records the authenticated citizen has standing on. This means even if we walked an end user through the OAuth redirect, the returned token would be useless for the portfolio-wide analytics we actually need.

### Finding 7 — HTML Inspection-tab follow-up probe (April 2026)

A follow-up probe on 2026-04-14 tested whether the Accela CapDetail "Inspections sub-tab" could be fetched directly via HTTP as an alternative to the token-gated REST endpoint. Findings:

- **Not a separate page.** The `<div id="tab-inspections">` is embedded inline in the CapDetail HTML response. Tab navigation is pure client-side hash anchors; there is no independent URL for the inspection grid.
- **Partial postback returns empty.** Full ASP.NET AJAX partial-postback (headers `X-MicrosoftAjax: Delta=true`, `__ASYNCPOST=true`, ScriptManager=`inspectionUpdatePanel|btnRefreshGridView`) returns a valid 31 KB MS-AJAX delta but `panelsToRefreshIDs` is empty. Two sequential postbacks with refreshed ViewState produce identical empty results.
- **Platform-level gate.** The dispositive JS in the CapDetail page source: `if ($.global.isAdmin) { unhide real content } else { __doPostBack('...btnRefreshGridView') }`. The admin branch unhides pre-rendered server content; the anonymous branch fires a postback the server intentionally returns empty for.
- **Identical across agencies and permit ages.** Sampled POLKCO permits BR-2026-2894, BT-2024-2125, BR-2024-1234, BR-2022-1500, and eight BR-2025-46xx permits. Also tested BREVARD `24BC01760` and BOCC (Charlotte) old residential permits. Every response rendered byte-identical "There are no completed inspections on this record." placeholder regardless of the permit's actual inspection history.

**Implication:** ACCELA-06 (originally scoped as an HTML tab-fetch alternative to the token-gated REST `/inspections`) is blocked by the same platform-level agency-config gate that blocks ACCELA-02. Until an agency's Civic Platform admin enables the anonymous-user toggle, inspections are not extractable via HTML either. ACCELA-06 reclassified to P3/blocked in the Polk improvement report.

## What would unblock

Three theoretical paths, honestly assessed:

- **Agency enables anonymous user.** Requires per-agency outreach to the Civic Platform admin. Each agency is a separate conversation, and no Florida county we tested has opted in. No control on our side. Long-tail.
- **Agency staff credentials.** Would require a formal data-sharing agreement with each county. Out of scope for our product posture.
- **Per-citizen authorization_code.** OAuth redirect flow we would walk end users through; returns a token that can *only* see that user's records. Irrelevant for bulk extraction.

## Recommendation

> **HTML scraping via the ACA citizen portal remains the primary strategy for bulk Accela public-data extraction. REST should be treated as an opportunistic fallback that only unlocks if and when an agency admin enables anonymous access; do not plan the v4 REST migration (formerly ACCELA-02) as a foundational P1 project.**

## Appendix A — Agency codes tested

- `POLKCO` — Polk County (valid; anonymous disabled)
- `CITRUS` — Citrus County (valid; anonymous disabled)
- `COLA` — Lake Alfred, Polk (valid; anonymous disabled)
- `BOCC` — Charlotte County (valid; anonymous disabled)
- `BREVARD` — Brevard County (valid; anonymous disabled). The alternate code `BREVARDFL` is invalid — the server returns `400 "Agency BREVARDFL does not exist"`.

## Appendix B — Reproducing the probe

```
python scripts/accela_rest_probe.py --agency POLKCO --permit BR-2026-2894
python scripts/accela_rest_probe.py --agency CITRUS --permit <any>
```

The script reads `ACCELA_APP_ID` and optionally `ACCELA_APP_SECRET` from `.env`. `ACCELA_APP_ID` is required; `ACCELA_APP_SECRET` is only needed to exercise the `client_credentials` token request. Output is written to `tmp/accela_probe_<agency>.md` (versioned `_v2`, `_v3`, ... on re-runs).
