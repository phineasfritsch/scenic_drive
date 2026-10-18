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

/** T-0411: the most requests one search sends that it may never record - each a guess at the next midpoint. */
export const MAX_SPECULATIVE = 2;

/**
 * searchLambda's search with at most two requests in flight (P-COST-04) - the SAME samples, so the same outcome.
 * T-0403: the first midpoint runs alongside the fastest request and lambda 0 alongside the second midpoint. T-0411:
 * a slot the search would leave idle carries the midpoint it needs next if the one in flight fits the ceiling (its
 * upper child) - at most MAX_SPECULATIVE such guesses, never recorded unless the bisection reaches them. Every result is RECORDED in
 * searchLambda's order (fastest, lambda 0, then each midpoint), so the error searchLambda would throw is the error
 * thrown. A midpoint whose answer is unusable launches no successor. Every request the search sent has settled
 * before it returns or throws, so nothing it sent is in flight after it.
 */
export async function searchLambdaAlongside(fastest: Promise<number>, budget: number,
  measure: (lambda: number) => Promise<number>, maxEvaluations = DEFAULT_MAX_EVALUATIONS): Promise<BudgetOutcome> {
  const cap = Math.max(1, maxEvaluations);
  const budgetOk = Number.isFinite(budget) && budget >= 0;
  const runs = new Map<number, Promise<Settled<number>>>();
  const answers = new Map<number, Settled<number>>();
  const box: { fastest: Settled<number> | null; inFlight: number; wake: () => void } =
    { fastest: null, inFlight: 1, wake: () => undefined };
  const landed = () => {
    box.inFlight -= 1;
    box.wake();
  };
  void settle(() => fastest).then((s) => {
    box.fastest = s;
    landed();
  });
  const launch = (lambda: number) => {
    box.inFlight += 1;
    runs.set(lambda, settle(() => measure(lambda)).then((s) => {
      answers.set(lambda, s);
      landed();
      return s;
    }));
  };

  let lo = 0;
  let hi = MAX_LAMBDA;
  let steps = 0;
  let pending = budgetOk ? nextMidpoint(0, MAX_LAMBDA, 0, cap) : null;
  let blocked = false;
  let guesses = 0;
  const path: number[] = [];
  const fill = () => {
    while (box.inFlight < 2 && box.fastest?.ok !== false && budgetOk) {
      const guess = pending === null || blocked ? null : nextMidpoint(pending, hi, steps + 1, cap);
      if (pending !== null && !blocked && !runs.has(pending)) launch(pending);
      else if (!runs.has(0)) launch(0);
      else if (guess !== null && !runs.has(guess) && guesses < MAX_SPECULATIVE) {
        guesses += 1;
        launch(guess);
      } else return;
    }
  };

  let samples: ReturnType<typeof samplesUnder> | null = null;
  let recorded = 0;
  try {
    for (;;) {
      const fastestNow = box.fastest as Settled<number> | null;
      if (fastestNow !== null) {
        if (samples === null) {
          const fastestSeconds = unwrap(fastestNow);
          samples = samplesUnder(fastestSeconds, budget, ceilingOf(fastestSeconds, budget));
        }
        const ceiling = fastestNow.ok ? fastestNow.value + budget : 0;
        for (let a = pending === null ? undefined : answers.get(pending); a !== undefined && !blocked;
          a = pending === null ? undefined : answers.get(pending)) {
          if (!a.ok || !usable(a.value)) {
            blocked = true;
            break;
          }
          if (a.value <= ceiling) lo = pending as number;
          else hi = pending as number;
          path.push(pending as number);
          steps += 1;
          pending = nextMidpoint(lo, hi, steps, cap);
        }
        const floor = answers.get(0);
        if (floor !== undefined) {
          if (recorded === 0) {
            samples.record(0, unwrap(floor));
            recorded = 1;
          }
          for (; recorded <= path.length; recorded += 1) samples.record(path[recorded - 1]!, unwrap(answers.get(path[recorded - 1]!)!));
          if (blocked) samples.record(pending as number, unwrap(answers.get(pending as number)!));
          if (pending === null) return samples.outcome();
        }
      }
      fill();
      await new Promise<void>((resolve) => {
        box.wake = resolve;
      });
    }
  } finally {
    await Promise.all(runs.values());
  }
}
