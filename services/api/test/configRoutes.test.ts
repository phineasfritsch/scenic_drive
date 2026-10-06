/**
 * T-0288 R8: ROUTES['/config'] over the cross product CONFIG row x KILL source, whole response by equality. Every row
 * is a function of the KILL variant (its planning_paused is killed OR the KV's own true), and the meta-test asserts no
 * row's expectation ignores the variant - the one named exception is a row whose KV itself pauses.
 */
import { describe, expect, it } from "vitest";
import { ROUTES } from "../src/index";
import { fakeKv } from "./doFake";
import { configKv, expected, getConfig, KILLS } from "./configHarness";
import { KV_PAUSES, ROWS } from "./configRows";

/** Every method a client can send; /config answers each one alike (R7: no request read, no method gate). */
const METHODS = ["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"];

describe("ROUTES['/config'] (T-0288)", () => {
  it("ROUTES has a /config entry", () => {
    expect(Object.keys(ROUTES).filter((k) => k === "/config")).toEqual(["/config"]);
  });

  it("every CONFIG row x every KILL source answers 200 with the whole expected response (KILL never blocks /config)", async () => {
    const got: [string, string, unknown][] = [];
    for (const r of ROWS) for (const [kill, source] of KILLS) got.push([r.name, kill, await getConfig({ ...source, CONFIG: r.config })]);
    expect(got).toEqual(ROWS.flatMap((r) => KILLS.map(([kill, , killed]) => [r.name, kill, expected(r.overrides, killed, r.warnings)])));
  });

  it("no row's expectation ignores the KILL variant, bar the named rows whose KV pauses on its own", () => {
    const ignoring = ROWS.filter((r) => JSON.stringify(expected(r.overrides, false, r.warnings))
      === JSON.stringify(expected(r.overrides, true, r.warnings))).map((r) => r.name);
    expect(ignoring).toEqual(KV_PAUSES);
    expect(KILLS.map(([, , killed]) => killed)).toEqual([false, false, true, true, true]);
  });

  it("a KV planning_paused false cannot unpause an env KILL=1 or a KV KILL_SWITCH KILL=1", async () => {
    const config = configKv('{"planning_paused":false}');
    const paused = [await getConfig({ KILL: "1", CONFIG: config }), await getConfig({ KILL_SWITCH: fakeKv({ KILL: "1" }), CONFIG: config })];
    expect(paused.map((p) => JSON.parse(p.text).planning_paused)).toEqual([true, true]);
  });

  it("every method x every KILL source answers the GET response whole: the handler reads no request", async () => {
    const config = '{"min_app_build":7,"feature_trip":false}';
    const got: [string, string, unknown][] = [];
    for (const method of METHODS) {
      for (const [kill, source] of KILLS) {
        const e = { DB: undefined, GIT_SHA: "test", BUILT_AT: "test", ...source, CONFIG: configKv(config) } as never;
        const body = method === "GET" || method === "HEAD" ? undefined : '{"planning_paused":false,"min_app_build":9}';
        const req = new Request("https://scenic-api.test/config?min_app_build=9&planning_paused=false", { method, body });
        const r = await ROUTES["/config"]!(req, e, new URL(req.url));
        got.push([method, kill, { status: r.status, contentType: r.headers.get("content-type"),
          cacheControl: r.headers.get("cache-control"), text: await r.text() }]);
      }
    }
    expect(got).toEqual(METHODS.flatMap((method) => KILLS.map(([kill, , killed]) =>
      [method, kill, expected({ min_app_build: 7, feature_trip: false }, killed, [])])));
    expect(METHODS).toEqual(["GET", "HEAD", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]);
  });
});
