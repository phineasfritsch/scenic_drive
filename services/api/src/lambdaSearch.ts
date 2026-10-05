/**
 * The budget search - a port of Sources/ScenicKit/Budget/LambdaSearch.swift (T-0248 R7, P-SAFE-04).
 *
 * Find the largest lambda whose route still fits inside fastest + budget. The bisection is correct only if
 * duration is monotone in lambda, which is an assumption about a routing engine and not a theorem, so ONLY
 * MEASURED, VERIFIED-FEASIBLE candidates are eligible to be returned: a non-monotone router costs accuracy and
 * never the ceiling. Violations are reported, never relied upon.
 *
 * Among feasible routes the LONGEST wins (the point is to spend the budget), and on a tie in duration the
 * LARGER lambda wins - it avoided more dull road at no cost in time.
 */

/** The top of the bracket; plan :116 and customModel.ts's LAMBDA_MAX. */
export const MAX_LAMBDA = 8;
/** Below this width two lambdas produce the same route and another request buys nothing. */
export const LAMBDA_TOLERANCE = 0.05;
/** The share of the budget that must be spent before the result counts as having used it. */
export const MIN_BUDGET_USE = 0.5;
export const DEFAULT_MAX_EVALUATIONS = 6;

export interface Sample {
  lambda: number;
  duration: number;
}

export interface BudgetOutcome {
  lambda: number;
  duration: number;
  ceiling: number;
  evaluations: number;
  usedBudget: boolean;
  monotonicityViolated: boolean;
}

export type BudgetRefusal = "not_a_duration" | "not_a_budget" | "router_nonsense" | "no_feasible_lambda";

export class BudgetError extends Error {
  readonly reason: BudgetRefusal;

  constructor(reason: BudgetRefusal, message: string) {
    super(message);
    this.reason = reason;
    this.name = "BudgetError";
  }
}

/** True if any measured pair has a larger lambda with a strictly shorter duration - every pair, because the
 *  bisection visits lambdas out of order and "consecutive in time" is not "adjacent in lambda". */
export function violatesMonotonicity(samples: Sample[]): boolean {
  for (const a of samples) {
    for (const b of samples) {
      if (b.lambda > a.lambda && b.duration < a.duration) return true;
    }
  }
  return false;
}

export async function searchLambda(fastest: number, budget: number, measure: (lambda: number) => Promise<number>,
  maxEvaluations = DEFAULT_MAX_EVALUATIONS): Promise<BudgetOutcome> {
  if (!Number.isFinite(fastest) || !(fastest > 0)) {
    throw new BudgetError("not_a_duration", `fastest must be a positive duration, got ${fastest}`);
  }
  if (!Number.isFinite(budget) || !(budget >= 0)) {
    throw new BudgetError("not_a_budget", `budget must be a non-negative duration, got ${budget}`);
  }
  const cap = Math.max(1, maxEvaluations);
  const ceiling = fastest + budget;
  let evaluations = 0;
  let best: Sample | null = null;
  const seen: Sample[] = [];

  const evaluate = async (lambda: number): Promise<number> => {
    const duration = await measure(lambda);
    evaluations += 1;
    if (!Number.isFinite(duration) || !(duration >= 0)) {
      throw new BudgetError("router_nonsense", `the router answered ${duration} s at lambda ${lambda}`);
    }
    seen.push({ lambda, duration });
    if (duration <= ceiling && (best === null || duration > best.duration ||
      (duration === best.duration && lambda > best.lambda))) {
      best = { lambda, duration };
    }
    return duration;
  };

  // lambda 0 is the fastest route by construction: the guaranteed-feasible floor, MEASURED, not assumed.
  await evaluate(0);

  let lo = 0;
  let hi = MAX_LAMBDA;
  while (evaluations < cap && hi - lo > LAMBDA_TOLERANCE) {
    const mid = lo + (hi - lo) / 2;
    const duration = await evaluate(mid);
    if (duration <= ceiling) lo = mid;
    else hi = mid;
  }

  const winner = best as Sample | null;
  if (winner === null) {
    const shortest = Math.min(...seen.map((s) => s.duration));
    throw new BudgetError("no_feasible_lambda",
      `no measured lambda fits the ceiling of ${ceiling} s (shortest ${shortest} s over ${evaluations} evaluations)`);
  }
  return {
    lambda: winner.lambda,
    duration: winner.duration,
    ceiling,
    evaluations,
    usedBudget: budget === 0 || winner.duration >= fastest + MIN_BUDGET_USE * budget,
    monotonicityViolated: violatesMonotonicity(seen),
  };
}
