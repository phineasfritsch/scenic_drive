/**
 * The only way to reach the routing box.
 *
 * Everything that costs money goes through `guardedUpstream`. That is the point: P-COST-01 asserts that a
 * quota decrement PRECEDES every upstream call, and the only way to make that assertion mechanical rather
 * than aspirational is to have exactly one door and put the guard in front of it.
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

export class UpstreamPaused extends Error {
  constructor(public readonly verdict: QuotaVerdict) {
    super("upstream paused");
  }
}

/**
 * Reserve budget, then call. Never the other way round: a quota checked after the fact is an accounting
 * record, not a limit, and the request it should have stopped has already cost money.
 */
export async function guardedUpstream(
  deps: UpstreamDeps,
  args: { userId: string; tier: Tier; url: string; init?: RequestInit },
): Promise<Response> {
  const now = deps.now();

  if (deps.killed()) {
    throw new UpstreamPaused({ ok: false, reason: "upstream_paused", monthlyCalls: -1 });
  }

  const { plansUsedToday, monthlyUpstreamCalls } = await deps.counters.read(args.userId, now);
  const verdict = checkQuota({ tier: args.tier, plansUsedToday, monthlyUpstreamCalls, now });
  if (!verdict.ok) throw new UpstreamPaused(verdict);

  // Reserve BEFORE the call. If the upstream then fails, we have over-counted by one plan, which is the
  // safe direction to be wrong in: it costs the user one plan of allowance, not us an unbounded bill.
  await deps.counters.reserve(args.userId, PLAN_UPSTREAM_COST, now);

  return deps.fetchImpl(args.url, args.init);
}

export { killSwitchTripped };
