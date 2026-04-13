import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  getStats,
  getPermitDashboard,
  getCommissionSummary,
  getInventoryCounties,
  getETLStatus,
  getReviewQueue,
  searchInventorySubdivisions,
  getPermitScrapeJobs,
  getInventorySnapshots,
} from "../api";

function fmt(n: number): string {
  return n.toLocaleString();
}

function relTime(iso: string | null | undefined): string {
  if (!iso) return "Never";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

const MODULE_COLORS = {
  transactions: { border: "border-blue-300", bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" },
  subdivisions: { border: "border-violet-300", bg: "bg-violet-50", text: "text-violet-700", dot: "bg-violet-500" },
  inventory: { border: "border-green-300", bg: "bg-green-50", text: "text-green-700", dot: "bg-green-500" },
  permits: { border: "border-amber-300", bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" },
  commission: { border: "border-rose-300", bg: "bg-rose-50", text: "text-rose-700", dot: "bg-rose-500" },
  pipeline: { border: "border-cyan-300", bg: "bg-cyan-50", text: "text-cyan-700", dot: "bg-cyan-500" },
} as const;

export default function DashboardPage() {
  const navigate = useNavigate();

  const statsQ = useQuery({ queryKey: ["stats"], queryFn: getStats });
  const permitsQ = useQuery({ queryKey: ["permit-dashboard"], queryFn: getPermitDashboard });
  const commissionQ = useQuery({ queryKey: ["commission-summary"], queryFn: getCommissionSummary });
  const inventoryQ = useQuery({ queryKey: ["inventory-counties"], queryFn: getInventoryCounties });
  const etlQ = useQuery({ queryKey: ["etl-status"], queryFn: getETLStatus });
  const reviewQ = useQuery({
    queryKey: ["review-queue", "", "", 1, 1],
    queryFn: () => getReviewQueue({ page: 1, page_size: 1 }),
  });
  const subdivisionsQ = useQuery({ queryKey: ["inventory-subdivisions-count"], queryFn: () => searchInventorySubdivisions({}) });
  const scrapeJobsQ = useQuery({
    queryKey: ["scrape-jobs-recent"],
    queryFn: () => getPermitScrapeJobs({ limit: 10 }),
  });
  const snapshotsQ = useQuery({
    queryKey: ["inventory-snapshots-recent"],
    queryFn: () => getInventorySnapshots({ limit: 10 }),
  });

  const stats = statsQ.data;
  const permits = permitsQ.data;
  const commission = commissionQ.data;
  const counties = inventoryQ.data ?? [];
  const etl = etlQ.data;
  const subdivisions = subdivisionsQ.data;
  const scrapeJobs = scrapeJobsQ.data;
  const snapshots = snapshotsQ.data;

  // Derive inventory freshness
  const latestSnapshot = counties
    .filter((c) => c.last_snapshot_at)
    .sort((a, b) => new Date(b.last_snapshot_at!).getTime() - new Date(a.last_snapshot_at!).getTime())[0];
  const inventoryLots = counties.reduce((s, c) => s + (c.last_snapshot_parcels ?? 0), 0);

  // Pipeline counts
  const recentScrapes = scrapeJobs?.jobs?.length ?? 0;
  const recentSnapshots = snapshots?.length ?? 0;

  // Action needed items
  const actionItems: { label: string; onClick: () => void; color: "amber" | "blue" | "red" }[] = [];
  if ((stats?.flagged_for_review ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(stats!.flagged_for_review)} transactions flagged for review`,
      onClick: () => navigate("/transactions?unmatched_only=true"),
      color: "amber",
    });
  }
  if ((commission?.needs_review ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(commission!.needs_review)} commission actions need review`,
      onClick: () => navigate("/commission"),
      color: "amber",
    });
  }
  if ((reviewQ.data?.total ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(reviewQ.data!.total)} items in review queue`,
      onClick: () => navigate("/transactions?unmatched_only=true"),
      color: "blue",
    });
  }
  if (permits && permits.last_runs.some((r) => r.freshness === "stale" || r.freshness === "dead")) {
    actionItems.push({
      label: `${permits.last_runs.filter((r) => r.freshness !== "fresh").length} permit scrapers stale or dead`,
      onClick: () => navigate("/permits"),
      color: "red",
    });
  }
  if (etl?.status === "failed") {
    actionItems.push({
      label: "Last ETL run failed",
      onClick: () => navigate("/pipeline"),
      color: "red",
    });
  }

  const anyLoading = statsQ.isLoading || permitsQ.isLoading || commissionQ.isLoading || inventoryQ.isLoading;

  if (anyLoading) return <p className="text-gray-500 p-6">Loading dashboard...</p>;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* 6 Module Cards — 2x3 grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {/* Transactions */}
        <ModuleCard
          title="Transactions"
          color="transactions"
          onClick={() => navigate("/transactions")}
          stats={[
            { label: "Total", value: stats ? fmt(stats.total_transactions) : "—" },
            { label: "Counties", value: stats ? String(stats.by_county.length) : "—" },
            { label: "Flagged", value: stats ? fmt(stats.flagged_for_review) : "—", accent: (stats?.flagged_for_review ?? 0) > 0 },
          ]}
          footer={stats?.date_range ? `${stats.date_range.min} — ${stats.date_range.max}` : undefined}
          status={etl?.status === "running" ? "Running" : etl?.completed_at ? relTime(etl.completed_at) : "Idle"}
          statusColor={etl?.status === "running" ? "text-blue-600" : etl?.completed_at ? "text-green-600" : "text-gray-400"}
        />

        {/* Subdivisions */}
        <ModuleCard
          title="Subdivisions"
          color="subdivisions"
          onClick={() => navigate("/subdivisions")}
          stats={[
            { label: "Total", value: subdivisions ? fmt(subdivisions.length) : "—" },
            { label: "Counties", value: stats ? String(stats.by_county.length) : "—" },
          ]}
          status={subdivisions ? `${fmt(subdivisions.length)} loaded` : "—"}
          statusColor="text-gray-500"
        />

        {/* Inventory */}
        <ModuleCard
          title="Inventory"
          color="inventory"
          onClick={() => navigate("/inventory")}
          stats={[
            { label: "Active Lots", value: fmt(inventoryLots) },
            { label: "Counties", value: String(counties.filter((c) => c.has_endpoint).length) },
            { label: "Tracked", value: String(counties.length) },
          ]}
          status={latestSnapshot?.last_snapshot_at ? relTime(latestSnapshot.last_snapshot_at) : "Never"}
          statusColor={latestSnapshot ? "text-green-600" : "text-gray-400"}
        />

        {/* Permits */}
        <ModuleCard
          title="Permits"
          color="permits"
          onClick={() => navigate("/permits")}
          stats={[
            { label: "Total", value: permits ? fmt(permits.summary.total_permits) : "—" },
            { label: "This Month", value: permits ? fmt(permits.summary.current_month) : "—" },
            { label: "Watchlist", value: permits?.summary?.watchlist_count != null ? fmt(permits.summary.watchlist_count) : "—" },
          ]}
          footer={permits?.summary?.month_delta != null
            ? `${permits.summary.month_delta >= 0 ? "+" : ""}${permits.summary.month_delta} vs last month`
            : undefined}
          status={permits?.last_runs[0]?.last_success ? relTime(permits.last_runs[0].last_success) : "—"}
          statusColor={permits?.last_runs[0]?.freshness === "fresh" ? "text-green-600" : "text-amber-600"}
        />

        {/* Commission */}
        <ModuleCard
          title="Commission"
          color="commission"
          onClick={() => navigate("/commission")}
          stats={[
            { label: "Actions", value: commission ? fmt(commission.actions_extracted) : "—" },
            { label: "Projects", value: commission ? fmt(commission.projects_tracked) : "—" },
            { label: "Review", value: commission ? fmt(commission.needs_review) : "—", accent: (commission?.needs_review ?? 0) > 0 },
          ]}
          status={`${commission?.jurisdictions_active ?? 0} jurisdictions`}
          statusColor="text-gray-500"
        />

        {/* Pipeline */}
        <ModuleCard
          title="Pipeline"
          color="pipeline"
          onClick={() => navigate("/pipeline")}
          stats={[
            { label: "ETL", value: etl?.status ? etl.status.charAt(0).toUpperCase() + etl.status.slice(1) : "—" },
            { label: "Scrape Jobs", value: String(recentScrapes) },
            { label: "Snapshots", value: String(recentSnapshots) },
          ]}
          status={etl?.completed_at ? relTime(etl.completed_at) : etl?.started_at ? relTime(etl.started_at) : "—"}
          statusColor={
            etl?.status === "failed" ? "text-red-600"
              : etl?.status === "running" ? "text-blue-600"
                : etl?.status === "completed" ? "text-green-600"
                  : "text-gray-400"
          }
        />
      </div>

      {/* Action Needed — only when items exist */}
      {actionItems.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Action Needed
          </h2>
          <div className="space-y-2">
            {actionItems.map((item) => (
              <ActionItem key={item.label} {...item} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ModuleCard({
  title,
  color,
  onClick,
  stats,
  footer,
  status,
  statusColor,
}: {
  title: string;
  color: keyof typeof MODULE_COLORS;
  onClick: () => void;
  stats: { label: string; value: string; accent?: boolean }[];
  footer?: string;
  status: string;
  statusColor: string;
}) {
  const c = MODULE_COLORS[color];
  return (
    <button
      onClick={onClick}
      className={`bg-white border border-gray-200 rounded-xl p-5 text-left hover:${c.border} hover:shadow-md transition-all group`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${c.dot}`} />
          <h3 className={`text-sm font-bold uppercase tracking-wide ${c.text}`}>{title}</h3>
        </div>
        <span className={`text-xs font-medium ${statusColor}`}>{status}</span>
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-2">
        {stats.map((s) => (
          <div key={s.label}>
            <div className={`text-xl font-bold tabular-nums ${s.accent ? "text-amber-600" : "text-gray-800"}`}>
              {s.value}
            </div>
            <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>
      {footer && (
        <div className="mt-3 text-xs text-gray-400">{footer}</div>
      )}
      <div className={`mt-3 text-xs font-medium ${c.text} opacity-0 group-hover:opacity-100 transition-opacity`}>
        View details &rarr;
      </div>
    </button>
  );
}

function ActionItem({
  label,
  onClick,
  color,
}: {
  label: string;
  onClick: () => void;
  color: "amber" | "blue" | "red";
}) {
  const colors = {
    amber: "bg-amber-50 border-amber-200 text-amber-800 hover:bg-amber-100",
    blue: "bg-blue-50 border-blue-200 text-blue-800 hover:bg-blue-100",
    red: "bg-red-50 border-red-200 text-red-800 hover:bg-red-100",
  };
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors ${colors[color]}`}
    >
      {label}
    </button>
  );
}
