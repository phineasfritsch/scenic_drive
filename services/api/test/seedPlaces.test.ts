/**
 * T-0393 R2, R3, R7: the SQL `ops/seed-places` ships, applied to a local D1 built by every shipped migration. The files
 * under fixtures/seed-places/ are that entry point's output for services/etl/tests/test_seedplaces.py's fixture corpus
 * (the pytest requires them byte-equal to a fresh run). Rows are read back whole and compared to rows typed here;
 * ids above 2^53 stay exact strings. The Worker's own read, d1PlaceResolver, then resolves every one.
 */
import { env } from "cloudflare:test";
import { beforeEach, describe, expect, it } from "vitest";
import { d1PlaceResolver } from "../src/placeResolver";
import { freshAllTables } from "./siwaHarness";

const SEED = import.meta.glob("./fixtures/seed-places/*.sql", { query: "?raw", import: "default", eager: true }) as Record<string, string>;

/** [id, lat_e7, lon_e7] of the fixture corpus, typed out; ascending id as text sorts them. */
const FIXTURE: [string, number, number][] = [
  ["1", 900000000, 1800000000],
  ["5618378043290861", 342641350, -1185229920],
  ["9007199254740993", 0, 0],
  ["9221466198646572373", 344491615, -1178446900],
  ["9223372036854775807", -900000000, -1800000000],
];
const EXPECTED = FIXTURE.map(([id, lat, lon]) => ({ id, lat: lat / 1e7, lon: lon / 1e7 }));

async function seed(): Promise<void> {
  const files = Object.keys(SEED).sort();
  expect(files.map((f) => f.split("/").pop())).toEqual(["places-0001.sql", "places-0002.sql", "places-0003.sql"]);
  for (const file of files) await env.DB.prepare(SEED[file]!).run();
}

async function rows(): Promise<unknown[]> {
  return (await env.DB.prepare("SELECT id, lat, lon FROM places ORDER BY id").all()).results;
}

beforeEach(async () => {
  await freshAllTables();
});

describe("ops/seed-places SQL on D1 places (T-0393)", () => {
  it("the seeded rows are the fixture corpus whole: decimal place_id text, lat_e7 / 1e7, lon_e7 / 1e7", async () => {
    await seed();
    expect(await rows()).toEqual(EXPECTED);
  });

  it("a second apply leaves the same rows", async () => {
    await seed();
    await seed();
    expect(await rows()).toEqual(EXPECTED);
  });

  it("a stale coordinate is updated and a row the corpus does not carry is kept (R2: upsert, never delete)", async () => {
    await env.DB.prepare("INSERT INTO places (id, lat, lon) VALUES ('5618378043290861', 1.5, 2.5), ('42', 3.5, 4.5)").run();
    await seed();
    expect(await rows()).toEqual([...EXPECTED, { id: "42", lat: 3.5, lon: 4.5 }].sort((a, b) => (a.id < b.id ? -1 : 1)));
  });

  it("d1PlaceResolver - the Worker's /plan and /trip read - resolves every seeded id and null for an unseeded one", async () => {
    await seed();
    const resolve = d1PlaceResolver(env.DB);
    const got = await Promise.all(FIXTURE.map(([id]) => resolve(id)));
    expect(got).toEqual(EXPECTED.map(({ lat, lon }) => ({ lat, lon })));
    expect(await resolve("9007199254740992")).toBeNull();
  });
});
