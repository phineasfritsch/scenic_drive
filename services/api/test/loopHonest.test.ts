/**
 * T-0335 A2 through handleLoop - the handler ROUTES["/loop"] calls: a dull loop is not shown. The planner re-rolls
 * inside LOOP_UPSTREAM_COST (seed, seed + 1, then seed + 2 when the second was retrace-clean but dull) and answers
 * nothing_pretty only when every attempt it could make was dull or retraced and at least one was retrace-clean.
 * Scores per edge, read by T-0332's oracle over squareLoop: 2 -> 0.020000, 5 -> 0.425000, 6 -> 0.510000, 8 -> 0.713333.
 */
import { describe, expect, it } from "vitest";
import { TEST_VERSION } from "./closuresFake";
import type { ClosureSnapshot } from "../src/closuresStore";
import { appleMapsUrl } from "../src/appleMaps";
import { buildCustomModel } from "../src/customModel";
import { handleLoop } from "../src/loop";
import { fnv1a32, LOOP_LAMBDA } from "../src/loopPlanner";
import { decisionPoints } from "../src/planWaypoints";
import { retraceFraction } from "../src/retrace";
import { decodeRoutePath } from "../src/routePath";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, NOW, outAndBack, squareLoop, START } from "./loopHarness";

const SEED = fnv1a32("device-1|2026-10-05");
const NOW_ISO = NOW.toISOString();
const square = (score: number | null) => loopPath(squareLoop(), 2_700_000, score);
const retraced = () => loopPath(outAndBack(2000), 2_700_000, 8);

/** The whole 200 a shipped attempt answers, recomputed from the body the router sent for it. */
function shipped(text: string, attempts: number, seed: number) {
  const path = decodeRoutePath(text);
  const waypoints = decisionPoints(path);
  return {
    route: { coordinates: path.coordinates, distance_m: 4000 },
    duration_s: 2700,
    retrace_fraction: retraceFraction(path.coordinates.map(([lon, lat]) => ({ lat, lon }))),
    attempts,
    seed,
    target_distance_m: 30000,
    minutes: 45,
    eta_is_estimate: true,
    waypoints,
    apple_maps_url: appleMapsUrl(START, START, waypoints),
  };
}

async function run(answers: string[]) {
  const h = loopHarness(answers);
  const response = await handleLoop(loopRequest(LOOP_BODY), {}, h.deps);
  return { status: response.status, json: await response.json(), seeds: h.sent.map((s) => s.body["round_trip.seed"]),
    models: h.sent.map((s) => s.body.custom_model) };
}

const NOTHING_PRETTY = { error: "nothing_pretty", minutes: 45 };
const FEED_MODEL = JSON.parse(JSON.stringify(buildCustomModel(LOOP_LAMBDA, null)));

describe("POST /loop honest failure (T-0335 A2, P-SAFE-04)", () => {
  it("a dull first loop re-rolls: seed + 1 clean and pretty answers the whole 200, attempts 2", async () => {
    const answers = [square(2), square(8)];
    expect(await run(answers)).toEqual({ status: 200, json: shipped(answers[1]!, 2, (SEED + 1) >>> 0),
      seeds: [SEED, (SEED + 1) >>> 0], models: [FEED_MODEL, FEED_MODEL] });
  });

  it("dull at seed and seed + 1 re-rolls seed + 2 over the feed (no retrace areas), attempts 3", async () => {
    const answers = [square(2), square(2), square(8)];
    expect(await run(answers)).toEqual({ status: 200, json: shipped(answers[2]!, 3, (SEED + 2) >>> 0),
      seeds: [SEED, (SEED + 1) >>> 0, (SEED + 2) >>> 0], models: [FEED_MODEL, FEED_MODEL, FEED_MODEL] });
  });

  it("three dull loops answer nothing_pretty after exactly LOOP_UPSTREAM_COST requests, never a 200 loop", async () => {
    expect(await run([square(2), square(2), square(2), square(8)])).toEqual({ status: 422, json: NOTHING_PRETTY,
      seeds: [SEED, (SEED + 1) >>> 0, (SEED + 2) >>> 0], models: [FEED_MODEL, FEED_MODEL, FEED_MODEL] });
  });

  it("unscored loops are dull (T-0332 R3, fail closed); every edge 5 (0.425) is dull; every edge 6 (0.51) ships", async () => {
    const refused = { status: 422, json: NOTHING_PRETTY, seeds: [SEED, (SEED + 1) >>> 0, (SEED + 2) >>> 0],
      models: [FEED_MODEL, FEED_MODEL, FEED_MODEL] };
    expect(await run([square(null), square(null), square(null)])).toEqual(refused);
    expect(await run([square(5), square(5), square(5)])).toEqual(refused);
    const pretty = [square(6)];
    expect(await run(pretty)).toEqual({ status: 200, json: shipped(pretty[0]!, 1, SEED), seeds: [SEED], models: [FEED_MODEL] });
  });

  it("retraced, then clean but dull, then retraced again answers nothing_pretty: a clean loop was found and it was dull", async () => {
    expect(await run([retraced(), square(2), retraced()])).toEqual({ status: 422, json: NOTHING_PRETTY,
      seeds: [SEED, (SEED + 1) >>> 0, (SEED + 2) >>> 0], models: [FEED_MODEL, FEED_MODEL, FEED_MODEL] });
  });
});

/** rv1 B2 by class: every step of the seed ladder stays a uint32 at the wrap. The userIds are FNV-1a preimages
 *  (.artifacts/t0335/preimage.mjs); the expected seeds are (S + i) modulo 2^32, not the source's `>>> 0`. */
const WRAP_USERS = [{ seed: 0xfffffffe, user: "agO3ON" }, { seed: 0xffffffff, user: "v551St" }];
const WRAP_ANSWERS = [[2, 8], [2, 2, 8], [2, 2, 2]];
const WRAP_ROWS = WRAP_USERS.flatMap((u) => WRAP_ANSWERS.map((scores) => ({ ...u, scores })));

async function runAs(user: string, answers: string[]) {
  const h = loopHarness(answers);
  const deps = { ...h.deps, identify: async (req: Request) => ({ ...(await h.deps.identify(req)), userId: user }) };
  const response = await handleLoop(loopRequest(LOOP_BODY), {}, deps);
  return { status: response.status, json: await response.json(), seeds: h.sent.map((s) => s.body["round_trip.seed"]) };
}

describe("POST /loop seed ladder at the uint32 wrap (T-0335 rv1 B2, P-SAFE-04)", () => {
  it.each(WRAP_ROWS)("seed $seed, scores $scores: the whole answer and every router seed stay uint32", async ({ seed, user, scores }) => {
    expect(fnv1a32(`${user}|2026-10-05`)).toBe(seed);
    const answers = scores.map((s) => square(s));
    const seeds = scores.map((_, i) => (seed + i) % 2 ** 32);
    const last = scores.length - 1;
    const json = scores[last] === 8 ? shipped(answers[last]!, scores.length, seeds[last]!) : NOTHING_PRETTY;
    expect(await runAs(user, answers)).toEqual({ status: scores[last] === 8 ? 200 : 422, json, seeds });
  });

  it("meta: the rows reach both wraps - seed + 1 at 0xFFFFFFFF and seed + 2 at both", () => {
    const wrapped = WRAP_ROWS.flatMap((r) => r.scores.map((_, i) => r.seed + i)).filter((s) => s >= 2 ** 32);
    expect(wrapped).toEqual([2 ** 32, 2 ** 32, 2 ** 32, 2 ** 32, 2 ** 32 + 1, 2 ** 32, 2 ** 32 + 1]);
  });
});

/** The closure re-request: X sits on squareLoop's east-going side, stored but not sent (50 tiny squares due south of
 *  the start are nearer the start -> start corridor), so the pretty first loop crosses it and buys ONE re-request at
 *  the same seed (2 <= 3), answered with the square mirrored west - clear of X - scored `again`. */
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
function box(name: string, lon: number, lat: number, half: number): Feature {
  const ring = [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half], [lon - half, lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
const SQUARE = squareLoop();
const X = box("x", SQUARE[30]![1], SQUARE[30]![0], 0.0005);
const SOUTH = Array.from({ length: 50 }, (_, i) => box(`s-${i + 1}`, START.lon, START.lat - 0.001 - i * 0.0001, 0.00004));
const SNAPSHOT: ClosureSnapshot = { version: TEST_VERSION, closures: { type: "FeatureCollection", features: [...SOUTH, X] },
  hazard: null, fetchedAt: NOW_ISO };
const WEST = SQUARE.map(([lat, lon]) => [lat, 2 * START.lon - lon] as [number, number]);

async function crossing(again: number) {
  const answers = [loopPath(SQUARE, 2_700_000, 8), loopPath(WEST, 2_700_000, again)];
  const h = loopHarness(answers);
  const response = await handleLoop(loopRequest(LOOP_BODY), {}, { ...h.deps, closures: async () => SNAPSHOT });
  const carriesX = h.sent.map((s) => JSON.stringify((s.body.custom_model as { areas?: unknown }).areas ?? null)
    .includes(JSON.stringify(X.geometry.coordinates)));
  return { answers, got: { status: response.status, json: await response.json(), seeds: h.sent.map((s) => s.body["round_trip.seed"]), carriesX } };
}

describe("POST /loop honest failure holds the closure re-request too (T-0335 R3)", () => {
  it("a pretty loop crossing a closure, re-requested to a dull clean loop, keeps the pretty loop and names the crossing", async () => {
    const { answers, got } = await crossing(2);
    expect(got).toEqual({ status: 200, seeds: [SEED, SEED], carriesX: [false, true], json: { ...shipped(answers[0]!, 2, SEED),
      closures_hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW_ISO, dropped: 1, crosses: ["x"] } } });
  });

  it("a pretty loop crossing a closure, re-requested to a pretty clean loop, ships the re-request", async () => {
    const { answers, got } = await crossing(8);
    expect(got).toEqual({ status: 200, seeds: [SEED, SEED], carriesX: [false, true], json: { ...shipped(answers[1]!, 2, SEED),
      closures_hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW_ISO, dropped: 1 } } });
  });
});
