/**
 * T-0276 R8 past the first request: a loop's retry and retrace attempts keep the feed's closures (feed first, then the
 * retrace squares, at most 50), and a paid trip's day legs carry them - through handleLoop / handleTrip, the handlers
 * ROUTES calls, with injected deps (no shipped identity reaches paid until /attest; T-0256 R3).
 */
import { describe, expect, it } from "vitest";
import type { ClosureSnapshot } from "../src/closuresStore";
import { buildCustomModel, MAX_CLOSURE_POLYGONS, type ClosureCollection } from "../src/customModel";
import { handleLoop } from "../src/loop";
import { handleTrip } from "../src/trip";
import { squareClosure, TEST_VERSION, TWO_CLOSURES } from "./closuresFake";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, outAndBack, squareLoop } from "./loopHarness";
import { BIG_SUR, NOW, ROUTER, TRIP_BODY, tripCounters, tripRequest, tripRouter } from "./tripHarness";

const fresh = (closures: unknown): ClosureSnapshot => ({ version: TEST_VERSION, closures: closures as ClosureCollection, hazard: null, fetchedAt: null });
const AREAS = buildCustomModel(0, TWO_CLOSURES as ClosureCollection).areas!;
const FIFTY = { type: "FeatureCollection", features: Array.from({ length: MAX_CLOSURE_POLYGONS }, (_, i) => squareClosure(-118.9 + i * 0.001, 34.3)) };

async function loopWith(closures: unknown) {
  const h = loopHarness([loopPath(outAndBack(4000)), loopPath(outAndBack(4000)), loopPath(squareLoop())]);
  h.deps.closures = async () => fresh(closures);
  const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
  return { status: response.status, models: h.sent.map((s) => s.body.custom_model as { areas?: { features: { id: string; geometry: unknown }[] } }) };
}

describe("a loop keeps the closures on every attempt (R8)", () => {
  it("the reseed carries the set; the retrace attempt carries the set FIRST, then its squares", async () => {
    const r = await loopWith(TWO_CLOSURES);
    const third = r.models[2]!.areas!.features;
    expect([r.status, r.models.length, r.models[0]!.areas, r.models[1]!.areas, third.slice(0, 2), third.length > 2])
      .toEqual([200, 3, AREAS, AREAS, AREAS.features, true]);
  });

  it("a full set of 50 leaves the retrace attempt the 50 feed polygons, never 51", async () => {
    const r = await loopWith(FIFTY);
    const full = buildCustomModel(0, FIFTY as ClosureCollection).areas;
    expect([r.status, r.models.map((m) => m.areas)]).toEqual([200, [full, full, full]]);
  });
});

describe("a paid trip's day legs carry the closures (R8)", () => {
  it("every car_scenic request - the search and the five legs - carries the set as areas", async () => {
    const events: string[] = [];
    const { counters } = tripCounters(events);
    const router = tripRouter();
    const deps = {
      upstream: { counters, fetchImpl: router.fetchImpl, now: () => NOW, killed: () => false },
      routerBase: ROUTER,
      resolvePlace: async (id: string) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
      identify: () => ({ userId: "device-1", tier: "paid" as const }),
      closures: async () => fresh(TWO_CLOSURES),
    };
    const response = await handleTrip(tripRequest(TRIP_BODY), {}, deps);
    const scenic = router.sent.filter((s) => s.body.profile === "car_scenic");
    expect([response.status, scenic.length, scenic.map((s) => (s.body.custom_model as { areas?: unknown }).areas)])
      .toEqual([200, 11, Array(11).fill(AREAS)]);
  });
});
