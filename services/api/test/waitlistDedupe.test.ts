/**
 * T-0296 (P-PRIV-06, P-PRIV-05): POST /waitlist counts one device once per cell per UTC day. The dedupe row is a keyed
 * tag - HMAC(HMAC(SESSION_JWT_SECRET, "scenic-waitlist/v1/" + day), who + "\n" + cell) - recomputed here by an
 * independent WebCrypto oracle and compared WHOLE, with the waitlist table, after every step of one sequence, over two
 * table variants whose expected rows are computed from the variant's own pre-state.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import { signSession } from "../src/sessionJwt";
import waitlistSql from "../migrations/0006_waitlist.sql?raw";
import seenSql from "../migrations/0007_waitlist_seen.sql?raw";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";

const SECRET = "t0296-waitlist-test-secret-0123456789abcdef";
const CELL = "85283473fffffff";
const OTHER = "850dab63fffffff";
const DEVICE_A = "1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f";
const DEVICE_B = "6f5e4d3c-2b1a-4f0e-9d8c-7b6a5f4e3d2c";
const DEVICE_C = "0a0b0c0d-0e0f-4a1b-8c2d-3e4f5a6b7c8d";
const UNIDENTIFIED = "unidentified";
type Row = Record<string, unknown>;
type Who = "A" | "B" | "none" | "bad-bearer" | "header-only";
const SUB: Record<Who, string> = { A: DEVICE_A, B: DEVICE_B, none: UNIDENTIFIED, "bad-bearer": UNIDENTIFIED, "header-only": UNIDENTIFIED };

const utf8 = (t: string) => new TextEncoder().encode(t);
async function hmac(key: Uint8Array, message: string): Promise<Uint8Array> {
  const k = await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", k, utf8(message)));
}
/** The ruled tag (R2), recomputed from the ruling's text and not from src. */
async function oracleTag(secret: string, who: string, cell: string, day: string): Promise<string> {
  const dayKey = await hmac(utf8(secret), `scenic-waitlist/v1/${day}`);
  return Array.from(await hmac(dayKey, `${who}\n${cell}`), (b) => (b < 16 ? "0" : "") + b.toString(16)).join("");
}

interface Variant { waitlist: Row[]; seen: Row[] }
const VARIANTS: Record<string, () => Promise<Variant>> = {
  empty: async () => ({ waitlist: [], seen: [] }),
  holding: async () => ({
    waitlist: [{ cell: CELL, count: 3, updated_at: "2026-10-01" }, { cell: OTHER, count: 1, updated_at: "2026-09-30" }],
    // yesterday's tag of A at CELL (must be purged) and today's tag of B at OTHER (must make B's post a repeat)
    seen: [{ tag: await oracleTag(SECRET, DEVICE_A, CELL, "2026-10-04"), day: "2026-10-04" },
      { tag: await oracleTag(SECRET, DEVICE_B, OTHER, "2026-10-05"), day: "2026-10-05" }],
  }),
};

/** One step: the instant, who sends, the cell. */
const STEPS: [string, string, Who, string][] = [
  ["A first", "2026-10-05T12:00:00.000Z", "A", CELL],
  ["A repeats the cell", "2026-10-05T12:00:01.000Z", "A", CELL],
  ["B, a second device", "2026-10-05T12:00:02.000Z", "B", CELL],
  ["B at the other cell", "2026-10-05T12:00:03.000Z", "B", OTHER],
  ["A at the other cell", "2026-10-05T12:00:04.000Z", "A", OTHER],
  ["no bearer", "2026-10-05T12:00:05.000Z", "none", CELL],
  ["a bearer that does not verify: the same unidentified bucket", "2026-10-05T12:00:06.000Z", "bad-bearer", CELL],
  ["A at the last instant of the day", "2026-10-05T23:59:59.999Z", "A", CELL],
  ["A at the first instant of the next day", "2026-10-06T00:00:00.000Z", "A", CELL],
  ["A again that instant", "2026-10-06T00:00:00.000Z", "A", CELL],
  ["no bearer the next day", "2026-10-06T00:00:01.000Z", "none", CELL],
  ["a bare x-scenic-device header with the secret set: unidentified", "2026-10-06T00:00:02.000Z", "header-only", CELL],
  ["B at the other cell the next day", "2026-10-06T00:00:03.000Z", "B", OTHER],
];

let quota: FakeQuota;

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  quota = fakeQuotaNamespace();
  vi.stubGlobal("fetch", async () => new Response("{}", { status: 500 }));
  for (const sql of [waitlistSql, seenSql]) {
    for (const statement of sql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  }
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const byJson = (rows: Row[]) => rows.map((r) => JSON.stringify(r)).sort().map((r) => JSON.parse(r) as Row);

async function seed(v: Variant): Promise<void> {
  await env.DB.prepare("DELETE FROM waitlist").run();
  await env.DB.prepare("DELETE FROM waitlist_seen").run();
  for (const r of v.waitlist) {
    await env.DB.prepare("INSERT INTO waitlist (cell, count, updated_at) VALUES (?1, ?2, ?3)").bind(r.cell, r.count, r.updated_at).run();
  }
  for (const r of v.seen) await env.DB.prepare("INSERT INTO waitlist_seen (tag, day) VALUES (?1, ?2)").bind(r.tag, r.day).run();
}

async function tables(): Promise<Variant> {
  const waitlist = (await env.DB.prepare("SELECT * FROM waitlist").all()).results as Row[];
  const seen = (await env.DB.prepare("SELECT * FROM waitlist_seen").all()).results as Row[];
  return { waitlist: byJson(waitlist), seen: byJson(seen) };
}

/** `secret` null leaves SESSION_JWT_SECRET unbound (an explicit sentinel: undefined would take the default). */
async function send(at: string, who: Who, cell: string, secret: string | null = SECRET) {
  vi.setSystemTime(new Date(at));
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (who === "A" || who === "B") headers.authorization = `Bearer ${(await signSession(SECRET, { sub: SUB[who] }, Date.parse(at))).token}`;
  if (who === "bad-bearer") headers.authorization = "Bearer not.a.jwt";
  if (who === "header-only") headers["x-scenic-device"] = DEVICE_C;
  const e = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
    ...(secret === null ? {} : { SESSION_JWT_SECRET: secret }) } as unknown as Env;
  const response = await worker.fetch(new Request("https://scenic-api.test/waitlist", { method: "POST", headers, body: JSON.stringify({ cell }) }), e);
  return { status: response.status, json: (await response.json()) as unknown };
}

const OK = { status: 200, json: { waitlisted: true } };
const UNAVAILABLE = { status: 503, json: { error: "waitlist_unavailable" } };

/** The ruled model (R2, R4): purge other days, count iff the tag is new, date the count by the UTC day. */
async function expectedTrace(pre: Variant): Promise<unknown[]> {
  let waitlist = pre.waitlist.map((r) => ({ ...r }));
  let seen = pre.seen.map((r) => ({ ...r }));
  const trace: unknown[] = [];
  for (const [label, at, who, cell] of STEPS) {
    const day = at.slice(0, 10);
    seen = seen.filter((r) => r.day === day);
    const tag = await oracleTag(SECRET, SUB[who], cell, day);
    if (!seen.some((r) => r.tag === tag)) {
      seen.push({ tag, day });
      const row = waitlist.find((r) => r.cell === cell);
      waitlist = row ? waitlist.map((r) => (r === row ? { cell, count: (r.count as number) + 1, updated_at: day } : r))
        : [...waitlist, { cell, count: 1, updated_at: day }];
    }
    trace.push([label, OK, { waitlist: byJson(waitlist), seen: byJson(seen) }]);
  }
  return trace;
}

describe("POST /waitlist counts one device once per cell per UTC day (T-0296)", () => {
  it("the variants' expected traces differ, so no row can pass by ignoring the tables it runs over", async () => {
    expect(await expectedTrace(await VARIANTS.empty!())).not.toEqual(await expectedTrace(await VARIANTS.holding!()));
  });

  it("same device same cell same day counts once; a second device, a second cell and the next day count again - every step's tables whole, over both variants", async () => {
    const answered: unknown[] = [];
    const expected: unknown[] = [];
    for (const [name, make] of Object.entries(VARIANTS)) {
      const pre = await make();
      await seed(pre);
      for (const [label, at, who, cell] of STEPS) answered.push([name, label, await send(at, who, cell), await tables()]);
      expected.push(...(await expectedTrace(pre)).map((row) => [name, ...(row as unknown[])]));
    }
    expect(answered).toEqual(expected);
    expect(quota.state()).toEqual({});
  });

  it("the dedupe table holds no device id and no cell, only 64-hex tags and the UTC day", async () => {
    await seed(await VARIANTS.empty!());
    for (const [, at, who, cell] of STEPS.slice(0, 7)) await send(at, who, cell);
    const { seen } = await tables();
    expect(seen.length).toBe(5);
    const text = JSON.stringify(seen);
    expect([DEVICE_A, DEVICE_B, CELL, OTHER, UNIDENTIFIED].filter((s) => text.includes(s))).toEqual([]);
    expect(seen.every((r) => /^[0-9a-f]{64}$/.test(String(r.tag)) && r.day === "2026-10-05" && Object.keys(r).length === 2)).toBe(true);
  });

  it("without a usable SESSION_JWT_SECRET the route fails closed: unbound, empty or 31 chars is 503 and writes nothing; 32 chars counts", async () => {
    const answered: unknown[] = [];
    const expected: unknown[] = [];
    const at = "2026-10-05T12:00:00.000Z";
    for (const [name, make] of Object.entries(VARIANTS)) {
      const pre = await make();
      for (const secret of [null, "", "s".repeat(31)]) {
        await seed(pre);
        answered.push([name, String(secret?.length), await send(at, "none", OTHER, secret), await tables()]);
        expected.push([name, String(secret?.length), UNAVAILABLE, { waitlist: byJson(pre.waitlist), seen: byJson(pre.seen) }]);
      }
      const exact = "s".repeat(32);
      await seed(pre);
      answered.push([name, "32", await send(at, "none", OTHER, exact), await tables()]);
      const other = pre.waitlist.find((r) => r.cell === OTHER);
      expected.push([name, "32", OK, {
        waitlist: byJson([...pre.waitlist.filter((r) => r.cell !== OTHER),
          { cell: OTHER, count: ((other?.count as number | undefined) ?? 0) + 1, updated_at: "2026-10-05" }]),
        seen: byJson([...pre.seen.filter((r) => r.day === "2026-10-05"),
          { tag: await oracleTag(exact, UNIDENTIFIED, OTHER, "2026-10-05"), day: "2026-10-05" }]),
      }]);
    }
    expect(answered).toEqual(expected);
  });
});
