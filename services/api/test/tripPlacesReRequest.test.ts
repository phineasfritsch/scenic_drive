/**
 * T-0318 rv1 (R9-R11): a closure re-request ships a DIFFERENT split, and that split's places are its own read. Through
 * handleTrip with the T-0318 deps over closuresCrossingTrip's fixture: the chosen DETOUR crosses the stored closure X,
 * the re-request carrying X answers BOWED (2 degrees south at its middle, outside the DETOUR's box), and the corpus
 * holds an inn at every BOWED vertex plus a stop by BOWED's vertex 10. The box oracle is typed out from R3.
 */
import { describe, expect, it } from "vitest";
import type { ClosureSnapshot } from "../src/closuresStore";
import type { ClosureCollection } from "../src/customModel";
import type { RoadTripPlace } from "../src/roadTrip";
import { handleTrip } from "../src/trip";
import type { PlacesBox } from "../src/tripPlacesBox";
import { TEST_VERSION } from "./closuresFake";
import { BIG_SUR, FAST_EDGE_MS, NOW, ORIGIN, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath, tripRequest } from "./tripHarness";

const EARTH_M = 6_371_008.8;
const PAD_M = 16_000;
const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;
type LL = { lat: number; lon: number };

/** R3 typed out: the vertices' extremes padded 16 km, outward on the 0.1 degree grid, clamped / full width. */
function oracle(points: LL[]): PlacesBox {
  const lats = points.map((p) => p.lat), lons = points.map((p) => p.lon);
  const padDeg = deg(PAD_M / EARTH_M);
  const south = Math.max(-90, Math.floor((Math.min(...lats) - padDeg) * 10) / 10);
  const north = Math.min(90, Math.ceil((Math.max(...lats) + padDeg) * 10) / 10);
  const ratio = Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(Math.max(-south, north)));
  if (!(ratio < 1)) return { south, north, west: -180, east: 180 };
  const lonPad = deg(2 * Math.asin(ratio));
  const west = Math.floor((Math.min(...lons) - lonPad) * 10) / 10;
  const east = Math.ceil((Math.max(...lons) + lonPad) * 10) / 10;
  return west < -180 || east > 180 ? { south, north, west: -180, east: 180 } : { south, north, west, east };
}
const inBox = (b: PlacesBox, p: LL) => p.lat >= b.south && p.lat <= b.north && p.lon >= b.west && p.lon <= b.east;
const ll = ([lon, lat]: [number, number]): LL => ({ lat, lon });

type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
function square(name: string, c: LL, half = 0.0005): Feature {
  const ring = [[c.lon - half, c.lat - half], [c.lon + half, c.lat - half], [c.lon + half, c.lat + half],
    [c.lon - half, c.lat + half], [c.lon - half, c.lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
/** 50 squares due south of an end, nearer that end's corridor than X: X is stored, not sent, and DETOUR crosses it. */
const south = (tag: string, c: LL) => Array.from({ length: 50 }, (_, i) => square(`${tag}-${i + 1}`, { lat: c.lat - 0.01 - (i + 1) * 0.002, lon: c.lon }));
const D20: [number, number] = [ROAD[20]![0] + 0.3, ROAD[20]![1] + 0.3];
const DETOUR = ROAD.map((p, i) => (i === 20 ? D20 : p));
const X = square("x", { lon: (ROAD[19]![0] + D20[0]) / 2, lat: (ROAD[19]![1] + D20[1]) / 2 });
const SNAPSHOT: ClosureSnapshot = { version: TEST_VERSION, hazard: null, fetchedAt: NOW.toISOString(),
  closures: { type: "FeatureCollection", features: [...south("o", ll(ROAD[0]!)), ...south("l", ll(ROAD[40]!)), X] } as ClosureCollection };
const BOWED = ROAD.map(([lon, lat], i) => [lon, lat - 2 * Math.sin((Math.PI * i) / (ROAD.length - 1))] as [number, number]);
const CORPUS: RoadTripPlace[] = [...BOWED.map(([lon, lat], i) => ({ name: `Inn-${i}`, kind: "lodging" as const, score: 0, coordinate: { lat, lon } })),
  { name: "Bow Stop", kind: "stop", score: 0, coordinate: ll(BOWED[10]!) }];
const carriesX = (body: Record<string, unknown>) =>
  JSON.stringify((body.custom_model as { areas?: unknown } | undefined)?.areas ?? null).includes(JSON.stringify(X.geometry.coordinates));
const DETOUR_BOX = oracle(DETOUR.map(ll));
const BOWED_BOX = oracle(BOWED.map(ll));

/** One paid 2-day trip; the read numbered `throwOn` (1 = the DETOUR split's, 2 = the re-request's, 0 = none) throws. */
async function trip(throwOn: 0 | 1 | 2) {
  const sent: Record<string, unknown>[] = [];
  let scenic = 0;
  const fetchImpl = async (_input: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push(body);
    if (body.profile === "car_fast") return new Response(tripPath(ROAD, FAST_EDGE_MS));
    const points = body.points as [number, number][];
    if (JSON.stringify(points) !== JSON.stringify(sent[0]!.points)) return new Response(tripPath([points[0]!, points[1]!], 1000));
    scenic += 1;
    if (scenic === 1) return new Response(tripPath(ROAD, FAST_EDGE_MS));
    return new Response(tripPath(carriesX(body) ? BOWED : DETOUR, SCENIC_EDGE_MS));
  };
  const reads: PlacesBox[] = [];
  const response = await handleTrip(tripRequest({ ...TRIP_BODY, origin: ORIGIN, days: 2 }), {}, {
    upstream: { counters: tripCounters([]).counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id: string) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier: "paid" as const }),
    closures: async () => SNAPSHOT,
    tripPlaces: async (box: PlacesBox) => {
      reads.push(box);
      if (reads.length === throwOn) throw new Error("D1 unavailable");
      return CORPUS.filter((p) => inBox(box, p.coordinate));
    },
  });
  const json = (await response.json()) as { route: { coordinates: [number, number][] }; places_searched: boolean;
    days: { stops: string[]; overnight: unknown }[] };
  return { status: response.status, reRequested: sent.filter(carriesX).length, reads, route: json.route.coordinates,
    places_searched: json.places_searched, days: json.days.map((d) => [d.stops, d.overnight]) };
}

const SEARCHED = { places_searched: true, days: [[["Bow Stop"], { kind: "lodging", name: "Inn-20", meters: 0 }], [[], null]] };
const NOT_SEARCHED = { places_searched: false, days: [[[], { kind: "not_searched" }], [[], null]] };

describe("a closure re-request's split reads its own path's box, and its places are the ones that ship (T-0318 rv1)", () => {
  it("the fixture: BOWED's middle is outside the DETOUR's box, and so are its inn and stop", () => {
    expect([JSON.stringify(DETOUR_BOX) === JSON.stringify(BOWED_BOX), inBox(DETOUR_BOX, ll(BOWED[20]!)),
      inBox(DETOUR_BOX, ll(BOWED[10]!)), inBox(BOWED_BOX, ll(BOWED[20]!)), inBox(BOWED_BOX, ll(BOWED[10]!))])
      .toEqual([false, false, false, true, true]);
  });

  it("the re-request reads [DETOUR's box, BOWED's box] and ships BOWED with its stop and its boundary inn (whole answer)", async () => {
    expect(await trip(0)).toEqual({ status: 200, reRequested: 1, reads: [DETOUR_BOX, BOWED_BOX], route: BOWED, ...SEARCHED });
  });

  it("the re-request's read throws after the first answered: places_searched false and every night not_searched", async () => {
    expect(await trip(2)).toEqual({ status: 200, reRequested: 1, reads: [DETOUR_BOX, BOWED_BOX], route: BOWED, ...NOT_SEARCHED });
  });

  it("the first read throws and the re-request's answers: places_searched true and BOWED's inn and stop", async () => {
    expect(await trip(1)).toEqual({ status: 200, reRequested: 1, reads: [DETOUR_BOX, BOWED_BOX], route: BOWED, ...SEARCHED });
  });

  it("no row ignores the shipped read: the two mirrored rows differ, and the first read's outcome never reaches the answer", async () => {
    const [none, first, second] = [await trip(0), await trip(1), await trip(2)];
    expect([JSON.stringify(first) === JSON.stringify(second), JSON.stringify(first) === JSON.stringify(none),
      first.places_searched, second.places_searched]).toEqual([false, true, true, false]);
  });
});
