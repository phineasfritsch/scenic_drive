/**
 * T-0248 R7: src/appleMaps.ts ports Sources/Handoff/AppleMapsDirections.swift. Expected strings typed out.
 */
import { describe, expect, it } from "vitest";
import { appleMapsUrl, coordinateText } from "../src/appleMaps";

describe("appleMapsUrl - the AppleMapsDirections port", () => {
  it("spells source, destination, waypoints in order, then mode=driving", () => {
    expect(appleMapsUrl({ lat: 34.02, lon: -118.49 }, { lat: 34.0676, lon: -118.5957 },
      [{ lat: 34.1, lon: -118.2 }, { lat: 34.05, lon: -118.3 }]))
      .toBe("https://maps.apple.com/directions?source=34.02000,-118.49000&destination=34.06760,-118.59570"
        + "&waypoint=34.10000,-118.20000&waypoint=34.05000,-118.30000&mode=driving");
  });

  it("rounds half away from zero at 5 decimals, as Swift's rounded() does, on both signs", () => {
    expect(coordinateText({ lat: 0.000005, lon: -0.000005 })).toBe("0.00001,-0.00001");
    expect(coordinateText({ lat: 12.3456749, lon: -12.3456751 })).toBe("12.34567,-12.34568");
    expect(coordinateText({ lat: -0.000004, lon: 0 })).toBe("0.00000,0.00000");
    expect(coordinateText({ lat: 90, lon: -180 })).toBe("90.00000,-180.00000");
  });

  it("refuses a coordinate out of range or not finite", () => {
    expect(() => coordinateText({ lat: 90.000001, lon: 0 })).toThrow();
    expect(() => coordinateText({ lat: 0, lon: -180.000001 })).toThrow();
    expect(() => coordinateText({ lat: Number.NaN, lon: 0 })).toThrow();
  });

  it("refuses more than 9 waypoints and accepts exactly 9", () => {
    const at = (i: number) => ({ lat: 34 + i / 100, lon: -118 });
    expect(() => appleMapsUrl(at(0), at(1), Array.from({ length: 10 }, (_, i) => at(i)))).toThrow();
    expect(appleMapsUrl(at(0), at(1), Array.from({ length: 9 }, (_, i) => at(i))).split("&waypoint=")).toHaveLength(10);
  });
});
