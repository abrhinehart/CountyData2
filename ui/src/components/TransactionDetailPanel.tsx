import type { ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getTransaction } from "../api";
import {
  DismissAction,
  PhasePicker,
  PhaseResolver,
  SubdivisionAssigner,
  SubdivisionPicker,
} from "./ResolutionActions";
import type { TransactionDetail } from "../types";

function fmtNum(val: number | null | undefined): string {
  if (val == null) return "-";
  return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function fmtJson(val: Record<string, unknown> | null | undefined): string {
  if (!val || Object.keys(val).length === 0) return "-";
  return JSON.stringify(val, null, 2);
}

const FIELDS: { label: string; key: string; format?: "num" | "json" | "pre" }[] = [
  { label: "ID", key: "id" },
  { label: "County", key: "county" },
  { label: "Date", key: "date" },
  { label: "Type", key: "type" },
  { label: "Instrument", key: "instrument" },
  { label: "Grantor", key: "grantor" },
  { label: "Grantee", key: "grantee" },
  { label: "Subdivision", key: "subdivision" },
  { label: "Phase", key: "phase" },
  { label: "Inventory Category", key: "inventory_category" },
  { label: "Lots", key: "lots", format: "num" },
  { label: "Price", key: "price", format: "num" },
  { label: "$ / Lot", key: "price_per_lot", format: "num" },
  { label: "Acres", key: "acres", format: "num" },
  { label: "Acres Source", key: "acres_source" },
  { label: "$ / Acre", key: "price_per_acre", format: "num" },
  { label: "Export Legal Description", key: "export_legal_desc", format: "pre" },
  { label: "Export Legal Raw", key: "export_legal_raw", format: "pre" },
  { label: "Deed Legal Description", key: "deed_legal_desc", format: "pre" },
  { label: "Deed Legal Parsed", key: "deed_legal_parsed", format: "json" },
  { label: "Deed Locator", key: "deed_locator", format: "json" },
  { label: "Notes", key: "notes" },
  { label: "Source File", key: "source_file" },
  { label: "Inserted At", key: "inserted_at" },
  { label: "Updated At", key: "updated_at" },
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

export default function TransactionDetailPanel({
  transactionId,
  onClose,
  onResolved,
}: {
  transactionId: number;
  onClose: () => void;
  onResolved?: () => void;
}) {
  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["transaction", transactionId],
    queryFn: () => getTransaction(transactionId),
  });

  const reviewReasons =
    ((data?.parsed_data as Record<string, unknown> | null)?.review_reasons as string[] | undefined) ??
    [];

  const handleResolved = () => {
    queryClient.invalidateQueries({ queryKey: ["transactions"] });
    queryClient.invalidateQueries({ queryKey: ["review-queue"] });
    queryClient.invalidateQueries({ queryKey: ["stats"] });
    onResolved?.();
    onClose();
  };

  return (
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="inspector-drawer">
        <div className="inspector-header">
          <div>
            <p className="inspector-kicker">Transaction</p>
            <h2 className="inspector-title">#{transactionId}</h2>
            <p className="inspector-subtitle">
              Sales record detail, parsed legal text, and resolution controls.
            </p>
          </div>
          <button onClick={onClose} className="inspector-close" aria-label="Close panel">
            &times;
          </button>
        </div>

        <div className="inspector-body">
          {isLoading && <p className="data-note">Loading transaction...</p>}
          {error && <p className="data-note text-[var(--danger)]">Failed to load transaction.</p>}
          {data && (
            <>
              {(data.review_flag || reviewReasons.length > 0) && (
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
                    <span className="badge badge-warning">Flagged with no explicit reason</span>
                  )}
                </section>
              )}

              <section className="inspector-section">
                <div className="section-head">
                  <h3 className="section-title">Field Summary</h3>
                  <span className="badge badge-neutral">Core record</span>
                </div>
                <div className="detail-grid">
                  {FIELDS.map((field) => {
                    const raw = (data as unknown as Record<string, unknown>)[field.key];
                    if (raw == null && field.format !== "json") return null;

                    let display: ReactNode;
                    if (field.format === "num") {
                      display = fmtNum(raw as number | null);
                    } else if (field.format === "json") {
                      const text = fmtJson(raw as Record<string, unknown> | null);
                      if (text === "-") return null;
                      display = <pre className="code-block">{text}</pre>;
                    } else if (field.format === "pre") {
                      display = <pre className="code-block">{String(raw ?? "-")}</pre>;
                    } else if (typeof raw === "boolean") {
                      display = raw ? "Yes" : "No";
                    } else {
                      display = String(raw ?? "-");
                    }

                    return (
                      <div key={field.key} className="detail-row">
                        <span className="detail-label">{field.label}</span>
                        <span className="detail-value">{display}</span>
                      </div>
                    );
                  })}
                </div>
              </section>

              {(data.review_flag || reviewReasons.length > 0) && (
                <section className="inspector-section">
                  <div className="section-head">
                    <h3 className="section-title">Resolve</h3>
                    <span className="badge badge-accent">Actions</span>
                  </div>
                  {pickResolutionComponent(reviewReasons, data, handleResolved)}
                  <div className="mt-4 border-t border-[var(--border-subtle)] pt-4">
                    <DismissAction transaction={data} onResolved={handleResolved} />
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
