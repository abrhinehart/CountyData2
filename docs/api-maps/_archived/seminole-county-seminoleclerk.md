# Seminole County FL -- Seminole Clerk Deed Portal API Map (CD2)

Last updated: 2026-04-14

## 1. Portal Overview

| Property | Value |
|----------|-------|
| Platform | **`unverified — needs validation`** — Seminole County Clerk of the Circuit Court & Comptroller public records |
| Clerk website | `https://www.seminoleclerk.org/` (WordPress / Yoast SEO v27.4) |
| Deed portal host | **Not identified by probe** — likely vendor-hosted off a different domain |
| Auth | Unknown |
| Protocol | Unknown |
| Adapter status | **`unverified — needs validation`** — no adapter for Seminole deeds exists in this repo |
| Registry status | **No `cd2:` row in `county-registry.yaml` for Seminole** — `seminole-fl` has only `bi: active` and `cr: partial_or_outlier` (L509-522) |

## 2. Probe (2026-04-14)

### Seminole Clerk main website (SSL-bypass required)

```
GET https://www.seminoleclerk.org/
-> SSL: CERTIFICATE_VERIFY_FAILED  (strict verification)
-> HTTP 200, 144,446 bytes, text/html  (with SSL verification disabled)
   <title>Home - Seminole County Clerk of the Circuit Court & Comptroller</title>
   WordPress-based site (Yoast SEO v27.4), article:modified_time 2026-03-31.
   Canonical: https://www.seminoleclerk.org/
   xmlrpc.php endpoint present — WordPress confirmed.

GET https://www.seminoleclerk.org/officialrecords
-> SSL: CERTIFICATE_VERIFY_FAILED  (strict verification)
-> HTTP 404 (with SSL verification disabled) — specific path not present.
```

### Negative-result probes (Seminole Clerk is NOT on these)

```
GET https://officialrecords.seminoleclerk.org/         -> URLError (DNS fail)
GET https://acclaim.seminoleclerk.org/acclaimweb/      -> URLError (DNS fail)
GET https://or.seminoleclerk.org/LandmarkWeb           -> URLError (DNS fail)
```

None of the expected deed-portal subdomain patterns resolve on `seminoleclerk.org`.

## 3. Query Capabilities

**`unverified — needs validation`.** No deed-portal API surface was located by probe. Discovery path:

1. Fetch `https://www.seminoleclerk.org/` with SSL verification disabled (cert chain issue).
2. Parse page markup for outbound links containing `record`, `deed`, `search`, `official`, or similar.
3. Follow external links to the actual vendor-hosted portal (likely on an AWS-hosted subdomain of a vendor SaaS platform — AcclaimWeb, LandmarkWeb, OnCore, MyPublicRecords, or similar).

## 4. Field Inventory

**Not available** — platform not yet identified.

## 5. What We Extract / What a Future Adapter Would Capture

Nothing currently. Any future adapter delivers the standard CD2 canonical row (grantor / grantee / record_date / doc_type / instrument / book / page / legal / consideration) once the platform is identified.

## 6. Bypass Method / Auth Posture

- **Certificate verification fails on `www.seminoleclerk.org`** under strict TLS (CERTIFICATE_VERIFY_FAILED: unable to get local issuer). Client code must either (a) pin the certificate chain manually or (b) disable verification for this one host only — standard Python `ssl.create_default_context()` with default trust store rejects it.
- With SSL verification off, the site responds HTTP 200.
- The actual deed portal (once found) is on a different host and may have a different certificate posture.

## 7. What We Extract vs What's Available

**Nothing extracted; platform unknown.**

## 8. Known Limitations and Quirks

1. **SSL cert issue on `www.seminoleclerk.org`.** The cert chain is incomplete as far as standard Python trust stores are concerned. Downstream scrapers need per-host exceptions or a trust-store supplement. Browsers may tolerate it differently (due to expanded AIA fetch / intermediate chain caching).
2. **No `cd2:` row in `county-registry.yaml` for Seminole.** Only `bi: active` and `cr: partial_or_outlier`. Adding CD2 would require a new registry row with platform identified.
3. **WordPress + Yoast SEO infrastructure** — the clerk's main site is a standard content CMS, not a records portal. The actual records search lives on an external vendor-hosted SaaS.
4. **All predictable vendor-portal subdomains DNS-fail.** No `officialrecords.`, `acclaim.`, `or.` on the `seminoleclerk.org` zone. The search portal hostname must be harvested from the main site's HTML.
5. **Seminole is distinct from `seminoleclerk.org`** domain ownership perspective — the `.org` TLD is the Clerk's, not the County's (which uses `.gov` — see `seminolecountyfl.gov`).
6. **`article:modified_time 2026-03-31`** in the page metadata indicates active site maintenance. The portal URL is likely current and discoverable via manual navigation.
7. **xmlrpc.php exposed** — WordPress back-end attack surface; not related to records-search capability. Purely an operational observation.
8. **No sign of Legistar / Accela / Tyler on the clerk surface** — Seminole Clerk is not currently known to use any of the standard FL recorder platforms. Remains to be discovered whether they are on AcclaimWeb (Harris Recording Solutions), OnCore, LandmarkWeb (Pioneer Technology Group), or something else.
9. **`officialrecords.seminoleclerk.org` would be the natural subdomain** and its DNS failure is significant — rules out a typical county-owned subdomain pattern.
10. **Follow-on task: parse `www.seminoleclerk.org` HTML** (144 KB, WordPress — navigation menus likely contain the canonical records-search link). This document's purpose is to prevent re-guessing subdomain patterns and to anchor the SSL cert issue as a known operational quirk.

Source of truth: live probes 2026-04-14 of `https://www.seminoleclerk.org/` (HTTP 200 with SSL verification disabled, 144,446 bytes — WordPress site), and DNS-failed probes of `officialrecords.seminoleclerk.org`, `acclaim.seminoleclerk.org/acclaimweb/`, `or.seminoleclerk.org/LandmarkWeb`. `county-registry.yaml` L509-522 (`seminole-fl.projects` — no `cd2` row). **Deed portal URL `unverified — needs validation`; platform `unverified — needs validation`.**
