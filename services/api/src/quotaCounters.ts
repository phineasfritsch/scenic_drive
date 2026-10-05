/**
 * upstream.ts's Counters over the QuotaCounter Durable Object (T-0256 R1/R4). The device's daily allowance is
 * reserved first, then the month's calls; a refusal from either throws UpstreamPaused before guardedPlan reaches
 * its first fetch. Either order of failure over-counts, which is the safe direction.
 */
import { dailyQuota, dayKey, monthKey, nextReset } from "./quota";
import type { QuotaCounter } from "./QuotaCounter";
import { UpstreamPaused, type Counters } from "./upstream";

export const GLOBAL_COUNTER = "global";

export function countersFromNamespace(ns: DurableObjectNamespace<QuotaCounter>): Counters {
  const device = (userId: string) => ns.get(ns.idFromName(`device:${userId}`));
  const global = () => ns.get(ns.idFromName(GLOBAL_COUNTER));
  return {
    async read(userId, now, kind) {
      const [plansUsedToday, monthlyUpstreamCalls] = await Promise.all([
        device(userId).readDaily(dayKey(now), kind),
        global().readMonthly(monthKey(now)),
      ]);
      return { plansUsedToday, monthlyUpstreamCalls };
    },
    async reserve(userId, upstreamCalls, now, kind, tier) {
      if (!(await device(userId).reserveDaily(dayKey(now), kind, dailyQuota(kind, tier)))) {
        throw new UpstreamPaused({ ok: false, reason: "quota_exhausted", tier, resetsAt: nextReset(now) });
      }
      if (!(await global().reserveMonthly(monthKey(now), upstreamCalls))) {
        throw new UpstreamPaused({ ok: false, reason: "upstream_paused", monthlyCalls: -1 });
      }
    },
  };
}
