/**
 * T-0293 R9, R10 (P-PRIV-05, P-PRIV-06): the server-column clause, read from D1 itself. Every shipped migration is applied
 * to the test database and every column of every table it creates is read back with pragma_table_info - the schema the
 * Worker would run against, not the SQL's spelling - so a column added under any spelling of CREATE or ALTER is seen.
 */
import { env } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";
import { freshAllTables, migrationTables } from "./siwaHarness";

const FORBIDDEN = /home|address|breadcrumb|trail|speed/i;

/** Every table in the database bar SQLite's and D1's own, with its columns in declaration order. */
async function columns(): Promise<Record<string, string[]>> {
  const { results } = await env.DB.prepare(
    "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_cf_%' ORDER BY name").all();
  const out: Record<string, string[]> = {};
  for (const { name } of results as { name: string }[]) {
    const info = await env.DB.prepare("SELECT name FROM pragma_table_info(?1) ORDER BY cid").bind(name).all();
    out[name] = (info.results as { name: string }[]).map((c) => c.name);
  }
  return out;
}

beforeEach(async () => {
  await freshAllTables();
});

describe("the D1 schema the shipped migrations build (T-0293 R10)", () => {
  it("no column of any table the shipped migrations create names home, address, breadcrumb, trail or speed (P-PRIV-05)", async () => {
    const schema = await columns();
    expect(Object.keys(schema)).toEqual(expect.arrayContaining(migrationTables()));
    expect(Object.keys(schema).length).toBeGreaterThanOrEqual(8);
    expect(Object.entries(schema).flatMap(([t, cs]) => cs.filter((c) => FORBIDDEN.test(c)).map((c) => `${t}.${c}`))).toEqual([]);
  });

  it("the waitlist table is exactly (cell, count, updated_at): no column can hold a person (P-PRIV-06)", async () => {
    expect((await columns()).waitlist).toEqual(["cell", "count", "updated_at"]);
  });

  it("the waitlist dedupe table is exactly (tag, day): no column can hold a device, a cell or an instant (T-0296, P-PRIV-05)", async () => {
    expect((await columns()).waitlist_seen).toEqual(["tag", "day"]);
  });

  it("the surprise ledger table is exactly (user_id, place_id, cell, day): no coordinate, no instant finer than a day (T-0302 R9, P-PRIV-05)", async () => {
    expect((await columns()).surprise_ledger).toEqual(["user_id", "place_id", "cell", "day"]);
  });
});
