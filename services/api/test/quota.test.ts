import { describe, expect, it } from "vitest";
import {
  checkQuota,
  dayKey,
  monthKey,
  nextReset,
  killSwitchTripped,
  DAILY_PLAN_QUOTA,
  MAX_MONTHLY_UPSTREAM_CALLS,
  KILL_SWITCH_THRESHOLD,
  PLAN_UPSTREAM_COST,
} from "../src/quota";

const NOW = new Date("2026-09-07T14:00:00Z");

describe("the constant is a constant", () => {
  it("MAX_MONTHLY_UPSTREAM_CALLS is a literal, not read from env or config", () => {
    // P-COST-02 pins this. A config value is a value an agent can raise while "fixing" a 429 at 3am;
    // raising this one requires a code change, a PR, and a review.
    expect(MAX_MONTHLY_UPSTREAM_CALLS).toBe(250_000);
    expect(Number.isInteger(MAX_MONTHLY_UPSTREAM_CALLS)).toBe(true);
  });

  it("trips with headroom, not at the cliff", () => {
    expect(KILL_SWITCH_THRESHOLD).toBeLessThan(1);
    expect(KILL_SWITCH_THRESHOLD).toBeGreaterThanOrEqual(0.8);
  });

  it("a plan is priced in upstream calls, not in plans", () => {
    expect(PLAN_UPSTREAM_COST).toBeGreaterThan(1);
  });
});

describe("kill switch", () => {
  it("is not tripped well below the ceiling", () => {
    expect(killSwitchTripped(0)).toBe(false);
    expect(killSwitchTripped(MAX_MONTHLY_UPSTREAM_CALLS / 2)).toBe(false);
  });

  it("trips exactly at the threshold, not one call later", () => {
    const at = MAX_MONTHLY_UPSTREAM_CALLS * KILL_SWITCH_THRESHOLD;
    expect(killSwitchTripped(at - 1)).toBe(false);
    expect(killSwitchTripped(at)).toBe(true);
  });

  it("stays tripped past the ceiling", () => {
    expect(killSwitchTripped(MAX_MONTHLY_UPSTREAM_CALLS * 10)).toBe(true);
  });
});

describe("per-user quota", () => {
  it("allows a first plan and reports what is left", () => {
    const v = checkQuota({ tier: "free", plansUsedToday: 0, monthlyUpstreamCalls: 0, now: NOW });
    expect(v).toMatchObject({ ok: true, tier: "free", remaining: DAILY_PLAN_QUOTA.free - 1 });
  });

  it("allows the LAST plan in the allowance", () => {
    const v = checkQuota({ tier: "free", plansUsedToday: DAILY_PLAN_QUOTA.free - 1, monthlyUpstreamCalls: 0, now: NOW });
    expect(v).toMatchObject({ ok: true, remaining: 0 });
  });

  it("refuses the one after that, and says when it resets", () => {
    const v = checkQuota({ tier: "free", plansUsedToday: DAILY_PLAN_QUOTA.free, monthlyUpstreamCalls: 0, now: NOW });
    expect(v).toMatchObject({ ok: false, reason: "quota_exhausted", tier: "free" });
    if (!v.ok && v.reason === "quota_exhausted") expect(v.resetsAt).toBe("2026-09-08T00:00:00.000Z");
  });

  it("anon is the tightest tier and paid the loosest", () => {
    expect(DAILY_PLAN_QUOTA.anon).toBeLessThan(DAILY_PLAN_QUOTA.free);
    expect(DAILY_PLAN_QUOTA.free).toBeLessThan(DAILY_PLAN_QUOTA.paid);
  });
});

describe("global beats local", () => {
  it("a paid user with plenty of quota is still refused once the kill switch trips", () => {
    // The bill is global; the allowance is not. This is the case that actually protects the budget.
    const v = checkQuota({
      tier: "paid",
      plansUsedToday: 0,
      monthlyUpstreamCalls: MAX_MONTHLY_UPSTREAM_CALLS,
      now: NOW,
    });
    expect(v).toMatchObject({ ok: false, reason: "upstream_paused" });
  });

  it("reports the count that caused the pause, so the refusal is diagnosable", () => {
    const v = checkQuota({ tier: "paid", plansUsedToday: 0, monthlyUpstreamCalls: 240_000, now: NOW });
    if (!v.ok && v.reason === "upstream_paused") expect(v.monthlyCalls).toBe(240_000);
    else throw new Error("expected upstream_paused");
  });
});

describe("fails closed on values it cannot compare", () => {
  // Every finding in this block is reviewer-14's. Each one turned a ceiling into a suggestion, and none of
  // them threw: the code returned a cheerful `ok: true`, which is the exact failure mode the spend controls
  // exist to prevent. NaN is the worst of them, because every comparison against NaN is false.
  it("an unreadable monthly counter TRIPS the kill switch instead of disabling it", () => {
    expect(killSwitchTripped(NaN)).toBe(true);
    expect(killSwitchTripped(Infinity)).toBe(true);
    expect(killSwitchTripped(-1)).toBe(true);
    expect(killSwitchTripped(1.5)).toBe(true);
    expect(killSwitchTripped("250000" as unknown as number)).toBe(true);
  });

  it("a NaN counter reaching checkQuota pauses upstream rather than admitting the plan", () => {
    const v = checkQuota({ tier: "paid", plansUsedToday: 0, monthlyUpstreamCalls: NaN, now: NOW });
    expect(v).toMatchObject({ ok: false, reason: "upstream_paused" });
  });

  it("an unrecognised tier is refused, not given an undefined limit", () => {
    // `tier` comes from a D1 row, not from the compiler. DAILY_PLAN_QUOTA["premum"] is undefined,
    // `plansUsedToday >= undefined` is false, and the caller got an unlimited plan with remaining: NaN.
    const v = checkQuota({
      tier: "premum" as unknown as "paid",
      plansUsedToday: 10_000,
      monthlyUpstreamCalls: 0,
      now: NOW,
    });
    expect(v).toMatchObject({ ok: false, reason: "invalid_state" });
  });

  it("does not inherit a limit from Object.prototype", () => {
    const v = checkQuota({
      tier: "constructor" as unknown as "paid",
      plansUsedToday: 0,
      monthlyUpstreamCalls: 0,
      now: NOW,
    });
    expect(v).toMatchObject({ ok: false, reason: "invalid_state" });
  });

  it("a negative or fractional usage count is refused, not treated as spare allowance", () => {
    // -5 previously reported remaining: 14 on a 10-plan tier; 9.5 reported { ok: true, remaining: -0.5 }.
    for (const plansUsedToday of [-5, 9.5, NaN, Infinity]) {
      const v = checkQuota({ tier: "free", plansUsedToday, monthlyUpstreamCalls: 0, now: NOW });
      expect(v).toMatchObject({ ok: false, reason: "invalid_state" });
    }
  });
});

describe("time keys", () => {
  it("day and month keys are UTC, so the quota has no timezone seam", () => {
    expect(dayKey(new Date("2026-09-07T23:59:59Z"))).toBe("2026-09-07");
    expect(dayKey(new Date("2026-09-08T00:00:01Z"))).toBe("2026-09-08");
    expect(monthKey(new Date("2026-09-30T23:59:59Z"))).toBe("2026-09");
    expect(monthKey(new Date("2026-10-01T00:00:00Z"))).toBe("2026-10");
  });

  it("nextReset rolls over month and year boundaries", () => {
    expect(nextReset(new Date("2026-09-30T12:00:00Z"))).toBe("2026-10-01T00:00:00.000Z");
    expect(nextReset(new Date("2026-12-31T23:00:00Z"))).toBe("2027-01-01T00:00:00.000Z");
  });
});
