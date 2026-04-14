import { useState, useMemo, type ReactNode } from "react";
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
    <div className="page-stack report-page">
      <div className="page-header">
        <div className="page-heading">
          <p className="page-kicker">Commission Radar</p>
          <h1 className="page-title">Entitlement Watch</h1>
          <p className="page-subtitle">
            Track meetings, project rosters, and action outcomes across county commissions.
          </p>
        </div>
      </div>

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
        <div className="surface-card panel-pad">
          <div className="section-head mb-3">
            <h2 className="section-title">Meeting Calendar</h2>
          </div>
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
        <div className="lg:col-span-2 surface-card panel-pad">
          <div className="section-head mb-3">
            <h2 className="section-title">Upcoming Meetings</h2>
          </div>
          {futureMeetings.length === 0 ? (
            <p className="data-note">No upcoming meetings in current data.</p>
          ) : (
            <div className="space-y-2">
              {futureMeetings.slice(0, 10).map((date) => {
                const actions = actionsQ.data?.items.filter((a) => a.meeting_date === date) ?? [];
                const jurisdictions = [...new Set(actions.map((a) => a.jurisdiction_name))];
                return (
                  <div key={date} className="surface-muted flex items-center gap-3 rounded-[var(--radius-lg)] border border-[var(--border-subtle)] px-3 py-2 text-sm">
                    <span className="w-24 shrink-0 font-semibold text-[var(--text)]">{date}</span>
                    <span className="text-[var(--text-muted)]">{jurisdictions.join(", ")}</span>
                    <span className="ml-auto text-xs text-[var(--text-soft)]">{actions.length} action{actions.length !== 1 ? "s" : ""}</span>
                  </div>
                );
              })}
              {futureMeetings.length > 10 && (
                <p className="data-note">+{futureMeetings.length - 10} more dates</p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tab switcher */}
      <div className="chip-row">
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
            <p className="data-note">Loading...</p>
          ) : meetingGroups.length === 0 ? (
            <p className="data-note">No meetings found.</p>
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
            <div className="data-toolbar pt-2">
              <span className="data-note">
                Page {actionsQ.data.page} of {actionsQ.data.pages} ({fmt(actionsQ.data.total)} actions)
              </span>
              <div className="button-row">
                <button
                  onClick={() => setActionPage((p) => Math.max(1, p - 1))}
                  disabled={actionPage <= 1}
                  className="button-ghost"
                >
                  Prev
                </button>
                <button
                  onClick={() => setActionPage((p) => p + 1)}
                  disabled={actionPage >= (actionsQ.data?.pages ?? 1)}
                  className="button-ghost"
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
          <div className="surface-card panel-pad mb-4">
            <input
              type="text"
              placeholder="Search projects..."
              value={rosterSearch}
              onChange={(e) => { setRosterSearch(e.target.value); setRosterPage(1); }}
              className="form-control w-full max-w-xs"
            />
          </div>

          <div className="surface-card data-shell overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="text-left">Project</th>
                  <th className="text-left">County</th>
                  <th className="text-left">Jurisdiction</th>
                  <th className="text-left">Status</th>
                  <th className="text-left">Stage</th>
                  <th className="text-left">Last Action</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rosterQ.isLoading ? (
                  <tr>
                    <td colSpan={7} className="table-empty text-center">Loading...</td>
                  </tr>
                ) : !rosterQ.data || rosterQ.data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="table-empty text-center">No projects found</td>
                  </tr>
                ) : (
                  rosterQ.data.items
                    .filter((r) => r.action_count > 0)
                    .map((r) => (
                      <tr key={r.id}>
                        <td>
                          <Link
                            to={`/subdivisions/${r.id}`}
                            className="font-medium text-[var(--accent)] hover:underline"
                          >
                            {r.name}
                          </Link>
                        </td>
                        <td>{r.county}</td>
                        <td>{r.jurisdiction_name}</td>
                        <td>
                          {r.entitlement_status && (
                            <span className="badge badge-accent">
                              {r.entitlement_status}
                            </span>
                          )}
                        </td>
                        <td>{r.lifecycle_stage_label}</td>
                        <td className="whitespace-nowrap">{r.last_action_date}</td>
                        <td className="text-right tabular-nums">{r.action_count}</td>
                      </tr>
                    ))
                )}
              </tbody>
            </table>
            {rosterQ.data && rosterQ.data.pages > 1 && (
              <div className="data-toolbar">
                <span className="data-note">
                  Page {rosterQ.data.page} of {rosterQ.data.pages} ({fmt(rosterQ.data.total)} total)
                </span>
                <div className="button-row">
                  <button
                    onClick={() => setRosterPage((p) => Math.max(1, p - 1))}
                    disabled={rosterPage <= 1}
                    className="button-ghost"
                  >
                    Prev
                  </button>
                  <button
                    onClick={() => setRosterPage((p) => p + 1)}
                    disabled={rosterPage >= (rosterQ.data?.pages ?? 1)}
                    className="button-ghost"
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
    <div id={`meeting-${date}`} className="surface-card overflow-hidden">
      <button
        onClick={() => setExpanded((e) => !e)}
        className="surface-muted flex w-full items-center justify-between border-b border-[var(--border-subtle)] px-4 py-3 text-left"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-bold text-[var(--text)]">{date || "No date"}</span>
          <span className="text-sm font-medium text-[var(--text-muted)]">{jurisdiction}</span>
          <span className="badge badge-accent">
            {items.length} action{items.length !== 1 ? "s" : ""}
          </span>
        </div>
        <span className="text-sm text-[var(--text-soft)]">{expanded ? "\u25b2" : "\u25bc"}</span>
      </button>
      {expanded && (
        <div className="data-shell">
          <table className="data-table">
            <tbody>
              {items.map((a) => (
                <tr
                  key={a.id}
                  className="cursor-pointer"
                  onClick={() => onActionClick(a)}
                >
                  <td className="max-w-[200px] truncate pl-8 font-medium" title={a.project_name}>
                    {a.project_name}
                  </td>
                  <td>{a.approval_type.replace(/_/g, " ")}</td>
                  <td>{a.ref_number}</td>
                  <td>
                    <OutcomeBadge status={a.status} />
                  </td>
                  <td className="text-xs text-[var(--text-soft)]">{a.document_type}</td>
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
    <div className={`metric-card ${accent ? "warn" : ""}`.trim()}>
      <p className="metric-label">{label}</p>
      <p className={`metric-value ${accent ? "warn" : ""}`.trim()}>{value}</p>
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
  children: ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`chip-pill ${active ? "active" : ""}`}
    >
      {children}
    </button>
  );
}

function OutcomeBadge({ status }: { status: string }) {
  if (!status) return <span className="text-gray-400 text-xs">&mdash;</span>;
  const s = status.toLowerCase();
  const styles = s.includes("approv") || s.includes("rec. approval")
    ? "badge-success"
    : s.includes("denied") || s.includes("rec. denial")
      ? "badge-danger"
      : s.includes("tabled") || s.includes("deferred")
        ? "badge-warning"
        : "badge-neutral";
  return (
    <span className={`badge ${styles}`}>
      {status}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Action detail panel
// ---------------------------------------------------------------------------

function DetailRow({ label, value }: { label: string; value: ReactNode }) {
  if (!value || value === "") return null;
  return (
    <div className="detail-row">
      <dt className="detail-label">{label}</dt>
      <dd className="detail-value">{value}</dd>
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
    <>
      <div className="drawer-scrim" onClick={onClose} />
      <aside className="inspector-drawer">
      <div className="inspector-header">
        <div className="min-w-0 pr-4">
          <p className="inspector-kicker">Commission Action</p>
          <h2 className="inspector-title">{a.project_name}</h2>
          <div className="drawer-chip-row mt-2">
            <OutcomeBadge status={a.status} />
            <span className="badge badge-neutral">{a.jurisdiction_name}</span>
            <span className="badge badge-neutral">{a.meeting_date}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="inspector-close"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="inspector-body">
        <section className="inspector-section">
          <div className="section-head">
            <h3 className="section-title">Case Information</h3>
          </div>
          <dl className="detail-grid">
            <DetailRow label="Approval Type" value={a.approval_type.replace(/_/g, " ")} />
            <DetailRow label="Case Number" value={a.case_number} />
            <DetailRow label="Ordinance" value={a.ordinance_number} />
            <DetailRow label="Reading" value={a.reading_number} />
            <DetailRow label="Action Requested" value={a.action_requested} />
            <DetailRow label="Document Type" value={a.document_type} />
          </dl>
        </section>

        {/* Project details */}
        <section className="inspector-section">
          <div className="section-head">
            <h3 className="section-title">Project Details</h3>
          </div>
          <dl className="detail-grid">
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
          <section className="inspector-section">
            <div className="section-head">
              <h3 className="section-title">Land Use &amp; Zoning</h3>
            </div>
            <dl className="detail-grid">
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
          <section className="inspector-section">
            <div className="section-head">
              <h3 className="section-title">Summary</h3>
            </div>
            <p className="detail-value whitespace-pre-wrap">{a.action_summary}</p>
          </section>
        )}

        {/* Conditions */}
        {a.conditions && (
          <section className="inspector-section">
            <div className="section-head">
              <h3 className="section-title">Conditions</h3>
            </div>
            <p className="detail-value whitespace-pre-wrap">{a.conditions}</p>
          </section>
        )}

        {/* Vote */}
        {(a.vote_detail || votes.length > 0) && (
          <section className="inspector-section">
            <div className="section-head">
              <h3 className="section-title">Vote</h3>
            </div>
            {a.vote_detail && <p className="detail-value">{a.vote_detail}</p>}
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
          <section className="inspector-section flat">
            <div className="section-head">
              <h3 className="section-title">Needs Review</h3>
              <span className="badge badge-warning">Review</span>
            </div>
            <p className="detail-value text-[var(--warning)]">{a.review_notes}</p>
          </section>
        )}

        {/* Source document link */}
        {a.document_url && (
          <a
            href={a.document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="button-primary w-full justify-center"
          >
            View Source Document &#8599;
          </a>
        )}
      </div>
      </aside>
    </>
  );
}

function VoteBadge({ vote }: { vote: string }) {
  const v = vote.toLowerCase();
  const styles = v === "yes" || v === "aye"
    ? "badge-success"
    : v === "no" || v === "nay"
      ? "badge-danger"
      : v === "absent" || v === "abstain"
        ? "badge-neutral"
        : "badge-neutral";
  return (
    <span className={`badge ${styles}`}>
      {vote}
    </span>
  );
}
