import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  getStats,
  getPermitDashboard,
  getCommissionSummary,
  getInventoryCounties,
  getETLStatus,
  getReviewQueue,
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

  const stats = statsQ.data;
  const permits = permitsQ.data;
  const commission = commissionQ.data;
  const counties = inventoryQ.data ?? [];
  const etl = etlQ.data;

  // Derive inventory freshness
  const latestSnapshot = counties
    .filter((c) => c.last_snapshot_at)
    .sort((a, b) => new Date(b.last_snapshot_at!).getTime() - new Date(a.last_snapshot_at!).getTime())[0];
  const inventoryLots = counties.reduce((s, c) => s + (c.last_snapshot_parcels ?? 0), 0);

  const anyLoading = statsQ.isLoading || permitsQ.isLoading || commissionQ.isLoading || inventoryQ.isLoading;

  if (anyLoading) return <p className="text-gray-500">Loading dashboard...</p>;

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Module Health KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Sales / Transactions */}
        <ModuleCard
          title="Sales ETL"
          onClick={() => navigate("/transactions")}
          stats={[
            { label: "Transactions", value: stats ? fmt(stats.total_transactions) : "—" },
            { label: "Counties", value: stats ? String(stats.by_county.length) : "—" },
          ]}
          freshness={etl?.completed_at ? relTime(etl.completed_at) : etl?.status === "running" ? "Running..." : "Idle"}
          freshnessColor={etl?.status === "running" ? "text-blue-600" : etl?.completed_at ? "text-green-600" : "text-gray-400"}
        />

        {/* Permits */}
        <ModuleCard
          title="Permits"
          onClick={() => navigate("/permits")}
          stats={[
            { label: "This Month", value: permits ? fmt(permits.summary.current_month) : "—" },
            { label: "Total", value: permits ? fmt(permits.summary.total_permits) : "—" },
          ]}
          freshness={permits?.last_runs[0]?.last_success ? relTime(permits.last_runs[0].last_success) : "—"}
          freshnessColor={permits?.last_runs[0]?.freshness === "fresh" ? "text-green-600" : "text-amber-600"}
        />

        {/* Commission */}
        <ModuleCard
          title="Commission"
          onClick={() => navigate("/commission")}
          stats={[
            { label: "Actions", value: commission ? fmt(commission.actions_extracted) : "—" },
            { label: "Review", value: commission ? fmt(commission.needs_review) : "—", accent: (commission?.needs_review ?? 0) > 0 },
          ]}
          freshness={`${commission?.jurisdictions_active ?? 0} jurisdictions`}
          freshnessColor="text-gray-500"
        />

        {/* Inventory */}
        <ModuleCard
          title="Inventory"
          onClick={() => navigate("/inventory")}
          stats={[
            { label: "Active Lots", value: fmt(inventoryLots) },
            { label: "Counties", value: String(counties.filter((c) => c.has_endpoint).length) },
          ]}
          freshness={latestSnapshot?.last_snapshot_at ? relTime(latestSnapshot.last_snapshot_at) : "Never"}
          freshnessColor={latestSnapshot ? "text-green-600" : "text-gray-400"}
        />
      </div>

      {/* Action Needed section */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Action Needed
        </h2>
        <div className="space-y-2">
          {(stats?.flagged_for_review ?? 0) > 0 && (
            <ActionItem
              label={`${fmt(stats!.flagged_for_review)} transactions flagged for review`}
              onClick={() => navigate("/transactions?unmatched_only=true")}
              color="amber"
            />
          )}
          {(commission?.needs_review ?? 0) > 0 && (
            <ActionItem
              label={`${fmt(commission!.needs_review)} commission actions need review`}
              onClick={() => navigate("/commission")}
              color="amber"
            />
          )}
          {(reviewQ.data?.total ?? 0) > 0 && (
            <ActionItem
              label={`${fmt(reviewQ.data!.total)} items in review queue`}
              onClick={() => navigate("/transactions?unmatched_only=true")}
              color="blue"
            />
          )}
          {permits && permits.last_runs.some((r) => r.freshness === "stale" || r.freshness === "dead") && (
            <ActionItem
              label={`${permits.last_runs.filter((r) => r.freshness !== "fresh").length} permit scrapers stale or dead`}
              onClick={() => navigate("/permits")}
              color="red"
            />
          )}
          {etl?.status === "failed" && (
            <ActionItem
              label="Last ETL run failed"
              onClick={() => navigate("/pipeline")}
              color="red"
            />
          )}
          {!(stats?.flagged_for_review) && !(commission?.needs_review) && etl?.status !== "failed" && (
            <p className="text-sm text-gray-400">All clear — no items need attention.</p>
          )}
        </div>
      </div>

      {/* Two-column: County breakdown + Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* County breakdown */}
        {stats && (
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Transactions by County
            </h2>
            <div className="space-y-2">
              {stats.by_county.map((c) => {
                const totalByCounty = stats.by_county.reduce((s, x) => s + x.count, 0);
                return (
                  <button
                    key={c.county}
                    onClick={() => navigate(`/transactions?county=${encodeURIComponent(c.county)}`)}
                    className="w-full flex items-center gap-3 group text-left"
                  >
                    <span className="text-sm font-medium text-gray-700 w-28 shrink-0 group-hover:text-blue-700 transition-colors">
                      {c.county}
                    </span>
                    <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                      <div
                        className="bg-blue-500 h-full rounded-full transition-all"
                        style={{ width: `${Math.max((c.count / totalByCounty) * 100, 2)}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500 w-16 text-right tabular-nums">
                      {fmt(c.count)}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Permit trend + scraper health */}
        {permits && (
          <div className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Scraper Health
            </h2>
            <div className="space-y-2">
              {permits.last_runs.map((r) => (
                <div key={r.name} className="flex items-center gap-3 text-sm">
                  <FreshnessDot freshness={r.freshness} />
                  <span className="text-gray-700 flex-1 truncate">{r.name}</span>
                  <span className="text-gray-400 text-xs">
                    {r.last_success ? new Date(r.last_success).toLocaleDateString() : "Never"}
                  </span>
                </div>
              ))}
              {permits.last_runs.length === 0 && (
                <p className="text-sm text-gray-400">No scraper data.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ModuleCard({
  title,
  onClick,
  stats,
  freshness,
  freshnessColor,
}: {
  title: string;
  onClick: () => void;
  stats: { label: string; value: string; accent?: boolean }[];
  freshness: string;
  freshnessColor: string;
}) {
  return (
    <button
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-lg p-4 text-left hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{title}</h3>
        <span className={`text-xs ${freshnessColor}`}>{freshness}</span>
      </div>
      <div className="flex gap-4">
        {stats.map((s) => (
          <div key={s.label}>
            <div className={`text-lg font-semibold tabular-nums ${s.accent ? "text-amber-600" : "text-gray-800"}`}>
              {s.value}
            </div>
            <div className="text-xs text-gray-400">{s.label}</div>
          </div>
        ))}
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

function FreshnessDot({ freshness }: { freshness: string }) {
  const color =
    freshness === "fresh" ? "bg-green-500" : freshness === "stale" ? "bg-amber-500" : "bg-red-500";
  return <span className={`w-2 h-2 rounded-full shrink-0 ${color}`} />;
}
