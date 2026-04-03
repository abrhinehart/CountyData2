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
