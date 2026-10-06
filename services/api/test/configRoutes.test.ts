/**
 * T-0288 R8: ROUTES['/config'] over the cross product CONFIG row x KILL source, whole response by equality. Every row
 * is a function of the KILL variant (its planning_paused is killed OR the KV's own true), and the meta-test asserts no
 * row's expectation ignores the variant - the one named exception is a row whose KV itself pauses.
 */
import { describe, expect, it } from "vitest";
import { ROUTES } from "../src/index";
import { fakeKv } from "./doFake";
import { configKv, DEFAULTS, expected, FIELDS, getConfig, KILLS } from "./configHarness";

type Row = { name: string; config: unknown; overrides: Record<string, unknown>; warnings: string[] };
const row = (name: string, config: unknown, overrides: Record<string, unknown>, warnings: string[]): Row =>
  ({ name, config, overrides, warnings });

const MAX = 2147483647;
const ALL_INVALID = '{"min_app_build":0,"planning_paused":"1","supported_regions":[],"feature_loop":"false",'
  + '"feature_trip":0,"feature_surprise":null}';
const LOW = { min_app_build: 1, planning_paused: false, supported_regions: ["la"], feature_loop: false, feature_trip: false, feature_surprise: false };
const HIGH = { min_app_build: MAX, planning_paused: true, supported_regions: ["la"], feature_loop: true, feature_trip: true, feature_surprise: true };

const ROWS: Row[] = [
  row("CONFIG unbound", undefined, {}, []),
  row("config/v1 absent", fakeKv({}), {}, []),
  row("CONFIG throws", fakeKv({}, true), {}, ["record"]),
  row("not JSON", configKv("{"), {}, ["record"]),
  row("JSON null", configKv("null"), {}, ["record"]),
  row("JSON array", configKv('[{"min_app_build":7}]'), {}, ["record"]),
  row("JSON string", configKv('"min_app_build"'), {}, ["record"]),
  row("JSON number", configKv("7"), {}, ["record"]),
  row("empty object", configKv("{}"), {}, []),
  row("defaults restated", configKv(JSON.stringify(DEFAULTS)), {}, []),
  row("every field invalid", configKv(ALL_INVALID), {}, [...FIELDS]),
  row("every field at its low bound, features off", configKv(JSON.stringify(LOW)), LOW, []),
  row("every field at its high bound, KV pauses", configKv(JSON.stringify(HIGH)), HIGH, []),
  row("KV planning_paused false alone", configKv('{"planning_paused":false}'), { planning_paused: false }, []),
  row("unknown keys beside a valid field", configKv('{"quota":{"anon":{"plan":999}},"min_app_build":7,"kill":false}'),
    { min_app_build: 7 }, ["unknown_keys"]),
  row("__proto__ key", configKv('{"__proto__":{"min_app_build":9},"feature_trip":false}'), { feature_trip: false }, ["unknown_keys"]),
  row("one invalid among valid", configKv(`{"min_app_build":${MAX + 1},"feature_loop":false,"supported_regions":["la"]}`),
    { feature_loop: false, supported_regions: ["la"] }, ["min_app_build"]),
];
/** Rows whose KV pauses on its own, so killed and not-killed answer alike - the only rows allowed to ignore KILL. */
const KV_PAUSES = ["every field at its high bound, KV pauses"];

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

  it("any method answers the same body: the handler reads no request", async () => {
    const e = { DB: undefined, GIT_SHA: "test", BUILT_AT: "test" } as never;
    const req = new Request("https://scenic-api.test/config?min_app_build=9", { method: "POST", body: '{"planning_paused":true}' });
    const response = await ROUTES["/config"]!(req, e, new URL(req.url));
    expect(await response.text()).toEqual(expected({}, false, []).text);
  });
});
