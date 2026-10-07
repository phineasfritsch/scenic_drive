/**
 * T-0304 R1-R3: POST /ledger admits at most 200 rows per user per UTC day (LEDGER_DAILY_CAP, the paid Surprise
 * allowance by reference; the literal here is the ruled number, so a moved reference fails). Every row runs once per
 * writer variant (USER_A writes, USER_B writes) x stale-owner variant (the row outside the window is the writer's own,
 * or the other user's) over a seed built from both; the expected answer and the whole table after are literal
 * functions of both, and meta-tests hold that no row's expectation is the same for both writers or for both stale
 * owners. A refused write is 429 ledger_daily_cap and writes nothing - no insert and no purge: the stale row survives
 * it whoever owns it (rv1-t0304 B1). Bounds: cap-2, cap-1 and cap rows held, and across the UTC midnight. Ruling
 * rv1-t0304 S1: the answer turns on D1's admission row alone - only `admitted` exactly 1 is 200; no row, no
 * `admitted`, or any other value is 429 ledger_daily_cap (fail closed), each batch result shape a row of its own.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fakeQuotaNamespace } from "./doFake";
import { apply, CELL, ledgerTable, OTHER, row, seed, shippedEnv, sortRows, USER_A, USER_B, type LedgerRow } from "./ledgerHarness";

const CAP = 200;
const NOON = "2026-10-05T12:00:00.000Z";
const TODAY = "2026-10-05";
const YESTERDAY = "2026-10-04";
const PLACE = "909";
const WRITERS: Record<string, string> = { A: USER_A, B: USER_B };
const other = (writer: string) => (writer === USER_A ? USER_B : USER_A);
/** `n` rows of `user` dated `day`, place ids 1000 ... 1000 + n - 1. */
const fill = (user: string, n: number, day: string) => Array.from({ length: n }, (_, i) => row(user, String(1000 + i), CELL, day));
const STALE_OWNERS = ["writer", "other"] as const;
type StaleOwner = (typeof STALE_OWNERS)[number];
/** A row of `owner` outside the 90-day window at every instant below: a successful write purges it, a refusal does not. */
const staleRow = (writer: string, owner: StaleOwner) => row(owner === "writer" ? writer : other(writer), "77", OTHER, "2026-07-01");

const RECORDED = { status: 200, json: { recorded: true } };
const REFUSED = { status: 429, json: { error: "ledger_daily_cap" } };
interface Case { now: string; pre: LedgerRow[]; place: string; answer: unknown; post: LedgerRow[] }
const written = (writer: string, day: string) => row(writer, PLACE, CELL, day);
const purged = (pre: LedgerRow[]) => pre.filter((r) => r.place_id !== "77");

/** [name, the case as a function of the writer and the stale row's owner]. */
const ROWS: [string, (w: string, s: StaleOwner) => Case][] = [
  ["cap-2 held today: the (cap-1)th write records", (w, s) => {
    const pre = [...fill(w, CAP - 2, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap-1 held today: the cap-th write records", (w, s) => {
    const pre = [...fill(w, CAP - 1, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap held today: the (cap+1)th write is 429 and writes nothing, not even the purge", (w, s) => {
    const pre = [...fill(w, CAP, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held today: a place the writer already holds today is 200 and adds nothing", (w, s) => {
    const pre = [...fill(w, CAP, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: "1000", answer: RECORDED, post: purged(pre) };
  }],
  ["the other user at the cap today does not limit the writer", (w, s) => {
    const pre = [...fill(other(w), CAP, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap held today: the place held today by the other user only is 429", (w, s) => {
    const pre = [...fill(w, CAP, TODAY), row(other(w), PLACE, CELL, TODAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held today: the place the writer held yesterday only is 429", (w, s) => {
    const pre = [...fill(w, CAP, TODAY), written(w, YESTERDAY), staleRow(w, s)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held yesterday: at 23:59:59.999Z the day has not turned and the write is 429", (w, s) => {
    const pre = [...fill(w, CAP, YESTERDAY), staleRow(w, s)];
    return { now: "2026-10-04T23:59:59.999Z", pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held yesterday: at 00:00:00.000Z the day has turned and the write records today", (w, s) => {
    const pre = [...fill(w, CAP, YESTERDAY), staleRow(w, s)];
    return { now: "2026-10-05T00:00:00.000Z", pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("POST /ledger caps each user's rows per UTC day (T-0304 R1-R3)", () => {
  it("no row ignores the writer: every row's expected answer or table differs between the two writers", () => {
    const same = ROWS.flatMap(([name, c]) => STALE_OWNERS.filter((s) => JSON.stringify(c(USER_A, s)) === JSON.stringify(c(USER_B, s)))
      .map((s) => `${name} / ${s}`));
    expect(same).toEqual([]);
  });

  it("no row ignores the stale owner: every row's expected table differs between the writer's own stale row and the other's", () => {
    const same = ROWS.flatMap(([name, c]) => Object.values(WRITERS)
      .filter((w) => JSON.stringify(c(w, "writer")) === JSON.stringify(c(w, "other"))).map((w) => `${name} / ${w}`));
    expect(same).toEqual([]);
  });

  it("every refused row and every recorded row runs with the stale row owned by the writer and by the other user", () => {
    const owners = (answer: unknown) => ROWS.flatMap(([, c]) => STALE_OWNERS.filter((s) =>
      JSON.stringify(c(USER_A, s).answer) === JSON.stringify(answer)
      && c(USER_A, s).pre.some((r) => r.place_id === "77" && r.user_id === (s === "writer" ? USER_A : USER_B))));
    expect([new Set(owners(REFUSED)), new Set(owners(RECORDED))]).toEqual([new Set(STALE_OWNERS), new Set(STALE_OWNERS)]);
  });

  it("at cap-2, cap-1 and cap rows held and across the UTC midnight, the write answers 200 or 429 ledger_daily_cap and leaves exactly the expected table, for each writer", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [variant, writer] of Object.entries(WRITERS)) for (const owner of STALE_OWNERS) {
      for (const [name, build] of ROWS) {
        const c = build(writer, owner);
        vi.setSystemTime(new Date(c.now));
        await seed(c.pre);
        const answer = await apply({ method: "POST", body: { place_id: c.place, cell: CELL } }, writer, shippedEnv(fakeQuotaNamespace()));
        got.push([variant, owner, name, answer, await ledgerTable()]);
        want.push([variant, owner, name, c.answer, sortRows(c.post)]);
      }
    }
    expect(got).toEqual(want);
  }, 300_000);

  it("the answer turns on D1's admission row alone: only admitted exactly 1 records, every other batch result shape is 429", async () => {
    vi.setSystemTime(new Date(NOON));
    const shapes: [string, unknown, unknown][] = [
      ["the batch returns no results", [], REFUSED],
      ["the admission statement returns no row", [{ results: [] }, { results: [] }, { results: [] }], REFUSED],
      ["the admission row has no admitted", [{ results: [{}] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is null", [{ results: [{ admitted: null }] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is 0", [{ results: [{ admitted: 0 }] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is the string 1", [{ results: [{ admitted: "1" }] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is true", [{ results: [{ admitted: true }] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is 2", [{ results: [{ admitted: 2 }] }, { results: [] }, { results: [] }], REFUSED],
      ["admitted is 1", [{ results: [{ admitted: 1 }] }, { results: [] }, { results: [] }], RECORDED],
    ];
    const got: unknown[] = [];
    for (const [name, result] of shapes) {
      const statement = { bind: () => statement };
      const DB = { prepare: () => statement, batch: async () => result };
      const e = shippedEnv(fakeQuotaNamespace(), { DB });
      got.push([name, await apply({ method: "POST", body: { place_id: PLACE, cell: CELL } }, USER_A, e)]);
    }
    expect(got).toEqual(shapes.map(([name, , answer]) => [name, answer]));
  });
});
