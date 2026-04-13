import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getGeometryCoverage } from "../api";
import type { GeometryCoverageRow } from "../types";

type SortKey = "county" | "total" | "with_geom" | "without_geom" | "pct";
type SortDir = "asc" | "desc";

export default function HealthPage() {
  const [sortBy, setSortBy] = useState<SortKey>("county");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const { data, isLoading, error } = useQuery({
    queryKey: ["geometry-coverage"],
    queryFn: getGeometryCoverage,
  });

  function toggleSort(key: SortKey) {
    if (sortBy === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortDir(key === "county" ? "asc" : "desc");
    }
  }

  const rows = useMemo(() => {
    if (!data?.rows) return [];
    const dir = sortDir === "asc" ? 1 : -1;
    return [...data.rows].sort((a, b) => {
      let cmp: number;
      switch (sortBy) {
        case "county":
          cmp = a.county.localeCompare(b.county);
          break;
        case "total":
          cmp = a.total - b.total;
          break;
        case "with_geom":
          cmp = a.with_geom - b.with_geom;
          break;
        case "without_geom":
          cmp = a.without_geom - b.without_geom;
          break;
        case "pct":
          cmp =
            (a.total ? a.with_geom / a.total : 0) -
            (b.total ? b.with_geom / b.total : 0);
          break;
      }
      return cmp * dir;
    });
  }, [data, sortBy, sortDir]);

  const totals = useMemo(() => {
    if (!rows.length) return { total: 0, with_geom: 0, without_geom: 0 };
    return rows.reduce(
      (acc, r) => ({
        total: acc.total + r.total,
        with_geom: acc.with_geom + r.with_geom,
        without_geom: acc.without_geom + r.without_geom,
      }),
      { total: 0, with_geom: 0, without_geom: 0 },
    );
  }, [rows]);

  const arrow = (key: SortKey) =>
    sortBy === key ? (sortDir === "asc" ? " \u25B2" : " \u25BC") : "";

  const pct = (n: number, d: number) =>
    d ? `${((n / d) * 100).toFixed(1)}%` : "\u2014";

  return (
    <div className="space-y-6 max-w-4xl">
      <h1 className="text-2xl font-semibold text-gray-800">Platform Health</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium text-gray-700">
          Subdivision Geometry Coverage
        </h2>

        {isLoading && <p className="text-sm text-gray-500">Loading...</p>}
        {error && (
          <p className="text-sm text-red-600">
            Failed to load geometry coverage.
          </p>
        )}

        {rows.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {([
                    ["county", "County"],
                    ["total", "Total"],
                    ["with_geom", "With Geom"],
                    ["without_geom", "Without Geom"],
                    ["pct", "Coverage"],
                  ] as [SortKey, string][]).map(([key, label]) => (
                    <th
                      key={key}
                      onClick={() => toggleSort(key)}
                      className="px-4 py-2 text-left font-medium text-gray-600 cursor-pointer select-none hover:text-gray-900"
                    >
                      {label}
                      {arrow(key)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {rows.map((r) => (
                  <tr key={r.county} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium text-gray-800">
                      {r.county}
                    </td>
                    <td className="px-4 py-2 text-gray-700">{r.total}</td>
                    <td className="px-4 py-2 text-gray-700">{r.with_geom}</td>
                    <td className="px-4 py-2 text-gray-700">
                      {r.without_geom}
                    </td>
                    <td className="px-4 py-2 text-gray-700">
                      {pct(r.with_geom, r.total)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-gray-50 border-t border-gray-200 font-medium">
                <tr>
                  <td className="px-4 py-2 text-gray-800">Total</td>
                  <td className="px-4 py-2 text-gray-700">{totals.total}</td>
                  <td className="px-4 py-2 text-gray-700">
                    {totals.with_geom}
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {totals.without_geom}
                  </td>
                  <td className="px-4 py-2 text-gray-700">
                    {pct(totals.with_geom, totals.total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
