import { useState, useRef, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getInventoryCounties,
  getInventorySummary,
  getInventoryBuilders,
  getInventorySnapshots,
  getActiveSnapshots,
  triggerSnapshot,
} from "../api";
import type { InventoryCounty } from "../types";
import DrillDownTable from "../components/DrillDownTable";

function fmt(n: number): string {
  return n.toLocaleString();
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

export default function InventoryPage() {
  const queryClient = useQueryClient();
  const [selectedCounty, setSelectedCounty] = useState<number | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [confirmState, setConfirmState] = useState<null | { label: string }>(null);
  const [elapsedTick, setElapsedTick] = useState(0);

  const countiesQ = useQuery({
    queryKey: ["inventory-counties"],
    queryFn: getInventoryCounties,
  });

  const inventoryQ = useQuery({
    queryKey: ["inventory-summary"],
    queryFn: getInventorySummary,
  });

  const buildersQ = useQuery({
    queryKey: ["inventory-builders"],
    queryFn: getInventoryBuilders,
  });

  const snapshotsQ = useQuery({
    queryKey: ["inventory-snapshots"],
    queryFn: () => getInventorySnapshots({ limit: 5 }),
  });

  const activeQ = useQuery({
    queryKey: ["active-snapshots"],
    queryFn: getActiveSnapshots,
    refetchInterval: (query) => {
      return (query.state.data?.length ?? 0) > 0 ? 3000 : false;
    },
  });

  // Tick elapsed timer every second while snapshots are active
  useEffect(() => {
    const hasActive = (activeQ.data?.length ?? 0) > 0;
    if (!hasActive) return;
    const id = setInterval(() => setElapsedTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [activeQ.data]);

  // Detect when active snapshots transition from >0 to 0 and refresh data
  const prevActiveCount = useRef(0);
  useEffect(() => {
    const count = activeQ.data?.length ?? 0;
    if (prevActiveCount.current > 0 && count === 0) {
      queryClient.invalidateQueries({ queryKey: ["inventory-snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-counties"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-summary"] });
    }
    prevActiveCount.current = count;
  }, [activeQ.data, queryClient]);

  const counties = countiesQ.data ?? [];
  const runnableCounties = counties.filter((c) => c.has_endpoint && c.is_active);
  const inventory = inventoryQ.data ?? [];
  const builders = buildersQ.data ?? [];
  const snapshots = snapshotsQ.data ?? [];

  const totalLots = inventory.reduce((s, c) => s + c.total, 0);
  const totalCounties = inventory.length;
  const totalBuilders = builders.filter((b) => b.is_active).length;

  // Last successful snapshot info
  const lastSnapshot = deriveLastSnapshot(counties);

  // Build county name lookup for active snapshots display
  const countyNameMap = new Map(counties.map((c) => [c.id, c.name]));

  // Recent failed snapshots for error display
  const recentFailed = snapshots.filter(
    (s) => s.status === "failed" && s.error_message
  );

  const handleRunClick = () => {
    if (selectedCounty) {
      const county = counties.find((c) => c.id === selectedCounty);
      setConfirmState({ label: `Run snapshot for ${county?.name ?? "selected county"}?` });
    } else {
      setConfirmState({ label: `Run snapshot for all ${runnableCounties.length} counties?` });
    }
  };

  const handleConfirm = async () => {
    setConfirmState(null);
    setTriggering(true);
    try {
      await triggerSnapshot(selectedCounty ?? undefined);
      queryClient.invalidateQueries({ queryKey: ["active-snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-counties"] });
    } catch {
      alert("Failed to trigger snapshot");
    } finally {
      setTriggering(false);
    }
  };

  const handleCancel = () => {
    setConfirmState(null);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Builder Inventory</h1>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card label="Active Lots" value={fmt(totalLots)} />
        <Card label="Counties" value={String(totalCounties)} />
        <Card label="Active Builders" value={String(totalBuilders)} />
        <Card label="Last Snapshot" value={lastSnapshot.label} small />
      </div>

      {/* Run Snapshot controls */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Run Snapshot
        </h2>
        <div className="flex items-end gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">County</label>
            <select
              value={selectedCounty ?? ""}
              onChange={(e) => setSelectedCounty(e.target.value ? Number(e.target.value) : null)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white min-w-[200px]"
            >
              <option value="">All Counties ({runnableCounties.length})</option>
              {runnableCounties.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                  {c.last_snapshot_at ? ` (last: ${fmtDate(c.last_snapshot_at)})` : " (never run)"}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleRunClick}
            disabled={triggering || confirmState !== null}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {triggering ? "Triggering..." : selectedCounty ? "Run Selected" : "Run All"}
          </button>
        </div>

        {/* Inline confirm dialog */}
        {confirmState && (
          <div className="mt-3 flex items-center gap-3 bg-amber-50 border border-amber-200 rounded px-4 py-2.5">
            <span className="text-sm text-amber-800">{confirmState.label}</span>
            <button
              onClick={handleCancel}
              className="px-3 py-1 text-sm rounded border border-gray-300 text-gray-600 hover:bg-gray-100"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Confirm
            </button>
          </div>
        )}

        {/* Active snapshots with progress */}
        {(activeQ.data?.length ?? 0) > 0 && (
          <div className="mt-4 space-y-3">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
              Running
            </h3>
            {activeQ.data!.map((snap) => {
              const elapsed = Date.now() - new Date(snap.started_at).getTime();
              const minutes = Math.floor(elapsed / 60_000);
              const seconds = Math.floor((elapsed % 60_000) / 1000);
              const pct = snap.progress_total > 0
                ? Math.round((snap.progress_current / snap.progress_total) * 100)
                : 0;
              // elapsedTick is used to force re-render every second
              void elapsedTick;
              return (
                <div key={snap.id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-gray-700">
                      {countyNameMap.get(snap.county_id) ?? `County #${snap.county_id}`}
                    </span>
                    <span className="text-gray-400 tabular-nums">
                      {minutes}m {seconds}s
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 tabular-nums whitespace-nowrap">
                      {snap.progress_current} / {snap.progress_total} builders
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Recent failed snapshot errors */}
        {recentFailed.length > 0 && (
          <div className="mt-4 space-y-2">
            {recentFailed.map((snap) => (
              <div
                key={snap.id}
                className="bg-red-50 border border-red-200 rounded px-4 py-2.5 text-sm text-red-700"
              >
                <span className="font-medium">
                  {countyNameMap.get(snap.county_id) ?? `County #${snap.county_id}`} failed:
                </span>{" "}
                {snap.error_message}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Inventory drill-down + builders side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Inventory Drill-Down
          </h2>
          <DrillDownTable />
        </div>

        <BuilderTable builders={builders} isLoading={buildersQ.isLoading} />
      </div>

      {/* Most recent snapshot */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Most Recent Snapshot
        </h2>
        {snapshotsQ.isLoading ? (
          <p className="text-sm text-gray-400">Loading...</p>
        ) : snapshots.length === 0 ? (
          <p className="text-sm text-gray-400">No snapshots yet.</p>
        ) : (
          <MostRecentSnapshot snapshots={snapshots} counties={counties} />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function deriveLastSnapshot(counties: InventoryCounty[]): { label: string } {
  const withSnapshots = counties
    .filter((c) => c.last_snapshot_at)
    .sort((a, b) => new Date(b.last_snapshot_at!).getTime() - new Date(a.last_snapshot_at!).getTime());

  if (withSnapshots.length === 0) return { label: "Never" };

  const latest = withSnapshots[0];
  const latestDate = fmtDate(latest.last_snapshot_at!);
  const sameDay = withSnapshots.filter(
    (c) => fmtDate(c.last_snapshot_at!) === latestDate
  );

  if (sameDay.length <= 3) {
    return { label: `${sameDay.map((c) => c.name).join(", ")} — ${latestDate}` };
  }
  return { label: `${sameDay.length} counties — ${latestDate}` };
}

function MostRecentSnapshot({
  snapshots,
  counties,
}: {
  snapshots: { id: number; county_id: number; started_at: string; completed_at: string | null; status: string; total_parcels_queried: number; new_count: number; removed_count: number; changed_count: number }[];
  counties: InventoryCounty[];
}) {
  const countyMap = new Map(counties.map((c) => [c.id, c.name]));

  // Group snapshots by started_at date (same run batch)
  const latest = snapshots[0];
  if (!latest) return <p className="text-sm text-gray-400">No snapshots.</p>;

  // Find all snapshots from the same run (within 1 minute of the latest)
  const latestTime = new Date(latest.started_at).getTime();
  const batch = snapshots.filter(
    (s) => Math.abs(new Date(s.started_at).getTime() - latestTime) < 60_000
  );

  const countyNames = batch.map((s) => countyMap.get(s.county_id) ?? `County #${s.county_id}`);
  const countyLabel =
    countyNames.length <= 3
      ? countyNames.join(", ")
      : `${countyNames.length} counties`;

  const totalNew = batch.reduce((s, b) => s + b.new_count, 0);
  const totalRemoved = batch.reduce((s, b) => s + b.removed_count, 0);
  const totalChanged = batch.reduce((s, b) => s + b.changed_count, 0);
  const totalQueried = batch.reduce((s, b) => s + b.total_parcels_queried, 0);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <SnapshotBadge status={latest.status} />
        <span className="text-sm font-medium text-gray-800">{countyLabel}</span>
        <span className="text-sm text-gray-500">
          {new Date(latest.started_at).toLocaleString()}
        </span>
      </div>
      <div className="flex gap-6 text-sm">
        <span className="text-gray-500">
          Queried: <span className="font-medium text-gray-700 tabular-nums">{fmt(totalQueried)}</span>
        </span>
        <span className="text-emerald-600 tabular-nums">
          +{totalNew} new
        </span>
        <span className="text-red-600 tabular-nums">
          -{totalRemoved} removed
        </span>
        <span className="text-amber-600 tabular-nums">
          {totalChanged} changed
        </span>
      </div>
    </div>
  );
}

function Card({ label, value, small }: { label: string; value: string; small?: boolean }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </p>
      <p className={`font-semibold text-gray-800 tabular-nums ${small ? "text-sm" : "text-2xl"}`}>
        {value}
      </p>
    </div>
  );
}

function SnapshotBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    running: "bg-blue-100 text-blue-700 animate-pulse",
    failed: "bg-red-100 text-red-700",
    pending: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? styles.pending}`}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Builder table with type filter
// ---------------------------------------------------------------------------

type BuilderType = "all" | "builder" | "developer" | "land_banker" | "btr";
const BUILDER_TYPE_OPTIONS: { key: BuilderType; label: string }[] = [
  { key: "all", label: "All" },
  { key: "builder", label: "Builder" },
  { key: "developer", label: "Developer" },
  { key: "land_banker", label: "Land Banker" },
  { key: "btr", label: "BTR" },
];

function BuilderTable({
  builders,
  isLoading,
}: {
  builders: { id: number; canonical_name: string; type: string }[];
  isLoading: boolean;
}) {
  const [typeFilter, setTypeFilter] = useState<BuilderType>("all");

  const allTypes = ["builder", "developer", "land_banker", "btr"];

  // Lot counts + lot acreage per builder
  const lotInvQ = useQuery({
    queryKey: ["inventory-summary-lot-all-types"],
    queryFn: () => getInventorySummary({ parcel_class: "lot", entity_type: allTypes }),
  });

  // Total acreage (all parcel classes) per builder — for undeveloped acreage calc
  const allInvQ = useQuery({
    queryKey: ["inventory-summary-all-classes"],
    queryFn: () => getInventorySummary({ entity_type: allTypes }),
  });

  // Aggregate per builder: parcel count, lot acreage, total acreage
  const builderAgg = new Map<number, { parcels: number; lotAcreage: number; totalAcreage: number }>();
  for (const county of lotInvQ.data ?? []) {
    for (const b of county.builders) {
      const entry = builderAgg.get(b.builder_id) ?? { parcels: 0, lotAcreage: 0, totalAcreage: 0 };
      entry.parcels += b.count;
      entry.lotAcreage += b.acreage;
      builderAgg.set(b.builder_id, entry);
    }
  }
  for (const county of allInvQ.data ?? []) {
    for (const b of county.builders) {
      const entry = builderAgg.get(b.builder_id) ?? { parcels: 0, lotAcreage: 0, totalAcreage: 0 };
      entry.totalAcreage += b.acreage;
      builderAgg.set(b.builder_id, entry);
    }
  }

  const showAcreage = typeFilter === "land_banker" || typeFilter === "developer";

  const filtered = (typeFilter === "all"
    ? builders
    : builders.filter((b) => b.type === typeFilter)
  )
    .map((b) => {
      const agg = builderAgg.get(b.id) ?? { parcels: 0, lotAcreage: 0, totalAcreage: 0 };
      return {
        ...b,
        parcels: agg.parcels,
        undevelopedAcreage: agg.totalAcreage - agg.lotAcreage,
      };
    })
    .sort((a, b) => b.parcels - a.parcels);

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Builders
      </h2>

      {/* Type filter toggles */}
      <div className="flex items-center gap-1 mb-3">
        {BUILDER_TYPE_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => setTypeFilter(opt.key)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              typeFilter === opt.key
                ? "bg-blue-100 text-blue-700"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            }`}
          >
            {opt.label}
          </button>
        ))}
        {filtered.length > 0 && (
          <span className="text-xs text-gray-400 ml-2">{filtered.length}</span>
        )}
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-400">No builders match filter.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b border-gray-100">
              <th className="pb-2 font-medium">Name</th>
              <th className="pb-2 font-medium">Type</th>
              <th className="pb-2 font-medium text-right">Parcels</th>
              {showAcreage && <th className="pb-2 font-medium text-right">Undeveloped Acres</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((b) => (
              <tr key={b.id} className="border-b border-gray-50 last:border-0">
                <td className="py-1.5 text-gray-700 font-medium">{b.canonical_name}</td>
                <td className="py-1.5 text-gray-500">{b.type}</td>
                <td className="py-1.5 text-right text-gray-700 tabular-nums font-medium">{b.parcels.toLocaleString()}</td>
                {showAcreage && (
                  <td className="py-1.5 text-right text-gray-600 tabular-nums">
                    {b.undevelopedAcreage > 0 ? b.undevelopedAcreage.toLocaleString(undefined, { maximumFractionDigits: 1 }) : "—"}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
