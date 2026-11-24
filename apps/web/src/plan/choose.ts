import type { Corridor, RouteOption } from "./types";

/** routeScore.ts HONEST_FAILURE_THRESHOLD: below this a route has no scenic middle worth recommending. */
export const HONEST_FAILURE_THRESHOLD = 0.45;
export const MAX_BUDGET_MINUTES = 30;

export interface OptionView {
  route: RouteOption;
  extraS: number;
  /** The product invariant: an offered route's ETA is at most fastest + budget. */
  fitsBudget: boolean;
  recommended: boolean;
}

export interface Choice {
  recommended: RouteOption;
  options: OptionView[];
  /** True when nothing inside the budget clears the honest-failure bar, so the fastest route is the answer. */
  honestFailure: boolean;
}

/**
 * The highest-scoring route whose ETA fits the extra-time budget. The budget is a CEILING:
 * a route over fastest + budget is never recommended, however pretty it is.
 */
export function choose(corridor: Corridor, budgetMinutes: number): Choice {
  const ceilingS = corridor.fastest.timeS + Math.max(0, budgetMinutes) * 60;
  const fitting = corridor.alternatives.filter((r) => r.timeS <= ceilingS);
  const best = fitting.reduce<RouteOption | null>(
    (top, r) => (top === null || r.score.value > top.score.value ? r : top),
    null,
  );
  const honestFailure = best === null || best.score.value < HONEST_FAILURE_THRESHOLD ||
    best.score.value <= corridor.fastest.score.value;
  const recommended = honestFailure ? corridor.fastest : best!;
  const options = [corridor.fastest, ...corridor.alternatives].map((route) => ({
    route,
    extraS: route.timeS - corridor.fastest.timeS,
    fitsBudget: route.timeS <= ceilingS,
    recommended: route.id === recommended.id,
  }));
  return { recommended, options, honestFailure };
}

/** The smallest budget, in whole minutes, that reaches the corridor's best-scoring route. */
export function budgetForBest(corridor: Corridor): number {
  const best = corridor.alternatives.reduce((top, r) => (r.score.value > top.score.value ? r : top), corridor.fastest);
  return Math.min(MAX_BUDGET_MINUTES, Math.ceil((best.timeS - corridor.fastest.timeS) / 60));
}
