import type {
  PaginatedResponse,
  Transaction,
  TransactionDetail,
  ReviewRow,
  Subdivision,
  SubdivisionDetail,
  Stats,
  ETLState,
  TransactionFilters,
  CommissionRosterDetail,
  PermitsResponse,
  ParcelPage,
  InventorySubdivisionOut,
  InventoryCounty,
  CountyInventory,
  CountyDetail,
  BuilderOut,
  SnapshotOut,
  PermitDashboard,
  PermitListPayload,
  ScrapeJob,
  CommissionSummary,
  CommissionActionsPayload,
  RosterPayload,
  SubdivisionGeoFeature,
  GeometryCoverageRow,
} from "./types";

const BASE = "/api";

function qs(params: Record<string, string | number | boolean | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== "" && v !== false
  );
  if (!entries.length) return "";
  return "?" + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

async function checked<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(body || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getCounties(): Promise<string[]> {
  return checked(await fetch(`${BASE}/counties`));
}

export async function getSubdivisions(county?: string): Promise<Subdivision[]> {
  return checked(await fetch(`${BASE}/subdivisions${qs({ county })}`));
}

export async function getSubdivision(id: number): Promise<SubdivisionDetail> {
  return checked(await fetch(`${BASE}/subdivisions/${id}`));
}

export async function resolveAction(
  transactionId: number,
  body: Record<string, unknown>
): Promise<{ id: number; resolved: boolean }> {
  return checked(
    await fetch(`${BASE}/transactions/${transactionId}/resolve-action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  );
}

export async function getStats(): Promise<Stats> {
  return checked(await fetch(`${BASE}/stats`));
}

export async function getTransaction(id: number): Promise<TransactionDetail> {
  return checked(await fetch(`${BASE}/transactions/${id}`));
}

export async function resolveTransaction(id: number, note?: string): Promise<{ id: number; resolved: boolean }> {
  return checked(
    await fetch(`${BASE}/transactions/${id}/resolve`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ note: note || "" }),
    })
  );
}

export async function getTransactions(
  filters: TransactionFilters
): Promise<PaginatedResponse<Transaction>> {
  return checked(
    await fetch(
      `${BASE}/transactions${qs({
        county: filters.county,
        subdivision: filters.subdivision,
        date_from: filters.date_from,
        date_to: filters.date_to,
        inventory_category: filters.inventory_category,
        unmatched_only: filters.unmatched_only,
        search: filters.search,
        page: filters.page,
        page_size: filters.page_size,
        sort_by: filters.sort_by,
        sort_dir: filters.sort_dir,
      })}`
    )
  );
}

export async function getReviewQueue(params: {
  county?: string;
  reason?: string;
  page: number;
  page_size: number;
}): Promise<PaginatedResponse<ReviewRow>> {
  return checked(await fetch(`${BASE}/review-queue${qs(params)}`));
}

export async function startETL(counties?: string[]): Promise<void> {
  const res = await fetch(`${BASE}/etl/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(counties?.length ? { counties } : {}),
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(body || `HTTP ${res.status}`);
  }
}

export async function getETLStatus(): Promise<ETLState> {
  return checked(await fetch(`${BASE}/etl/status`));
}

export async function exportTransactions(params: Record<string, unknown>): Promise<{ filename: string; records: number }> {
  return checked(
    await fetch(`${BASE}/export/transactions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  );
}

export async function exportReviewQueue(params: Record<string, unknown>): Promise<{ filename: string; records: number }> {
  return checked(
    await fetch(`${BASE}/export/review-queue`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  );
}

export function downloadUrl(filename: string): string {
  return `${BASE}/export/download/${filename}`;
}

export async function getCommissionRoster(subdivisionId: number): Promise<CommissionRosterDetail> {
  const res = await fetch(`${BASE}/commission/roster/${subdivisionId}`);
  if (res.status === 404) {
    return {
      id: subdivisionId,
      name: "",
      jurisdiction_name: "",
      county: "",
      entitlement_status: "",
      lifecycle_stage: "",
      lifecycle_stage_label: "",
      last_action_date: "",
      next_expected_action: "",
      actions: [],
    };
  }
  return checked(res);
}

export async function getPermitsBySubdivision(subdivisionId: number): Promise<PermitsResponse> {
  return checked(
    await fetch(`${BASE}/permits/permits${qs({ subdivision_id: subdivisionId, page_size: 25, sort: "issue_date_desc" })}`)
  );
}

export async function getParcelsBySubdivision(subdivisionId: number): Promise<ParcelPage> {
  return checked(
    await fetch(`${BASE}/inventory/parcels${qs({ subdivision_id: subdivisionId, page_size: 2000, sort: "last_changed", order: "desc" })}`)
  );
}

export async function getSalesBySubdivision(
  canonicalName: string
): Promise<PaginatedResponse<Transaction>> {
  return checked(
    await fetch(`${BASE}/transactions${qs({ subdivision: canonicalName, page_size: 25, sort_by: "date", sort_dir: "desc" })}`)
  );
}

export async function searchInventorySubdivisions(
  params: { search?: string; county_id?: number }
): Promise<InventorySubdivisionOut[]> {
  return checked(await fetch(`${BASE}/inventory/subdivisions${qs(params)}`));
}

export async function getSubdivisionGeoJSON(
  params: { county_id?: number; builder_id?: number }
): Promise<SubdivisionGeoFeature[]> {
  return checked(await fetch(`${BASE}/inventory/subdivisions/geojson${qs(params)}`));
}

// ---------------------------------------------------------------------------
// Builder Inventory module
// ---------------------------------------------------------------------------

export async function getInventoryCounties(): Promise<InventoryCounty[]> {
  return checked(await fetch(`${BASE}/inventory/counties`));
}

export async function getInventorySummary(
  params?: { parcel_class?: string; entity_type?: string[] }
): Promise<CountyInventory[]> {
  const search = new URLSearchParams();
  if (params?.parcel_class) search.append("parcel_class", params.parcel_class);
  if (params?.entity_type) {
    for (const t of params.entity_type) search.append("entity_type", t);
  }
  const q = search.toString();
  const base = `${BASE}/inventory/inventory`;
  return checked(await fetch(q ? `${base}?${q}` : base));
}

export async function getInventoryCountyDetail(
  countyId: number,
  params?: { parcel_class?: string; entity_type?: string[]; builder_id?: number }
): Promise<CountyDetail> {
  const search = new URLSearchParams();
  if (params?.parcel_class) search.append("parcel_class", params.parcel_class);
  if (params?.entity_type) {
    for (const t of params.entity_type) search.append("entity_type", t);
  }
  if (params?.builder_id != null) search.append("builder_id", String(params.builder_id));
  const q = search.toString();
  const base = `${BASE}/inventory/inventory/${countyId}`;
  return checked(await fetch(q ? `${base}?${q}` : base));
}

export async function getInventoryTrends(
  countyId?: number,
  days = 90
): Promise<import("./types").TrendPoint[]> {
  const params: Record<string, string | number> = { days };
  if (countyId != null) params.county_id = countyId;
  return checked(await fetch(`${BASE}/inventory/inventory/trends${qs(params)}`));
}

export async function getInventoryBuilders(): Promise<BuilderOut[]> {
  return checked(await fetch(`${BASE}/inventory/builders`));
}

export async function getInventorySnapshots(params?: {
  county_id?: number;
  limit?: number;
}): Promise<SnapshotOut[]> {
  return checked(await fetch(`${BASE}/inventory/snapshots${qs(params ?? {})}`));
}

export async function getActiveSnapshots(): Promise<SnapshotOut[]> {
  return checked(await fetch(`${BASE}/inventory/snapshots/active`));
}

export async function triggerSnapshot(county_id?: number): Promise<{ message: string }> {
  return checked(
    await fetch(`${BASE}/inventory/snapshots/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(county_id ? { county_id } : {}),
    })
  );
}

// ---------------------------------------------------------------------------
// Permit Tracker module
// ---------------------------------------------------------------------------

export async function getPermitDashboard(): Promise<PermitDashboard> {
  return checked(await fetch(`${BASE}/permits/dashboard`));
}

export async function getPermitList(params?: {
  page?: string;
  page_size?: string;
  sort?: string;
  jurisdiction_id?: number;
  status?: string;
}): Promise<PermitListPayload> {
  return checked(await fetch(`${BASE}/permits/permits${qs(params ?? {})}`));
}

export async function getPermitScrapeJobs(params?: {
  limit?: number;
  status?: string;
}): Promise<{ jobs: ScrapeJob[]; active_count: number }> {
  return checked(await fetch(`${BASE}/permits/scrape/jobs${qs(params ?? {})}`));
}

export async function triggerPermitScrape(params?: {
  jurisdiction?: string;
}): Promise<{ message: string }> {
  return checked(
    await fetch(`${BASE}/permits/scrape/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params ?? {}),
    })
  );
}

// ---------------------------------------------------------------------------
// Commission Radar module
// ---------------------------------------------------------------------------

export async function getCommissionSummary(): Promise<CommissionSummary> {
  return checked(await fetch(`${BASE}/commission/dashboard/summary`));
}

export async function getCommissionActions(params?: {
  page?: number;
  per_page?: number;
  jurisdiction?: string;
  approval_type?: string;
  outcome?: string;
  needs_review?: string;
  date_from?: string;
  date_to?: string;
}): Promise<CommissionActionsPayload> {
  return checked(await fetch(`${BASE}/commission/dashboard/actions${qs(params ?? {})}`));
}

export async function getCommissionRosterList(params?: {
  page?: number;
  per_page?: number;
  county?: string;
  search?: string;
  sort?: string;
}): Promise<RosterPayload> {
  return checked(await fetch(`${BASE}/commission/roster${qs(params ?? {})}`));
}

// ---------------------------------------------------------------------------
// Platform Health
// ---------------------------------------------------------------------------

export async function getGeometryCoverage(): Promise<{ rows: GeometryCoverageRow[] }> {
  return checked(await fetch(`${BASE}/platform/geometry-coverage`));
}
