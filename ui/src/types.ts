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
  phases: string[];
}

export interface SubdivisionDetail {
  id: number;
  canonical_name: string;
  county: string;
  phases: string[];
  geojson: GeoJSON.Geometry | null;
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

export interface CommissionAction {
  id: number;
  approval_type: string;
  case_number: string;
  ordinance_number: string;
  outcome: string;
  meeting_date: string;
  reading_number: string;
  phase_name: string;
  acreage: number | null;
  lot_count: number | null;
}

export interface CommissionRosterDetail {
  id: number;
  name: string;
  jurisdiction_name: string;
  county: string;
  entitlement_status: string;
  lifecycle_stage: string;
  lifecycle_stage_label: string;
  last_action_date: string;
  next_expected_action: string;
  actions: CommissionAction[];
}

export interface PermitRow {
  id: number;
  permit_number: string;
  address: string | null;
  issue_date: string | null;
  status: string | null;
  permit_type: string | null;
  valuation: number | null;
  jurisdiction: string | null;
  subdivision: string | null;
  builder: string | null;
}

export interface PermitsResponse {
  permits: PermitRow[];
  count: number;
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ParcelRow {
  id: number;
  parcel_number: string;
  county: string | null;
  entity: string | null;
  subdivision: string | null;
  owner_name: string | null;
  site_address: string | null;
  use_type: string | null;
  acreage: number | null;
  appraised_value: number | null;
  parcel_class: string | null;
}

export interface ParcelPage {
  items: ParcelRow[];
  total: number;
  page: number;
  page_size: number;
}

export interface InventorySubdivisionOut {
  id: number;
  name: string;
  county_id: number;
  county_name: string;
  has_geometry: boolean;
  parcel_count: number;
  builder_lot_count: number;
  distinct_builder_count: number;
}

export interface SubdivisionBuilderSummary {
  builder_id: number;
  builder_name: string;
  lot_count: number;
}

export interface SubdivisionGeoFeature {
  id: number;
  name: string;
  county_id: number;
  county_name: string;
  builder_lot_count: number;
  distinct_builder_count: number;
  builders: SubdivisionBuilderSummary[];
  geojson: GeoJSON.Geometry;
}

// ---------------------------------------------------------------------------
// Builder Inventory module
// ---------------------------------------------------------------------------

export interface InventoryCounty {
  id: number;
  name: string;
  state: string;
  is_active: boolean;
  has_endpoint: boolean;
  last_snapshot_at: string | null;
  last_snapshot_parcels: number | null;
}

export interface BuilderCount {
  builder_id: number;
  builder_name: string;
  count: number;
  acreage: number;
}

export interface CountyInventory {
  county_id: number;
  county: string;
  total: number;
  builders: BuilderCount[];
}

export interface SubdivisionInventory {
  subdivision_id: number | null;
  subdivision: string;
  total: number;
  builders: BuilderCount[];
}

export interface CountyDetail {
  county_id: number;
  county: string;
  total: number;
  subdivisions: SubdivisionInventory[];
}

export interface BuilderOut {
  id: number;
  canonical_name: string;
  type: string;
  is_active: boolean;
  scope: string;
  aliases: { id: number; alias: string }[];
  counties: { id: number; county_id: number }[];
}

export interface SnapshotOut {
  id: number;
  county_id: number;
  started_at: string;
  completed_at: string | null;
  status: string;
  total_parcels_queried: number;
  new_count: number;
  removed_count: number;
  changed_count: number;
  unchanged_count: number;
  error_message: string | null;
  summary_text: string | null;
  progress_current: number;
  progress_total: number;
}

// ---------------------------------------------------------------------------
// Permit Tracker module
// ---------------------------------------------------------------------------

export interface PermitDashboard {
  summary: {
    current_month: number;
    last_month: number;
    month_delta: number;
    total_permits: number;
    watchlist_count: number;
  };
  trend: { label: string; count: number }[];
  top_subdivisions: { name: string; total: number }[];
  top_builders: { name: string; total: number }[];
  last_runs: {
    name: string;
    portal_type: string | null;
    last_success: string | null;
    last_attempt: string | null;
    freshness: string;
  }[];
}

export interface PermitListItem {
  id: number;
  permit_number: string;
  address: string | null;
  issue_date: string | null;
  status: string | null;
  permit_type: string | null;
  valuation: number | null;
  jurisdiction: string | null;
  subdivision: string | null;
  builder: string | null;
}

export interface PermitListPayload {
  permits: PermitListItem[];
  count: number;
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ScrapeJob {
  id: number;
  jurisdiction: string;
  status: string;
  trigger_type: string;
  queued_at: string;
  started_at: string | null;
  finished_at: string | null;
  last_error: string | null;
  attempt_count: number;
  can_retry: boolean;
  summary: { permits_found?: number; [key: string]: unknown } | null;
}

// ---------------------------------------------------------------------------
// Commission Radar module
// ---------------------------------------------------------------------------

export interface CommissionSummary {
  documents_processed: number;
  projects_tracked: number;
  actions_extracted: number;
  needs_review: number;
  jurisdictions_active: number;
}

export interface CommissionActionItem {
  id: number;
  jurisdiction_name: string;
  jurisdiction_slug: string;
  project_name: string;
  phase_name: string;
  approval_type: string;
  case_number: string;
  ordinance_number: string;
  ref_number: string;
  outcome: string;
  status: string;
  meeting_date: string;
  acreage: number | null;
  lot_count: number | null;
  action_summary: string;
  needs_review: boolean;
  document_type: string;
}

export interface CommissionActionsPayload {
  items: CommissionActionItem[];
  total: number;
  page: number;
  pages: number;
}

export interface RosterItem {
  id: number;
  name: string;
  county: string;
  jurisdiction_name: string;
  jurisdiction_slug: string;
  acreage: number | null;
  lot_count: number | null;
  entitlement_status: string;
  lifecycle_stage: string;
  lifecycle_stage_label: string;
  last_action_date: string;
  action_count: number;
  action_types: string[];
}

export interface RosterPayload {
  items: RosterItem[];
  total: number;
  page: number;
  pages: number;
}
