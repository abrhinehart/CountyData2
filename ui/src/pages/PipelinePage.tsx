import { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getCounties, startETL, getETLStatus, exportTransactions, exportReviewQueue, downloadUrl } from "../api";

export default function PipelinePage() {
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<string[]>([]);
  const [polling, setPolling] = useState(false);

  const { data: counties } = useQuery({ queryKey: ["counties"], queryFn: getCounties });
  const { data: etlStatus, refetch: refetchStatus } = useQuery({
    queryKey: ["etl-status"],
    queryFn: getETLStatus,
    refetchInterval: polling ? 2000 : false,
  });

  useEffect(() => {
    if (etlStatus?.status === "running") {
      setPolling(true);
    } else if (polling && (etlStatus?.status === "completed" || etlStatus?.status === "failed")) {
      setPolling(false);
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
    }
  }, [etlStatus?.status, polling, queryClient]);

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

  const isRunning = etlStatus?.status === "running";
  const results = etlStatus?.results ?? {};
  const hasResults = Object.keys(results).length > 0;

  return (
    <div className="max-w-3xl">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">Pipeline Controls</h2>

      {/* ETL Run */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <h3 className="font-medium text-gray-700 mb-3">Run ETL</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {counties?.map((c) => (
            <label
              key={c}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded border text-sm cursor-pointer transition-colors ${
                selected.includes(c) ? "bg-blue-50 border-blue-300 text-blue-700" : "border-gray-200 text-gray-600 hover:bg-gray-50"
              }`}
            >
              <input
                type="checkbox"
                checked={selected.includes(c)}
                onChange={() => toggleCounty(c)}
                className="rounded"
              />
              {c}
            </label>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleRun(false)}
            disabled={isRunning || selected.length === 0}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Run Selected ({selected.length})
          </button>
          <button
            onClick={() => handleRun(true)}
            disabled={isRunning}
            className="px-4 py-2 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50"
          >
            Run All Counties
          </button>
        </div>
      </div>

      {/* ETL Status */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 mb-4">
        <h3 className="font-medium text-gray-700 mb-3">ETL Status</h3>
        <div className="flex items-center gap-3 mb-3">
          <StatusBadge status={etlStatus?.status ?? "idle"} />
          {etlStatus?.started_at && (
            <span className="text-sm text-gray-500">
              Started: {new Date(etlStatus.started_at).toLocaleString()}
            </span>
          )}
          {etlStatus?.completed_at && (
            <span className="text-sm text-gray-500">
              Finished: {new Date(etlStatus.completed_at).toLocaleString()}
            </span>
          )}
        </div>

        {etlStatus?.error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm mb-3">
            {etlStatus.error}
          </div>
        )}

        {hasResults && (
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
                  <td className="py-1.5">{county}</td>
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

      {/* Export Controls */}
      <div className="bg-white rounded-lg border border-gray-200 p-5">
        <h3 className="font-medium text-gray-700 mb-3">Export</h3>
        <div className="flex gap-2">
          <button
            onClick={handleExportTransactions}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700"
          >
            Export All Transactions
          </button>
          <button
            onClick={handleExportReview}
            className="px-4 py-2 text-sm bg-amber-600 text-white rounded hover:bg-amber-700"
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
