/**
 * The honest failure (T-0332): the route /plan would ship scores below RouteScore's 0.45 - no scenic middle worth
 * showing - so the Worker says "not much pretty within N minutes of this drive" instead of selling it as scenic.
 *
 * The answer ships NO route (R4): nothing to drive, so the budget ceiling (P-SAFE-04) is untouched. It carries the
 * plan's two offers:
 *   - more time: budget + 40 minutes, a number the client re-plans with - null when that is past MAX_BUDGET_MINUTES;
 *   - all back roads: the route at MAX_LAMBDA, shown with its REAL ETA (which may exceed fastest + budget - it is an
 *     offer, not an answer), and only when that route itself scores >= 0.45 (R5): a dull back-roads offer would
 *     repeat the dishonesty this answer exists to avoid. A router refusal of that one request is no offer.
 */
import { MAX_BUDGET_MINUTES } from "./planRequest";
import { isHonestFailure, routeScoreOf } from "./routeScore";
import { durationSeconds, RouteError, type RoutePath } from "./routePath";

/** The plan's "+40". */
export const MORE_TIME_MINUTES = 40;

export class HonestFailure extends Error {
  /** The back-roads route's own ETA in seconds, or null when there is no back-roads route worth offering. */
  readonly backRoadsEtaSeconds: number | null;

  constructor(backRoadsEtaSeconds: number | null) {
    super("the chosen route scores below the honest-failure threshold");
    this.backRoadsEtaSeconds = backRoadsEtaSeconds;
    this.name = "HonestFailure";
  }
}

/** The back-roads ETA: `measure` routes at MAX_LAMBDA; a refusal, or a route that is itself dull, is no offer. */
export async function backRoadsEta(measure: (() => Promise<RoutePath>) | null): Promise<number | null> {
  if (measure === null) return null;
  let path: RoutePath;
  try {
    path = await measure();
  } catch (error) {
    if (error instanceof RouteError) return null;
    throw error;
  }
  return isHonestFailure(routeScoreOf(path)) ? null : durationSeconds(path);
}

/** The 422 body. `budgetMinutes` is the request's own, echoed. */
export function honestFailureBody(budgetMinutes: number, failure: HonestFailure): Record<string, unknown> {
  const more = budgetMinutes + MORE_TIME_MINUTES;
  return {
    error: "nothing_pretty",
    budget_minutes: budgetMinutes,
    more_time_minutes: more <= MAX_BUDGET_MINUTES ? more : null,
    back_roads_eta_s: failure.backRoadsEtaSeconds,
  };
}
