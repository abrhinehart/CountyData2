import type { ModuleState, RosterState, MapCell } from "../types";

// ── glyph helpers ──────────────────────────────────────────────────────────

// 5 waxing lunar phases: new → full. Higher index = more filled.
export const MOON_PHASES = [
  "\uD83C\uDF11", // 🌑 new
  "\uD83C\uDF12", // 🌒 waxing crescent
  "\uD83C\uDF13", // 🌓 first quarter
  "\uD83C\uDF14", // 🌔 waxing gibbous
  "\uD83C\uDF15", // 🌕 full
];

export function moonByPct(pct: number | null): string | null {
  if (pct === null || pct === undefined) return null;
  const idx = Math.min(4, Math.max(0, Math.floor(pct * 5)));
  return MOON_PHASES[idx];
}

// Map map-age (days) to 5 phases: fresh -> full (🌕, idx 4), stale -> new (🌑, idx 0).
// Buckets: 0-30d, 30-60d, 60-120d, 120-240d, 240+d.
export function moonByAge(days: number | null): string | null {
  if (days === null || days === undefined) return null;
  if (days <= 30) return MOON_PHASES[4];
  if (days <= 60) return MOON_PHASES[3];
  if (days <= 120) return MOON_PHASES[2];
  if (days <= 240) return MOON_PHASES[1];
  return MOON_PHASES[0];
}

export function moduleDot(state: ModuleState): string {
  switch (state) {
    case "green":  return "bg-emerald-400";
    case "yellow": return "bg-amber-300";
    case "red":    return "bg-rose-400";
    default:       return "bg-gray-700";
  }
}

export function lastRunDot(days: number | null): string {
  if (days === null) return "bg-gray-700";
  if (days <= 14)  return "bg-emerald-400";
  if (days <= 60)  return "bg-amber-300";
  return "bg-rose-400";
}

// ── header cells ───────────────────────────────────────────────────────────

export function StackHead({ label, title }: { label: string; title: string }) {
  return (
    <th
      title={title}
      className="align-bottom w-14 px-1 py-2 border-l border-gray-700 bg-gray-900 text-[11px] font-medium text-gray-200 leading-tight text-center"
    >
      <div className="break-words hyphens-none">
        {label}
      </div>
    </th>
  );
}

export function GroupHead({ label, span, tone }: { label: string; span: number; tone?: string }) {
  return (
    <th
      colSpan={span}
      className={
        "px-2 py-1 text-[11px] font-semibold uppercase tracking-wide text-center border-l border-gray-700 " +
        (tone || "bg-gray-800 text-gray-200")
      }
    >
      {label}
    </th>
  );
}

// ── cell renderers ─────────────────────────────────────────────────────────

export function DotCell({ state, title }: { state: ModuleState; title: string }) {
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={title}>
      <span className={"inline-block w-3 h-3 rounded-full " + moduleDot(state)} />
    </td>
  );
}

export function MapCellView({ cell, title }: { cell: MapCell | null; title: string }) {
  const glyph = cell ? moonByAge(cell.age_days) : null;
  const tip = cell
    ? `${title}: ${cell.filename} (${Math.round(cell.age_days)}d old)`
    : `${title}: no map`;
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={tip}>
      {glyph ? (
        <span className="text-base leading-none">{glyph}</span>
      ) : (
        <span className="text-gray-600">{"\u00B7"}</span>
      )}
    </td>
  );
}

export function MoonCell({ pct, title }: { pct: number | null; title: string }) {
  const glyph = moonByPct(pct);
  const tip = pct === null ? `${title}: n/a` : `${title}: ${(pct * 100).toFixed(1)}%`;
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={tip}>
      {glyph ? (
        <span className="text-base leading-none">{glyph}</span>
      ) : (
        <span className="text-gray-600">{"\u00B7"}</span>
      )}
    </td>
  );
}

export function RosterCell({ state }: { state: RosterState }) {
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={`Commissioner roster: ${state}`}>
      {state === "yes"  && <span className="text-emerald-400">{"\u2713"}</span>}
      {state === "no"   && <span className="text-rose-400">{"\u2717"}</span>}
      {state === "na"   && <span className="text-gray-600">{"\u2014"}</span>}
    </td>
  );
}

export function LastRunCell({ days }: { days: number | null }) {
  const tip = days === null ? "No activity recorded" : `Last activity: ${Math.round(days)}d ago`;
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={tip}>
      <span className={"inline-block w-3 h-3 rounded-full " + lastRunDot(days)} />
    </td>
  );
}

export function DocCell({ doc }: { doc: boolean }) {
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={doc ? "Registry entry present" : "Registry entry missing/stub"}>
      {doc ? (
        <span className="text-emerald-400">{"\u2713"}</span>
      ) : (
        <span className="text-gray-600">{"\u00B7"}</span>
      )}
    </td>
  );
}
