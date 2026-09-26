import { describe, expect, it } from "vitest";
import {
  buildCustomModel,
  CustomModelError,
  LAMBDA_MAX,
  MAX_CLOSURE_POLYGONS,
  rejectCustomModel,
  bandMultiplier,
  bandSlope,
  BAND_LADDER,
  HIGH_BAND,
  MINOR_CONDITION,
  MINOR_SLOPE,
  type ClosureCollection,
  type ClosurePolygon,
} from "../src/customModel";

/**
 * Every expected value below is TYPED OUT from the plan's "GraphHopper profiles" block (:105-110), not
 * computed from buildCustomModel or bandMultiplier. A test that derives its expectation from the
 * function under test passes for every implementation of it, including the broken ones - that is the
 * defect this repository exists to catch (see test/ro.test.ts on MAX_SQL_LENGTH).
 */
const LAMBDA_GRID = [0, 0.25, 0.5, 1, 2, 4, 8];

/** T-0244's model BY HAND, as serialised: minor 1/(1+2l), then bands >= 7, 6..1, else at 1/(1 + l(7-s)/7). */
const PLAN_MULTIPLIERS = [
  { lambda: 0, minor: "1", bands: ["1", "1", "1", "1", "1", "1", "1", "1"] },
  { lambda: 1, minor: "0.333333", bands: ["1", "0.875", "0.777778", "0.7", "0.636364", "0.583333", "0.538462", "0.5"] },
  { lambda: 2, minor: "0.2", bands: ["1", "0.777778", "0.636364", "0.538462", "0.466667", "0.411765", "0.368421", "0.333333"] },
  { lambda: 8, minor: "0.058824", bands: ["1", "0.466667", "0.304348", "0.225806", "0.179487", "0.148936", "0.127273", "0.111111"] },
];

function square(lon: number, lat: number): ClosurePolygon {
  return {
    type: "Feature",
    geometry: {
      type: "Polygon",
      coordinates: [[[lon, lat], [lon + 0.01, lat], [lon + 0.01, lat + 0.01], [lon, lat + 0.01], [lon, lat]]],
    },
    properties: {},
  };
}

function closures(count: number): ClosureCollection {
  const features: ClosurePolygon[] = [];
  for (let i = 0; i < count; i += 1) features.push(square(-122.4 + i * 0.02, 37.7));
  return { type: "FeatureCollection", features };
}

describe("(a) the built model never names a safety encoded value", () => {
  for (const lambda of LAMBDA_GRID) {
    it(`built model never mentions road_access or surface at lambda ${lambda}`, () => {
      const serialised = JSON.stringify(buildCustomModel(lambda, closures(3)));
      expect(serialised).not.toMatch(/road_access/i);
      expect(serialised).not.toMatch(/surface/i);
    });
  }

  it("drops closure feature properties so a poisoned KV feed cannot smuggle surface in", () => {
    const feed = closures(1);
    feed.features[0]!.properties = { note: "surface == GRAVEL", source: "511 road_access" };
    feed.features[0]!.id = "road_access";
    const serialised = JSON.stringify(buildCustomModel(2, feed));
    expect(serialised).not.toMatch(/road_access/i);
    expect(serialised).not.toMatch(/surface/i);
    expect(buildCustomModel(2, feed).areas!.features[0]!.properties).toEqual({});
  });

  it("emits the plan's clause shape: if / else_if / else with string multiply_by", () => {
    const model = buildCustomModel(1, null);
    expect(model.distance_influence).toBe(0);
    expect(model.priority).toEqual([
      {
        if: "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7",
        multiply_by: "0.333333",
      },
      { else_if: "scenic_score >= 7", multiply_by: "1" },
      { else_if: "scenic_score >= 6", multiply_by: "0.875" },
      { else_if: "scenic_score >= 5", multiply_by: "0.777778" },
      { else_if: "scenic_score >= 4", multiply_by: "0.7" },
      { else_if: "scenic_score >= 3", multiply_by: "0.636364" },
      { else_if: "scenic_score >= 2", multiply_by: "0.583333" },
      { else_if: "scenic_score >= 1", multiply_by: "0.538462" },
      { else: "", multiply_by: "0.5" },
    ]);
    expect(model.areas).toBeUndefined();
  });

  it("keys areas the way the closure clause references them", () => {
    const model = buildCustomModel(2, closures(2));
    expect(model.priority[9]).toEqual({ if: "in_closure_1 || in_closure_2", multiply_by: "0" });
    expect(model.distance_influence).toBe(0);
    expect(model.areas!.type).toBe("FeatureCollection");
    expect(model.areas!.features.map((f) => f.id)).toEqual(["closure_1", "closure_2"]);
    expect(model.areas!.features.map((f) => f.geometry.type)).toEqual(["Polygon", "Polygon"]);
  });
});

describe("(b) rejectCustomModel refuses a request-supplied model that touches the safety gates", () => {
  it("accepts the built model, with and without closures", () => {
    expect(rejectCustomModel(buildCustomModel(0, null))).toBeNull();
    expect(rejectCustomModel(buildCustomModel(8, closures(MAX_CLOSURE_POLYGONS)))).toBeNull();
  });

  it("refuses road_access in a top-level condition", () => {
    const body = { priority: [{ if: "road_access == PRIVATE", multiply_by: "1" }] };
    expect(rejectCustomModel(body)).toMatch(/road_access/);
  });

  it("refuses road_access hidden in a nested else_if clause", () => {
    const body = {
      custom_model: {
        priority: [
          { if: "scenic_score >= 7", multiply_by: "1" },
          { else_if: "road_access == DESTINATION", multiply_by: "1" },
        ],
      },
    };
    expect(rejectCustomModel(body)).toMatch(/road_access/);
  });

  it("refuses surface hidden in an areas feature property", () => {
    const body = {
      custom_model: {
        priority: [{ if: "in_a", multiply_by: "0" }],
        areas: {
          type: "FeatureCollection",
          features: [{ type: "Feature", id: "a", properties: { why: "surface == GRAVEL" }, geometry: null }],
        },
      },
    };
    expect(rejectCustomModel(body)).toMatch(/surface/);
  });

  it("refuses a forbidden encoded value used as an object KEY, not only as a value", () => {
    expect(rejectCustomModel({ priority: [{ if: "x", multiply_by: "1", surface: "PAVED" }] })).toMatch(/surface/);
    expect(rejectCustomModel({ road_access: { a: 1 } })).toMatch(/road_access/);
  });

  it("refuses ROAD_ACCESS whatever its case", () => {
    expect(rejectCustomModel({ priority: [{ if: "ROAD_ACCESS == NO", multiply_by: "1" }] })).toMatch(/road_access/);
  });

  it("refuses a body that is not an object", () => {
    for (const body of [null, undefined, 7, "road_access", true, [{ if: "x", multiply_by: "1" }]]) {
      expect(rejectCustomModel(body)).toBe("custom model must be a JSON object");
    }
  });

  it("accepts an unrelated body", () => {
    expect(rejectCustomModel({ profile: "car_scenic", "ch.disable": true, points: [[-122.4, 37.7]] })).toBeNull();
  });
});

describe("(c) the band multipliers are monotone non-increasing in lambda", () => {
  const SLOPES = [MINOR_SLOPE, ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(bandSlope)];

  it("the constants are the ruled ones: high band 7, minor slope 2, one band per score 6..0", () => {
    expect(HIGH_BAND).toBe(7);
    expect(MINOR_SLOPE).toBe(2);
    expect([...BAND_LADDER]).toEqual([6, 5, 4, 3, 2, 1, 0]);
    expect(MINOR_CONDITION).toBe(
      "(road_class == RESIDENTIAL || road_class == LIVING_STREET || road_class == SERVICE) && scenic_score < 7",
    );
    expect([7, 8, 10].map(bandSlope)).toEqual([0, 0, 0]);
    expect(bandSlope(0)).toBe(1);
    expect(bandSlope(4)).toBeCloseTo(3 / 7, 12);
  });

  it("every band is exactly 1 at lambda 0, and a high band (scenic_score >= 7) at every lambda", () => {
    for (const slope of SLOPES) expect(bandMultiplier(slope, 0)).toBe(1);
    for (const lambda of LAMBDA_GRID) for (const score of [7, 8, 9, 10]) expect(bandMultiplier(bandSlope(score), lambda)).toBe(1);
  });

  it("every band stays monotone non-increasing across the grid and its interval midpoints", () => {
    const sampled = [...LAMBDA_GRID];
    for (let i = 1; i < LAMBDA_GRID.length; i += 1) sampled.push((LAMBDA_GRID[i - 1]! + LAMBDA_GRID[i]!) / 2);
    sampled.sort((a, b) => a - b);
    expect(sampled).toEqual([0, 0.125, 0.25, 0.375, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8]);
    for (let i = 1; i < sampled.length; i += 1) {
      for (const slope of SLOPES) {
        expect(bandMultiplier(slope, sampled[i]!)).toBeLessThanOrEqual(bandMultiplier(slope, sampled[i - 1]!));
      }
    }
  });

  it("duller is penalised at least as hard, the minor clause hardest, and nothing is excluded", () => {
    for (const lambda of LAMBDA_GRID) {
      const bands = SLOPES.map((slope) => bandMultiplier(slope, lambda));
      for (let i = 1; i < bands.length; i += 1) expect(bands[i - 1]!).toBeLessThanOrEqual(bands[i]!);
      expect(bands[0]!).toBeGreaterThan(0);
    }
  });

  it("the built model's multipliers are monotone non-increasing over the grid", () => {
    for (let i = 1; i < LAMBDA_GRID.length; i += 1) {
      const before = buildCustomModel(LAMBDA_GRID[i - 1]!, null).priority;
      const after = buildCustomModel(LAMBDA_GRID[i]!, null).priority;
      expect(after.length).toBe(9);
      for (let clause = 0; clause < after.length; clause += 1) {
        expect(Number(after[clause]!.multiply_by)).toBeLessThanOrEqual(Number(before[clause]!.multiply_by));
      }
    }
  });

  for (const row of PLAN_MULTIPLIERS) {
    it(`matches the hand-evaluated multipliers at lambda ${row.lambda}`, () => {
      const priority = buildCustomModel(row.lambda, null).priority;
      expect(priority[0]!.multiply_by).toBe(row.minor);
      expect(priority.slice(1).map((clause) => clause.multiply_by)).toEqual(row.bands);
    });
  }

  // The same rows as exact doubles, so a rounding change to formatMultiplier cannot hide a maths change.
  it("matches 1/(1+2l), 1/(1+l(7-s)/7) and 1/(1+l) as doubles at lambda 1, 2 and 8", () => {
    expect(bandMultiplier(MINOR_SLOPE, 1)).toBeCloseTo(1 / 3, 12);
    expect(bandMultiplier(bandSlope(6), 1)).toBeCloseTo(0.875, 12);
    expect(bandMultiplier(bandSlope(0), 2)).toBeCloseTo(1 / 3, 12);
    expect(bandMultiplier(bandSlope(4), 2)).toBeCloseTo(7 / 13, 12);
    expect(bandMultiplier(MINOR_SLOPE, 8)).toBeCloseTo(1 / 17, 12);
    expect(bandMultiplier(bandSlope(0), 8)).toBeCloseTo(1 / 9, 12);
  });
});

describe("(d) lambda outside the bisection bracket throws and is never clamped", () => {
  it("throws lambda_out_of_range for a negative lambda", () => {
    expect(() => buildCustomModel(-0.5, null)).toThrow(CustomModelError);
    try {
      buildCustomModel(-0.5, null);
      expect.unreachable("buildCustomModel clamped a negative lambda instead of throwing");
    } catch (error) {
      expect((error as CustomModelError).reason).toBe("lambda_out_of_range");
    }
  });

  it("throws lambda_out_of_range just above the bracket, rather than returning the lambda 8 model", () => {
    expect(LAMBDA_MAX).toBe(8);
    try {
      buildCustomModel(8.000001, null);
      expect.unreachable("buildCustomModel clamped a lambda above 8 instead of throwing");
    } catch (error) {
      expect((error as CustomModelError).reason).toBe("lambda_out_of_range");
    }
  });

  it("throws lambda_not_finite for NaN and Infinity", () => {
    for (const lambda of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
      try {
        buildCustomModel(lambda, null);
        expect.unreachable(`buildCustomModel accepted lambda ${lambda}`);
      } catch (error) {
        expect((error as CustomModelError).reason).toBe("lambda_not_finite");
      }
    }
  });

  it("accepts both ends of the bracket", () => {
    expect(buildCustomModel(0, null).priority[8]!.multiply_by).toBe("1");
    expect(buildCustomModel(8, null).priority[8]!.multiply_by).toBe("0.111111");
  });
});

describe("(e) the closures feed is bounded and must be polygons", () => {
  it("accepts exactly 50 closure polygons", () => {
    expect(MAX_CLOSURE_POLYGONS).toBe(50);
    expect(buildCustomModel(1, closures(50)).areas!.features).toHaveLength(50);
  });

  it("throws too_many_closure_polygons for 51 polygons", () => {
    try {
      buildCustomModel(1, closures(51));
      expect.unreachable("buildCustomModel accepted 51 closure polygons");
    } catch (error) {
      expect((error as CustomModelError).reason).toBe("too_many_closure_polygons");
      expect((error as CustomModelError).message).toMatch(/51/);
    }
  });

  it("throws closure_not_polygon for a LineString feature", () => {
    const feed = closures(1);
    feed.features[0]!.geometry = { type: "LineString" as unknown as "Polygon", coordinates: [] as unknown as number[][][] };
    try {
      buildCustomModel(1, feed);
      expect.unreachable("buildCustomModel accepted a non-Polygon closure");
    } catch (error) {
      expect((error as CustomModelError).reason).toBe("closure_not_polygon");
    }
  });

  it("throws closures_not_feature_collection for a bare array", () => {
    try {
      buildCustomModel(1, [] as unknown as ClosureCollection);
      expect.unreachable("buildCustomModel accepted a bare array of closures");
    } catch (error) {
      expect((error as CustomModelError).reason).toBe("closures_not_feature_collection");
    }
  });
});
