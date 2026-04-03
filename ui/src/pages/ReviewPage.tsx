import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getReviewQueue, getCounties, getTransaction, exportReviewQueue, downloadUrl } from "../api";
import Pagination from "../components/Pagination";
import {
  SubdivisionAssigner,
  PhaseResolver,
  SubdivisionPicker,
  PhasePicker,
  DismissAction,
} from "../components/ResolutionActions";
import type { TransactionDetail } from "../types";

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
  const queryClient = useQueryClient();
  const [county, setCounty] = useState<string>("");
  const [reason, setReason] = useState<string>("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const [exporting, setExporting] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);

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

  const handleResolved = () => {
    setSelectedId(null);
    queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    queryClient.invalidateQueries({ queryKey: ["stats"] });
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
                <tr
                  key={i}
                  onClick={() => {
                    const id = (row as Record<string, unknown>).ID;
                    if (typeof id === "number") setSelectedId(id);
                  }}
                  className="border-b border-gray-100 hover:bg-blue-50 cursor-pointer"
                >
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

      {selectedId !== null && (
        <ReviewDetailPanel
          transactionId={selectedId}
          onClose={() => setSelectedId(null)}
          onResolved={handleResolved}
        />
      )}
    </div>
  );
}


// --- Review Detail Panel ---

const DETAIL_FIELDS: { label: string; key: keyof TransactionDetail }[] = [
  { label: "County", key: "county" },
  { label: "Date", key: "date" },
  { label: "Type", key: "type" },
  { label: "Instrument", key: "instrument" },
  { label: "Grantor", key: "grantor" },
  { label: "Grantee", key: "grantee" },
  { label: "Subdivision", key: "subdivision" },
  { label: "Phase", key: "phase" },
  { label: "Inventory Category", key: "inventory_category" },
  { label: "Lots", key: "lots" },
  { label: "Price", key: "price" },
  { label: "Acres", key: "acres" },
  { label: "Notes", key: "notes" },
  { label: "Source File", key: "source_file" },
];

const SUBDIVISION_REASONS = [
  "subdivision_unmatched",
  "subdivision_unparsed_lines",
  "legal_unparsed_lines",
];

const PHASE_UNCONFIRMED_REASONS = ["phase_not_confirmed_by_lookup"];

const SUBDIVISION_PICK_REASONS = [
  "subdivision_ambiguous_candidates",
  "multiple_subdivision_candidates",
];

const PHASE_PICK_REASONS = ["multiple_phase_candidates"];


function pickResolutionComponent(
  reviewReasons: string[],
  transaction: TransactionDetail,
  onResolved: () => void,
) {
  const reasons = new Set(reviewReasons);

  // Priority: subdivision issues > phase issues > fallback
  if (SUBDIVISION_REASONS.some((r) => reasons.has(r))) {
    return <SubdivisionAssigner transaction={transaction} onResolved={onResolved} />;
  }
  if (SUBDIVISION_PICK_REASONS.some((r) => reasons.has(r))) {
    return <SubdivisionPicker transaction={transaction} onResolved={onResolved} />;
  }
  if (PHASE_UNCONFIRMED_REASONS.some((r) => reasons.has(r))) {
    return <PhaseResolver transaction={transaction} onResolved={onResolved} />;
  }
  if (PHASE_PICK_REASONS.some((r) => reasons.has(r))) {
    return <PhasePicker transaction={transaction} onResolved={onResolved} />;
  }
  return null;
}


function ReviewDetailPanel({
  transactionId,
  onClose,
  onResolved,
}: {
  transactionId: number;
  onClose: () => void;
  onResolved: () => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["transaction", transactionId],
    queryFn: () => getTransaction(transactionId),
  });

  const reviewReasons: string[] =
    (data?.parsed_data as Record<string, unknown> | null)?.review_reasons as string[] ?? [];

  return (
    <>
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-white shadow-xl z-50 flex flex-col border-l border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
          <h2 className="text-sm font-semibold text-gray-700">
            Review #{transactionId}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg leading-none px-1"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-5">
          {isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
          {error && <p className="text-red-600 text-sm">Failed to load transaction.</p>}
          {data && (
            <>
              {/* Review reasons */}
              <div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Review Reasons
                </h3>
                {reviewReasons.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {reviewReasons.map((r) => (
                      <span
                        key={r}
                        className="px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-800 rounded"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No specific reasons recorded</p>
                )}
              </div>

              {/* Legal description */}
              {data.export_legal_desc && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">
                    Legal Description
                  </h3>
                  <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-2 whitespace-pre-wrap">
                    {data.export_legal_desc}
                  </pre>
                </div>
              )}

              {/* Transaction details */}
              <div>
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                  Transaction Details
                </h3>
                <dl className="space-y-2">
                  {DETAIL_FIELDS.map((f) => {
                    const val = data[f.key];
                    if (val == null) return null;
                    return (
                      <div key={f.key} className="flex gap-2">
                        <dt className="text-xs text-gray-400 w-28 shrink-0 text-right pt-0.5">
                          {f.label}
                        </dt>
                        <dd className="text-sm text-gray-800">
                          {typeof val === "number"
                            ? val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : String(val)}
                        </dd>
                      </div>
                    );
                  })}
                </dl>
              </div>

              {/* Resolution actions */}
              <div className="border-t border-gray-200 pt-4 space-y-4">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                  Resolve
                </h3>
                {pickResolutionComponent(reviewReasons, data, onResolved)}

                {/* Dismiss is always available as fallback */}
                <div className="border-t border-gray-100 pt-3">
                  <DismissAction transaction={data} onResolved={onResolved} />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
