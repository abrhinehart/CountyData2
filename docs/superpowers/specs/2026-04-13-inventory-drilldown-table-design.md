# Inventory Drill-Down Lots Table — Design Spec

## Purpose

Replace the flat "Lots by County" bar chart on the Inventory page with an interactive hierarchical table: State → County → Builder → Subdivision, with a parcel type filter.

## Scope

This spec covers only the drill-down lots table. The builders table redesign and snapshot runner improvements are separate sub-projects.

## Hierarchy

| Level | Click action | Columns |
|-------|-------------|---------|
| **State** (top) | Expands to counties | State name, lot count |
| **County** | Expands to builders | County name, lot count |
| **Builder** | Expands to subdivisions | Builder name, lot count |
| **Subdivision** (bottom) | Opens detail page in new tab | Subdivision name, lot count |

Each level is an expandable row. Only one branch is expanded at a time per level (clicking a different state collapses the previous one). A breadcrumb trail at the top shows the current drill path (e.g. "All States > FL > Bay > DR Horton") with each segment clickable to navigate back up.

## Parcel Type Filter

Toggle buttons above the table: **Lots** (default) | **Raw** | **HOA** | **Other**

Maps to backend `parcel_class` values:
- Lots → `lot`
- Raw → `tract`
- HOA → `common_area`
- Other → `other`

Changing the filter refreshes all counts at every level. Only one parcel type active at a time.

## Data Sources

No new backend endpoints needed. All existing endpoints support the required filters.

### State + County level

`GET /api/inventory/inventory?parcel_class=lot&entity_type=builder&entity_type=developer&entity_type=land_banker&entity_type=btr`

Returns `CountyInventory[]` — each has `county_id`, `county` (name), `total`, and `builders[]` array. The County model has a `state` field. To get state for each county, cross-reference with `GET /api/inventory/counties` which returns `CountyOut[]` including `state`.

Frontend groups counties by state to build the State level.

### Builder level (within a county)

Already included in the `CountyInventory.builders` array from the same response above. No additional fetch needed.

### Subdivision level (within a county + builder)

`GET /api/inventory/inventory/{county_id}?parcel_class=lot&entity_type=builder&entity_type=developer&entity_type=land_banker&entity_type=btr&builder_id={builder_id}`

Returns `CountyDetail` with `subdivisions[]` — each has `subdivision_id`, `subdivision` (name), `total`, and `builders[]`. Filter client-side to the selected builder's subdivisions.

Fetched on demand when a builder row is expanded.

## UI Component

Replaces the current "Lots by County" `<div>` section in `InventoryPage.tsx`. Implemented as a `DrillDownTable` component.

### Visual design

- Clean table rows with indentation per level (0px state, 16px county, 32px builder, 48px subdivision)
- Expand/collapse chevron on rows that have children
- Active/expanded row gets a subtle highlight
- Lot counts right-aligned, tabular-nums
- Subdivision rows link out (new tab icon)
- Breadcrumb bar above the table for quick navigation

### Loading states

- State + County level: loaded on mount (single query)
- Builder level: already in the county data (no additional fetch)
- Subdivision level: fetched on demand when builder row is clicked, with inline "Loading..." indicator

## Files

- Modify: `ui/src/pages/InventoryPage.tsx` — replace the bar chart section with the new DrillDownTable
- Create: `ui/src/components/DrillDownTable.tsx` — the hierarchical table component
- Modify: `ui/src/api.ts` — may need to add `getInventoryDetail(countyId, params)` if not already present
- Modify: `ui/src/types.ts` — add any missing types for the county detail response

## Out of Scope

- Builder type filter (separate sub-project: builders table redesign)
- Snapshot runner improvements (separate sub-project)
- Changing the parcel classification logic itself (confirmed as good)
