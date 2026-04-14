import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getPermitBootstrap,
  getPermitDashboard,
  getPermitList,
  getPermitScrapeJobs,
} from "../api";
import Pagination from "../components/Pagination";
import type { PermitDashboard } from "../types";

function fmt(n: number): string {
  return n.toLocaleString();
}

export default function PermitsPage() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [jurisdictionId, setJurisdictionId] = useState<number | undefined>();

  const bootQ = useQuery({
    queryKey: ["permit-bootstrap"],
    queryFn: getPermitBootstrap,
    staleTime: 5 * 60_000,
  });

  const dashQ = useQuery({
    queryKey: ["permit-dashboard", jurisdictionId],
    queryFn: () => getPermitDashboard({ jurisdiction_id: jurisdictionId }),
  });

  const listQ = useQuery({
    queryKey: ["permit-list", page, pageSize, jurisdictionId],
    queryFn: () =>
      getPermitList({
        page: String(page),
        page_size: String(pageSize),
        jurisdiction_id: jurisdictionId,
      }),
  });

  const jobsQ = useQuery({
    queryKey: ["permit-scrape-jobs"],
    queryFn: () => getPermitScrapeJobs({ limit: 10 }),
  });

  const dash = dashQ.data;
  const permits = listQ.data;
  const jobs = jobsQ.data?.jobs ?? [];
  const jurisdictions = bootQ.data?.jurisdictions ?? [];

  const handleJurisdictionChange = (id: number | undefined) => {
    setJurisdictionId(id);
    setPage(1);
  };

  return (
    <div className="page-stack report-page">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Permit Tracker</p>
          <h1 className="page-title">Permits</h1>
          <p className="page-subtitle">
            Monitor permit volume, top subdivisions, and scraper freshness by jurisdiction.
          </p>
        </div>
        <div className="page-actions">
          <JurisdictionFilter
            jurisdictions={jurisdictions}
            value={jurisdictionId}
            onChange={handleJurisdictionChange}
          />
        </div>
      </div>

      {/* KPI cards */}
      {dash && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <Card label="Total Permits" value={fmt(dash.summary.total_permits)} />
          <Card label="This Month" value={fmt(dash.summary.current_month)} />
          <VsLastMonthCard summary={dash.summary} />
          <Card label="Last Month" value={fmt(dash.summary.last_month)} />
          <Card label="Watchlist" value={fmt(dash.summary.watchlist_count)} tooltip="Permits from builders on your watchlist" />
        </div>
      )}

      {/* Top subdivisions + Top builders side by side */}
      {dash && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="surface-card panel-pad">
            <div className="section-head mb-4">
              <h2 className="section-title">Top Subdivisions</h2>
            </div>
            {dash.top_subdivisions.length === 0 ? (
              <p className="data-note">No data.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-100">
                    <th className="pb-2 font-medium">Subdivision</th>
                    <th className="pb-2 font-medium text-right">Permits</th>
                  </tr>
                </thead>
                <tbody>
                  {dash.top_subdivisions.map((s) => (
                    <tr key={s.name} className="border-b border-gray-50 last:border-0">
                      <td className="py-1.5 text-gray-700">{s.name}</td>
                      <td className="py-1.5 text-right text-gray-500 tabular-nums">
                        {fmt(s.total)}
                        {s.current_month > 0 && (
                          <span className="ml-2 text-amber-600 text-xs">
                            {s.current_month} this mo
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="surface-card panel-pad">
            <div className="section-head mb-4">
              <h2 className="section-title">Top Builders</h2>
            </div>
            {dash.top_builders.length === 0 ? (
              <p className="data-note">No data.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-400 border-b border-gray-100">
                    <th className="pb-2 font-medium">Builder</th>
                    <th className="pb-2 font-medium text-right">Permits</th>
                  </tr>
                </thead>
                <tbody>
                  {dash.top_builders.map((b) => (
                    <tr key={b.name} className="border-b border-gray-50 last:border-0">
                      <td className="py-1.5 text-gray-700">{b.name}</td>
                      <td className="py-1.5 text-right text-gray-500 tabular-nums">
                        {fmt(b.total)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      )}

      {/* Permit listing table */}
      <div className="surface-card data-shell">
        <div className="data-toolbar">
          <div>
            <p className="section-title">All Permits</p>
            <p className="data-note">Issued permits, builder attribution, and valuation by jurisdiction.</p>
          </div>
          {jurisdictionId && (
            <button
              onClick={() => handleJurisdictionChange(undefined)}
              className="button-ghost"
            >
              Clear filter
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th className="text-left">Issued</th>
                <th className="text-left">Permit #</th>
                <th className="text-left">Status</th>
                <th className="text-left">Jurisdiction</th>
                <th className="text-left">Address</th>
                <th className="text-left">Subdivision</th>
                <th className="text-left">Builder</th>
                <th className="text-right">Valuation</th>
              </tr>
            </thead>
            <tbody>
              {listQ.isLoading ? (
                <tr>
                  <td colSpan={8} className="table-empty text-center">Loading...</td>
                </tr>
              ) : !permits || permits.permits.length === 0 ? (
                <tr>
                  <td colSpan={8} className="table-empty text-center">No permits found</td>
                </tr>
              ) : (
                permits.permits.map((p) => (
                  <tr key={p.id}>
                    <td className="whitespace-nowrap">{p.issue_date ?? ""}</td>
                    <td>{p.permit_number}</td>
                    <td><StatusBadge status={p.status} /></td>
                    <td>{p.jurisdiction ?? ""}</td>
                    <td className="max-w-[220px] truncate" title={p.address ?? ""}>{p.address ?? ""}</td>
                    <td>{p.subdivision ?? ""}</td>
                    <td>{p.builder ?? ""}</td>
                    <td className="text-right tabular-nums">
                      {p.valuation != null ? `$${fmt(p.valuation)}` : ""}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {permits && (
          <div className="px-3">
            <Pagination
              page={permits.page}
              pageSize={permits.page_size}
              total={permits.total_count}
              onPageChange={setPage}
              onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
            />
          </div>
        )}
      </div>

      {/* Scrape jobs */}
      <div className="surface-card panel-pad">
        <div className="section-head mb-4">
          <h2 className="section-title">Recent Scrape Jobs</h2>
        </div>
        {jobsQ.isLoading ? (
          <p className="data-note">Loading...</p>
        ) : jobs.length === 0 ? (
          <p className="data-note">No scrape jobs.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-3 py-2 text-left font-medium text-gray-600">ID</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Status</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Queued</th>
                <th className="px-3 py-2 text-right font-medium text-gray-600">Permits</th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((j) => (
                <tr key={j.id} className="border-b border-gray-100">
                  <td className="px-3 py-1.5 text-gray-700">{j.id}</td>
                  <td className="px-3 py-1.5 text-gray-700">{j.jurisdiction}</td>
                  <td className="px-3 py-1.5">
                    <JobBadge status={j.status} />
                  </td>
                  <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">
                    {new Date(j.queued_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-gray-700">
                    {j.summary?.permits_found ?? "\u2014"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Scraper health */}
      {dash && dash.last_runs.length > 0 && (
        <div className="surface-card panel-pad">
          <div className="section-head mb-4">
            <h2 className="section-title">Scraper Health</h2>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-3 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Portal</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Last Success</th>
                <th className="px-3 py-2 text-left font-medium text-gray-600">Freshness</th>
              </tr>
            </thead>
            <tbody>
              {dash.last_runs.map((r) => (
                <tr key={r.name} className="border-b border-gray-100">
                  <td className="px-3 py-1.5 text-gray-700">{r.name}</td>
                  <td className="px-3 py-1.5 text-gray-500">{r.portal_type ?? "\u2014"}</td>
                  <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">
                    {r.last_success ? new Date(r.last_success).toLocaleDateString() : "Never"}
                  </td>
                  <td className="px-3 py-1.5">
                    <FreshnessBadge freshness={r.freshness} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Jurisdiction filter dropdown                                       */
/* ------------------------------------------------------------------ */

interface JurisdictionOption {
  id: number;
  name: string;
  portal_type: string | null;
  active: boolean;
}

function JurisdictionFilter({
  jurisdictions,
  value,
  onChange,
}: {
  jurisdictions: JurisdictionOption[];
  value: number | undefined;
  onChange: (id: number | undefined) => void;
}) {
  // Group by county-level vs city-level based on naming heuristics
  // (cities in Polk County are the new ones we're adding)
  const sorted = [...jurisdictions].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
      className="form-control min-w-[220px]"
    >
      <option value="">All Jurisdictions</option>
      {sorted.map((j) => (
        <option key={j.id} value={j.id} disabled={!j.active}>
          {j.name}
          {j.portal_type ? ` (${j.portal_type})` : ""}
          {!j.active ? " \u2014 inactive" : ""}
        </option>
      ))}
    </select>
  );
}

/* ------------------------------------------------------------------ */
/*  VS Last Month KPI                                                  */
/* ------------------------------------------------------------------ */

function VsLastMonthCard({ summary }: { summary: PermitDashboard["summary"] }) {
  const { current_month, last_month, month_delta } = summary;
  const now = new Date();
  const dayOfMonth = now.getDate();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const daysInLastMonth = new Date(now.getFullYear(), now.getMonth(), 0).getDate();
  const dailyRate = dayOfMonth > 0 ? current_month / dayOfMonth : 0;
  const dailyLast = daysInLastMonth > 0 ? last_month / daysInLastMonth : 0;
  const pctChange = dailyLast > 0 ? Math.round(((dailyRate - dailyLast) / dailyLast) * 100) : 0;
  const projected = Math.round(dailyRate * daysInMonth);
  const positive = month_delta >= 0;

  return (
    <div className={`metric-card ${positive ? "" : "danger"}`.trim()}>
      <p className="metric-label">vs Last Month</p>
      <p className={`metric-value ${positive ? "" : "danger"}`.trim()}>
        {positive ? "+" : ""}{month_delta}
      </p>
      <p className={`metric-meta ${pctChange >= 0 ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
        {pctChange >= 0 ? "+" : ""}{pctChange}% daily rate
      </p>
      <p className="metric-meta">
        ~{fmt(projected)} projected
      </p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helper components                                                  */
/* ------------------------------------------------------------------ */

function Card({
  label,
  value,
  accent,
  tooltip,
}: {
  label: string;
  value: string;
  accent?: boolean;
  tooltip?: string;
}) {
  return (
    <div className={`metric-card ${accent ? "danger" : ""}`.trim()} title={tooltip}>
      <p className="metric-label">{label}</p>
      <p className={`metric-value ${accent ? "danger" : ""}`.trim()}>{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string | null }) {
  if (!status) return null;
  const s = status.toLowerCase();
  const styles =
    s.includes("issued") || s.includes("final") || s.includes("closed")
      ? "bg-green-100 text-green-700"
      : s.includes("pending") || s.includes("review")
        ? "bg-amber-100 text-amber-700"
        : "bg-gray-100 text-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles}`}>
      {status}
    </span>
  );
}

function JobBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    success: "bg-green-100 text-green-700",
    running: "bg-blue-100 text-blue-700 animate-pulse",
    failed: "bg-red-100 text-red-700",
    queued: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? styles.queued}`}>
      {status}
    </span>
  );
}

function FreshnessBadge({ freshness }: { freshness: string }) {
  const styles: Record<string, string> = {
    fresh: "bg-green-100 text-green-700",
    stale: "bg-amber-100 text-amber-700",
    dead: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[freshness] ?? "bg-gray-100 text-gray-600"}`}>
      {freshness}
    </span>
  );
}
