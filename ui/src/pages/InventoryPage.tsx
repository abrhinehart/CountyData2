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

  if (isLoading) {
    return (
      <div className="surface-card panel-pad">
        <p className="data-note">Loading trend data...</p>
      </div>
    );
  }
  if (!rawPoints || rawPoints.length === 0) return null;

  return (
    <div className="surface-card panel-pad">
      <div className="section-head mb-3">
        <div>
          <h2 className="section-title">Inventory Trend</h2>
          <p className="section-caption">{chartTitle}</p>
        </div>
        <div className="flex gap-2 items-center">
          <select
            className="form-control min-w-[140px]"
            value={trendCounty ?? ""}
            onChange={(e) => setTrendCounty(e.target.value ? Number(e.target.value) : undefined)}
          >
            <option value="">All Counties</option>
            {counties.sort((a, b) => a.name.localeCompare(b.name)).map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
          <select
            className="form-control min-w-[110px]"
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
        <div className="table-empty text-center">
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
    <div className="surface-card panel-pad">
      <div className="section-head mb-3">
        <div>
          <h2 className="section-title">Top Entities</h2>
          <p className="section-caption">Most active builders across current filters.</p>
        </div>
      </div>
      <div className="data-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-9 text-center">#</th>
              <th className="text-left">Entity</th>
              <th className="text-right">Lots</th>
              <th className="text-right">Counties</th>
            </tr>
          </thead>
          <tbody>
            {leaders.map((l, i) => (
              <tr key={l.id}>
                <td className="text-center text-xs text-[var(--text-soft)]">{i + 1}</td>
                <td className="font-medium">{l.name}</td>
                <td className="text-right font-semibold tabular-nums">{l.total.toLocaleString()}</td>
                <td className="text-right tabular-nums text-[var(--text-muted)]">{l.counties}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
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
      if (next.has(id)) next.delete(id);
      else next.add(id);
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
    <div className="surface-card panel-pad">
      <div className="section-head mb-4">
        <div>
          <h2 className="section-title">County Drilldown</h2>
          <p className="section-caption">Expand counties into builders and subdivision counts.</p>
        </div>
      </div>
      <div className="flex items-center gap-3 mb-4">
        <input
          type="search"
          placeholder="Search counties..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="form-control max-w-xs"
        />
        {search && (
          <span className="data-note">
            {filtered.length} result{filtered.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {filtered.length === 0 ? (
        <p className="table-empty">No inventory data for this filter.</p>
      ) : (
        <div className="data-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th
                className="cursor-pointer select-none text-left"
                onClick={() => toggleSort("name")}
              >
                County{arrow("name")}
              </th>
              <th className="w-24 text-center">
                Entities
              </th>
              <th
                className="w-32 cursor-pointer select-none text-right"
                onClick={() => toggleSort("total")}
              >
                Parcels{arrow("total")}
              </th>
              <th className="w-40 text-left">
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
            <tr>
              <td className="font-semibold">Total ({filtered.length} counties)</td>
              <td></td>
              <td className="text-right font-bold tabular-nums">{filtered.reduce((s, c) => s + c.total, 0).toLocaleString()}</td>
              <td></td>
            </tr>
          </tbody>
        </table>
        </div>
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
        className={`cursor-pointer border-l-4 transition-colors ${
          isOpen
            ? "border-l-[var(--accent)] bg-[rgba(29,78,216,0.08)] hover:bg-[rgba(29,78,216,0.12)]"
            : "border-l-transparent"
        }`}
        onClick={onToggle}
      >
        <td className="text-base font-semibold">{county.county}</td>
        <td className="text-center text-sm text-[var(--text-muted)]">{county.builders.length}</td>
        <td className="text-right text-base font-bold tabular-nums text-[var(--accent)]">{county.total.toLocaleString()}</td>
        <td className="whitespace-nowrap text-sm">
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
        className={`cursor-pointer border-l-4 border-l-[var(--accent)] transition-colors ${
          isExpanded
            ? "bg-[rgba(29,78,216,0.12)] hover:bg-[rgba(29,78,216,0.16)]"
            : "bg-[rgba(29,78,216,0.05)] hover:bg-[rgba(29,78,216,0.1)]"
        }`}
        onClick={onToggle}
      >
        <td className="pl-10 text-sm font-medium">{builderName}</td>
        <td></td>
        <td className="text-right text-sm font-semibold tabular-nums text-[var(--accent)]">{count.toLocaleString()}</td>
        <td></td>
      </tr>
      {isExpanded && (
        detailQ.isLoading ? (
          <tr className="border-l-4 border-l-[var(--accent)] bg-[var(--surface-muted)]">
            <td colSpan={4} className="pl-16 text-sm text-[var(--text-soft)]">Loading subdivisions...</td>
          </tr>
        ) : subdivisions.length === 0 ? (
          <tr className="border-l-4 border-l-[var(--accent)] bg-[var(--surface-muted)]">
            <td colSpan={4} className="pl-16 text-sm text-[var(--text-soft)]">No subdivision data</td>
          </tr>
        ) : (
          subdivisions.map((s) => (
            <tr key={s.subdivision_id ?? s.subdivision} className="border-l-4 border-l-[var(--accent)] bg-[var(--surface-muted)]">
              <td className="pl-16 text-sm text-[var(--text-muted)]">{s.subdivision}</td>
              <td></td>
              <td className="text-right text-sm tabular-nums text-[var(--text-muted)]">{s.total.toLocaleString()}</td>
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
    <div className="surface-card panel-pad">
      <div className="section-head mb-3">
        <div>
          <h2 className="section-title">Run Snapshot</h2>
          <p className="section-caption">Trigger county refreshes and monitor live snapshot progress.</p>
        </div>
      </div>
      <div className="filter-grid items-end">
        <div className="field-stack">
          <label className="field-label" htmlFor="snapshot-county">County</label>
          <select
            id="snapshot-county"
            value={selectedCounty ?? ""}
            onChange={(e) => setSelectedCounty(e.target.value ? Number(e.target.value) : null)}
            className="form-control min-w-[240px]"
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
          className="button-primary"
        >
          {triggering ? "Triggering..." : selectedCounty ? "Run Selected" : "Run All"}
        </button>
      </div>

      {confirmState && (
        <div className="mt-3 flex flex-wrap items-center gap-3 rounded-[var(--radius-lg)] border border-[rgba(161,98,7,0.28)] bg-[rgba(161,98,7,0.08)] px-4 py-2.5">
          <span className="text-sm text-[var(--warning)]">{confirmState.label}</span>
          <button onClick={() => setConfirmState(null)} className="button-ghost">Cancel</button>
          <button onClick={handleConfirm} className="button-primary">Confirm</button>
        </div>
      )}

      {(activeQ.data?.length ?? 0) > 0 && (
        <div className="mt-4 space-y-3">
          <h3 className="field-label">Running</h3>
          {activeQ.data!.map((snap) => {
            const elapsed = Date.now() - new Date(snap.started_at).getTime();
            const minutes = Math.floor(elapsed / 60_000);
            const seconds = Math.floor((elapsed % 60_000) / 1000);
            const pct = snap.progress_total > 0 ? Math.round((snap.progress_current / snap.progress_total) * 100) : 0;
            void elapsedTick;
            return (
              <div key={snap.id} className="surface-muted space-y-1 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] px-3 py-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium text-[var(--text)]">{countyNameMap.get(snap.county_id) ?? `County #${snap.county_id}`}</span>
                  <span className="tabular-nums text-[var(--text-soft)]">{minutes}m {seconds}s</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-[rgba(214,211,209,0.8)]">
                    <div className="h-full rounded-full bg-[var(--accent)] transition-all" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="whitespace-nowrap text-xs tabular-nums text-[var(--text-muted)]">{snap.progress_current} / {snap.progress_total} builders</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {recentFailed.length > 0 && (
        <div className="mt-4 space-y-2">
          {recentFailed.map((snap) => (
            <div key={snap.id} className="rounded-[var(--radius-lg)] border border-[rgba(185,28,28,0.24)] bg-[rgba(185,28,28,0.08)] px-4 py-2.5 text-sm text-[var(--danger)]">
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
  const counties = useMemo(() => countiesQ.data ?? [], [countiesQ.data]);

  const snapshotMap = useMemo(() => {
    const m = new Map<number, string | null>();
    for (const c of counties) m.set(c.id, c.last_snapshot_at);
    return m;
  }, [counties]);

  const countyNameMap = useMemo(() => new Map(counties.map((c) => [c.id, c.name])), [counties]);

  const grandTotal = data?.reduce((sum, c) => sum + c.total, 0) ?? 0;
  const totalEntities = new Set(data?.flatMap((c) => c.builders.map((b) => b.builder_name)) ?? []).size;

  return (
    <div className="page-stack report-page">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Inventory Intelligence</p>
          <h1 className="page-title">Builder Inventory</h1>
          <p className="page-subtitle">
            Track lot ownership, snapshot freshness, and county-level builder mix from one report workspace.
          </p>
        </div>
      </div>

      <section className="filter-band">
        <div className="section-head">
          <div>
            <p className="section-title">Filters</p>
            <p className="section-caption">Switch parcel class and entity role before drilling into county detail.</p>
          </div>
        </div>
        <div className="chip-row">
          <span className="field-label mr-1">Parcels</span>
          {PARCEL_FILTERS.map((f) => (
            <button
              key={f.key}
              className={`chip-pill ${parcelFilter === f.key ? "active" : ""}`}
              onClick={() => setParcelFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="chip-row">
          <span className="field-label mr-1">Entity</span>
          {ENTITY_FILTERS.map((f) => (
            <button
              key={f.key}
              className={`chip-pill ${entityFilter === f.key ? "active" : ""}`}
              onClick={() => setEntityFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </section>

      {isLoading ? (
        <p className="data-note">Loading...</p>
      ) : error ? (
        <p className="data-note text-[var(--danger)]">Error loading inventory</p>
      ) : (
        <>
          <section className="hero-band panel-pad">
            <div className="section-head">
              <div>
                <p className="section-title text-slate-50">Inventory posture</p>
                <p className="section-caption text-slate-300">
                  Coverage, lot totals, and active entities for the current inventory slice.
                </p>
              </div>
            </div>
            <div className="hero-grid">
              <div className="hero-stat">
                <span className="hero-label">Counties reporting</span>
                <span className="hero-value">{String(data?.length ?? 0)}</span>
                <span className="hero-meta">Current feed footprint</span>
              </div>
              <div className="hero-stat">
                <span className="hero-label">Total parcels</span>
                <span className="hero-value">{fmt(grandTotal)}</span>
                <span className="hero-meta">Across visible counties</span>
              </div>
              <div className="hero-stat">
                <span className="hero-label">Active entities</span>
                <span className="hero-value">{String(totalEntities)}</span>
                <span className="hero-meta">Distinct names in current slice</span>
              </div>
            </div>
          </section>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
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
  const tone = accent === "green" ? "" : accent === "purple" ? "warn" : "";
  return (
    <div className={`metric-card ${tone}`.trim()}>
      <p className="metric-label">{label}</p>
      <p className="metric-value">{value}</p>
    </div>
  );
}
