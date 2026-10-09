/**
 * T-0326 (P-PRIV-04): DELETE /account sweeps PLANS. A plan remembered for any of the user's devices - the session
 * device and every device bound to the user's Apple subs - is gone with the account, not after the 12 h TTL; every
 * other key is unchanged, compared WHOLE against the test's own key predicate over the row's device set. The fake KV
 * lists in pages of two with an EMPTY page (list_complete false) after the first, continued by cursor, as the Workers
 * runtime may answer. A PLANS failure or the operation bound never fails the deletion: it answers plans_pending.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES, type Env } from "../src/index";
import { PLAN_SWEEP_MAX_OPS } from "../src/planSweep";
import {
  ACCOUNT, allTables, APPLE_USER, CLIENT_SECRET, deleteAccount, DEVICE, fakeAppleFetch, freshAllTables, NOW, OTHER_APPLE_USER, OTHER_DEVICE,
  SECOND_DEVICE, SECRET, sessionToken, siwaDeps,
} from "./siwaHarness";

type Rows = Record<string, string>;
/** Cloudflare Workers: KV operations one invocation may make (T-0326 R7 measured). */
const WORKERS_KV_OPS_PER_INVOCATION = 1000;
const T = (n: number) => `0f1e2d3c-4b5a-4968-8776-${String(n).padStart(12, "0")}`;
const UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";
const plan = (device: string, n: number): [string, string] =>
  [`plan:${device}:${T(n)}`, JSON.stringify({ device, place: "la:topanga", pins: [{ lat: 34.03, lon: -118.52 }], lambda: 7.75 })];

/** The user's devices' plans beside every neighbour a sweep must leave: another user, the unidentified bucket, the
 *  pre-T-0326 shape, a key past a token, an uppercase token, a device id extending DEVICE, another prefix. */
const HOLDING: Rows = Object.fromEntries([
  ...[1, 2, 3, 4, 5].map((n) => plan(DEVICE, n)), ...[6, 7, 8].map((n) => plan(SECOND_DEVICE, n)),
  ...[9, 10].map((n) => plan(OTHER_DEVICE, n)), plan("unidentified", 11), [`plan:${T(12)}`, "legacy"],
  [`plan:${DEVICE}:${T(13)}:x`, "past"], [`plan:${DEVICE}:${T(14).toUpperCase()}`, "upper"], [`plan:${DEVICE}0:${T(15)}`, "extends"],
  [`quota:${DEVICE}`, "other prefix"],
]);
const STORES: Record<string, Rows> = { empty: {}, holding: HOLDING };

interface FakeOptions { page?: number; failList?: string; failDelete?: string; noCursor?: boolean }
interface SweepFake { store: Map<string, string>; ops: number; list: unknown; delete: unknown }

/** A KV namespace's list/delete over a Map: pages of `page` keys in key order, an empty incomplete page after the
 *  first, the cursor naming the last key served (so a delete never shifts the next page). */
function sweepKv(rows: Rows, o: FakeOptions = {}): SweepFake {
  const store = new Map(Object.entries(rows));
  const size = o.page ?? 2;
  const fake: SweepFake = {
    store,
    ops: 0,
    async list({ prefix, cursor }: { prefix: string; cursor?: string }) {
      fake.ops += 1;
      if (o.failList === prefix) throw new Error("kv down");
      if (cursor?.startsWith("empty|")) return { keys: [], list_complete: false, cursor: `after|${cursor.slice(6)}` };
      const after = cursor?.startsWith("after|") ? cursor.slice(6) : null;
      const names = [...store.keys()].filter((k) => k.startsWith(prefix) && (after === null || k > after)).sort();
      const keys = names.slice(0, size).map((name) => ({ name }));
      if (names.length <= size) return { keys, list_complete: true };
      const next = `${after === null ? "empty" : "after"}|${keys[keys.length - 1]!.name}`;
      return o.noCursor ? { keys, list_complete: false } : { keys, list_complete: false, cursor: next };
    },
    async delete(key: string) {
      fake.ops += 1;
      if (o.failDelete === key) throw new Error("kv down");
      store.delete(key);
    },
  };
  return fake;
}

/** The test's own predicate: a plan key of one of `devices`, a lowercase token after it. */
const userKey = (devices: string[]) => new RegExp(`^plan:(${devices.join("|")}):${UUID}$`);
const minus = (rows: Rows, gone: (key: string) => boolean): Rows => Object.fromEntries(Object.entries(rows).filter(([k]) => !gone(k)));
const contents = (kv: SweepFake): Rows => Object.fromEntries([...kv.store.entries()]);

const unbind = () => env.DB.prepare("DELETE FROM apple_accounts WHERE device_id = ?1").bind(DEVICE).run();
interface Session { claims: Record<string, string>; before?: () => Promise<unknown>; devices: string[] }
/** Each row's device set is what USER_DEVICES selects for it: the session device plus the subs' bound devices. */
const SESSIONS: Record<string, Session> = {
  "apple claim": { claims: { act: ACCOUNT, apple: APPLE_USER }, devices: [DEVICE, SECOND_DEVICE] },
  "act only": { claims: { act: ACCOUNT }, devices: [DEVICE, SECOND_DEVICE] },
  "apple claim with the device unbound": { claims: { apple: APPLE_USER }, before: unbind, devices: [DEVICE, SECOND_DEVICE] },
  "no claims with the device unbound": { claims: {}, before: unbind, devices: [DEVICE] },
};

async function seed(): Promise<void> {
  await env.DB.prepare("INSERT INTO apple_accounts VALUES (?1, ?2, 'r.1', 1), (?3, ?2, 'r.2', 2), (?4, ?5, 'r.3', 3)")
    .bind(DEVICE, APPLE_USER, SECOND_DEVICE, OTHER_DEVICE, OTHER_APPLE_USER).run();
}

async function deletion(kv: SweepFake, s: Session) {
  await seed();
  if (s.before) await s.before();
  const deps = siwaDeps(fakeAppleFetch([]).fetchImpl, { APPLE_CLIENT_SECRET: CLIENT_SECRET, PLANS: kv as unknown as KVNamespace });
  const got = await deleteAccount(deps, await sessionToken(s.claims));
  return { got, bindings: (await allTables()).apple_accounts };
}

const ANSWER = (pending: boolean) => ({ status: 200, json: { deleted: true, revoke_pending: false, plans_pending: pending } });
const OTHERS_BINDING = [{ device_id: OTHER_DEVICE, apple_sub: OTHER_APPLE_USER, refresh_token: "r.3", bound_at: 3 }];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAllTables();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("DELETE /account sweeps PLANS (T-0326, P-PRIV-04)", () => {
  for (const [session, s] of Object.entries(SESSIONS)) {
    for (const [name, rows] of Object.entries(STORES)) {
      it(`every plan key of the user's devices is gone, every other key unchanged: ${session} x ${name}`, async () => {
        const kv = sweepKv(rows);
        const r = await deletion(kv, s);
        expect({ got: r.got, post: contents(kv) }).toEqual({ got: ANSWER(false), post: minus(rows, (k) => userKey(s.devices).test(k)) });
      });
    }
  }

  it("no row ignores its variant: the holding store's expected sweep differs between the device sets and the empty store's is empty", () => {
    const sets = [...new Set(Object.values(SESSIONS).map((s) => s.devices.join("|")))].map((d) => d.split("|"));
    const swept = sets.map((d) => Object.keys(HOLDING).filter((k) => userKey(d).test(k)).sort());
    expect({ sets: sets.length, distinct: new Set(swept.map((k) => k.join())).size,
      everyDevice: sets.map((d) => d.every((dev) => swept[sets.indexOf(d)]!.some((k) => k.startsWith(`plan:${dev}:`)))),
      empty: sets.map((d) => Object.keys(STORES.empty!).filter((k) => userKey(d).test(k))) })
      .toEqual({ sets: 2, distinct: 2, everyDevice: [true, true], empty: [[], []] });
  });

  const user = userKey([DEVICE, SECOND_DEVICE]);
  /** The first page the fake serves for a device: the first two keys under its prefix, in key order. */
  const firstPage = (device: string) => Object.keys(HOLDING).filter((k) => k.startsWith(`plan:${device}:`)).sort().slice(0, 2);
  const ARMS: [string, FakeOptions, (key: string) => boolean][] = [
    ["list throws for DEVICE, the first device swept", { failList: `plan:${DEVICE}:` }, (k) => userKey([SECOND_DEVICE]).test(k)],
    ["one delete throws", { failDelete: `plan:${DEVICE}:${T(3)}` }, (k) => user.test(k) && k !== `plan:${DEVICE}:${T(3)}`],
    ["a page incomplete without a cursor", { noCursor: true },
      (k) => user.test(k) && [...firstPage(DEVICE), ...firstPage(SECOND_DEVICE)].includes(k)],
  ];
  for (const [name, o, reached] of ARMS) {
    it(`a PLANS failure never fails the deletion: ${name}`, async () => {
      const kv = sweepKv(HOLDING, o);
      const r = await deletion(kv, SESSIONS["apple claim"]!);
      expect({ got: r.got, bindings: r.bindings, post: contents(kv) })
        .toEqual({ got: ANSWER(true), bindings: OTHERS_BINDING, post: minus(HOLDING, reached) });
    });
  }

  it("the sweep's operation bound: PLAN_SWEEP_MAX_OPS operations finish, one more leaves plans_pending", async () => {
    const many = (n: number): Rows => Object.fromEntries(Array.from({ length: n }, (_, i) => plan(DEVICE, 100 + i)));
    const s = SESSIONS["no claims with the device unbound"]!;
    const fits = sweepKv(many(PLAN_SWEEP_MAX_OPS - 1), { page: 1000 });
    const fitsGot = (await deletion(fits, s)).got;
    await freshAllTables();
    const over = sweepKv(many(PLAN_SWEEP_MAX_OPS), { page: 1000 });
    const overGot = (await deletion(over, s)).got;
    await freshAllTables();
    const second = sweepKv({ ...many(PLAN_SWEEP_MAX_OPS - 1), ...Object.fromEntries([plan(SECOND_DEVICE, 1)]) }, { page: 1000 });
    const secondGot = (await deletion(second, SESSIONS["apple claim"]!)).got;
    expect({ underTheWorkersLimit: PLAN_SWEEP_MAX_OPS < WORKERS_KV_OPS_PER_INVOCATION,
      fits: [fitsGot, fits.store.size, fits.ops], over: [overGot, over.store.size, over.ops],
      second: [secondGot, [...second.store.keys()], second.ops] })
      .toEqual({ underTheWorkersLimit: true, fits: [ANSWER(false), 0, PLAN_SWEEP_MAX_OPS], over: [ANSWER(true), 1, PLAN_SWEEP_MAX_OPS],
        second: [ANSWER(true), [plan(SECOND_DEVICE, 1)[0]], PLAN_SWEEP_MAX_OPS] });
  });

  it("the shipped ROUTES['/account'] sweeps env.PLANS across pages", async () => {
    await seed();
    await unbind();
    const kv = sweepKv(HOLDING);
    const req = new Request("https://scenic-api.test/account", { method: "DELETE", headers: { authorization: `Bearer ${await sessionToken({})}` } });
    const shipped = { ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET, PLANS: kv as unknown as KVNamespace };
    const response = await ROUTES["/account"]!(req, shipped, new URL(req.url));
    expect({ status: response.status, json: await response.json(), post: contents(kv) })
      .toEqual({ ...ANSWER(false), post: minus(HOLDING, (k) => userKey([DEVICE]).test(k)) });
  });
});
