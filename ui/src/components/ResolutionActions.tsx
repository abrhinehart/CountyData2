import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getSubdivisions, getSubdivision, resolveAction } from "../api";
import type { TransactionDetail, Subdivision, SubdivisionDetail } from "../types";

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

function NoteField({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Optional note"
      rows={2}
      className="w-full border border-gray-300 rounded px-3 py-2 text-sm resize-none"
    />
  );
}

function ActionButton({
  onClick,
  disabled,
  loading,
  label,
  loadingLabel,
  className,
}: {
  onClick: () => void;
  disabled?: boolean;
  loading: boolean;
  label: string;
  loadingLabel?: string;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={
        className ??
        "w-full px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
      }
    >
      {loading ? (loadingLabel ?? "Working...") : label}
    </button>
  );
}

/** Filterable subdivision dropdown */
function SubdivisionDropdown({
  county,
  value,
  onChange,
}: {
  county: string;
  value: number | null;
  onChange: (id: number | null, sub: Subdivision | null) => void;
}) {
  const { data: subdivisions } = useQuery({
    queryKey: ["subdivisions", county],
    queryFn: () => getSubdivisions(county),
    enabled: !!county,
  });

  const [filter, setFilter] = useState("");

  const filtered = useMemo(() => {
    if (!subdivisions) return [];
    if (!filter) return subdivisions;
    const lower = filter.toLowerCase();
    return subdivisions.filter((s) => s.canonical_name.toLowerCase().includes(lower));
  }, [subdivisions, filter]);

  return (
    <div className="space-y-1">
      <input
        type="text"
        placeholder="Type to filter subdivisions..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
      />
      <select
        value={value ?? ""}
        onChange={(e) => {
          const id = e.target.value ? Number(e.target.value) : null;
          const sub = subdivisions?.find((s) => s.id === id) ?? null;
          onChange(id, sub);
        }}
        className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm bg-white"
        size={Math.min(filtered.length + 1, 8)}
      >
        <option value="">-- Select subdivision --</option>
        {filtered.map((s) => (
          <option key={s.id} value={s.id}>
            {s.canonical_name}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Phase dropdown that combines known phases with free text input */
function PhaseInput({
  phases,
  value,
  onChange,
}: {
  phases: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex gap-2">
      {phases.length > 0 && (
        <select
          value={phases.includes(value) ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1.5 text-sm bg-white flex-1"
        >
          <option value="">-- Select phase --</option>
          {phases.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      )}
      <input
        type="text"
        placeholder={phases.length > 0 ? "Or type phase" : "Phase"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-300 rounded px-2 py-1.5 text-sm flex-1"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// SubdivisionAssigner
// for: subdivision_unmatched, *_unparsed_lines
// ---------------------------------------------------------------------------

export function SubdivisionAssigner({
  transaction,
  onResolved,
}: {
  transaction: TransactionDetail;
  onResolved: () => void;
}) {
  const [selectedSubId, setSelectedSubId] = useState<number | null>(null);
  const [selectedSub, setSelectedSub] = useState<Subdivision | null>(null);
  const [phase, setPhase] = useState("");
  const [lots, setLots] = useState<string>(String(transaction.lots ?? "1"));
  const [addAlias, setAddAlias] = useState(false);
  const [aliasText, setAliasText] = useState(() => {
    const pd = transaction.parsed_data as Record<string, unknown> | null;
    return String(pd?.subdivision_lookup_text ?? pd?.preparsed_subdivision ?? "").trim();
  });
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  // Fetch phases for selected subdivision
  const { data: subDetail } = useQuery<SubdivisionDetail>({
    queryKey: ["subdivision-detail", selectedSubId],
    queryFn: () => getSubdivision(selectedSubId!),
    enabled: selectedSubId != null,
  });

  const phases = subDetail?.phases ?? selectedSub?.phases ?? [];

  const handleAssign = async () => {
    if (!selectedSubId) return;
    setLoading(true);
    try {
      await resolveAction(transaction.id, {
        action: "assign_subdivision",
        subdivision_id: selectedSubId,
        phase: phase || null,
        lots: lots ? parseInt(lots, 10) : undefined,
        add_alias: addAlias ? aliasText : null,
        note,
      });
      onResolved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to assign subdivision");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Assign Subdivision
      </h4>

      <div>
        <label className="block text-xs text-gray-500 mb-1">Subdivision ({transaction.county})</label>
        <SubdivisionDropdown
          county={transaction.county}
          value={selectedSubId}
          onChange={(id, sub) => {
            setSelectedSubId(id);
            setSelectedSub(sub);
          }}
        />
      </div>

      <div>
        <label className="block text-xs text-gray-500 mb-1">Phase</label>
        <PhaseInput phases={phases} value={phase} onChange={setPhase} />
      </div>

      <div>
        <label className="block text-xs text-gray-500 mb-1">Lots</label>
        <input
          type="number"
          min="1"
          value={lots}
          onChange={(e) => setLots(e.target.value)}
          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
        />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="add-alias"
          checked={addAlias}
          onChange={(e) => setAddAlias(e.target.checked)}
          className="rounded border-gray-300"
        />
        <label htmlFor="add-alias" className="text-sm text-gray-700">
          Also add alias
        </label>
      </div>
      {addAlias && (
        <input
          type="text"
          value={aliasText}
          onChange={(e) => setAliasText(e.target.value)}
          placeholder="Alias text"
          className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
        />
      )}

      <NoteField value={note} onChange={setNote} />

      <ActionButton
        onClick={handleAssign}
        disabled={!selectedSubId}
        loading={loading}
        label="Assign & Resolve"
        loadingLabel="Assigning..."
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// PhaseResolver
// for: phase_not_confirmed_by_lookup
// ---------------------------------------------------------------------------

export function PhaseResolver({
  transaction,
  onResolved,
}: {
  transaction: TransactionDetail;
  onResolved: () => void;
}) {
  const [mode, setMode] = useState<"confirm" | "override">("confirm");
  const [overridePhase, setOverridePhase] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  // Fetch subdivision phases for override dropdown
  const { data: subDetail } = useQuery<SubdivisionDetail>({
    queryKey: ["subdivision-detail", transaction.subdivision_id],
    queryFn: () => getSubdivision(transaction.subdivision_id!),
    enabled: transaction.subdivision_id != null,
  });

  const phases = subDetail?.phases ?? [];

  const handleAction = async () => {
    setLoading(true);
    try {
      if (mode === "confirm") {
        await resolveAction(transaction.id, {
          action: "confirm_phase",
          note,
        });
      } else {
        if (!overridePhase) return;
        await resolveAction(transaction.id, {
          action: "override_phase",
          phase: overridePhase,
          note,
        });
      }
      onResolved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to resolve phase");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Resolve Phase
      </h4>

      <div className="bg-gray-50 border border-gray-200 rounded px-3 py-2 text-sm">
        <span className="text-gray-500">Current phase:</span>{" "}
        <span className="font-medium text-gray-800">{transaction.phase ?? "(none)"}</span>
        {transaction.subdivision && (
          <>
            <br />
            <span className="text-gray-500">Subdivision:</span>{" "}
            <span className="font-medium text-gray-800">{transaction.subdivision}</span>
          </>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setMode("confirm")}
          className={`flex-1 px-3 py-1.5 text-sm rounded border ${
            mode === "confirm"
              ? "bg-blue-50 border-blue-300 text-blue-700 font-medium"
              : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          Confirm phase
        </button>
        <button
          onClick={() => setMode("override")}
          className={`flex-1 px-3 py-1.5 text-sm rounded border ${
            mode === "override"
              ? "bg-blue-50 border-blue-300 text-blue-700 font-medium"
              : "bg-white border-gray-300 text-gray-600 hover:bg-gray-50"
          }`}
        >
          Override phase
        </button>
      </div>

      {mode === "override" && (
        <div>
          <label className="block text-xs text-gray-500 mb-1">New phase</label>
          <PhaseInput phases={phases} value={overridePhase} onChange={setOverridePhase} />
        </div>
      )}

      <NoteField value={note} onChange={setNote} />

      <ActionButton
        onClick={handleAction}
        disabled={mode === "override" && !overridePhase}
        loading={loading}
        label={mode === "confirm" ? "Confirm & Resolve" : "Override & Resolve"}
        loadingLabel="Resolving..."
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// SubdivisionPicker
// for: subdivision_ambiguous_candidates, multiple_subdivision_candidates
// ---------------------------------------------------------------------------

export function SubdivisionPicker({
  transaction,
  onResolved,
}: {
  transaction: TransactionDetail;
  onResolved: () => void;
}) {
  const pd = transaction.parsed_data as Record<string, unknown> | null;
  const countyParse = (pd?.county_parse ?? {}) as Record<string, unknown>;
  const candidates = (countyParse?.normalized_subdivision_candidates ?? []) as Array<{
    subdivision?: string;
    subdivision_id?: number;
    phase?: string;
    raw?: string;
    details?: Record<string, unknown>;
  }>;

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [phase, setPhase] = useState("");
  const [showFull, setShowFull] = useState(candidates.length === 0);
  const [fullSubId, setFullSubId] = useState<number | null>(null);
  const [fullSub, setFullSub] = useState<Subdivision | null>(null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const effectiveSubId = showFull ? fullSubId : selectedId;

  // Fetch phases for whichever subdivision is selected
  const { data: subDetail } = useQuery<SubdivisionDetail>({
    queryKey: ["subdivision-detail", effectiveSubId],
    queryFn: () => getSubdivision(effectiveSubId!),
    enabled: effectiveSubId != null,
  });

  const phases = subDetail?.phases ?? fullSub?.phases ?? [];

  // Auto-populate phase from candidate if selected from candidate list
  const handleCandidateSelect = (cand: (typeof candidates)[0]) => {
    const id = cand.subdivision_id ?? null;
    setSelectedId(id);
    setShowFull(false);
    if (cand.phase) setPhase(String(cand.phase));
  };

  const handlePick = async () => {
    if (!effectiveSubId) return;
    setLoading(true);
    try {
      await resolveAction(transaction.id, {
        action: "pick_subdivision",
        subdivision_id: effectiveSubId,
        phase: phase || null,
        note,
      });
      onResolved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to pick subdivision");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Pick Subdivision
      </h4>

      {candidates.length > 0 && !showFull && (
        <div className="space-y-1.5">
          <label className="block text-xs text-gray-500">Candidates</label>
          {candidates.map((cand, i) => {
            const id = cand.subdivision_id ?? null;
            const name = cand.subdivision ?? cand.raw ?? "(unknown)";
            const isSelected = selectedId === id && id != null;
            return (
              <button
                key={i}
                onClick={() => handleCandidateSelect(cand)}
                className={`w-full text-left px-3 py-2 rounded border text-sm ${
                  isSelected
                    ? "bg-blue-50 border-blue-300 text-blue-800"
                    : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
                }`}
              >
                <span className="font-medium">{name}</span>
                {cand.phase && (
                  <span className="text-gray-500 ml-2">phase: {cand.phase}</span>
                )}
                {cand.details?.alias_source ? (
                  <span className="text-gray-400 ml-2 text-xs">
                    alias: {String(cand.details.alias_source)}
                  </span>
                ) : null}
              </button>
            );
          })}
          <button
            onClick={() => setShowFull(true)}
            className="text-xs text-blue-600 hover:underline mt-1"
          >
            Use full subdivision list instead
          </button>
        </div>
      )}

      {showFull && (
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs text-gray-500">Subdivision ({transaction.county})</label>
            {candidates.length > 0 && (
              <button
                onClick={() => setShowFull(false)}
                className="text-xs text-blue-600 hover:underline"
              >
                Back to candidates
              </button>
            )}
          </div>
          <SubdivisionDropdown
            county={transaction.county}
            value={fullSubId}
            onChange={(id, sub) => {
              setFullSubId(id);
              setFullSub(sub);
            }}
          />
        </div>
      )}

      <div>
        <label className="block text-xs text-gray-500 mb-1">Phase</label>
        <PhaseInput phases={phases} value={phase} onChange={setPhase} />
      </div>

      <NoteField value={note} onChange={setNote} />

      <ActionButton
        onClick={handlePick}
        disabled={!effectiveSubId}
        loading={loading}
        label="Pick & Resolve"
        loadingLabel="Resolving..."
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// PhasePicker
// for: multiple_phase_candidates
// ---------------------------------------------------------------------------

export function PhasePicker({
  transaction,
  onResolved,
}: {
  transaction: TransactionDetail;
  onResolved: () => void;
}) {
  const pd = transaction.parsed_data as Record<string, unknown> | null;
  const candidates = ((pd?.phase_candidate_values ?? []) as string[]).filter(Boolean);

  const [selected, setSelected] = useState<string>("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const handlePick = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      await resolveAction(transaction.id, {
        action: "pick_phase",
        phase: selected,
        note,
      });
      onResolved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to pick phase");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
        Pick Phase
      </h4>

      {transaction.subdivision && (
        <div className="bg-gray-50 border border-gray-200 rounded px-3 py-2 text-sm">
          <span className="text-gray-500">Subdivision:</span>{" "}
          <span className="font-medium text-gray-800">{transaction.subdivision}</span>
        </div>
      )}

      {candidates.length > 0 ? (
        <div className="space-y-1.5">
          <label className="block text-xs text-gray-500">Phase candidates</label>
          {candidates.map((cand) => (
            <label
              key={cand}
              className={`flex items-center gap-2 px-3 py-2 rounded border text-sm cursor-pointer ${
                selected === cand
                  ? "bg-blue-50 border-blue-300 text-blue-800"
                  : "bg-white border-gray-200 text-gray-700 hover:bg-gray-50"
              }`}
            >
              <input
                type="radio"
                name="phase-candidate"
                value={cand}
                checked={selected === cand}
                onChange={() => setSelected(cand)}
                className="text-blue-600"
              />
              <span className="font-medium">{cand}</span>
            </label>
          ))}
        </div>
      ) : (
        <div>
          <label className="block text-xs text-gray-500 mb-1">Phase</label>
          <input
            type="text"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            placeholder="Enter phase"
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm"
          />
        </div>
      )}

      <NoteField value={note} onChange={setNote} />

      <ActionButton
        onClick={handlePick}
        disabled={!selected}
        loading={loading}
        label="Pick & Resolve"
        loadingLabel="Resolving..."
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// DismissAction (generic fallback)
// ---------------------------------------------------------------------------

export function DismissAction({
  transaction,
  onResolved,
}: {
  transaction: TransactionDetail;
  onResolved: () => void;
}) {
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);

  const handleDismiss = async () => {
    setLoading(true);
    try {
      await resolveAction(transaction.id, {
        action: "dismiss",
        note,
      });
      onResolved();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Dismiss failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <NoteField value={note} onChange={setNote} />
      <ActionButton
        onClick={handleDismiss}
        loading={loading}
        label="Dismiss (clear review flag)"
        loadingLabel="Dismissing..."
        className="w-full px-4 py-2 text-sm font-medium bg-gray-500 text-white rounded hover:bg-gray-600 disabled:opacity-50"
      />
    </div>
  );
}
