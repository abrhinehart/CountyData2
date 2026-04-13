import type { CommissionAction } from "../types";

/**
 * Entitlement pipeline stages:
 * 1. Planning/Zoning Board — 1 reading (recommendation)
 * 2. City Commission 1st Reading — first reading
 * 3. City Commission 2nd Reading — final vote
 *
 * Derives the current position from the project's entitlement actions
 * by inspecting approval_type, reading_number, and outcome.
 */

interface Stage {
  label: string;
  status: "completed" | "active" | "upcoming";
  detail?: string;
}

function deriveStages(actions: CommissionAction[]): Stage[] {
  // Categorize actions
  const pzActions = actions.filter(
    (a) => a.approval_type === "zoning" || a.approval_type === "land_use" || a.approval_type === "conditional_use"
  );
  const ccActions = actions.filter(
    (a) => a.approval_type === "development_review" || a.approval_type === "subdivision" || a.approval_type === "annexation"
  );

  // Check PZ board recommendation
  const pzOutcome = pzActions.find((a) => a.outcome)?.outcome ?? "";
  const pzDone = pzActions.length > 0 && !!pzOutcome;

  // Check CC first reading
  const firstReading = ccActions.find((a) => a.reading_number === "first");
  const firstDone = !!firstReading?.outcome;

  // Check CC second/final reading
  const secondReading = ccActions.find((a) => a.reading_number === "second" || a.reading_number === "final");
  const secondDone = !!secondReading?.outcome;

  return [
    {
      label: "P&Z Board",
      status: pzDone ? "completed" : pzActions.length > 0 ? "active" : "upcoming",
      detail: pzDone ? pzOutcome : pzActions.length > 0 ? "Pending" : undefined,
    },
    {
      label: "CC 1st Reading",
      status: firstDone ? "completed" : firstReading ? "active" : pzDone ? "upcoming" : "upcoming",
      detail: firstDone ? firstReading?.outcome : firstReading ? "Scheduled" : undefined,
    },
    {
      label: "CC 2nd Reading",
      status: secondDone ? "completed" : secondReading ? "active" : firstDone ? "upcoming" : "upcoming",
      detail: secondDone ? secondReading?.outcome : secondReading ? "Scheduled" : undefined,
    },
  ];
}

export default function EntitlementProgress({ actions }: { actions: CommissionAction[] }) {
  if (actions.length === 0) return null;

  const stages = deriveStages(actions);

  return (
    <div className="flex items-center gap-1 w-full">
      {stages.map((stage, i) => (
        <div key={stage.label} className="flex items-center flex-1 min-w-0">
          {/* Step node */}
          <div className="flex flex-col items-center gap-0.5">
            <div
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0
                ${stage.status === "completed" ? "bg-green-500 text-white" :
                  stage.status === "active" ? "bg-blue-500 text-white animate-pulse" :
                  "bg-gray-200 text-gray-400"}`}
            >
              {stage.status === "completed" ? "\u2713" : i + 1}
            </div>
            <span className="text-[10px] text-gray-500 text-center leading-tight whitespace-nowrap">
              {stage.label}
            </span>
            {stage.detail && (
              <span className={`text-[9px] font-medium text-center leading-tight
                ${stage.status === "completed" ? "text-green-600" :
                  stage.status === "active" ? "text-blue-600" : "text-gray-400"}`}>
                {stage.detail}
              </span>
            )}
          </div>

          {/* Connector line */}
          {i < stages.length - 1 && (
            <div className={`flex-1 h-0.5 mx-1 rounded ${
              stage.status === "completed" ? "bg-green-400" : "bg-gray-200"
            }`} />
          )}
        </div>
      ))}
    </div>
  );
}
