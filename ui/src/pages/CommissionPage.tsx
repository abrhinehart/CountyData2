import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCommissionSummary, getCommissionActions, getCommissionRosterList } from "../api";
import MeetingCalendar from "../components/MeetingCalendar";
import type { CommissionActionItem } from "../types";

function fmt(n: number): string {
  return n.toLocaleString();
}

type Tab = "meetings" | "roster";

export default function CommissionPage() {
  const [tab, setTab] = useState<Tab>("meetings");
  const [actionPage, setActionPage] = useState(1);
  const [rosterPage, setRosterPage] = useState(1);
  const [rosterSearch, setRosterSearch] = useState("");

  const summaryQ = useQuery({
    queryKey: ["commission-summary"],
    queryFn: getCommissionSummary,
  });

  const actionsQ = useQuery({
    queryKey: ["commission-actions", actionPage],
    queryFn: () => getCommissionActions({ page: actionPage, per_page: 100 }),
  });

  const rosterQ = useQuery({
    queryKey: ["commission-roster-list", rosterPage, rosterSearch],
    queryFn: () =>
      getCommissionRosterList({
        page: rosterPage,
        per_page: 50,
        search: rosterSearch || undefined,
      }),
    enabled: tab === "roster",
  });

  const summary = summaryQ.data;

  // Extract all meeting dates for calendar
  const meetingDates = useMemo(() => {
    if (!actionsQ.data?.items) return [];
    const dates = new Set<string>();
    for (const a of actionsQ.data.items) {
      if (a.meeting_date) dates.add(a.meeting_date);
    }
    return [...dates].sort();
  }, [actionsQ.data]);

  // Future meetings (#25)
  const futureMeetings = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return meetingDates.filter((d) => d >= today);
  }, [meetingDates]);

  // Group actions by meeting date (#24)
  const meetingGroups = useMemo(() => {
    if (!actionsQ.data?.items) return [];
    const groups = new Map<string, CommissionActionItem[]>();
    for (const a of actionsQ.data.items) {
      const key = `${a.meeting_date}|${a.jurisdiction_name}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(a);
    }
    return [...groups.entries()].map(([key, items]) => {
      const [date, jurisdiction] = key.split("|");
      return { date, jurisdiction, items };
    });
  }, [actionsQ.data]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold text-gray-800">Commission Radar</h1>

      {/* KPI cards — #23: fix "Projects Tracked" to meaningful count (backend already fixed) */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
          <Card label="Documents Processed" value={fmt(summary.documents_processed)} />
          <Card label="Actions Extracted" value={fmt(summary.actions_extracted)} />
          <Card label="Projects Tracked" value={fmt(summary.projects_tracked)} />
          <Card label="Needs Review" value={fmt(summary.needs_review)} accent={summary.needs_review > 0} />
          <Card label="Active Jurisdictions" value={fmt(summary.jurisdictions_active)} />
        </div>
      )}

      {/* Calendar + Upcoming meetings (#25, #26) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Meeting Calendar
          </h2>
          <MeetingCalendar
            meetingDates={meetingDates}
            onDateClick={(date) => {
              setTab("meetings");
              setActionPage(1);
              // Scroll to the meeting group for this date
              const el = document.getElementById(`meeting-${date}`);
              el?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
          />
        </div>
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-5">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Upcoming Meetings
          </h2>
          {futureMeetings.length === 0 ? (
            <p className="text-sm text-gray-400">No upcoming meetings in current data.</p>
          ) : (
            <div className="space-y-2">
              {futureMeetings.slice(0, 10).map((date) => {
                const actions = actionsQ.data?.items.filter((a) => a.meeting_date === date) ?? [];
                const jurisdictions = [...new Set(actions.map((a) => a.jurisdiction_name))];
                return (
                  <div key={date} className="flex items-center gap-3 text-sm">
                    <span className="font-semibold text-gray-800 w-24 shrink-0">{date}</span>
                    <span className="text-gray-600">{jurisdictions.join(", ")}</span>
                    <span className="text-gray-400 text-xs ml-auto">{actions.length} action{actions.length !== 1 ? "s" : ""}</span>
                  </div>
                );
              })}
              {futureMeetings.length > 10 && (
                <p className="text-xs text-gray-400">+{futureMeetings.length - 10} more dates</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex gap-1 border-b border-gray-200">
        <TabButton active={tab === "meetings"} onClick={() => setTab("meetings")}>
          Recent Meetings
        </TabButton>
        <TabButton active={tab === "roster"} onClick={() => setTab("roster")}>
          Project Roster
        </TabButton>
      </div>

      {/* Meetings tab (#24: grouped by meeting date, expandable) */}
      {tab === "meetings" && (
        <div className="space-y-3">
          {actionsQ.isLoading ? (
            <p className="text-sm text-gray-400">Loading...</p>
          ) : meetingGroups.length === 0 ? (
            <p className="text-sm text-gray-400">No meetings found.</p>
          ) : (
            meetingGroups.map((group) => (
              <MeetingGroup
                key={`${group.date}-${group.jurisdiction}`}
                date={group.date}
                jurisdiction={group.jurisdiction}
                items={group.items}
              />
            ))
          )}
          {actionsQ.data && actionsQ.data.pages > 1 && (
            <div className="flex items-center justify-between text-sm text-gray-600 px-1 pt-2">
              <span>
                Page {actionsQ.data.page} of {actionsQ.data.pages} ({fmt(actionsQ.data.total)} actions)
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setActionPage((p) => Math.max(1, p - 1))}
                  disabled={actionPage <= 1}
                  className="px-2 py-1 rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
                >
                  Prev
                </button>
                <button
                  onClick={() => setActionPage((p) => p + 1)}
                  disabled={actionPage >= (actionsQ.data?.pages ?? 1)}
                  className="px-2 py-1 rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Roster tab (#29: filter to projects with action_count > 0) */}
      {tab === "roster" && (
        <div>
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
            <input
              type="text"
              placeholder="Search projects..."
              value={rosterSearch}
              onChange={(e) => { setRosterSearch(e.target.value); setRosterPage(1); }}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm w-72"
            />
          </div>

          <div className="bg-white border border-gray-200 rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Project</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">County</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Jurisdiction</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Status</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Stage</th>
                  <th className="px-3 py-2 text-left font-medium text-gray-600">Last Action</th>
                  <th className="px-3 py-2 text-right font-medium text-gray-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rosterQ.isLoading ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : !rosterQ.data || rosterQ.data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-gray-400">No projects found</td>
                  </tr>
                ) : (
                  rosterQ.data.items
                    .filter((r) => r.action_count > 0)
                    .map((r) => (
                      <tr key={r.id} className="border-b border-gray-100 hover:bg-blue-50">
                        <td className="px-3 py-1.5">
                          <Link
                            to={`/subdivisions/${r.id}`}
                            className="text-blue-600 hover:underline font-medium"
                          >
                            {r.name}
                          </Link>
                        </td>
                        <td className="px-3 py-1.5 text-gray-700">{r.county}</td>
                        <td className="px-3 py-1.5 text-gray-700">{r.jurisdiction_name}</td>
                        <td className="px-3 py-1.5">
                          {r.entitlement_status && (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              {r.entitlement_status}
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-1.5 text-gray-500">{r.lifecycle_stage_label}</td>
                        <td className="px-3 py-1.5 text-gray-700 whitespace-nowrap">{r.last_action_date}</td>
                        <td className="px-3 py-1.5 text-right tabular-nums text-gray-700">{r.action_count}</td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
            {rosterQ.data && rosterQ.data.pages > 1 && (
              <div className="flex items-center justify-between text-sm text-gray-600 px-3 py-3">
                <span>
                  Page {rosterQ.data.page} of {rosterQ.data.pages} ({fmt(rosterQ.data.total)} total)
                </span>
                <div className="flex gap-1">
                  <button
                    onClick={() => setRosterPage((p) => Math.max(1, p - 1))}
                    disabled={rosterPage <= 1}
                    className="px-2 py-1 rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
                  >
                    Prev
                  </button>
                  <button
                    onClick={() => setRosterPage((p) => p + 1)}
                    disabled={rosterPage >= (rosterQ.data?.pages ?? 1)}
                    className="px-2 py-1 rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function MeetingGroup({
  date,
  jurisdiction,
  items,
}: {
  date: string;
  jurisdiction: string;
  items: CommissionActionItem[];
}) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div id={`meeting-${date}`} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-800">{date || "No date"}</span>
          <span className="text-sm text-gray-500">{jurisdiction}</span>
          <span className="text-xs text-gray-400">{items.length} action{items.length !== 1 ? "s" : ""}</span>
        </div>
        <span className="text-gray-400 text-sm">{expanded ? "\u25b2" : "\u25bc"}</span>
      </button>
      {expanded && (
        <div className="border-t border-gray-100">
          <table className="w-full text-sm">
            <tbody>
              {items.map((a) => (
                <tr key={a.id} className="border-b border-gray-50 last:border-0 hover:bg-blue-50/30">
                  <td className="px-4 py-1.5 text-gray-700 font-medium max-w-[200px] truncate" title={a.project_name}>
                    {a.project_name}
                  </td>
                  <td className="px-3 py-1.5 text-gray-500">{a.approval_type.replace(/_/g, " ")}</td>
                  <td className="px-3 py-1.5 text-gray-500">{a.ref_number}</td>
                  <td className="px-3 py-1.5">
                    <OutcomeBadge status={a.status} />
                  </td>
                  <td className="px-3 py-1.5 text-gray-400 text-xs">{a.document_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Card({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-1">
        {label}
      </p>
      <p
        className={`text-2xl font-semibold tabular-nums ${
          accent ? "text-amber-600" : "text-gray-800"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? "border-blue-600 text-blue-700"
          : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
      }`}
    >
      {children}
    </button>
  );
}

function OutcomeBadge({ status }: { status: string }) {
  if (!status) return <span className="text-gray-400 text-xs">&mdash;</span>;
  const s = status.toLowerCase();
  const styles = s.includes("approv") || s.includes("rec. approval")
    ? "bg-green-100 text-green-700"
    : s.includes("denied") || s.includes("rec. denial")
      ? "bg-red-100 text-red-700"
      : s.includes("tabled") || s.includes("deferred")
        ? "bg-amber-100 text-amber-700"
        : "bg-gray-100 text-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles}`}>
      {status}
    </span>
  );
}
