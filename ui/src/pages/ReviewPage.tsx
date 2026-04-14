import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  downloadUrl,
  exportReviewQueue,
  getCounties,
  getReviewQueue,
  getTransaction,
} from "../api";
import Pagination from "../components/Pagination";
import {
  DismissAction,
  PhasePicker,
  PhaseResolver,
  SubdivisionAssigner,
  SubdivisionPicker,
} from "../components/ResolutionActions";
import type { TransactionDetail } from "../types";

interface ColumnDef {
  key: string;
  label: string;
  w: string;
  numeric?: boolean;
}

const COLUMNS: ColumnDef[] = [
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

function fmt(val: unknown, numeric?: boolean): string {
  if (val == null) return "";
  if (numeric && typeof val === "number") {
    return val.toLocaleString(undefined, { maximumFractionDigits: 0 });
  }
  return String(val);
}

function pickResolutionComponent(
  reviewReasons: string[],
  transaction: TransactionDetail,
  onResolved: () => void,
) {
  const reasons = new Set(reviewReasons);
  if (SUBDIVISION_REASONS.some((reason) => reasons.has(reason))) {
    return <SubdivisionAssigner transaction={transaction} onResolved={onResolved} />;
  }
  if (SUBDIVISION_PICK_REASONS.some((reason) => reasons.has(reason))) {
    return <SubdivisionPicker transaction={transaction} onResolved={onResolved} />;
  }
  if (PHASE_UNCONFIRMED_REASONS.some((reason) => reasons.has(reason))) {
    return <PhaseResolver transaction={transaction} onResolved={onResolved} />;
  }
  if (PHASE_PICK_REASONS.some((reason) => reasons.has(reason))) {
    return <PhasePicker transaction={transaction} onResolved={onResolved} />;
  }
  return null;
}

export default function ReviewPage() {
  const queryClient = useQueryClient();
  const [county, setCounty] = useState("");
  const [reason, setReason] = useState("");
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
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
  };

  return (
    <div className="page-stack report-page">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Review Queue</p>
          <h1 className="page-title">Triage Workbench</h1>
          <p className="page-subtitle">
            Investigate flagged deeds, scan review reasons quickly, and resolve
            subdivision or phase issues from one focused queue.
          </p>
        </div>
        <div className="page-actions">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting}
            className="button-primary"
          >
            {exporting ? "Exporting..." : "Export Queue"}
          </button>
        </div>
      </div>

      <section className="hero-band panel-pad">
        <div className="section-head">
          <div>
            <p className="section-title text-slate-50">Triage posture</p>
            <p className="section-caption text-slate-300">
              Review volume, active county focus, and reason filtering for the
              current queue slice.
            </p>
          </div>
          <div className="chip-row">
            {county && <span className="badge badge-accent">{county}</span>}
            {reason && <span className="badge badge-warning">{reason}</span>}
          </div>
        </div>
        <div className="hero-grid">
          <div className="hero-stat">
            <span className="hero-label">Flagged rows</span>
            <span className="hero-value">{data ? data.total.toLocaleString() : "..."}</span>
            <span className="hero-meta">Current triage set</span>
          </div>
          <div className="hero-stat">
            <span className="hero-label">Page size</span>
            <span className="hero-value">{pageSize.toLocaleString()}</span>
            <span className="hero-meta">Rows per review sweep</span>
          </div>
          <div className="hero-stat">
            <span className="hero-label">Focused reason</span>
            <span className="hero-value">{reason ? "1" : "All"}</span>
            <span className="hero-meta">
              {reason ? "Single issue isolated" : "No reason filter applied"}
            </span>
          </div>
        </div>
      </section>

      <section className="filter-band">
        <div className="section-head">
          <div>
            <p className="section-title">Queue Filters</p>
            <p className="section-caption">
              Narrow the queue by county or one specific parsing reason.
            </p>
          </div>
        </div>
        <div className="filter-grid">
          <div className="field-stack">
            <label className="field-label" htmlFor="review-county">
              County
            </label>
            <select
              id="review-county"
              value={county}
              onChange={(event) => {
                setCounty(event.target.value);
                setPage(1);
              }}
              className="form-control"
            >
              <option value="">All Counties</option>
              {counties?.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div className="field-stack min-w-[280px] flex-1">
            <label className="field-label" htmlFor="review-reason">
              Review reason
            </label>
            <input
              id="review-reason"
              type="text"
              placeholder="e.g. subdivision_unmatched"
              value={reason}
              onChange={(event) => {
                setReason(event.target.value);
                setPage(1);
              }}
              className="form-control"
            />
          </div>

          <div className="field-stack min-w-[180px]">
            <span className="field-label">Queue volume</span>
            <span className="chip-pill">
              {data ? `${data.total.toLocaleString()} flagged rows` : "Loading..."}
            </span>
          </div>
        </div>
      </section>

      <section className="surface-card data-shell">
        <div className="data-toolbar">
          <div>
            <p className="section-title">Review grid</p>
            <p className="data-note">
              Review reasons stay visible in-line so the queue remains scannable
              before you open the drawer.
            </p>
          </div>
          <div className="chip-row">
            {county && <span className="badge badge-accent">{county}</span>}
            {reason && <span className="badge badge-warning">Reason filter</span>}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                {COLUMNS.map((column) => (
                  <th
                    key={column.key}
                    className={`${column.w} ${column.numeric ? "text-right" : "text-left"}`}
                  >
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={COLUMNS.length} className="table-empty text-center">
                    Loading review queue...
                  </td>
                </tr>
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={COLUMNS.length} className="table-empty text-center">
                    No review rows found.
                  </td>
                </tr>
              ) : (
                data?.items.map((row, index) => {
                  const id = (row as Record<string, unknown>).ID;
                  const reasons = fmt((row as Record<string, unknown>)["Review Reasons"]);
                  return (
                    <tr
                      key={index}
                      onClick={() => {
                        if (typeof id === "number") setSelectedId(id);
                      }}
                      className="cursor-pointer"
                    >
                      {COLUMNS.map((column) => (
                        <td
                          key={column.key}
                          className={`${column.numeric ? "text-right tabular-nums" : ""} truncate max-w-xs`}
                          title={fmt((row as Record<string, unknown>)[column.key])}
                        >
                          {column.key === "Review Reasons" ? (
                            <ReviewReasonCell text={reasons} />
                          ) : (
                            fmt((row as Record<string, unknown>)[column.key], column.numeric)
                          )}
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
          onPageChange={setPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(1);
          }}
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

function ReviewReasonCell({ text }: { text: string }) {
  const parts = text
    .split(/[,;]+/)
    .map((part) => part.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return <span className="text-[var(--text-soft)]">No reason recorded</span>;
  }

  return (
    <div className="drawer-chip-row">
      {parts.slice(0, 2).map((part) => (
        <span key={part} className="badge badge-warning">
          {part.replace(/_/g, " ")}
        </span>
      ))}
      {parts.length > 2 && <span className="badge badge-neutral">+{parts.length - 2}</span>}
    </div>
  );
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

  const reviewReasons =
    ((data?.parsed_data as Record<string, unknown> | null)?.review_reasons as string[] | undefined) ??
    [];

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="inspector-drawer">
        <div className="inspector-header">
          <div>
            <p className="inspector-kicker">Review</p>
            <h2 className="inspector-title">#{transactionId}</h2>
            <p className="inspector-subtitle">
              Flagged transaction detail with legal context and resolution controls.
            </p>
          </div>
          <button onClick={onClose} className="inspector-close" aria-label="Close panel">
            &times;
          </button>
        </div>

        <div className="inspector-body">
          {isLoading && <p className="data-note">Loading review detail...</p>}
          {error && <p className="data-note text-[var(--danger)]">Failed to load transaction.</p>}
          {data && (
            <>
              <section className="inspector-section flat">
                <div className="section-head">
                  <h3 className="section-title">Review Reasons</h3>
                  <span className="badge badge-warning">
                    {reviewReasons.length > 0 ? reviewReasons.length : 1}
                  </span>
                </div>
                {reviewReasons.length > 0 ? (
                  <div className="drawer-chip-row">
                    {reviewReasons.map((reason) => (
                      <span key={reason} className="badge badge-warning">
                        {reason.replace(/_/g, " ")}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="data-note">No specific reasons recorded.</p>
                )}
              </section>

              {data.export_legal_desc && (
                <section className="inspector-section">
                  <div className="section-head">
                    <h3 className="section-title">Legal Description</h3>
                    <span className="badge badge-neutral">Parsed text</span>
                  </div>
                  <pre className="code-block">{data.export_legal_desc}</pre>
                </section>
              )}

              <section className="inspector-section">
                <div className="section-head">
                  <h3 className="section-title">Transaction Detail</h3>
                  <span className="badge badge-neutral">Record</span>
                </div>
                <div className="detail-grid">
                  {DETAIL_FIELDS.map((field) => {
                    const value = data[field.key];
                    if (value == null) return null;
                    return (
                      <div key={field.key} className="detail-row">
                        <span className="detail-label">{field.label}</span>
                        <span className="detail-value">
                          {typeof value === "number"
                            ? value.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            : String(value)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>

              <section className="inspector-section">
                <div className="section-head">
                  <h3 className="section-title">Resolve</h3>
                  <span className="badge badge-accent">Action panel</span>
                </div>
                {pickResolutionComponent(reviewReasons, data, onResolved)}
                <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
                  <DismissAction transaction={data} onResolved={onResolved} />
                </div>
              </section>
            </>
          )}
        </div>
      </aside>
    </>
  );
}
