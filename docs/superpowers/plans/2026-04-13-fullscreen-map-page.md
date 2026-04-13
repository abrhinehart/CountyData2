# Full-Screen Map Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an interactive full-screen satellite map page showing builder-active subdivision polygons, styled by builder, with hover tooltips and a click-detail side panel.

**Architecture:** New `/map` route with a fullscreen Leaflet map on Esri satellite tiles. A new batch GeoJSON backend endpoint returns all subdivision geometries + per-builder lot breakdowns for a county in a single request. Frontend config maps top builders to brand colors. Hover shows builder/lot summary; click opens a side panel with sales velocity and commission data fetched on demand.

**Tech Stack:** Leaflet 1.9 (already installed), React 19, TanStack Query, Tailwind v4, FastAPI + PostGIS (ST_AsGeoJSON). No new npm packages needed — SVG pattern fills use raw Leaflet SVG path options.

**Spec:** `docs/superpowers/specs/2026-04-13-fullscreen-map-page-design.md`

---

### Task 1: Batch GeoJSON Backend Endpoint

**Files:**
- Modify: `modules/inventory/routers/subdivisions.py`
- Modify: `modules/inventory/schemas/subdivision.py`

This endpoint returns a GeoJSON FeatureCollection for all builder-active subdivisions in a county, with per-builder lot breakdowns in each feature's properties. One request per county instead of 300+ individual fetches.

- [ ] **Step 1: Add schema for builder breakdown and GeoJSON feature response**

In `modules/inventory/schemas/subdivision.py`, add:

```python
class SubdivisionBuilderSummary(BaseModel):
    builder_id: int
    builder_name: str
    lot_count: int

class SubdivisionGeoFeature(BaseModel):
    """One feature in the map GeoJSON response."""
    id: int
    name: str
    county_id: int
    county_name: str
    builder_lot_count: int
    distinct_builder_count: int
    builders: list[SubdivisionBuilderSummary]
    geojson: dict  # GeoJSON Geometry object
```

- [ ] **Step 2: Add the batch endpoint**

In `modules/inventory/routers/subdivisions.py`, add a new route below the existing `list_subdivisions`:

```python
@router.get("/geojson", response_model=list[SubdivisionGeoFeature])
def get_subdivision_geojson(
    county_id: int | None = None,
    builder_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Return builder-active subdivisions with geometry and per-builder lot breakdown.

    Used by the map page to load all polygons for a county in one request.
    Only returns subdivisions that have geometry AND builder activity.
    """
    from geoalchemy2.shape import to_shape

    cutoff = datetime.now(timezone.utc) - timedelta(days=5 * 365)

    # Get builder-active subdivision IDs (same logic as list_subdivisions)
    ba_q = (
        db.query(Parcel.subdivision_id)
        .filter(
            Parcel.subdivision_id.isnot(None),
            Parcel.builder_id.isnot(None),
            or_(
                Parcel.is_active == True,  # noqa: E712
                Parcel.last_seen >= cutoff,
            ),
        )
        .distinct()
    )
    if county_id is not None:
        ba_q = ba_q.filter(Parcel.county_id == county_id)
    builder_active_ids = {row[0] for row in ba_q.all()}

    if not builder_active_ids:
        return []

    # Fetch subdivisions with geometry
    subs = (
        db.query(Subdivision.id, Subdivision.name, Subdivision.county_id,
                 County.name.label("county_name"), Subdivision.geom)
        .join(County, County.id == Subdivision.county_id)
        .filter(
            Subdivision.id.in_(builder_active_ids),
            Subdivision.geom.isnot(None),
        )
    )
    if county_id is not None:
        subs = subs.filter(Subdivision.county_id == county_id)

    sub_rows = subs.all()
    sub_ids = [r.id for r in sub_rows]

    if not sub_ids:
        return []

    # Per-builder lot counts for these subdivisions
    builder_lots = (
        db.query(
            Parcel.subdivision_id,
            Parcel.builder_id,
            Builder.canonical_name.label("builder_name"),
            func.count(Parcel.id).label("lot_count"),
        )
        .join(Builder, Builder.id == Parcel.builder_id)
        .filter(
            Parcel.subdivision_id.in_(sub_ids),
            Parcel.builder_id.isnot(None),
            Parcel.is_active == True,  # noqa: E712
        )
        .group_by(Parcel.subdivision_id, Parcel.builder_id, Builder.canonical_name)
        .all()
    )

    # Group builder data by subdivision
    from collections import defaultdict
    builders_by_sub: dict[int, list] = defaultdict(list)
    for row in builder_lots:
        builders_by_sub[row.subdivision_id].append(
            SubdivisionBuilderSummary(
                builder_id=row.builder_id,
                builder_name=row.builder_name,
                lot_count=row.lot_count,
            )
        )

    # Optional: filter to specific builder
    if builder_id is not None:
        sub_ids_with_builder = {
            sub_id for sub_id, builders in builders_by_sub.items()
            if any(b.builder_id == builder_id for b in builders)
        }
    else:
        sub_ids_with_builder = None

    # Build response
    features = []
    for row in sub_rows:
        if sub_ids_with_builder is not None and row.id not in sub_ids_with_builder:
            continue
        builders = sorted(builders_by_sub.get(row.id, []), key=lambda b: -b.lot_count)
        geom_shape = to_shape(row.geom)
        features.append(SubdivisionGeoFeature(
            id=row.id,
            name=row.name,
            county_id=row.county_id,
            county_name=row.county_name,
            builder_lot_count=sum(b.lot_count for b in builders),
            distinct_builder_count=len(builders),
            builders=builders,
            geojson=mapping(geom_shape),
        ))

    return features
```

Add `Builder` to the imports from `modules.inventory.models` at the top of the file (it's not imported yet), and add the new schema imports.

- [ ] **Step 3: Verify backend compiles and endpoint returns data**

Run:
```bash
python -c "from modules.inventory.routers.subdivisions import router; print('OK')"
curl -s "http://localhost:1460/api/inventory/subdivisions/geojson?county_id=3" | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} features'); print(d[0]['name'], d[0]['builders'][:2]) if d else print('empty')"
```

Expected: Features with geometry and builders array.

- [ ] **Step 4: Add frontend API function and types**

In `ui/src/types.ts`, add:

```typescript
export interface SubdivisionBuilderSummary {
  builder_id: number;
  builder_name: string;
  lot_count: number;
}

export interface SubdivisionGeoFeature {
  id: number;
  name: string;
  county_id: number;
  county_name: string;
  builder_lot_count: number;
  distinct_builder_count: number;
  builders: SubdivisionBuilderSummary[];
  geojson: GeoJSON.Geometry;
}
```

In `ui/src/api.ts`, add:

```typescript
export async function getSubdivisionGeoJSON(
  params: { county_id?: number; builder_id?: number }
): Promise<SubdivisionGeoFeature[]> {
  return checked(await fetch(`${BASE}/inventory/subdivisions/geojson${qs(params)}`));
}
```

- [ ] **Step 5: Commit**

```bash
git add modules/inventory/routers/subdivisions.py modules/inventory/schemas/subdivision.py ui/src/types.ts ui/src/api.ts
git commit -m "feat: add batch GeoJSON endpoint for map page"
```

---

### Task 2: Builder Brand Color Config

**Files:**
- Create: `ui/src/config/builderColors.ts`

A static map from builder ID to brand hex color for the top national builders. All others fall through to a default gray.

- [ ] **Step 1: Create the color config file**

Create `ui/src/config/builderColors.ts`:

```typescript
/** Brand colors for top national builders. Keyed by builder ID. */
const BUILDER_BRAND_COLORS: Record<number, { fill: string; stroke: string; label: string }> = {
  1:   { fill: "#D64309", stroke: "#A33307", label: "DR Horton" },       // DR Horton orange
  3:   { fill: "#003DA5", stroke: "#002B75", label: "Lennar" },          // Lennar blue
  12:  { fill: "#00843D", stroke: "#005C2A", label: "Pulte" },           // Pulte green
  11:  { fill: "#E4002B", stroke: "#B30022", label: "Meritage" },        // Meritage red
  10:  { fill: "#F7941D", stroke: "#C47516", label: "LGI" },             // LGI orange-gold
  13:  { fill: "#7B2D8E", stroke: "#5C2169", label: "Starlight" },       // Starlight purple
  15:  { fill: "#1B365D", stroke: "#122541", label: "NVR" },             // NVR navy
  9:   { fill: "#B8860B", stroke: "#8B6508", label: "DSLD" },            // DSLD gold
  2:   { fill: "#2E8B57", stroke: "#1F5F3B", label: "Adams Homes" },     // Adams green
  5:   { fill: "#DC143C", stroke: "#A30E2D", label: "Holiday" },         // Holiday crimson
  8:   { fill: "#4682B4", stroke: "#335F80", label: "Maronda" },          // Maronda steel blue
  244: { fill: "#556B2F", stroke: "#3D4D21", label: "Clayton" },          // Clayton olive
  339: { fill: "#CD853F", stroke: "#9A632F", label: "Century" },          // Century tan
  16:  { fill: "#8B0000", stroke: "#630000", label: "Hovnanian" },        // Hovnanian dark red
  14:  { fill: "#008B8B", stroke: "#006363", label: "West Bay" },         // West Bay teal
};

const OTHER_STYLE = { fill: "#9CA3AF", stroke: "#6B7280", label: "Other" };

export function getBuilderColor(builderId: number): { fill: string; stroke: string; label: string } {
  return BUILDER_BRAND_COLORS[builderId] ?? OTHER_STYLE;
}

export function getBuilderFill(builderId: number): string {
  return (BUILDER_BRAND_COLORS[builderId] ?? OTHER_STYLE).fill;
}

export function getBuilderStroke(builderId: number): string {
  return (BUILDER_BRAND_COLORS[builderId] ?? OTHER_STYLE).stroke;
}

export { BUILDER_BRAND_COLORS, OTHER_STYLE };
```

- [ ] **Step 2: Commit**

```bash
git add ui/src/config/builderColors.ts
git commit -m "feat: add builder brand color config for map"
```

---

### Task 3: Map Page — Core Map with Polygons

**Files:**
- Create: `ui/src/pages/MapPage.tsx`
- Modify: `ui/src/App.tsx` (add route)
- Modify: `ui/src/components/Layout.tsx` (add nav link)

The core map page: fullscreen Leaflet on satellite tiles, fetches subdivision GeoJSON for a county, renders polygons styled by primary builder color. No hover/click yet — just polygons on the map.

- [ ] **Step 1: Create MapPage.tsx with basic map and polygon rendering**

Create `ui/src/pages/MapPage.tsx`:

```typescript
import { useEffect, useRef, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { getSubdivisionGeoJSON, getCounties } from "../api";
import { getBuilderColor, OTHER_STYLE } from "../config/builderColors";
import type { SubdivisionGeoFeature } from "../types";

export default function MapPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  const [countyFilter, setCountyFilter] = useState("Bay");

  const countiesQ = useQuery({ queryKey: ["counties"], queryFn: getCounties });

  const geoQ = useQuery({
    queryKey: ["subdivision-geojson", countyFilter],
    queryFn: () => {
      // Find county_id from name — we need a lookup. For now pass undefined
      // and filter client-side, or we add county_id lookup.
      return getSubdivisionGeoJSON({});
    },
    staleTime: 5 * 60 * 1000,
  });

  // Filter features by county name (until we wire county_id)
  const features = useMemo(() => {
    if (!geoQ.data) return [];
    if (!countyFilter) return geoQ.data;
    return geoQ.data.filter((f) => f.county_name === countyFilter);
  }, [geoQ.data, countyFilter]);

  // Initialize map once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: [30.2, -85.7], // Bay County default
      zoom: 11,
      zoomControl: true,
      attributionControl: false,
    });
    mapRef.current = map;

    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: "Esri" }
    ).addTo(map);

    // Label overlay for road names on satellite
    L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Transportation/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, opacity: 0.7 }
    ).addTo(map);

    layerGroupRef.current = L.layerGroup().addTo(map);

    return () => {
      map.remove();
      mapRef.current = null;
      layerGroupRef.current = null;
    };
  }, []);

  // Render polygons when features change
  useEffect(() => {
    const lg = layerGroupRef.current;
    if (!lg) return;
    lg.clearLayers();

    for (const feat of features) {
      const primary = feat.builders[0];
      const color = primary ? getBuilderColor(primary.builder_id) : OTHER_STYLE;
      const isGracePeriod = feat.builder_lot_count === 0;

      const layer = L.geoJSON(feat.geojson as GeoJSON.GeoJsonObject, {
        style: {
          color: isGracePeriod ? "#9CA3AF" : color.stroke,
          weight: isGracePeriod ? 1.5 : 2,
          fillColor: isGracePeriod ? "#D1D5DB" : color.fill,
          fillOpacity: isGracePeriod ? 0.1 : 0.35,
          dashArray: isGracePeriod ? "6 4" : undefined,
        },
      });

      // Store feature data on the layer for hover/click (Task 4 & 5)
      (layer as any)._subdivisionFeature = feat;

      layer.addTo(lg);
    }

    // Fit bounds to all polygons if any exist
    if (features.length > 0 && mapRef.current) {
      const allBounds = L.featureGroup(
        lg.getLayers() as L.Layer[]
      ).getBounds();
      if (allBounds.isValid()) {
        mapRef.current.fitBounds(allBounds, { padding: [40, 40] });
      }
    }
  }, [features]);

  return (
    <div className="fixed inset-0 top-[53px] flex flex-col">
      {/* Filter bar */}
      <div className="bg-white/90 backdrop-blur border-b border-gray-200 px-4 py-2 flex items-center gap-4 z-[1000]">
        <label className="text-xs text-gray-500 font-medium">County</label>
        <select
          value={countyFilter}
          onChange={(e) => setCountyFilter(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-sm bg-white min-w-[140px]"
        >
          <option value="">All Counties</option>
          {countiesQ.data?.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        {geoQ.isLoading && <span className="text-xs text-gray-400">Loading polygons...</span>}
        {features.length > 0 && (
          <span className="text-xs text-gray-500">{features.length} subdivisions</span>
        )}
      </div>

      {/* Map container */}
      <div ref={containerRef} className="flex-1" />
    </div>
  );
}
```

- [ ] **Step 2: Add route to App.tsx**

In `ui/src/App.tsx`, add the import and route:

```typescript
import MapPage from "./pages/MapPage";
```

Add inside the `<Route element={<Layout />}>` block, after the subdivisions routes:

```typescript
<Route path="map" element={<MapPage />} />
```

- [ ] **Step 3: Add nav link to Layout.tsx**

In `ui/src/components/Layout.tsx`, add to the `links` array:

```typescript
{ to: "/map", label: "Map" },
```

- [ ] **Step 4: Verify TypeScript compiles and map renders**

Run:
```bash
cd ui && npx tsc --noEmit
```

Then open http://localhost:1560/map — verify satellite tiles load, polygons appear for Bay county, colored by primary builder.

- [ ] **Step 5: Commit**

```bash
git add ui/src/pages/MapPage.tsx ui/src/App.tsx ui/src/components/Layout.tsx
git commit -m "feat: add full-screen map page with builder-colored subdivision polygons"
```

---

### Task 4: Hover Tooltips

**Files:**
- Modify: `ui/src/pages/MapPage.tsx`

Add Leaflet tooltip on polygon hover showing subdivision name, total lots, and per-builder breakdown.

- [ ] **Step 1: Add hover handlers to polygon rendering**

In the polygon rendering `useEffect` in `MapPage.tsx`, after the `L.geoJSON(...)` creation and before `layer.addTo(lg)`, add:

```typescript
      // Tooltip content
      const builderLines = feat.builders
        .map((b) => `${b.builder_name}: ${b.lot_count}`)
        .join("<br>");
      const tooltipHtml = `
        <div style="font-size:13px;line-height:1.4">
          <strong>${feat.name}</strong><br>
          <span style="color:#666">${feat.builder_lot_count} builder lots</span>
          <hr style="margin:4px 0;border-color:#e5e7eb">
          ${builderLines}
        </div>
      `;

      layer.bindTooltip(tooltipHtml, {
        sticky: true,
        direction: "top",
        offset: [0, -10],
        opacity: 0.95,
        className: "map-subdivision-tooltip",
      });
```

- [ ] **Step 2: Add tooltip CSS**

In `MapPage.tsx`, add a `<style>` tag inside the component return, before the filter bar div:

```tsx
      <style>{`
        .map-subdivision-tooltip {
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          padding: 8px 12px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          max-width: 280px;
        }
        .map-subdivision-tooltip hr {
          border: none;
          border-top: 1px solid #e5e7eb;
        }
      `}</style>
```

- [ ] **Step 3: Verify tooltip appears on hover**

Open http://localhost:1560/map, hover over a polygon. Tooltip should show subdivision name, lot count, and builder breakdown.

- [ ] **Step 4: Commit**

```bash
git add ui/src/pages/MapPage.tsx
git commit -m "feat: add hover tooltips to map subdivision polygons"
```

---

### Task 5: Click Detail Side Panel

**Files:**
- Modify: `ui/src/pages/MapPage.tsx`

Click a polygon to open a right-side panel with deeper data: builder lots with price data, monthly sales velocity, and commission actions. Fetched on demand.

- [ ] **Step 1: Add selected-subdivision state and click handlers**

In `MapPage.tsx`, add state:

```typescript
const [selectedSub, setSelectedSub] = useState<SubdivisionGeoFeature | null>(null);
```

In the polygon rendering `useEffect`, add click handler after `bindTooltip`:

```typescript
      layer.on("click", () => {
        setSelectedSub(feat);
      });
```

- [ ] **Step 2: Add the detail panel component**

Add a `MapDetailPanel` function component below `MapPage` in the same file:

```typescript
function MapDetailPanel({
  feature,
  onClose,
}: {
  feature: SubdivisionGeoFeature;
  onClose: () => void;
}) {
  const parcelsQ = useQuery({
    queryKey: ["parcels-by-sub", feature.id],
    queryFn: () =>
      import("../api").then((m) =>
        m.getParcelsBySubdivision(feature.id)
      ),
  });

  const salesQ = useQuery({
    queryKey: ["sales-by-sub", feature.name],
    queryFn: () =>
      import("../api").then((m) =>
        m.getSalesBySubdivision(feature.name)
      ),
  });

  const commissionQ = useQuery({
    queryKey: ["commission-roster", feature.id],
    queryFn: () =>
      import("../api").then((m) => m.getCommissionRoster(feature.id)),
  });

  // Aggregate parcels by builder (entity) for price data
  const builderStats = useMemo(() => {
    const items = parcelsQ.data?.items ?? [];
    const map = new Map<string, { count: number; values: number[] }>();
    for (const p of items) {
      const name = p.entity ?? p.owner_name ?? "Unknown";
      const entry = map.get(name) ?? { count: 0, values: [] };
      entry.count++;
      if (p.appraised_value != null) entry.values.push(p.appraised_value);
      map.set(name, entry);
    }
    return [...map.entries()]
      .map(([name, data]) => ({
        name,
        lots: data.count,
        avgValue: data.values.length > 0
          ? Math.round(data.values.reduce((a, b) => a + b, 0) / data.values.length)
          : null,
      }))
      .sort((a, b) => b.lots - a.lots);
  }, [parcelsQ.data]);

  // Monthly sales velocity
  const monthlySales = useMemo(() => {
    const txns = salesQ.data?.items ?? [];
    const months = new Map<string, number>();
    for (const t of txns) {
      if (!t.Date) continue;
      const month = t.Date.slice(0, 7); // YYYY-MM
      months.set(month, (months.get(month) ?? 0) + 1);
    }
    return [...months.entries()]
      .sort((a, b) => a[0].localeCompare(b[0]))
      .slice(-12);
  }, [salesQ.data]);

  const actions = commissionQ.data?.actions ?? [];

  return (
    <div className="w-96 bg-white border-l border-gray-200 shadow-xl overflow-y-auto z-[1000]">
      <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div>
          <h2 className="font-semibold text-gray-800 text-sm">{feature.name}</h2>
          <span className="text-xs text-gray-500">{feature.county_name}, FL</span>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-700 text-lg leading-none"
        >
          &times;
        </button>
      </div>

      <div className="p-4 space-y-5">
        {/* Builder lots */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Builder Lots</h3>
          {parcelsQ.isLoading ? (
            <p className="text-xs text-gray-400">Loading...</p>
          ) : (
            <div className="space-y-1">
              {builderStats.map((b) => (
                <div key={b.name} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 truncate">{b.name}</span>
                  <span className="text-gray-500 tabular-nums shrink-0 ml-2">
                    {b.lots} lots
                    {b.avgValue != null && (
                      <span className="text-gray-400 ml-1">
                        ~${(b.avgValue / 1000).toFixed(0)}k
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Monthly sales velocity */}
        <section>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Monthly Sales</h3>
          {salesQ.isLoading ? (
            <p className="text-xs text-gray-400">Loading...</p>
          ) : monthlySales.length === 0 ? (
            <p className="text-xs text-gray-400">No sales data.</p>
          ) : (
            <div className="space-y-1">
              {monthlySales.map(([month, count]) => (
                <div key={month} className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">{month}</span>
                  <span className="text-gray-800 tabular-nums font-medium">{count}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Commission actions */}
        {actions.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Commission Actions</h3>
            <div className="space-y-1.5">
              {actions.slice(0, 6).map((a) => (
                <div key={a.id} className="text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 text-xs shrink-0">{a.meeting_date}</span>
                    <span className="text-gray-700 truncate">{a.approval_type.replace(/_/g, " ")}</span>
                  </div>
                  {a.outcome && (
                    <span className={`text-xs font-medium ${
                      a.outcome === "approved" ? "text-green-600"
                        : a.outcome === "denied" ? "text-red-600"
                          : "text-gray-500"
                    }`}>
                      {a.outcome}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Link to full detail page */}
        <a
          href={`/subdivisions/${feature.id}`}
          className="block text-center text-sm text-blue-600 hover:text-blue-800 font-medium py-2"
        >
          View full detail &rarr;
        </a>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Wire the panel into the page layout**

Update the `MapPage` return to include the panel. Change the outermost div to a flex row:

```tsx
  return (
    <div className="fixed inset-0 top-[53px] flex flex-col">
      <style>{`
        .map-subdivision-tooltip { /* ... existing styles ... */ }
      `}</style>

      {/* Filter bar */}
      <div className="bg-white/90 backdrop-blur border-b border-gray-200 px-4 py-2 flex items-center gap-4 z-[1000]">
        {/* ... existing filter content ... */}
      </div>

      {/* Map + optional side panel */}
      <div className="flex-1 flex">
        <div ref={containerRef} className="flex-1" />
        {selectedSub && (
          <MapDetailPanel feature={selectedSub} onClose={() => setSelectedSub(null)} />
        )}
      </div>
    </div>
  );
```

- [ ] **Step 4: Add useMemo import**

Ensure `useMemo` is imported at the top of `MapPage.tsx` (it should already be from Task 3).

Also import the needed types at the top:

```typescript
import type { SubdivisionGeoFeature } from "../types";
```

This should already be imported from Task 3 as well.

- [ ] **Step 5: Verify panel opens on click, data loads**

Open http://localhost:1560/map, click a polygon. Panel should slide in from the right showing builder lots, monthly sales, and commission actions.

- [ ] **Step 6: Commit**

```bash
git add ui/src/pages/MapPage.tsx
git commit -m "feat: add click detail panel with sales velocity and commission data"
```

---

### Task 6: Multi-Builder Polygon Styling

**Files:**
- Modify: `ui/src/pages/MapPage.tsx`

For subdivisions with multiple builders, use SVG stripe patterns to show each builder's color proportionally.

- [ ] **Step 1: Add SVG pattern generation utility**

In `MapPage.tsx`, add a utility function above the component:

```typescript
let patternCounter = 0;

function createStripePattern(
  map: L.Map,
  builders: { builder_id: number; lot_count: number }[],
): string {
  const total = builders.reduce((s, b) => s + b.lot_count, 0);
  const patternId = `stripe-${++patternCounter}`;
  const stripeWidth = 8;
  const patternWidth = stripeWidth * builders.length;

  // Get or create the SVG defs element
  const svg = (map as any)._renderer?._container ?? map.getPane("overlayPane")?.querySelector("svg");
  if (!svg) return getBuilderColor(builders[0].builder_id).fill;

  let defs = svg.querySelector("defs");
  if (!defs) {
    defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
    svg.insertBefore(defs, svg.firstChild);
  }

  const pattern = document.createElementNS("http://www.w3.org/2000/svg", "pattern");
  pattern.setAttribute("id", patternId);
  pattern.setAttribute("width", String(patternWidth));
  pattern.setAttribute("height", String(patternWidth));
  pattern.setAttribute("patternUnits", "userSpaceOnUse");
  pattern.setAttribute("patternTransform", "rotate(45)");

  let offset = 0;
  for (const b of builders) {
    const width = Math.max(stripeWidth * (b.lot_count / total) * builders.length, 2);
    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(offset));
    rect.setAttribute("y", "0");
    rect.setAttribute("width", String(width));
    rect.setAttribute("height", String(patternWidth));
    rect.setAttribute("fill", getBuilderColor(b.builder_id).fill);
    pattern.appendChild(rect);
    offset += width;
  }

  defs.appendChild(pattern);
  return `url(#${patternId})`;
}
```

- [ ] **Step 2: Update polygon rendering to use stripes for multi-builder**

In the polygon rendering `useEffect`, replace the existing style/layer creation with:

```typescript
      const isSingle = feat.builders.length <= 1;
      const primary = feat.builders[0];
      const color = primary ? getBuilderColor(primary.builder_id) : OTHER_STYLE;

      let fillColor: string;
      if (isSingle) {
        fillColor = color.fill;
      } else if (mapRef.current) {
        fillColor = createStripePattern(mapRef.current, feat.builders);
      } else {
        fillColor = color.fill;
      }

      const layer = L.geoJSON(feat.geojson as GeoJSON.GeoJsonObject, {
        style: {
          color: isSingle ? color.stroke : "#374151",
          weight: isSingle ? 2 : 2.5,
          fillColor,
          fillOpacity: 0.35,
        },
        renderer: L.svg(), // SVG renderer required for pattern fills
      });
```

- [ ] **Step 3: Clean up patterns when layers change**

At the top of the polygon rendering `useEffect`, after `lg.clearLayers()`, add:

```typescript
    // Clean up old SVG patterns
    const svg = mapRef.current?.getPane("overlayPane")?.querySelector("svg");
    const defs = svg?.querySelector("defs");
    if (defs) defs.innerHTML = "";
    patternCounter = 0;
```

- [ ] **Step 4: Verify multi-builder polygons show stripes**

Open http://localhost:1560/map. Find a multi-builder subdivision (visible with the hover tooltip showing 2+ builders). It should display diagonal stripes in each builder's color. Single-builder polygons should remain solid fills.

- [ ] **Step 5: Commit**

```bash
git add ui/src/pages/MapPage.tsx
git commit -m "feat: add SVG stripe patterns for multi-builder subdivision polygons"
```

---

### Task 7: Builder Filter

**Files:**
- Modify: `ui/src/pages/MapPage.tsx`

Add a multi-select builder filter to the top bar.

- [ ] **Step 1: Add builder query and filter state**

Add to MapPage imports:

```typescript
import { getSubdivisionGeoJSON, getCounties, getInventoryBuilders } from "../api";
```

Add state and query:

```typescript
const [builderFilter, setBuilderFilter] = useState<number[]>([]);

const buildersQ = useQuery({
  queryKey: ["inventory-builders"],
  queryFn: () => getInventoryBuilders(),
});
```

The function is `getInventoryBuilders` in `api.ts` (line 216), returns `Promise<BuilderOut[]>`.

- [ ] **Step 2: Update feature filtering to include builder filter**

Update the `features` useMemo:

```typescript
  const features = useMemo(() => {
    if (!geoQ.data) return [];
    let filtered = geoQ.data;
    if (countyFilter) {
      filtered = filtered.filter((f) => f.county_name === countyFilter);
    }
    if (builderFilter.length > 0) {
      filtered = filtered.filter((f) =>
        f.builders.some((b) => builderFilter.includes(b.builder_id))
      );
    }
    return filtered;
  }, [geoQ.data, countyFilter, builderFilter]);
```

- [ ] **Step 3: Add builder multi-select to filter bar**

In the filter bar div, after the county select, add:

```tsx
        <label className="text-xs text-gray-500 font-medium">Builder</label>
        <select
          multiple
          value={builderFilter.map(String)}
          onChange={(e) => {
            const selected = Array.from(e.target.selectedOptions, (o) => Number(o.value));
            setBuilderFilter(selected);
          }}
          className="border border-gray-300 rounded px-2 py-1 text-sm bg-white min-w-[160px] max-h-[80px]"
        >
          {(buildersQ.data ?? [])
            .filter((b) => b.type === "builder")
            .map((b) => (
              <option key={b.id} value={b.id}>{b.canonical_name}</option>
            ))}
        </select>
        {builderFilter.length > 0 && (
          <button
            onClick={() => setBuilderFilter([])}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Clear
          </button>
        )}
```

- [ ] **Step 4: Verify builder filter works**

Select a builder from the multi-select. Only subdivisions containing that builder should remain visible. Clear returns all.

- [ ] **Step 5: Commit**

```bash
git add ui/src/pages/MapPage.tsx
git commit -m "feat: add builder filter to map page"
```

---

### Task 8: Final Verification

- [ ] **Step 1: TypeScript check**

```bash
cd ui && npx tsc --noEmit
```

Expected: exit code 0, zero errors.

- [ ] **Step 2: Backend check**

```bash
python -c "from modules.inventory.routers.subdivisions import router; print('OK')"
```

- [ ] **Step 3: Full functional verification**

Open http://localhost:1560/map and verify:
- Satellite tiles load
- Polygons appear for Bay county (default), colored by builder
- Hover tooltip shows subdivision name, lot count, builder breakdown
- Click opens side panel with builder lots, monthly sales, commission actions
- Multi-builder subdivisions show striped fills
- County filter switches to another county (e.g., Lee) and polygons update
- Builder filter narrows visible polygons
- "View full detail" link in side panel navigates to subdivision detail page
- Map nav link in top bar is present and active when on /map

- [ ] **Step 4: Commit any fixes from verification**
