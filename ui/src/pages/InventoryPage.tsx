import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getInventoryCounties,
  getInventorySummary,
  getInventoryBuilders,
  getInventorySnapshots,
  triggerSnapshot,
} from "../api";
import type { InventoryCounty } from "../types";

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

  const handleTrigger = async () => {
    setTriggering(true);
    try {
      await triggerSnapshot(selectedCounty ?? undefined);
      queryClient.invalidateQueries({ queryKey: ["inventory-snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-counties"] });
    } catch {
      alert("Failed to trigger snapshot");
    } finally {
      setTriggering(false);
    }
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
            onClick={handleTrigger}
            disabled={triggering}
            className="px-4 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {triggering ? "Triggering..." : selectedCounty ? "Run Selected" : "Run All"}
          </button>
        </div>
      </div>

      {/* County inventory breakdown + builders side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Lots by County
          </h2>
          {inventoryQ.isLoading ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : inventory.length === 0 ? (
            <p className="text-sm text-gray-400">No inventory data.</p>
          ) : (
            <div className="space-y-2">
              {inventory.map((c) => (
                <div key={c.county_id} className="flex items-center gap-3">
                  <span className="text-sm font-medium text-gray-700 w-28 shrink-0">
                    {c.county}
                  </span>
                  <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                    <div
                      className="bg-emerald-500 h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max((c.total / totalLots) * 100, 2)}%`,
                      }}
                    />
                  </div>
                  <span className="text-sm text-gray-500 w-16 text-right tabular-nums">
                    {fmt(c.total)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Builders
          </h2>
          {buildersQ.isLoading ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : builders.length === 0 ? (
            <p className="text-sm text-gray-400">No builders.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-100">
                  <th className="pb-2 font-medium">Name</th>
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Scope</th>
                  <th className="pb-2 font-medium text-right">Aliases</th>
                </tr>
              </thead>
              <tbody>
                {builders.slice(0, 20).map((b) => (
                  <tr
                    key={b.id}
                    className="border-b border-gray-50 last:border-0"
                  >
                    <td className="py-1.5 text-gray-700 font-medium">{b.canonical_name}</td>
                    <td className="py-1.5 text-gray-500">{b.type}</td>
                    <td className="py-1.5 text-gray-500">{b.scope}</td>
                    <td className="py-1.5 text-right text-gray-500 tabular-nums">
                      {b.aliases.length}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
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
