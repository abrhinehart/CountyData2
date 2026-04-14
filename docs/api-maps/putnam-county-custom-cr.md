# Putnam County FL -- Custom / Website (No Public API) API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Platform | **Custom / website** (no standard meeting-management platform detected) |
| Portal URL | `https://www.putnam-fl.gov` (redirected from `main.putnam-fl.com`) |
| Adapter | **None** (no auto-scraper possible from the current surface) |
| Protocol | HTTPS HTML; agendas and minutes served from the county website directly |
| Auth | Anonymous |
| Document format | PDF (agendas + minutes) |
| Jurisdiction config | **NONE** -- there is NO `putnam-county-bcc.yaml` / `-pz.yaml` / `-boa.yaml` under `modules/commission/config/jurisdictions/FL/` |
| Registry status | `research_done` (per `putnam-fl.projects.cr`, `county-registry.yaml` L325-336) |
| Live streaming | YouTube and Facebook |
| Public comments | `BOCCmeetingcomments@putnam-fl.com` |

### Probe (2026-04-14)

```
GET https://www.putnam-fl.gov
-> HTTP 200, body ~310 KB
Generic county website (not a dedicated meeting portal).

GET https://apps.putnam-fl.com/bocc/
-> HTTP 403, 199 bytes   (likely internal-only)
```

---

## 2. Why This Is a Manual / Custom Surface

Per the registry notes:

> "No Legistar, CivicClerk, NovusAgenda, or CivicPlus detected. Minutes & Agendas served from putnam-fl.gov website (redirected from main.putnam-fl.com). BCC meets 2nd and 4th Tuesdays at 9 AM, Government Complex Suite 100, 2509 Crill Ave, Palatka. Live streamed on YouTube and Facebook. Public comments via BOCCmeetingcomments@putnam-fl.com. apps.putnam-fl.com/bocc/ returned 403 (may require internal access). Planning Commission and Zoning Board of Adjustment also active; contact (386) 329-0491."

There is no Granicus, Legistar, CivicPlus, CivicClerk, or NovusAgenda tenant for Putnam -- every standard meeting-portal vendor has been checked and is absent. Agendas and minutes for BCC, Planning Commission, and Zoning Board of Adjustment are hosted directly on the county website.

---

## 3. Meeting Cadence

| Body | Cadence | Location |
|------|---------|----------|
| BCC | 2nd and 4th Tuesdays at 9 AM | Government Complex Suite 100, 2509 Crill Ave, Palatka |
| Planning Commission | Active (cadence per `(386) 329-0491` contact) | -- |
| Zoning Board of Adjustment | Active (cadence per `(386) 329-0491` contact) | -- |

Videos are streamed on YouTube and Facebook; links presumably live on the county website itself.

---

## 4. No Jurisdiction YAML Exists

**Gap flagged (do NOT create):** There is currently no jurisdiction YAML for Putnam County under `modules/commission/config/jurisdictions/FL/`. The `FL/` directory contains:

```
bay-county-* / citrus-county-* / escambia-county-* /
okeechobee-county-* / polk-county-* /
santa-rosa-county-* (BCC + ZB) /
okaloosa-county-* (BCC + BOA + P&Z) /
walton-county-* (BCC + BOA + P&Z, all platform: manual)
```

Putnam is absent. A future engineer onboarding Putnam CR would need to:

1. Identify where on `www.putnam-fl.gov` the agenda/minutes PDFs live (likely a dedicated "Meetings" or "Agendas" subpage).
2. Decide whether to use `platform: manual` (like Walton) or write a custom scraper for the county website (less reusable).
3. Create `putnam-county-bcc.yaml` (+ `-pz.yaml` + `-boa.yaml` if Planning Commission and ZBA are to be tracked).

**Per the Planner's directive, this doc does NOT create the YAML -- it only flags the gap.**

---

## 5. Manual Workflow (current)

Until an adapter or jurisdiction YAML exists:

1. Human operator visits `https://www.putnam-fl.gov` and navigates to the agenda/minutes section.
2. Downloads PDFs manually.
3. References them out-of-band into downstream analysis pipelines.

This is the same mode as Walton County CR (`walton-county-civicplus.md`), but without even a YAML-level config to anchor the workflow.

---

## 6. Diff vs Walton CivicPlus `manual` + Okeechobee Granicus `pending_validation`

Putnam is the most bare-bones CR surface in the FL doc set.

| Attribute | Putnam (custom) | Walton (CivicPlus manual) | Okeechobee (Granicus auto) |
|-----------|------------------|----------------------------|-----------------------------|
| Standard platform | **NONE** | CivicPlus AgendaCenter | Granicus IQM2 |
| Jurisdiction YAML(s) | **NONE (gap)** | 3 (BCC, BOA, P&Z) | 1 (BCC) |
| `scraping.platform` | n/a (no YAML) | `manual` | `granicus` |
| Auto-scraper | NO | NO | YES |
| Manual workflow | YES | YES | NO |
| Registry `cr` status | `research_done` | (not tracked under Walton's `cr`) | `pending_validation` |
| Portal URL pattern | `www.putnam-fl.gov` (generic county site) | `mywaltonfl.gov/AgendaCenter` | `okeechobeecountyfl.iqm2.com/Citizens` |
| Streaming | YouTube + Facebook | Per county | Per county |
| Contact (discovery) | `(386) 329-0491` | n/a | n/a |

---

## 7. Endpoints That Are NOT Available

For clarity, negative findings from the registry research:

| Vendor check | Result |
|--------------|--------|
| Legistar OData / `legistar.com` tenant | NO |
| CivicClerk tenant | NO |
| NovusAgenda tenant | NO |
| CivicPlus AgendaCenter | NO |
| Granicus IQM2 / Legistar-v2 (govt subdomain pattern) | NO |
| `apps.putnam-fl.com/bocc/` (internal apps root) | 403 (internal only) |

---

## 8. Known Limitations and Quirks

1. **No standard platform.** Unlike every other FL county in this doc set, Putnam does not use a recognized meeting-management platform (Legistar, Granicus IQM2, CivicPlus, CivicClerk, NovusAgenda). Agendas and minutes are hosted directly on the county website.

2. **NO jurisdiction YAML exists for Putnam.** The gap is deliberate -- per Planner's directive, this doc flags the absence but does not create `putnam-county-bcc.yaml` (or pz/boa). Any future CR work must first author a YAML.

3. **`apps.putnam-fl.com/bocc/` returns 403.** The BOCC apps subdomain root is not publicly accessible. Do not treat it as a discovery surface; it likely requires internal county-network credentials. Sub-paths under it (`/bocc/pds/pds_inq/`, `/bocc/pds/Permits.html`) ARE publicly accessible (see `putnam-county-citizenserve.md` for the PT surfaces), but the BOCC root itself is blocked.

4. **Registry redirect from `main.putnam-fl.com` to `www.putnam-fl.gov`.** Older references to `main.putnam-fl.com` should be updated to `www.putnam-fl.gov`.

5. **BCC cadence: 2nd and 4th Tuesdays at 9 AM.** Fixed twice-monthly schedule (not the 1st/3rd pattern common elsewhere). Consistent meeting cadence simplifies any future automation's date-expectation model.

6. **Public comments via email (`BOCCmeetingcomments@putnam-fl.com`).** Not through an online form. A scraper that wants to track public comments has no programmatic hook.

7. **Livestreaming on YouTube + Facebook, not Granicus/Swagit.** No ASX/M3U8 stream catalog is exposed.

8. **Planning Commission + Zoning Board of Adjustment are active** but their publication cadence requires calling `(386) 329-0491` for discovery. None of their agendas are indexed in the registry.

9. **No `modules/commission/...` code path currently touches Putnam.** Any future engineer will need to decide: (a) use the generic `manual` pattern (like Walton), or (b) write a Putnam-specific custom scraper for `www.putnam-fl.gov`.

10. **Registry status `research_done` is the correct label.** Everything that can be discovered by external probing has been discovered; the only next step is to commit a YAML and/or write a scraper.

11. **No per-meeting video URLs are stable.** YouTube and Facebook videos use platform-generated IDs; unless the county publishes a canonical meetings page with embed links, tracking video provenance requires separate logic.

12. **Consider merging this work with the PT surfaces.** Putnam Citizenserve (PT) and the legacy `apps.putnam-fl.com/bocc/pds/` surfaces are already documented in `putnam-county-citizenserve.md`. Any unified "Putnam county website scraper" engineered in the future would likely overlap with that PT work.

**Source of truth:** `county-registry.yaml` (`putnam-fl.projects.cr`, L325-336 -- full notes including YouTube/Facebook streaming, public-comments email, `(386) 329-0491` contact, and the 403 on `apps.putnam-fl.com/bocc/`), absence of any Putnam YAML under `modules/commission/config/jurisdictions/FL/`, live probes of `https://www.putnam-fl.gov` (HTTP 200) and `https://apps.putnam-fl.com/bocc/` (HTTP 403).
