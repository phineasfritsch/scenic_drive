/**
 * T-0256 R4: the QuotaCounter re-checks inside its own transaction. Read-then-reserve from the Worker is two
 * round trips, so two requests can both read 2 of 3; the reservation itself must refuse the one that loses.
 * Driven through countersFromNamespace - the Counters the shipped deps hand guardedPlan - over the R9 fake.
 */
import { describe, expect, it } from "vitest";
import { handleLoop } from "../src/loop";
import { countersFromNamespace } from "../src/quotaCounters";
import { UpstreamPaused } from "../src/upstream";
import { fakeQuotaNamespace } from "./doFake";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, squareLoop } from "./loopHarness";
import { NOW } from "./planHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";

async function refusal(promise: Promise<unknown>): Promise<unknown> {
  try {
    await promise;
  } catch (error) {
    expect(error).toBeInstanceOf(UpstreamPaused);
    return (error as UpstreamPaused).verdict;
  }
  throw new Error("the reservation was not refused");
}

describe("QuotaCounter reservations refuse inside the transaction (R4)", () => {
  it("a device already at its daily plan limit is refused quota_exhausted and nothing changes", async () => {
    const quota = fakeQuotaNamespace();
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 3, loop: 0 });
    const counters = countersFromNamespace(quota.ns);
    expect(await refusal(counters.reserve(DEVICE, 12, NOW, "plan", "anon"))).toEqual(
      { ok: false, reason: "quota_exhausted", tier: "anon", resetsAt: "2026-10-06T00:00:00.000Z" });
    expect(quota.state()).toEqual({ [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan: 3, loop: 0 } } });
  });

  it("a free device's one loop is refused at the second without touching its plans", async () => {
    const quota = fakeQuotaNamespace();
    const counters = countersFromNamespace(quota.ns);
    await counters.reserve(DEVICE, 3, NOW, "loop", "free");
    expect(await refusal(counters.reserve(DEVICE, 3, NOW, "loop", "free"))).toEqual(
      { ok: false, reason: "quota_exhausted", tier: "free", resetsAt: "2026-10-06T00:00:00.000Z" });
    expect(quota.state()).toEqual({
      [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan: 0, loop: 1 } },
      global: { monthly: { month: "2026-10", calls: 3 } },
    });
  });

  it("a paid device's loop allowance is the paid plan cap, by reference", async () => {
    const quota = fakeQuotaNamespace();
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 0, loop: 199 });
    const counters = countersFromNamespace(quota.ns);
    await counters.reserve(DEVICE, 3, NOW, "loop", "paid");
    expect(await refusal(counters.reserve(DEVICE, 3, NOW, "loop", "paid"))).toEqual(
      { ok: false, reason: "quota_exhausted", tier: "paid", resetsAt: "2026-10-06T00:00:00.000Z" });
    expect(quota.state()[`device:${DEVICE}`]).toEqual({ daily: { day: "2026-10-05", plan: 0, loop: 200 } });
  });

  it("a month that tripped between read and reserve is refused upstream_paused; the device plan stays spent", async () => {
    const quota = fakeQuotaNamespace();
    quota.seed("global", "monthly", { month: "2026-10", calls: 224_999 });
    const counters = countersFromNamespace(quota.ns);
    await counters.reserve(DEVICE, 12, NOW, "plan", "anon");
    expect(await refusal(counters.reserve(DEVICE, 12, NOW, "plan", "anon"))).toEqual(
      { ok: false, reason: "upstream_paused", monthlyCalls: -1 });
    expect(quota.state()).toEqual({
      [`device:${DEVICE}`]: { daily: { day: "2026-10-05", plan: 2, loop: 0 } },
      global: { monthly: { month: "2026-10", calls: 225_011 } },
    });
  });

  it("read answers the kind asked for and the month, and an unreadable record reads as not a count", async () => {
    const quota = fakeQuotaNamespace();
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 2, loop: 1 });
    quota.seed("global", "monthly", { month: "2026-10", calls: 40 });
    const counters = countersFromNamespace(quota.ns);
    expect(await counters.read(DEVICE, NOW, "plan")).toEqual({ plansUsedToday: 2, monthlyUpstreamCalls: 40 });
    expect(await counters.read(DEVICE, NOW, "loop")).toEqual({ plansUsedToday: 1, monthlyUpstreamCalls: 40 });
    expect(await counters.read(DEVICE, new Date("2026-11-01T00:00:00Z"), "plan"))
      .toEqual({ plansUsedToday: 0, monthlyUpstreamCalls: 0 });
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: "x", loop: 0 });
    expect(await counters.read(DEVICE, NOW, "plan")).toEqual({ plansUsedToday: "x", monthlyUpstreamCalls: 40 });
  });

  it("handleLoop refuses a free device's second loop on the READ, before any reservation (checkQuota knows the kind)", async () => {
    const h = loopHarness([loopPath(squareLoop())], { plansUsedToday: 1 });
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(response.status).toBe(429);
    expect(h.events).toEqual([]);
  });
});
