/**
 * T-0304 R1-R3: POST /ledger admits at most 200 rows per user per UTC day (LEDGER_DAILY_CAP, the paid Surprise
 * allowance by reference; the literal here is the ruled number, so a moved reference fails). Every row runs once per
 * writer variant (USER_A writes, USER_B writes) over a seed built from the writer; the expected answer and the whole
 * table after are literal functions of the writer, and a meta-test holds that no row's expectation is the same for
 * both writers. A refused write is 429 ledger_daily_cap and writes nothing - no insert and no purge (a stale row of the
 * other user, outside the window, survives it). Bounds: cap-2, cap-1 and cap rows held, and across the UTC midnight.
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
/** The other user's row outside the 90-day window at every instant below: a successful write purges it, a refusal does not. */
const stale = (writer: string) => row(other(writer), "77", OTHER, "2026-07-01");

const RECORDED = { status: 200, json: { recorded: true } };
const REFUSED = { status: 429, json: { error: "ledger_daily_cap" } };
interface Case { now: string; pre: LedgerRow[]; place: string; answer: unknown; post: LedgerRow[] }
const written = (writer: string, day: string) => row(writer, PLACE, CELL, day);
const purged = (pre: LedgerRow[]) => pre.filter((r) => r.place_id !== "77");

/** [name, the case as a function of the writer]. */
const ROWS: [string, (w: string) => Case][] = [
  ["cap-2 held today: the (cap-1)th write records", (w) => {
    const pre = [...fill(w, CAP - 2, TODAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap-1 held today: the cap-th write records", (w) => {
    const pre = [...fill(w, CAP - 1, TODAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap held today: the (cap+1)th write is 429 and writes nothing, not even the purge", (w) => {
    const pre = [...fill(w, CAP, TODAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held today: a place the writer already holds today is 200 and adds nothing", (w) => {
    const pre = [...fill(w, CAP, TODAY), stale(w)];
    return { now: NOON, pre, place: "1000", answer: RECORDED, post: purged(pre) };
  }],
  ["the other user at the cap today does not limit the writer", (w) => {
    const pre = [...fill(other(w), CAP, TODAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: RECORDED, post: [...purged(pre), written(w, TODAY)] };
  }],
  ["cap held today: the place held today by the other user only is 429", (w) => {
    const pre = [...fill(w, CAP, TODAY), row(other(w), PLACE, CELL, TODAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held today: the place the writer held yesterday only is 429", (w) => {
    const pre = [...fill(w, CAP, TODAY), written(w, YESTERDAY), stale(w)];
    return { now: NOON, pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held yesterday: at 23:59:59.999Z the day has not turned and the write is 429", (w) => {
    const pre = [...fill(w, CAP, YESTERDAY), stale(w)];
    return { now: "2026-10-04T23:59:59.999Z", pre, place: PLACE, answer: REFUSED, post: pre };
  }],
  ["cap held yesterday: at 00:00:00.000Z the day has turned and the write records today", (w) => {
    const pre = [...fill(w, CAP, YESTERDAY), stale(w)];
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
    expect(ROWS.filter(([, c]) => JSON.stringify(c(USER_A)) === JSON.stringify(c(USER_B))).map(([name]) => name)).toEqual([]);
  });

  it("at cap-2, cap-1 and cap rows held and across the UTC midnight, the write answers 200 or 429 ledger_daily_cap and leaves exactly the expected table, for each writer", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [variant, writer] of Object.entries(WRITERS)) {
      for (const [name, build] of ROWS) {
        const c = build(writer);
        vi.setSystemTime(new Date(c.now));
        await seed(c.pre);
        const answer = await apply({ method: "POST", body: { place_id: c.place, cell: CELL } }, writer, shippedEnv(fakeQuotaNamespace()));
        got.push([variant, name, answer, await ledgerTable()]);
        want.push([variant, name, c.answer, sortRows(c.post)]);
      }
    }
    expect(got).toEqual(want);
  }, 120_000);
});
