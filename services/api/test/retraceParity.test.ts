/**
 * The TS half of the shared retrace fixture (T-0252 R7). Tests/Fixtures/t0252/loops.json is read here AND by
 * Tests/ScenicKitTests/LoopRetraceParityTests.swift; both assert the same IEEE-754 bits of the fraction and the
 * same verdict, recorded from the Swift original. Two green suites over one file = the same answer, exactly -
 * except a loop whose `max_ulps` names, with a witness, the libm call V8 and ucrt round differently.
 */
import { describe, expect, it } from "vitest";
import { angularDifference, isAcceptable, isAcceptableLoop, retraceFraction } from "../src/retrace";
import loopsRaw from "../../../Tests/Fixtures/t0252/loops.json?raw";

interface SharedLoop {
  name: string;
  fraction_bits: string;
  acceptable: boolean | null;
  max_ulps: number;
  points: [number, number][];
}

const loops = (JSON.parse(loopsRaw) as { loops: SharedLoop[] }).loops;
const coordinates = (loop: SharedLoop) => loop.points.map(([lat, lon]) => ({ lat: lat / 1_000_000, lon: lon / 1_000_000 }));

function bits(value: number): string {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, value);
  return view.getBigUint64(0).toString(16).padStart(16, "0");
}

describe("the shared retrace fixture (R7)", () => {
  it("carries at least five loops, both verdicts among them", () => {
    expect(loops.length).toBeGreaterThanOrEqual(5);
    // Five loops with a non-zero fraction are held to EXACT bits; an allowance needs a witnessed libm call.
    expect(loops.filter((l) => l.max_ulps === 0 && l.fraction_bits !== "0".repeat(16)).length).toBeGreaterThanOrEqual(5);
    for (const l of loops) if (l.max_ulps !== 0) expect(typeof (l as { witness?: unknown }).witness).toBe("string");
    expect(loops.some((l) => l.acceptable === true)).toBe(true);
    expect(loops.some((l) => l.acceptable === false)).toBe(true);
  });

  it("every shared loop gives the Swift original's fraction bits and verdict", () => {
    const actual = loops.map((l) => {
      const f = retraceFraction(coordinates(l));
      const off = f === null ? Infinity : Number(BigInt(`0x${bits(f)}`) - BigInt(`0x${l.fraction_bits}`));
      return { name: l.name, within: Math.abs(off) <= l.max_ulps, acceptable: isAcceptableLoop(coordinates(l)) };
    });
    expect(actual).toEqual(loops.map((l) => ({ name: l.name, within: true, acceptable: l.acceptable })));
  });
});

describe("the port's edges (R6)", () => {
  it("the threshold is inclusive at 0.15", () => {
    expect([isAcceptable(0.15), isAcceptable(0.15000000000000002)]).toEqual([true, false]);
  });

  it("the heading comparison wraps", () => {
    expect([angularDifference(350, 10), angularDifference(10, 350), angularDifference(90, 270), angularDifference(359, 1)])
      .toEqual([20, 20, 180, 2]);
  });

  it("a duplicated coordinate is not a retrace (a zero-length segment plants no sample)", () => {
    // RetraceDetectorTests.duplicatedCoordinateIsNotARetrace: bearing(a, a) is 0, so a planted sample would read
    // as due north on a southbound road and every next sample within 25 m would score 180 degrees against it.
    const road = Array.from({ length: 40 }, (_, i) => ({ lat: 34.0689 - i * 0.00045, lon: -118.4452 }));
    road.splice(10, 0, { ...road[10]! });
    expect(retraceFraction(road)).toBe(0);
  });

  it("no fraction for nothing, or for a point that is not one", () => {
    expect(retraceFraction([{ lat: 34, lon: -118 }])).toBeNull();
    expect(retraceFraction([{ lat: 34, lon: -118 }, { lat: 34, lon: -118 }])).toBeNull();
    expect(retraceFraction([{ lat: 91, lon: -118 }, { lat: 34, lon: -118 }])).toBeNull();
    expect(retraceFraction([{ lat: 34, lon: -181 }, { lat: 34, lon: -118 }])).toBeNull();
    expect(retraceFraction([{ lat: Number.NaN, lon: -118 }, { lat: 34, lon: -118 }])).toBeNull();
    expect(isAcceptableLoop([{ lat: 34, lon: -118 }])).toBe(false);
  });
});
