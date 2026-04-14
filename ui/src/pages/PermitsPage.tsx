import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getPermitBootstrap,
  getPermitDashboard,
  getPermitList,
  getPermitScrapeJobs,
  triggerPermitScrape,
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-800">Permit Tracker</h1>
        <div className="flex items-center gap-3">
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
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Top Subdivisions
            </h2>
            {dash.top_subdivisions.length === 0 ? (
              <p className="text-sm text-gray-400">No data.</p>
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

          <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Top Builders
            </h2>
            {dash.top_builders.length === 0 ? (
              <p className="text-sm text-gray-400">No data.</p>
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
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-x-auto">
        <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">
            All Permits
          </h2>
          {jurisdictionId && (
            <button
              onClick={() => handleJurisdictionChange(undefined)}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Clear filter
            </button>
          )}
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-2 text-left font-medium text-gray-600">Issued</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Permit #</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Status</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Address</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Subdivision</th>
              <th className="px-3 py-2 text-left font-medium text-gray-600">Builder</th>
              <th className="px-3 py-2 text-right font-medium text-gray-600">Valuation</th>
            </tr>
          </thead>
          <tbody>
            {listQ.isLoading ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-gray-400">Loading...</td>
              </tr>
            ) : !permits || permits.permits.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-3 py-8 text-center text-gray-400">No permits found</td>
              </tr>
            ) : (
              permits.permits.map((p) => (
                <tr key={p.id} className="border-b border-gray-100 hover:bg-blue-50">
                  <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{p.issue_date ?? ""}</td>
                  <td className="px-3 py-1.5 text-gray-700">{p.permit_number}</td>
                  <td className="px-3 py-1.5">
                    <StatusBadge status={p.status} />
                  </td>
                  <td className="px-3 py-1.5 text-gray-700">{p.jurisdiction ?? ""}</td>
                  <td className="px-3 py-1.5 text-gray-700 max-w-[220px] truncate" title={p.address ?? ""}>
                    {p.address ?? ""}
                  </td>
                  <td className="px-3 py-1.5 text-gray-700">{p.subdivision ?? ""}</td>
                  <td className="px-3 py-1.5 text-gray-700">{p.builder ?? ""}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-gray-700">
                    {p.valuation != null ? `$${fmt(p.valuation)}` : ""}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Recent Scrape Jobs
        </h2>
        {jobsQ.isLoading ? (
          <p className="text-sm text-gray-400">Loading...</p>
        ) : jobs.length === 0 ? (
          <p className="text-sm text-gray-400">No scrape jobs.</p>
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
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Scraper Health
          </h2>
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
      className="text-sm border border-gray-300 rounded-md px-3 py-1.5 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        vs Last Month
      </p>
      <p className={`text-2xl font-semibold tabular-nums ${positive ? "text-green-600" : "text-red-600"}`}>
        {positive ? "+" : ""}{month_delta}
      </p>
      <p className={`text-xs tabular-nums mt-0.5 ${pctChange >= 0 ? "text-green-600" : "text-red-600"}`}>
        {pctChange >= 0 ? "+" : ""}{pctChange}% daily rate
      </p>
      <p className="text-xs text-gray-400 tabular-nums mt-0.5">
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
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4" title={tooltip}>
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </p>
      <p
        className={`text-2xl font-semibold tabular-nums ${
          accent ? "text-red-600" : "text-gray-800"
        }`}
      >
        {value}
      </p>
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
