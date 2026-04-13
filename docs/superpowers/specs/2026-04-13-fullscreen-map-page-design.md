# Full-Screen Map Page — Design Spec

## Purpose

Replace the Google Earth + PowerPoint workflow with a native in-app map view. Subdivision polygons styled by builder, with hover summaries and click-through detail panels. All data live from existing APIs.

## Route

`/map` — added to the app's main navigation.

## Layout

- Satellite tile map (Esri World Imagery or similar free provider) filling the viewport
- Thin filter bar pinned to the top of the map
- Collapsible side panel (right edge) for click-detail view — slides in over the map, doesn't navigate away

## Polygon Styling

### Builder color system

- Top ~10-15 national builders get manually assigned brand colors (stored in a frontend config map keyed by builder ID)
- All other builders share a single neutral style (gray fill, dashed outline)
- Colors are semi-transparent fills (~0.3 opacity) with solid-color outlines so the satellite imagery stays visible

### Single-builder subdivisions

- Solid fill in the builder's assigned color
- Solid outline in a darker shade of the same color

### Multi-builder subdivisions

- Quartered or striped fill proportional to each builder's lot share
- Each segment in that builder's color
- If all builders in the subdivision are "other" (no brand color), use the neutral gray
- Technical approach: Leaflet doesn't support multi-color fills natively. Use SVG `<pattern>` definitions (stripes or quadrants) applied as Leaflet path `fillPattern`. Libraries like `leaflet-pattern` or custom SVG defs can handle this.

### Grace-period subdivisions (0 current builder lots)

- Dimmed/dashed outline, no fill or very low opacity fill
- Still hoverable and clickable

## Hover Tooltip

Appears on polygon hover. Lightweight, no interaction needed.

Contents:
- Subdivision name (bold)
- Total builder lots (e.g. "44 lots")
- Builder breakdown: each builder name + lot count (e.g. "DR Horton: 44")

Tooltip disappears on mouse-out. Positioned near cursor, does not obscure the polygon.

## Click Detail Panel

Slides in from the right side of the viewport on polygon click. Does not navigate away from the map. Closeable via X button or clicking elsewhere on the map.

Contents:
- Subdivision name + county (header)
- Builder lot breakdown (name, lot count, lot price range/avg per builder)
- Monthly sales velocity (lots sold per month, last 6-12 months)
- Commission actions (if any exist for this subdivision) — date, type, outcome
- Link to full subdivision detail page (`/subdivisions/:id`)

Data fetched on click from existing endpoints:
- `getParcelsBySubdivision(id)` — builder lots, price data
- `getSalesBySubdivision(canonicalName)` — sales velocity
- `getCommissionRoster(id)` — commission actions

## Filters (Top Bar)

Thin horizontal bar overlaying the top of the map.

- **County** — single-select dropdown (defaults to "Bay")
- **Builder** — multi-select, filters to subdivisions where selected builder(s) have lots
- **Toggle layers** — checkboxes for optional pin layers:
  - Permit locations (future, data exists)
  - Transaction locations (future, data exists)

Filters apply to polygon visibility — filtered-out polygons are hidden, not dimmed.

## Data Sources

One new backend field required; all endpoints already exist.

- Subdivision list + geometry: `GET /api/inventory/subdivisions` (has `has_geometry`, `builder_lot_count`, `distinct_builder_count`)
  - **New field needed:** `builders: [{builder_id, builder_name, lot_count}]` — per-builder breakdown for hover tooltips and polygon coloring. Added to the existing endpoint response, computed from the same parcel join.
- Individual geometry: `GET /api/subdivisions/:id` (returns `geojson` field)
- Parcels for click panel: `GET /api/inventory/parcels?subdivision_id=X`
- Sales for click panel: `GET /api/transactions?subdivision=X`
- Commission for click panel: `GET /api/commission/roster/:id`
- Builder list (for filter + color mapping): `GET /api/inventory/builders`

### Geometry loading strategy

The subdivision list endpoint does not return full GeoJSON. Individual geometries must be fetched per subdivision. For the initial load:
- Fetch the filtered subdivision list (builder_active_only=true, county filter)
- Batch-fetch geometries for all visible subdivisions (parallel requests or a new batch endpoint if needed)
- Cache in TanStack Query by subdivision ID

If the number of subdivisions per county with geometry is large (>100), consider a new backend endpoint that returns lightweight GeoJSON FeatureCollection for a county in one request. Evaluate during implementation.

## New Files

- `ui/src/pages/MapPage.tsx` — main page component (map, filter bar, side panel)
- `ui/src/config/builderColors.ts` — brand color mapping for top builders (builder ID -> hex color)

## Existing Infrastructure

- Leaflet is already in the project (used by `SubdivisionMap` component)
- React 19 + TanStack Query for data fetching
- Tailwind v4 for styling
- All API functions already exist in `ui/src/api.ts`

## Out of Scope

- Per-lot pins on the map (future consideration)
- Editing subdivision geometry from the map
- Offline/export functionality (the map replaces the Google Earth workflow)
- Builder color stored in the database (frontend config is sufficient for ~15 entries)
