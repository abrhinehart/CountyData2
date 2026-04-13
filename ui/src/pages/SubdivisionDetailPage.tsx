import { useQuery } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import {
  getSubdivision,
  getCommissionRoster,
  getPermitsBySubdivision,
  getParcelsBySubdivision,
  getSalesBySubdivision,
} from "../api";
import SubdivisionMap from "../components/SubdivisionMap";
import EntitlementProgress from "../components/EntitlementProgress";
import type {
  CommissionRosterDetail,
  PermitsResponse,
  ParcelPage,
  PaginatedResponse,
  Transaction,
  SubdivisionDetail,
} from "../types";

function fmtNum(n: number | null | undefined): string {
  if (n == null) return "";
  return n.toLocaleString(undefined, { maximumFractionDigits: 0 });
}

function fmtDollar(n: number | null | undefined): string {
  if (n == null) return "";
  return `$${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export default function SubdivisionDetailPage() {
  const { id: idParam } = useParams<{ id: string }>();
  const id = Number(idParam);
  const navigate = useNavigate();
  const valid = !!idParam && !Number.isNaN(id);

  const subdivisionQ = useQuery<SubdivisionDetail>({
    queryKey: ["subdivision", id],
    queryFn: () => getSubdivision(id),
    enabled: valid,
  });

  const commissionQ = useQuery<CommissionRosterDetail>({
    queryKey: ["commission-roster", id],
    queryFn: () => getCommissionRoster(id),
    enabled: valid,
  });

  const permitsQ = useQuery<PermitsResponse>({
    queryKey: ["permits-by-sub", id],
    queryFn: () => getPermitsBySubdivision(id),
    enabled: valid,
  });

  const parcelsQ = useQuery<ParcelPage>({
    queryKey: ["parcels-by-sub", id],
    queryFn: () => getParcelsBySubdivision(id),
    enabled: valid,
  });

  const canonicalName = subdivisionQ.data?.canonical_name;
  const salesQ = useQuery<PaginatedResponse<Transaction>>({
    queryKey: ["sales-by-sub", canonicalName],
    queryFn: () => getSalesBySubdivision(canonicalName as string),
    enabled: valid && !!canonicalName,
  });

  if (!valid) {
    return <p className="text-red-600">Invalid subdivision id</p>;
  }

  const header = subdivisionQ.data;
  const commission = commissionQ.data;
  const hasCommissionMeta =
    commission && (commission.entitlement_status || commission.lifecycle_stage_label);

  // Derive builder totals from parcels — group by canonical builder name (entity)
  const parcels = parcelsQ.data?.items ?? [];
  const builderTotals = new Map<string, number>();
  for (const p of parcels) {
    const builder = p.entity ?? p.owner_name ?? "Unknown";
    builderTotals.set(builder, (builderTotals.get(builder) ?? 0) + 1);
  }
  const sortedBuilders = [...builderTotals.entries()].sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Back button + Header */}
      <div>
        <button
          onClick={() => navigate("/subdivisions")}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2 inline-flex items-center gap-1"
        >
          <span>&larr;</span> Back to Subdivisions
        </button>
        {subdivisionQ.isLoading ? (
          <p className="text-gray-400">Loading subdivision...</p>
        ) : subdivisionQ.error || !header ? (
          <p className="text-red-600 text-sm">
            Failed to load subdivision: {(subdivisionQ.error as Error | null)?.message ?? "not found"}
          </p>
        ) : (
          <>
            <h1 className="text-2xl font-semibold text-gray-800">{header.canonical_name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-sm text-gray-500">{header.county}, FL</span>
              {hasCommissionMeta && (
                <>
                  {commission?.entitlement_status && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {commission.entitlement_status}
                    </span>
                  )}
                  {commission?.lifecycle_stage_label && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                      {commission.lifecycle_stage_label}
                    </span>
                  )}
                </>
              )}
            </div>
          </>
        )}
      </div>

      {/* Info + Map layout (1:2) — map placeholder for now */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Subdivision info (1/3) */}
        <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">Details</h2>
          <dl className="space-y-2 text-sm">
            {header?.county && (
              <div><dt className="text-gray-400">County</dt><dd className="text-gray-800 font-medium">{header.county}, FL</dd></div>
            )}
            {header?.phases && header.phases.length > 0 && (
              <div><dt className="text-gray-400">Phases</dt><dd className="text-gray-800">{header.phases.join(", ")}</dd></div>
            )}
            {commission?.last_action_date && (
              <div><dt className="text-gray-400">Last Commission Action</dt><dd className="text-gray-800">{commission.last_action_date}</dd></div>
            )}
            {commission?.next_expected_action && (
              <div><dt className="text-gray-400">Next Expected</dt><dd className="text-gray-800">{commission.next_expected_action}</dd></div>
            )}
            <div><dt className="text-gray-400">Total Parcels</dt><dd className="text-gray-800 font-medium">{fmtNum(parcelsQ.data?.total)}</dd></div>
            <div><dt className="text-gray-400">Total Permits</dt><dd className="text-gray-800 font-medium">{fmtNum(permitsQ.data?.total_count)}</dd></div>
            <div><dt className="text-gray-400">Total Sales</dt><dd className="text-gray-800 font-medium">{fmtNum(salesQ.data?.total)}</dd></div>
          </dl>
        </div>

        {/* Map (2/3) */}
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg overflow-hidden min-h-[300px]">
          <SubdivisionMap geojson={header?.geojson ?? null} />
        </div>
      </div>

      {/* Builder totals (instead of individual lot listing) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Builder inventory */}
        <PanelShell title="Builder Lots" subtitle={`${fmtNum(parcelsQ.data?.total)} total parcels`}>
          {parcelsQ.isLoading ? (
            <p className="text-gray-400 text-sm">Loading...</p>
          ) : parcelsQ.error ? (
            <p className="text-red-600 text-sm">Failed to load</p>
          ) : sortedBuilders.length === 0 ? (
            <p className="text-gray-400 text-sm">No parcels tracked.</p>
          ) : (
            <div className="space-y-1.5">
              {sortedBuilders.slice(0, 10).map(([name, count]) => (
                <div key={name} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 truncate max-w-[200px]" title={name}>{name}</span>
                  <span className="text-gray-500 tabular-nums shrink-0 ml-2">{fmtNum(count)}</span>
                </div>
              ))}
              {sortedBuilders.length > 10 && (
                <p className="text-xs text-gray-400">+{sortedBuilders.length - 10} more owners</p>
              )}
            </div>
          )}
        </PanelShell>

        {/* Commission actions */}
        <CommissionPanel
          isLoading={commissionQ.isLoading}
          error={commissionQ.error as Error | null}
          data={commissionQ.data}
        />

        {/* Permits */}
        <PermitsPanel
          isLoading={permitsQ.isLoading}
          error={permitsQ.error as Error | null}
          data={permitsQ.data}
        />

        {/* Sales */}
        <SalesPanel
          isLoading={salesQ.isLoading || (!canonicalName && !subdivisionQ.error)}
          error={salesQ.error as Error | null}
          data={salesQ.data}
        />
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Panel components
// ---------------------------------------------------------------------------

function PanelShell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5">
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">{title}</h2>
        {subtitle && <div className="text-xs text-gray-400 mt-0.5">{subtitle}</div>}
      </div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}

function CommissionPanel({
  isLoading,
  error,
  data,
}: {
  isLoading: boolean;
  error: Error | null;
  data: CommissionRosterDetail | undefined;
}) {
  const actions = data?.actions ?? [];
  const subtitle = data
    ? `${data.entitlement_status || "—"} · ${actions.length} actions`
    : undefined;

  return (
    <PanelShell title="Commission" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load: {error.message}</p>
      ) : actions.length === 0 ? (
        <p className="text-gray-400 text-sm">No commission actions.</p>
      ) : (
        <div className="space-y-3">
          <EntitlementProgress actions={actions} />
          <div className="space-y-1.5">
          {actions.slice(0, 8).map((a) => (
            <div key={a.id} className="text-sm">
              <div className="flex items-center gap-2">
                <span className="text-gray-500 text-xs shrink-0">{a.meeting_date}</span>
                <span className="text-gray-700 truncate">{a.approval_type.replace(/_/g, " ")}</span>
              </div>
              {a.outcome && (
                <span className={`text-xs font-medium ${a.outcome === "approved" ? "text-green-600" : a.outcome === "denied" ? "text-red-600" : "text-gray-500"}`}>
                  {a.outcome}
                </span>
              )}
            </div>
          ))}
          {actions.length > 8 && (
            <p className="text-xs text-gray-400">+{actions.length - 8} more actions</p>
          )}
          </div>
        </div>
      )}
    </PanelShell>
  );
}

function PermitsPanel({
  isLoading,
  error,
  data,
}: {
  isLoading: boolean;
  error: Error | null;
  data: PermitsResponse | undefined;
}) {
  const rows = data?.permits ?? [];
  const subtitle = data ? `${data.total_count} total` : undefined;

  return (
    <PanelShell title="Permits" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-400 text-sm">No permits.</p>
      ) : (
        <div className="space-y-1.5">
          {rows.slice(0, 8).map((p) => (
            <div key={p.id} className="flex items-center gap-2 text-sm">
              <span className="text-gray-500 text-xs shrink-0">{p.issue_date ?? ""}</span>
              <span className="text-gray-700 truncate">{p.address ?? p.permit_number}</span>
              {p.builder && <span className="text-gray-400 text-xs shrink-0">{p.builder}</span>}
            </div>
          ))}
          {rows.length > 8 && (
            <p className="text-xs text-gray-400">+{data!.total_count - 8} more permits</p>
          )}
        </div>
      )}
    </PanelShell>
  );
}

function SalesPanel({
  isLoading,
  error,
  data,
}: {
  isLoading: boolean;
  error: Error | null;
  data: PaginatedResponse<Transaction> | undefined;
}) {
  const rows = data?.items ?? [];
  const subtitle = data ? `${data.total} total` : undefined;

  return (
    <PanelShell title="Sales" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-400 text-sm">No transactions.</p>
      ) : (
        <div className="space-y-1.5">
          {rows.slice(0, 8).map((t, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className="text-gray-500 text-xs shrink-0">{t.Date ?? ""}</span>
              <span className="text-gray-700 truncate">{t.Grantor}</span>
              {t.Price != null && (
                <span className="text-gray-500 tabular-nums text-xs shrink-0 ml-auto">
                  {fmtDollar(t.Price)}
                </span>
              )}
            </div>
          ))}
          {rows.length > 8 && (
            <p className="text-xs text-gray-400">+{data!.total - 8} more sales</p>
          )}
        </div>
      )}
    </PanelShell>
  );
}
