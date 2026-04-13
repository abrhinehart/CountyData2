import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getCounties,
  startETL,
  getETLStatus,
  exportTransactions,
  exportReviewQueue,
  downloadUrl,
  getPermitScrapeJobs,
  getInventorySnapshots,
} from "../api";

export default function PipelinePage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);

  const { data: counties } = useQuery({ queryKey: ["counties"], queryFn: getCounties });
  const { data: etlStatus, refetch: refetchStatus } = useQuery({
    queryKey: ["etl-status"],
    queryFn: async () => {
      const result = await getETLStatus();
      // Handle polling lifecycle inside the query function
      if (result.status !== "running" && polling) {
        setPolling(false);
        queryClient.invalidateQueries({ queryKey: ["stats"] });
        queryClient.invalidateQueries({ queryKey: ["transactions"] });
      }
      return result;
    },
    refetchInterval: polling ? 2000 : false,
  });

  // Last run data (#35)
  const scrapeJobsQ = useQuery({
    queryKey: ["permit-scrape-jobs"],
    queryFn: () => getPermitScrapeJobs({ limit: 5 }),
  });
  const snapshotsQ = useQuery({
    queryKey: ["inventory-snapshots"],
    queryFn: () => getInventorySnapshots({}),
  });

  const toggleCounty = (c: string) => {
    setSelected((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const handleRun = async (all: boolean) => {
    await startETL(all ? [] : selected);
    setPolling(true);
    refetchStatus();
  };

  const handleExportTransactions = async () => {
    try {
      const res = await exportTransactions({});
      window.open(downloadUrl(res.filename), "_blank");
    } catch {
      alert("Export failed");
    }
  };

  const handleExportReview = async () => {
    try {
      const res = await exportReviewQueue({});
      window.open(downloadUrl(res.filename), "_blank");
    } catch {
      alert("Export failed");
    }
  };

  const isRunning = etlStatus?.status === "running" || polling;
  const results = etlStatus?.results ?? {};
  const hasResults = Object.keys(results).length > 0;
  const scrapeJobs = scrapeJobsQ.data?.jobs ?? [];
  const snapshots = snapshotsQ.data ?? [];

  return (
    <div className="max-w-5xl space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Pipeline Controls</h1>

      {/* ETL section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Run ETL */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Sales ETL</h2>
            <StatusBadge status={etlStatus?.status ?? "idle"} />
          </div>

          {etlStatus?.started_at && (
            <p className="text-xs text-gray-400 mb-3">
              {etlStatus.status === "running" ? "Started" : "Last run"}:{" "}
              {new Date(etlStatus.started_at).toLocaleString()}
              {etlStatus.completed_at && (
                <> &mdash; finished {new Date(etlStatus.completed_at).toLocaleString()}</>
              )}
            </p>
          )}

          {etlStatus?.error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded p-2 text-xs mb-3">
              {etlStatus.error}
            </div>
          )}

          <div className="flex flex-wrap gap-1.5 mb-3">
            {counties?.map((c) => (
              <label
                key={c}
                className={`flex items-center gap-1 px-2 py-1 rounded border text-xs cursor-pointer transition-colors ${
                  selected.includes(c)
                    ? "bg-blue-50 border-blue-300 text-blue-700"
                    : "border-gray-200 text-gray-600 hover:bg-gray-50"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(c)}
                  onChange={() => toggleCounty(c)}
                  className="rounded text-xs"
                />
                {c}
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleRun(false)}
              disabled={isRunning || selected.length === 0}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Run Selected ({selected.length})
            </button>
            <button
              onClick={() => handleRun(true)}
              disabled={isRunning}
              className="px-3 py-1.5 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
            >
              Run All
            </button>
          </div>
        </div>

        {/* ETL Results */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            ETL Results
          </h2>
          {!hasResults ? (
            <p className="text-sm text-gray-400">No recent results.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-1.5 font-medium text-gray-600">County</th>
                  <th className="text-right py-1.5 font-medium text-gray-600">Files</th>
                  <th className="text-right py-1.5 font-medium text-gray-600">Inserted</th>
                  <th className="text-right py-1.5 font-medium text-gray-600">Updated</th>
                  <th className="text-right py-1.5 font-medium text-gray-600">Errors</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(results).map(([county, r]) => (
                  <tr key={county} className="border-b border-gray-100">
                    <td className="py-1.5 text-gray-700">{county}</td>
                    <td className="text-right tabular-nums py-1.5">{r.files}</td>
                    <td className="text-right tabular-nums py-1.5">{r.inserted}</td>
                    <td className="text-right tabular-nums py-1.5">{r.updated}</td>
                    <td className="text-right tabular-nums py-1.5">
                      <span className={r.errors > 0 ? "text-red-600 font-medium" : ""}>{r.errors}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Last Run Data (#35) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent permit scrape jobs */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Recent Permit Scrapes
          </h2>
          {scrapeJobs.length === 0 ? (
            <p className="text-sm text-gray-400">No recent jobs.</p>
          ) : (
            <div className="space-y-2">
              {scrapeJobs.map((j) => (
                <div key={j.id} className="flex items-center gap-2 text-sm">
                  <JobBadge status={j.status} />
                  <span className="text-gray-700 flex-1 truncate">{j.jurisdiction}</span>
                  <span className="text-gray-400 text-xs tabular-nums">
                    {j.summary?.permits_found ?? "—"} permits
                  </span>
                  <span className="text-gray-400 text-xs">
                    {new Date(j.queued_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent inventory snapshots */}
        <div className="bg-white rounded-lg border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Recent Inventory Snapshots
          </h2>
          {snapshots.length === 0 ? (
            <p className="text-sm text-gray-400">No recent snapshots.</p>
          ) : (
            <div className="space-y-2">
              {snapshots.map((s) => (
                <div key={s.id} className="flex items-center gap-2 text-sm">
                  <SnapshotBadge status={s.status} />
                  <span className="text-gray-700 flex-1 tabular-nums">
                    {s.total_parcels_queried.toLocaleString()} parcels
                  </span>
                  <span className="text-xs text-emerald-600">+{s.new_count}</span>
                  <span className="text-xs text-red-600">-{s.removed_count}</span>
                  <span className="text-gray-400 text-xs">
                    {new Date(s.started_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Export Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Export</h2>
        <div className="flex gap-2">
          <button
            onClick={handleExportTransactions}
            className="px-4 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Export All Transactions
          </button>
          <button
            onClick={handleExportReview}
            className="px-4 py-1.5 text-sm bg-amber-600 text-white rounded hover:bg-amber-700"
          >
            Export Review Queue
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    idle: "bg-gray-100 text-gray-600",
    running: "bg-blue-100 text-blue-700 animate-pulse",
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? styles.idle}`}>
      {status.toUpperCase()}
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
    <span className={`px-2 py-0.5 rounded text-xs font-medium shrink-0 ${styles[status] ?? styles.queued}`}>
      {status}
    </span>
  );
}

function SnapshotBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    running: "bg-blue-100 text-blue-700 animate-pulse",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium shrink-0 ${styles[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}
