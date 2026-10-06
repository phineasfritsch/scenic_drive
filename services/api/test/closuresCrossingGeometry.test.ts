/**
 * T-0286 C1, C2, C4 at the predicate and the picker the routes call: the closed segment-polygon intersection case by
 * case on a unit square (touching, collinear, a one-point path, the ring's closing edge), outer ring only (a path in a
 * hole crosses), the closure id without an lcs_index, and the picker's one re-request: only for a crossed closure the
 * request did not send, never a futile one, the crossers first, the swap's own left-out count in dropped().
 */
import { describe, expect, it } from "vitest";
import { pathCrossesRing } from "../src/closuresCrossing";
import { closurePicker, swappedClosures } from "../src/closuresNearest";
import type { ClosureCollection } from "../src/customModel";

const SQUARE = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]];
const CASES: [string, number[][], boolean][] = [
  ["an empty path", [], false],
  ["one point inside", [[0.5, 0.5]], true],
  ["one point on an edge", [[0.5, 0]], true],
  ["one point at a vertex", [[1, 1]], true],
  ["one point outside", [[2, 2]], false],
  ["a proper crossing", [[-1, 0.5], [2, 0.5]], true],
  ["ending at a vertex", [[2, 2], [1, 1]], true],
  ["starting at a vertex", [[1, 1], [2, 2]], true],
  ["through a vertex, tangent to the corner", [[-1, 0], [1, 2]], true],
  ["collinear, overlapping an edge", [[-1, 0], [2, 0]], true],
  ["collinear, on the edge's line past its end", [[2, 0], [3, 0]], false],
  ["collinear, meeting the edge at its end", [[1, 0], [3, 0]], true],
  ["parallel to an edge, apart", [[-1, -0.5], [2, -0.5]], false],
  ["ending on an edge's interior", [[0.5, -1], [0.5, 0]], true],
  ["starting on an edge's interior", [[0.5, 0], [0.5, -1]], true],
  ["passing the corner outside", [[1.2, 0.9], [0.9, 1.2]], false],
  ["wholly inside, three vertices", [[0.2, 0.2], [0.8, 0.2], [0.5, 0.8]], true],
  ["clear first segment, crossing second", [[-2, -2], [-1, -1], [0.5, 0.5]], true],
  ["crossing only on the third of three segments", [[-3, 0.5], [-2, 0.5], [-1, 0.5], [2, 0.6]], true],
  ["ending on the ring's closing edge", [[-1, 0.5], [0, 0.5]], true],
  ["a far path", [[5, 5], [6, 6], [7, 5]], false],
  ["starting on the top edge's interior (the crossing number calls it outside)", [[0.5, 1], [0.5, 2]], true],
  ["ending on the top edge's interior", [[0.5, 2], [0.5, 1]], true],
  ["ending at the top-left vertex from the north-east", [[1, 2], [0, 1]], true],
  ["collinear on a vertical edge's line, past its end", [[1, 2], [1, 3]], false],
];

describe("the closed segment-polygon intersection (C1)", () => {
  for (const [name, path, crosses] of CASES) {
    it(`${name}: ${crosses ? "crosses" : "does not cross"}`, () => {
      expect(pathCrossesRing(path, SQUARE)).toEqual(crosses);
    });
  }
  it("the ring's CLOSING edge is an edge: a ring from the top-right corner, a path ending on its right side", () => {
    expect(pathCrossesRing([[2, 0.5], [1, 0.5]], [[1, 1], [0, 1], [0, 0], [1, 0], [1, 1]])).toEqual(true);
  });
  it("meta: both verdicts occur, and every case is a different path", () => {
    expect([CASES.some((c) => c[2]), CASES.some((c) => !c[2]), new Set(CASES.map((c) => JSON.stringify(c[1]))).size]).toEqual([true, true, CASES.length]);
  });
});

type F = { type: "Feature"; properties?: Record<string, unknown>; geometry: { type: "Polygon"; coordinates: number[][][] } };
const sq = (lon: number, lat: number, name: string | null, h = 0.001, holes: number[][][] = []): F => ({ type: "Feature",
  ...(name === null ? {} : { properties: { lcs_index: name } }),
  geometry: { type: "Polygon", coordinates: [[[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]], ...holes] } });
const set = (features: F[]) => ({ type: "FeatureCollection", features }) as ClosureCollection;
const O = { lat: 34, lon: -118 };
/** n squares due east of O at 0.01 degree steps: the nearer, the earlier. */
const row = (n: number, from = 0) => Array.from({ length: n }, (_, i) => sq(-118 + 0.01 * (from + i + 1), 34, `e${from + i + 1}`));
const coords = (p: number[][]) => p;
/** West to east through the square's centre, 0.004 degrees past each side: clear of its neighbours 0.01 away. */
const through = (f: F) => [[f.geometry.coordinates[0]![0]![0]! - 0.004, f.geometry.coordinates[0]![0]![1]! + 0.001],
  [f.geometry.coordinates[0]![1]![0]! + 0.004, f.geometry.coordinates[0]![0]![1]! + 0.001]];

describe("the picker: which polygons, which ids, one re-request (C2, C4, C5)", () => {
  it("outer ring only: a path inside a hole crosses; the id without an lcs_index is #<stored position>", async () => {
    const holed = sq(-117, 35, null, 0.01, [[[-117.005, 34.995], [-116.995, 34.995], [-116.995, 35.005], [-117.005, 35.005], [-117.005, 34.995]]]);
    const picker = closurePicker(set([sq(-118, 34, "a"), sq(-118.1, 34, "a"), holed]));
    await picker.returned([[-117, 35]], coords, O, O, null);
    expect(picker.crosses()).toEqual(["#2"]);
  });
  it("outer ring only: a path between the outer ring and the hole crosses", async () => {
    const holed = sq(-117, 35, "h", 0.01, [[[-117.005, 34.995], [-116.995, 34.995], [-116.995, 35.005], [-117.005, 35.005], [-117.005, 34.995]]]);
    const picker = closurePicker(set([holed]));
    await picker.returned([[-117.008, 35]], coords, O, O, null);
    expect(picker.crosses()).toEqual(["h"]);
  });
  it("crosses() is in stored order across paths: a later path's earlier-stored closure comes first", async () => {
    const picker = closurePicker(set(row(6)));
    await picker.returned(through(row(6)[4]!), coords, O, O, null);
    await picker.returned(through(row(6)[1]!), coords, O, O, null);
    expect(picker.crosses()).toEqual(["e2", "e5"]);
  });
  it("crossing only a SENT closure: no re-request, the closure named", async () => {
    const picker = closurePicker(set(row(3)));
    let retried = 0;
    const back = await picker.returned(through(row(3)[1]!), coords, O, O, async () => { retried += 1; return [[9, 9]]; });
    expect([retried, back, picker.crosses()]).toEqual([0, through(row(3)[1]!), ["e2"]]);
  });
  it("crossing a dropped closure: one re-request carrying it; a clear answer replaces the path and names nothing", async () => {
    const stored = row(60);
    const picker = closurePicker(set(stored));
    const carried: unknown[] = [];
    const back = await picker.returned(through(stored[59]!), coords, O, O, async (c) => { carried.push(c); return [[9, 9]]; });
    expect([back, picker.crosses(), carried]).toEqual([[[9, 9]], [], [set([...stored.slice(0, 49), stored[59]!])]]);
  });
  it("the re-request still crosses another closure: its path is returned and THAT closure named", async () => {
    const stored = row(60);
    const picker = closurePicker(set(stored));
    const back = await picker.returned(through(stored[59]!), coords, O, O, async () => through(stored[58]!));
    expect([back, picker.crosses()]).toEqual([through(stored[58]!), ["e59"]]);
  });
  it("the re-request fails its route's guards (null): the original is returned and its crossing named", async () => {
    const stored = row(60);
    const picker = closurePicker(set(stored));
    const back = await picker.returned(through(stored[59]!), coords, O, O, async () => null);
    expect([back, picker.crosses()]).toEqual([through(stored[59]!), ["e60"]]);
  });
  it("capped (retry null): the original is returned, the dropped closure named, nothing re-requested", async () => {
    const stored = row(60);
    const picker = closurePicker(set(stored));
    expect([await picker.returned(through(stored[59]!), coords, O, O, null), picker.crosses()]).toEqual([through(stored[59]!), ["e60"]]);
  });
  it("a futile swap (51 crossers, the 50 nearest already sent) makes no request; all 51 named", async () => {
    const tie = Array.from({ length: 51 }, (_, k) => sq(-118, 34, `t${k + 1}`, 0.001 + k * 0.00001));
    const picker = closurePicker(set(tie));
    let retried = 0;
    await picker.returned([[-118, 34]], coords, O, O, async () => { retried += 1; return null; });
    expect([retried, picker.crosses()]).toEqual([0, tie.map((f) => f.properties!.lcs_index)]);
  });
  it("dropped() counts the re-request's own left-out closures: a two-polygon crosser displaces two", async () => {
    const pair = [sq(-117.5, 34, "far"), sq(-117.49, 34, "far")];
    const stored = [...row(60), ...pair];
    const picker = closurePicker(set(stored));
    picker.pick(O, O);
    const first = picker.dropped();
    await picker.returned(through(pair[0]!), coords, O, O, async () => [[9, 9]]);
    expect([first, picker.dropped()]).toEqual([11, 12]);
  });
});

describe("the swap itself (C4)", () => {
  it("the crossers first, then the nearest others in the room left, sent in stored order", () => {
    const stored = row(60);
    expect(swappedClosures(set(stored), O, O, new Set([57, 59]))).toEqual({ closures: set([...stored.slice(0, 48), stored[57]!, stored[59]!]), dropped: 10 });
  });
  it("more crossers than fit: the nearest 50 crossers, nothing else", () => {
    const stored = row(60);
    const all = new Set(Array.from({ length: 60 }, (_, i) => i));
    expect(swappedClosures(set(stored), O, O, all)).toEqual({ closures: set(stored.slice(0, 50)), dropped: 10 });
  });
  it("a crosser that does not fit STOPS the crossers: the farther one-polygon crosser is not taken past it", () => {
    const stored = [...row(49), sq(-117.3, 34, "pair"), sq(-117.29, 34, "pair"), sq(-117.2, 34, "solo")];
    const swap = swappedClosures(set(stored), O, O, new Set(Array.from({ length: 51 }, (_, i) => i)));
    expect(swap).toEqual({ closures: set(stored.slice(0, 49)), dropped: 2 });
  });
});
