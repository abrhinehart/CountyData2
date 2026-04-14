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
import type {
  CommissionSummary,
  ETLState,
  InventoryCounty,
  InventorySubdivisionOut,
  PermitDashboard,
  ScrapeJob,
  SnapshotOut,
  Stats,
} from "../types";

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

const MODULE_TONES = {
  transactions: { border: "rgba(29, 78, 216, 0.34)", dot: "#2563eb", text: "#1d4ed8" },
  inventory: { border: "rgba(15, 118, 110, 0.28)", dot: "#0f766e", text: "#0f766e" },
  permits: { border: "rgba(217, 119, 6, 0.3)", dot: "#d97706", text: "#a16207" },
  commission: { border: "rgba(225, 29, 72, 0.24)", dot: "#e11d48", text: "#be123c" },
  subdivisions: { border: "rgba(124, 58, 237, 0.22)", dot: "#7c3aed", text: "#6d28d9" },
  pipeline: { border: "rgba(15, 23, 42, 0.2)", dot: "#334155", text: "#334155" },
} as const;

export default function DashboardPage() {
  const navigate = useNavigate();

  const statsQ = useQuery<Stats>({ queryKey: ["stats"], queryFn: getStats });
  const permitsQ = useQuery<PermitDashboard>({
    queryKey: ["permit-dashboard"],
    queryFn: () => getPermitDashboard(),
  });
  const commissionQ = useQuery<CommissionSummary>({
    queryKey: ["commission-summary"],
    queryFn: getCommissionSummary,
  });
  const inventoryQ = useQuery<InventoryCounty[]>({
    queryKey: ["inventory-counties"],
    queryFn: getInventoryCounties,
  });
  const etlQ = useQuery<ETLState>({ queryKey: ["etl-status"], queryFn: getETLStatus });
  const reviewQ = useQuery({
    queryKey: ["review-queue", "", "", 1, 1],
    queryFn: () => getReviewQueue({ page: 1, page_size: 1 }),
  });
  const subdivisionsQ = useQuery<InventorySubdivisionOut[]>({
    queryKey: ["inventory-subdivisions-count"],
    queryFn: () => searchInventorySubdivisions({}),
  });
  const scrapeJobsQ = useQuery<{ jobs: ScrapeJob[]; active_count: number }>({
    queryKey: ["scrape-jobs-recent"],
    queryFn: () => getPermitScrapeJobs({ limit: 10 }),
  });
  const snapshotsQ = useQuery<SnapshotOut[]>({
    queryKey: ["inventory-snapshots-recent"],
    queryFn: () => getInventorySnapshots({ limit: 10 }),
  });

  const stats = statsQ.data;
  const permits = permitsQ.data;
  const commission = commissionQ.data;
  const counties = inventoryQ.data ?? [];
  const etl = etlQ.data;
  const subdivisions = subdivisionsQ.data ?? [];
  const scrapeJobs = scrapeJobsQ.data?.jobs ?? [];
  const snapshots = snapshotsQ.data ?? [];

  const inventoryLots = counties.reduce((sum, county) => sum + (county.last_snapshot_parcels ?? 0), 0);
  const latestSnapshot = counties
    .filter((county) => county.last_snapshot_at)
    .sort((a, b) => new Date(b.last_snapshot_at ?? 0).getTime() - new Date(a.last_snapshot_at ?? 0).getTime())[0];

  const actionItems: { label: string; route: string; tone: "warning" | "danger" | "accent" }[] = [];
  if ((stats?.flagged_for_review ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(stats!.flagged_for_review)} transactions flagged for review`,
      route: "/transactions?unmatched_only=true",
      tone: "warning",
    });
  }
  if ((commission?.needs_review ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(commission!.needs_review)} commission actions need review`,
      route: "/commission",
      tone: "warning",
    });
  }
  if ((reviewQ.data?.total ?? 0) > 0) {
    actionItems.push({
      label: `${fmt(reviewQ.data!.total)} rows still in the review queue`,
      route: "/review",
      tone: "accent",
    });
  }
  if (permits && permits.last_runs.some((run) => run.freshness === "stale" || run.freshness === "dead")) {
    actionItems.push({
      label: `${permits.last_runs.filter((run) => run.freshness !== "fresh").length} permit scrapers are stale or dead`,
      route: "/permits",
      tone: "danger",
    });
  }
  if (etl?.status === "failed") {
    actionItems.push({
      label: "The last ETL run failed and needs attention",
      route: "/pipeline",
      tone: "danger",
    });
  }

  const anyLoading =
    statsQ.isLoading ||
    permitsQ.isLoading ||
    commissionQ.isLoading ||
    inventoryQ.isLoading ||
    etlQ.isLoading;

  if (anyLoading) {
    return (
      <div className="page-stack report-page">
        <div className="hero-band">
          <div className="page-kicker" style={{ color: "rgba(191,219,254,0.82)" }}>
            Command Summary
          </div>
          <h1 className="page-title" style={{ color: "#f8fafc", marginTop: 8 }}>
            Loading platform snapshot
          </h1>
          <p className="page-subtitle" style={{ color: "rgba(226,232,240,0.8)" }}>
            Pulling the latest counts, run status, and queue pressure across the unified workspace.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-stack report-page">
      <header className="page-header">
        <div className="page-heading">
          <span className="page-kicker">Command Summary</span>
          <h1 className="page-title">CountyData2 operational overview</h1>
          <p className="page-subtitle">
            One place to scan the live state of sales ETL, builder inventory, permit scraping,
            subdivision tracking, entitlement activity, and platform health before you dive into a workflow.
          </p>
        </div>
      </header>

      <section className="hero-band">
        <div className="section-head" style={{ marginBottom: 18 }}>
          <div>
            <div className="section-title" style={{ color: "rgba(191,219,254,0.88)" }}>
              Today&apos;s pulse
            </div>
            <div className="hero-meta">
              Latest ETL {etl?.completed_at ? relTime(etl.completed_at) : "not run yet"} · latest BI snapshot{" "}
              {latestSnapshot?.last_snapshot_at ? relTime(latestSnapshot.last_snapshot_at) : "never"}
            </div>
          </div>
          <span className={`badge ${etl?.status === "failed" ? "badge-danger" : etl?.status === "running" ? "badge-accent" : "badge-success"}`}>
            ETL {etl?.status ?? "idle"}
          </span>
        </div>

        <div className="hero-grid">
          <div className="hero-stat">
            <div className="hero-label">Transactions</div>
            <div className="hero-value">{stats ? fmt(stats.total_transactions) : "—"}</div>
            <div className="hero-meta">{stats ? `${fmt(stats.flagged_for_review)} flagged` : "No stats"}</div>
          </div>
          <div className="hero-stat">
            <div className="hero-label">Builder Lots</div>
            <div className="hero-value">{fmt(inventoryLots)}</div>
            <div className="hero-meta">{counties.filter((county) => county.has_endpoint).length} counties reporting</div>
          </div>
          <div className="hero-stat">
            <div className="hero-label">Permits</div>
            <div className="hero-value">{permits ? fmt(permits.summary.total_permits) : "—"}</div>
            <div className="hero-meta">{permits ? `${fmt(permits.summary.current_month)} this month` : "No permit data"}</div>
          </div>
          <div className="hero-stat">
            <div className="hero-label">Entitlement Actions</div>
            <div className="hero-value">{commission ? fmt(commission.actions_extracted) : "—"}</div>
            <div className="hero-meta">{commission ? `${fmt(commission.projects_tracked)} tracked projects` : "No commission data"}</div>
          </div>
        </div>
      </section>

      {actionItems.length > 0 && (
        <section className="surface-card panel-pad">
          <div className="section-head">
            <div>
              <div className="section-title">Action Needed</div>
              <div className="section-caption">Priority queues that need a human pass before the next run.</div>
            </div>
          </div>
          <div className="page-stack" style={{ gap: 10 }}>
            {actionItems.map((item) => (
              <button
                key={item.label}
                onClick={() => navigate(item.route)}
                className="surface-muted"
                style={{
                  padding: "14px 16px",
                  borderColor:
                    item.tone === "danger"
                      ? "rgba(185, 28, 28, 0.2)"
                      : item.tone === "warning"
                        ? "rgba(161, 98, 7, 0.24)"
                        : "rgba(29, 78, 216, 0.18)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 14,
                  textAlign: "left",
                }}
              >
                <span
                  style={{
                    fontSize: 14,
                    fontWeight: 600,
                    color:
                      item.tone === "danger"
                        ? "var(--danger)"
                        : item.tone === "warning"
                          ? "var(--warning)"
                          : "var(--accent)",
                  }}
                >
                  {item.label}
                </span>
                <span className={`badge ${item.tone === "danger" ? "badge-danger" : item.tone === "warning" ? "badge-warning" : "badge-accent"}`}>
                  Open
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="metric-grid">
        <ModuleCard
          title="Transactions"
          tone="transactions"
          status={etl?.status === "running" ? "Running" : etl?.completed_at ? relTime(etl.completed_at) : "Idle"}
          stats={[
            { label: "Total", value: stats ? fmt(stats.total_transactions) : "—" },
            { label: "Counties", value: stats ? String(stats.by_county.length) : "—" },
            { label: "Flagged", value: stats ? fmt(stats.flagged_for_review) : "—", emphasis: (stats?.flagged_for_review ?? 0) > 0 ? "warn" : undefined },
          ]}
          footer={stats?.date_range ? `${stats.date_range.min ?? "—"} → ${stats.date_range.max ?? "—"}` : undefined}
          onClick={() => navigate("/transactions")}
        />
        <ModuleCard
          title="Inventory"
          tone="inventory"
          status={latestSnapshot?.last_snapshot_at ? relTime(latestSnapshot.last_snapshot_at) : "Never"}
          stats={[
            { label: "Builder Lots", value: fmt(inventoryLots) },
            { label: "Tracked", value: String(counties.length) },
            { label: "Endpoints", value: String(counties.filter((county) => county.has_endpoint).length) },
          ]}
          footer={`${snapshots.length} recent snapshots`}
          onClick={() => navigate("/inventory")}
        />
        <ModuleCard
          title="Permits"
          tone="permits"
          status={permits?.last_runs[0]?.last_success ? relTime(permits.last_runs[0].last_success) : "No successful run"}
          stats={[
            { label: "Total", value: permits ? fmt(permits.summary.total_permits) : "—" },
            { label: "This Month", value: permits ? fmt(permits.summary.current_month) : "—" },
            { label: "Watchlist", value: permits ? fmt(permits.summary.watchlist_count) : "—" },
          ]}
          footer={`${scrapeJobs.length} recent scrape jobs`}
          onClick={() => navigate("/permits")}
        />
        <ModuleCard
          title="Commission"
          tone="commission"
          status={commission ? `${fmt(commission.jurisdictions_active)} jurisdictions` : "No summary"}
          stats={[
            { label: "Actions", value: commission ? fmt(commission.actions_extracted) : "—" },
            { label: "Projects", value: commission ? fmt(commission.projects_tracked) : "—" },
            { label: "Needs Review", value: commission ? fmt(commission.needs_review) : "—", emphasis: (commission?.needs_review ?? 0) > 0 ? "warn" : undefined },
          ]}
          footer="Agenda extraction and lifecycle tracking"
          onClick={() => navigate("/commission")}
        />
        <ModuleCard
          title="Subdivisions"
          tone="subdivisions"
          status={subdivisions.length > 0 ? `${fmt(subdivisions.length)} loaded` : "Idle"}
          stats={[
            { label: "Visible", value: fmt(subdivisions.length) },
            { label: "Counties", value: stats ? String(stats.by_county.length) : "—" },
            { label: "Geometry Candidates", value: String(subdivisions.filter((row) => row.has_geometry).length) },
          ]}
          footer="Builder-active subdivision index"
          onClick={() => navigate("/subdivisions")}
        />
        <ModuleCard
          title="Pipeline"
          tone="pipeline"
          status={etl?.completed_at ? relTime(etl.completed_at) : "Not run"}
          stats={[
            { label: "ETL", value: etl?.status ? etl.status.toUpperCase() : "IDLE", emphasis: etl?.status === "failed" ? "danger" : undefined },
            { label: "Scrapes", value: String(scrapeJobs.length) },
            { label: "Snapshots", value: String(snapshots.length) },
          ]}
          footer="Runs, exports, and queue pressure"
          onClick={() => navigate("/pipeline")}
        />
      </section>
    </div>
  );
}

function ModuleCard({
  title,
  tone,
  stats,
  status,
  footer,
  onClick,
}: {
  title: string;
  tone: keyof typeof MODULE_TONES;
  stats: { label: string; value: string; emphasis?: "warn" | "danger" }[];
  status: string;
  footer?: string;
  onClick: () => void;
}) {
  const palette = MODULE_TONES[tone];
  return (
    <button
      onClick={onClick}
      className="surface-card panel-pad"
      style={{
        textAlign: "left",
        borderColor: palette.border,
        transition: "transform 180ms var(--ease-standard), box-shadow 180ms var(--ease-standard), border-color 180ms var(--ease-standard)",
      }}
    >
      <div className="section-head">
        <div>
          <div className="section-title" style={{ color: palette.text }}>
            {title}
          </div>
          <div className="section-caption">{status}</div>
        </div>
        <span
          style={{
            width: 12,
            height: 12,
            borderRadius: 999,
            background: palette.dot,
            boxShadow: `0 0 0 6px ${palette.border}`,
          }}
        />
      </div>

      <div className="hero-grid" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 12 }}>
        {stats.map((stat) => (
          <div key={stat.label} className="surface-muted" style={{ padding: "12px 12px 10px", borderRadius: 14 }}>
            <div className="metric-label">{stat.label}</div>
            <div
              className={`metric-value ${stat.emphasis === "warn" ? "warn" : stat.emphasis === "danger" ? "danger" : ""}`}
              style={{ fontSize: "1.55rem", marginTop: 8 }}
            >
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {footer && <div className="metric-meta">{footer}</div>}
    </button>
  );
}
