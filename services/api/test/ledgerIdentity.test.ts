/**
 * T-0304 R4 (rv1-t0302 recordable a): the /ledger user is the verified session's sub and nothing else, held by
 * BEHAVIOUR through the shipped worker.fetch - not only by requestReadSites' line whitelist. Every combination of the
 * signed sub (USER_A, USER_B), the extra claims (none, apple, act = the other user's id, both), an x-scenic-device
 * header naming the other user (absent, present) and IDENTITY_HEADERS (unset, "1") runs GET, POST, GET and must
 * answer the T-0302 model for the sub and leave its whole table, over a seed holding the other user's rows and rows
 * keyed by the apple id. Expectations are a function of the sub; a meta-test holds that no combination's
 * expectation is the same for both subs, so a handler keyed by anything but the sub fails a row.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { signSession } from "../src/sessionJwt";
import { fakeQuotaNamespace } from "./doFake";
import { CELL, ledgerTable, model, OTHER, row, SECRET, seed, send, shippedEnv, USER_A, USER_B, type Op } from "./ledgerHarness";

const NOW = new Date("2026-10-05T12:00:00.000Z");
/** A Sign in with Apple user id (appleIdentity APPLE_SUB: [A-Za-z0-9.]{1,64}). */
const APPLE = "001234.0a1b2c3d4e5f60718293a4b5c6d7e8f9.1234";
const SEED = [
  row(USER_A, "101", CELL, "2026-10-05"), row(USER_A, "202", OTHER, "2026-08-01"),
  row(USER_B, "303", OTHER, "2026-10-04"), row(USER_B, "404", CELL, "2026-09-01"),
  row(APPLE, "505", CELL, "2026-10-05"), row(APPLE, "606", OTHER, "2026-07-01"),
];
const OPS: Op[] = [{ method: "GET" }, { method: "POST", body: { place_id: "909", cell: CELL } }, { method: "GET" }];
const SUBS: Record<string, string> = { A: USER_A, B: USER_B };
const other = (sub: string) => (sub === USER_A ? USER_B : USER_A);

type Claims = (sub: string) => { apple?: string; act?: string };
const CLAIMS: [string, Claims][] = [
  ["no extra claim", () => ({})],
  ["an apple claim", () => ({ apple: APPLE })],
  ["an act claim naming the other user", (sub) => ({ act: other(sub) })],
  ["apple and act claims", (sub) => ({ apple: APPLE, act: other(sub) })],
];
type Header = (sub: string) => Record<string, string>;
const HEADERS: [string, Header][] = [
  ["no x-scenic-device", () => ({})],
  ["x-scenic-device naming the other user", (sub) => ({ "x-scenic-device": other(sub) })],
];
const ENVS: [string, Record<string, unknown>][] = [["IDENTITY_HEADERS unset", {}], ["IDENTITY_HEADERS 1", { IDENTITY_HEADERS: "1" }]];

const COMBOS = CLAIMS.flatMap(([c, claims]) => HEADERS.flatMap(([h, header]) => ENVS.map(([e, extra]) =>
  ({ name: `${c}, ${h}, ${e}`, claims, header, extra }))));

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("/ledger's user is the session sub by behaviour (T-0304 R4)", () => {
  it("no combination ignores the sub: every combination's expected answers and table differ between the two subs", () => {
    expect(COMBOS.filter(() => JSON.stringify(model(SEED, USER_A, OPS, NOW)) === JSON.stringify(model(SEED, USER_B, OPS, NOW)))
      .map((x) => x.name)).toEqual([]);
    expect(COMBOS.length).toBe(16);
  });

  it("an apple or act claim and an x-scenic-device header beside a valid Bearer change nothing: GET, POST, GET answer the sub's rows and leave the sub's table, full equality", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [variant, sub] of Object.entries(SUBS)) {
      for (const { name, claims, header, extra } of COMBOS) {
        const quota = fakeQuotaNamespace();
        await seed(SEED);
        const token = (await signSession(SECRET, { sub, ...claims(sub) }, NOW.getTime())).token;
        const headers = { authorization: `Bearer ${token}`, ...header(sub) };
        const answers = [];
        for (const op of OPS) {
          answers.push(await send(op.method, op.method === "POST" ? JSON.stringify(op.body) : null, shippedEnv(quota, extra), headers));
        }
        got.push([variant, name, { answers, table: await ledgerTable() }]);
        want.push([variant, name, model(SEED, sub, OPS, NOW)]);
      }
    }
    expect(got).toEqual(want);
  }, 120_000);
});
