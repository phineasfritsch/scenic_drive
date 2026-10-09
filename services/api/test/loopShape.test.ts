/**
 * T-0252 R1-R4/R9: what /loop sends and what it answers, each by EXACT equality to a recomputation - the one
 * request body, the seed, and the whole response (geometry, duration, retrace fraction, Apple Maps URL).
 */
import { describe, expect, it } from "vitest";
import { appleMapsUrl } from "../src/appleMaps";
import { buildCustomModel } from "../src/customModel";
import { handleLoop } from "../src/loop";
import { MAX_LOOP_MINUTES, MIN_LOOP_MINUTES, parseLoopRequest } from "../src/loopRequest";
import { fnv1a32, loopSeed, roundTripDistance } from "../src/loopPlanner";
import { decisionPoints } from "../src/planWaypoints";
import { retraceFraction } from "../src/retrace";
import { decodeRoutePath } from "../src/routePath";
import { ROUTE_DETAILS } from "../src/scenicPlanner";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, squareLoop, START } from "./loopHarness";

describe("the /loop request (R1-R4)", () => {
  it("FNV-1a 32 matches the published test vectors", () => {
    expect([fnv1a32(""), fnv1a32("a"), fnv1a32("foobar")]).toEqual([0x811c9dc5, 0xe40c292c, 0xbf9cf968]);
  });

  it("the seed is FNV-1a of user|UTC day", () => {
    expect(loopSeed("device-1", "2026-10-05")).toBe(fnv1a32("device-1|2026-10-05"));
    expect(loopSeed("device-1", "2026-10-06")).not.toBe(loopSeed("device-1", "2026-10-05"));
  });

  it("round_trip.distance is minutes at 40 km/h", () => {
    expect([roundTripDistance(45), roundTripDistance(10), roundTripDistance(180), roundTripDistance(31)])
      .toEqual([30000, 6667, 120000, 20667]);
  });

  it("the one request carries one point - the 2 dp start - and the lambda 2 model, exactly", async () => {
    const h = loopHarness([loopPath(squareLoop())]);
    await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    expect(h.sent).toEqual([{ url: "https://router.test/route", body: {
      points: [[-118.45, 34.07]],
      profile: "car_scenic",
      algorithm: "round_trip",
      "round_trip.distance": 30000,
      "round_trip.seed": fnv1a32("device-1|2026-10-05"),
      points_encoded: false,
      instructions: false,
      "ch.disable": true,
      details: ROUTE_DETAILS,
      custom_model: JSON.parse(JSON.stringify(buildCustomModel(2, null))),
    } }]);
  });
});

describe("the /loop body whitelist (R1, P-PRIV-05)", () => {
  it("accepts exactly {start:{lat,lon}, minutes}", () => {
    expect(parseLoopRequest(LOOP_BODY)).toEqual({ ok: true, request: { start: START, minutes: 45 } });
  });

  it("refuses a start with more than 2 decimals", () => {
    expect(parseLoopRequest({ start: { lat: 34.071, lon: -118.45 }, minutes: 45 }).ok).toBe(false);
    expect(parseLoopRequest({ start: { lat: 34.07, lon: -118.451 }, minutes: 45 }).ok).toBe(false);
  });

  it("refuses any key it does not name, at every level", () => {
    for (const body of [
      { ...LOOP_BODY, end: { lat: 34.1, lon: -118.5 } },
      { ...LOOP_BODY, via: [[34.1, -118.5]] },
      { start: { ...START, alt: 1 }, minutes: 45 },
      { start: START },
      { minutes: 45 },
      { start: { lat: 34.07 }, minutes: 45 },
    ]) expect(parseLoopRequest(body).ok).toBe(false);
  });

  it("minutes must lie in [10, 180]", () => {
    const at = (minutes: unknown) => parseLoopRequest({ start: START, minutes }).ok;
    expect([MIN_LOOP_MINUTES, MAX_LOOP_MINUTES]).toEqual([10, 180]);
    expect([at(10), at(180), at(9.99), at(180.01), at(Number.NaN), at("45")]).toEqual([true, true, false, false, false, false]);
  });

  it("a refused body is 400 with zero upstream calls", async () => {
    const h = loopHarness([loopPath(squareLoop())]);
    const response = await handleLoop(loopRequest({ start: { lat: 34.0712, lon: -118.45 }, minutes: 45 }), {}, h.deps);
    expect(response.status).toBe(400);
    expect(h.events).toEqual([]);
  });
});

describe("the /loop response (R9)", () => {
  it("carries geometry, duration, the retrace fraction and the Apple Maps URL - equal to a recomputation", async () => {
    const text = loopPath(squareLoop(), 2_640_000);
    const h = loopHarness([text]);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
    const path = decodeRoutePath(text);
    const waypoints = decisionPoints(path);
    expect(await response.json()).toEqual({
      route: { coordinates: path.coordinates, distance_m: 4000 },
      duration_s: 2640,
      retrace_fraction: retraceFraction(path.coordinates.map(([lon, lat]) => ({ lat, lon }))),
      attempts: 1,
      seed: fnv1a32("device-1|2026-10-05"),
      target_distance_m: 30000,
      minutes: 45,
      eta_is_estimate: true,
      hazards: [],
      waypoints,
      apple_maps_url: appleMapsUrl(START, START, waypoints),
    });
    expect(waypoints.length).toBeGreaterThan(0);
  });
});
