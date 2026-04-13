import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCounties, searchInventorySubdivisions } from "../api";
import type { InventorySubdivisionOut } from "../types";

type SortKey = "name" | "county" | "builders" | "lots";
type SortDir = "asc" | "desc";

const SORT_DEFAULTS: Record<SortKey, SortDir> = {
  name: "asc",
  county: "asc",
  builders: "desc",
  lots: "desc",
};

export default function SubdivisionsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [countyFilter, setCountyFilter] = useState<string>("Bay");
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

  const countiesQ = useQuery<string[]>({
    queryKey: ["counties"],
    queryFn: getCounties,
  });

  const hasSearch = debouncedSearch.length >= 2;
  const hasCounty = !!countyFilter;
  const gated = hasSearch || hasCounty;

  const subsQ = useQuery<InventorySubdivisionOut[]>({
    queryKey: ["inventory-subdivisions", debouncedSearch, countyFilter],
    queryFn: () =>
      searchInventorySubdivisions({
        search: hasSearch ? debouncedSearch : undefined,
      }),
    enabled: gated,
  });

  const rows = useMemo(() => {
    const filtered = (subsQ.data ?? []).filter((r) =>
      countyFilter ? r.county_name === countyFilter : true
    );
    const dir = sortDir === "asc" ? 1 : -1;
    return filtered.sort((a, b) => {
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
      }
      return cmp * dir;
    });
  }, [subsQ.data, countyFilter, sortBy, sortDir]);

  return (
    <div className="space-y-4 max-w-5xl">
      <h1 className="text-2xl font-semibold text-gray-800">Subdivisions</h1>
      <p className="text-sm text-gray-500">
        Showing subdivisions where builders own or have recently owned lots.
      </p>

      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[240px]">
            <label className="block text-xs text-gray-500 mb-1">Search</label>
            <input
              type="text"
              placeholder="Subdivision name..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-500 mb-1">County</label>
            <select
              value={countyFilter}
              onChange={(e) => setCountyFilter(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white min-w-[160px]"
            >
              <option value="">All Counties</option>
              {countiesQ.data?.map((c) => (
                <option key={c} value={c}>
                  {c}, FL
                </option>
              ))}
            </select>
          </div>

          {gated && rows.length > 0 && (
            <span className="text-sm text-gray-500 pb-1">
              {rows.length} subdivision{rows.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {!gated ? (
          <p className="text-sm text-gray-400 p-4">
            Type at least 2 characters or pick a county to search.
          </p>
        ) : subsQ.isLoading ? (
          <p className="text-sm text-gray-400 p-4">Loading...</p>
        ) : subsQ.error ? (
          <p className="text-sm text-red-600 p-4">
            Failed to load: {(subsQ.error as Error).message}
          </p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-gray-400 p-4">No subdivisions with builder activity found.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold uppercase tracking-wide">
                <SortTh label="Subdivision" sortKey="name" align="left" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="County" sortKey="county" align="left" className="w-36" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builders" sortKey="builders" align="right" className="w-24" active={sortBy} dir={sortDir} onSort={toggleSort} />
                <SortTh label="Builder Lots" sortKey="lots" align="right" className="w-28" active={sortBy} dir={sortDir} onSort={toggleSort} />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {rows.map((row) => (
                <tr key={row.id} className="hover:bg-blue-50">
                  <td className="px-4 py-2">
                    <Link
                      to={`/subdivisions/${row.id}`}
                      className="font-semibold text-gray-800 hover:text-blue-700"
                    >
                      {row.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-gray-500">{row.county_name}</td>
                  <td className="px-4 py-2 text-right tabular-nums text-gray-700">
                    {row.distinct_builder_count}
                  </td>
                  <td className="px-4 py-2 text-right tabular-nums font-medium text-gray-800">
                    {row.builder_lot_count.toLocaleString()}
                  </td>
                </tr>
              ))}
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
      className={`px-4 py-2 cursor-pointer select-none hover:text-gray-800 transition-colors ${
        align === "right" ? "text-right" : "text-left"
      } ${isActive ? "text-gray-800" : "text-gray-500"} ${className ?? ""}`}
      onClick={() => onSort(sortKey)}
    >
      {label}{arrow}
    </th>
  );
}
