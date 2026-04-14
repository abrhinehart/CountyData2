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
      className="form-control"
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
        "button-primary w-full justify-center"
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
    <div className="space-y-2">
      <input
        type="text"
        placeholder="Type to filter subdivisions..."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="form-control"
      />
      <select
        value={value ?? ""}
        onChange={(e) => {
          const id = e.target.value ? Number(e.target.value) : null;
          const sub = subdivisions?.find((s) => s.id === id) ?? null;
          onChange(id, sub);
        }}
        className="form-control min-h-[11rem]"
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
    <div className="flex flex-col gap-2 sm:flex-row">
      {phases.length > 0 && (
        <select
          value={phases.includes(value) ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          className="form-control flex-1"
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
        className="form-control flex-1"
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
      <h4 className="field-label">
        Assign Subdivision
      </h4>

      <div>
        <label className="field-label mb-1 block">Subdivision ({transaction.county})</label>
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
        <label className="field-label mb-1 block">Phase</label>
        <PhaseInput phases={phases} value={phase} onChange={setPhase} />
      </div>

      <div>
        <label className="field-label mb-1 block">Lots</label>
        <input
          type="number"
          min="1"
          value={lots}
          onChange={(e) => setLots(e.target.value)}
          className="form-control"
        />
      </div>

      <label className="chip-pill">
        <input
          type="checkbox"
          id="add-alias"
          checked={addAlias}
          onChange={(e) => setAddAlias(e.target.checked)}
          className="h-4 w-4 rounded border-stone-300"
        />
        <span className="text-sm text-[var(--text)]">
          Also add alias
        </span>
      </label>
      {addAlias && (
        <input
          type="text"
          value={aliasText}
          onChange={(e) => setAliasText(e.target.value)}
          placeholder="Alias text"
          className="form-control"
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
      <h4 className="field-label">
        Resolve Phase
      </h4>

      <div className="surface-muted rounded-[var(--radius-lg)] border border-[var(--border-subtle)] px-3 py-2.5 text-sm">
        <span className="detail-label">Current phase:</span>{" "}
        <span className="font-medium text-[var(--text)]">{transaction.phase ?? "(none)"}</span>
        {transaction.subdivision && (
          <>
            <br />
            <span className="detail-label">Subdivision:</span>{" "}
            <span className="font-medium text-[var(--text)]">{transaction.subdivision}</span>
          </>
        )}
      </div>

      <div className="flex gap-2">
        <button
          onClick={() => setMode("confirm")}
          className={`chip-pill flex-1 justify-center ${mode === "confirm" ? "active" : ""}`}
        >
          Confirm phase
        </button>
        <button
          onClick={() => setMode("override")}
          className={`chip-pill flex-1 justify-center ${mode === "override" ? "active" : ""}`}
        >
          Override phase
        </button>
      </div>

      {mode === "override" && (
        <div>
          <label className="field-label mb-1 block">New phase</label>
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
      <h4 className="field-label">
        Pick Subdivision
      </h4>

      {candidates.length > 0 && !showFull && (
        <div className="space-y-2">
          <label className="field-label">Candidates</label>
          {candidates.map((cand, i) => {
            const id = cand.subdivision_id ?? null;
            const name = cand.subdivision ?? cand.raw ?? "(unknown)";
            const isSelected = selectedId === id && id != null;
            return (
              <button
                key={i}
                onClick={() => handleCandidateSelect(cand)}
                className={`w-full rounded-[var(--radius-lg)] border px-3 py-2.5 text-left text-sm transition-colors ${
                  isSelected
                    ? "border-[rgba(29,78,216,0.24)] bg-[var(--accent-soft)] text-[var(--accent)]"
                    : "border-[var(--border-subtle)] bg-[var(--surface-muted)] text-[var(--text)] hover:bg-white"
                }`}
              >
                <span className="font-medium">{name}</span>
                {cand.phase && (
                  <span className="ml-2 text-[var(--text-muted)]">phase: {cand.phase}</span>
                )}
                {cand.details?.alias_source ? (
                  <span className="ml-2 text-xs text-[var(--text-soft)]">
                    alias: {String(cand.details.alias_source)}
                  </span>
                ) : null}
              </button>
            );
          })}
          <button
            onClick={() => setShowFull(true)}
            className="text-xs font-medium text-[var(--accent)] hover:underline"
          >
            Use full subdivision list instead
          </button>
        </div>
      )}

      {showFull && (
        <div>
          <div className="mb-1 flex items-center justify-between">
            <label className="field-label">Subdivision ({transaction.county})</label>
            {candidates.length > 0 && (
              <button
                onClick={() => setShowFull(false)}
                className="text-xs font-medium text-[var(--accent)] hover:underline"
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
        <label className="field-label mb-1 block">Phase</label>
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
      <h4 className="field-label">
        Pick Phase
      </h4>

      {transaction.subdivision && (
        <div className="surface-muted rounded-[var(--radius-lg)] border border-[var(--border-subtle)] px-3 py-2.5 text-sm">
          <span className="detail-label">Subdivision:</span>{" "}
          <span className="font-medium text-[var(--text)]">{transaction.subdivision}</span>
        </div>
      )}

      {candidates.length > 0 ? (
        <div className="space-y-2">
          <label className="field-label">Phase candidates</label>
          {candidates.map((cand) => (
            <label
              key={cand}
              className={`flex items-center gap-2 rounded-[var(--radius-lg)] border px-3 py-2.5 text-sm ${
                selected === cand
                  ? "border-[rgba(29,78,216,0.24)] bg-[var(--accent-soft)] text-[var(--accent)]"
                  : "border-[var(--border-subtle)] bg-[var(--surface-muted)] text-[var(--text)] hover:bg-white"
              }`}
            >
              <input
                type="radio"
                name="phase-candidate"
                value={cand}
                checked={selected === cand}
                onChange={() => setSelected(cand)}
                className="h-4 w-4 border-stone-300 text-[var(--accent)]"
              />
              <span className="font-medium">{cand}</span>
            </label>
          ))}
        </div>
      ) : (
        <div>
          <label className="field-label mb-1 block">Phase</label>
          <input
            type="text"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            placeholder="Enter phase"
            className="form-control"
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
        className="button-danger w-full justify-center"
      />
    </div>
  );
}
