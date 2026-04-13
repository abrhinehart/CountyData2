import { useState, useRef, useEffect, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";
import {
  getInventoryCounties,
  getInventorySummary,
  getInventoryBuilders,
  getInventorySnapshots,
  getActiveSnapshots,
  getInventoryTrends,
  getInventoryCountyDetail,
  triggerSnapshot,
} from "../api";
import type { InventoryCounty, CountyInventory, TrendPoint } from "../types";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt(n: number): string {
  return n.toLocaleString();
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString();
}

function formatAge(isoDate: string | null): { text: string; stale: boolean } {
  if (!isoDate) return { text: "Never", stale: true };
  const ms = Date.now() - new Date(isoDate).getTime();
  const hours = ms / 3_600_000;
  if (hours < 1) return { text: `${Math.round(hours * 60)}m ago`, stale: false };
  if (hours < 24) return { text: `${Math.round(hours)}h ago`, stale: false };
  const days = Math.round(hours / 24);
  return { text: `${days}d ago`, stale: days > 7 };
}

type EntityType = "builder" | "developer" | "land_banker" | "btr";

const PARCEL_FILTERS = [
  { key: "lots", label: "Lots", classes: ["lot"] },
  { key: "hoa", label: "HOA", classes: ["common_area"] },
  { key: "raw_land", label: "Raw Land", classes: ["tract"] },
  { key: "other", label: "Other", classes: ["other"] },
] as const;

const ENTITY_FILTERS: { key: EntityType; label: string }[] = [
  { key: "builder", label: "Builders" },
  { key: "developer", label: "Developers" },
  { key: "land_banker", label: "Land Bankers" },
  { key: "btr", label: "BTR" },
];

// ---------------------------------------------------------------------------
// Trend Chart
// ---------------------------------------------------------------------------

function aggregateByDate(points: TrendPoint[]) {
  const byDate = new Map<string, { total: number; new_count: number; removed_count: number }>();
  for (const p of points) {
    const day = p.date.slice(0, 10);
    const existing = byDate.get(day);
    if (existing) {
      existing.total += p.total_parcels;
      existing.new_count += p.new_count;
      existing.removed_count += p.removed_count;
    } else {
      byDate.set(day, { total: p.total_parcels, new_count: p.new_count, removed_count: p.removed_count });
    }
  }
  return Array.from(byDate.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, v]) => ({
      date,
      label: new Date(date + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      ...v,
    }));
}

function singleCountyByDate(points: TrendPoint[], countyId: number) {
  return points
    .filter((p) => p.county_id === countyId)
    .map((p) => ({
      date: p.date.slice(0, 10),
      label: new Date(p.date.slice(0, 10) + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric" }),
      total: p.total_parcels,
      new_count: p.new_count,
      removed_count: p.removed_count,
    }))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function formatTooltipValue(value: ValueType | undefined): string {
  if (Array.isArray(value)) return value.map((i) => (typeof i === "number" ? i.toLocaleString() : i)).join(", ");
  if (value == null) return "";
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}

function formatTooltipName(name: NameType | undefined): string {
  if (name === "total") return "Total Parcels";
  if (name === "new_count") return "New";
  if (name === "removed_count") return "Removed";
  return name == null ? "" : String(name);
}

function TrendChart({ counties }: { counties: { id: number; name: string }[] }) {
  const [trendCounty, setTrendCounty] = useState<number | undefined>(undefined);
  const [trendDays, setTrendDays] = useState(90);

  const { data: rawPoints, isLoading } = useQuery({
    queryKey: ["inventory-trends", trendDays],
    queryFn: () => getInventoryTrends(undefined, trendDays),
  });

  const chartData = useMemo(() => {
    if (!rawPoints || rawPoints.length === 0) return [];
    if (trendCounty != null) return singleCountyByDate(rawPoints, trendCounty);
    return aggregateByDate(rawPoints);
  }, [rawPoints, trendCounty]);

  const chartTitle = trendCounty != null
    ? counties.find((c) => c.id === trendCounty)?.name ?? "County"
    : "All Counties";

  if (isLoading) return <div className="bg-white border border-gray-200 rounded-lg p-5"><p className="text-sm text-gray-400">Loading trend data...</p></div>;
  if (!rawPoints || rawPoints.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
          Inventory Trend — {chartTitle}
        </h2>
        <div className="flex gap-2 items-center">
          <select
            className="border border-gray-300 rounded px-2 py-1 text-sm bg-white min-w-[140px]"
            value={trendCounty ?? ""}
            onChange={(e) => setTrendCounty(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">All Counties</option>
            {counties.sort((a, b) => a.name.localeCompare(b.name)).map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select
            className="border border-gray-300 rounded px-2 py-1 text-sm bg-white min-w-[90px]"
            value={trendDays}
            onChange={(e) => setTrendDays(Number(e.target.value))}
          >
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={180}>180 days</option>
            <option value={365}>1 year</option>
          </select>
        </div>
      </div>
      {chartData.length < 2 ? (
        <div className="text-gray-400 text-sm py-8 text-center">
          Not enough data points to chart. Run more snapshots to see trends.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
            <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} tickFormatter={(v: number) => v.toLocaleString()} width={60} />
            <Tooltip
              contentStyle={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: "0.8rem", boxShadow: "0 4px 6px -1px rgba(0,0,0,0.1)" }}
              formatter={(value, name) => [formatTooltipValue(value), formatTooltipName(name)]}
              labelFormatter={(label) => label}
            />
            <Line type="monotone" dataKey="total" stroke="#2563eb" strokeWidth={2} dot={{ r: 3, fill: "#2563eb" }} activeDot={{ r: 5 }} name="total" />
            <Line type="monotone" dataKey="new_count" stroke="#16a34a" strokeWidth={1.5} dot={false} strokeDasharray="4 3" name="new_count" />
            <Line type="monotone" dataKey="removed_count" stroke="#dc2626" strokeWidth={1.5} dot={false} strokeDasharray="4 3" name="removed_count" />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Leaderboard
// ---------------------------------------------------------------------------

function Leaderboard({ data }: { data: CountyInventory[] | undefined }) {
  const leaders = useMemo(() => {
    if (!data) return [];
    const map = new Map<number, { id: number; name: string; total: number; counties: number }>();
    for (const county of data) {
      for (const b of county.builders) {
        const existing = map.get(b.builder_id);
        if (existing) {
          existing.total += b.count;
          existing.counties += 1;
        } else {
          map.set(b.builder_id, { id: b.builder_id, name: b.builder_name, total: b.count, counties: 1 });
        }
      }
    }
    return Array.from(map.values())
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);
  }, [data]);

  if (leaders.length === 0) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
        Top Entities
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left border-b border-gray-200">
            <th className="pb-2 w-9 text-center text-gray-400 font-medium">#</th>
            <th className="pb-2 text-gray-400 font-medium">Entity</th>
            <th className="pb-2 text-right text-gray-400 font-medium">Lots</th>
            <th className="pb-2 text-right text-gray-400 font-medium">Counties</th>
          </tr>
        </thead>
        <tbody>
          {leaders.map((l, i) => (
            <tr key={l.id} className="border-b border-gray-50 last:border-0">
              <td className="py-1.5 text-center text-gray-400 text-xs">{i + 1}</td>
              <td className="py-1.5 font-medium text-gray-800">{l.name}</td>
              <td className="py-1.5 text-right tabular-nums font-semibold text-gray-800">{l.total.toLocaleString()}</td>
              <td className="py-1.5 text-right tabular-nums text-gray-500">{l.counties}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Expandable county table
// ---------------------------------------------------------------------------

function FreshnessDot({ age }: { age: { text: string; stale: boolean; never?: boolean } }) {
  const color = age.never ? "bg-red-400" : age.stale ? "bg-amber-400" : "bg-green-400";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block w-2 h-2 rounded-full ${color}`} />
      <span className={age.stale ? "text-amber-600" : "text-gray-500"}>{age.text}</span>
    </span>
  );
}

function CountyTable({
  data,
  snapshotMap,
}: {
  data: CountyInventory[];
  snapshotMap: Map<number, string | null>;
}) {
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [sortBy, setSortBy] = useState<"name" | "total">("total");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const filtered = data
    .filter((c) => c.county.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      const mul = sortDir === "asc" ? 1 : -1;
      if (sortBy === "name") return mul * a.county.localeCompare(b.county);
      return mul * (a.total - b.total);
    });

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function toggleSort(col: "name" | "total") {
    if (sortBy === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortBy(col); setSortDir(col === "name" ? "asc" : "desc"); }
  }

  const arrow = (col: "name" | "total") =>
    sortBy === col ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : "";

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <div className="flex items-center gap-3 mb-4">
        <input
          type="search"
          placeholder="Search counties..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white w-72"
        />
        {search && (
          <span className="text-xs text-gray-400">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="text-sm text-gray-400 py-4">No inventory data for this filter.</p>
      ) : (
        <table className="w-full">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th
                className="py-3 px-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none"
                onClick={() => toggleSort("name")}
              >
                County{arrow("name")}
              </th>
              <th className="py-3 px-4 text-center text-xs font-semibold text-gray-500 uppercase tracking-wide w-24">
                Entities
              </th>
              <th
                className="py-3 px-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer select-none w-32"
                onClick={() => toggleSort("total")}
              >
                Parcels{arrow("total")}
              </th>
              <th className="py-3 pl-10 pr-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide w-40">
                Last Scanned
              </th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((county) => {
              const isOpen = expanded.has(county.county_id);
              const age = formatAge(snapshotMap.get(county.county_id) ?? null);
              return (
                <CountyRow
                  key={county.county_id}
                  county={county}
                  age={{ ...age, never: !snapshotMap.get(county.county_id) }}
                  isOpen={isOpen}
                  onToggle={() => toggleExpand(county.county_id)}
                />
              );
            })}
            <tr className="bg-gray-50 border-t-2 border-gray-200">
              <td className="py-3 px-4 font-semibold text-gray-700">Total ({filtered.length} counties)</td>
              <td></td>
              <td className="py-3 px-4 text-right font-bold tabular-nums text-gray-800 text-base">{filtered.reduce((s, c) => s + c.total, 0).toLocaleString()}</td>
              <td></td>
            </tr>
          </tbody>
        </table>
      )}
    </div>
  );
}

function CountyRow({
  county,
  age,
  isOpen,
  onToggle,
}: {
  county: CountyInventory;
  age: { text: string; stale: boolean; never?: boolean };
  isOpen: boolean;
  onToggle: () => void;
}) {
  const [expandedBuilder, setExpandedBuilder] = useState<number | null>(null);

  return (
    <>
      <tr
        className={`cursor-pointer transition-colors border-l-4 ${
          isOpen
            ? "border-l-blue-500 bg-blue-50/40 hover:bg-blue-50/60"
            : "border-l-transparent hover:bg-gray-50"
        }`}
        onClick={onToggle}
      >
        <td className="py-2.5 px-4 text-base font-semibold text-gray-800">{county.county}</td>
        <td className="py-2.5 px-4 text-center text-sm text-gray-500">{county.builders.length}</td>
        <td className="py-2.5 px-4 text-right font-bold tabular-nums text-blue-700 text-base">{county.total.toLocaleString()}</td>
        <td className="py-2.5 pl-10 pr-4 text-sm whitespace-nowrap">
          <FreshnessDot age={age} />
        </td>
      </tr>
      {isOpen &&
        county.builders
          .sort((a, b) => b.count - a.count)
          .map((b) => (
            <BuilderRow
              key={`${county.county_id}-${b.builder_id}`}
              countyId={county.county_id}
              builderId={b.builder_id}
              builderName={b.builder_name}
              count={b.count}
              isExpanded={expandedBuilder === b.builder_id}
              onToggle={() => setExpandedBuilder(expandedBuilder === b.builder_id ? null : b.builder_id)}
            />
          ))}
    </>
  );
}

function BuilderRow({
  countyId,
  builderId,
  builderName,
  count,
  isExpanded,
  onToggle,
}: {
  countyId: number;
  builderId: number;
  builderName: string;
  count: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  const detailQ = useQuery({
    queryKey: ["inventory-detail", countyId, builderId],
    queryFn: () => getInventoryCountyDetail(countyId, { builder_id: builderId }),
    enabled: isExpanded,
  });

  const subdivisions = useMemo(() => {
    if (!detailQ.data) return [];
    return detailQ.data.subdivisions
      .filter((s) => s.total > 0)
      .sort((a, b) => b.total - a.total);
  }, [detailQ.data]);

  return (
    <>
      <tr
        className={`cursor-pointer transition-colors border-l-4 border-l-blue-500 ${
          isExpanded
            ? "bg-blue-50/60 hover:bg-blue-100/50"
            : "bg-blue-50/20 hover:bg-blue-50/40"
        }`}
        onClick={onToggle}
      >
        <td className="py-2 pl-10 pr-4 text-sm font-medium text-gray-700">{builderName}</td>
        <td></td>
        <td className="py-2 px-4 text-right tabular-nums text-sm font-semibold text-blue-600">{count.toLocaleString()}</td>
        <td></td>
      </tr>
      {isExpanded && (
        detailQ.isLoading ? (
          <tr className="border-l-4 border-l-blue-500 bg-gray-50/50">
            <td colSpan={4} className="py-2 pl-16 pr-4 text-sm text-gray-400">Loading subdivisions...</td>
          </tr>
        ) : subdivisions.length === 0 ? (
          <tr className="border-l-4 border-l-blue-500 bg-gray-50/50">
            <td colSpan={4} className="py-2 pl-16 pr-4 text-sm text-gray-400">No subdivision data</td>
          </tr>
        ) : (
          subdivisions.map((s) => (
            <tr key={s.subdivision_id ?? s.subdivision} className="border-l-4 border-l-blue-500 bg-gray-50/40">
              <td className="py-1.5 pl-16 pr-4 text-sm text-gray-500">{s.subdivision}</td>
              <td></td>
              <td className="py-1.5 px-4 text-right tabular-nums text-sm text-gray-500">{s.total.toLocaleString()}</td>
              <td></td>
            </tr>
          ))
        )
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Snapshot controls (kept from CD2 — confirm, progress, errors)
// ---------------------------------------------------------------------------

function SnapshotControls({
  counties,
  countyNameMap,
}: {
  counties: InventoryCounty[];
  countyNameMap: Map<number, string>;
}) {
  const queryClient = useQueryClient();
  const [selectedCounty, setSelectedCounty] = useState<number | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [confirmState, setConfirmState] = useState<null | { label: string }>(null);
  const [elapsedTick, setElapsedTick] = useState(0);

  const activeQ = useQuery({
    queryKey: ["active-snapshots"],
    queryFn: getActiveSnapshots,
    refetchInterval: (query) => {
      return (query.state.data?.length ?? 0) > 0 ? 3000 : false;
    },
  });

  const snapshotsQ = useQuery({
    queryKey: ["inventory-snapshots"],
    queryFn: () => getInventorySnapshots({ limit: 5 }),
  });

  useEffect(() => {
    const hasActive = (activeQ.data?.length ?? 0) > 0;
    if (!hasActive) return;
    const id = setInterval(() => setElapsedTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [activeQ.data]);

  const prevActiveCount = useRef(0);
  useEffect(() => {
    const count = activeQ.data?.length ?? 0;
    if (prevActiveCount.current > 0 && count === 0) {
      queryClient.invalidateQueries({ queryKey: ["inventory-snapshots"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-counties"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-summary"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-trends"] });
    }
    prevActiveCount.current = count;
  }, [activeQ.data, queryClient]);

  const runnableCounties = counties.filter((c) => c.has_endpoint && c.is_active);
  const recentFailed = (snapshotsQ.data ?? []).filter((s) => s.status === "failed" && s.error_message);

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

  return (
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

      {confirmState && (
        <div className="mt-3 flex items-center gap-3 bg-amber-50 border border-amber-200 rounded px-4 py-2.5">
          <span className="text-sm text-amber-800">{confirmState.label}</span>
          <button onClick={() => setConfirmState(null)} className="px-3 py-1 text-sm rounded border border-gray-300 text-gray-600 hover:bg-gray-100">Cancel</button>
          <button onClick={handleConfirm} className="px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700">Confirm</button>
        </div>
      )}

      {(activeQ.data?.length ?? 0) > 0 && (
        <div className="mt-4 space-y-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">Running</h3>
          {activeQ.data!.map((snap) => {
            const elapsed = Date.now() - new Date(snap.started_at).getTime();
            const minutes = Math.floor(elapsed / 60_000);
            const seconds = Math.floor((elapsed % 60_000) / 1000);
            const pct = snap.progress_total > 0 ? Math.round((snap.progress_current / snap.progress_total) * 100) : 0;
            void elapsedTick;
            return (
              <div key={snap.id} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-gray-700">{countyNameMap.get(snap.county_id) ?? `County #${snap.county_id}`}</span>
                  <span className="text-gray-400 tabular-nums">{minutes}m {seconds}s</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 tabular-nums whitespace-nowrap">{snap.progress_current} / {snap.progress_total} builders</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {recentFailed.length > 0 && (
        <div className="mt-4 space-y-2">
          {recentFailed.map((snap) => (
            <div key={snap.id} className="bg-red-50 border border-red-200 rounded px-4 py-2.5 text-sm text-red-700">
              <span className="font-medium">{countyNameMap.get(snap.county_id) ?? `County #${snap.county_id}`} failed:</span>{" "}
              {snap.error_message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function InventoryPage() {
  const [parcelFilter, setParcelFilter] = useState("lots");
  const [entityFilter, setEntityFilter] = useState<EntityType>("builder");

  const parcelClasses = PARCEL_FILTERS.find((f) => f.key === parcelFilter)!.classes;
  const entityTypes = [entityFilter];

  const { data, isLoading, error } = useQuery({
    queryKey: ["inventory-summary", parcelFilter, entityFilter],
    queryFn: () => getInventorySummary({ parcel_class: [...parcelClasses][0], entity_type: [...entityTypes] }),
  });

  const countiesQ = useQuery({ queryKey: ["inventory-counties"], queryFn: getInventoryCounties });
  const counties = countiesQ.data ?? [];

  const snapshotMap = useMemo(() => {
    const m = new Map<number, string | null>();
    for (const c of counties) m.set(c.id, c.last_snapshot_at);
    return m;
  }, [counties]);

  const countyNameMap = useMemo(() => new Map(counties.map((c) => [c.id, c.name])), [counties]);

  const grandTotal = data?.reduce((sum, c) => sum + c.total, 0) ?? 0;
  const totalEntities = new Set(data?.flatMap((c) => c.builders.map((b) => b.builder_name)) ?? []).size;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Builder Inventory</h1>

      {/* Filter bar */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-1">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide mr-1">Parcels</span>
          {PARCEL_FILTERS.map((f) => (
            <button
              key={f.key}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                parcelFilter === f.key
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
              onClick={() => setParcelFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="h-5 w-px bg-gray-200" />
        <div className="flex items-center gap-1">
          <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide mr-1">Entity</span>
          {ENTITY_FILTERS.map((f) => (
            <button
              key={f.key}
              className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                entityFilter === f.key
                  ? "bg-blue-100 text-blue-700"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
              }`}
              onClick={() => setEntityFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-gray-400">Loading...</p>
      ) : error ? (
        <p className="text-sm text-red-500">Error loading inventory</p>
      ) : (
        <>
          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <Card label="Counties reporting" value={String(data?.length ?? 0)} accent="blue" />
            <Card label="Total parcels" value={fmt(grandTotal)} accent="green" />
            <Card label="Active entities" value={String(totalEntities)} accent="purple" />
          </div>

          {/* Trend chart */}
          <TrendChart counties={counties.filter((c) => c.is_active).map((c) => ({ id: c.id, name: c.name }))} />

          {/* Leaderboard + Snapshot controls side by side */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Leaderboard data={data} />
            <SnapshotControls counties={counties} countyNameMap={countyNameMap} />
          </div>

          {/* County table */}
          <CountyTable data={data ?? []} snapshotMap={snapshotMap} />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Stat card
// ---------------------------------------------------------------------------

function Card({ label, value, accent }: { label: string; value: string; accent: "blue" | "green" | "purple" }) {
  const border = { blue: "border-l-blue-500", green: "border-l-green-500", purple: "border-l-purple-500" }[accent];
  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-4 border-l-4 ${border}`}>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-semibold text-gray-800 tabular-nums">{value}</p>
    </div>
  );
}
