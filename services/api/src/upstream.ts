/**
 * The only way to reach the routing box.
 *
 * Everything that costs money goes through `guardedPlan`. That is the point: P-COST-01 asserts that a
 * quota decrement PRECEDES every upstream call, and the only way to make that assertion mechanical rather
 * than aspirational is to have exactly one door and put the guard in front of it.
 *
 * THE UNIT IS A PLAN, NOT A CALL. One scenic plan is a lambda bisection - up to PLAN_UPSTREAM_COST requests
 * to our own box. The daily allowance is counted in plans; the monthly kill-switch counter is counted in
 * upstream calls. So the door opens once per plan, reserves that budget up front, and hands the body a `call`
 * that refuses past it. The earlier shape reserved PLAN_UPSTREAM_COST and then made exactly one call, which
 * read as either a 12x over-count or a 12x under-count depending on how the caller looped - and neither
 * convention was tested. reviewer-14 found it; this is the fix.
 *
 * The reservation is deliberately an UPPER BOUND: a plan that finishes in 4 calls still spends 12 of the
 * monthly counter. Over-counting pauses us early, which is recoverable. Under-counting is an unbounded bill.
 *
 * `fetchImpl` is injectable so tests can COUNT calls. A test that asserts "no upstream call happened" by
 * checking a log is asserting about a log; this one is asserting about the call.
 */
import { checkQuota, killSwitchTripped, PLAN_UPSTREAM_COST, type QuotaVerdict, type Tier } from "./quota";

export interface Counters {
  /** Plans this user has started today, and upstream calls made this month, across everyone. */
  read(userId: string, now: Date): Promise<{ plansUsedToday: number; monthlyUpstreamCalls: number }>;
  /** Record that a plan is starting. Called BEFORE the upstream work, not after. */
  reserve(userId: string, upstreamCalls: number, now: Date): Promise<void>;
}

export interface UpstreamDeps {
  counters: Counters;
  fetchImpl: (url: string, init?: RequestInit) => Promise<Response>;
  now: () => Date;
  /** Manual override: KILL=1 pauses all upstream work without a deploy. */
  killed: () => boolean;
}

/** What a plan body is given. It cannot reach `fetchImpl` any other way. */
export type GuardedFetch = (url: string, init?: RequestInit) => Promise<Response>;

export class UpstreamPaused extends Error {
  constructor(public readonly verdict: QuotaVerdict) {
    super("upstream paused");
  }
}

/** Thrown when a plan body tries to spend more than the budget it reserved. Refusing here keeps the
 *  reservation an upper bound on real calls; letting it through would make the counter a lie. */
export class PlanBudgetExceeded extends Error {
  constructor(public readonly budget: number) {
    super(`plan exceeded its budget of ${budget} upstream calls`);
  }
}

/**
 * Reserve the budget, then run the plan. Never the other way round: a quota checked after the fact is an
 * accounting record, not a limit, and the request it should have stopped has already cost money.
 */
export async function guardedPlan<T>(
  deps: UpstreamDeps,
  args: { userId: string; tier: Tier },
  body: (call: GuardedFetch) => Promise<T>,
): Promise<T> {
  const now = deps.now();

  if (deps.killed()) {
    throw new UpstreamPaused({ ok: false, reason: "upstream_paused", monthlyCalls: -1 });
  }

  const { plansUsedToday, monthlyUpstreamCalls } = await deps.counters.read(args.userId, now);
  const verdict = checkQuota({ tier: args.tier, plansUsedToday, monthlyUpstreamCalls, now });
  if (!verdict.ok) throw new UpstreamPaused(verdict);

  // Reserve BEFORE any call. If the plan then fails, we have over-counted by one plan, which is the safe
  // direction to be wrong in: it costs the user one plan of allowance, not us an unbounded bill.
  await deps.counters.reserve(args.userId, PLAN_UPSTREAM_COST, now);

  let spent = 0;
  const call: GuardedFetch = (url, init) => {
    spent += 1;
    if (spent > PLAN_UPSTREAM_COST) {
      // Reject BEFORE fetchImpl, so the call never happens. P-COST-04 wants <= 12 requests per plan, and a
      // cap that fires after the request has already gone out is not a cap.
      return Promise.reject(new PlanBudgetExceeded(PLAN_UPSTREAM_COST));
    }
    return deps.fetchImpl(url, init);
  };

  return body(call);
}

/**
 * A plan that makes exactly one upstream call. It still reserves the full plan budget, because the daily
 * allowance is counted in plans - one plan is one plan whether it needed 1 request or 12.
 */
export async function guardedUpstream(
  deps: UpstreamDeps,
  args: { userId: string; tier: Tier; url: string; init?: RequestInit },
): Promise<Response> {
  return guardedPlan(deps, { userId: args.userId, tier: args.tier }, (call) => call(args.url, args.init));
}

export { killSwitchTripped, PLAN_UPSTREAM_COST };
