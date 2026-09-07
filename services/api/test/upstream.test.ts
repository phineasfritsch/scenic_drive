import { describe, expect, it } from "vitest";
import {
  guardedPlan,
  guardedUpstream,
  PlanBudgetExceeded,
  UpstreamPaused,
  type Counters,
  type UpstreamDeps,
} from "../src/upstream";
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

describe("guardedPlan - the unit is a plan, not a call", () => {
  // reviewer-14: the old shape reserved PLAN_UPSTREAM_COST and then made exactly ONE call, so the two ways a
  // caller might read it were 12x apart and neither was tested. Under the looping reading, an anon user with
  // 3 plans a day was exhausted after 3 real requests and the monthly counter ran 12x hot.
  const planArgs = { userId: "u1", tier: "free" as const };

  it("reserves ONCE for a plan that makes many calls", async () => {
    const { deps, calls, reserved } = harness();
    await guardedPlan(deps, planArgs, async (call) => {
      for (let i = 0; i < PLAN_UPSTREAM_COST; i += 1) await call(`https://routing.example/${i}`);
    });
    expect(calls).toHaveLength(PLAN_UPSTREAM_COST);
    expect(reserved).toEqual([{ userId: "u1", upstreamCalls: PLAN_UPSTREAM_COST }]);
  });

  it("refuses the call past the budget, and does not make it", async () => {
    // P-COST-04 wants <= 12 requests per plan. A cap that fires after the request has gone out is not a cap.
    const { deps, calls } = harness();
    await expect(
      guardedPlan(deps, planArgs, async (call) => {
        for (let i = 0; i <= PLAN_UPSTREAM_COST; i += 1) await call(`https://routing.example/${i}`);
      }),
    ).rejects.toBeInstanceOf(PlanBudgetExceeded);
    expect(calls).toHaveLength(PLAN_UPSTREAM_COST);
  });

  it("reserves before the plan body runs, not before each call", async () => {
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
      fetchImpl: async () => {
        order.push("fetch");
        return new Response("ok");
      },
    };
    await guardedPlan(wrapped, planArgs, async (call) => {
      await call("https://routing.example/a");
      await call("https://routing.example/b");
    });
    expect(order).toEqual(["reserve", "fetch", "fetch"]);
  });

  it("makes NO call at all when the plan is refused", async () => {
    const { deps, calls, reserved } = harness({ plansUsedToday: 999 });
    await expect(
      guardedPlan(deps, planArgs, async (call) => call("https://routing.example/a")),
    ).rejects.toBeInstanceOf(UpstreamPaused);
    expect(calls).toEqual([]);
    expect(reserved).toEqual([]);
  });

  it("guardedUpstream is a plan of one call and still reserves exactly one plan", async () => {
    const { deps, calls, reserved } = harness();
    await guardedUpstream(deps, args);
    expect(calls).toHaveLength(1);
    expect(reserved).toEqual([{ userId: "u1", upstreamCalls: PLAN_UPSTREAM_COST }]);
  });

  it("the reservation is an upper bound on calls actually made", async () => {
    const { deps, calls, reserved } = harness();
    await guardedPlan(deps, planArgs, async (call) => {
      await call("https://routing.example/only-one");
    });
    expect(calls.length).toBeLessThanOrEqual(reserved[0].upstreamCalls);
  });
});
