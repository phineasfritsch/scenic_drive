/**
 * The quota counters' storage (T-0256 R1): one Durable Object class, addressed two ways.
 *
 *   idFromName("device:<install uuid>")  the DAILY record {day, plan, loop} for one device. A new UTC day replaces
 *                                        it in place, so nothing accumulates per day.
 *   idFromName("global")                 the MONTHLY record {month, calls} - upstream calls across everyone.
 *
 * A reservation re-checks its limit INSIDE a storage transaction and refuses (false) rather than going over: the
 * Worker reads and then reserves in two round trips, so two requests can both read 2 of 3, and only the
 * reservation can tell which one lost. Reads hand back whatever is stored for the current period - a record that
 * is not a count reaches checkQuota as one and is refused there (invalid_state / tripped), never repaired here.
 */
import { DurableObject } from "cloudflare:workers";
import { killSwitchTripped, type QuotaKind } from "./quota";

export const DAILY_RECORD = "daily";
export const MONTHLY_RECORD = "monthly";

interface DailyRecord {
  day: string;
  plan: number;
  loop: number;
}

interface MonthlyRecord {
  month: string;
  calls: number;
}

export class QuotaCounter extends DurableObject {
  /** Reservations of `kind` this device has made on `day` (UTC). */
  async readDaily(day: string, kind: QuotaKind): Promise<number> {
    const stored = await this.ctx.storage.get<DailyRecord>(DAILY_RECORD);
    return stored?.day === day ? stored[kind] : 0;
  }

  /** One more `kind` on `day` if that stays within `limit`; false, and nothing written, if it would not. */
  async reserveDaily(day: string, kind: QuotaKind, limit: number): Promise<boolean> {
    return this.ctx.storage.transaction(async (txn) => {
      const stored = await txn.get<DailyRecord>(DAILY_RECORD);
      const record: DailyRecord = stored?.day === day ? stored : { day, plan: 0, loop: 0 };
      if (!(record[kind] < limit)) return false;
      await txn.put(DAILY_RECORD, { ...record, [kind]: record[kind] + 1 });
      return true;
    });
  }

  /** Upstream calls reserved across everyone in `month` (UTC). */
  async readMonthly(month: string): Promise<number> {
    const stored = await this.ctx.storage.get<MonthlyRecord>(MONTHLY_RECORD);
    return stored?.month === month ? stored.calls : 0;
  }

  /** Add `calls` to `month` unless the month has already tripped the kill switch; false, nothing written, if so. */
  async reserveMonthly(month: string, calls: number): Promise<boolean> {
    return this.ctx.storage.transaction(async (txn) => {
      const stored = await txn.get<MonthlyRecord>(MONTHLY_RECORD);
      const current = stored?.month === month ? stored.calls : 0;
      if (killSwitchTripped(current)) return false;
      await txn.put(MONTHLY_RECORD, { month, calls: current + calls });
      return true;
    });
  }
}
