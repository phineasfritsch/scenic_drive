/**
 * The rest of THIS drive (T-0319 R7): the one 2-dp origin through the pins not yet passed to the destination, at
 * the lambda the plan chose - never a bare origin-to-destination while the plan is remembered.
 *
 * Two requests: the fastest from here (it sets the ceiling), then one car_scenic request through the remaining
 * pins carrying buildCustomModel(lambda, closures). The closures guard may spend one re-request through the same
 * points. A route over fastest + budget is never returned: the answer is null and the caller plans afresh inside
 * the same reservation. There is no difference guard - the drive was ruled different when it was planned, and its
 * own continuation is meant to overlap it.
 */
import type { ClosuresFor, PathGuard } from "./closuresNearest";
import { buildCustomModel } from "./customModel";
import { appleMapsUrl } from "./appleMaps";
import { hazardsOf } from "./hazards";
import { MIN_BUDGET_USE } from "./lambdaSearch";
import type { LatLon } from "./latLon";
import { decisionPoints } from "./planWaypoints";
import { PLAN_UPSTREAM_COST } from "./quota";
import { durationSeconds } from "./routePath";
import { FAST_PROFILE, route, SCENIC_PROFILE, timeRunsField, type ScenicPlanResult } from "./scenicPlanner";
import type { GuardedFetch } from "./upstream";

export async function planReroute(call: GuardedFetch, routerBase: string, origin: LatLon, destination: LatLon,
  budgetSeconds: number, pins: LatLon[], lambda: number, closuresFor: ClosuresFor, returned: PathGuard,
): Promise<ScenicPlanResult | null> {
  let used = 0;
  const counted: GuardedFetch = (url, init) => {
    used += 1;
    return call(url, init);
  };
  const points = [origin, ...pins, destination];
  const closures = closuresFor(origin, destination);
  const fastest = await route(counted, routerBase, [origin, destination], FAST_PROFILE, undefined);
  const fastestSeconds = durationSeconds(fastest);
  const ceiling = fastestSeconds + budgetSeconds;

  const measured = await route(counted, routerBase, points, SCENIC_PROFILE, buildCustomModel(lambda, closures));
  if (!(durationSeconds(measured) <= ceiling)) return null;
  const chosen = await returned(measured, (p) => p.coordinates, origin, destination,
    used + 1 <= PLAN_UPSTREAM_COST ? async (swapped) => {
      const again = await route(counted, routerBase, points, SCENIC_PROFILE, buildCustomModel(lambda, swapped));
      return durationSeconds(again) <= ceiling ? again : null;
    } : null);
  const eta = durationSeconds(chosen);

  const waypoints = decisionPoints(chosen);
  return {
    route: { coordinates: chosen.coordinates, distance_m: chosen.distanceM },
    eta_s: eta,
    fastest_eta_s: fastestSeconds,
    ceiling_s: ceiling,
    budget_s: budgetSeconds,
    lambda,
    evaluations: 1,
    used_budget: budgetSeconds === 0 || eta >= fastestSeconds + MIN_BUDGET_USE * budgetSeconds,
    eta_is_estimate: true,
    hazards: hazardsOf(chosen),
    waypoints,
    apple_maps_url: appleMapsUrl(origin, destination, waypoints),
    ...timeRunsField(chosen),
  };
}
