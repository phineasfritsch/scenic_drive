/**
 * T-0293 R8, R9 (P-PRIV-06): POST /waitlist {cell} counts interest per H3 resolution-5 cell and stores nothing else.
 * Every row runs through the shipped worker.fetch over two table variants - empty, and already holding both cells -
 * and is a function of the variant: the table after a refusal equals the variant's own pre-state, compared whole.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import waitlistSql from "../migrations/0006_waitlist.sql?raw";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";

// Published uber/h3 resolution-5 cells (the telemetry fixtures' and the h3 docs' own).
const CELL = "85283473fffffff";
const OTHER = "850dab63fffffff";
const NOW = new Date("2026-10-05T12:00:00Z");
type Row = Record<string, unknown>;
const VARIANTS: Record<string, Row[]> = {
  empty: [],
  holding: [{ cell: CELL, count: 3, updated_at: "2026-10-01" }, { cell: OTHER, count: 1, updated_at: "2026-09-30" }],
};

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input));
    return new Response("{}", { status: 500 });
  });
  for (const statement of waitlistSql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  await env.DB.prepare("DELETE FROM waitlist").run();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

async function seed(rows: Row[]): Promise<void> {
  await env.DB.prepare("DELETE FROM waitlist").run();
  for (const r of rows) {
    await env.DB.prepare("INSERT INTO waitlist (cell, count, updated_at) VALUES (?1, ?2, ?3)").bind(r.cell, r.count, r.updated_at).run();
  }
}

async function table(): Promise<Row[]> {
  return (await env.DB.prepare("SELECT * FROM waitlist ORDER BY cell").all()).results as Row[];
}

const shippedEnv = (extra: Record<string, unknown> = {}) =>
  ({ DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ...extra }) as unknown as Env;

async function send(body: string | null, method = "POST", e: Env = shippedEnv()) {
  const req = new Request("https://scenic-api.test/waitlist", {
    method, headers: { "content-type": "application/json" }, body: method === "GET" ? undefined : body,
  });
  const response = await worker.fetch(req, e);
  return { status: response.status, json: (await response.json()) as unknown };
}

const REFUSALS: [string, string, string][] = [
  ["not JSON", "cell=85283473fffffff", "the body is not JSON"],
  ["empty body", "", "the body is not JSON"],
  ["null", "null", "the body must be a JSON object"],
  ["an array", JSON.stringify([CELL]), "the body must be a JSON object"],
  ["a bare string", JSON.stringify(CELL), "the body must be a JSON object"],
  ["a number", "5", "the body must be a JSON object"],
  ["no key", "{}", "the body must be exactly {cell}"],
  ["a second key", JSON.stringify({ cell: CELL, lat: 34.02 }), "the body must be exactly {cell}"],
  ["a second cell", JSON.stringify({ cell: CELL, cells: [OTHER] }), "the body must be exactly {cell}"],
  ["the key cased", JSON.stringify({ Cell: CELL }), "the body must be exactly {cell}"],
  ["the key padded", JSON.stringify({ " cell": CELL }), "the body must be exactly {cell}"],
  ["a __proto__ key", `{"__proto__":{"cell":"${CELL}"}}`, "the body must be exactly {cell}"],
  ["a number cell", JSON.stringify({ cell: 5 }), "cell is not an H3 resolution-5 cell"],
  ["a null cell", JSON.stringify({ cell: null }), "cell is not an H3 resolution-5 cell"],
  ["a list cell", JSON.stringify({ cell: [CELL] }), "cell is not an H3 resolution-5 cell"],
  ["an object cell", JSON.stringify({ cell: { lat: 34.02, lon: -118.49 } }), "cell is not an H3 resolution-5 cell"],
  ["an empty cell", JSON.stringify({ cell: "" }), "cell is not an H3 resolution-5 cell"],
  ["an uppercase cell", JSON.stringify({ cell: CELL.toUpperCase() }), "cell is not an H3 resolution-5 cell"],
  ["a space-padded cell", JSON.stringify({ cell: ` ${CELL}` }), "cell is not an H3 resolution-5 cell"],
  ["a newline-suffixed cell", JSON.stringify({ cell: `${CELL}\n` }), "cell is not an H3 resolution-5 cell"],
  ["a resolution-6 cell", JSON.stringify({ cell: "86283472fffffff" }), "cell is not an H3 resolution-5 cell"],
  ["a resolution-4 cell", JSON.stringify({ cell: "8428347ffffffff" }), "cell is not an H3 resolution-5 cell"],
  ["a coordinate as the cell", JSON.stringify({ cell: "34.02,-118.49" }), "cell is not an H3 resolution-5 cell"],
];

describe("POST /waitlist counts a coarse cell and nothing else (T-0293 R8, P-PRIV-06)", () => {
  it("the two variants differ, so no row can pass by ignoring the table it runs over", () => {
    expect(VARIANTS.empty).not.toEqual(VARIANTS.holding);
  });

  it("a valid cell is 200 waitlisted and adds one to that cell's row, dated by the UTC day only, over both variants", async () => {
    const answered: unknown[] = [];
    for (const [name, rows] of Object.entries(VARIANTS)) {
      await seed(rows);
      const first = await send(JSON.stringify({ cell: CELL }));
      const second = await send(JSON.stringify({ cell: CELL }));
      answered.push([name, first, second, await table()]);
    }
    const ok = { status: 200, json: { waitlisted: true } };
    expect(answered).toEqual([
      ["empty", ok, ok, [{ cell: CELL, count: 2, updated_at: "2026-10-05" }]],
      ["holding", ok, ok, [{ cell: OTHER, count: 1, updated_at: "2026-09-30" }, { cell: CELL, count: 5, updated_at: "2026-10-05" }]],
    ]);
    expect(routerRequests).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("every other body is 400 invalid_request with its detail, and the table is the variant's own, over both variants", async () => {
    const answered: unknown[] = [];
    for (const [name, rows] of Object.entries(VARIANTS)) {
      await seed(rows);
      for (const [label, body] of REFUSALS) answered.push([name, label, await send(body), await table()]);
    }
    const sorted = (rows: Row[]) => [...rows].sort((a, b) => String(a.cell).localeCompare(String(b.cell)));
    expect(answered).toEqual(Object.entries(VARIANTS).flatMap(([name, rows]) => REFUSALS.map(([label, , detail]) =>
      [name, label, { status: 400, json: { error: "invalid_request", detail } }, sorted(rows)])));
    expect(routerRequests).toEqual([]);
    expect(quota.state()).toEqual({});
  });

  it("a method other than POST is 405 and writes nothing", async () => {
    const answered: unknown[] = [];
    for (const [name, rows] of Object.entries(VARIANTS)) {
      await seed(rows);
      answered.push([name, await send(null, "GET"), await send(JSON.stringify({ cell: CELL }), "PUT"), (await table()).length]);
    }
    const no = { status: 405, json: { error: "POST only" } };
    expect(answered).toEqual([["empty", no, no, 0], ["holding", no, no, 2]]);
  });

  it("no D1 binding, or a D1 whose write throws, is 503 waitlist_unavailable", async () => {
    const throwing = { prepare: () => ({ bind: () => ({ run: async () => { throw new Error("d1 down"); } }) }) };
    const answered = [await send(JSON.stringify({ cell: CELL }), "POST", shippedEnv({ DB: undefined })),
      await send(JSON.stringify({ cell: CELL }), "POST", shippedEnv({ DB: throwing }))];
    const unavailable = { status: 503, json: { error: "waitlist_unavailable" } };
    expect(answered).toEqual([unavailable, unavailable]);
  });

  it("is kill-switch-exempt and quota-exempt by ruling: KILL=1 and a KV KILL still count the cell, with no quota touch", async () => {
    const answered: unknown[] = [];
    for (const kill of [{ KILL: "1" }, { KILL_SWITCH: fakeKv({ KILL: "1" }) }]) {
      answered.push(await send(JSON.stringify({ cell: OTHER }), "POST", shippedEnv(kill)));
    }
    expect({ answered, table: await table(), quota: quota.state(), routerRequests }).toEqual({
      answered: [{ status: 200, json: { waitlisted: true } }, { status: 200, json: { waitlisted: true } }],
      table: [{ cell: OTHER, count: 2, updated_at: "2026-10-05" }], quota: {}, routerRequests: [],
    });
  });
});
