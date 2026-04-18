# Certificate of Occupancy Module Sketch

## Purpose

Stand up a module for certificate-of-occupancy tracking so finished product delivery can be monitored as a first-class signal rather than inferred indirectly from permits.

## Core idea

This module should answer: which structures received a CO, when they received it, which permit and subdivision they belong to, and where issuance is stalling?

## Candidate entities

- `certificate_of_occupancy_records`
- `certificate_document_links`
- `certificate_permit_links`
- `certificate_property_links`
- `certificate_event_log`

## Likely integrations

- `pt_permits` for upstream permit matching
- `subdivisions` for community rollups
- `builders` for cadence and throughput analysis
- `transactions` where ownership timing matters

## First useful slice

1. Ingest CO events manually or from permit-system exports.
2. Link them to permits and subdivisions.
3. Distinguish temporary vs final CO when available.
4. Surface builder and subdivision completion trends.

## Open design questions

- Do temporary COs represent progress, noise, or both?
- How important is document retrieval versus event-only tracking in the first version?
- Should this module feed BI or sales forecasting once it is mature?
