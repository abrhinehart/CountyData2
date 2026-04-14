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
  const [countyId, setCountyId] = useState<number | null>(null);
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

  // Default to Bay (most data) or first county
  useEffect(() => {
    if (countyId === null && countiesQ.data && countiesQ.data.length > 0) {
      const bay = countiesQ.data.find((c) => c.name === "Bay");
      setCountyId(bay ? bay.id : countiesQ.data[0].id);
    }
  }, [countiesQ.data, countyId]);

  const hasSearch = debouncedSearch.length >= 2;
  const hasCounty = countyId !== null;
  const gated = hasSearch || hasCounty;

  const subsQ = useQuery<InventorySubdivisionOut[]>({
    queryKey: ["inventory-subdivisions", debouncedSearch, countyId],
    queryFn: () =>
      searchInventorySubdivisions({
        search: hasSearch ? debouncedSearch : undefined,
        county_id: hasCounty ? countyId : undefined,
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
  const selectedCounty = countiesQ.data?.find((c) => c.id === countyId);

  return (
    <div className="space-y-4 max-w-6xl">
      <h1 className="text-2xl font-semibold text-gray-800">Subdivisions</h1>
      <p className="text-sm text-gray-500">
        Showing subdivisions where builders own or have recently owned lots.
      </p>

      {/* Filter card */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[240px]">
            <label className="block text-xs text-gray-500 mb-1">Search</label>
            <input
              type="text"
              placeholder="Subdivision name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300 focus:border-violet-400 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">County</label>
            <select
              value={countyId ?? ""}
              onChange={(e) => {
                const v = e.target.value;
                setCountyId(v ? Number(v) : null);
              }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white min-w-[180px] focus:outline-none focus:ring-2 focus:ring-violet-300 focus:border-violet-400 transition-colors"
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
            <span className="inline-flex items-center rounded-full bg-violet-100 text-violet-700 px-2.5 py-1 text-xs font-medium">
              {rows.length} subdivision{rows.length !== 1 ? "s" : ""}
              {selectedCounty ? ` in ${selectedCounty.name}` : ""}
            </span>
          )}
        </div>
      </div>

      {/* Table container */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        {!gated ? (
          <p className="text-sm text-gray-400 p-5">
            Type at least 2 characters or pick a county to search.
          </p>
        ) : subsQ.isLoading ? (
          <p className="text-sm text-gray-400 p-5">Loading...</p>
        ) : subsQ.error ? (
          <p className="text-sm text-red-600 p-5">
            Failed to load: {(subsQ.error as Error).message}
          </p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-gray-400 p-5">No subdivisions with builder activity found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide">
                <SortTh label="Subdivision" sortKey="name" align="left" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="County" sortKey="county" align="left" className="w-32" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Parcels" sortKey="parcels" align="right" className="w-24" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builders" sortKey="builders" align="right" className="w-24" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builder Lots" sortKey="lots" align="right" className="w-28" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Classification" sortKey="classification" align="left" className="w-32" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Last Activity" sortKey="activity" align="right" className="w-28" active={sortBy} dir={sortDir} onSort={toggleSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row) => {
                const cls = classificationLabel(row.classification);
                return (
                  <tr
                    key={row.id}
                    onClick={() => navigate(`/subdivisions/${row.id}`)}
                    className="cursor-pointer hover:bg-violet-50/60 transition-colors"
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/subdivisions/${row.id}`}
                        className="font-semibold text-gray-900 hover:text-gray-900"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {toTitleCase(row.name)}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{row.county_name}</td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-700">
                      {row.parcel_count.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums text-gray-700">
                      {row.distinct_builder_count}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums font-medium text-gray-800">
                      {row.builder_lot_count.toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      {cls.classes ? (
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${cls.classes}`}>
                          {cls.text}
                        </span>
                      ) : (
                        <span className="text-gray-400">{cls.text}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500 text-xs">
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
      className={`px-4 py-3 cursor-pointer select-none hover:text-gray-800 transition-colors ${
        align === "right" ? "text-right" : "text-left"
      } ${isActive ? "text-gray-800" : "text-gray-500"} ${className ?? ""}`}
      onClick={() => onSort(sortKey)}
    >
      {label}{arrow}
    </th>
  );
}
