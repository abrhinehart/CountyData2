export interface Transaction {
  Grantor: string;
  Grantee: string | null;
  Type: string | null;
  Instrument: string | null;
  Date: string | null;
  "Export Legal Description": string | null;
  Subdivision: string | null;
  Phase: string | null;
  "Inventory Category": string | null;
  Lots: number | null;
  Price: number | null;
  "$ / Lot": number | null;
  Acres: number | null;
  "$ / Acre": number | null;
  County: string;
  Notes: string | null;
  [key: string]: unknown;
}

export interface TransactionDetail {
  id: number;
  grantor: string;
  grantee: string | null;
  type: string | null;
  instrument: string | null;
  date: string | null;
  export_legal_desc: string | null;
  export_legal_raw: string | null;
  deed_legal_desc: string | null;
  deed_legal_parsed: Record<string, unknown> | null;
  deed_locator: Record<string, unknown> | null;
  subdivision: string | null;
  subdivision_id: number | null;
  phase: string | null;
  inventory_category: string | null;
  lots: number | null;
  price: number | null;
  price_per_lot: number | null;
  acres: number | null;
  acres_source: string | null;
  price_per_acre: number | null;
  parsed_data: Record<string, unknown> | null;
  county: string;
  notes: string | null;
  review_flag: boolean;
  source_file: string | null;
  inserted_at: string | null;
  updated_at: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Subdivision {
  id: number;
  canonical_name: string;
  county: string;
}

export interface CountyStat {
  county: string;
  count: number;
}

export interface TypeStat {
  type: string;
  count: number;
}

export interface Stats {
  total_transactions: number;
  flagged_for_review: number;
  date_range: { min: string | null; max: string | null };
  by_county: CountyStat[];
  by_type: TypeStat[];
}

export interface ETLState {
  status: "idle" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  counties: string[];
  results: Record<string, { files: number; inserted: number; updated: number; errors: number }>;
  error: string | null;
}

export interface ReviewRow {
  ID: number;
  County: string;
  Date: string | null;
  "Review Reasons": string;
  Grantor: string;
  Grantee: string | null;
  Type: string | null;
  Instrument: string | null;
  Price: number | null;
  Lots: number | null;
  "Inventory Category": string | null;
  Subdivision: string | null;
  "Subdivision ID": number | null;
  Phase: string | null;
  "Export Legal Description": string | null;
  [key: string]: unknown;
}

export interface TransactionFilters {
  county?: string;
  subdivision?: string;
  date_from?: string;
  date_to?: string;
  inventory_category?: string;
  unmatched_only?: boolean;
  search?: string;
  page: number;
  page_size: number;
  sort_by?: string;
  sort_dir?: string;
}
