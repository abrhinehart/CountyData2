# Inventory Drill-Down Table Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat "Lots by County" bar chart on the Inventory page with an interactive State → County → Builder → Subdivision drill-down table with parcel type filtering.

**Architecture:** Pure frontend change. The two existing backend endpoints already provide all the data with the right filters. Task 1 adds the missing frontend API function. Task 2 builds the DrillDownTable component. Task 3 wires it into the Inventory page, replacing the bar chart.

**Tech Stack:** React 19, TanStack Query, Tailwind v4. Backend: FastAPI (no changes needed).

**Spec:** `docs/superpowers/specs/2026-04-13-inventory-drilldown-table-design.md`

---

### Task 1: Add frontend API function + types for county detail

**Files:**
- Modify: `ui/src/api.ts`
- Modify: `ui/src/types.ts`

The county detail endpoint (`GET /api/inventory/inventory/{county_id}`) exists but has no frontend API function. We need it for the Builder → Subdivision drill level.

- [ ] **Step 1: Add TypeScript types for CountyDetail response**

In `ui/src/types.ts`, add after the `CountyInventory` interface (after line 256):

```typescript
export interface SubdivisionInventory {
  subdivision_id: number | null;
  subdivision: string;
  total: number;
  builders: BuilderCount[];
}

export interface CountyDetail {
  county_id: number;
  county: string;
  total: number;
  subdivisions: SubdivisionInventory[];
}
```

- [ ] **Step 2: Add API function for inventory summary with params**

The existing `getInventorySummary()` hardcodes no params, but the endpoint accepts `parcel_class` and `entity_type`. Replace it with a parameterized version.

In `ui/src/api.ts`, replace the existing `getInventorySummary` function:

```typescript
export async function getInventorySummary(
  params?: { parcel_class?: string; entity_type?: string[] }
): Promise<CountyInventory[]> {
  const p: Record<string, string> = {};
  if (params?.parcel_class) p.parcel_class = params.parcel_class;
  // entity_type needs special handling — backend expects repeated params
  const base = `${BASE}/inventory/inventory`;
  const search = new URLSearchParams();
  if (params?.parcel_class) search.append("parcel_class", params.parcel_class);
  if (params?.entity_type) {
    for (const t of params.entity_type) search.append("entity_type", t);
  }
  const q = search.toString();
  return checked(await fetch(q ? `${base}?${q}` : base));
}
```

- [ ] **Step 3: Add API function for county detail**

In `ui/src/api.ts`, add after `getInventorySummary`:

```typescript
export async function getInventoryCountyDetail(
  countyId: number,
  params?: { parcel_class?: string; entity_type?: string[]; builder_id?: number }
): Promise<CountyDetail> {
  const search = new URLSearchParams();
  if (params?.parcel_class) search.append("parcel_class", params.parcel_class);
  if (params?.entity_type) {
    for (const t of params.entity_type) search.append("entity_type", t);
  }
  if (params?.builder_id != null) search.append("builder_id", String(params.builder_id));
  const q = search.toString();
  const base = `${BASE}/inventory/inventory/${countyId}`;
  return checked(await fetch(q ? `${base}?${q}` : base));
}
```

Add the new types to the import in `api.ts`:

```typescript
import type { ..., CountyDetail, SubdivisionInventory } from "./types";
```

(The `SubdivisionInventory` import isn't strictly needed since it's only used inside `CountyDetail`, but include it for completeness.)

- [ ] **Step 4: Verify TypeScript compiles**

Run: `cd ui && npx tsc --noEmit`
Expected: exit 0

- [ ] **Step 5: Commit**

```bash
git add ui/src/types.ts ui/src/api.ts
git commit -m "feat: add inventory county detail API function and types"
```

---

### Task 2: Build DrillDownTable component

**Files:**
- Create: `ui/src/components/DrillDownTable.tsx`

A self-contained component that renders the State → County → Builder → Subdivision hierarchy with parcel type filter toggle buttons.

- [ ] **Step 1: Create the DrillDownTable component**

Create `ui/src/components/DrillDownTable.tsx`:

```typescript
import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getInventorySummary,
  getInventoryCounties,
  getInventoryCountyDetail,
} from "../api";
import type { InventoryCounty, CountyInventory, BuilderCount } from "../types";

type ParcelType = "lot" | "tract" | "common_area" | "other";
const PARCEL_TYPES: { key: ParcelType; label: string }[] = [
  { key: "lot", label: "Lots" },
  { key: "tract", label: "Raw" },
  { key: "common_area", label: "HOA" },
  { key: "other", label: "Other" },
];

const ALL_ENTITY_TYPES = ["builder", "developer", "land_banker", "btr"];

interface DrillState {
  state: string | null;
  countyId: number | null;
  countyName: string | null;
  builderId: number | null;
  builderName: string | null;
}

export default function DrillDownTable() {
  const [parcelType, setParcelType] = useState<ParcelType>("lot");
  const [drill, setDrill] = useState<DrillState>({
    state: null,
    countyId: null,
    countyName: null,
    builderId: null,
    builderName: null,
  });

  // Counties (for state field)
  const countiesQ = useQuery({
    queryKey: ["inventory-counties"],
    queryFn: getInventoryCounties,
  });

  // Inventory summary (county + builder breakdowns) — refetch when parcel type changes
  const inventoryQ = useQuery({
    queryKey: ["inventory-summary", parcelType],
    queryFn: () =>
      getInventorySummary({
        parcel_class: parcelType,
        entity_type: ALL_ENTITY_TYPES,
      }),
  });

  // County detail (subdivision breakdown) — fetch on demand when builder is selected
  const detailQ = useQuery({
    queryKey: ["inventory-detail", drill.countyId, parcelType, drill.builderId],
    queryFn: () =>
      getInventoryCountyDetail(drill.countyId!, {
        parcel_class: parcelType,
        entity_type: ALL_ENTITY_TYPES,
        builder_id: drill.builderId ?? undefined,
      }),
    enabled: drill.countyId != null && drill.builderId != null,
  });

  // Build state -> county lookup
  const stateMap = useMemo(() => {
    const counties = countiesQ.data ?? [];
    const inventory = inventoryQ.data ?? [];
    const countyStateMap = new Map<number, string>();
    for (const c of counties) {
      countyStateMap.set(c.id, c.state);
    }

    const states = new Map<string, { total: number; counties: (CountyInventory & { state: string })[] }>();
    for (const ci of inventory) {
      const st = countyStateMap.get(ci.county_id) ?? "??";
      if (!states.has(st)) states.set(st, { total: 0, counties: [] });
      const entry = states.get(st)!;
      entry.total += ci.total;
      entry.counties.push({ ...ci, state: st });
    }

    // Sort counties within each state by total desc
    for (const entry of states.values()) {
      entry.counties.sort((a, b) => b.total - a.total);
    }

    return states;
  }, [countiesQ.data, inventoryQ.data]);

  // Breadcrumb segments
  const crumbs: { label: string; onClick: () => void }[] = [];
  crumbs.push({
    label: "All States",
    onClick: () => setDrill({ state: null, countyId: null, countyName: null, builderId: null, builderName: null }),
  });
  if (drill.state) {
    crumbs.push({
      label: drill.state,
      onClick: () => setDrill({ ...drill, countyId: null, countyName: null, builderId: null, builderName: null }),
    });
  }
  if (drill.countyName) {
    crumbs.push({
      label: drill.countyName,
      onClick: () => setDrill({ ...drill, builderId: null, builderName: null }),
    });
  }
  if (drill.builderName) {
    crumbs.push({ label: drill.builderName, onClick: () => {} });
  }

  const isLoading = countiesQ.isLoading || inventoryQ.isLoading;

  // Determine what level to render
  let rows: React.ReactNode;

  if (!drill.state) {
    // State level
    const sorted = [...stateMap.entries()].sort((a, b) => b[1].total - a[1].total);
    rows = sorted.map(([st, data]) => (
      <Row
        key={st}
        indent={0}
        label={st}
        count={data.total}
        onClick={() => setDrill({ state: st, countyId: null, countyName: null, builderId: null, builderName: null })}
      />
    ));
  } else if (!drill.countyId) {
    // County level
    const stateData = stateMap.get(drill.state);
    rows = (stateData?.counties ?? []).map((ci) => (
      <Row
        key={ci.county_id}
        indent={1}
        label={ci.county}
        count={ci.total}
        onClick={() =>
          setDrill({ ...drill, countyId: ci.county_id, countyName: ci.county, builderId: null, builderName: null })
        }
      />
    ));
  } else if (!drill.builderId) {
    // Builder level — from inventory summary
    const county = stateMap
      .get(drill.state)
      ?.counties.find((c) => c.county_id === drill.countyId);
    const builders = (county?.builders ?? []).sort((a, b) => b.count - a.count);
    rows = builders.map((b) => (
      <Row
        key={b.builder_id}
        indent={2}
        label={b.builder_name}
        count={b.count}
        onClick={() => setDrill({ ...drill, builderId: b.builder_id, builderName: b.builder_name })}
      />
    ));
  } else {
    // Subdivision level — from county detail
    if (detailQ.isLoading) {
      rows = <tr><td colSpan={2} className="px-4 py-3 text-sm text-gray-400">Loading subdivisions...</td></tr>;
    } else {
      const subs = (detailQ.data?.subdivisions ?? [])
        .filter((s) => s.builders.some((b) => b.builder_id === drill.builderId))
        .map((s) => ({
          ...s,
          builderCount: s.builders.find((b) => b.builder_id === drill.builderId)?.count ?? s.total,
        }))
        .sort((a, b) => b.builderCount - a.builderCount);

      rows = subs.map((s) => (
        <Row
          key={s.subdivision_id ?? "unlinked"}
          indent={3}
          label={s.subdivision}
          count={s.builderCount}
          href={s.subdivision_id != null ? `/subdivisions/${s.subdivision_id}` : undefined}
        />
      ));
    }
  }

  return (
    <div>
      {/* Parcel type filter */}
      <div className="flex items-center gap-1 mb-3">
        {PARCEL_TYPES.map((pt) => (
          <button
            key={pt.key}
            onClick={() => setParcelType(pt.key)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              parcelType === pt.key
                ? "bg-blue-100 text-blue-700"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            }`}
          >
            {pt.label}
          </button>
        ))}
      </div>

      {/* Breadcrumbs */}
      <div className="flex items-center gap-1 text-sm text-gray-500 mb-3">
        {crumbs.map((c, i) => (
          <span key={i} className="flex items-center gap-1">
            {i > 0 && <span className="text-gray-300">&rsaquo;</span>}
            <button
              onClick={c.onClick}
              className={`hover:text-blue-600 ${i === crumbs.length - 1 ? "text-gray-800 font-medium" : ""}`}
            >
              {c.label}
            </button>
          </span>
        ))}
      </div>

      {/* Table */}
      {isLoading ? (
        <p className="text-sm text-gray-400 py-4">Loading...</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wide">
              <th className="text-left px-4 py-2">Name</th>
              <th className="text-right px-4 py-2 w-28">
                {PARCEL_TYPES.find((p) => p.key === parcelType)?.label ?? "Count"}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">{rows}</tbody>
        </table>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Row component
// ---------------------------------------------------------------------------

const INDENT_PX = [0, 16, 32, 48] as const;

function Row({
  indent,
  label,
  count,
  onClick,
  href,
}: {
  indent: number;
  label: string;
  count: number;
  onClick?: () => void;
  href?: string;
}) {
  const pl = INDENT_PX[indent] ?? 0;

  if (href) {
    return (
      <tr className="hover:bg-blue-50">
        <td className="px-4 py-2" style={{ paddingLeft: `${16 + pl}px` }}>
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            {label}
            <span className="text-gray-400 ml-1 text-xs">&#8599;</span>
          </a>
        </td>
        <td className="px-4 py-2 text-right tabular-nums text-gray-700">{count.toLocaleString()}</td>
      </tr>
    );
  }

  return (
    <tr
      className={onClick ? "hover:bg-blue-50 cursor-pointer" : ""}
      onClick={onClick}
    >
      <td className="px-4 py-2 font-medium text-gray-800" style={{ paddingLeft: `${16 + pl}px` }}>
        {onClick && <span className="text-gray-400 mr-2">&rsaquo;</span>}
        {label}
      </td>
      <td className="px-4 py-2 text-right tabular-nums text-gray-700">{count.toLocaleString()}</td>
    </tr>
  );
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd ui && npx tsc --noEmit`
Expected: exit 0

- [ ] **Step 3: Commit**

```bash
git add ui/src/components/DrillDownTable.tsx
git commit -m "feat: add DrillDownTable component for inventory page"
```

---

### Task 3: Wire DrillDownTable into InventoryPage

**Files:**
- Modify: `ui/src/pages/InventoryPage.tsx`

Replace the "Lots by County" bar chart section with the new DrillDownTable component. Keep all other sections (KPI cards, Builders table, Snapshots, Run Snapshot) unchanged.

- [ ] **Step 1: Read the current InventoryPage to identify the bar chart section**

Read `ui/src/pages/InventoryPage.tsx` and find the section that renders "Lots by County" (a horizontal bar chart). This is the section to replace.

- [ ] **Step 2: Replace the bar chart with DrillDownTable**

Import DrillDownTable at the top:

```typescript
import DrillDownTable from "../components/DrillDownTable";
```

Find the "Lots by County" section (it will be a `<div>` with an `<h2>` saying "Lots by County" and horizontal bars). Replace the entire section with:

```tsx
<div className="bg-white border border-gray-200 rounded-lg p-5">
  <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
    Inventory Drill-Down
  </h2>
  <DrillDownTable />
</div>
```

Do NOT change any other sections on the page.

- [ ] **Step 3: Verify TypeScript compiles**

Run: `cd ui && npx tsc --noEmit`
Expected: exit 0

- [ ] **Step 4: Visual verification**

Open http://localhost:1560/inventory and verify:
- DrillDownTable appears where the bar chart was
- Parcel type toggles (Lots/Raw/HOA/Other) work
- State level shows FL, AL with counts
- Click FL → shows counties sorted by count
- Click a county → shows builders
- Click a builder → shows subdivisions (loads on demand)
- Click a subdivision → opens detail page in new tab
- Breadcrumbs work for navigating back up
- KPI cards, Builders table, Snapshots section all still render correctly

- [ ] **Step 5: Commit**

```bash
git add ui/src/pages/InventoryPage.tsx
git commit -m "feat: replace inventory bar chart with drill-down table"
```
