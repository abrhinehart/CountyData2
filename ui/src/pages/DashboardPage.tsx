import { useQuery } from "@tanstack/react-query";
import { getStats } from "../api";
import { useNavigate } from "react-router-dom";

function fmt(n: number): string {
  return n.toLocaleString();
}

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
  });
  const navigate = useNavigate();

  if (isLoading) return <p className="text-gray-500">Loading stats...</p>;
  if (error || !stats)
    return <p className="text-red-600">Failed to load stats.</p>;

  const totalByCounty = stats.by_county.reduce((s, c) => s + c.count, 0);

  return (
    <div className="space-y-8 max-w-5xl">
      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card label="Total Transactions" value={fmt(stats.total_transactions)} />
        <Card label="Flagged for Review" value={fmt(stats.flagged_for_review)} accent />
        <Card
          label="Date Range"
          value={
            stats.date_range.min && stats.date_range.max
              ? `${stats.date_range.min} - ${stats.date_range.max}`
              : "N/A"
          }
          small
        />
        <Card label="Counties" value={String(stats.by_county.length)} />
      </div>

      {/* County breakdown + Type breakdown side-by-side */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* By county */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Transactions by County
          </h2>
          <div className="space-y-2">
            {stats.by_county.map((c) => (
              <button
                key={c.county}
                onClick={() =>
                  navigate(`/transactions?county=${encodeURIComponent(c.county)}`)
                }
                className="w-full flex items-center gap-3 group text-left"
              >
                <span className="text-sm font-medium text-gray-700 w-28 shrink-0 group-hover:text-blue-700 transition-colors">
                  {c.county}
                </span>
                <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                  <div
                    className="bg-blue-500 h-full rounded-full transition-all"
                    style={{
                      width: `${Math.max((c.count / totalByCounty) * 100, 2)}%`,
                    }}
                  />
                </div>
                <span className="text-sm text-gray-500 w-16 text-right tabular-nums">
                  {fmt(c.count)}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* By type */}
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
            Transactions by Type
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-100">
                <th className="pb-2 font-medium">Type</th>
                <th className="pb-2 font-medium text-right">Count</th>
              </tr>
            </thead>
            <tbody>
              {stats.by_type.map((t) => (
                <tr
                  key={t.type}
                  className="border-b border-gray-50 last:border-0"
                >
                  <td className="py-1.5 text-gray-700">{t.type}</td>
                  <td className="py-1.5 text-right text-gray-500 tabular-nums">
                    {fmt(t.count)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function Card({
  label,
  value,
  accent,
  small,
}: {
  label: string;
  value: string;
  accent?: boolean;
  small?: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </p>
      <p
        className={`font-semibold ${
          small ? "text-sm" : "text-2xl"
        } ${accent ? "text-amber-600" : "text-gray-800"} tabular-nums`}
      >
        {value}
      </p>
    </div>
  );
}
