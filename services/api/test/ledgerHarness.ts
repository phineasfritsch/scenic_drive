/**
 * T-0302: the shared rig of the /ledger tests - the shipped worker.fetch over the test D1 with every migration applied,
 * a session JWT per caller, the whole surprise_ledger table read back, and the model the answers are compared to by
 * full equality (R4, R5). The model's window is computed by calendar arithmetic (setUTCDate), not the handler's
 * millisecond subtraction. Not a test file.
 */
import { env } from "cloudflare:test";
import worker, { type Env } from "../src/index";
import { signSession } from "../src/sessionJwt";
import type { FakeQuota } from "./doFake";
import ledgerSql from "../migrations/0008_surprise_ledger.sql?raw";

export const SECRET = "t0302-ledger-test-secret-0123456789abcdef";
export const USER_A = "1c2d3e4f-5a6b-4c7d-8e9f-0a1b2c3d4e5f";
export const USER_B = "6f5e4d3c-2b1a-4f0e-9d8c-7b6a5f4e3d2c";
// Published uber/h3 resolution-5 cells (the waitlist tests' own).
export const CELL = "85283473fffffff";
export const OTHER = "850dab63fffffff";
/** The largest corpus place id: segid.py place_id masks fnv1a64 to 63 bits. */
export const MAX_PLACE = "9223372036854775807";
export const WINDOW_DAYS = 90;

export interface LedgerRow { user_id: string; place_id: string; cell: string; day: string }
export interface Answer { status: number; json: unknown }
export type Op = { method: "GET" } | { method: "POST"; body: { place_id: string; cell: string } };

export const row = (user_id: string, place_id: string, cell: string, day: string): LedgerRow => ({ user_id, place_id, cell, day });
const key = (r: LedgerRow) => [r.user_id, r.place_id, r.day, r.cell].join("|");
export const sortRows = (rows: LedgerRow[]) => [...rows].sort((a, b) => (key(a) < key(b) ? -1 : key(a) > key(b) ? 1 : 0));

/** The shipped 0008 migration, then exactly `rows` in surprise_ledger (one batch: the tables run on a contended box). */
export async function seed(rows: LedgerRow[]): Promise<void> {
  for (const statement of ledgerSql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  await env.DB.batch([env.DB.prepare("DELETE FROM surprise_ledger"), ...rows.map((r) =>
    env.DB.prepare("INSERT INTO surprise_ledger (user_id, place_id, cell, day) VALUES (?1, ?2, ?3, ?4)").bind(r.user_id, r.place_id, r.cell, r.day))]);
}

export async function ledgerTable(): Promise<LedgerRow[]> {
  return sortRows((await env.DB.prepare("SELECT * FROM surprise_ledger").all<LedgerRow>()).results);
}

export const shippedEnv = (quota: FakeQuota, extra: Record<string, unknown> = {}) =>
  ({ DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, SESSION_JWT_SECRET: SECRET, ...extra }) as unknown as Env;

export async function bearer(user: string, secret = SECRET, nowMs = Date.now()): Promise<Record<string, string>> {
  return { authorization: `Bearer ${(await signSession(secret, { sub: user }, nowMs)).token}` };
}

export async function send(method: string, body: string | null, e: Env, headers: Record<string, string>): Promise<Answer> {
  const init: RequestInit = { method, headers: { "content-type": "application/json", ...headers } };
  if (body !== null) init.body = body;
  const response = await worker.fetch(new Request("https://scenic-api.test/ledger", init), e);
  return { status: response.status, json: (await response.json()) as unknown };
}

/** One op as `user`, through the shipped worker. */
export async function apply(op: Op, user: string, e: Env): Promise<Answer> {
  return send(op.method, op.method === "POST" ? JSON.stringify(op.body) : null, e, await bearer(user));
}

/** The window's first UTC day: `now`'s UTC day less WINDOW_DAYS calendar days. */
export function windowFirst(now: Date): string {
  const day = new Date(`${now.toISOString().slice(0, 10)}T00:00:00.000Z`);
  day.setUTCDate(day.getUTCDate() - WINDOW_DAYS);
  return day.toISOString().slice(0, 10);
}

const newestFirst = (a: LedgerRow, b: LedgerRow) =>
  a.day !== b.day ? (a.day < b.day ? 1 : -1) : a.place_id < b.place_id ? -1 : a.place_id > b.place_id ? 1 : 0;

/** R4/R5's model: the answers `user`'s ops get at `now` from `pre`, and the whole table after. */
export function model(pre: LedgerRow[], user: string, ops: Op[], now: Date): { answers: Answer[]; table: LedgerRow[] } {
  const today = now.toISOString().slice(0, 10);
  const first = windowFirst(now);
  let table = [...pre];
  const answers: Answer[] = [];
  for (const op of ops) {
    if (op.method === "GET") {
      const places = table.filter((r) => r.user_id === user && r.day >= first).sort(newestFirst)
        .map(({ place_id, cell, day }) => ({ place_id, cell, day }));
      answers.push({ status: 200, json: { places } });
      continue;
    }
    table = table.filter((r) => r.day >= first);
    if (!table.some((r) => r.user_id === user && r.place_id === op.body.place_id && r.day === today)) {
      table.push(row(user, op.body.place_id, op.body.cell, today));
    }
    answers.push({ status: 200, json: { recorded: true } });
  }
  return { answers, table: sortRows(table) };
}
