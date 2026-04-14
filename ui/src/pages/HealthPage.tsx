import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getGeometryCoverage,
  getBiSnapshotHealth,
  getPtScrapeHealth,
  getCrDocumentHealth,
} from "../api";
import type {
  GeometryCoverageRow,
  BiSnapshotHealthRow,
  PtScrapeHealthRow,
  CrDocumentHealthRow,
} from "../types";

type SortKey = "county" | "total" | "with_geom" | "without_geom" | "pct";
type SortDir = "asc" | "desc";

export default function HealthPage() {
  const [sortBy, setSortBy] = useState<SortKey>("county");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const { data, isLoading, error } = useQuery({
    queryKey: ["geometry-coverage"],
    queryFn: getGeometryCoverage,
  });

  const biHealth = useQuery({
    queryKey: ["bi-snapshot-health"],
    queryFn: getBiSnapshotHealth,
  });

  const ptHealth = useQuery({
    queryKey: ["pt-scrape-health"],
    queryFn: getPtScrapeHealth,
  });

  const crHealth = useQuery({
    queryKey: ["cr-document-health"],
    queryFn: getCrDocumentHealth,
  });

  function toggleSort(key: SortKey) {
    if (sortBy === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDir(key === "county" ? "asc" : "desc");
    }
  }

  const rows = useMemo(() => {
    if (!data?.rows) return [];
    const dir = sortDir === "asc" ? 1 : -1;
    return [...data.rows].sort((a, b) => {
      let cmp: number;
      switch (sortBy) {
        case "county":
          cmp = a.county.localeCompare(b.county);
          break;
        case "total":
          cmp = a.total - b.total;
          break;
        case "with_geom":
          cmp = a.with_geom - b.with_geom;
          break;
        case "without_geom":
          cmp = a.without_geom - b.without_geom;
          break;
        case "pct":
          cmp =
            (a.total ? a.with_geom / a.total : 0) -
            (b.total ? b.with_geom / b.total : 0);
          break;
      }
      return cmp * dir;
    });
  }, [data, sortBy, sortDir]);

  const totals = useMemo(() => {
    if (!rows.length) return { total: 0, with_geom: 0, without_geom: 0 };
    return rows.reduce(
      (acc, r) => ({
        total: acc.total + r.total,
        with_geom: acc.with_geom + r.with_geom,
        without_geom: acc.without_geom + r.without_geom,
      }),
      { total: 0, with_geom: 0, without_geom: 0 },
    );
  }, [rows]);

  const arrow = (key: SortKey) =>
    sortBy === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : "";

  const pct = (n: number, d: number) =>
    d ? `${((n / d) * 100).toFixed(1)}%` : "\u2014";

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-semibold text-gray-800">Platform Health</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-700">
          Subdivision Geometry Coverage
        </h2>

        {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {error && (
          <p className="text-sm text-red-600">
            Failed to load geometry coverage.
          </p>
        )}

        {rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {([
                    ["county", "County"],
                    ["total", "Total"],
                    ["with_geom", "With Geom"],
                    ["without_geom", "Without Geom"],
                    ["pct", "Coverage"],
                  ] as [SortKey, string][]).map(([key, label]) => (
                    <th
                      key={key}
                      onClick={() => toggleSort(key)}
                      className="px-4 py-2 text-left font-medium text-gray-600 cursor-pointer select-none hover:text-gray-900"
                    >
                      {label}
                      {arrow(key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((r) => (
                  <tr key={r.county} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-800">
                      {r.county}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{r.total}</td>
                    <td className="px-4 py-2 text-gray-700">{r.with_geom}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.without_geom}
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {pct(r.with_geom, r.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 border-t border-gray-200 font-medium">
                <tr>
                  <td className="px-4 py-2 text-gray-800">Total</td>
                  <td className="px-4 py-2 text-gray-700">{totals.total}</td>
                  <td className="px-4 py-2 text-gray-700">
                    {totals.with_geom}
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {totals.without_geom}
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {pct(totals.with_geom, totals.total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </section>

      {/* ── BI Snapshot Health ─────────────────────────────────────── */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-700">
          Builder Inventory — Latest Snapshots
        </h2>

        {biHealth.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {biHealth.error && (
          <p className="text-sm text-red-600">Failed to load BI snapshot health.</p>
        )}

        {biHealth.data && biHealth.data.rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">County</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Started</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Parcels</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">New</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Changed</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {biHealth.data.rows.map((r: BiSnapshotHealthRow) => (
                  <tr key={r.county} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-800">{r.county}</td>
                    <td className="px-4 py-2">
                      <span
                        className={
                          r.status === "completed"
                            ? "text-green-600"
                            : r.status === "failed"
                            ? "text-red-600"
                            : r.status === "running"
                            ? "text-blue-600"
                            : "text-gray-600"
                        }
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.started_at ? new Date(r.started_at).toLocaleString() : "\u2014"}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{r.total_parcels_queried}</td>
                    <td className="px-4 py-2 text-gray-700">{r.new_count}</td>
                    <td className="px-4 py-2 text-gray-700">{r.changed_count}</td>
                    <td className="px-4 py-2 text-gray-700 max-w-xs truncate">
                      {r.error_message || "\u2014"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── PT Scrape Health ───────────────────────────────────────── */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-700">
          Permit Tracker — Recent Scrape Jobs
        </h2>

        {ptHealth.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {ptHealth.error && (
          <p className="text-sm text-red-600">Failed to load PT scrape health.</p>
        )}

        {ptHealth.data && ptHealth.data.rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">ID</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Status</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Trigger</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Queued</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Finished</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Attempts</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {ptHealth.data.rows.map((r: PtScrapeHealthRow) => (
                  <tr key={r.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 text-gray-700">{r.id}</td>
                    <td className="px-4 py-2 font-medium text-gray-800">
                      {r.jurisdiction_name || "All"}
                    </td>
                    <td className="px-4 py-2">
                      <span
                        className={
                          r.status === "completed"
                            ? "text-green-600"
                            : r.status === "failed"
                            ? "text-red-600"
                            : r.status === "running"
                            ? "text-blue-600"
                            : "text-gray-600"
                        }
                      >
                        {r.status}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-gray-700">{r.trigger_type}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {new Date(r.queued_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.finished_at ? new Date(r.finished_at).toLocaleString() : "\u2014"}
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.attempt_count}/{r.max_attempts}
                    </td>
                    <td className="px-4 py-2 text-gray-700 max-w-xs truncate">
                      {r.last_error || "\u2014"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* ── CR Document Health ─────────────────────────────────────── */}
      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-700">
          Commission Radar — Document Extraction
        </h2>

        {crHealth.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {crHealth.error && (
          <p className="text-sm text-red-600">Failed to load CR document health.</p>
        )}

        {crHealth.data && crHealth.data.rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Total Docs</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Extracted OK</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Failed</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Not Attempted</th>
                  <th className="px-4 py-2 text-left font-medium text-gray-600">Latest Meeting</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {crHealth.data.rows.map((r: CrDocumentHealthRow) => (
                  <tr key={r.jurisdiction} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-800">{r.jurisdiction}</td>
                    <td className="px-4 py-2 text-gray-700">{r.total_documents}</td>
                    <td className="px-4 py-2 text-green-600">{r.extracted_ok}</td>
                    <td className="px-4 py-2 text-red-600">{r.extracted_fail}</td>
                    <td className="px-4 py-2 text-gray-700">{r.not_attempted}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.latest_meeting || "\u2014"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
