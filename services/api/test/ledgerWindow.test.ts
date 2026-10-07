/**
 * T-0302 R4, R5: the 90-day window's every bound, by literal rows (not the model). A row dated exactly 90 UTC days
 * before today is returned; 91 days is not, and the next write deletes it - for every user, not only the writer. Each
 * side of each day boundary is a row: 23:59:59.999Z and the 00:00:00.000Z one millisecond later.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fakeQuotaNamespace } from "./doFake";
import { apply, CELL, ledgerTable, OTHER, row, seed, shippedEnv, sortRows, USER_A, USER_B } from "./ledgerHarness";

const SEED = [
  row(USER_A, "11", CELL, "2026-07-08"), row(USER_A, "12", CELL, "2026-07-07"), row(USER_A, "13", CELL, "2026-07-06"),
  row(USER_B, "21", OTHER, "2026-07-07"), row(USER_B, "22", OTHER, "2026-07-06"),
];
const [A11, A12, A13, B21] = SEED as [typeof SEED[0], typeof SEED[0], typeof SEED[0], typeof SEED[0]];
const read = (...rows: (typeof SEED)[0][]) => ({ status: 200, json: { places: rows.map(({ place_id, cell, day }) => ({ place_id, cell, day })) } });
const written = (day: string) => row(USER_A, "99", CELL, day);

/** [now, A's GET before the write, the whole table after A posts place 99]. */
const BOUNDS: [string, unknown, (typeof SEED)[0][]][] = [
  // today 2026-10-04: the first day is 2026-07-06, so the 90-day-old 07-06 rows are inside.
  ["2026-10-04T23:59:59.999Z", read(A11, A12, A13), [...SEED, written("2026-10-04")]],
  // today 2026-10-05: 07-07 is exactly 90 days old (returned, kept); 07-06 is 91 (not returned, deleted for A and B).
  ["2026-10-05T00:00:00.000Z", read(A11, A12), [A11, A12, B21, written("2026-10-05")]],
  ["2026-10-05T23:59:59.999Z", read(A11, A12), [A11, A12, B21, written("2026-10-05")]],
  // today 2026-10-06: 07-07 is now 91 days old.
  ["2026-10-06T00:00:00.000Z", read(A11), [A11, written("2026-10-06")]],
];

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("the /ledger 90-day window (T-0302 R4, R5)", () => {
  it("90 days is returned and kept, 91 is not returned and is deleted on the next write, on each side of each midnight", async () => {
    const got: unknown[] = [];
    for (const [now] of BOUNDS) {
      vi.setSystemTime(new Date(now));
      const quota = fakeQuotaNamespace();
      await seed(SEED);
      const before = await apply({ method: "GET" }, USER_A, shippedEnv(quota));
      const posted = await apply({ method: "POST", body: { place_id: "99", cell: CELL } }, USER_A, shippedEnv(quota));
      got.push([now, before, posted, await ledgerTable()]);
    }
    expect(got).toEqual(BOUNDS.map(([now, before, after]) => [now, before, { status: 200, json: { recorded: true } }, sortRows(after)]));
  });

  it("GET writes nothing: a 91-day-old row outlives any number of reads", async () => {
    vi.setSystemTime(new Date("2026-10-06T00:00:00.000Z"));
    const quota = fakeQuotaNamespace();
    await seed(SEED);
    const reads = [];
    for (const user of [USER_A, USER_B]) reads.push(await apply({ method: "GET" }, user, shippedEnv(quota)));
    expect({ reads, table: await ledgerTable() }).toEqual({ reads: [read(A11), read()], table: sortRows(SEED) });
  });
});
