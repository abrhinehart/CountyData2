import { useQuery } from "@tanstack/react-query";
import { getTransaction } from "../api";

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
  { label: "Parsed Data", key: "parsed_data", format: "json" },
  { label: "Notes", key: "notes" },
  { label: "Review Flag", key: "review_flag" },
  { label: "Source File", key: "source_file" },
  { label: "Inserted At", key: "inserted_at" },
  { label: "Updated At", key: "updated_at" },
];

export default function TransactionDetailPanel({
  transactionId,
  onClose,
}: {
  transactionId: number;
  onClose: () => void;
}) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["transaction", transactionId],
    queryFn: () => getTransaction(transactionId),
  });

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40"
        onClick={onClose}
      />
      {/* Panel */}
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-white shadow-xl z-50 flex flex-col border-l border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
          <h2 className="text-sm font-semibold text-gray-700">
            Transaction #{transactionId}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg leading-none px-1"
          >
            &times;
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading && (
            <p className="text-gray-400 text-sm">Loading...</p>
          )}
          {error && (
            <p className="text-red-600 text-sm">Failed to load transaction.</p>
          )}
          {data && (
            <dl className="space-y-3">
              {FIELDS.map((f) => {
                const raw = (data as unknown as Record<string, unknown>)[f.key];
                if (raw == null && f.format !== "json") return null;

                let display: React.ReactNode;
                if (f.format === "num") {
                  display = fmtNum(raw as number | null);
                } else if (f.format === "json") {
                  const text = fmtJson(raw as Record<string, unknown> | null);
                  if (text === "-") return null;
                  display = (
                    <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                      {text}
                    </pre>
                  );
                } else if (f.format === "pre") {
                  display = (
                    <pre className="text-xs bg-gray-50 border border-gray-200 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                      {String(raw ?? "-")}
                    </pre>
                  );
                } else if (typeof raw === "boolean") {
                  display = raw ? "Yes" : "No";
                } else {
                  display = String(raw ?? "-");
                }

                return (
                  <div key={f.key}>
                    <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                      {f.label}
                    </dt>
                    <dd className="mt-0.5 text-sm text-gray-800">{display}</dd>
                  </div>
                );
              })}
            </dl>
          )}
        </div>
      </div>
    </>
  );
}
