/**
 * T-0262 R1-R3, R7, R8: what POST /isochrone accepts, the one GraphHopper request it makes, the whole answer by EXACT
 * equality over the ruled-synthetic router answer, and the conversion a client makes for Surprise.pick's reach.
 * Every case drives the SHIPPED ROUTES["/isochrone"] (deps from env).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { roundTripMinutesAt } from "../src/surpriseReach";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { expectedReach, isochroneAnswer, isochroneRouter, NOW, reach, REACH_BODY, reachEnv, SECRET, START, wire } from "./isochroneHarness";

let quota: FakeQuota;
let router: ReturnType<typeof isochroneRouter>;
let answer: ((url: URL) => unknown) | undefined;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  answer = undefined;
  router = isochroneRouter(() => {}, (url) => (answer ? answer(url) : isochroneAnswer(START.lat, START.lon, Number(url.searchParams.get("buckets")))));
  vi.stubGlobal("fetch", router.fetchImpl);
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("POST /isochrone answers the reach (R3, R7)", () => {
  it("the whole response equals the buckets of ONE GraphHopper /isochrone GET carrying the secret header", async () => {
    const r = await reach(reachEnv(quota));
    expect(r).toEqual({ status: 200, json: expectedReach(120, 4) });
    expect(router.calls).toEqual([{ url: wire("34.07", "-118.45", 3600, 4), method: "GET", headers: [["x-scenic-router-secret", SECRET]] }]);
  });

  it("the buckets are 15-minute one-way steps up to half the round-trip minutes", async () => {
    const cases: [number, number, number][] = [[30, 900, 1], [59, 900, 1], [60, 1800, 2], [125, 3600, 4], [240, 7200, 8]];
    for (const [minutes, seconds, buckets] of cases) {
      const r = await reach(reachEnv(fakeQuotaNamespace()), { start: START, minutes });
      expect(r).toEqual({ status: 200, json: expectedReach(minutes, buckets) });
      expect(router.calls.at(-1)!.url).toBe(wire("34.07", "-118.45", seconds, buckets));
    }
    expect(router.calls).toHaveLength(5);
  });

  it("a router answer that is not 200, not JSON, misses or repeats a bucket, or is not a Polygon is 502 no_route", async () => {
    const good = isochroneAnswer(START.lat, START.lon, 4) as { polygons: { properties: { bucket: number }; geometry: unknown }[] };
    const last = (geometry: unknown) => ({ polygons: [...good.polygons.slice(1), { ...good.polygons[0]!, geometry }] });
    const bad: unknown[] = [
      new Response(JSON.stringify(good), { status: 500 }),
      new Response("<html>not json</html>", { status: 200 }),
      new Response(JSON.stringify(good).replace(/\[-118\.[0-9]+,/, "[1e999,")),
      { polygons: good.polygons.slice(1) },
      { polygons: [...good.polygons, { ...good.polygons[1]! }] },
      { polygons: [...good.polygons.slice(1), { ...good.polygons[0]!, properties: { bucket: 4 } }] },
      { polygons: [...good.polygons.slice(1), { ...good.polygons[0]!, properties: { bucket: -1 } }] },
      last({ type: "MultiPolygon", coordinates: (good.polygons[0]!.geometry as { coordinates: unknown }).coordinates }),
      last({ type: "Polygon", coordinates: [[[0, 0], [1, 1], [0, 0]]] }),
      last({ type: "Polygon", coordinates: [] }),
      { paths: [] },
    ];
    for (const body of bad) {
      answer = () => body;
      const r = await reach(reachEnv(fakeQuotaNamespace()));
      expect(r.status).toBe(502);
      expect(r.json.error).toBe("no_route");
    }
    expect(router.calls).toHaveLength(bad.length);
  });
});

describe("POST /isochrone takes one coordinate at 2 dp and nothing else (R1, P-PRIV-05)", () => {
  it("every key at every level is whitelisted, the start is at most 2 dp and minutes is in [30, 240]", async () => {
    const refused: unknown[] = [
      { ...REACH_BODY, end: START },
      { start: { ...START, accuracy: 5 }, minutes: 120 },
      { start: { lat: 34.071, lon: -118.45 }, minutes: 120 },
      { start: { lat: 34.07, lon: -118.451 }, minutes: 120 },
      { start: { lat: 91, lon: -118.45 }, minutes: 120 },
      { start: START, minutes: 29 },
      { start: START, minutes: 241 },
      { start: START, minutes: "120" },
      [START],
    ];
    for (const body of refused) {
      const r = await reach(reachEnv(quota), body);
      expect(r.status).toBe(400);
      expect(r.json.error).toBe("invalid_request");
    }
    const missing = await reach(reachEnv(quota), { start: START });
    expect(missing).toEqual({ status: 400, json: { error: "invalid_request", detail: "the body needs minutes" } });
    expect(router.calls).toEqual([]);
    expect(quota.state()).toEqual({});
  });
});

describe("the reach a client hands Surprise.pick (R8)", () => {
  it("a candidate's round-trip minutes is twice the upper bound of the smallest bucket containing it - three points", async () => {
    const { json } = await reach(reachEnv(quota));
    const buckets = json.buckets as Parameters<typeof roundTripMinutesAt>[0];
    expect(roundTripMinutesAt(buckets, { lat: 34.1, lon: -118.45 })).toBe(30);
    expect(roundTripMinutesAt(buckets, { lat: 34.07, lon: -118.32 })).toBe(90);
    expect(roundTripMinutesAt(buckets, { lat: 33.8, lon: -118.45 })).toBeNull();
  });

  it("a point in a bucket's hole is in that bucket only if a larger bucket holds it, and the edges of the polygon are exact", async () => {
    answer = () => ({
      polygons: [
        { type: "Feature", properties: { bucket: 0 }, geometry: { type: "Polygon", coordinates: [
          [[-118.5, 34.02], [-118.4, 34.02], [-118.4, 34.12], [-118.5, 34.12], [-118.5, 34.02]],
          [[-118.46, 34.06], [-118.44, 34.06], [-118.44, 34.08], [-118.46, 34.08], [-118.46, 34.06]],
        ] } },
        { type: "Feature", properties: { bucket: 1 }, geometry: { type: "Polygon", coordinates: [
          [[-118.6, 33.97], [-118.3, 33.97], [-118.45, 34.27], [-118.6, 33.97]],
        ] } },
      ],
    });
    const { json } = await reach(reachEnv(quota), { start: START, minutes: 60 });
    const buckets = json.buckets as Parameters<typeof roundTripMinutesAt>[0];
    expect(roundTripMinutesAt(buckets, { lat: 34.07, lon: -118.45 })).toBe(60);
    expect(roundTripMinutesAt(buckets, { lat: 34.1, lon: -118.42 })).toBe(30);
    expect(roundTripMinutesAt(buckets, { lat: 34.25, lon: -118.45 })).toBe(60);
    expect(roundTripMinutesAt(buckets, { lat: 34.25, lon: -118.38 })).toBeNull();
    expect(roundTripMinutesAt(buckets, { lat: 34.27, lon: -118.5 })).toBeNull();
    expect(roundTripMinutesAt([], START)).toBeNull();
  });
});
