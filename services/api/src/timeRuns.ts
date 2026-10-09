/**
 * T-0342 R2: the shipped route's per-edge free-flow times - GraphHopper's details=time runs - as the /plan answer
 * carries them in `time_runs`, so the device can retime the route edge by edge (Sources/ScenicKit/Traffic,
 * CorridorRoute). Read by tripPlanner.edgesOf's rule: the runs tile route.coordinates edge for edge - the first from
 * vertex 0, each from the previous run's end, each to past its from, the last to the last vertex - every value a
 * whole, safe, non-negative count of milliseconds and some of them above zero. Anything else is null and the answer
 * omits the field: the runs only feed the device's badge, and without them the badge stays on.
 */
import type { RoutePath } from "./routePath";

export interface TimeRun {
  from: number;
  to: number;
  ms: number;
}

export const TIME_DETAIL = "time";

export function timeRunsOf(path: RoutePath): TimeRun[] | null {
  const runs = path.details[TIME_DETAIL] ?? [];
  if (runs.length === 0) return null;
  const answer: TimeRun[] = [];
  let at = 0;
  for (const run of runs) {
    if (run.from !== at || !(run.to > run.from)) return null;
    if (typeof run.value !== "number" || !Number.isSafeInteger(run.value) || run.value < 0) return null;
    answer.push({ from: run.from, to: run.to, ms: run.value });
    at = run.to;
  }
  if (at !== path.coordinates.length - 1) return null;
  if (!answer.some((run) => run.ms > 0)) return null;
  return answer;
}
