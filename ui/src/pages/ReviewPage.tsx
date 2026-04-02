import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getReviewQueue, getCounties, exportReviewQueue, downloadUrl } from "../api";
import Pagination from "../components/Pagination";

const COLUMNS = [
  { key: "ID", label: "ID", w: "w-16" },
  { key: "County", label: "County", w: "w-24" },
  { key: "Date", label: "Date", w: "w-24" },
  { key: "Review Reasons", label: "Review Reasons", w: "w-52" },
  { key: "Grantor", label: "Grantor", w: "w-40" },
  { key: "Grantee", label: "Grantee", w: "w-40" },
  { key: "Type", label: "Type", w: "w-28" },
  { key: "Price", label: "Price", w: "w-20", numeric: true },
  { key: "Subdivision", label: "Subdivision", w: "w-36" },
  { key: "Phase", label: "Phase", w: "w-16" },
  { key: "Inventory Category", label: "Category", w: "w-28" },
];

function fmt(val: unknown, numeric?: boolean): string {
  if (val == null) return "";
  if (numeric && typeof val === "number") return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return String(val);
}

export default function ReviewPage() {
  const [county, setCounty] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [exporting, setExporting] = useState(false);

  const { data: counties } = useQuery({ queryKey: ["counties"], queryFn: getCounties });

  const { data, isLoading } = useQuery({
    queryKey: ["review-queue", county, reason, page, pageSize],
    queryFn: () =>
      getReviewQueue({
        county: county || undefined,
        reason: reason || undefined,
        page,
        page_size: pageSize,
      }),
  });

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await exportReviewQueue({
        county: county || undefined,
        reasons: reason ? [reason] : undefined,
      });
      window.open(downloadUrl(res.filename), "_blank");
    } catch {
      alert("Export failed");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-800">Review Queue</h2>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
        >
          {exporting ? "Exporting..." : "Export to Excel"}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">County</label>
            <select
              value={county}
              onChange={(e) => { setCounty(e.target.value); setPage(1); }}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white min-w-[140px]"
            >
              <option value="">All Counties</option>
              {counties?.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Review Reason</label>
            <input
              type="text"
              placeholder="e.g. subdivision_unmatched"
              value={reason}
              onChange={(e) => { setReason(e.target.value); setPage(1); }}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-64"
            />
          </div>

          {data && (
            <span className="text-sm text-gray-500 pb-1">
              {data.total.toLocaleString()} flagged rows
            </span>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  className={`px-3 py-2 text-left font-medium text-gray-600 ${col.w} ${col.numeric ? "text-right" : ""}`}
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={COLUMNS.length} className="px-3 py-8 text-center text-gray-400">Loading...</td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length} className="px-3 py-8 text-center text-gray-400">No review rows found</td>
              </tr>
            ) : (
              data?.items.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  {COLUMNS.map((col) => (
                    <td
                      key={col.key}
                      className={`px-3 py-1.5 truncate max-w-xs ${col.numeric ? "text-right tabular-nums" : ""}`}
                      title={fmt((row as Record<string, unknown>)[col.key])}
                    >
                      {fmt((row as Record<string, unknown>)[col.key], col.numeric)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          onPageChange={setPage}
          onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        />
      )}
    </div>
  );
}
