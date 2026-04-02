import type {
  PaginatedResponse,
  Transaction,
  ReviewRow,
  Subdivision,
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

export async function getCounties(): Promise<string[]> {
  const res = await fetch(`${BASE}/counties`);
  return res.json();
}

export async function getSubdivisions(county?: string): Promise<Subdivision[]> {
  const res = await fetch(`${BASE}/subdivisions${qs({ county })}`);
  return res.json();
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${BASE}/stats`);
  return res.json();
}

export async function getTransactions(
  filters: TransactionFilters
): Promise<PaginatedResponse<Transaction>> {
  const res = await fetch(
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
  );
  return res.json();
}

export async function getReviewQueue(params: {
  county?: string;
  reason?: string;
  page: number;
  page_size: number;
}): Promise<PaginatedResponse<ReviewRow>> {
  const res = await fetch(`${BASE}/review-queue${qs(params)}`);
  return res.json();
}

export async function startETL(counties?: string[]): Promise<void> {
  await fetch(`${BASE}/etl/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(counties?.length ? { counties } : {}),
  });
}

export async function getETLStatus(): Promise<ETLState> {
  const res = await fetch(`${BASE}/etl/status`);
  return res.json();
}

export async function exportTransactions(params: Record<string, unknown>): Promise<{ filename: string; records: number }> {
  const res = await fetch(`${BASE}/export/transactions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return res.json();
}

export async function exportReviewQueue(params: Record<string, unknown>): Promise<{ filename: string; records: number }> {
  const res = await fetch(`${BASE}/export/review-queue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return res.json();
}

export function downloadUrl(filename: string): string {
  return `${BASE}/export/download/${filename}`;
}
