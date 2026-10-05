/**
 * The TS half of T-0263's shared reach fixture (R5). Tests/Fixtures/t0263/isochrone.json (a body as /isochrone
 * emits it) and points.json (58 points, hand-ruled) are read here AND by
 * Tests/ScenicKitTests/Surprise/SurpriseReachParityTests.swift, and both compare the WHOLE answer array to the
 * recorded one. Two green suites over one file = the Swift port answers what the reference answers, exactly.
 */
import { describe, expect, it } from "vitest";
import type { ReachBucket } from "../src/isochronePlanner";
import { roundTripMinutesAt } from "../src/surpriseReach";
import bodyRaw from "../../../Tests/Fixtures/t0263/isochrone.json?raw";
import pointsRaw from "../../../Tests/Fixtures/t0263/points.json?raw";

interface SharedPoint {
  name: string;
  why: string;
  lat: number;
  lon: number;
  round_trip_minutes: number | null;
}

const body = JSON.parse(bodyRaw) as { minutes: number; buckets: ReachBucket[] };
const points = (JSON.parse(pointsRaw) as { points: SharedPoint[] }).points;

describe("the shared reach fixture (T-0263 R5)", () => {
  it("carries at least 40 points over at least 3 buckets, a hole among them, and every answer", () => {
    expect(points.length).toBeGreaterThanOrEqual(40);
    expect(body.buckets.length).toBeGreaterThanOrEqual(3);
    expect(body.buckets.some((b) => b.polygon.coordinates.length > 1)).toBe(true);
    const answers = new Set(points.map((p) => p.round_trip_minutes));
    expect([...answers].sort()).toEqual([...new Set([...body.buckets.map((b) => b.round_trip_minutes), null])].sort());
  });

  it("every shared point gets the recorded round-trip minutes from roundTripMinutesAt", () => {
    const actual = points.map((p) => ({ name: p.name, minutes: roundTripMinutesAt(body.buckets, { lat: p.lat, lon: p.lon }) }));
    expect(actual).toEqual(points.map((p) => ({ name: p.name, minutes: p.round_trip_minutes })));
  });
});
