import { describe, expect, it } from "vitest";
import {
  buildCustomModel,
  CustomModelError,
  MIN_RING_POSITIONS,
  rejectCustomModel,
  type ClosureCollection,
  type ClosurePolygon,
} from "../src/customModel";

/**
 * The safety gate itself, at the three places review round 1 (agent/rv1-pr91) showed nothing was looking.
 * One concern: what `rejectCustomModel` refuses and what `buildCustomModel` lets out of a poisoned feed.
 * customModel.test.ts owns the plan's multipliers and the clause shape.
 *
 * Every expectation below is TYPED OUT - the refusal strings and the emitted coordinates are written by
 * hand from plan :98-110 and from the message formats in src/customModel.ts, never read back out of the
 * function under test. Each block names the mutant it exists to kill.
 */

/** B1: `mentioned()` matching by prefix (`startsWith`) instead of substring passed all 108 earlier tests. */
describe("(f) a forbidden token is refused wherever it sits inside a string or a key", () => {
  it("refuses road_access in the MIDDLE of a condition, not only at its start", () => {
    const body = { priority: [{ if: "road_class == MOTORWAY || road_access == PRIVATE", multiply_by: "1" }] };
    expect(rejectCustomModel(body)).toBe("custom model mentions road_access at priority[0].if");
  });

  it("refuses a key that merely CONTAINS a forbidden token", () => {
    const body = { priority: [{ if: "scenic_score >= 4", multiply_by: "1", our_road_access_note: 1 }] };
    expect(rejectCustomModel(body)).toBe("custom model mentions road_access at priority[0].our_road_access_note");
  });

  it("refuses a forbidden token that only ENDS a string value", () => {
    expect(rejectCustomModel({ comment: "prefer anything with a sealed surface" })).toBe(
      "custom model mentions surface at comment",
    );
  });

  it("refuses a forbidden token mid-string inside an areas property value, several levels down", () => {
    const body = {
      custom_model: {
        priority: [{ if: "in_a", multiply_by: "0" }],
        areas: {
          type: "FeatureCollection",
          features: [
            { type: "Feature", id: "a", properties: { why: "closed while the surface is relaid" }, geometry: null },
          ],
        },
      },
    };
    expect(rejectCustomModel(body)).toBe(
      "custom model mentions surface at custom_model.areas.features[0].properties.why",
    );
  });

  it("refuses an upper-case token in the MIDDLE of a condition", () => {
    const body = { priority: [{ else_if: "scenic_score >= 4 && ROAD_ACCESS == YES", multiply_by: "1" }] };
    expect(rejectCustomModel(body)).toBe("custom model mentions road_access at priority[0].else_if");
  });
});

/** Nest `levels` objects around `leaf`; the leaf is then walked at depth == levels. */
function nest(levels: number, leaf: unknown): Record<string, unknown> {
  let node: unknown = leaf;
  for (let i = 0; i < levels; i += 1) node = { deeper: node };
  return node as Record<string, unknown>;
}

/** B2: the depth cap returning `null` instead of a refusal passed all 108 earlier tests. */
describe("(g) the 64-level walk cap refuses rather than silently forwarding", () => {
  it("refuses a body nested past 64 levels, naming the depth", () => {
    const problem = rejectCustomModel(nest(70, "harmless"));
    expect(problem).not.toBeNull();
    expect(problem).toContain("custom model nests deeper than 64 levels at deeper.deeper");
  });

  it("refuses at 65 levels even when the deep leaf is the forbidden token itself", () => {
    const problem = rejectCustomModel(nest(65, "road_access == NO"));
    expect(problem).not.toBeNull();
    expect(problem).toContain("custom model nests deeper than 64 levels at");
  });

  it("walks a body just under the cap to the bottom and refuses it by the TOKEN, not the depth", () => {
    const problem = rejectCustomModel(nest(64, "road_access == NO"));
    expect(problem).toContain("custom model mentions road_access at deeper.deeper");
    expect(problem).not.toContain("nests deeper");
  });
});

/** The ring of test (f)/(h), written out rather than computed, so no float arithmetic is in the fixture. */
function squareRing(): number[][] {
  return [
    [-122.4, 37.7],
    [-122.39, 37.7],
    [-122.39, 37.71],
    [-122.4, 37.71],
    [-122.4, 37.7],
  ];
}

function feedWith(geometry: unknown): ClosureCollection {
  return {
    type: "FeatureCollection",
    features: [{ type: "Feature", properties: {}, geometry } as unknown as ClosurePolygon],
  };
}

function thrownBy(run: () => unknown): CustomModelError {
  try {
    run();
  } catch (error) {
    expect(error).toBeInstanceOf(CustomModelError);
    return error as CustomModelError;
  }
  throw new Error("buildCustomModel accepted a geometry it should have refused");
}

/**
 * B3: the head this fixes passed `geometry.coordinates` through by reference behind a lone `Array.isArray`,
 * so foreign members and non-numeric elements reached the router. Kills both `{ ...geometry }` and any
 * return to passing the feed's own `coordinates` array out.
 */
describe("(h) closure geometry is rebuilt, so nothing from the feed reaches the router", () => {
  it("drops foreign members on the closure geometry instead of forwarding them", () => {
    const geometry = {
      type: "Polygon",
      coordinates: [squareRing()],
      bbox: "surface == GRAVEL",
      note: { why: "road_access == PRIVATE" },
    };
    const model = buildCustomModel(2, feedWith(geometry));
    const serialised = JSON.stringify(model);
    expect(serialised).not.toMatch(/surface/i);
    expect(serialised).not.toMatch(/road_access/i);
    expect(Object.keys(model.areas!.features[0]!.geometry).sort()).toEqual(["coordinates", "type"]);
  });

  it("emits the ring as fresh [lon, lat] pairs, position by position", () => {
    const model = buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [squareRing()] }));
    expect(model.areas!.features[0]!.geometry.coordinates).toEqual([
      [
        [-122.4, 37.7],
        [-122.39, 37.7],
        [-122.39, 37.71],
        [-122.4, 37.71],
        [-122.4, 37.7],
      ],
    ]);
  });

  it("shares no array with the feed, so poisoning the feed after the build changes nothing", () => {
    const geometry = { type: "Polygon", coordinates: [squareRing()] };
    const model = buildCustomModel(2, feedWith(geometry));
    const emitted = model.areas!.features[0]!.geometry;
    expect(emitted.coordinates).not.toBe(geometry.coordinates);
    expect(emitted.coordinates[0]).not.toBe(geometry.coordinates[0]);
    expect(emitted.coordinates[0]![0]).not.toBe(geometry.coordinates[0]![0]);

    (geometry.coordinates[0]! as unknown[]).push("surface == GRAVEL");
    (geometry.coordinates as unknown[]).push("road_access == PRIVATE");
    expect(emitted.coordinates).toHaveLength(1);
    expect(emitted.coordinates[0]).toHaveLength(5);
    expect(JSON.stringify(model)).not.toMatch(/surface/i);
    expect(JSON.stringify(model)).not.toMatch(/road_access/i);
  });

  it("refuses a position that is not two finite numbers, by name", () => {
    const poisoned = squareRing();
    poisoned[0] = ["surface == GRAVEL" as unknown as number, 37.7];
    const error = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [poisoned] })));
    expect(error.reason).toBe("closure_position_not_numeric");
    expect(error.message).toBe("closure feature 0 ring 0 position 0 is not two finite numbers (string, number)");
    expect(error.message).not.toMatch(/GRAVEL/);
  });

  it("refuses NaN and a three-element position by name", () => {
    const notFinite = squareRing();
    notFinite[2] = [Number.NaN, 37.71];
    const first = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [notFinite] })));
    expect(first.reason).toBe("closure_position_not_numeric");
    expect(first.message).toBe("closure feature 0 ring 0 position 2 is not two finite numbers (number, number)");

    const triple = squareRing();
    triple[1] = [-122.39, 37.7, 12];
    const second = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [triple] })));
    expect(second.reason).toBe("closure_position_not_numeric");
    expect(second.message).toBe("closure feature 0 ring 0 position 1 is not a [lon, lat] pair (3 elements)");
  });

  it("refuses a ring that does not close on its first position, by name", () => {
    const open = squareRing();
    open[4] = [-122.38, 37.72];
    const error = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [open] })));
    expect(error.reason).toBe("closure_ring_not_closed");
    expect(error.message).toBe("closure feature 0 ring 0 does not close on its first position");
  });

  it("refuses a ring shorter than four positions, by name", () => {
    expect(MIN_RING_POSITIONS).toBe(4);
    const short = squareRing().slice(0, 3);
    const error = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [short] })));
    expect(error.reason).toBe("closure_ring_not_closed");
    expect(error.message).toBe("closure feature 0 ring 0 needs at least 4 positions (3)");
  });

  it("refuses a Polygon with no rings at all, by name", () => {
    const error = thrownBy(() => buildCustomModel(2, feedWith({ type: "Polygon", coordinates: [] })));
    expect(error.reason).toBe("closure_ring_not_closed");
    expect(error.message).toBe("closure feature 0 has no rings");
  });
});
