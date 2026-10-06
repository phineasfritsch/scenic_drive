/**
 * T-0276 R6 through the shipped scheduled() entry point: the recorded feed becomes the oracle's record in KV, once;
 * every way the feed can fail writes NOTHING, so the last good record stays and ages into stale; the cron trigger is
 * the wrangler.jsonc one and CLOSURES is not bound there (the owner's step).
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import feedRaw from "../../../Tests/Fixtures/t0276/lcsStatusD07.json?raw";
import expectedRaw from "../../../Tests/Fixtures/t0276/expected.json?raw";
import wranglerRaw from "../wrangler.jsonc?raw";
import worker, { type Env } from "../src/index";
import { CLOSURES_CRON } from "../src/closuresCron";
import { CLOSURES_KEY } from "../src/closuresStore";
import { LCS_D7_FEED } from "../src/lcsFeed";
import { closuresKv } from "./closuresFake";

const EXPECTED = JSON.parse(expectedRaw) as { cap: { geojson: unknown }; version: string };
const NOW = new Date("2026-10-06T08:06:12Z");
const LAST_MODIFIED = "Tue, 06 Oct 2026 08:04:20 GMT";
const RECORD = {
  version: EXPECTED.version, fetched_at: "2026-10-06T08:04:20.000Z", geojson: EXPECTED.cap.geojson,
  stats: { rows: 2808, full: 1708, active: 163, refused: 0, kept: 42, dropped: 121 },
};

let fetched: string[];
let answer: () => Promise<Response>;

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  fetched = [];
  answer = async () => new Response(feedRaw, { headers: { "last-modified": LAST_MODIFIED } });
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    fetched.push(String(input instanceof Request ? input.url : input));
    return answer();
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function tick(closures: KVNamespace | undefined) {
  const waits: Promise<unknown>[] = [];
  const ctx = { waitUntil: (p: Promise<unknown>) => waits.push(p), passThroughOnException: () => {} } as unknown as ExecutionContext;
  const env = { GIT_SHA: "test", BUILT_AT: "test", ...(closures ? { CLOSURES: closures } : {}) } as unknown as Env;
  await worker.scheduled!({ cron: CLOSURES_CRON, scheduledTime: NOW.getTime(), noRetry: () => {} } as ScheduledController, env, ctx);
  await Promise.all(waits);
}

const row = (index: string, lon: string) => ({ lcs: { index, location: { begin: { beginLongitude: lon, beginLatitude: "34.0" },
  end: { endLongitude: lon, endLatitude: "34.0" } }, closure: { typeOfClosure: "Full", facility: "On Ramp",
  closureTimestamp: { closureStartEpoch: "1", closureEndEpoch: "9999999999", isClosureEndIndefinite: "false" },
  code1097: { isCode1097: "false" }, code1098: { isCode1098: "false" }, code1022: { isCode1022: "false" } } } });
const feedOf = (data: unknown) => async () => new Response(JSON.stringify({ data }), { headers: { "last-modified": LAST_MODIFIED } });

describe("the closures cron through scheduled() (R6)", () => {
  it("writes the oracle's record under closures/lcs-d7, once, from one fetch of the D7 feed", async () => {
    const k = closuresKv({});
    await tick(k.kv);
    expect([fetched, k.puts.map(([key, value]) => [key, JSON.parse(value)])]).toEqual([[LCS_D7_FEED], [[CLOSURES_KEY, RECORD]]]);
  });

  it("fetched_at is the feed's Last-Modified, or now when that is in the future", async () => {
    const k = closuresKv({});
    answer = async () => new Response(JSON.stringify({ data: [row("a", "-118.4")] }), { headers: { "last-modified": "Tue, 06 Oct 2026 08:06:13 GMT" } });
    await tick(k.kv);
    expect(k.puts.map(([, value]) => JSON.parse(value).fetched_at)).toEqual(["2026-10-06T08:06:12.000Z"]);
  });

  it("without the CLOSURES binding the cron does nothing: zero fetches", async () => {
    await tick(undefined);
    expect(fetched).toEqual([]);
  });

  const nothing: [string, () => Promise<Response>][] = [
    ["a 503", async () => new Response(feedRaw, { status: 503, headers: { "last-modified": LAST_MODIFIED } })],
    ["a 204", async () => new Response(null, { status: 204, headers: { "last-modified": LAST_MODIFIED } })],
    ["no Last-Modified", async () => new Response(feedRaw)],
    ["an unparseable Last-Modified", async () => new Response(feedRaw, { headers: { "last-modified": "yesterday-ish" } })],
    ["a body that is not JSON", async () => new Response("<html>", { headers: { "last-modified": LAST_MODIFIED } })],
    ["no data", async () => new Response("{}", { headers: { "last-modified": LAST_MODIFIED } })],
    ["data an object", feedOf({})],
    ["data empty", feedOf([])],
    ["2 of 3 Full rows refused", feedOf([row("a", "-118.4"), row("b", "0"), row("c", "0")])],
    ["every row without a type", feedOf([{ lcs: { index: "a" } }])],
    ["a fetch that throws", async () => { throw new Error("network down"); }],
  ];
  for (const [name, respond] of nothing) {
    it(`${name} writes nothing: the last good record stays`, async () => {
      const k = closuresKv({});
      answer = respond;
      await tick(k.kv);
      expect([fetched, k.puts]).toEqual([[LCS_D7_FEED], []]);
    });
  }

  it("exactly half the Full rows refused still writes (the bound), with the refusal counted", async () => {
    const k = closuresKv({});
    answer = feedOf([row("a", "-118.4"), row("b", "0")]);
    await tick(k.kv);
    expect(k.puts.map(([, value]) => JSON.parse(value).stats)).toEqual([{ rows: 2, full: 2, active: 1, refused: 1, kept: 1, dropped: 0 }]);
  });
});

describe("the trigger (R6)", () => {
  it("wrangler.jsonc runs the cron every 15 minutes and binds no CLOSURES namespace", () => {
    const config = JSON.parse(wranglerRaw.split("\n").filter((line) => !line.trim().startsWith("//")).join("\n"));
    expect([CLOSURES_CRON, config.triggers, config.kv_namespaces]).toEqual(["*/15 * * * *", { crons: ["*/15 * * * *"] }, undefined]);
  });
});
