/**
 * T-0248 R3: /plan over the t0221 santa-monica-topanga recording returns what `ops/plan` printed for it.
 *
 * The expected URL, lambda and ETA are LITERALS typed from the task Log's quoted run of
 *   ops/plan 34.02,-118.49 34.0676,-118.5957 25 --recorded Tests/Fixtures/t0221/santa-monica-topanga
 * and the route is the recorded lambda-7.75.json's own bytes, parsed here - never values the module under test
 * computed. Every assertion is EXACT equality.
 */
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import { handlePlan } from "../src/plan";
import { harness, planRequest, SANTA_MONICA_TOPANGA, SANTA_MONICA_TOPANGA_BODY, SANTA_MONICA_TOPANGA_FILES } from "./planHarness";

const OPS_PLAN_URL =
  "https://maps.apple.com/directions?source=34.02000,-118.49000&destination=34.06760,-118.59570" +
  "&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540" +
  "&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722" +
  "&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288" +
  "&mode=driving";

/** `12m34s`, typed out here (SantaMonica ops/plan prints ETA lines in this spelling). */
function clock(seconds: number): string {
  const whole = Math.round(seconds);
  const mm = Math.floor(whole / 60);
  const ss = whole % 60;
  return `${mm}m${ss < 10 ? "0" : ""}${ss}s`;
}

interface PlanBody {
  route: { coordinates: number[][]; distance_m: number };
  eta_s: number;
  fastest_eta_s: number;
  ceiling_s: number;
  budget_s: number;
  lambda: number;
  evaluations: number;
  used_budget: boolean;
  eta_is_estimate: boolean;
  hazards: unknown[];
  waypoints: { lat: number; lon: number }[];
  apple_maps_url: string;
}

const recordedPath = (text: string) => JSON.parse(text).paths[0] as { time: number; distance: number; points: { coordinates: number[][] } };

describe("POST /plan over the t0221 santa-monica-topanga recording (R3)", () => {
  it("Santa Monica -> Topanga +25 returns ops/plan's Apple Maps URL, ETA and route for the recording", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const response = await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    expect(response.status).toBe(200);
    const body = (await response.json()) as PlanBody;

    const chosen = recordedPath(SANTA_MONICA_TOPANGA_FILES.get(7.75)!);
    const fastest = recordedPath(SANTA_MONICA_TOPANGA.fastest);

    expect(body.apple_maps_url).toBe(OPS_PLAN_URL);
    expect(body.lambda).toBe(7.75);
    expect(body.evaluations).toBe(6);
    expect(body.used_budget).toBe(false);
    expect(body.eta_s).toBe(1346.01);
    expect(body.eta_s).toBe(chosen.time / 1000);
    expect(clock(body.eta_s)).toBe("22m26s");
    expect(body.fastest_eta_s).toBe(fastest.time / 1000);
    expect(clock(body.fastest_eta_s)).toBe("20m14s");
    expect(body.budget_s).toBe(1500);
    expect(body.ceiling_s).toBe(fastest.time / 1000 + 1500);
    expect(clock(body.ceiling_s)).toBe("45m14s");
    expect(body.route).toEqual({ coordinates: chosen.points.coordinates, distance_m: chosen.distance });
    expect(body.eta_is_estimate).toBe(true);
    expect(body.hazards).toEqual([]);
    // Each waypoint is one of the recorded route's own points, and the URL literal's pin is it at 5 dp.
    const pins = OPS_PLAN_URL.split("&").filter((part) => part.startsWith("waypoint="))
      .map((part) => part.slice("waypoint=".length).split(",").map(Number));
    expect(body.waypoints).toHaveLength(pins.length);
    body.waypoints.forEach((w, i) => {
      expect(chosen.points.coordinates.some(([lon, lat]) => lon === w.lon && lat === w.lat)).toBe(true);
      expect(Math.abs(w.lat - pins[i]![0]!)).toBeLessThanOrEqual(0.0000051);
      expect(Math.abs(w.lon - pins[i]![1]!)).toBeLessThanOrEqual(0.0000051);
    });
  });

  it("the response carries exactly the ruled fields (R8)", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    const body = (await (await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps)).json()) as object;
    expect(Object.keys(body).sort()).toEqual([
      "apple_maps_url", "budget_s", "ceiling_s", "eta_is_estimate", "eta_s", "evaluations", "fastest_eta_s",
      "hazards", "lambda", "plan_token", "route", "used_budget", "waypoints",
    ]);
  });

  it("visits exactly the recorded lambdas, each with buildCustomModel's model and no safety-gate name (P-SAFE-01)", async () => {
    const h = harness(SANTA_MONICA_TOPANGA);
    await handlePlan(planRequest(SANTA_MONICA_TOPANGA_BODY), {}, h.deps);
    const scenic = h.sent.filter((s) => s.body.profile === "car_scenic");
    const fast = h.sent.filter((s) => s.body.profile === "car_fast");
    expect(fast).toHaveLength(1);
    expect(fast[0]!.body.custom_model).toBeUndefined();
    expect(scenic.map((s) => s.body.custom_model)).toEqual([0, 4, 6, 7, 7.5, 7.75].map((l) => buildCustomModel(l, null)));
    for (const request of scenic) {
      const model = JSON.stringify(request.body.custom_model);
      expect(model.includes("road_access")).toBe(false);
      expect(model.includes("surface")).toBe(false);
    }
    expect(h.sent.every((s) => s.url === "https://router.test/route")).toBe(true);
    expect(fast[0]!.body.points).toEqual([[-118.49, 34.02], [-118.5957, 34.0676]]);
  });
});
