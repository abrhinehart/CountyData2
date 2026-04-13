import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCounties, searchInventorySubdivisions } from "../api";
import type { InventorySubdivisionOut } from "../types";

export default function SubdivisionsPage() {
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [countyFilter, setCountyFilter] = useState<string>("Bay");

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

  const rows = (subsQ.data ?? []).filter((r) =>
    countyFilter ? r.county_name === countyFilter : true
  );

  return (
    <div className="space-y-4 max-w-4xl">
      <h1 className="text-2xl font-semibold text-gray-800">Subdivisions</h1>

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
              {rows.length} builder-active subdivision{rows.length !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {!gated ? (
          <p className="text-sm text-gray-400">
            Type at least 2 characters or pick a county to search.
          </p>
        ) : subsQ.isLoading ? (
          <p className="text-sm text-gray-400">Loading...</p>
        ) : subsQ.error ? (
          <p className="text-sm text-red-600">
            Failed to load: {(subsQ.error as Error).message}
          </p>
        ) : rows.length === 0 ? (
          <p className="text-sm text-gray-400">No builder-active subdivisions found.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {rows.map((row) => (
              <li key={row.id}>
                <Link
                  to={`/subdivisions/${row.id}`}
                  className="flex items-center gap-4 px-2 py-2 rounded hover:bg-blue-50"
                >
                  <span className="flex-1 font-semibold text-gray-800">{row.name}</span>
                  <span className="text-sm text-gray-500 w-40 truncate">{row.county_name}, FL</span>
                  <span className="text-sm text-gray-400 w-24 text-right tabular-nums">
                    {row.parcel_count.toLocaleString()} parcels
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
