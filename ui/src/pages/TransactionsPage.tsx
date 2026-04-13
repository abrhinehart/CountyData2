import { useState, useCallback, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { getTransactions, getCounties, getSubdivisions, getReviewQueue, exportTransactions, downloadUrl, resolveAction } from "../api";
import type { TransactionFilters } from "../types";
import Pagination from "../components/Pagination";
import TransactionDetailPanel from "../components/TransactionDetailPanel";

const COLUMNS = [
  { key: "Date", label: "Date", w: "w-24" },
  { key: "County", label: "County", w: "w-24" },
  { key: "Type", label: "Type", w: "w-32" },
  { key: "Grantor", label: "Grantor", w: "w-44" },
  { key: "Grantee", label: "Grantee", w: "w-44" },
  { key: "Subdivision", label: "Subdivision", w: "w-40" },
  { key: "Phase", label: "Phase", w: "w-16" },
  { key: "Inventory Category", label: "Category", w: "w-32" },
  { key: "Lots", label: "Lots", w: "w-14", numeric: true },
  { key: "Price", label: "Price", w: "w-24", numeric: true },
  { key: "$ / Lot", label: "$/Lot", w: "w-20", numeric: true },
  { key: "Acres", label: "Acres", w: "w-16", numeric: true },
  { key: "$ / Acre", label: "$/Acre", w: "w-20", numeric: true },
];

const SORT_MAP: Record<string, string> = {
  Date: "date",
  County: "county",
  Type: "type",
  Grantor: "grantor",
  Grantee: "grantee",
  Subdivision: "subdivision",
  "Inventory Category": "inventory_category",
  Lots: "lots",
  Price: "price",
  "$ / Lot": "price_per_lot",
  Acres: "acres",
  "$ / Acre": "price_per_acre",
};

const FILTER_PRESETS: { label: string; params: Record<string, string> }[] = [
  { label: "All Transactions", params: {} },
  { label: "Flagged for Review", params: { unmatched_only: "true" } },
  { label: "Bay Unmatched", params: { county: "Bay", unmatched_only: "true" } },
  { label: "House Sales", params: { inventory_category: "House Sale" } },
];

function fmt(val: unknown, numeric?: boolean): string {
  if (val == null) return "";
  if (numeric && typeof val === "number") return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return String(val);
}

function filtersFromParams(sp: URLSearchParams): TransactionFilters {
  return {
    county: sp.get("county") || undefined,
    subdivision: sp.get("subdivision") || undefined,
    date_from: sp.get("date_from") || undefined,
    date_to: sp.get("date_to") || undefined,
    inventory_category: sp.get("inventory_category") || undefined,
    unmatched_only: sp.get("unmatched_only") === "true" || undefined,
    search: sp.get("search") || undefined,
    page: Number(sp.get("page")) || 1,
    page_size: Number(sp.get("page_size")) || 50,
    sort_by: sp.get("sort_by") || "date",
    sort_dir: sp.get("sort_dir") || "desc",
  };
}

function filtersToParams(f: TransactionFilters): Record<string, string> {
  const out: Record<string, string> = {};
  if (f.county) out.county = f.county;
  if (f.subdivision) out.subdivision = f.subdivision;
  if (f.date_from) out.date_from = f.date_from;
  if (f.date_to) out.date_to = f.date_to;
  if (f.inventory_category) out.inventory_category = f.inventory_category;
  if (f.unmatched_only) out.unmatched_only = "true";
  if (f.search) out.search = f.search;
  if (f.page && f.page > 1) out.page = String(f.page);
  if (f.page_size && f.page_size !== 50) out.page_size = String(f.page_size);
  if (f.sort_by && f.sort_by !== "date") out.sort_by = f.sort_by;
  if (f.sort_dir && f.sort_dir !== "desc") out.sort_dir = f.sort_dir;
  return out;
}

export default function TransactionsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => filtersFromParams(searchParams), [searchParams]);
  const setFilters = useCallback(
    (updater: (prev: TransactionFilters) => TransactionFilters) => {
      setSearchParams((prev) => {
        const current = filtersFromParams(prev);
        const next = updater(current);
        return filtersToParams(next);
      });
    },
    [setSearchParams],
  );
  const queryClient = useQueryClient();
  const [search, setSearch] = useState(filters.search ?? "");
  const [exporting, setExporting] = useState(false);
  const [bulkResolving, setBulkResolving] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());

  const { data: counties } = useQuery({ queryKey: ["counties"], queryFn: getCounties });
  const { data: subdivisions } = useQuery({
    queryKey: ["subdivisions", filters.county],
    queryFn: () => getSubdivisions(filters.county),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["transactions", filters],
    queryFn: () => getTransactions(filters),
  });

  // Review queue depth for context stats
  const reviewDepthQ = useQuery({
    queryKey: ["review-queue-depth", filters.county],
    queryFn: () => getReviewQueue({
      county: filters.county,
      page: 1,
      page_size: 1,
    }),
  });

  const applySearch = useCallback(() => {
    setFilters((f) => ({ ...f, search: search || undefined, page: 1 }));
  }, [search, setFilters]);

  const toggleSort = (col: string) => {
    const dbCol = SORT_MAP[col];
    if (!dbCol) return;
    setFilters((f) => ({
      ...f,
      sort_by: dbCol,
      sort_dir: f.sort_by === dbCol && f.sort_dir === "asc" ? "desc" : "asc",
      page: 1,
    }));
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await exportTransactions({
        county: filters.county,
        subdivision: filters.subdivision,
        date_from: filters.date_from,
        date_to: filters.date_to,
        inventory_category: filters.inventory_category,
        unmatched_only: filters.unmatched_only,
      });
      window.open(downloadUrl(res.filename), "_blank");
    } catch {
      alert("Export failed");
    } finally {
      setExporting(false);
    }
  };

  const toggleRow = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const applyPreset = (params: Record<string, string>) => {
    setSearchParams(params);
  };

  const handleBulkResolve = async () => {
    if (selectedIds.size === 0) return;
    setBulkResolving(true);
    try {
      await Promise.all(
        [...selectedIds].map((id) => resolveAction(id, { action: "dismiss", note: "Bulk resolved" }))
      );
      setSelectedIds(new Set());
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
    } catch {
      alert("Some items failed to resolve");
    } finally {
      setBulkResolving(false);
    }
  };

  return (
    <div>
      {/* Context stats bar */}
      <div className="flex items-center gap-4 mb-4 text-sm">
        <span className="text-gray-800 font-semibold">
          {data ? `${data.total.toLocaleString()} transactions` : "Loading..."}
        </span>
        {filters.county && (
          <span className="text-gray-500">
            in {filters.county}
          </span>
        )}
        {(reviewDepthQ.data?.total ?? 0) > 0 && (
          <span className="text-amber-600 font-medium">
            {reviewDepthQ.data!.total.toLocaleString()} flagged
            {filters.county ? ` in ${filters.county}` : ""}
          </span>
        )}
        {filters.unmatched_only && (
          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium">
            Review mode
          </span>
        )}
      </div>

      {/* Filter presets */}
      <div className="flex gap-1.5 mb-3">
        {FILTER_PRESETS.map((p) => {
          const isActive = Object.entries(p.params).every(
            ([k, v]) => searchParams.get(k) === v
          ) && (Object.keys(p.params).length > 0 || searchParams.toString() === "");
          return (
            <button
              key={p.label}
              onClick={() => applyPreset(p.params)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                isActive
                  ? "bg-blue-100 text-blue-700"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">County</label>
            <select
              value={filters.county ?? ""}
              onChange={(e) => setFilters((f) => ({ ...f, county: e.target.value || undefined, subdivision: undefined, page: 1 }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white min-w-[140px]"
            >
              <option value="">All Counties</option>
              {counties?.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Subdivision</label>
            <select
              value={filters.subdivision ?? ""}
              onChange={(e) => setFilters((f) => ({ ...f, subdivision: e.target.value || undefined, page: 1 }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white min-w-[180px]"
            >
              <option value="">All Subdivisions</option>
              {subdivisions?.map((s) => <option key={s.id} value={s.canonical_name}>{s.canonical_name}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={filters.date_from ?? ""}
              onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value || undefined, page: 1 }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={filters.date_to ?? ""}
              onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value || undefined, page: 1 }))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">Search</label>
            <div className="flex gap-1">
              <input
                type="text"
                placeholder="Grantor, grantee, subdivision..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && applySearch()}
                className="border border-gray-300 rounded px-2 py-1.5 text-sm w-60"
              />
              <button onClick={applySearch} className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">
                Search
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 pb-0.5">
            <label className="flex items-center gap-1.5 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={filters.unmatched_only ?? false}
                onChange={(e) => setFilters((f) => ({ ...f, unmatched_only: e.target.checked || undefined, page: 1 }))}
                className="rounded"
              />
              Flagged only
            </label>
          </div>

          <div className="ml-auto pb-0.5">
            <button
              onClick={handleExport}
              disabled={exporting}
              className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {exporting ? "Exporting..." : "Export"}
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-2 w-8">
                <input
                  type="checkbox"
                  checked={selectedIds.size > 0 && data?.items.every((r) => {
                    const id = (r as Record<string, unknown>).id;
                    return typeof id === "number" && selectedIds.has(id);
                  })}
                  onChange={(e) => {
                    if (e.target.checked) {
                      const ids = new Set(selectedIds);
                      data?.items.forEach((r) => {
                        const id = (r as Record<string, unknown>).id;
                        if (typeof id === "number") ids.add(id);
                      });
                      setSelectedIds(ids);
                    } else {
                      setSelectedIds(new Set());
                    }
                  }}
                  className="rounded"
                />
              </th>
              {COLUMNS.map((col) => (
                <th
                  key={col.key}
                  onClick={() => toggleSort(col.key)}
                  className={`px-3 py-2 text-left font-medium text-gray-600 cursor-pointer hover:text-gray-900 select-none ${col.w} ${
                    col.numeric ? "text-right" : ""
                  }`}
                >
                  {col.label}
                  {filters.sort_by === SORT_MAP[col.key] && (
                    <span className="ml-1">{filters.sort_dir === "asc" ? "\u25b2" : "\u25bc"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="px-3 py-8 text-center text-gray-400">Loading...</td>
              </tr>
            ) : data?.items.length === 0 ? (
              <tr>
                <td colSpan={COLUMNS.length + 1} className="px-3 py-8 text-center text-gray-400">No transactions found</td>
              </tr>
            ) : (
              data?.items.map((row, i) => {
                const id = (row as Record<string, unknown>).id;
                const isSelected = typeof id === "number" && selectedIds.has(id);
                return (
                  <tr
                    key={i}
                    onClick={() => {
                      if (typeof id === "number") setSelectedId(id);
                    }}
                    className={`border-b border-gray-100 hover:bg-blue-50 cursor-pointer ${isSelected ? "bg-blue-50/50" : ""}`}
                  >
                    <td className="px-3 py-1.5" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => { if (typeof id === "number") toggleRow(id); }}
                        className="rounded"
                      />
                    </td>
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
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          onPageChange={(p) => setFilters((f) => ({ ...f, page: p }))}
          onPageSizeChange={(s) => setFilters((f) => ({ ...f, page_size: s, page: 1 }))}
        />
      )}

      {/* Bulk action bar */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900 text-white rounded-lg shadow-xl px-5 py-3 flex items-center gap-4 z-30">
          <span className="text-sm">{selectedIds.size} selected</span>
          <button
            onClick={handleBulkResolve}
            disabled={bulkResolving}
            className="px-3 py-1.5 text-sm bg-amber-500 text-white rounded hover:bg-amber-600 disabled:opacity-50 font-medium"
          >
            {bulkResolving ? "Resolving..." : "Dismiss Selected"}
          </button>
          <button
            onClick={() => setSelectedIds(new Set())}
            className="px-3 py-1.5 text-sm text-gray-300 hover:text-white"
          >
            Clear
          </button>
        </div>
      )}

      {selectedId !== null && (
        <TransactionDetailPanel
          transactionId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}
    </div>
  );
}
