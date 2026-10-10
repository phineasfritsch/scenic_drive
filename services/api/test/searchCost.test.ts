/**
 * T-0359 R5 (P-COST-01): the kill switch, the daily search allowance and the month's call in front of the ONE Photon
 * request /search makes. Every case drives the SHIPPED ROUTES["/search"] (deps from env) over the QuotaCounter fake,
 * counts real fetch invocations and asserts the counter state WHOLE.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES, type Env } from "../src/index";
import { UPSTREAM_TRIP_AT } from "../src/quota";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { DEVICE, feature, NOW, SEARCH_BODY, searchEnv, searchRequest } from "./searchHarness";

let quota: FakeQuota;
let calls: string[];
let stateAtFirstFetch: unknown;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  calls = [];
  stateAtFirstFetch = undefined;
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    stateAtFirstFetch ??= quota.state();
    calls.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ features: [feature({ name: "Mulholland Drive", state: "California" })] }));
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function send(req: Request, env: Env) {
  const response = await ROUTES["/search"]!(req, env, new URL(req.url));
  return { status: response.status, json: (await response.json()) as unknown };
}


const RESERVED = {
  [`device:${DEVICE}`]: { daily: { day: "2026-10-10", plan: 0, loop: 0, search: 1 } },
  global: { monthly: { month: "2026-10", calls: 1 } },
};

describe("ROUTES['/search'] spend control (T-0359 R5, P-COST-01)", () => {
  it("KILL=1 in env or the KV switch is 503 planning_paused before the body is read (bodyUsed false): zero Photon requests, no reservation", async () => {
    const answered: unknown[] = [];
    for (const source of [{ KILL: "1" }, { KILL_SWITCH: fakeKv({ KILL: "1" }) }, { KILL_SWITCH: fakeKv({}, true) }]) {
      const req = searchRequest(SEARCH_BODY);
      answered.push([await send(req, searchEnv(quota, source)), req.bodyUsed]);
    }
    const paused = [{ status: 503, json: { error: "planning_paused" } }, false];
    expect([answered, calls, quota.state()]).toEqual([[paused, paused, paused], [], {}]);
  });

  it("the search allowance and one monthly call are reserved before the one Photon request", async () => {
    const answer = await send(searchRequest(SEARCH_BODY), searchEnv(quota));
    expect([answer.status, calls.length, stateAtFirstFetch, quota.state()]).toEqual([200, 1, RESERVED, RESERVED]);
  });

  it("an exhausted daily search allowance is 429 with resets_at and zero Photon requests", async () => {
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-10", search: 30 });
    const answer = await send(searchRequest(SEARCH_BODY), searchEnv(quota));
    // The read touched the global instance and wrote nothing to either.
    expect([answer, calls, quota.state()]).toEqual([
      { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-11T00:00:00.000Z" } }, [],
      { [`device:${DEVICE}`]: { daily: { day: "2026-10-10", search: 30 } }, global: {} }]);
  });

  it("29 searches used leaves one: the 30th is answered and reserved", async () => {
    quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-10", search: 29 });
    const answer = await send(searchRequest(SEARCH_BODY), searchEnv(quota));
    expect([answer.status, calls.length, quota.state()[`device:${DEVICE}`]]).toEqual([200, 1, { daily: { day: "2026-10-10", search: 30 } }]);
  });

  it("a tripped monthly counter is 503 planning_paused with zero Photon requests", async () => {
    quota.seed("global", "monthly", { month: "2026-10", calls: UPSTREAM_TRIP_AT });
    const answer = await send(searchRequest(SEARCH_BODY), searchEnv(quota));
    expect([answer, calls, quota.state()]).toEqual([{ status: 503, json: { error: "planning_paused" } }, [],
      { global: { monthly: { month: "2026-10", calls: UPSTREAM_TRIP_AT } }, [`device:${DEVICE}`]: {} }]);
  });

  it("without QUOTA, a routable SEARCH_URL or SEARCH_SECRET the route is 503 search_unavailable with zero requests", async () => {
    const answered: unknown[] = [];
    for (const extra of [{ QUOTA: undefined }, { SEARCH_URL: undefined }, { SEARCH_URL: "http://search.test" },
      { SEARCH_URL: "https://search.invalid" }, { SEARCH_URL: "not a url" }, { SEARCH_SECRET: undefined }, { SEARCH_SECRET: "" }]) {
      answered.push(await send(searchRequest(SEARCH_BODY), searchEnv(quota, extra)));
    }
    const unavailable = { status: 503, json: { error: "search_unavailable" } };
    expect([answered, calls, quota.state()]).toEqual([Array(7).fill(unavailable), [], {}]);
  });

  it("a session that does not verify is 401 session_rejected, reserving nothing and sending nothing", async () => {
    const env = searchEnv(quota, { SESSION_JWT_SECRET: "t0359-session-secret-0123456789abcdef0123" });
    const answer = await send(searchRequest(SEARCH_BODY, { authorization: "Bearer e30.e30.sig" }), env);
    expect([answer, calls, quota.state()]).toEqual([{ status: 401, json: { error: "session_rejected" } }, [], {}]);
  });

  it("anything but POST is 405, reserving nothing and sending nothing", async () => {
    const req = new Request("https://scenic-api.test/search?q=x", { method: "GET", headers: { "x-scenic-device": DEVICE } });
    expect([await send(req, searchEnv(quota)), calls, quota.state()]).toEqual([{ status: 405, json: { error: "POST only" } }, [], {}]);
  });
});
