/**
 * T-0282 N3-N4 at the selection itself (the route rows are closuresNearest.test.ts): the metric's cases - a corridor
 * crossing a polygon, an origin inside one, a polygon beside the corridor's middle, a point corridor - a closure as a
 * run of features sharing lcs_index, the prefix fill that stops at the first closure that does not fit, and the
 * stored order of what is sent. Expectations are built by hand from the geometry, never from the module.
 */
import { describe, expect, it } from "vitest";
import { closurePicker, nearestClosures } from "../src/closuresNearest";
import type { ClosureCollection } from "../src/customModel";

type Pt = { lat: number; lon: number };
const sq = (name: string | null, c: Pt, half = 0.0005) => ({ type: "Feature" as const,
  properties: name === null ? {} : { lcs_index: name },
  geometry: { type: "Polygon" as const, coordinates: [[[c.lon - half, c.lat - half], [c.lon + half, c.lat - half],
    [c.lon + half, c.lat + half], [c.lon - half, c.lat + half], [c.lon - half, c.lat - half]]] } });
const fc = (features: ReturnType<typeof sq>[]) => ({ type: "FeatureCollection", features }) as ClosureCollection;
const names = (set: ClosureCollection | null) => set?.features.map((f) => (f.properties as { lcs_index?: string }).lcs_index ?? "-") ?? null;
/** n squares due south of `o`, 0.01 + 0.002 i degrees: farther with i from any corridor heading north. */
const south = (o: Pt, n: number, tag = "s") => Array.from({ length: n }, (_, i) => sq(`${tag}${i + 1}`, { lat: o.lat - 0.01 - (i + 1) * 0.002, lon: o.lon }));

const A = { lat: 34.0, lon: -118.5 };
const B = { lat: 34.2, lon: -118.5 };

describe("the metric (N3)", () => {
  it("a polygon the corridor crosses beats every one beside it, wherever it is stored", () => {
    const r = nearestClosures(fc([...south(A, 50), sq("cross", { lat: 34.1, lon: -118.5 })]), A, B);
    expect([r.dropped, names(r.closures)]).toEqual([1, [...south(A, 49).map((f) => f.properties.lcs_index), "cross"]]);
  });

  it("a polygon beside the corridor's MIDDLE ranks by its perpendicular distance, not its distance to an end", () => {
    const near = sq("beside-middle", { lat: 34.1, lon: -118.5 + 0.02 });
    const r = nearestClosures(fc([...south(A, 50), near]), A, B);
    expect([r.dropped, names(r.closures)!.at(-1), names(r.closures)!.includes("s50")]).toEqual([1, "beside-middle", false]);
  });

  it("a point corridor (a loop's start) inside a polygon: distance 0, kept over 50 nearer-stored ones", () => {
    const r = nearestClosures(fc([...south(A, 50), sq("holds-start", A, 0.002)]), A, A);
    expect([r.dropped, names(r.closures)!.at(-1)]).toEqual([1, "holds-start"]);
  });

  it("a long bar the corridor crosses, its corners kilometres off: distance 0, kept over 50 squares beside the line", () => {
    const beside = Array.from({ length: 50 }, (_, i) => sq(`b${i + 1}`, { lat: 34.1, lon: -118.5 + 0.003 + i * 0.0005 }));
    const bar = { ...sq("bar", { lat: 34.1, lon: -118.5 }), geometry: { type: "Polygon" as const, coordinates: [[[-118.55, 34.0995],
      [-118.45, 34.0995], [-118.45, 34.1005], [-118.55, 34.1005], [-118.55, 34.0995]]] } };
    const r = nearestClosures(fc([...beside, bar]), A, B);
    expect([r.dropped, names(r.closures)!.at(-1), names(r.closures)!.includes("b50")]).toEqual([1, "bar", false]);
  });

  it("a start inside a large polygon whose edges lie past 50 others: distance 0, kept", () => {
    const nearer = Array.from({ length: 50 }, (_, i) => sq(`n${i + 1}`, { lat: A.lat - 0.002 - i * 0.0005, lon: A.lon }));
    const r = nearestClosures(fc([...nearer, sq("around", A, 0.05)]), A, A);
    expect([r.dropped, names(r.closures)!.at(-1), names(r.closures)!.includes("n50")]).toEqual([1, "around", false]);
  });

  it("a polygon on the corridor's LINE past either end is as far as its distance to that end, not 0", () => {
    const pastB = nearestClosures(fc([sq("line-past-b", { lat: 35.0, lon: -118.5 }), ...south(A, 50)]), A, B);
    const beforeA = nearestClosures(fc([sq("line-before-a", { lat: 33.0, lon: -118.5 }),
      ...Array.from({ length: 50 }, (_, i) => sq(`e${i + 1}`, { lat: 34.1, lon: -118.5 + 0.003 + i * 0.001 }))]), A, B);
    expect([pastB.dropped, names(pastB.closures)!.includes("line-past-b"), beforeA.dropped, names(beforeA.closures)!.includes("line-before-a")])
      .toEqual([1, false, 1, false]);
  });

  it("a long bar just past either END, its corners kilometres off: as near as the end's gap to its edge, kept", () => {
    const beside = Array.from({ length: 50 }, (_, i) => sq(`b${i + 1}`, { lat: 34.1, lon: -118.5 + 0.003 + i * 0.0005 }));
    const bar = (name: string, lat: number) => ({ ...sq(name, { lat, lon: -118.5 }), geometry: { type: "Polygon" as const,
      coordinates: [[[-118.55, lat - 0.0005], [-118.45, lat - 0.0005], [-118.45, lat + 0.0005], [-118.55, lat + 0.0005], [-118.55, lat - 0.0005]]] } });
    const pastB = nearestClosures(fc([...beside, bar("bar-past-b", B.lat + 0.0011)]), A, B);
    const beforeA = nearestClosures(fc([...beside, bar("bar-before-a", A.lat - 0.0011)]), A, B);
    expect([pastB.dropped, names(pastB.closures)!.at(-1), beforeA.dropped, names(beforeA.closures)!.at(-1)])
      .toEqual([1, "bar-past-b", 1, "bar-before-a"]);
  });

  it("metres, not degrees: a square 0.0115 deg east is nearer than one 0.0100 deg north at lat 34 (91961 vs 110946 m/deg)", () => {
    const close = Array.from({ length: 49 }, (_, i) => sq(`c${i + 1}`, { lat: A.lat - 0.002 - i * 0.0001, lon: A.lon }));
    const r = nearestClosures(fc([...close, sq("north", { lat: A.lat + 0.01, lon: A.lon }), sq("east", { lat: A.lat, lon: A.lon + 0.0115 })]), A, A);
    expect([r.dropped, names(r.closures)!.at(-1)]).toEqual([1, "east"]);
  });

  it("a destination end near a polygon counts as much as the origin end", () => {
    const r = nearestClosures(fc([...south(A, 50), sq("past-b", { lat: B.lat + 0.001, lon: B.lon })]), A, B);
    expect([r.dropped, names(r.closures)!.at(-1)]).toEqual([1, "past-b"]);
  });
});

describe("closures and the prefix fill (N3, N4)", () => {
  it("a two-gate closure is one closure: at 49, it does not fit, the fill STOPS, the farther single is not kept", () => {
    const set = fc([...south(A, 49), sq("gate", { lat: 33.8, lon: -118.5 }), sq("gate", { lat: 33.79, lon: -118.5 }),
      sq("last", { lat: 33.5, lon: -118.5 })]);
    const r = nearestClosures(set, A, B);
    expect([r.dropped, names(r.closures)]).toEqual([2, south(A, 49).map((f) => f.properties.lcs_index)]);
  });

  it("a gate pair with ONE gate on the corridor is as near as that gate: kept whole, both polygons", () => {
    const set = fc([...south(A, 50), sq("gate", { lat: 34.05, lon: -118.5 }), sq("gate", { lat: 33.0, lon: -118.5 })]);
    const r = nearestClosures(set, A, B);
    expect([r.dropped, names(r.closures)]).toEqual([2, [...south(A, 48).map((f) => f.properties.lcs_index), "gate", "gate"]]);
  });

  it("features without an lcs_index stand alone; the same index apart is two closures", () => {
    const set = fc([sq(null, { lat: 30, lon: -118.5 }), ...south(A, 49), sq(null, { lat: 34.1, lon: -118.5 })]);
    const r = nearestClosures(set, A, B);
    expect([r.dropped, names(r.closures)]).toEqual([1, [...south(A, 49).map((f) => f.properties.lcs_index), "-"]]);
  });

  it("a set of <= 50 polygons is sent unchanged - the same object - and none is dropped", () => {
    const set = fc(south(A, 50).reverse());
    const r = nearestClosures(set, A, B);
    expect([r.dropped, r.closures === set, nearestClosures(null, A, B)]).toEqual([0, true, { closures: null, dropped: 0 }]);
  });

  it("51 ties at distance 0: the first 50 stored are kept", () => {
    const set = fc(Array.from({ length: 51 }, (_, k) => sq(`t${k + 1}`, A, 0.001 + k * 0.00001)));
    const r = nearestClosures(set, A, B);
    expect([r.dropped, names(r.closures)]).toEqual([1, Array.from({ length: 50 }, (_, k) => `t${k + 1}`)]);
  });
});

describe("the picker (N6)", () => {
  it("dropped() is the most any one pick left out, not the sum or the last", () => {
    const G = { lat: 35, lon: -118.5 };
    const set = fc([...south(A, 49), sq("g", G), sq("g", { lat: 35.01, lon: -118.5 }), sq("x", { lat: 34.3, lon: -118.5 })]);
    const picker = closurePicker(set);
    const atG = names(picker.pick(G, G));
    const first = picker.dropped();
    const atA = names(picker.pick(A, A));
    expect([atG!.slice(-3), first, atA!.slice(-1), picker.dropped(), closurePicker(set).dropped()])
      .toEqual([["g", "g", "x"], 2, ["x"], 2, 0]);
  });
});
