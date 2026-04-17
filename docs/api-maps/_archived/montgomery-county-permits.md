# Montgomery County AL -- Building Permits (No Online Portal) API Map (PT)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Jurisdiction | Montgomery County Engineering Department (unincorporated county) |
| Online portal | **None identified at probe time** |
| Program page | `https://www.mc-ala.org/departments/engineering/building-permits` |
| Fallback | In-person / phone / paper application process |
| Registry entry | `county-registry.yaml` L600-613 has BI only; **no `pt:` block** |

Montgomery County (the unincorporated county portion) does **not** appear to operate a self-service online building-permit search portal. All probes for common vendor-subdomain patterns (Accela ACA, Tyler EnerGov, CityView, CitizenServe) returned no match on any `montgomery*al` or `*mc-ala` naming. The county engineering department's building-permits page references neither Accela, Tyler, CityView, nor CitizenServe.

**Out-of-scope: City of Montgomery building permits.** The City of Montgomery is the state capital and the dominant population center of the county; the City runs its own permit office (Inspections Department). City permits are **explicitly out of scope** for this county-level doc. Likewise smaller Montgomery County municipalities (Pike Road, etc.) have their own city-level processes out of scope here.

## 2. Probe (2026-04-14)

```
GET https://www.mc-ala.org/
-> HTTP 403  (Akamai edgesuite shield)

GET https://web.archive.org/web/2025/https://www.mc-ala.org/departments/engineering/building-permits
-> HTTP 200  (Vision CMS page; no permit-portal iframe or external-vendor link detected in the body)

Platform subdomain probes:
- https://aca-prod.accela.com/{mgm,montgomeryal,mc-ala}/...           -> HTTP 404 / no tenant
- https://montgomery-al.iqm2.com/...                                  -> ErrorPage.aspx (no content)
- https://www5.citizenserve.com/Portal/...(search "Montgomery AL")    -> no matching installation
- https://*.selfservice.tyler* / *.energov / *.municipalonlinepayments -> no matches
```

Result: no publicly discoverable self-service permit portal for Montgomery County unincorporated. The in-person/paper process at the Engineering Department appears to be the current workflow.

**unverified -- needs validation.** The absence of a public online portal is inferred from probe misses plus the absence of a portal link on the (archived) building-permits page. It is possible that an unpublicized internal portal exists for contractors with accounts, or that a portal is launching post-probe. A direct inquiry with Montgomery County Engineering would confirm definitively.

## 3. Search / Query Capabilities

None online. Permit records must be obtained via open-records request to the Engineering Department.

## 4. Field Inventory

Not applicable -- no online source from which to inventory fields.

If the county later publishes a portal, expected fields would follow whichever vendor they adopt (Accela: CAP records; Tyler: Permit + Inspection modules; CityView: Permit Locator; CitizenServe: Portal permit search).

## 5. What We Extract / What a Future Adapter Would Capture

Currently extracted: **nothing.** No PT adapter exists and no target surface is available to build one against. Until a county-level online portal emerges, the only path to structured Montgomery permit data is:

1. Periodic open-records-request extractions (manual CSV delivery).
2. If/when a vendor portal launches, revisit this doc and build the adapter.

## 6. Auth Posture / Bypass Method

Not applicable online. Paper/in-person only.

## 7. What We Extract vs What's Available

Nothing extracted; nothing directly available online to extract. Any future availability depends on the county's platform decisions.

## 8. Known Limitations and Quirks

- **No online permit portal identified at probe time** -- this is the primary limitation.
- **City of Montgomery permits are OUT OF SCOPE** for this county-level CountyData2 PT doc. City of Montgomery Inspections Department runs a separate city-level program; any online City presence is not inventoried here.
- Montgomery County main site (`www.mc-ala.org`) is Akamai-shielded against curl UAs -- direct content reads required the Web Archive during this probe.
- If a future probe finds the Engineering Department has launched a vendor portal (Accela / Tyler / CitizenServe), this doc should be rewritten around that platform.
- Non-disclosure state applies to deeds (not permits).

Source of truth: `county-registry.yaml` (montgomery-al L600-613, BI-only), archived Montgomery Engineering Building Permits page (web.archive.org capture of `www.mc-ala.org/departments/engineering/building-permits`), negative platform subdomain probes.
