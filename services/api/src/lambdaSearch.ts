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

function checkBudget(budget: number): void {
  if (!Number.isFinite(budget) || !(budget >= 0)) {
    throw new BudgetError("not_a_budget", `budget must be a non-negative duration, got ${budget}`);
  }
}

/** fastest + budget, refusing a fastest that is not a positive duration FIRST and then a budget that is not one. */
function ceilingOf(fastest: number, budget: number): number {
  if (!Number.isFinite(fastest) || !(fastest > 0)) {
    throw new BudgetError("not_a_duration", `fastest must be a positive duration, got ${fastest}`);
  }
  checkBudget(budget);
  return fastest + budget;
}

const usable = (duration: number) => Number.isFinite(duration) && duration >= 0;

/** The samples one search has recorded, and its outcome - a function of the SET of samples, never their order:
 *  the longest feasible wins, a tie goes to the larger lambda (no lambda is measured twice). */
function samplesUnder(fastest: number, budget: number, ceiling: number) {
  let best: Sample | null = null;
  const seen: Sample[] = [];
  return {
    get evaluations() {
      return seen.length;
    },
    record(lambda: number, duration: number): number {
      if (!usable(duration)) {
        throw new BudgetError("router_nonsense", `the router answered ${duration} s at lambda ${lambda}`);
      }
      seen.push({ lambda, duration });
      if (duration <= ceiling && (best === null || duration > best.duration ||
        (duration === best.duration && lambda > best.lambda))) {
        best = { lambda, duration };
      }
      return duration;
    },
    outcome(): BudgetOutcome {
      const winner = best as Sample | null;
      if (winner === null) {
        const shortest = Math.min(...seen.map((s) => s.duration));
        throw new BudgetError("no_feasible_lambda",
          `no measured lambda fits the ceiling of ${ceiling} s (shortest ${shortest} s over ${seen.length} evaluations)`);
      }
      return {
        lambda: winner.lambda,
        duration: winner.duration,
        ceiling,
        evaluations: seen.length,
        usedBudget: budget === 0 || winner.duration >= fastest + MIN_BUDGET_USE * budget,
        monotonicityViolated: violatesMonotonicity(seen),
      };
    },
  };
}

/** The next bisection midpoint after `steps` midpoints narrowed the bracket to [lo, hi], or null when the search
 *  is done: lambda 0 plus the midpoints may not pass the cap, and below the tolerance another request buys nothing. */
function nextMidpoint(lo: number, hi: number, steps: number, cap: number): number | null {
  return 1 + steps < cap && hi - lo > LAMBDA_TOLERANCE ? lo + (hi - lo) / 2 : null;
}

export async function searchLambda(fastest: number, budget: number, measure: (lambda: number) => Promise<number>,
  maxEvaluations = DEFAULT_MAX_EVALUATIONS): Promise<BudgetOutcome> {
  const ceiling = ceilingOf(fastest, budget);
  const cap = Math.max(1, maxEvaluations);
  const samples = samplesUnder(fastest, budget, ceiling);

  // lambda 0 is the fastest route by construction: the guaranteed-feasible floor, MEASURED, not assumed.
  samples.record(0, await measure(0));

  let lo = 0;
  let hi = MAX_LAMBDA;
  for (let steps = 0, mid = nextMidpoint(lo, hi, steps, cap); mid !== null; steps += 1, mid = nextMidpoint(lo, hi, steps, cap)) {
    if (samples.record(mid, await measure(mid)) <= ceiling) lo = mid;
    else hi = mid;
  }
  return samples.outcome();
}

export type Settled<T> = { ok: true; value: T } | { ok: false; error: unknown };

/** A request's answer or its failure, held until it is that request's turn to be recorded. */
export function settle<T>(run: () => Promise<T>): Promise<Settled<T>> {
  return (async () => run())().then((value) => ({ ok: true as const, value }), (error: unknown) => ({ ok: false as const, error }));
}

export function unwrap<T>(settled: Settled<T>): T {
  if (!settled.ok) throw settled.error;
  return settled.value;
}

/**
 * T-0403: searchLambda's search with its requests two in flight (P-COST-04) - the SAME samples, so the same outcome.
 * The first midpoint is always MAX_LAMBDA / 2 and measuring it needs nothing, so it runs alongside the fastest
 * request; lambda 0 never moves the bracket, so it runs alongside the second midpoint. Every result is RECORDED in
 * searchLambda's order (fastest, lambda 0, then each midpoint) once its round has settled, so the error searchLambda
 * would throw is the error thrown. A midpoint whose answer is unusable launches no successor.
 */
export async function searchLambdaAlongside(fastest: Promise<number>, budget: number,
  measure: (lambda: number) => Promise<number>, maxEvaluations = DEFAULT_MAX_EVALUATIONS): Promise<BudgetOutcome> {
  const cap = Math.max(1, maxEvaluations);
  const budgetOk = Number.isFinite(budget) && budget >= 0;
  let pending = budgetOk ? nextMidpoint(0, MAX_LAMBDA, 0, cap) : null;
  const [fastestSettled, firstSettled] = await Promise.all([settle(() => fastest),
    pending === null ? null : settle(() => measure(pending as number))]);
  const fastestSeconds = unwrap(fastestSettled);
  const ceiling = ceilingOf(fastestSeconds, budget);
  const samples = samplesUnder(fastestSeconds, budget, ceiling);
  if (pending === null || firstSettled === null) {
    samples.record(0, await measure(0));
    return samples.outcome();
  }

  let lo = 0;
  let hi = MAX_LAMBDA;
  let answer: Settled<number> = firstSettled;
  let floorRecorded = false;
  for (let steps = 0; pending !== null; steps += 1) {
    const mid: number = pending;
    const feasible = answer.ok && usable(answer.value) ? answer.value <= ceiling : null;
    const next = feasible === null ? null
      : nextMidpoint(feasible ? mid : lo, feasible ? hi : mid, steps + 1, cap);
    const floorRun = floorRecorded ? null : settle(() => measure(0));
    const nextRun = next === null ? null : settle(() => measure(next));
    if (floorRun !== null) {
      floorRecorded = true;
      const [floor] = await Promise.all([floorRun, nextRun]);
      samples.record(0, unwrap(floor));
    }
    const nextSettled = nextRun === null ? null : await nextRun;
    samples.record(mid, unwrap(answer));
    if (feasible) lo = mid;
    else hi = mid;
    pending = next;
    if (nextSettled !== null) answer = nextSettled;
  }
  return samples.outcome();
}
