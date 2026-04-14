import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { getInventoryCounties, searchInventorySubdivisions } from "../api";
import type { InventorySubdivisionOut, InventoryCounty } from "../types";

type SortKey = "name" | "county" | "builders" | "lots" | "parcels" | "classification" | "activity";
type SortDir = "asc" | "desc";

const SORT_DEFAULTS: Record<SortKey, SortDir> = {
  name: "asc",
  county: "asc",
  builders: "desc",
  lots: "desc",
  parcels: "desc",
  classification: "asc",
  activity: "desc",
};

const SMALL_WORDS = new Set([
  "a", "an", "the", "and", "but", "or", "nor", "for", "yet", "so",
  "at", "by", "in", "of", "on", "to", "up", "as", "is", "it",
]);

const PHASE_RE = /\b(ph\.?|phase)\s*(\d+)/gi;

function toTitleCase(s: string): string {
  // Normalize phase abbreviations first (Ph 1, PH1, Ph.1 → Phase 1)
  let result = s.replace(PHASE_RE, (_, _prefix, num) => `Phase ${num}`);
  // Title-case each word, keeping small words lowercase (except first word)
  result = result.toLowerCase().replace(/\b\w+/g, (word, idx) =>
    idx === 0 || !SMALL_WORDS.has(word)
      ? word.charAt(0).toUpperCase() + word.slice(1)
      : word,
  );
  return result;
}

function relTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  const diff = Date.now() - d.getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function classificationLabel(c: string | null): { text: string; classes: string } {
  if (!c) return { text: "—", classes: "" };
  if (c === "active_development")
    return { text: "Active", classes: "bg-green-100 text-green-700" };
  if (c === "scattered")
    return { text: "Scattered", classes: "bg-gray-100 text-gray-600" };
  return { text: toTitleCase(c.replace(/_/g, " ")), classes: "bg-gray-100 text-gray-600" };
}

export default function SubdivisionsPage() {
  const navigate = useNavigate();
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [countyId, setCountyId] = useState<number | "all" | undefined>(undefined);
  const [sortBy, setSortBy] = useState<SortKey>("lots");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  function toggleSort(key: SortKey) {
    if (sortBy === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDir(SORT_DEFAULTS[key]);
    }
  }

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchInput.trim()), 250);
    return () => clearTimeout(t);
  }, [searchInput]);

  const countiesQ = useQuery<InventoryCounty[]>({
    queryKey: ["inventory-counties"],
    queryFn: getInventoryCounties,
  });

  const defaultCountyId = useMemo(() => {
    if (!countiesQ.data || countiesQ.data.length === 0) return null;
    const bay = countiesQ.data.find((c) => c.name === "Bay");
    return bay ? bay.id : countiesQ.data[0].id;
  }, [countiesQ.data]);

  const activeCountyId =
    countyId === undefined ? defaultCountyId : countyId === "all" ? null : countyId;

  const hasSearch = debouncedSearch.length >= 2;
  const hasCounty = activeCountyId !== null;
  const gated = hasSearch || hasCounty;

  const subsQ = useQuery<InventorySubdivisionOut[]>({
    queryKey: ["inventory-subdivisions", debouncedSearch, activeCountyId],
    queryFn: () =>
      searchInventorySubdivisions({
        search: hasSearch ? debouncedSearch : undefined,
        county_id: hasCounty ? activeCountyId : undefined,
      }),
    enabled: gated,
  });

  const rows = useMemo(() => {
    const data = subsQ.data ?? [];
    const dir = sortDir === "asc" ? 1 : -1;
    return [...data].sort((a, b) => {
      let cmp: number;
      switch (sortBy) {
        case "name":
          cmp = a.name.localeCompare(b.name);
          break;
        case "county":
          cmp = a.county_name.localeCompare(b.county_name) || a.name.localeCompare(b.name);
          break;
        case "builders":
          cmp = a.distinct_builder_count - b.distinct_builder_count || a.builder_lot_count - b.builder_lot_count;
          break;
        case "lots":
          cmp = a.builder_lot_count - b.builder_lot_count || a.name.localeCompare(b.name);
          break;
        case "parcels":
          cmp = a.parcel_count - b.parcel_count || a.name.localeCompare(b.name);
          break;
        case "classification":
          cmp = (a.classification ?? "").localeCompare(b.classification ?? "");
          break;
        case "activity":
          cmp = (a.updated_at ?? "").localeCompare(b.updated_at ?? "");
          break;
      }
      return cmp * dir;
    });
  }, [subsQ.data, sortBy, sortDir]);

  // Find the selected county object for display in the result badge
  const selectedCounty = countiesQ.data?.find((c) => c.id === activeCountyId);

  return (
    <div className="page-stack report-page max-w-6xl">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Subdivision Search</p>
          <h1 className="page-title">Subdivisions</h1>
          <p className="page-subtitle">
            Search for builder-active subdivisions, sort by lot footprint, and jump into the detail report.
          </p>
        </div>
      </div>

      <div className="filter-band">
        <div className="section-head">
          <div>
            <p className="section-title">Search Filters</p>
            <p className="section-caption">Search by name or narrow the inventory atlas to one county.</p>
          </div>
        </div>
        <div className="filter-grid">
          <div className="flex-1 min-w-[240px]">
            <label className="field-label mb-1 block">Search</label>
            <input
              type="text"
              placeholder="Subdivision name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="form-control"
            />
          </div>

          <div>
            <label className="field-label mb-1 block">County</label>
            <select
              value={activeCountyId ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                setCountyId(v ? Number(v) : "all");
              }}
              className="form-control min-w-[220px]"
            >
              <option value="">All Counties</option>
              {countiesQ.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}, {c.state}
                </option>
              ))}
            </select>
          </div>

          {gated && rows.length > 0 && (
            <span className="badge badge-accent">
              {rows.length} subdivision{rows.length !== 1 ? "s" : ""}
              {selectedCounty ? ` in ${selectedCounty.name}` : ""}
            </span>
          )}
        </div>
      </div>

      {/* Table container */}
      <div className="surface-card data-shell overflow-hidden">
        {!gated ? (
          <p className="table-empty">
            Type at least 2 characters or pick a county to search.
          </p>
        ) : subsQ.isLoading ? (
          <p className="table-empty">Loading...</p>
        ) : subsQ.error ? (
          <p className="table-empty text-[var(--danger)]">
            Failed to load: {(subsQ.error as Error).message}
          </p>
        ) : rows.length === 0 ? (
          <p className="table-empty">No subdivisions with builder activity found.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <SortTh label="Subdivision" sortKey="name" align="left" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="County" sortKey="county" align="left" className="w-32" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Parcels" sortKey="parcels" align="right" className="w-24" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builders" sortKey="builders" align="right" className="w-24" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builder Lots" sortKey="lots" align="right" className="w-28" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Classification" sortKey="classification" align="left" className="w-32" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Last Activity" sortKey="activity" align="right" className="w-28" active={sortBy} dir={sortDir} onSort={toggleSort} />
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const cls = classificationLabel(row.classification);
                return (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/subdivisions/${row.id}`)}
                    className="cursor-pointer"
                  >
                    <td>
                      <Link
                        to={`/subdivisions/${row.id}`}
                        className="font-semibold text-[var(--text)] hover:text-[var(--text)]"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {toTitleCase(row.name)}
                      </Link>
                    </td>
                    <td>{row.county_name}</td>
                    <td className="text-right tabular-nums">
                      {row.parcel_count.toLocaleString()}
                    </td>
                    <td className="text-right tabular-nums">
                      {row.distinct_builder_count}
                    </td>
                    <td className="text-right tabular-nums font-medium">
                      {row.builder_lot_count.toLocaleString()}
                    </td>
                    <td>
                      {cls.classes ? (
                        <span className={`badge ${cls.classes.includes("green") ? "badge-success" : "badge-neutral"}`}>
                          {cls.text}
                        </span>
                      ) : (
                        <span className="text-[var(--text-soft)]">{cls.text}</span>
                      )}
                    </td>
                    <td className="text-right text-xs text-[var(--text-muted)]">
                      {relTime(row.updated_at)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function SortTh({
  label,
  sortKey,
  align,
  className,
  active,
  dir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  align: "left" | "right";
  className?: string;
  active: SortKey;
  dir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  const isActive = active === sortKey;
  const arrow = isActive ? (dir === "asc" ? " \u25B2" : " \u25BC") : "";
  return (
    <th
      className={`cursor-pointer select-none transition-colors hover:text-[var(--text)] ${
        align === "right" ? "text-right" : "text-left"
      } ${isActive ? "text-[var(--text)]" : "text-[var(--text-muted)]"} ${className ?? ""}`}
      onClick={() => onSort(sortKey)}
    >
      {label}{arrow}
    </th>
  );
}
