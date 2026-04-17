import { useEffect, useMemo, useState, Fragment } from "react";
import { useQuery } from "@tanstack/react-query";
import { getStatusMatrix } from "../api";
import {
  DocCell,
  DotCell,
  MapCellView,
  RosterCell,
  LastRunCell,
  StackHead,
  GroupHead,
} from "./matrixCells";

// Cities matrix — 8-column compact view grouped by state → county → cities.

export default function CitiesMatrix() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["status-matrix"],
    queryFn: getStatusMatrix,
  });

  const [openStates, setOpenStates] = useState<Record<string, boolean>>(() => {
    try {
      const raw = localStorage.getItem("health:cities-matrix:states");
      if (raw) return JSON.parse(raw);
    } catch {
      /* ignore */
    }
    return {};
  });

  useEffect(() => {
    try {
      localStorage.setItem(
        "health:cities-matrix:states",
        JSON.stringify(openStates),
      );
    } catch {
      /* ignore */
    }
  }, [openStates]);

  const isStateOpen = (s: string) => openStates[s] !== false; // default open

  // Pre-filter states/counties down to those that actually have cities.
  const stateGroups = useMemo(() => {
    if (!data) return [];
    return data.states
      .map((st) => ({
        state: st.state,
        counties: st.counties.filter((c) => (c.cities?.length ?? 0) > 0),
      }))
      .filter((st) => st.counties.length > 0);
  }, [data]);

  const totals = useMemo(() => {
    let cityRows = 0;
    stateGroups.forEach((st) =>
      st.counties.forEach((c) => {
        cityRows += c.cities?.length ?? 0;
      }),
    );
    return { cityRows, stateCount: stateGroups.length };
  }, [stateGroups]);

  if (isLoading) return <p className="text-sm text-gray-400">Loading cities matrix...</p>;
  if (error) return <p className="text-sm text-rose-400">Failed to load cities matrix.</p>;
  if (!data) return null;
  if (stateGroups.length === 0) {
    return <p className="text-sm text-gray-400">No cities tracked.</p>;
  }

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-x-auto text-gray-100">
      <table className="text-sm border-collapse">
        <thead>
          <tr>
            <th rowSpan={2} className="px-3 py-2 text-left align-bottom font-medium text-gray-200 bg-gray-900 border-b border-gray-700 min-w-[220px]">
              City
              <span className="block text-[10px] font-normal text-gray-500">
                {totals.cityRows} cities / {totals.stateCount} states
              </span>
            </th>
            <GroupHead label="Profile"  span={1} tone="bg-indigo-900/60 text-indigo-200" />
            <GroupHead label="Modules"  span={2} tone="bg-emerald-900/60 text-emerald-200" />
            <GroupHead label="API Maps" span={2} tone="bg-sky-900/60 text-sky-200" />
            <GroupHead label="Ops"      span={2} tone="bg-amber-900/60 text-amber-200" />
          </tr>
          <tr>
            <StackHead label="Doc"      title="Onboarding doc / city-registry entry" />
            <StackHead label="PT"       title="Permit Tracker" />
            <StackHead label="CR"       title="Commission Radar" />
            <StackHead label="PT Map"   title="PT API map" />
            <StackHead label="CR Map"   title="CR API map" />
            <StackHead label="Roster"   title="Commissioner roster known" />
            <StackHead label="Last Run" title="Days since last successful activity" />
          </tr>
        </thead>
        <tbody>
          {stateGroups.map((st) => {
            const open = isStateOpen(st.state);
            const cityCount = st.counties.reduce(
              (n, c) => n + (c.cities?.length ?? 0),
              0,
            );
            return (
              <Fragment key={st.state}>
                <tr
                  className="bg-indigo-950/80 hover:bg-indigo-900/80 cursor-pointer select-none"
                  onClick={() => setOpenStates((prev) => ({ ...prev, [st.state]: !open }))}
                >
                  <td colSpan={8} className="px-3 py-1 text-sm font-semibold text-indigo-200">
                    {st.state}
                    <span className="text-gray-400 font-normal ml-2">
                      ({cityCount} cities across {st.counties.length} counties
                      {!open ? " — collapsed" : ""})
                    </span>
                  </td>
                </tr>
                {open &&
                  st.counties.map((c) => (
                    <Fragment key={`${st.state}:${c.county}`}>
                      <tr className="bg-gray-800 font-medium">
                        <td
                          colSpan={8}
                          className="pl-4 pr-3 py-1 whitespace-nowrap text-gray-100"
                        >
                          {c.county}
                          <span className="ml-2 text-[10px] text-gray-500">
                            {c.cities.length} {c.cities.length === 1 ? "city" : "cities"}
                          </span>
                        </td>
                      </tr>
                      {c.cities.map((city) => (
                        <tr
                          key={city.id}
                          className="bg-gray-900 hover:bg-gray-800 text-gray-300"
                        >
                          <td className="px-3 py-1 whitespace-nowrap pl-10">
                            {city.name}
                            {city.type && (
                              <span className="ml-2 text-[10px] uppercase tracking-wide text-gray-500">
                                {city.type}
                              </span>
                            )}
                          </td>
                          <DocCell doc={city.doc} />
                          <DotCell state={city.pt} title="PT (Permit Tracker)" />
                          <DotCell state={city.cr} title="CR (Commission Radar)" />
                          <MapCellView cell={city.pt_map} title="PT map" />
                          <MapCellView cell={city.cr_map} title="CR map" />
                          <RosterCell state={city.roster} />
                          <LastRunCell days={city.last_run_days} />
                        </tr>
                      ))}
                    </Fragment>
                  ))}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
