# Walton County FL -- CivicPlus AgendaCenter API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | CivicPlus AgendaCenter (CivicEngage) |
| Portal URL | `https://www.mywaltonfl.gov/AgendaCenter` |
| Protocol | Server-rendered HTML; documents are PDFs fetched from `AgendaCenter/ViewFile/...` |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction configs | `modules/commission/config/jurisdictions/FL/walton-county-bcc.yaml`, `-boa.yaml`, `-pz.yaml` (3 bodies) |
| **`scraping.platform`** | **`manual`** (all three YAMLs) |
| Registry status | Not specifically tracked under `cr` in `county-registry.yaml` (Walton's registry block at L358-377 lists only BI, CD2, PT for Walton) |

### Probe (2026-04-14)

```
GET https://www.mywaltonfl.gov/AgendaCenter
-> HTTP 200, body ~98.7 KB
<title>Agenda Center - Walton County - CivicEngage</title>
Category IDs visible in HTML: CID=1, CID=19, CID=118 (at least 3 categories)
Body text includes "Board of County Commissioners"
```

---

## 2. Bodies / Categories -- `platform: manual`

All three Walton commission YAMLs set **`scraping.platform: manual`**. This means there is **no auto-scraper** hitting this portal; agendas and minutes are tracked manually out-of-band and referenced into the pipeline by human-curated lists.

| Slug | Body | commission_type | `scraping.platform` | `base_url` |
|------|------|-----------------|----------------------|------------|
| `walton-county-bcc` | Walton County BCC | `bcc` | **`manual`** | `https://www.mywaltonfl.gov/AgendaCenter` |
| `walton-county-boa` | Walton County BOA | `board_of_adjustment` | **`manual`** | (omitted from YAML) |
| `walton-county-pz` | Walton County P&Z | `planning_board` | **`manual`** | `https://www.mywaltonfl.gov/AgendaCenter` |

```yaml
# walton-county-bcc.yaml (verbatim)
slug: walton-county-bcc
name: "Walton County BCC"
state: FL
county: Walton
municipality: null
commission_type: bcc
scraping:
  platform: manual
  base_url: "https://www.mywaltonfl.gov/AgendaCenter"
  document_formats: [pdf]
  has_duplicate_page_bug: false
detection_patterns:
  header_keywords:
    - "COUNTY COMMISSIONERS"
    - "BOARD OF COUNTY COMMISSIONERS"
  require_also:
    - "WALTON COUNTY"
  header_zone: wide
extraction_notes:
  - "County body -- cannot annex."
  - "Generic Florida county. Flag sparse items for review."
```

The `-boa.yaml` and `-pz.yaml` follow the same shape, except:

- `walton-county-boa.yaml`: **NO `base_url`** in its `scraping` block (just `platform: manual` + `document_formats`). Header keywords: `ADJUSTMENT`, `APPEALS`. Extraction note: "Board of Adjustment -- handles variances and appeals, outside core tracking scope."
- `walton-county-pz.yaml`: `base_url` is the same mywaltonfl.gov AgendaCenter. Header keywords: `PLANNING`. Extraction note: "Planning/advisory board -- recommendations only, not final authority on legislative items."

---

## 3. Portal Structure (observed, for future reference)

```
GET https://www.mywaltonfl.gov/AgendaCenter                             # landing
GET https://www.mywaltonfl.gov/AgendaCenter?CID={id}                    # per-category listing
GET https://www.mywaltonfl.gov/AgendaCenter/Search/?term=&CIDs={csv}    # federated search
GET https://www.mywaltonfl.gov/AgendaCenter/ViewFile/Agenda/_{id}       # PDF agenda
GET https://www.mywaltonfl.gov/AgendaCenter/ViewFile/Minutes/_{id}      # PDF minutes
```

Observed category IDs in the landing HTML (2026-04-14 probe): at least **1, 19, 118**. These are candidate IDs for BCC / BOA / P&Z mapping IF a future engineer decides to replace the `manual` platform with an automated scraper.

---

## 4. Why `manual`?

The commission-radar pipeline tracks dozens of FL counties. For Walton, the decision was made to handle AgendaCenter pulls out-of-band rather than automate them. Possible contributors:

1. CivicPlus does not expose REST / OData for AgendaCenter.
2. Walton's agenda publishing cadence or naming conventions may have been inconsistent enough to require human judgment.
3. A dedicated scraper for CivicPlus AgendaCenter is elsewhere in the codebase (reused by Santa Rosa, etc.) but NOT wired to Walton.

This is opposite of Santa Rosa (`santa-rosa-county-bcc.yaml`, `platform: civicplus`), which IS wired to the scraper but currently returns `zero_listing`.

---

## 5. Diff vs Santa Rosa CivicPlus (sibling CivicPlus county)

Both use CivicPlus AgendaCenter. Santa Rosa is wired to the automated adapter; Walton is `manual`.

| Attribute | Walton | Santa Rosa |
|-----------|--------|------------|
| Platform | CivicPlus AgendaCenter | CivicPlus AgendaCenter |
| Portal URL | `mywaltonfl.gov/AgendaCenter` | `santarosafl.gov/AgendaCenter` |
| `scraping.platform` | **`manual`** | `civicplus` |
| Bodies | 3 (BCC, BOA, P&Z) | 2 (BCC, combined Zoning Board) |
| Registry `cr` status | Not tracked | `zero_listing` |
| `category_id` on YAMLs | NO (manual; wouldn't be consulted anyway) | YES (1 and 2) |
| BOA `base_url` | Omitted entirely | n/a (ZB is combined, no BOA YAML) |
| Auto-scraper active | NO | YES (but returning zero listings) |
| Human curation | YES | NO |

---

## 6. Diff vs Okeechobee Granicus (CR peer with auto-scraper)

Useful to contrast with a granicus/automated county.

| Attribute | Walton (CivicPlus manual) | Okeechobee (Granicus auto) |
|-----------|----------------------------|-----------------------------|
| Platform | CivicPlus AgendaCenter | Granicus IQM2 |
| `scraping.platform` | `manual` | `granicus` |
| Automated fetch | NO | YES |
| Bodies configured | 3 (BCC, BOA, P&Z) | 1 (BCC) |
| Status | (manual workflow, not registry-tracked) | `pending_validation` |
| Portal URL pattern | `mywaltonfl.gov/AgendaCenter` | `{county}.iqm2.com/Citizens` |

---

## 7. What We Extract vs What's Available

| Data Category | Currently Extracted | Source | Notes |
|---------------|--------------------|---------|-------|
| Meeting agenda (PDF) | Manual (offline) | `AgendaCenter/ViewFile/Agenda/...` | Scraper does not run |
| Meeting minutes (PDF) | Manual (offline) | `AgendaCenter/ViewFile/Minutes/...` | Scraper does not run |
| Meeting date | Manual | Document filename / title | Humans curate |
| Body identification | Manual | Category per document | Humans tag |
| Agenda items | Manual | PDF body | Requires human reading or separate PDF ETL |
| Attachments | Manual | `ViewFile/Attachment/...` | Rarely exposed |
| Video | Manual | Usually a separate video-on-demand portal | Not currently tracked |
| Member roster | NO | -- | -- |
| RSS | Would be automatable | `RSS.aspx` | Not used |

---

## 8. Known Limitations and Quirks

1. **`scraping.platform: manual` in ALL THREE Walton YAMLs.** No automated scraper runs against `mywaltonfl.gov/AgendaCenter`. Do NOT claim live scraping in downstream docs.

2. **`walton-county-boa.yaml` omits `base_url` entirely.** While `walton-county-bcc.yaml` and `walton-county-pz.yaml` both set `base_url: "https://www.mywaltonfl.gov/AgendaCenter"`, the BOA YAML has just `platform: manual` and `document_formats: [pdf]` in its `scraping` block. This is benign for a manual workflow but would break any automated scraper expecting a `base_url`.

3. **Walton's registry `cr` slot is absent.** `county-registry.yaml` L358-377 lists only `bi`, `cd2`, `pt` for Walton. The CivicPlus CR track is tracked through the jurisdiction YAMLs alone, not as a registry `projects.cr` entry. This is because the workflow is manual and doesn't need an auto-tracked status.

4. **Three bodies all route to the same portal (in principle).** CID=1 appears to be BCC on the HTML landing page. CID=19 and CID=118 are candidates for other bodies. A future automation pass would need to identify which CID maps to BOA vs P&Z.

5. **CivicPlus does NOT expose REST / OData.** HTML-only. Any future automation must parse `AgendaCenter` HTML, same as Santa Rosa's scraper.

6. **Domain is `mywaltonfl.gov`** (with `my` prefix). Not `waltonfl.gov`, not `waltoncountyfl.gov`, not `co.walton.fl.us`. Easy to typo.

7. **`has_duplicate_page_bug: false`** on all three YAMLs.

8. **BCC note: "County body -- cannot annex."** Any annexation keyword hit on a BCC meeting is a false positive.

9. **BOA note: "outside core tracking scope."** Suggests the BOA was configured for completeness but the downstream pipeline may not weigh BOA items heavily.

10. **P&Z is advisory only.** "recommendations only, not final authority." Planning Commission items flag as advisory.

11. **Federated-search CIDs parameter is plural.** Even for a single category filter, the URL reads `CIDs={id}`.

12. **Any future promotion from `manual` to automated** would flip each YAML's `scraping.platform` to `civicplus` AND add `category_id` entries -- the same pattern already used by Santa Rosa.

**Source of truth:** `modules/commission/config/jurisdictions/FL/walton-county-bcc.yaml`, `walton-county-boa.yaml`, `walton-county-pz.yaml`, absence of `cr` entry in `county-registry.yaml` under `walton-fl.projects`, live probe of `https://www.mywaltonfl.gov/AgendaCenter` (HTTP 200, 98.7 KB, CivicEngage title, CID 1 / 19 / 118 visible).
