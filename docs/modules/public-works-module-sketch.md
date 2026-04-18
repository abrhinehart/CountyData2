# Public Works Module Sketch

## Purpose

Track infrastructure projects that materially affect development readiness, absorption, or site selection.

## Core idea

This module should answer: what infrastructure is planned or underway, when will it deliver, who is paying for it, and which subdivisions or growth corridors does it help or hurt?

## Candidate entities

- `public_projects`
- `public_project_segments`
- `funding_sources`
- `project_documents`
- `impact_areas`

## Likely integrations

- `subdivisions.geom` for impact overlays
- `counties` and `jurisdictions` for ownership and governance
- `cr_entitlement_actions` for CIP approvals, utility expansions, and related agenda actions
- `pt_permits` for downstream construction acceleration signals

## First useful slice

1. Ingest a manually curated list of public works projects.
2. Classify by category, sponsor, and status.
3. Attach one or more counties, corridors, or subdivisions.
4. Expose a map and a sortable project watchlist.

## Open design questions

- What counts as "public works" for this product: utilities only, or roads, schools, parks, and drainage too?
- Do we need bond/CIP document parsing on day one, or is manual seeding enough for the sketch?
- Should impact be measured qualitatively first before modeling parcel-level effects?
