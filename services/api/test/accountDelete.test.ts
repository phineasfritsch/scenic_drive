/**
 * T-0287 R7, R9 (P-PRIV-04): DELETE /account. The tables are ENUMERATED from the shipped migrations' CREATE TABLE
 * statements and must equal this file's whitelist - each either user-keyed (a predicate naming the user's rows) or
 * not (a reason) - so a table added later without a delete fails here by name. After a deletion every user row of
 * every table is gone and every other row is unchanged, compared WHOLE; the Apple revocations are recorded WHOLE;
 * revoke_pending in each arm; a repeat is 200 with nothing left; the shipped ROUTES answer 401/405/503.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ROUTES, type Env } from "../src/index";
import {
  ACCOUNT, allTables, APPLE_USER, CLIENT_SECRET, deleteAccount, DEVICE, fakeAppleFetch, freshAllTables, migrationTables, NOW, OTHER_ACCOUNT,
  OTHER_APPLE_USER, OTHER_DEVICE, revokeCall, SECOND_DEVICE, SECRET, sessionToken, siwaDeps, type FakeApple,
} from "./siwaHarness";

type R = Record<string, unknown>;
interface User { devices: string[]; keys: string[]; act: string | null }

/** Every migration table: how a row belongs to the user, or why no row can. */
const TABLES: Record<string, ((row: R, user: User) => boolean) | string> = {
  places: "no user column: (id, lat, lon), a resolved place the server answers to anyone",
  entitlements: (r, u) => u.act !== null && r.app_account_token === u.act,
  attest_challenges: "no user column: (challenge, expires_at), single-use and live 300 s",
  attested_keys: (r, u) => u.devices.includes(r.device_id as string),
  attest_sign_counts: (r, u) => u.keys.includes(r.key_id as string),
  attest_challenge_counts: (r, u) => u.devices.map((d) => `device:${d}`).includes(r.bucket as string),
  apple_accounts: (r, u) => u.devices.includes(r.device_id as string),
  waitlist: "no user column: (cell, count, updated_at), an H3-5 cell's count and the UTC day it last moved",
  waitlist_seen: "no user column: (tag, day), a tag is HMAC under a never-stored daily key of device and cell, purged at the next UTC day (T-0296 R4)",
  surprise_ledger: (r, u) => u.devices.includes(r.user_id as string),
  trip_places: "no user column: (id, name, kind, score, lat, lon), a corpus stop or lodging the server answers to anyone (T-0316)",
};

async function seed(): Promise<void> {
  const run = (sql: string, ...v: unknown[]) => env.DB.prepare(sql).bind(...v).run();
  await run("INSERT INTO apple_accounts VALUES (?1, ?2, 'r.1', 1), (?3, ?2, 'r.2', 2), (?4, ?5, 'r.3', 3)", DEVICE, APPLE_USER, SECOND_DEVICE, OTHER_DEVICE, OTHER_APPLE_USER);
  await run("INSERT INTO attested_keys VALUES ('kd', ?1, '04', 'production', 1), ('ks', ?2, '04', 'production', 2), ('ko', ?3, '04', 'production', 3)", DEVICE, SECOND_DEVICE, OTHER_DEVICE);
  await run("INSERT INTO attest_sign_counts VALUES ('kd', 5), ('ks', 6), ('ko', 7)");
  await run("INSERT INTO attest_challenge_counts VALUES (?1, 0, 1), (?2, 0, 1), (?3, 0, 1), ('global', 0, 3)", `device:${DEVICE}`, `device:${SECOND_DEVICE}`, `device:${OTHER_DEVICE}`);
  await run(`INSERT INTO entitlements VALUES ('t1', ?1, 'Production', 'p', 'active', NULL, 'SUBSCRIBED', NULL, 1),
    ('t2', ?2, 'Production', 'p', 'active', NULL, 'SUBSCRIBED', NULL, 1), ('t3', NULL, 'Sandbox', 'p', 'inactive', NULL, 'EXPIRED', NULL, 1)`, ACCOUNT, OTHER_ACCOUNT);
  await run("INSERT INTO places VALUES ('p1', 34.1, -118.5)");
  await run("INSERT INTO attest_challenges VALUES ('c1', ?1)", NOW + 1000);
  await run(`INSERT INTO surprise_ledger VALUES (?1, '101', '85283473fffffff', '2026-10-05'), (?2, '101', '85283473fffffff', '2026-10-05'),
    (?2, '202', '850dab63fffffff', '2026-10-04'), (?3, '101', '850dab63fffffff', '2026-10-05')`, DEVICE, SECOND_DEVICE, OTHER_DEVICE);
}

function userOf(pre: Record<string, unknown[]>, devices: string[], act: string | null): User {
  const keys = (pre.attested_keys as R[]).filter((r) => devices.includes(r.device_id as string)).map((r) => r.key_id as string);
  return { devices, keys, act };
}

/** The pre-state with the user's rows removed, table by table. */
function without(pre: Record<string, unknown[]>, user: User): Record<string, unknown[]> {
  return Object.fromEntries(Object.entries(pre).map(([t, rows]) => {
    const rule = TABLES[t];
    return [t, typeof rule === "function" ? (rows as R[]).filter((r) => !rule(r, user)) : rows];
  }));
}

async function deletion(session: R, o: { secret?: boolean; spec?: FakeApple; before?: () => Promise<unknown> } = {}) {
  await seed();
  if (o.before) await o.before();
  const pre = await allTables();
  const apple = fakeAppleFetch([], o.spec ?? {});
  const got = await deleteAccount(siwaDeps(apple.fetchImpl, o.secret === false ? {} : { APPLE_CLIENT_SECRET: CLIENT_SECRET }), await sessionToken(session));
  return { pre, got, post: await allTables(), calls: apple.calls };
}

const DONE = (pending: boolean) => ({ status: 200, json: { deleted: true, revoke_pending: pending, plans_pending: false } });
const FULL = { act: ACCOUNT, apple: APPLE_USER };

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAllTables();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("DELETE /account deletes every user row of every D1 table (R7, P-PRIV-04)", () => {
  it("every table the migrations create is in the deletion whitelist: a new table without a delete fails here by name", () => {
    expect(migrationTables().sort()).toEqual(Object.keys(TABLES).sort());
  });

  it("every user row is gone and every other row is unchanged; both refresh tokens revoked", async () => {
    const r = await deletion(FULL);
    const user = userOf(r.pre, [DEVICE, SECOND_DEVICE], ACCOUNT);
    const userRows = Object.fromEntries(Object.entries(r.pre).filter(([t]) => typeof TABLES[t] === "function")
      .map(([t, rows]) => [t, (rows as R[]).filter((row) => (TABLES[t] as (x: R, u: User) => boolean)(row, user)).length > 0]));
    expect({ userRows, got: r.got, post: r.post, calls: r.calls }).toEqual({
      userRows: Object.fromEntries(Object.keys(userRows).map((t) => [t, true])),
      got: DONE(false), post: without(r.pre, user), calls: [revokeCall("r.1"), revokeCall("r.2")],
    });
  });

  it("a session without the apple claim finds the user through the device's binding", async () => {
    const r = await deletion({ act: ACCOUNT });
    expect({ got: r.got, post: r.post, calls: r.calls }).toEqual({ got: DONE(false), post: without(r.pre, userOf(r.pre, [DEVICE, SECOND_DEVICE], ACCOUNT)), calls: [revokeCall("r.1"), revokeCall("r.2")] });
  });

  it("a session whose device is unbound deletes the apple claim's other devices", async () => {
    const r = await deletion(FULL, { before: () => env.DB.prepare("DELETE FROM apple_accounts WHERE device_id = ?1").bind(DEVICE).run() });
    expect({ got: r.got, post: r.post, calls: r.calls }).toEqual({ got: DONE(false), post: without(r.pre, userOf(r.pre, [DEVICE, SECOND_DEVICE], ACCOUNT)), calls: [revokeCall("r.2")] });
  });

  it("a device never bound and a session without apple or act: only the device's rows go, nothing to revoke", async () => {
    const r = await deletion({}, { before: () => env.DB.prepare("DELETE FROM apple_accounts WHERE device_id = ?1").bind(DEVICE).run() });
    expect({ got: r.got, post: r.post, calls: r.calls }).toEqual({ got: DONE(false), post: without(r.pre, userOf(r.pre, [DEVICE], null)), calls: [] });
  });

  const PENDING: [string, Parameters<typeof deletion>[1], string[]][] = [
    ["no client secret: no revoke call", { secret: false }, []],
    ["Apple refuses one revocation", { spec: { revoke: (t) => new Response("", { status: t === "r.2" ? 400 : 200 }) } }, ["r.1", "r.2"]],
    ["one revocation throws; the next is still made", { spec: { revoke: (t) => { if (t === "r.1") throw new Error("offline"); return new Response("", { status: 200 }); } } }, ["r.1", "r.2"]],
    ["a binding stored no refresh token", { before: () => env.DB.prepare("UPDATE apple_accounts SET refresh_token = NULL WHERE device_id = ?1").bind(SECOND_DEVICE).run() }, ["r.1"]],
  ];
  for (const [name, o, revoked] of PENDING) {
    it(`deletion completes and says revoke_pending: ${name}`, async () => {
      const r = await deletion(FULL, o);
      expect({ got: r.got, post: r.post, calls: r.calls }).toEqual({ got: DONE(true), post: without(r.pre, userOf(r.pre, [DEVICE, SECOND_DEVICE], ACCOUNT)), calls: revoked.map(revokeCall) });
    });
  }

  it("a repeat is idempotent: 200, nothing left to delete, no Apple call", async () => {
    const first = await deletion(FULL);
    const apple = fakeAppleFetch([]);
    const again = await deleteAccount(siwaDeps(apple.fetchImpl, { APPLE_CLIENT_SECRET: CLIENT_SECRET }), await sessionToken(FULL));
    expect({ first: first.got, again, post: await allTables(), calls: apple.calls }).toEqual({ first: DONE(false), again: DONE(false), post: first.post, calls: [] });
  });

  it("without a session JWT: 401, nothing deleted, no Apple call", async () => {
    await seed();
    const pre = await allTables();
    const apple = fakeAppleFetch([]);
    const got = await deleteAccount(siwaDeps(apple.fetchImpl, { APPLE_CLIENT_SECRET: CLIENT_SECRET }), null);
    expect({ got, post: await allTables(), calls: apple.calls }).toEqual({ got: { status: 401, json: { error: "unauthorized" } }, post: pre, calls: [] });
  });

  it("a POST is 405 and deletes nothing", async () => {
    await seed();
    const pre = await allTables();
    const got = await deleteAccount(siwaDeps(fakeAppleFetch([]).fetchImpl), await sessionToken(FULL), "POST");
    expect({ got, post: await allTables() }).toEqual({ got: { status: 405, json: { error: "DELETE only" } }, post: pre });
  });
});

describe("the shipped ROUTES['/auth/apple'] and ROUTES['/account'] (R1, R9)", () => {
  async function route(path: string, e: Partial<Env>, init: RequestInit) {
    const req = new Request(`https://scenic-api.test${path}`, init);
    const response = await ROUTES[path]!(req, { ...(env as unknown as Env), ...e }, new URL(req.url));
    return { status: response.status, json: (await response.json()) as unknown };
  }

  it("without SESSION_JWT_SECRET both are 503 auth_unavailable; without a Bearer both are 401", async () => {
    await seed();
    const pre = await allTables();
    const bearer = { authorization: `Bearer ${await sessionToken(FULL)}` };
    expect([
      await route("/auth/apple", {}, { method: "POST", headers: bearer, body: "{}" }),
      await route("/account", {}, { method: "DELETE", headers: bearer }),
      await route("/auth/apple", { SESSION_JWT_SECRET: SECRET }, { method: "POST", body: "{}" }),
      await route("/account", { SESSION_JWT_SECRET: SECRET }, { method: "DELETE" }),
      await allTables(),
    ]).toEqual([
      { status: 503, json: { error: "auth_unavailable" } }, { status: 503, json: { error: "auth_unavailable" } },
      { status: 401, json: { error: "unauthorized" } }, { status: 401, json: { error: "unauthorized" } }, pre,
    ]);
  });

  it("the shipped /account deletes an unbound device's rows with no Apple call", async () => {
    await seed();
    await env.DB.prepare("DELETE FROM apple_accounts WHERE device_id = ?1").bind(DEVICE).run();
    const pre = await allTables();
    const got = await route("/account", { SESSION_JWT_SECRET: SECRET }, { method: "DELETE", headers: { authorization: `Bearer ${await sessionToken({ act: ACCOUNT })}` } });
    expect({ got, post: await allTables() }).toEqual({ got: DONE(false), post: without(pre, userOf(pre, [DEVICE], ACCOUNT)) });
  });
});
