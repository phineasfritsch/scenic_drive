/**
 * upstream.ts's Counters over the QuotaCounter Durable Object (T-0256 R1/R4). The device's daily allowance is
 * reserved first, then the month's calls; a refusal from either throws UpstreamPaused before guardedPlan reaches
 * its first fetch. Either order of failure over-counts, which is the safe direction.
 */
import { dailyQuota, dayKey, isCount, monthKey, nextReset } from "./quota";
import type { QuotaCounter } from "./QuotaCounter";
import { UpstreamPaused, type Counters } from "./upstream";

export const GLOBAL_COUNTER = "global";

/** The month's upstream calls for /__health (T-0344): a READ of the global counter, never a reservation; null when
 *  QUOTA is unbound, the read throws, or the stored value is not a count - ops/sane reads null as "cannot tell". */
export async function monthlyUpstreamCalls(ns: DurableObjectNamespace<QuotaCounter> | undefined, now: Date): Promise<number | null> {
  if (!ns) return null;
  try {
    const calls: unknown = await ns.get(ns.idFromName(GLOBAL_COUNTER)).readMonthly(monthKey(now));
    return isCount(calls) ? calls : null;
  } catch {
    return null;
  }
}

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
