# Madison County AL -- Accela Meeting Portal (IQM2) API Map (CR)

Last updated: 2026-04-14

## 1. Platform Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Madison County Commission (Huntsville, AL metro) |
| Platform | IQM2 / Accela Meeting Portal (MinuteTraq heritage) |
| Candidate public URL | `https://madisoncountyal.iqm2.com/Citizens/` |
| Auth | Anonymous public read |
| Protocol | ASP.NET Web Forms (no REST / OData API) |
| Registry entry | **Not present** in `county-registry.yaml` (`madison-al` has no `cr:` block) |
| CR adapter | None -- no commission-radar surface configured for Madison AL |

Madison County's IQM2 tenant **exists but currently returns `ErrorPage.aspx`** for the Citizens root. This typically means the tenant is provisioned or was previously provisioned but is not serving public content at probe time. It is the closest platform match among the common Granicus / Legistar / IQM2 / CivicClerk / CivicWeb options the CR project consumes; no sibling platform responded with a live Madison AL instance.

## 2. Probe (2026-04-14)

```
GET https://madisoncountyal.iqm2.com/Citizens/Default.aspx
-> HTTP 200, body is /Citizens/ErrorPage.aspx  (IQM2 "Accela Meeting Portal" -- empty error page, no meeting list)

GET https://madisoncountyal.legistar.com/
-> HTTP 200 ("Invalid parameters!")
GET https://webapi.legistar.com/v1/madisoncountyal/bodies
-> HTTP 500  "LegistarConnectionString setting is not set up in InSite for client: madisoncountyal"
(Subdomain exists but no Legistar connection string is configured -- not a live Legistar tenant.)

GET https://madisoncountyal.granicus.com/
-> HTTP 404 (core/error/NotFound.aspx -- no Granicus tenant)

GET https://madisoncountyal.api.civicclerk.com/v1/Meetings
-> HTTP 404 (no CivicClerk tenant)

GET https://www.madisoncountyal.gov/
-> HTTP 403 Access Denied (Akamai edgesuite shield; rules block curl UAs)
```

The county's own website is shielded by Akamai and rejected our probe. Without being able to read the commission page, **the live agenda-publishing platform cannot be confirmed from the outside.** IQM2 subdomain existence is the single non-404 signal, which is suggestive but not conclusive.

**unverified -- needs validation** via a browser session that clears the Akamai challenge, or direct inspection of `www.madisoncountyal.gov/government/county-commission`. If the commission page instead embeds a Granicus video player or links to a non-subdomained agenda portal, the platform identification may be wrong.

## 3. Search / Query Capabilities

If IQM2 is indeed the live platform, the CR integration would use the standard IQM2 Citizens-side endpoints:

- Meeting list: `/Citizens/Detail_Meeting.aspx?ID={MeetingID}`
- Calendar: `/Citizens/Calendar.aspx`
- Document viewer: `/Citizens/SplitView.aspx?Mode=Agenda&MeetingID={MeetingID}`

IQM2 has no REST/OData API; scraping is HTML-parse only. This matches the Accela CR adapter pattern used elsewhere in the repo.

If the platform turns out to be something else, this section will need to be rewritten against the live URL.

## 4. Field Inventory

Expected (pending platform confirmation):

- Meeting ID, date, body, title.
- Agenda items per meeting (item number, title, type, body text).
- Attachments per item (PDF URLs).
- Vote roll-ups (yes/no/abstain) where published.

## 5. What We Extract / What a Future Adapter Would Capture

**We currently extract nothing.** No CR jurisdiction config exists for Madison AL. A future adapter would pick one of the existing CR platform adapters (Accela/IQM2, Legistar, Granicus, CivicClerk, CivicPlus) based on the confirmed live platform, then populate the standard `cr_jurisdiction_config` row + a `modules/commission/config/jurisdictions/AL/madison-county/` YAML.

## 6. Auth Posture / Bypass Method

Anonymous public read (IQM2 Citizens side is public by design). No auth anticipated. County website Akamai challenge does not gate the IQM2 subdomain directly.

## 7. What We Extract vs What's Available

Zero extraction currently -- no CR config for Madison AL. Full surface pending platform confirmation.

## 8. Known Limitations and Quirks

- IQM2 tenant returns `ErrorPage.aspx` at probe time -- may mean the tenant is stubbed, decommissioned, or the Citizens-side content is not provisioned. **unverified -- needs validation.**
- Main county website is shielded by Akamai; automated probing cannot read the commission page to confirm what agenda platform (if any) is embedded there. DNS existence of the IQM2 subdomain is the best signal we have from an outside-in probe.
- Legistar subdomain exists (`madisoncountyal.legistar.com`) but the Legistar API returns "LegistarConnectionString setting is not set up" -- the subdomain is a placeholder, not a live Legistar tenant.
- If the live platform turns out to differ from IQM2 (e.g., a newer Granicus GovDelivery deployment or a Civic Plus CMS-embedded PDF archive), this map should be re-titled and rewritten. File slug `madison-county-commission.md` is deliberately platform-neutral to minimize rename churn.
- Registry quirks note "Non-disclosure state" (deeds) -- **not relevant** to CR, which captures agendas and votes, not consideration.

Source of truth: `county-registry.yaml` (madison-al L544-570; no cr: block), live probes to `madisoncountyal.iqm2.com`, `madisoncountyal.legistar.com`, `madisoncountyal.granicus.com`, `madisoncountyal.api.civicclerk.com`, `www.madisoncountyal.gov`.
