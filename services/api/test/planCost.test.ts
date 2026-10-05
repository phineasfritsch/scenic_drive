/**
 * T-0248 R4/R5 (P-COST-01, P-COST-04): the kill switch and the quota stand in front of every router request
 * /plan makes, and one plan is at most PLAN_UPSTREAM_COST requests. Every case drives `handlePlan` with the
 * counting fake and counts real fetch invocations - never a log line.
 */
import { SELF, env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import { ROUTES } from "../src/index";
import { handlePlan } from "../src/plan";
import { harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

describe("POST /plan spend control (R4, P-COST-01)", () => {
  it("KILL=1 returns 503 with zero upstream calls and no reservation", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const response = await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), { KILL: "1" }, h.deps);
    expect(response.status).toBe(503);
    expect(((await response.json()) as { error: string }).error).toBe("planning_paused");
    expect(h.sent).toEqual([]);
    expect(h.events).toEqual([]);
  });

  it("KILL=1 is honoured before the body is even read", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const response = await handlePlan(planRequest("{not json"), { KILL: "1" }, h.deps);
    expect(response.status).toBe(503);
    expect(h.events).toEqual([]);
  });

  it("KILL other than exactly 1 does not pause planning", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const response = await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), { KILL: "0" }, h.deps);
    expect(response.status).toBe(200);
  });

  it("the quota is reserved once, before the first upstream call", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    expect(h.events).toEqual(["reserve", "fetch", "fetch", "fetch", "fetch", "fetch", "fetch", "fetch"]);
    expect(h.reserved).toEqual([12]);
  });

  it("an exhausted daily quota is 429 with resets_at and zero upstream calls", async () => {
    const h = harness(SANTA_MONICA_TOPANGA, { plansUsedToday: 10 });
    const response = await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    expect(response.status).toBe(429);
    expect(await response.json()).toEqual({ error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" });
    expect(h.sent).toEqual([]);
    expect(h.events).toEqual([]);
  });

  it("a tripped monthly counter is 503 planning_paused with zero upstream calls", async () => {
    const h = harness(SANTA_MONICA_TOPANGA, { monthlyUpstreamCalls: 225_000 });
    const response = await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    expect(response.status).toBe(503);
    expect(((await response.json()) as { error: string }).error).toBe("planning_paused");
    expect(h.sent).toEqual([]);
  });
});

describe("POST /plan request count (R5, P-COST-04)", () => {
  it("one plan makes 7 upstream requests - at most 12 - one in flight at a time", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    expect(h.sent).toHaveLength(7);
    expect(h.sent.length).toBeLessThanOrEqual(12);
    expect(h.maxInFlight()).toBe(1);
  });
});

describe("ROUTES['/plan'] - the shipped wiring (R4)", () => {
  it("ROUTES lists /plan", () => {
    expect(typeof ROUTES["/plan"]).toBe("function");
  });

  it("with no router, counters or corpus configured it answers 503 planning_unavailable", async () => {
    const response = await SELF.fetch("https://scenic-api.test/plan", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(SANTA_MONICA_TOPANGA_BODY),
    });
    expect(response.status).toBe(503);
    expect(((await response.json()) as { error: string }).error).toBe("planning_unavailable");
  });

  it("KILL=1 on the shipped route answers 503 planning_paused", async () => {
    (env as unknown as { KILL?: string }).KILL = "1";
    try {
      const response = await SELF.fetch("https://scenic-api.test/plan", { method: "POST", body: "{}" });
      expect(response.status).toBe(503);
      expect(((await response.json()) as { error: string }).error).toBe("planning_paused");
    } finally {
      delete (env as unknown as { KILL?: string }).KILL;
    }
  });
});
