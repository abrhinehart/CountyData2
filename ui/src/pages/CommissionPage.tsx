import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { getCommissionSummary, getCommissionActions, getCommissionRosterList } from "../api";
import MeetingCalendar from "../components/MeetingCalendar";
import type { CommissionActionItem, CommissionerVote } from "../types";

function fmt(n: number): string {
  return n.toLocaleString();
}

type Tab = "meetings" | "roster";

export default function CommissionPage() {
  const [tab, setTab] = useState<Tab>("meetings");
  const [actionPage, setActionPage] = useState(1);
  const [rosterPage, setRosterPage] = useState(1);
  const [rosterSearch, setRosterSearch] = useState("");
  const [selectedAction, setSelectedAction] = useState<CommissionActionItem | null>(null);

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
                onActionClick={setSelectedAction}
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

      {/* Action detail panel */}
      {selectedAction && (
        <ActionDetailPanel action={selectedAction} onClose={() => setSelectedAction(null)} />
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
  onActionClick,
}: {
  date: string;
  jurisdiction: string;
  items: CommissionActionItem[];
  onActionClick: (a: CommissionActionItem) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div id={`meeting-${date}`} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-left border-b border-gray-200"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold text-gray-900">{date || "No date"}</span>
          <span className="text-sm font-medium text-gray-600">{jurisdiction}</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
            {items.length} action{items.length !== 1 ? "s" : ""}
          </span>
        </div>
        <span className="text-gray-400 text-sm">{expanded ? "\u25b2" : "\u25bc"}</span>
      </button>
      {expanded && (
        <div>
          <table className="w-full text-sm">
            <tbody>
              {items.map((a) => (
                <tr
                  key={a.id}
                  className="border-b border-gray-50 last:border-0 hover:bg-blue-50/50 cursor-pointer"
                  onClick={() => onActionClick(a)}
                >
                  <td className="pl-8 pr-3 py-1.5 text-gray-700 font-medium max-w-[200px] truncate" title={a.project_name}>
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

// ---------------------------------------------------------------------------
// Action detail panel
// ---------------------------------------------------------------------------

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  if (!value || value === "") return null;
  return (
    <div>
      <dt className="text-xs text-gray-400 uppercase tracking-wide">{label}</dt>
      <dd className="text-sm text-gray-800 mt-0.5">{value}</dd>
    </div>
  );
}

function ActionDetailPanel({
  action: a,
  onClose,
}: {
  action: CommissionActionItem;
  onClose: () => void;
}) {
  const hasZoningChange = a.current_zoning || a.proposed_zoning;
  const hasLandUseChange = a.current_land_use || a.proposed_land_use;
  const votes = a.commissioner_votes ?? [];

  return (
    <div className="fixed right-0 top-[53px] bottom-0 w-[480px] bg-white shadow-xl border-l border-gray-200 z-[1000] overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 px-5 py-4 flex items-start justify-between">
        <div className="min-w-0 pr-4">
          <h2 className="text-lg font-semibold text-gray-900">{a.project_name}</h2>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <OutcomeBadge status={a.status} />
            <span className="text-sm text-gray-500">{a.jurisdiction_name}</span>
            <span className="text-sm text-gray-400">{a.meeting_date}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 shrink-0"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-5 space-y-5">
        {/* Case info */}
        <section className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Case Information</h3>
          <dl className="space-y-2">
            <DetailRow label="Approval Type" value={a.approval_type.replace(/_/g, " ")} />
            <DetailRow label="Case Number" value={a.case_number} />
            <DetailRow label="Ordinance" value={a.ordinance_number} />
            <DetailRow label="Reading" value={a.reading_number} />
            <DetailRow label="Action Requested" value={a.action_requested} />
            <DetailRow label="Document Type" value={a.document_type} />
          </dl>
        </section>

        {/* Project details */}
        <section className="space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Project Details</h3>
          <dl className="space-y-2">
            <DetailRow label="Phase" value={a.phase_name} />
            <DetailRow label="Address" value={a.address} />
            <DetailRow label="Applicant" value={a.applicant_name} />
            {a.acreage != null && <DetailRow label="Acreage" value={a.acreage.toLocaleString()} />}
            {a.lot_count != null && <DetailRow label="Lot Count" value={a.lot_count.toLocaleString()} />}
            {a.parcel_ids.length > 0 && (
              <DetailRow label="Parcel IDs" value={a.parcel_ids.join(", ")} />
            )}
          </dl>
        </section>

        {/* Land use / zoning changes */}
        {(hasLandUseChange || hasZoningChange) && (
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Land Use &amp; Zoning</h3>
            <dl className="space-y-2">
              {hasLandUseChange && (
                <DetailRow
                  label="Land Use"
                  value={
                    a.current_land_use && a.proposed_land_use
                      ? <span>{a.current_land_use} <span className="text-gray-400">&rarr;</span> <span className="font-medium">{a.proposed_land_use}</span></span>
                      : a.proposed_land_use || a.current_land_use
                  }
                />
              )}
              {a.land_use_scale && <DetailRow label="Scale" value={a.land_use_scale} />}
              {hasZoningChange && (
                <DetailRow
                  label="Zoning"
                  value={
                    a.current_zoning && a.proposed_zoning
                      ? <span>{a.current_zoning} <span className="text-gray-400">&rarr;</span> <span className="font-medium">{a.proposed_zoning}</span></span>
                      : a.proposed_zoning || a.current_zoning
                  }
                />
              )}
            </dl>
          </section>
        )}

        {/* Summary */}
        {a.action_summary && (
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Summary</h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{a.action_summary}</p>
          </section>
        )}

        {/* Conditions */}
        {a.conditions && (
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Conditions</h3>
            <p className="text-sm text-gray-700 whitespace-pre-wrap">{a.conditions}</p>
          </section>
        )}

        {/* Vote */}
        {(a.vote_detail || votes.length > 0) && (
          <section className="space-y-2">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Vote</h3>
            {a.vote_detail && <p className="text-sm text-gray-700">{a.vote_detail}</p>}
            {votes.length > 0 && (
              <table className="w-full text-sm mt-2">
                <thead>
                  <tr className="text-left text-xs text-gray-400 border-b border-gray-100">
                    <th className="pb-1 font-medium">Commissioner</th>
                    <th className="pb-1 font-medium">Vote</th>
                    <th className="pb-1 font-medium text-right">Role</th>
                  </tr>
                </thead>
                <tbody>
                  {votes.map((v) => (
                    <tr key={v.commissioner_id} className="border-b border-gray-50 last:border-0">
                      <td className="py-1 text-gray-700">
                        {v.name}
                        {v.title && <span className="text-gray-400 text-xs ml-1">({v.title})</span>}
                      </td>
                      <td className="py-1">
                        <VoteBadge vote={v.vote} />
                      </td>
                      <td className="py-1 text-right text-xs text-gray-400">
                        {v.made_motion && "Motion"}
                        {v.made_motion && v.seconded_motion && " / "}
                        {v.seconded_motion && "Second"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        )}

        {/* Review notes */}
        {a.needs_review && a.review_notes && (
          <section className="bg-amber-50 border border-amber-200 rounded-lg p-3">
            <h3 className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1">Needs Review</h3>
            <p className="text-sm text-amber-800">{a.review_notes}</p>
          </section>
        )}

        {/* Source document link */}
        {a.document_url && (
          <a
            href={a.document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block text-center text-sm font-medium text-blue-600 hover:text-blue-800 py-2 border border-blue-200 rounded hover:bg-blue-50 transition-colors"
          >
            View Source Document &#8599;
          </a>
        )}
      </div>
    </div>
  );
}

function VoteBadge({ vote }: { vote: string }) {
  const v = vote.toLowerCase();
  const styles = v === "yes" || v === "aye"
    ? "bg-green-100 text-green-700"
    : v === "no" || v === "nay"
      ? "bg-red-100 text-red-700"
      : v === "absent" || v === "abstain"
        ? "bg-gray-100 text-gray-500"
        : "bg-gray-100 text-gray-600";
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles}`}>
      {vote}
    </span>
  );
}
