import { describe, expect, it } from "vitest";
import { guardedUpstream, UpstreamPaused, type Counters, type UpstreamDeps } from "../src/upstream";
import { MAX_MONTHLY_UPSTREAM_CALLS, PLAN_UPSTREAM_COST } from "../src/quota";

const NOW = new Date("2026-09-07T14:00:00Z");

/** A counting fake. The whole point of P-COST-01 is that no upstream call escapes the guard, so the test
 *  counts actual invocations rather than trusting a log line. */
function harness(over: Partial<{ plansUsedToday: number; monthlyUpstreamCalls: number; killed: boolean }> = {}) {
  const calls: string[] = [];
  const reserved: Array<{ userId: string; upstreamCalls: number }> = [];
  const counters: Counters = {
    async read() {
      return {
        plansUsedToday: over.plansUsedToday ?? 0,
        monthlyUpstreamCalls: over.monthlyUpstreamCalls ?? 0,
      };
    },
    async reserve(userId, upstreamCalls) {
      reserved.push({ userId, upstreamCalls });
    },
  };
  const deps: UpstreamDeps = {
    counters,
    now: () => NOW,
    killed: () => over.killed ?? false,
    fetchImpl: async (url) => {
      calls.push(url);
      return new Response("ok");
    },
  };
  return { deps, calls, reserved };
}

const args = { userId: "u1", tier: "free" as const, url: "https://routing.example/route" };

describe("guardedUpstream", () => {
  it("calls upstream when there is budget, and reserves first", async () => {
    const { deps, calls, reserved } = harness();
    const r = await guardedUpstream(deps, args);
    expect(r.status).toBe(200);
    expect(calls).toEqual(["https://routing.example/route"]);
    expect(reserved).toEqual([{ userId: "u1", upstreamCalls: PLAN_UPSTREAM_COST }]);
  });

  it("reserves BEFORE calling, not after", async () => {
    // Ordering is the property. A reservation made after the call cannot prevent the call.
    const order: string[] = [];
    const { deps } = harness();
    const wrapped: UpstreamDeps = {
      ...deps,
      counters: {
        read: deps.counters.read.bind(deps.counters),
        async reserve(...a) {
          order.push("reserve");
          return deps.counters.reserve(...a);
        },
      },
      fetchImpl: async (u) => {
        order.push("fetch");
        return new Response("ok");
      },
    };
    await guardedUpstream(wrapped, args);
    expect(order).toEqual(["reserve", "fetch"]);
  });

  it("makes NO upstream call when the daily quota is exhausted", async () => {
    const { deps, calls, reserved } = harness({ plansUsedToday: 999 });
    await expect(guardedUpstream(deps, args)).rejects.toBeInstanceOf(UpstreamPaused);
    expect(calls).toEqual([]);
    expect(reserved).toEqual([]);
  });

  it("makes NO upstream call when the kill switch has tripped on volume", async () => {
    const { deps, calls } = harness({ monthlyUpstreamCalls: MAX_MONTHLY_UPSTREAM_CALLS });
    await expect(guardedUpstream(deps, args)).rejects.toBeInstanceOf(UpstreamPaused);
    expect(calls).toEqual([]);
  });

  it("makes NO upstream call when killed manually, before even reading counters", async () => {
    const { deps, calls, reserved } = harness({ killed: true });
    await expect(guardedUpstream(deps, args)).rejects.toBeInstanceOf(UpstreamPaused);
    expect(calls).toEqual([]);
    expect(reserved).toEqual([]);
  });

  it("a paid user with quota is still stopped by the global kill switch", async () => {
    const { deps, calls } = harness({ monthlyUpstreamCalls: MAX_MONTHLY_UPSTREAM_CALLS });
    await expect(
      guardedUpstream(deps, { ...args, tier: "paid" }),
    ).rejects.toBeInstanceOf(UpstreamPaused);
    expect(calls).toEqual([]);
  });

  it("carries the reason so the client can say something true", async () => {
    const { deps } = harness({ plansUsedToday: 999 });
    try {
      await guardedUpstream(deps, args);
      throw new Error("should have thrown");
    } catch (e) {
      expect(e).toBeInstanceOf(UpstreamPaused);
      const v = (e as UpstreamPaused).verdict;
      expect(v.ok).toBe(false);
      if (!v.ok && v.reason === "quota_exhausted") expect(v.resetsAt).toMatch(/^2026-09-08T00:00:00/);
    }
  });

  it("over-counts rather than under-counts when upstream fails", async () => {
    // Safe direction: the user loses one plan of allowance; we do not lose an unbounded amount of money.
    const { deps, reserved } = harness();
    const failing: UpstreamDeps = { ...deps, fetchImpl: async () => { throw new Error("upstream 500"); } };
    await expect(guardedUpstream(failing, args)).rejects.toThrow("upstream 500");
    expect(reserved).toHaveLength(1);
  });
});
