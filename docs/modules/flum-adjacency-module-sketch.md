# FLUM Adjacency Module Sketch

## Purpose

Create a module that explains a site's surrounding Future Land Use Map context in a way that supports entitlement strategy, acquisition filtering, and narrative-building.

## Core idea

This module should answer: what FLUM categories border or surround a site, how compatible are they with the proposed program, and how has that adjacency changed over time?

## Candidate entities

- `flum_sources`
- `flum_polygons`
- `adjacency_edges`
- `adjacency_scores`
- `adjacency_change_events`

## Likely integrations

- `subdivisions.geom` for project-level analysis
- `parcels.geom` and BI snapshots for finer site geometry
- `cr_entitlement_actions` for nearby FLUM amendment tracking
- future LDC/zoning work once those modules exist

## First useful slice

1. Load FLUM polygons for one pilot jurisdiction.
2. Compute which categories touch a selected subdivision or site polygon.
3. Summarize frontage/edge length or count by adjacent category.
4. Expose a map plus a short compatibility summary.

## Open design questions

- Is FLUM adjacency valuable on its own, or mainly as an input to entitlement scoring?
- Should adjacency be calculated from shared boundary length, nearest distance, or both?
- How much land-use taxonomy normalization is needed across counties before comparisons are useful?
