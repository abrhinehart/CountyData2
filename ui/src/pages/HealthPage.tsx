import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getGeometryCoverage,
  getBiSnapshotHealth,
  getPtScrapeHealth,
  getCrDocumentHealth,
} from "../api";
import type {
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
    <div className="page-stack report-page max-w-6xl">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Platform Health</p>
          <h1 className="page-title">System Coverage</h1>
          <p className="page-subtitle">
            Audit geometry coverage, inventory snapshots, permit scrapes, and commission extraction quality.
          </p>
        </div>
      </div>

      <section className="surface-card panel-pad">
        <div className="section-head mb-3">
          <h2 className="section-title">Subdivision Geometry Coverage</h2>
        </div>

        {isLoading && <p className="data-note">Loading...</p>}
        {error && (
          <p className="data-note text-[var(--danger)]">
            Failed to load geometry coverage.
          </p>
        )}

        {rows.length > 0 && (
          <div className="data-shell">
            <table className="data-table">
              <thead>
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
                      className="cursor-pointer select-none text-left hover:text-[var(--text)]"
                    >
                      {label}
                      {arrow(key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.county}>
                    <td className="font-medium">
                      {r.county}
                    </td>
                    <td>{r.total}</td>
                    <td>{r.with_geom}</td>
                    <td>
                      {r.without_geom}
                    </td>
                    <td>
                      {pct(r.with_geom, r.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-[var(--surface-muted)] font-medium">
                <tr>
                  <td>Total</td>
                  <td>{totals.total}</td>
                  <td>
                    {totals.with_geom}
                  </td>
                  <td>
                    {totals.without_geom}
                  </td>
                  <td>
                    {pct(totals.with_geom, totals.total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </section>

      {/* ── BI Snapshot Health ─────────────────────────────────────── */}
      <section className="surface-card panel-pad">
        <div className="section-head mb-3">
          <h2 className="section-title">Builder Inventory — Latest Snapshots</h2>
        </div>

        {biHealth.isLoading && <p className="data-note">Loading...</p>}
        {biHealth.error && (
          <p className="data-note text-[var(--danger)]">Failed to load BI snapshot health.</p>
        )}

        {biHealth.data && biHealth.data.rows.length > 0 && (
          <div className="data-shell overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="text-left">County</th>
                  <th className="text-left">Status</th>
                  <th className="text-left">Started</th>
                  <th className="text-left">Parcels</th>
                  <th className="text-left">New</th>
                  <th className="text-left">Changed</th>
                  <th className="text-left">Error</th>
                </tr>
              </thead>
              <tbody>
                {biHealth.data.rows.map((r: BiSnapshotHealthRow) => (
                  <tr key={r.county}>
                    <td className="font-medium">{r.county}</td>
                    <td>
                      <span className={`badge ${statusBadge(r.status)}`}>
                        {r.status}
                      </span>
                    </td>
                    <td>
                      {r.started_at ? new Date(r.started_at).toLocaleString() : "\u2014"}
                    </td>
                    <td>{r.total_parcels_queried}</td>
                    <td>{r.new_count}</td>
                    <td>{r.changed_count}</td>
                    <td className="max-w-xs truncate">
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
      <section className="surface-card panel-pad">
        <div className="section-head mb-3">
          <h2 className="section-title">Permit Tracker — Recent Scrape Jobs</h2>
        </div>

        {ptHealth.isLoading && <p className="data-note">Loading...</p>}
        {ptHealth.error && (
          <p className="data-note text-[var(--danger)]">Failed to load PT scrape health.</p>
        )}

        {ptHealth.data && ptHealth.data.rows.length > 0 && (
          <div className="data-shell overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="text-left">ID</th>
                  <th className="text-left">Jurisdiction</th>
                  <th className="text-left">Status</th>
                  <th className="text-left">Trigger</th>
                  <th className="text-left">Queued</th>
                  <th className="text-left">Finished</th>
                  <th className="text-left">Attempts</th>
                  <th className="text-left">Error</th>
                </tr>
              </thead>
              <tbody>
                {ptHealth.data.rows.map((r: PtScrapeHealthRow) => (
                  <tr key={r.id}>
                    <td>{r.id}</td>
                    <td className="font-medium">
                      {r.jurisdiction_name || "All"}
                    </td>
                    <td>
                      <span className={`badge ${statusBadge(r.status)}`}>
                        {r.status}
                      </span>
                    </td>
                    <td>{r.trigger_type}</td>
                    <td>
                      {new Date(r.queued_at).toLocaleString()}
                    </td>
                    <td>
                      {r.finished_at ? new Date(r.finished_at).toLocaleString() : "\u2014"}
                    </td>
                    <td>
                      {r.attempt_count}/{r.max_attempts}
                    </td>
                    <td className="max-w-xs truncate">
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
      <section className="surface-card panel-pad">
        <div className="section-head mb-3">
          <h2 className="section-title">Commission Radar — Document Extraction</h2>
        </div>

        {crHealth.isLoading && <p className="data-note">Loading...</p>}
        {crHealth.error && (
          <p className="data-note text-[var(--danger)]">Failed to load CR document health.</p>
        )}

        {crHealth.data && crHealth.data.rows.length > 0 && (
          <div className="data-shell overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="text-left">Jurisdiction</th>
                  <th className="text-left">Total Docs</th>
                  <th className="text-left">Extracted OK</th>
                  <th className="text-left">Failed</th>
                  <th className="text-left">Not Attempted</th>
                  <th className="text-left">Latest Meeting</th>
                </tr>
              </thead>
              <tbody>
                {crHealth.data.rows.map((r: CrDocumentHealthRow) => (
                  <tr key={r.jurisdiction}>
                    <td className="font-medium">{r.jurisdiction}</td>
                    <td>{r.total_documents}</td>
                    <td className="text-[var(--success)]">{r.extracted_ok}</td>
                    <td className="text-[var(--danger)]">{r.extracted_fail}</td>
                    <td>{r.not_attempted}</td>
                    <td>
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

function statusBadge(status: string) {
  if (status === "completed") return "badge-success";
  if (status === "failed") return "badge-danger";
  if (status === "running") return "badge-accent";
  return "badge-neutral";
}
