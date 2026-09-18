import { describe, expect, it } from "vitest";
import {
  buildCustomModel,
  CustomModelError,
  LAMBDA_MAX,
  MAX_CLOSURE_POLYGONS,
  rejectCustomModel,
  scenicBandMultipliers,
  type ClosureCollection,
  type ClosurePolygon,
} from "../src/customModel";

/**
 * Every expected value below is TYPED OUT from the plan's "GraphHopper profiles" block (:105-110), not
 * computed from buildCustomModel or scenicBandMultipliers. A test that derives its expectation from the
 * function under test passes for every implementation of it, including the broken ones - that is the
 * defect this repository exists to catch (see test/ro.test.ts on MAX_SQL_LENGTH).
 */
const LAMBDA_GRID = [0, 0.25, 0.5, 1, 2, 4, 8];

/** 1 / (1 + 0.5*lambda) and 1 / (1 + lambda), evaluated by hand, as they are serialised. */
const PLAN_MULTIPLIERS = [
  { lambda: 0, high: "1", mid: "1", low: "1" },
  { lambda: 1, high: "1", mid: "0.666667", low: "0.5" },
  { lambda: 2, high: "1", mid: "0.5", low: "0.333333" },
  { lambda: 8, high: "1", mid: "0.2", low: "0.111111" },
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
    expect(model.priority).toEqual([
      { if: "scenic_score >= 7", multiply_by: "1" },
      { else_if: "scenic_score >= 4", multiply_by: "0.666667" },
      { else: "", multiply_by: "0.5" },
      { if: "road_class == RESIDENTIAL && scenic_score < 7", multiply_by: "0.5" },
    ]);
    expect(model.areas).toBeUndefined();
  });

  it("keys areas the way the closure clause references them", () => {
    const model = buildCustomModel(2, closures(2));
    expect(model.priority[4]).toEqual({ if: "in_closure_1 || in_closure_2", multiply_by: "0" });
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
  it("every band is exactly 1 at lambda 0", () => {
    const m = scenicBandMultipliers(0);
    expect(m.high).toBe(1);
    expect(m.mid).toBe(1);
    expect(m.low).toBe(1);
  });

  it("high band (scenic_score >= 7) is 1 at every lambda on the grid", () => {
    for (const lambda of LAMBDA_GRID) expect(scenicBandMultipliers(lambda).high).toBe(1);
  });

  it("mid band (scenic_score >= 4) is monotone non-increasing over the grid", () => {
    for (let i = 1; i < LAMBDA_GRID.length; i += 1) {
      const previous = scenicBandMultipliers(LAMBDA_GRID[i - 1]!).mid;
      const current = scenicBandMultipliers(LAMBDA_GRID[i]!).mid;
      expect(current).toBeLessThanOrEqual(previous);
    }
  });

  it("low band (else) is monotone non-increasing over the grid", () => {
    for (let i = 1; i < LAMBDA_GRID.length; i += 1) {
      const previous = scenicBandMultipliers(LAMBDA_GRID[i - 1]!).low;
      const current = scenicBandMultipliers(LAMBDA_GRID[i]!).low;
      expect(current).toBeLessThanOrEqual(previous);
    }
  });

  it("the built model's multipliers are monotone non-increasing over the grid", () => {
    for (let i = 1; i < LAMBDA_GRID.length; i += 1) {
      const before = buildCustomModel(LAMBDA_GRID[i - 1]!, null).priority;
      const after = buildCustomModel(LAMBDA_GRID[i]!, null).priority;
      for (const clause of [1, 2]) {
        expect(Number(after[clause]!.multiply_by)).toBeLessThanOrEqual(Number(before[clause]!.multiply_by));
      }
    }
  });

  it("the low band is never zero, because a dull road is penalised and not excluded", () => {
    for (const lambda of LAMBDA_GRID) expect(scenicBandMultipliers(lambda).low).toBeGreaterThan(0);
  });

  for (const row of PLAN_MULTIPLIERS) {
    it(`matches the plan's multipliers at lambda ${row.lambda}`, () => {
      const priority = buildCustomModel(row.lambda, null).priority;
      expect(priority[0]!.multiply_by).toBe(row.high);
      expect(priority[1]!.multiply_by).toBe(row.mid);
      expect(priority[2]!.multiply_by).toBe(row.low);
    });
  }

  // The same four rows as exact doubles, so a rounding change to formatMultiplier cannot hide a maths change.
  it("matches 1/(1+0.5*lambda) and 1/(1+lambda) as doubles at lambda 0, 1, 2 and 8", () => {
    expect(scenicBandMultipliers(0).mid).toBeCloseTo(1, 12);
    expect(scenicBandMultipliers(0).low).toBeCloseTo(1, 12);
    expect(scenicBandMultipliers(1).mid).toBeCloseTo(0.6666666666666666, 12);
    expect(scenicBandMultipliers(1).low).toBeCloseTo(0.5, 12);
    expect(scenicBandMultipliers(2).mid).toBeCloseTo(0.5, 12);
    expect(scenicBandMultipliers(2).low).toBeCloseTo(0.3333333333333333, 12);
    expect(scenicBandMultipliers(8).mid).toBeCloseTo(0.2, 12);
    expect(scenicBandMultipliers(8).low).toBeCloseTo(0.1111111111111111, 12);
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
    expect(buildCustomModel(0, null).priority[2]!.multiply_by).toBe("1");
    expect(buildCustomModel(8, null).priority[2]!.multiply_by).toBe("0.111111");
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
