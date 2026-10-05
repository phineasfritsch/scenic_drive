/**
 * T-0248 R1/R2 (P-PRIV-05): the server never receives more than one coordinate per action, never more than
 * 2 decimals. Every case drives `handlePlan` - the handler ROUTES["/plan"] runs - with the counting fake, and
 * a refusal is a 400 with ZERO upstream calls and NO quota reservation: a refused body costs nobody anything.
 */
import { describe, expect, it } from "vitest";
import { handlePlan } from "../src/plan";
import { harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";

const base = SANTA_MONICA_TOPANGA_BODY;

async function refused(body: unknown, status = 400, method = "POST") {
  const h = harness(SANTA_MONICA_TOPANGA);
  const response = await handlePlan(planRequest(body, method), {}, h.deps);
  expect(response.status).toBe(status);
  expect(h.sent).toEqual([]);
  expect(h.events).toEqual([]);
  return (await response.json()) as { error: string; detail?: string };
}

describe("POST /plan privacy - one coordinate, two decimals (R2, P-PRIV-05)", () => {
  it("refuses an origin latitude with more than 2 decimals, with zero upstream calls", async () => {
    const body = await refused({ ...base, origin: { lat: 34.019, lon: -118.49 } });
    expect(body.error).toBe("invalid_request");
  });

  it("refuses an origin longitude with more than 2 decimals, with zero upstream calls", async () => {
    await refused({ ...base, origin: { lat: 34.02, lon: -118.4912 } });
  });

  it("refuses a destination carried as a coordinate - a second coordinate", async () => {
    await refused({ ...base, destination: { lat: 34.07, lon: -118.6 } });
  });

  it("refuses a destination carrying a coordinate beside its place id", async () => {
    await refused({ ...base, destination: { place: "la:topanga", lat: 34.07, lon: -118.6 } });
  });

  it("refuses a second coordinate under any key outside the whitelist", async () => {
    await refused({ ...base, waypoints: [[34.05, -118.55]] });
    await refused({ ...base, via: { lat: 34.05, lon: -118.55 } });
    await refused({ ...base, origin: { lat: 34.02, lon: -118.49, accuracy: 5 } });
  });

  it("refuses an origin that is not a {lat, lon} pair of in-range numbers", async () => {
    await refused({ ...base, origin: [34.02, -118.49] });
    await refused({ ...base, origin: { lat: "34.02", lon: -118.49 } });
    await refused({ ...base, origin: { lat: 91, lon: -118.49 } });
    await refused({ ...base, origin: { lat: 34.02, lon: -181 } });
    await refused({ ...base, origin: { lat: 34.02 } });
  });

  it("accepts an origin at exactly 2 decimals, and sends upstream exactly that one coordinate", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const response = await handlePlan(planRequest(base), {}, h.deps);
    expect(response.status).toBe(200);
    expect(h.sent[0]!.body.points).toEqual([[-118.49, 34.02], [-118.5957, 34.0676]]);
  });
});

describe("POST /plan request shape (R1)", () => {
  it("refuses a request-supplied custom_model naming road_access, never forwarding it (P-SAFE-01)", async () => {
    await refused({ ...base, custom_model: { priority: [{ if: "road_access == PRIVATE", multiply_by: "1" }] } });
  });

  it("refuses a budget that is not a number of minutes in [0, 180]", async () => {
    await refused({ ...base, budget_minutes: -1 });
    await refused({ ...base, budget_minutes: 181 });
    await refused({ ...base, budget_minutes: "25" });
    await refused({ ...base, budget_minutes: null });
  });

  it("accepts the budget bounds 0 and 180 as far as the router", async () => {
    for (const minutes of [0, 180]) {
      const h = harness(SANTA_MONICA_TOPANGA);
      await handlePlan(planRequest({ ...base, budget_minutes: minutes }), {}, h.deps);
      expect(h.sent.length).toBeGreaterThan(0);
    }
  });

  it("refuses a departs_at that is not an ISO-8601 UTC instant, and accepts one that is", async () => {
    await refused({ ...base, departs_at: "tomorrow" });
    await refused({ ...base, departs_at: "2026-10-05T25:00:00Z" });
    await refused({ ...base, departs_at: 1759665600 });
    const h = harness(SANTA_MONICA_TOPANGA);
    const ok = await handlePlan(planRequest({ ...base, departs_at: "2026-10-05T16:30:00Z" }), {}, h.deps);
    expect(ok.status).toBe(200);
  });

  it("refuses a place id that is not a short id string", async () => {
    await refused({ ...base, destination: { place: "" } });
    await refused({ ...base, destination: { place: "a b" } });
    await refused({ ...base, destination: { place: "x".repeat(129) } });
    await refused({ ...base, destination: { place: 7 } });
  });

  it("an unknown place is 404 with zero upstream calls and no reservation", async () => {
    const body = await refused({ ...base, destination: { place: "la:nowhere" } }, 404);
    expect(body.error).toBe("unknown_place");
  });

  it("refuses a body that is not a JSON object, and a method that is not POST", async () => {
    await refused("{not json");
    await refused([base]);
    await refused(null);
    await refused(base, 405, "GET");
  });
});
