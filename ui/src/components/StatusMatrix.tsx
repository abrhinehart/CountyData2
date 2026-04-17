import { useEffect, useMemo, useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStatusMatrix } from "../api";
import type {
  StatusMatrixRow,
  ModuleState,
  RosterState,
  MapCell,
} from "../types";

// ── glyph helpers ──────────────────────────────────────────────────────────

// 5 waxing lunar phases: new → full. Higher index = more filled.
const MOON_PHASES = [
  "\uD83C\uDF11", // 🌑 new
  "\uD83C\uDF12", // 🌒 waxing crescent
  "\uD83C\uDF13", // 🌓 first quarter
  "\uD83C\uDF14", // 🌔 waxing gibbous
  "\uD83C\uDF15", // 🌕 full
];

function moonByPct(pct: number | null): string | null {
  if (pct === null || pct === undefined) return null;
  const idx = Math.min(4, Math.max(0, Math.floor(pct * 5)));
  return MOON_PHASES[idx];
}

// Map map-age (days) to 5 phases: fresh -> full (🌕, idx 4), stale -> new (🌑, idx 0).
// Buckets: 0-30d, 30-60d, 60-120d, 120-240d, 240+d.
function moonByAge(days: number | null): string | null {
  if (days === null || days === undefined) return null;
  if (days <= 30) return MOON_PHASES[4];
  if (days <= 60) return MOON_PHASES[3];
  if (days <= 120) return MOON_PHASES[2];
  if (days <= 240) return MOON_PHASES[1];
  return MOON_PHASES[0];
}

function moduleDot(state: ModuleState): string {
  switch (state) {
    case "green":  return "bg-emerald-400";
    case "yellow": return "bg-amber-300";
    case "red":    return "bg-rose-400";
    default:       return "bg-gray-700";
  }
}

function lastRunDot(days: number | null): string {
  if (days === null) return "bg-gray-700";
  if (days <= 14)  return "bg-emerald-400";
  if (days <= 60)  return "bg-amber-300";
  return "bg-rose-400";
}

// ── header cells ───────────────────────────────────────────────────────────

function StackHead({ label, title }: { label: string; title: string }) {
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

function GroupHead({ label, span, tone }: { label: string; span: number; tone?: string }) {
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

function DotCell({ state, title }: { state: ModuleState; title: string }) {
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={title}>
      <span className={"inline-block w-3 h-3 rounded-full " + moduleDot(state)} />
    </td>
  );
}

function MapCellView({ cell, title }: { cell: MapCell | null; title: string }) {
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

function MoonCell({ pct, title }: { pct: number | null; title: string }) {
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

function RosterCell({ state }: { state: RosterState }) {
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={`Commissioner roster: ${state}`}>
      {state === "yes"  && <span className="text-emerald-400">{"\u2713"}</span>}
      {state === "no"   && <span className="text-rose-400">{"\u2717"}</span>}
      {state === "na"   && <span className="text-gray-600">{"\u2014"}</span>}
    </td>
  );
}

function LastRunCell({ days }: { days: number | null }) {
  const tip = days === null ? "No activity recorded" : `Last activity: ${Math.round(days)}d ago`;
  return (
    <td className="w-14 px-2 py-1 text-center border-l border-gray-800" title={tip}>
      <span className={"inline-block w-3 h-3 rounded-full " + lastRunDot(days)} />
    </td>
  );
}

function DocCell({ doc }: { doc: boolean }) {
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

// ── row ────────────────────────────────────────────────────────────────────

// ── cities sub-table (compact: 8 cols) ────────────────────────────────────

function CitySubTable({ cities }: { cities: StatusMatrixRow[] }) {
  if (!cities.length) return null;
  return (
    <tr className="bg-gray-950">
      <td colSpan={14} className="px-3 py-2 border-l-4 border-sky-900/60">
        <div className="text-[11px] uppercase tracking-wide text-sky-300/80 mb-1">
          Cities ({cities.length})
        </div>
        <table className="text-xs border-collapse w-full">
          <thead>
            <tr className="text-gray-400">
              <th className="text-left pl-2 pr-3 py-1 font-medium min-w-[200px]">Name</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">Doc</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">PT</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">CR</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">PT Map</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">CR Map</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">Roster</th>
              <th className="px-2 py-1 font-medium border-l border-gray-800">Last Run</th>
            </tr>
          </thead>
          <tbody>
            {cities.map((c) => (
              <tr key={c.id} className="hover:bg-gray-900 text-gray-300">
                <td className="pl-2 pr-3 py-1 whitespace-nowrap">
                  {c.name}
                  {c.type && (
                    <span className="ml-2 text-[10px] uppercase tracking-wide text-gray-500">
                      {c.type}
                    </span>
                  )}
                </td>
                <DocCell doc={c.doc} />
                <DotCell state={c.pt} title="PT (Permit Tracker)" />
                <DotCell state={c.cr} title="CR (Commission Radar)" />
                <MapCellView cell={c.pt_map} title="PT map" />
                <MapCellView cell={c.cr_map} title="CR map" />
                <RosterCell state={c.roster} />
                <LastRunCell days={c.last_run_days} />
              </tr>
            ))}
          </tbody>
        </table>
      </td>
    </tr>
  );
}

function MatrixRow({ r, indent }: { r: StatusMatrixRow; indent: boolean }) {
  return (
    <tr className={indent ? "bg-gray-900 hover:bg-gray-800" : "bg-gray-800 hover:bg-gray-700 font-medium"}>
      <td className={"px-3 py-1 whitespace-nowrap " + (indent ? "pl-10 text-gray-300" : "text-gray-100")}>
        {r.name}
        {r.type && r.type !== "county" && (
          <span className="ml-2 text-[10px] uppercase tracking-wide text-gray-500">{r.type}</span>
        )}
      </td>
      <DocCell doc={r.doc} />
      <DotCell state={r.cd2} title="CD2 (Sales)" />
      <DotCell state={r.bi}  title="BI (Builder Inventory)" />
      <DotCell state={r.pt}  title="PT (Permit Tracker)" />
      <DotCell state={r.cr}  title="CR (Commission Radar)" />
      <MapCellView cell={r.cd2_map} title="CD2 map" />
      <MapCellView cell={r.bi_map}  title="BI map" />
      <MapCellView cell={r.pt_map}  title="PT map" />
      <MapCellView cell={r.cr_map}  title="CR map" />
      <MoonCell pct={r.sub_pct}    title="Subdivision geom coverage" />
      <MoonCell pct={r.parcel_pct} title="Parcel geom coverage" />
      <RosterCell state={r.roster} />
      <LastRunCell days={r.last_run_days} />
    </tr>
  );
}

// ── main component ─────────────────────────────────────────────────────────

export default function StatusMatrix() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["status-matrix"],
    queryFn: getStatusMatrix,
  });

  const [openStates, setOpenStates] = useState<Record<string, boolean>>(() => {
    try {
      const raw = localStorage.getItem("health:matrix:states");
      if (raw) return JSON.parse(raw);
    } catch {
      /* ignore */
    }
    return {};
  });
  const [openCounties, setOpenCounties] = useState<Record<string, boolean>>(() => {
    try {
      const raw = localStorage.getItem("health:matrix:counties");
      if (raw) return JSON.parse(raw);
    } catch {
      /* ignore */
    }
    return {};
  });

  useEffect(() => {
    try {
      localStorage.setItem("health:matrix:states", JSON.stringify(openStates));
    } catch {
      /* ignore */
    }
  }, [openStates]);
  useEffect(() => {
    try {
      localStorage.setItem("health:matrix:counties", JSON.stringify(openCounties));
    } catch {
      /* ignore */
    }
  }, [openCounties]);

  const isStateOpen = (s: string) => openStates[s] !== false; // default open
  const isCountyOpen = (key: string) => !!openCounties[key];  // default closed

  const totals = useMemo(() => {
    let countyRows = 0, jurRows = 0, cityRows = 0;
    data?.states.forEach((st) =>
      st.counties.forEach((c) => {
        countyRows += 1;
        jurRows += c.jurisdictions.length;
        cityRows += c.cities?.length ?? 0;
      }),
    );
    return { countyRows, jurRows, cityRows };
  }, [data]);

  if (isLoading) return <p className="text-sm text-gray-400">Loading status matrix...</p>;
  if (error) return <p className="text-sm text-rose-400">Failed to load status matrix.</p>;
  if (!data) return null;

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-x-auto text-gray-100">
      <table className="text-sm border-collapse">
        <thead>
          <tr>
            <th rowSpan={2} className="px-3 py-2 text-left align-bottom font-medium text-gray-200 bg-gray-900 border-b border-gray-700 min-w-[220px]">
              Jurisdiction
              <span className="block text-[10px] font-normal text-gray-500">
                {totals.countyRows} counties / {totals.jurRows} county bodies / {totals.cityRows} cities
              </span>
            </th>
            <GroupHead label="Doc"      span={1} tone="bg-indigo-900/60 text-indigo-200" />
            <GroupHead label="Modules"  span={4} tone="bg-emerald-900/60 text-emerald-200" />
            <GroupHead label="API Maps" span={4} tone="bg-sky-900/60 text-sky-200" />
            <GroupHead label="Geom"     span={2} tone="bg-violet-900/60 text-violet-200" />
            <GroupHead label="Ops"      span={2} tone="bg-amber-900/60 text-amber-200" />
          </tr>
          <tr>
            <StackHead label="Doc"      title="Onboarding doc / county-registry entry" />
            <StackHead label="CD2"      title="Sales" />
            <StackHead label="BI"       title="Builder Inventory" />
            <StackHead label="PT"       title="Permit Tracker" />
            <StackHead label="CR"       title="Commission Radar" />
            <StackHead label="CD2 Map"  title="CD2 API map" />
            <StackHead label="BI Map"   title="BI API map" />
            <StackHead label="PT Map"   title="PT API map" />
            <StackHead label="CR Map"   title="CR API map" />
            <StackHead label="Subdiv"   title="Subdivision geometry coverage" />
            <StackHead label="Parcel"   title="Parcel geometry coverage" />
            <StackHead label="Roster"   title="Commissioner roster known" />
            <StackHead label="Last Run" title="Days since last successful activity" />
          </tr>
        </thead>
        <tbody>
          {data.states.map((st) => {
            const open = isStateOpen(st.state);
            return (
              <Fragment key={st.state}>
                <tr
                  className="bg-indigo-950/80 hover:bg-indigo-900/80 cursor-pointer select-none"
                  onClick={() => setOpenStates((prev) => ({ ...prev, [st.state]: !open }))}
                >
                  <td colSpan={14} className="px-3 py-1 text-sm font-semibold text-indigo-200">
                    {st.state}
                    <span className="text-gray-400 font-normal ml-2">
                      ({st.counties.length} counties{!open ? " — collapsed" : ""})
                    </span>
                  </td>
                </tr>
                {open &&
                  st.counties.map((c) => {
                    const countyKey = `${st.state}:${c.county}`;
                    const cOpen = isCountyOpen(countyKey);
                    const cities = c.cities ?? [];
                    const hasKids = c.jurisdictions.length > 0 || cities.length > 0;
                    return (
                      <Fragment key={countyKey}>
                        <tr
                          className={
                            "bg-gray-800 hover:bg-gray-700 font-medium " +
                            (hasKids ? "cursor-pointer" : "")
                          }
                          onClick={() =>
                            hasKids &&
                            setOpenCounties((prev) => ({ ...prev, [countyKey]: !cOpen }))
                          }
                        >
                          <td className="pl-4 pr-3 py-1 whitespace-nowrap text-gray-100">
                            {c.county}
                            {hasKids && (
                              <span className="ml-2 text-[10px] text-gray-500">
                                +{c.jurisdictions.length}
                                {cities.length > 0 && ` / ${cities.length} cities`}
                                {cOpen ? "" : " \u00B7 click"}
                              </span>
                            )}
                          </td>
                          <DocCell doc={c.row.doc} />
                          <DotCell state={c.row.cd2} title="CD2 (Sales)" />
                          <DotCell state={c.row.bi}  title="BI (Builder Inventory)" />
                          <DotCell state={c.row.pt}  title="PT (Permit Tracker)" />
                          <DotCell state={c.row.cr}  title="CR (Commission Radar)" />
                          <MapCellView cell={c.row.cd2_map} title="CD2 map" />
                          <MapCellView cell={c.row.bi_map}  title="BI map" />
                          <MapCellView cell={c.row.pt_map}  title="PT map" />
                          <MapCellView cell={c.row.cr_map}  title="CR map" />
                          <MoonCell pct={c.row.sub_pct}    title="Subdivision geom" />
                          <MoonCell pct={c.row.parcel_pct} title="Parcel geom" />
                          <RosterCell state={c.row.roster} />
                          <LastRunCell days={c.row.last_run_days} />
                        </tr>
                        {cOpen &&
                          c.jurisdictions.map((j) => (
                            <MatrixRow key={j.id} r={j} indent />
                          ))}
                        {cOpen && cities.length > 0 && (
                          <CitySubTable cities={cities} />
                        )}
                      </Fragment>
                    );
                  })}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      <div className="text-[11px] text-gray-400 px-3 py-2 border-t border-gray-700 flex flex-wrap gap-x-4 gap-y-1">
        <span><span className="inline-block w-2 h-2 rounded-full bg-emerald-400 mr-1" /> active / fresh</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-amber-300 mr-1" /> stale / partial</span>
        <span><span className="inline-block w-2 h-2 rounded-full bg-rose-400 mr-1" /> missing / broken</span>
        <span className="text-gray-500">Moons (coverage): {MOON_PHASES.join(" ")} &nbsp;0→100%</span>
        <span className="text-gray-500">Moons (map age): full = fresh &middot; new = stale</span>
      </div>
    </div>
  );
}
