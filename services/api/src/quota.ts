/**
 * Spend control. Two independent mechanisms, because they fail differently.
 *
 *   PER-USER QUOTA   bounds what one caller can cost us in a day. Decremented BEFORE the upstream call, never
 *                    after: a quota checked after the fact is an accounting record, not a limit.
 *   GLOBAL KILL      bounds what EVERYONE can cost us in a month. MAX_MONTHLY_UPSTREAM_CALLS is a compile-time
 *                    constant, not config, because a config value is a value an agent can raise at 3am while
 *                    "fixing" a 429. Changing it is a code change, a PR and a review.
 *
 * The counter counts UPSTREAM CALLS, not user actions. One scenic plan is up to 12 requests to our routing box;
 * counting plans would undercount the thing that actually costs money by an order of magnitude.
 */

/** Hard ceiling on upstream calls per calendar month, across all users. Pinned by P-COST-02. */
export const MAX_MONTHLY_UPSTREAM_CALLS = 250_000;

/** Trip the kill switch at 90%, leaving headroom to notice and react before anything is refused. */
export const KILL_SWITCH_THRESHOLD = 0.9;

/** Daily per-user plan budgets. A plan is at most PLAN_UPSTREAM_COST upstream calls. */
export const DAILY_PLAN_QUOTA = { anon: 3, free: 10, paid: 200 } as const;
export const PLAN_UPSTREAM_COST = 12;

export type Tier = keyof typeof DAILY_PLAN_QUOTA;

export type QuotaVerdict =
  | { ok: true; tier: Tier; remaining: number }
  | { ok: false; reason: "quota_exhausted"; tier: Tier; resetsAt: string }
  | { ok: false; reason: "upstream_paused"; monthlyCalls: number }
  // Counter or tier that is not a number/tier we recognise. Its own reason, because "we could not tell" is
  // not the same answer as "you are over your limit" and the caller may want to page someone about it.
  | { ok: false; reason: "invalid_state"; detail: string };

/** A count that a limit can be compared against: finite, integral, not negative. NaN is none of these, and
 *  every comparison against NaN is false - which is how a NaN counter silently disables a ceiling. */
function isCount(n: unknown): n is number {
  return typeof n === "number" && Number.isFinite(n) && Number.isInteger(n) && n >= 0;
}

export function isTier(t: unknown): t is Tier {
  return typeof t === "string" && Object.prototype.hasOwnProperty.call(DAILY_PLAN_QUOTA, t);
}

/** UTC day key. UTC, not local: a quota that resets at a different hour depending on where the user is
 *  is a quota with a seam, and seams get found. */
export function dayKey(now: Date): string {
  return now.toISOString().slice(0, 10);
}

/** UTC month key, matching how the upstream bill is actually cut. */
export function monthKey(now: Date): string {
  return now.toISOString().slice(0, 7);
}

/** Start of the next UTC day, so a refusal can tell the user exactly when they get their allowance back. */
export function nextReset(now: Date): string {
  const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1));
  return d.toISOString();
}

/**
 * Fails CLOSED on a counter it cannot read. `NaN >= anything` is false, so a NaN arriving from a KV miss, a
 * bad parseInt or a half-written Durable Object row would have returned "not tripped" and disabled the global
 * ceiling silently - the one failure this function exists to prevent. An unreadable counter trips the switch.
 */
export function killSwitchTripped(monthlyCalls: number): boolean {
  if (!isCount(monthlyCalls)) return true;
  return monthlyCalls >= MAX_MONTHLY_UPSTREAM_CALLS * KILL_SWITCH_THRESHOLD;
}

/**
 * Decide whether one more plan may proceed. Pure, so the policy is testable without a network, a clock or a
 * Durable Object — the parts most likely to be wrong are the arithmetic and the boundaries, not the storage.
 */
export function checkQuota(args: {
  tier: Tier;
  plansUsedToday: number;
  monthlyUpstreamCalls: number;
  now: Date;
}): QuotaVerdict {
  const { tier, plansUsedToday, monthlyUpstreamCalls, now } = args;

  // `tier` is typed, but it arrives from a D1 row, not from the compiler. An unrecognised value indexed
  // straight into DAILY_PLAN_QUOTA yielded `undefined`, `plansUsedToday >= undefined` is false, and the
  // caller got `{ ok: true, remaining: NaN }` - an unlimited plan for anyone whose tier column is misspelled.
  if (!isTier(tier)) {
    return { ok: false, reason: "invalid_state", detail: `unknown tier ${JSON.stringify(tier)}` };
  }
  // Same reasoning for the usage counter: -5 produced `remaining: 14` on a 10-plan tier, and 9.5 produced
  // `{ ok: true, remaining: -0.5 }`. Refuse what cannot be compared rather than admitting it.
  if (!isCount(plansUsedToday)) {
    return { ok: false, reason: "invalid_state", detail: `plansUsedToday is not a count: ${plansUsedToday}` };
  }

  // Global before per-user: when the kill switch is tripped nobody proceeds, including a paid user with
  // quota to spare. The bill is global; the allowance is not.
  if (killSwitchTripped(monthlyUpstreamCalls)) {
    return { ok: false, reason: "upstream_paused", monthlyCalls: monthlyUpstreamCalls };
  }

  const limit = DAILY_PLAN_QUOTA[tier];
  if (plansUsedToday >= limit) {
    return { ok: false, reason: "quota_exhausted", tier, resetsAt: nextReset(now) };
  }

  return { ok: true, tier, remaining: limit - plansUsedToday - 1 };
}
