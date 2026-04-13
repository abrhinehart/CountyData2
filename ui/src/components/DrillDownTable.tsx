import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getInventoryCounties,
  getInventorySummary,
  getInventoryCountyDetail,
} from "../api";
import type {
  InventoryCounty,
  CountyInventory,
  BuilderCount,
  SubdivisionInventory,
} from "../types";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ParcelClass = "lot" | "tract" | "common_area" | "other";

interface ParcelOption {
  value: ParcelClass;
  label: string;
}

const PARCEL_OPTIONS: ParcelOption[] = [
  { value: "lot", label: "Lots" },
  { value: "tract", label: "Raw" },
  { value: "common_area", label: "HOA" },
  { value: "other", label: "Other" },
];

const ENTITY_TYPES = ["builder", "developer", "land_banker", "btr"];

type Level = "state" | "county" | "builder" | "subdivision";

interface DrillState {
  level: Level;
  stateCode?: string;
  countyId?: number;
  countyName?: string;
  builderId?: number;
  builderName?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(n: number): string {
  return n.toLocaleString();
}

/** Aggregate CountyInventory rows by state */
function aggregateByState(
  inventory: CountyInventory[],
  counties: InventoryCounty[]
): { state: string; total: number }[] {
  const countyStateMap = new Map(counties.map((c) => [c.id, c.state]));
  const stateMap = new Map<string, number>();

  for (const ci of inventory) {
    const st = countyStateMap.get(ci.county_id) ?? "??";
    stateMap.set(st, (stateMap.get(st) ?? 0) + ci.total);
  }

  return Array.from(stateMap.entries())
    .map(([state, total]) => ({ state, total }))
    .sort((a, b) => b.total - a.total);
}

/** Aggregate builders across counties for a given state */
function aggregateBuildersByState(
  inventory: CountyInventory[],
  counties: InventoryCounty[],
  stateCode: string
): BuilderCount[] {
  const countyStateMap = new Map(counties.map((c) => [c.id, c.state]));
  const builderMap = new Map<number, { name: string; count: number }>();

  for (const ci of inventory) {
    if (countyStateMap.get(ci.county_id) !== stateCode) continue;
    for (const b of ci.builders) {
      const existing = builderMap.get(b.builder_id);
      if (existing) {
        existing.count += b.count;
      } else {
        builderMap.set(b.builder_id, { name: b.builder_name, count: b.count });
      }
    }
  }

  return Array.from(builderMap.entries())
    .map(([id, v]) => ({ builder_id: id, builder_name: v.name, count: v.count }))
    .sort((a, b) => b.count - a.count);
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function DrillDownTable() {
  const [parcelClass, setParcelClass] = useState<ParcelClass>("lot");
  const [drill, setDrill] = useState<DrillState>({ level: "state" });

  const activeLabel =
    PARCEL_OPTIONS.find((o) => o.value === parcelClass)?.label ?? "Count";

  // --- Data queries ---

  const countiesQ = useQuery({
    queryKey: ["inventory-counties"],
    queryFn: getInventoryCounties,
  });

  const summaryQ = useQuery({
    queryKey: ["inventory-summary", parcelClass],
    queryFn: () =>
      getInventorySummary({ parcel_class: parcelClass, entity_type: ENTITY_TYPES }),
  });

  const countyDetailQ = useQuery({
    queryKey: [
      "inventory-county-detail",
      drill.countyId,
      parcelClass,
      drill.builderId,
    ],
    queryFn: () =>
      getInventoryCountyDetail(drill.countyId!, {
        parcel_class: parcelClass,
        entity_type: ENTITY_TYPES,
        builder_id: drill.builderId,
      }),
    enabled:
      drill.countyId != null &&
      (drill.level === "builder" || drill.level === "subdivision"),
  });

  const counties = countiesQ.data ?? [];
  const inventory = summaryQ.data ?? [];
  const countyDetail = countyDetailQ.data;

  // --- Derived rows ---

  const stateRows = useMemo(
    () => aggregateByState(inventory, counties),
    [inventory, counties]
  );

  const countyRows = useMemo(() => {
    if (drill.level === "state" || !drill.stateCode) return [];
    const countyStateMap = new Map(counties.map((c) => [c.id, c.state]));
    return inventory
      .filter((ci) => countyStateMap.get(ci.county_id) === drill.stateCode)
      .sort((a, b) => b.total - a.total);
  }, [inventory, counties, drill.stateCode, drill.level]);

  const builderRows = useMemo(() => {
    if (drill.level !== "builder" && drill.level !== "subdivision") return [];
    if (!drill.countyId) return [];
    const ci = inventory.find((c) => c.county_id === drill.countyId);
    return ci ? [...ci.builders].sort((a, b) => b.count - a.count) : [];
  }, [inventory, drill.countyId, drill.level]);

  const subdivisionRows: SubdivisionInventory[] = useMemo(() => {
    if (drill.level !== "subdivision" || !countyDetail) return [];
    if (drill.builderId != null) {
      return [...countyDetail.subdivisions].sort((a, b) => b.total - a.total);
    }
    return [...countyDetail.subdivisions].sort((a, b) => b.total - a.total);
  }, [countyDetail, drill.level, drill.builderId]);

  // --- Navigation ---

  function goToState(stateCode: string) {
    setDrill({ level: "county", stateCode });
  }

  function goToCounty(countyId: number, countyName: string) {
    setDrill({
      level: "builder",
      stateCode: drill.stateCode,
      countyId,
      countyName,
    });
  }

  function goToBuilder(builderId: number, builderName: string) {
    setDrill({
      level: "subdivision",
      stateCode: drill.stateCode,
      countyId: drill.countyId,
      countyName: drill.countyName,
      builderId,
      builderName,
    });
  }

  function goBack(level: Level) {
    if (level === "state") {
      setDrill({ level: "state" });
    } else if (level === "county") {
      setDrill({ level: "county", stateCode: drill.stateCode });
    } else if (level === "builder") {
      setDrill({
        level: "builder",
        stateCode: drill.stateCode,
        countyId: drill.countyId,
        countyName: drill.countyName,
      });
    }
  }

  // --- Render ---

  const isLoading =
    countiesQ.isLoading ||
    summaryQ.isLoading ||
    (countyDetailQ.isLoading &&
      drill.countyId != null &&
      (drill.level === "builder" || drill.level === "subdivision"));

  return (
    <div>
      {/* Parcel type toggles */}
      <div className="flex gap-1.5 mb-4">
        {PARCEL_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => setParcelClass(opt.value)}
            className={`px-3 py-1 text-xs font-medium rounded-full transition-colors ${
              parcelClass === opt.value
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {/* Breadcrumbs */}
      <Breadcrumbs drill={drill} onNavigate={goBack} />

      {/* Table */}
      <div className="mt-3">
        <div className="flex items-center border-b border-gray-200 pb-2 mb-1">
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide flex-1">
            Name
          </span>
          <span className="text-xs font-medium text-gray-400 uppercase tracking-wide w-20 text-right">
            {activeLabel}
          </span>
        </div>

        {isLoading ? (
          <p className="text-sm text-gray-400 py-4">Loading...</p>
        ) : (
          <div>
            {drill.level === "state" &&
              stateRows.map((row) => (
                <Row
                  key={row.state}
                  label={row.state}
                  count={row.total}
                  indent={0}
                  onClick={() => goToState(row.state)}
                />
              ))}

            {drill.level === "county" &&
              countyRows.map((row) => (
                <Row
                  key={row.county_id}
                  label={row.county}
                  count={row.total}
                  indent={1}
                  onClick={() => goToCounty(row.county_id, row.county)}
                />
              ))}

            {drill.level === "builder" &&
              builderRows.map((row) => (
                <Row
                  key={row.builder_id}
                  label={row.builder_name}
                  count={row.count}
                  indent={2}
                  onClick={() => goToBuilder(row.builder_id, row.builder_name)}
                />
              ))}

            {drill.level === "subdivision" &&
              (countyDetailQ.isLoading ? (
                <p className="text-sm text-gray-400 py-4 pl-12">
                  Loading subdivisions...
                </p>
              ) : subdivisionRows.length === 0 ? (
                <p className="text-sm text-gray-400 py-4 pl-12">
                  No subdivisions found.
                </p>
              ) : (
                subdivisionRows.map((row, i) => (
                  <SubdivisionRow
                    key={row.subdivision_id ?? `null-${i}`}
                    subdivision={row}
                  />
                ))
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Row({
  label,
  count,
  indent,
  onClick,
}: {
  label: string;
  count: number;
  indent: number;
  onClick: () => void;
}) {
  const pad = indent * 16;
  return (
    <button
      onClick={onClick}
      className="flex items-center w-full text-left py-2 px-1 hover:bg-gray-50 rounded transition-colors group"
      style={{ paddingLeft: `${pad + 4}px` }}
    >
      <span className="text-sm text-gray-400 mr-2 group-hover:text-blue-500 transition-colors">
        &#x203A;
      </span>
      <span className="text-sm font-medium text-gray-700 flex-1 truncate">
        {label}
      </span>
      <span className="text-sm text-gray-500 tabular-nums w-20 text-right shrink-0">
        {fmt(count)}
      </span>
    </button>
  );
}

function SubdivisionRow({
  subdivision,
}: {
  subdivision: SubdivisionInventory;
}) {
  const pad = 3 * 16; // indent level 3

  if (subdivision.subdivision_id == null) {
    // Unmatched row — not linkable
    return (
      <div
        className="flex items-center w-full py-2 px-1"
        style={{ paddingLeft: `${pad + 4}px` }}
      >
        <span className="text-sm text-gray-400 italic flex-1 truncate">
          {subdivision.subdivision || "Unmatched"}
        </span>
        <span className="text-sm text-gray-500 tabular-nums w-20 text-right shrink-0">
          {fmt(subdivision.total)}
        </span>
      </div>
    );
  }

  return (
    <a
      href={`/subdivisions/${subdivision.subdivision_id}`}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center w-full py-2 px-1 hover:bg-gray-50 rounded transition-colors group"
      style={{ paddingLeft: `${pad + 4}px` }}
    >
      <span className="text-sm font-medium text-blue-600 hover:text-blue-800 flex-1 truncate">
        {subdivision.subdivision}
        <span className="ml-1 text-xs text-blue-400 group-hover:text-blue-600">
          &#x2197;
        </span>
      </span>
      <span className="text-sm text-gray-500 tabular-nums w-20 text-right shrink-0">
        {fmt(subdivision.total)}
      </span>
    </a>
  );
}

function Breadcrumbs({
  drill,
  onNavigate,
}: {
  drill: DrillState;
  onNavigate: (level: Level) => void;
}) {
  if (drill.level === "state") return null;

  const crumbs: { label: string; level: Level }[] = [
    { label: "All States", level: "state" },
  ];

  if (drill.stateCode) {
    crumbs.push({ label: drill.stateCode, level: "county" });
  }

  if (drill.countyName && (drill.level === "builder" || drill.level === "subdivision")) {
    crumbs.push({ label: drill.countyName, level: "builder" });
  }

  if (drill.builderName && drill.level === "subdivision") {
    crumbs.push({ label: drill.builderName, level: "subdivision" });
  }

  return (
    <nav className="flex items-center gap-1 text-xs text-gray-400">
      {crumbs.map((crumb, i) => {
        const isLast = i === crumbs.length - 1;
        return (
          <span key={crumb.level} className="flex items-center gap-1">
            {i > 0 && <span>&#x203A;</span>}
            {isLast ? (
              <span className="text-gray-600 font-medium">{crumb.label}</span>
            ) : (
              <button
                onClick={() => onNavigate(crumb.level)}
                className="text-blue-500 hover:text-blue-700 hover:underline"
              >
                {crumb.label}
              </button>
            )}
          </span>
        );
      })}
    </nav>
  );
}
