/**
 * T-0344: /__health's read-only quota fields, which ops/sane --prod reads for its exit 6. Every case is the WHOLE
 * answer - status and body by full equality - through the shipped worker.fetch, over every QUOTA reading x every
 * kill source, plus the quota state after the request (a health read writes nothing). The trip point is typed out:
 * a test that read the constant the handler reads would assert nothing.
 */
import { env } from "cloudflare:test";
import { describe, expect, it } from "vitest";
import worker, { type Env } from "../src/index";
import { killSwitchTripped } from "../src/quota";
import { fakeKv, fakeQuotaNamespace } from "./doFake";

const TRIP_AT = 225000;
const month = (d: Date) => d.toISOString().slice(0, 7);
const lastMonth = (d: Date) => month(new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - 1, 15)));

type QuotaRow = { name: string; make: (now: Date) => { ns: unknown; state: () => unknown }; calls: number | null; after: (now: Date) => unknown };

const seeded = (record: (now: Date) => unknown) => (now: Date) => {
  const q = fakeQuotaNamespace();
  q.seed("global", "monthly", record(now));
  return q;
};

const QUOTAS: QuotaRow[] = [
  { name: "nothing reserved", make: () => fakeQuotaNamespace(), calls: 0, after: () => ({ global: {} }) },
  { name: "1234 reserved this month", make: seeded((n) => ({ month: month(n), calls: 1234 })), calls: 1234,
    after: (n) => ({ global: { monthly: { month: month(n), calls: 1234 } } }) },
  { name: "the trip point reserved", make: seeded((n) => ({ month: month(n), calls: TRIP_AT })), calls: TRIP_AT,
    after: (n) => ({ global: { monthly: { month: month(n), calls: TRIP_AT } } }) },
  { name: "last month's record", make: seeded((n) => ({ month: lastMonth(n), calls: 99 })), calls: 0,
    after: (n) => ({ global: { monthly: { month: lastMonth(n), calls: 99 } } }) },
  { name: "a string count", make: seeded((n) => ({ month: month(n), calls: "7" })), calls: null,
    after: (n) => ({ global: { monthly: { month: month(n), calls: "7" } } }) },
  { name: "a negative count", make: seeded((n) => ({ month: month(n), calls: -1 })), calls: null,
    after: (n) => ({ global: { monthly: { month: month(n), calls: -1 } } }) },
  { name: "a fractional count", make: seeded((n) => ({ month: month(n), calls: 1.5 })), calls: null,
    after: (n) => ({ global: { monthly: { month: month(n), calls: 1.5 } } }) },
  { name: "QUOTA unbound", make: () => ({ ns: undefined, state: () => "unbound" }), calls: null, after: () => "unbound" },
  { name: "readMonthly throws", calls: null, after: () => "threw",
    make: () => ({ ns: { idFromName: (n: string) => ({ n }), get: () => ({ readMonthly: async () => { throw new Error("DO down"); } }) },
      state: () => "threw" }) },
];

const KILLS: { name: string; env: () => Record<string, unknown>; killed: boolean }[] = [
  { name: "no kill source", env: () => ({}), killed: false },
  { name: "env KILL=1", env: () => ({ KILL: "1" }), killed: true },
  { name: "env KILL=0", env: () => ({ KILL: "0" }), killed: false },
  { name: "KV KILL=1", env: () => ({ KILL_SWITCH: fakeKv({ KILL: "1" }) }), killed: true },
  { name: "KV KILL=0", env: () => ({ KILL_SWITCH: fakeKv({ KILL: "0" }) }), killed: false },
  { name: "KV get throws", env: () => ({ KILL_SWITCH: fakeKv({}, true) }), killed: true },
];

const DB_DOWN = { prepare: () => { throw new Error("D1 down"); } };

async function answer(e: Record<string, unknown>) {
  const r = await worker.fetch(new Request("https://scenic-api.test/__health"), e as unknown as Env);
  return { status: r.status, contentType: r.headers.get("content-type"), body: await r.json() };
}

const whole = (now: Date, db: boolean, killed: boolean, calls: number | null) => ({
  status: db ? 200 : 503,
  contentType: "application/json; charset=utf-8",
  body: { ok: db, db: db ? "up" : "down", git_sha: "test", kill_switch: killed, upstream_month: month(now),
    upstream_calls: calls, upstream_trip_at: TRIP_AT },
});

describe("/__health quota fields (T-0344)", () => {
  it("the whole /__health answer over every QUOTA reading x every kill source, D1 up and down, through the shipped worker.fetch, and the quota state is untouched", async () => {
    for (const db of [true, false]) {
      for (const q of QUOTAS) {
        for (const k of KILLS) {
          const now = new Date();
          const quota = q.make(now);
          const e = { DB: db ? env.DB : DB_DOWN, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ...k.env() };
          const got = await answer(e);
          const label = `${db ? "D1 up" : "D1 down"} / ${q.name} / ${k.name}`;
          expect({ label, ...got, state: quota.state() }).toEqual({ label, ...whole(now, db, k.killed, q.calls), state: q.after(now) });
        }
      }
    }
  });

  it("upstream_trip_at is the least monthly count killSwitchTripped refuses", async () => {
    const got = await answer({ DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: fakeQuotaNamespace().ns });
    const trip = (got.body as { upstream_trip_at: number }).upstream_trip_at;
    expect({ trip, at: killSwitchTripped(trip), below: killSwitchTripped(trip - 1) }).toEqual({ trip: TRIP_AT, at: true, below: false });
  });
});
