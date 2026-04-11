import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import {
  getSubdivision,
  getCommissionRoster,
  getPermitsBySubdivision,
  getParcelsBySubdivision,
  getSalesBySubdivision,
} from "../api";
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

export default function SubdivisionDetailPage() {
  const { id: idParam } = useParams<{ id: string }>();
  const id = Number(idParam);

  if (!idParam || Number.isNaN(id)) {
    return <p className="text-red-600">Invalid subdivision id</p>;
  }

  const subdivisionQ = useQuery<SubdivisionDetail>({
    queryKey: ["subdivision", id],
    queryFn: () => getSubdivision(id),
  });

  const commissionQ = useQuery<CommissionRosterDetail>({
    queryKey: ["commission-roster", id],
    queryFn: () => getCommissionRoster(id),
  });

  const permitsQ = useQuery<PermitsResponse>({
    queryKey: ["permits-by-sub", id],
    queryFn: () => getPermitsBySubdivision(id),
  });

  const parcelsQ = useQuery<ParcelPage>({
    queryKey: ["parcels-by-sub", id],
    queryFn: () => getParcelsBySubdivision(id),
  });

  const canonicalName = subdivisionQ.data?.canonical_name;
  const salesQ = useQuery<PaginatedResponse<Transaction>>({
    queryKey: ["sales-by-sub", canonicalName],
    queryFn: () => getSalesBySubdivision(canonicalName as string),
    enabled: !!canonicalName,
  });

  // Header
  const header = subdivisionQ.data;
  const commission = commissionQ.data;
  const hasCommissionMeta =
    commission && (commission.entitlement_status || commission.lifecycle_stage_label);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
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
              <span className="text-sm text-gray-500">{header.county}</span>
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

      {/* Four panels */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <CommissionPanel
          isLoading={commissionQ.isLoading}
          error={commissionQ.error as Error | null}
          data={commissionQ.data}
        />
        <PermitsPanel
          isLoading={permitsQ.isLoading}
          error={permitsQ.error as Error | null}
          data={permitsQ.data}
        />
        <InventoryPanel
          isLoading={parcelsQ.isLoading}
          error={parcelsQ.error as Error | null}
          data={parcelsQ.data}
        />
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
// Panel components (inline — do not factor out per plan)
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
    ? `${data.entitlement_status || "—"} · ${data.lifecycle_stage_label || "—"} · ${actions.length} actions`
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
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Date</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Type</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Case</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Outcome</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Phase</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((a) => (
              <tr key={a.id} className="border-b border-gray-100">
                <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{a.meeting_date}</td>
                <td className="px-3 py-1.5 text-gray-700">{a.approval_type}</td>
                <td className="px-3 py-1.5 text-gray-700">{a.case_number}</td>
                <td className="px-3 py-1.5 text-gray-700">{a.outcome}</td>
                <td className="px-3 py-1.5 text-gray-700">{a.phase_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
  const subtitle = data ? `showing ${rows.length} of ${data.total_count}` : undefined;

  return (
    <PanelShell title="Permits" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load: {error.message}</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-400 text-sm">No permits.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Issued</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Permit #</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Status</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Address</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Builder</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-b border-gray-100">
                <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{p.issue_date ?? ""}</td>
                <td className="px-3 py-1.5 text-gray-700">{p.permit_number}</td>
                <td className="px-3 py-1.5 text-gray-700">{p.status ?? ""}</td>
                <td className="px-3 py-1.5 text-gray-700 max-w-[220px] truncate" title={p.address ?? ""}>
                  {p.address ?? ""}
                </td>
                <td className="px-3 py-1.5 text-gray-700">{p.builder ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PanelShell>
  );
}

function InventoryPanel({
  isLoading,
  error,
  data,
}: {
  isLoading: boolean;
  error: Error | null;
  data: ParcelPage | undefined;
}) {
  const rows = data?.items ?? [];
  const subtitle = data ? `showing ${rows.length} of ${data.total}` : undefined;

  return (
    <PanelShell title="Builder Inventory" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load: {error.message}</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-400 text-sm">No parcels.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Parcel #</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Owner</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Address</th>
              <th className="px-3 py-1.5 text-right font-medium text-gray-600">Acres</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Class</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-gray-100">
                <td className="px-3 py-1.5 text-gray-700">{r.parcel_number}</td>
                <td className="px-3 py-1.5 text-gray-700 max-w-[180px] truncate" title={r.owner_name ?? ""}>
                  {r.owner_name ?? ""}
                </td>
                <td className="px-3 py-1.5 text-gray-700 max-w-[220px] truncate" title={r.site_address ?? ""}>
                  {r.site_address ?? ""}
                </td>
                <td className="px-3 py-1.5 text-gray-700 text-right tabular-nums">
                  {r.acreage != null ? r.acreage.toFixed(2) : ""}
                </td>
                <td className="px-3 py-1.5 text-gray-700">{r.parcel_class ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
  const subtitle = data ? `showing ${rows.length} of ${data.total}` : undefined;

  return (
    <PanelShell title="Sales" subtitle={subtitle}>
      {isLoading ? (
        <p className="text-gray-400 text-sm">Loading...</p>
      ) : error ? (
        <p className="text-red-600 text-sm">Failed to load: {error.message}</p>
      ) : rows.length === 0 ? (
        <p className="text-gray-400 text-sm">No transactions.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Date</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Type</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Grantor</th>
              <th className="px-3 py-1.5 text-left font-medium text-gray-600">Grantee</th>
              <th className="px-3 py-1.5 text-right font-medium text-gray-600">Price</th>
              <th className="px-3 py-1.5 text-right font-medium text-gray-600">Lots</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t, i) => (
              <tr key={i} className="border-b border-gray-100">
                <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{t.Date ?? ""}</td>
                <td className="px-3 py-1.5 text-gray-700">{t.Type ?? ""}</td>
                <td className="px-3 py-1.5 text-gray-700 max-w-[160px] truncate" title={t.Grantor}>
                  {t.Grantor}
                </td>
                <td className="px-3 py-1.5 text-gray-700 max-w-[160px] truncate" title={t.Grantee ?? ""}>
                  {t.Grantee ?? ""}
                </td>
                <td className="px-3 py-1.5 text-gray-700 text-right tabular-nums">
                  {fmtNum(t.Price)}
                </td>
                <td className="px-3 py-1.5 text-gray-700 text-right tabular-nums">
                  {fmtNum(t.Lots)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </PanelShell>
  );
}
