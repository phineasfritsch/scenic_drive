/**
 * T-0302 R1-R7: GET and POST /ledger through the shipped worker.fetch. Every row of the access table runs once per
 * caller variant (USER_A, USER_B) over one seed holding both users' rows inside and outside the window; its expected
 * answers and whole table are the model's, a function of the caller, and a meta-test holds that no row's expectation
 * is the same for both callers - so a handler that ignores the caller fails a row. Refusals leave the table whole.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fakeKv, fakeQuotaNamespace, type FakeQuota } from "./doFake";
import {
  apply, bearer, CELL, ledgerTable, MAX_PLACE, model, OTHER, row, seed, send, shippedEnv, sortRows, USER_A, USER_B, type Op,
} from "./ledgerHarness";

const NOW = new Date("2026-10-05T12:00:00.000Z");
const SEED = [
  row(USER_A, "101", CELL, "2026-10-05"), row(USER_A, "202", OTHER, "2026-07-07"), row(USER_A, "303", CELL, "2026-07-06"),
  row(USER_A, "404", OTHER, "2026-09-01"),
  row(USER_B, "404", CELL, "2026-10-04"), row(USER_B, "101", OTHER, "2026-07-07"), row(USER_B, "505", CELL, "2026-07-06"),
];
const CALLERS: Record<string, string> = { A: USER_A, B: USER_B };
const GET: Op = { method: "GET" };
const POST = (place_id: string, cell: string): Op => ({ method: "POST", body: { place_id, cell } });

const ROWS: [string, Op[]][] = [
  ["GET reads the caller's rows inside the window, newest day first", [GET]],
  ["POST a new place records it today, purges every user's rows before the window, and GET reads it back", [POST("909", CELL), GET]],
  ["POST the same place twice in one day keeps one row and its first cell", [POST("909", CELL), POST("909", OTHER), GET]],
  ["POST a place the caller may already hold today", [POST("101", OTHER), GET]],
  ["POST a place the other user holds records the caller's own row", [POST("404", OTHER), GET]],
  ["POST the corpus id bounds 1 and 9223372036854775807", [POST("1", CELL), POST(MAX_PLACE, OTHER), GET]],
];

const BODY = "the body must be exactly {place_id, cell}";
const PLACE = "place_id is not a corpus place id";
const H3 = "cell is not an H3 resolution-5 cell";
const REFUSALS: [string, string, string][] = [
  ["not JSON", "place_id=101", "the body is not JSON"],
  ["empty body", "", "the body is not JSON"],
  ["null", "null", "the body must be a JSON object"],
  ["an array", JSON.stringify(["101", CELL]), "the body must be a JSON object"],
  ["a bare string", JSON.stringify(CELL), "the body must be a JSON object"],
  ["no key", "{}", BODY],
  ["no cell", JSON.stringify({ place_id: "101" }), BODY],
  ["no place_id", JSON.stringify({ cell: CELL }), BODY],
  ["a third key", JSON.stringify({ place_id: "101", cell: CELL, lat: 34.02 }), BODY],
  ["a timestamp beside", JSON.stringify({ place_id: "101", cell: CELL, at: "2026-10-05T12:00:00Z" }), BODY],
  ["the key cased", JSON.stringify({ Place_id: "101", cell: CELL }), BODY],
  ["a __proto__ key", `{"__proto__":{"place_id":"101"},"cell":"${CELL}"}`, BODY],
  ["a number place_id", JSON.stringify({ place_id: 101, cell: CELL }), PLACE],
  ["a null place_id", JSON.stringify({ place_id: null, cell: CELL }), PLACE],
  ["an empty place_id", JSON.stringify({ place_id: "", cell: CELL }), PLACE],
  ["place_id 0", JSON.stringify({ place_id: "0", cell: CELL }), PLACE],
  ["a leading zero", JSON.stringify({ place_id: "0101", cell: CELL }), PLACE],
  ["a signed place_id", JSON.stringify({ place_id: "-101", cell: CELL }), PLACE],
  ["a plus sign", JSON.stringify({ place_id: "+101", cell: CELL }), PLACE],
  ["a space-padded place_id", JSON.stringify({ place_id: " 101", cell: CELL }), PLACE],
  ["a newline-suffixed place_id", JSON.stringify({ place_id: "101\n", cell: CELL }), PLACE],
  ["a decimal place_id", JSON.stringify({ place_id: "101.0", cell: CELL }), PLACE],
  ["an exponent place_id", JSON.stringify({ place_id: "1e3", cell: CELL }), PLACE],
  ["2^63, one past the largest id", JSON.stringify({ place_id: "9223372036854775808", cell: CELL }), PLACE],
  ["nineteen nines", JSON.stringify({ place_id: "9999999999999999999", cell: CELL }), PLACE],
  ["twenty digits", JSON.stringify({ place_id: "10000000000000000000", cell: CELL }), PLACE],
  ["a coordinate as the place id", JSON.stringify({ place_id: "34.0212_-118.4912", cell: CELL }), PLACE],
  ["a number cell", JSON.stringify({ place_id: "101", cell: 5 }), H3],
  ["an uppercase cell", JSON.stringify({ place_id: "101", cell: CELL.toUpperCase() }), H3],
  ["a resolution-6 cell", JSON.stringify({ place_id: "101", cell: "86283472fffffff" }), H3],
  ["a resolution-4 cell", JSON.stringify({ place_id: "101", cell: "8428347ffffffff" }), H3],
  ["a coordinate as the cell", JSON.stringify({ place_id: "101", cell: "34.02,-118.49" }), H3],
];

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input));
    return new Response("{}", { status: 500 });
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("GET and POST /ledger hold exactly the caller's Surprise places for 90 days (T-0302 R1-R5)", () => {
  it("no row ignores the caller: every row's expected answers or table differ between the two callers", () => {
    expect(ROWS.filter(([, ops]) => JSON.stringify(model(SEED, USER_A, ops, NOW)) === JSON.stringify(model(SEED, USER_B, ops, NOW)))
      .map(([name]) => name)).toEqual([]);
  });

  it("every row through worker.fetch answers the model's answers and leaves the model's whole table, for each caller", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [variant, user] of Object.entries(CALLERS)) {
      for (const [name, ops] of ROWS) {
        await seed(SEED);
        const answers = [];
        for (const op of ops) answers.push(await apply(op, user, shippedEnv(quota)));
        got.push([variant, name, { answers, table: await ledgerTable() }]);
        want.push([variant, name, model(SEED, user, ops, NOW)]);
      }
    }
    expect(got).toEqual(want);
    expect({ routerRequests, quota: quota.state() }).toEqual({ routerRequests: [], quota: {} });
  }, 60_000);

  it("every other POST body is 400 invalid_request with its detail and the table unchanged, for each caller", async () => {
    const got: unknown[] = [];
    for (const [variant, user] of Object.entries(CALLERS)) {
      for (const [label, body] of REFUSALS) {
        await seed(SEED);
        got.push([variant, label, await send("POST", body, shippedEnv(quota), await bearer(user)), await ledgerTable()]);
      }
    }
    expect(got).toEqual(Object.keys(CALLERS).flatMap((variant) => REFUSALS.map(([label, , detail]) =>
      [variant, label, { status: 400, json: { error: "invalid_request", detail } }, sortRows(SEED)])));
  }, 60_000);

  it("no verified session is 401 and no usable secret is 503, for GET and POST, with the table unchanged", async () => {
    const valid = JSON.stringify({ place_id: "909", cell: CELL });
    const cases: [string, Record<string, unknown>, () => Promise<Record<string, string>>, unknown][] = [
      ["SESSION_JWT_SECRET unbound", { SESSION_JWT_SECRET: undefined }, () => bearer(USER_A), { status: 503, json: { error: "auth_unavailable" } }],
      ["SESSION_JWT_SECRET 31 chars", { SESSION_JWT_SECRET: "x".repeat(31) }, () => bearer(USER_A, "x".repeat(31)), { status: 503, json: { error: "auth_unavailable" } }],
      ["no Bearer", {}, async () => ({}), { status: 401, json: { error: "unauthorized" } }],
      ["a bare x-scenic-device header under IDENTITY_HEADERS 1", { IDENTITY_HEADERS: "1" }, async () => ({ "x-scenic-device": USER_A }), { status: 401, json: { error: "unauthorized" } }],
      ["a Bearer signed with another secret", {}, () => bearer(USER_A, "t0302-another-secret-0123456789abcdefgh"), { status: 401, json: { error: "unauthorized" } }],
      ["an expired session", {}, () => bearer(USER_A, undefined, NOW.getTime() - 3_601_000), { status: 401, json: { error: "unauthorized" } }],
      ["a malformed Bearer", {}, async () => ({ authorization: "Bearer not a token" }), { status: 401, json: { error: "unauthorized" } }],
    ];
    const got: unknown[] = [];
    for (const [label, extra, headers, answer] of cases) {
      for (const method of ["GET", "POST"]) {
        await seed(SEED);
        got.push([label, method, await send(method, method === "POST" ? valid : null, shippedEnv(quota, extra), await headers()), await ledgerTable(), answer]);
      }
    }
    expect(got).toEqual(got.map((g) => { const [label, method, , , answer] = g as unknown[]; return [label, method, answer, sortRows(SEED), answer]; }));
  }, 60_000);

  it("a method other than GET or POST is 405 and the table unchanged; D1 unbound is 503 ledger_unavailable", async () => {
    const got: unknown[] = [];
    for (const method of ["PUT", "DELETE", "PATCH"]) {
      await seed(SEED);
      got.push([method, await send(method, JSON.stringify({ place_id: "909", cell: CELL }), shippedEnv(quota), await bearer(USER_A)), await ledgerTable()]);
    }
    const unbound = shippedEnv(quota, { DB: undefined });
    got.push(["no D1 POST", await send("POST", JSON.stringify({ place_id: "909", cell: CELL }), unbound, await bearer(USER_A))]);
    got.push(["no D1 GET", await send("GET", null, unbound, await bearer(USER_A))]);
    const refused = { status: 405, json: { error: "GET or POST only" } };
    const down = { status: 503, json: { error: "ledger_unavailable" } };
    expect(got).toEqual([["PUT", refused, sortRows(SEED)], ["DELETE", refused, sortRows(SEED)], ["PATCH", refused, sortRows(SEED)],
      ["no D1 POST", down], ["no D1 GET", down]]);
  });

  it("KILL=1 and the KV KILL_SWITCH do not pause /ledger: D1 only, zero router requests, no quota reservation (R7)", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const extra of [{ KILL: "1" }, { KILL_SWITCH: fakeKv({ KILL: "1" }) }]) {
      await seed(SEED);
      const ops = [POST("909", CELL), GET];
      const answers = [];
      for (const op of ops) answers.push(await apply(op, USER_A, shippedEnv(quota, extra)));
      got.push({ answers, table: await ledgerTable() });
      want.push(model(SEED, USER_A, ops, NOW));
    }
    expect({ got, routerRequests, quota: quota.state() }).toEqual({ got: want, routerRequests: [], quota: {} });
  });
});
