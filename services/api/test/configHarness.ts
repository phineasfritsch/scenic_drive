/**
 * T-0288: the GET /config harness. The expectation is built HERE, from test literals and quota.ts's exported tables -
 * never from src/config.ts - and compared to the shipped ROUTES['/config'] answer by whole-response equality.
 */
import { ROUTES, type Env } from "../src/index";
import { DAILY_LOOP_QUOTA, DAILY_PLAN_QUOTA, DAILY_SURPRISE_QUOTA, DAILY_TRIP_QUOTA } from "../src/quota";
import { fakeKv } from "./doFake";

/** The compiled defaults, retyped as the oracle (R1). */
export const DEFAULTS = {
  min_app_build: 1,
  planning_paused: false,
  supported_regions: ["la"] as unknown,
  feature_loop: true as unknown,
  feature_trip: true as unknown,
  feature_surprise: true as unknown,
} as Record<string, unknown>;

export const FIELDS = ["min_app_build", "planning_paused", "supported_regions", "feature_loop", "feature_trip", "feature_surprise"];

/** The display quota, read from quota.ts's exported tables tier by tier - an independent path from dailyQuota. */
export const QUOTA = {
  anon: { plan: DAILY_PLAN_QUOTA.anon, loop: DAILY_LOOP_QUOTA.anon, surprise: DAILY_SURPRISE_QUOTA.anon, trip: DAILY_TRIP_QUOTA.anon },
  free: { plan: DAILY_PLAN_QUOTA.free, loop: DAILY_LOOP_QUOTA.free, surprise: DAILY_SURPRISE_QUOTA.free, trip: DAILY_TRIP_QUOTA.free },
  paid: { plan: DAILY_PLAN_QUOTA.paid, loop: DAILY_LOOP_QUOTA.paid, surprise: DAILY_SURPRISE_QUOTA.paid, trip: DAILY_TRIP_QUOTA.paid },
};

export const CACHE_CONTROL = "public, max-age=300";
export const CONTENT_TYPE = "application/json; charset=utf-8";

/** The KILL sources (T-0256 R5) and whether each pauses. */
export const KILLS: [string, Record<string, unknown>, boolean][] = [
  ["no KILL", {}, false],
  ["env KILL=0", { KILL: "0" }, false],
  ["env KILL=1", { KILL: "1" }, true],
  ["KV KILL_SWITCH KILL=1", { KILL_SWITCH: fakeKv({ KILL: "1" }) }, true],
  ["KV KILL_SWITCH throws", { KILL_SWITCH: fakeKv({}, true) }, true],
];

/** The whole expected response: status, the two headers, and the body TEXT (key order included). */
export function expected(overrides: Record<string, unknown>, killed: boolean, warnings: string[]) {
  const fields = { ...DEFAULTS, ...overrides };
  const body = {
    ...fields,
    planning_paused: killed || fields.planning_paused === true,
    quota: QUOTA,
    config_warnings: warnings,
  };
  return { status: 200, contentType: CONTENT_TYPE, cacheControl: CACHE_CONTROL, text: JSON.stringify(body) };
}

/** A CONFIG KV holding `text` at config/v1 (a raw JSON text, so 1e400 and non-JSON can be stored). */
export const configKv = (text: string) => fakeKv({ "config/v1": text });

/** GET /config through the shipped ROUTES entry, with `extra` env bindings. */
export async function getConfig(extra: Record<string, unknown>) {
  const e = { DB: undefined, GIT_SHA: "test", BUILT_AT: "test", ...extra } as unknown as Env;
  const req = new Request("https://scenic-api.test/config", { method: "GET" });
  const response = await ROUTES["/config"]!(req, e, new URL(req.url));
  return {
    status: response.status,
    contentType: response.headers.get("content-type"),
    cacheControl: response.headers.get("cache-control"),
    text: await response.text(),
  };
}
