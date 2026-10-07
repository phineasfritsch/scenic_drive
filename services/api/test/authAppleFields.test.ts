/**
 * T-0287 rv1 B1, rv2 B1 (P-PRIV-04): the identity token's fields as ONE generated table through the shipped
 * ROUTES['/auth/apple']. Every header field (alg, kid, typ and an extra key) and every payload claim the verifier reads
 * (iss, aud, nonce, sub, exp, iat and an extra key) crossed with every VARIANT, each a function of the field's RIGHT
 * value. Every near-miss variant names the one OPERATION - the closed list of loosenings a compare can apply - that would
 * take it for the right value; the rest are type defects. A row is refused with every table WHOLE and the Apple calls
 * WHOLE over both table seeds, unless ACCEPTED names it with a reason - then it binds the sub it carries, tables WHOLE.
 * The field lists are checked against the verifier's own HEADER_KEYS and its destructured claims, every field x variant
 * is a row or a named no-op, and every field x operation is a row or a named no-op.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { PRODUCTION_JWKS } from "../src/account";
import { ROUTES, type Env } from "../src/index";
import {
  ACCOUNT, allTables, APPLE_USER, AUTH_CODE, BUNDLE, DEVICE, fakeAppleFetch, freshAllTables, grantedSession, identityClaims, ISSUER,
  keysCall, NOW, OTHER_APPLE_USER, rsaKey, S, SECRET, sessionToken, sha256Hex, signJws, type TestKey,
} from "./siwaHarness";

const SOURCE = Object.values(import.meta.glob("../src/appleIdentity.ts", { query: "?raw", import: "default", eager: true }))[0] as string;
const REFUSED = { status: 400, json: { error: "invalid_identity_token" } };
let K1: TestKey;

beforeAll(async () => {
  K1 = await rsaKey("K1");
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAllTables();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const SEEDS: [string, () => Promise<void>][] = [
  ["empty tables", async () => {}],
  ["the device already bound, keyed and entitled", async () => {
    await env.DB.prepare("INSERT INTO apple_accounts VALUES (?1, ?2, ?3, ?4)").bind(DEVICE, OTHER_APPLE_USER, "r.old", NOW - 1000).run();
    await env.DB.prepare("INSERT INTO attested_keys VALUES ('k', ?1, '04', 'production', 1)").bind(DEVICE).run();
    await env.DB.prepare("INSERT INTO entitlements VALUES ('t1', ?1, 'Production', 'p', 'active', NULL, 'SUBSCRIBED', NULL, 1)").bind(ACCOUNT).run();
  }],
];

type Right = string | number;
interface Field { part: "header" | "payload"; name: string; right: (bearer: string) => Promise<Right>; integer?: true }
const constant = (v: Right) => async () => v;
const FIELDS: Field[] = [
  { part: "header", name: "alg", right: constant("RS256") },
  { part: "header", name: "kid", right: constant("K1") },
  { part: "header", name: "typ", right: constant("JWT") },
  { part: "header", name: "extra", right: constant("value") },
  { part: "payload", name: "iss", right: constant(ISSUER) },
  { part: "payload", name: "aud", right: constant(BUNDLE) },
  { part: "payload", name: "nonce", right: (bearer) => sha256Hex(bearer) },
  { part: "payload", name: "sub", right: constant(APPLE_USER) },
  { part: "payload", name: "exp", right: constant(S + 600), integer: true },
  { part: "payload", name: "iat", right: constant(S), integer: true },
  { part: "payload", name: "extra", right: constant("value") },
];

/** rv2 B1: the closed list of loosenings a compare can apply before it compares, each as the lax compare it makes. */
const isText = (g: unknown): g is string => typeof g === "string";
const OPERATIONS = {
  "loose equality (==)": (g: unknown, r: Right) => (g as Right) == r,
  "Number() coercion": (g: unknown, r: Right) => typeof r === "number" && Number(g) === r,
  "trim()": (g: unknown, r: Right) => isText(g) && g.trim() === String(r),
  "zero-width strip": (g: unknown, r: Right) => isText(g) && g.replace(/[​-‍⁠]/g, "") === String(r),
  "normalize('NFKC')": (g: unknown, r: Right) => isText(g) && g.normalize("NFKC") === String(r),
  "case fold": (g: unknown, r: Right) => isText(g) && g.toLowerCase() === String(r).toLowerCase(),
  "substring match": (g: unknown, r: Right) => isText(g) && g !== "" && (g.includes(String(r)) || String(r).includes(g)),
  "NUL-terminated read": (g: unknown, r: Right) => isText(g) && g.split("\0")[0] === String(r),
};
type Operation = keyof typeof OPERATIONS;
/** A loosening no row can carry: JSON.parse yields only primitives, arrays and plain objects (the ruling test below). */
const NO_JSON_FORM: [string, string][] = [["a String object (new String(r))", "JSON hands back the primitive String(r)"]];

const swapCase = (s: string) => (s === s.toUpperCase() ? s.toLowerCase() : s.toUpperCase());
const pad = (before: string, after: string) => (r: Right) => `${before}${r}${after}`;
const numberText = (f: (n: number) => string) => (r: Right) => (typeof r === "number" ? f(r) : r);
const zeroWidthInside = (r: Right) => [...String(r)].map((c, i, all) => (i === Math.ceil(all.length / 2) ? `​${c}` : c)).join("");
const fullwidth = (r: Right) => String(r).replace(/[!-~]/g, (c) => String.fromCharCode(c.charCodeAt(0) + 0xfee0));
const VARIANTS: [string, (right: Right) => unknown, Operation | "a type defect"][] = [
  ["plus a suffix", (r) => (typeof r === "string" ? `${r}x` : `${r}0`), "substring match"],
  ["behind a prefix", pad("x", ""), "substring match"],
  ["less its last character", (r) => String(r).slice(0, -1), "substring match"],
  ["in changed case", (r) => swapCase(String(r)), "case fold"],
  ["a prefix of it", (r) => String(r).slice(0, Math.max(1, Math.floor(String(r).length / 2))), "substring match"],
  ["an array holding it", (r) => [r], "loose equality (==)"],
  ["its numeric string", numberText(String), "Number() coercion"],
  ["in exponent notation", numberText((n) => n.toExponential()), "Number() coercion"],
  ["a leading space", pad(" ", ""), "trim()"],
  ["a trailing space", pad("", " "), "trim()"],
  ["tab and newline padded", pad("\t", "\n"), "trim()"],
  ["NBSP padded", pad(" ", " "), "trim()"],
  ["other Unicode whitespace padded", pad(" ﻿", " 　"), "trim()"],
  ["a zero-width space inside", zeroWidthInside, "zero-width strip"],
  ["in fullwidth form", fullwidth, "normalize('NFKC')"],
  ["an embedded NUL before a tail", pad("", "\u0000tail"), "NUL-terminated read"],
  ["null", () => null, "a type defect"],
  ["a number", (r) => (typeof r === "string" ? r.length : r + 0.5), "a type defect"],
  ["a boolean", () => true, "a type defect"],
  ["an object holding it", (r) => ({ value: r }), "a type defect"],
  ["an empty string", () => "", "a type defect"],
  ["missing", () => undefined, "a type defect"],
];
/** Variants that carry no value of the field's: a type defect or an absence. */
const VALUE_FREE = ["null", "a boolean", "an empty string", "missing"];
const NAME = (f: Field, variant: string) => `${f.part} ${f.name}: ${variant}`;
const NUMBER_FORMS = VARIANTS.filter(([, , op]) => op === "Number() coercion").map(([v]) => v);
/** field x variant pairs that are no row, with the reason: the variant would hand the verifier the right value. */
const NOT_APPLICABLE: [string, string][] = FIELDS.flatMap((f): [string, string][] => (f.integer
  ? [[NAME(f, "in changed case"), "an integer's digits have no case"]]
  : NUMBER_FORMS.map((v): [string, string] => [NAME(f, v), "a string field has no number form: the variant is the right value"])));
/** Rows that bind, with the reason; every other row is refused. */
const ACCEPTED: [string, string][] = [
  ["header typ: missing", "typ is optional (R5)"],
  ["header extra: missing", "no extra key is the valid header itself"],
  ...["plus a suffix", "behind a prefix", "less its last character", "in changed case", "a prefix of it"].map((v): [string, string] =>
    [`payload sub: ${v}`, "another well-formed Apple user id binds as itself (APPLE_SUB)"]),
  ...VARIANTS.map(([v]) => `payload extra: ${v}`).filter((n) => !NOT_APPLICABLE.some(([na]) => na === n))
    .map((n): [string, string] => [n, "a claim the verifier does not read is allowed (R5)"]),
];

interface Row { name: string; field: Field; variant: string; make: (right: Right) => unknown; operation: Operation | "a type defect"; accepted: boolean }
const ROWS: Row[] = FIELDS.flatMap((field) => VARIANTS.filter(([v]) => !NOT_APPLICABLE.some(([n]) => n === NAME(field, v)))
  .map(([variant, make, operation]) => ({ name: NAME(field, variant), field, variant, make, operation,
    accepted: ACCEPTED.some(([n]) => n === NAME(field, variant)) })));

async function attempt(row: Row, seed: () => Promise<void>) {
  await freshAllTables();
  await seed();
  const before = await allTables();
  const bearer = await sessionToken();
  const value = row.make(await row.field.right(bearer));
  const header: Record<string, unknown> = { alg: "RS256", kid: "K1", typ: "JWT" };
  if (row.field.part === "header") header[row.field.name] = value;
  const claims = await identityClaims(bearer, row.field.part === "payload" ? { [row.field.name]: value } : {});
  const identityToken = await signJws(header, claims, K1.privateKey);
  PRODUCTION_JWKS.keys = null;
  PRODUCTION_JWKS.fetchedAtMs = 0;
  const apple = fakeAppleFetch([K1]);
  vi.stubGlobal("fetch", apple.fetchImpl);
  const req = new Request("https://scenic-api.test/auth/apple", { method: "POST", headers: { authorization: `Bearer ${bearer}` },
    body: JSON.stringify({ identityToken, authorizationCode: AUTH_CODE }) });
  const response = await ROUTES["/auth/apple"]!(req, { ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET }, new URL(req.url));
  const answer = { status: response.status, json: (await response.json()) as unknown };
  return { value, before, got: { answer, tables: await allTables(), calls: apple.calls } };
}

describe("every identity-token field x every variant through the shipped ROUTES['/auth/apple'] (R5, P-PRIV-04)", () => {
  for (const row of ROWS) {
    it(`${row.accepted ? "accepted" : "refused"}: ${row.name}`, async () => {
      for (const [seedName, seed] of SEEDS) {
        const { value, before, got } = await attempt(row, seed);
        if (row.accepted) {
          const sub = row.field.part === "payload" && row.field.name === "sub" ? value : APPLE_USER;
          expect({ seedName, ...got }).toEqual({ seedName, answer: await grantedSession({ apple: sub }), calls: [keysCall],
            tables: { ...before, apple_accounts: [{ device_id: DEVICE, apple_sub: sub, refresh_token: null, bound_at: NOW }] } });
        } else {
          const kidRead = row.field.part === "payload" || (row.field.name === "kid" && typeof value === "string" && value !== "");
          expect({ seedName, ...got }).toEqual({ seedName, answer: REFUSED, tables: before, calls: kidRead ? [keysCall] : [] });
        }
      }
    });
  }
});

describe("the field x variant table is whole (meta)", () => {
  const one = (re: RegExp) => {
    const all = [...SOURCE.matchAll(re)];
    expect(all.length).toBe(1);
    return all[0]![1]!.split(",").map((s) => s.trim().replace(/"/g, "")).sort();
  };
  it("the header fields are appleIdentity.ts's HEADER_KEYS and the claims its destructured reads, each plus an extra key", () => {
    const header = FIELDS.filter((f) => f.part === "header").map((f) => f.name).sort();
    const payload = FIELDS.filter((f) => f.part === "payload").map((f) => f.name).sort();
    expect({ header, payload }).toEqual({
      header: [...one(/const HEADER_KEYS = \[([^\]]*)\];/g), "extra"].sort(),
      payload: [...one(/const \{ ([^}]*) \} = claims;/g), "extra"].sort(),
    });
  });

  it("every field meets every variant: a row, or a named no-op whose variant hands back the right value", async () => {
    const missing: string[] = [];
    for (const field of FIELDS) {
      for (const [variant, make] of VARIANTS) {
        const name = NAME(field, variant);
        const rows = ROWS.filter((r) => r.name === name).length;
        const na = NOT_APPLICABLE.filter(([n]) => n === name).length;
        if (rows + na !== 1) missing.push(name);
        if (na === 1) expect(String(make(await field.right("b")))).toBe(String(await field.right("b")));
      }
    }
    expect({ missing, rows: ROWS.length }).toEqual({ missing: [], rows: FIELDS.length * VARIANTS.length - NOT_APPLICABLE.length });
  });

  it("every field meets every operation: rows its lax compare takes for the right value, or a named no-op", async () => {
    const bearer = await sessionToken();
    const seen: Record<string, string> = {};
    for (const field of FIELDS) {
      const right = await field.right(bearer);
      for (const op of Object.keys(OPERATIONS) as Operation[]) {
        const rows = ROWS.filter((r) => r.field === field && r.operation === op);
        const notTaken = rows.filter((r) => !OPERATIONS[op](r.make(right), right)).map((r) => r.variant);
        seen[NAME(field, op)] = rows.length === 0 ? "no-op" : notTaken.length === 0 ? "rows" : `not taken: ${notTaken.join()}`;
      }
    }
    const want = Object.fromEntries(FIELDS.flatMap((f) => (Object.keys(OPERATIONS) as Operation[]).map((op) =>
      [NAME(f, op), op === (f.integer ? "case fold" : "Number() coercion") ? "no-op" : "rows"])));
    expect(seen).toEqual(want);
  });

  it("a String object (new String(r)) is no row: JSON hands back the primitive String(r), the right value or its numeric string", async () => {
    const bearer = await sessionToken();
    const back = await Promise.all(FIELDS.map(async (f) => JSON.parse(JSON.stringify({ v: new String(await f.right(bearer)) })).v as unknown));
    const want = await Promise.all(FIELDS.map(async (f) => String(await f.right(bearer))));
    expect({ ruled: NO_JSON_FORM.map(([n]) => n), back }).toEqual({ ruled: ["a String object (new String(r))"], back: want });
  });

  it("every row's value differs from its field's right value", async () => {
    const same = [];
    for (const row of ROWS) {
      const right = await row.field.right(await sessionToken());
      if (JSON.stringify(row.make(right)) === JSON.stringify(right)) same.push(row.name);
    }
    expect(same).toEqual([]);
  });

  it("every variant but the value-free ones is a function of the right value", () => {
    const ignoring = VARIANTS.filter(([, make]) => JSON.stringify(make("ab")) === JSON.stringify(make("abcd"))
      || JSON.stringify(make(12)) === JSON.stringify(make(3456))).map(([v]) => v);
    expect(ignoring).toEqual(VALUE_FREE);
  });

  it("every ACCEPTED name is a row, and the refused rows are the rest", () => {
    expect(ACCEPTED.filter(([n]) => !ROWS.some((r) => r.name === n)).map(([n]) => n)).toEqual([]);
    expect(ROWS.filter((r) => r.accepted).length).toBe(ACCEPTED.length);
  });
});
