import { useEffect, useMemo, useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStatusMatrix } from "../api";
import type { StatusMatrixRow } from "../types";
import {
  DocCell,
  DotCell,
  MapCellView,
  MoonCell,
  RosterCell,
  LastRunCell,
  StackHead,
  GroupHead,
  MOON_PHASES,
} from "./matrixCells";

// ── row ────────────────────────────────────────────────────────────────────

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
                    const hasKids = c.jurisdictions.length > 0;
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
