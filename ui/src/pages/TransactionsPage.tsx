import { useCallback, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import {
  downloadUrl,
  exportTransactions,
  getCounties,
  getReviewQueue,
  getSubdivisions,
  getTransactions,
  resolveAction,
} from "../api";
import Pagination from "../components/Pagination";
import TransactionDetailPanel from "../components/TransactionDetailPanel";
import type { TransactionFilters } from "../types";

interface ColumnDef {
  key: string;
  label: string;
  w: string;
  numeric?: boolean;
}

const COLUMNS: ColumnDef[] = [
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
  if (numeric && typeof val === "number") {
    return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
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

  const reviewDepthQ = useQuery({
    queryKey: ["review-queue-depth", filters.county],
    queryFn: () =>
      getReviewQueue({
        county: filters.county,
        page: 1,
        page_size: 1,
      }),
  });

  const selectedOnPage = data?.items.filter((row) => {
    const id = (row as Record<string, unknown>).id;
    return typeof id === "number" && selectedIds.has(id);
  }).length ?? 0;

  const applySearch = useCallback(() => {
    setFilters((prev) => ({ ...prev, search: search || undefined, page: 1 }));
  }, [search, setFilters]);

  const toggleSort = (col: string) => {
    const dbCol = SORT_MAP[col];
    if (!dbCol) return;
    setFilters((prev) => ({
      ...prev,
      sort_by: dbCol,
      sort_dir: prev.sort_by === dbCol && prev.sort_dir === "asc" ? "desc" : "asc",
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
        [...selectedIds].map((id) =>
          resolveAction(id, { action: "dismiss", note: "Bulk resolved" }),
        ),
      );
      setSelectedIds(new Set());
      queryClient.invalidateQueries({ queryKey: ["transactions"] });
      queryClient.invalidateQueries({ queryKey: ["stats"] });
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    } catch {
      alert("Some items failed to resolve");
    } finally {
      setBulkResolving(false);
    }
  };

  return (
    <div className="page-stack report-page">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Sales Workbench</p>
          <h1 className="page-title">Transactions</h1>
          <p className="page-subtitle">
            Review deed flow, filter by county and subdivision, and clear flagged
            rows without leaving the table.
          </p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="button-primary"
          >
            {exporting ? "Exporting..." : "Export"}
          </button>
        </div>
      </div>

      <section className="hero-band panel-pad">
        <div className="section-head">
          <div>
            <p className="section-title text-slate-50">Queue posture</p>
            <p className="section-caption text-slate-300">
              Active filters and review pressure for the current transaction set.
            </p>
          </div>
          <div className="chip-row">
            {filters.county && (
              <span className="badge badge-accent">{filters.county}</span>
            )}
            {filters.unmatched_only && (
              <span className="badge badge-warning">Review mode</span>
            )}
          </div>
        </div>
        <div className="hero-grid">
          <div className="hero-stat">
            <span className="hero-label">Visible transactions</span>
            <span className="hero-value">{data ? data.total.toLocaleString() : "..."}</span>
            <span className="hero-meta">Current result set</span>
          </div>
          <div className="hero-stat">
            <span className="hero-label">Flagged rows</span>
            <span className="hero-value">
              {(reviewDepthQ.data?.total ?? 0).toLocaleString()}
            </span>
            <span className="hero-meta">
              {filters.county ? `Within ${filters.county}` : "Across all counties"}
            </span>
          </div>
          <div className="hero-stat">
            <span className="hero-label">Selected rows</span>
            <span className="hero-value">{selectedIds.size.toLocaleString()}</span>
            <span className="hero-meta">
              {selectedOnPage > 0 ? `${selectedOnPage} on this page` : "Ready for bulk dismissal"}
            </span>
          </div>
        </div>
      </section>

      <section className="surface-card panel-pad">
        <div className="section-head">
          <div>
            <p className="section-title">Presets</p>
            <p className="section-caption">
              Jump into the most common queue slices without rebuilding filters.
            </p>
          </div>
        </div>
        <div className="chip-row">
          {FILTER_PRESETS.map((preset) => {
            const isActive =
              Object.entries(preset.params).every(([key, value]) => searchParams.get(key) === value) &&
              (Object.keys(preset.params).length > 0 || searchParams.toString() === "");
            return (
              <button
                key={preset.label}
                type="button"
                onClick={() => applyPreset(preset.params)}
                className={`chip-pill ${isActive ? "active" : ""}`}
              >
                {preset.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="filter-band">
        <div className="section-head">
          <div>
            <p className="section-title">Filters</p>
            <p className="section-caption">
              Combine county, subdivision, date, and keyword filters before drilling
              into a transaction.
            </p>
          </div>
        </div>
        <div className="filter-grid">
          <div className="field-stack">
            <label className="field-label" htmlFor="tx-county">
              County
            </label>
            <select
              id="tx-county"
              value={filters.county ?? ""}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  county: event.target.value || undefined,
                  subdivision: undefined,
                  page: 1,
                }))
              }
              className="form-control"
            >
              <option value="">All Counties</option>
              {counties?.map((county) => (
                <option key={county} value={county}>
                  {county}
                </option>
              ))}
            </select>
          </div>

          <div className="field-stack">
            <label className="field-label" htmlFor="tx-subdivision">
              Subdivision
            </label>
            <select
              id="tx-subdivision"
              value={filters.subdivision ?? ""}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  subdivision: event.target.value || undefined,
                  page: 1,
                }))
              }
              className="form-control"
            >
              <option value="">All Subdivisions</option>
              {subdivisions?.map((subdivision) => (
                <option key={subdivision.id} value={subdivision.canonical_name}>
                  {subdivision.canonical_name}
                </option>
              ))}
            </select>
          </div>

          <div className="field-stack">
            <label className="field-label" htmlFor="tx-date-from">
              From
            </label>
            <input
              id="tx-date-from"
              type="date"
              value={filters.date_from ?? ""}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  date_from: event.target.value || undefined,
                  page: 1,
                }))
              }
              className="form-control"
            />
          </div>

          <div className="field-stack">
            <label className="field-label" htmlFor="tx-date-to">
              To
            </label>
            <input
              id="tx-date-to"
              type="date"
              value={filters.date_to ?? ""}
              onChange={(event) =>
                setFilters((prev) => ({
                  ...prev,
                  date_to: event.target.value || undefined,
                  page: 1,
                }))
              }
              className="form-control"
            />
          </div>

          <div className="field-stack min-w-[260px] flex-[1.3]">
            <label className="field-label" htmlFor="tx-search">
              Search
            </label>
            <div className="flex gap-2">
              <input
                id="tx-search"
                type="text"
                placeholder="Grantor, grantee, subdivision..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && applySearch()}
                className="form-control"
              />
              <button type="button" onClick={applySearch} className="button-primary">
                Search
              </button>
            </div>
          </div>

          <label className="field-stack min-w-[170px] justify-end">
            <span className="field-label">Queue mode</span>
            <span className="chip-pill">
              <input
                type="checkbox"
                checked={filters.unmatched_only ?? false}
                onChange={(event) =>
                  setFilters((prev) => ({
                    ...prev,
                    unmatched_only: event.target.checked || undefined,
                    page: 1,
                  }))
                }
                className="h-4 w-4 rounded border-stone-300"
              />
              Flagged only
            </span>
          </label>
        </div>
      </section>

      <section className="surface-card data-shell">
        <div className="data-toolbar">
          <div>
            <p className="section-title">Transaction grid</p>
            <p className="data-note">
              Click a row to inspect details. Selected rows stay staged for bulk
              dismissal while you paginate.
            </p>
          </div>
          <div className="chip-row">
            {filters.search && <span className="badge badge-neutral">Search active</span>}
            {filters.subdivision && (
              <span className="badge badge-accent">{filters.subdivision}</span>
            )}
            {filters.inventory_category && (
              <span className="badge badge-neutral">{filters.inventory_category}</span>
            )}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th className="w-10">
                  <input
                    type="checkbox"
                    checked={
                      selectedIds.size > 0 &&
                      data?.items.every((row) => {
                        const id = (row as Record<string, unknown>).id;
                        return typeof id === "number" && selectedIds.has(id);
                      }) === true
                    }
                    onChange={(event) => {
                      if (event.target.checked) {
                        const ids = new Set(selectedIds);
                        data?.items.forEach((row) => {
                          const id = (row as Record<string, unknown>).id;
                          if (typeof id === "number") ids.add(id);
                        });
                        setSelectedIds(ids);
                      } else {
                        setSelectedIds(new Set());
                      }
                    }}
                    className="h-4 w-4 rounded border-stone-300"
                  />
                </th>
                {COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    onClick={() => toggleSort(column.key)}
                    className={`${column.w} cursor-pointer select-none ${column.numeric ? "text-right" : "text-left"}`}
                  >
                    {column.label}
                    {filters.sort_by === SORT_MAP[column.key] && (
                      <span className="ml-1">
                        {filters.sort_dir === "asc" ? "\u25b2" : "\u25bc"}
                      </span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={COLUMNS.length + 1} className="table-empty text-center">
                    Loading transactions...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={COLUMNS.length + 1} className="table-empty text-center">
                    No transactions found for the current filter set.
                  </td>
                </tr>
              ) : (
                data?.items.map((row, index) => {
                  const id = (row as Record<string, unknown>).id;
                  const isSelected = typeof id === "number" && selectedIds.has(id);
                  return (
                    <tr
                      key={index}
                      onClick={() => {
                        if (typeof id === "number") setSelectedId(id);
                      }}
                      className={isSelected ? "is-selected cursor-pointer" : "cursor-pointer"}
                    >
                      <td onClick={(event) => event.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => {
                            if (typeof id === "number") toggleRow(id);
                          }}
                          className="h-4 w-4 rounded border-stone-300"
                        />
                      </td>
                      {COLUMNS.map((column) => (
                        <td
                          key={column.key}
                          className={`${column.numeric ? "text-right tabular-nums" : ""} truncate max-w-xs`}
                          title={fmt((row as Record<string, unknown>)[column.key])}
                        >
                          {fmt((row as Record<string, unknown>)[column.key], column.numeric)}
                        </td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {data && (
        <Pagination
          page={data.page}
          pageSize={data.page_size}
          total={data.total}
          onPageChange={(page) => setFilters((prev) => ({ ...prev, page }))}
          onPageSizeChange={(pageSize) =>
            setFilters((prev) => ({ ...prev, page_size: pageSize, page: 1 }))
          }
        />
      )}

      {selectedIds.size > 0 && (
        <div className="bulk-dock">
          <span className="text-sm font-medium text-slate-100">
            {selectedIds.size} selected
          </span>
          <button
            type="button"
            onClick={handleBulkResolve}
            disabled={bulkResolving}
            className="button-primary"
          >
            {bulkResolving ? "Resolving..." : "Dismiss Selected"}
          </button>
          <button
            type="button"
            onClick={() => setSelectedIds(new Set())}
            className="button-ghost"
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
