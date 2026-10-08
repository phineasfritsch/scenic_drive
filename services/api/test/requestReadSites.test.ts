/**
 * T-0272 (rv1 BLOCKING): a WHITELIST of every source line under services/api/src that names the request - the
 * identifier req or _req, the type Request - or reads a request member (.headers .url .json .text .formData
 * .arrayBuffer .blob .body .cf .method .signal .referrer .clone .bodyUsed, URL, searchParams). T-0288 S3: an unused
 * _req is a site, so a handler that starts reading it changes an approved line. The lines found are compared WHOLE
 * (trimmed) to the approved sites below, per
 * file, by full equality: a new site - a query-string fallback, a body read, another header name, a new file that
 * reads the request - is refused by its file and its line. FAIL-CLOSED (rv2): only lines that begin with two slashes
 * are skipped. A line that begins a block comment, closes one, or continues one is compared like code - a block
 * comment can open or close in front of code on the same line - so the JSDoc lines that name a request word are
 * approved sites below, by full equality, like every other line.
 * The tier module's ONLY request read is the one ACCOUNT_TOKEN_HEADER line. T-0278: the session JWT is read at ONE
 * site, routerDeps' identify, by AUTHORIZATION_HEADER; sessionIdentity.ts takes that string and reads no request.
 * T-0288 rv1 B1: a read THROUGH A VALUE DERIVED FROM THE REQUEST is a site too. A name bound (const/let/var, a
 * destructuring, or a statement-start reassignment) on a line that reads the request's url, headers, method, cf,
 * signal or referrer, its searchParams, pathname, search or hash - or that names an already-derived name - is
 * derived, to a fixpoint per file, and every line naming a derived name is a site compared whole like the rest: an
 * edit that gates on url, handler, token, raw or userId (or a new name taken from them) changes the approved lines.
 * NOT derived: values parsed from the BODY (the body read itself is the approved site of each POST route).
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob("../src/**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const SITE = /\b_?(req|Request)\b|\.(headers|url|json|text|formData|arrayBuffer|blob|body|cf|method|signal|referrer|clone|bodyUsed|pathname|search|hash)\b|\bURL\b|searchParams/;
const LINE_COMMENT = /^\/\//;
/** A line that derives a value from the request's metadata (never its body). */
const DERIVE = /\b_?req\.(url|headers|method|cf|signal|referrer)\b|\.searchParams\b|\.(pathname|search|hash)\b/;
/** The names a line binds: const/let/var X, a destructuring, or a statement-start (re)assignment X = / X.y = . */
const BOUND = /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)|\b(?:const|let|var)\s*[{[]([^}\]]*)[}\]]|^([A-Za-z_$][\w$]*)(?:\.[\w$]+|\[[^\]]*\])*\s*=(?![=>])/g;
const BLOCK_COMMENT = /^(\*|\/\*)/;
const named = (n: string) => new RegExp(`(^|[^\\w$])${n.replace(/\$/g, "\\$")}([^\\w$]|$)`);

const POST_ONLY = 'if (req.method !== "POST") return json({ error: "POST only" }, 405);';
const BODY_READ = "raw = await req.json();";
const CONFIG_ROUTE = '"/config": (_req, env) => handleConfig(env),';
const TIER_SIGNATURE = "export async function accountTier(req: Request, db: D1Database | undefined, nowMs: number): Promise<Tier> {";
const URL_LINE = "const url = new URL(req.url);";
const HANDLER_MISS = 'if (!handler) return json({ error: "not found" }, 404);';
const TIER_READ = 'const token = (req.headers.get(ACCOUNT_TOKEN_HEADER) ?? "").toLowerCase();';

const APPROVED: Record<string, string[]> = {
  // T-0287 R10: the session JWT's ONE read in account.ts is caller()'s; the Apple exchange's response is not the request.
  // T-0288 merge of T-0287: the rv1 B1 derivation follows match -> claims (session.claims) -> sub, act, signed, user ->
  // bindings -> binding through both handlers; every line naming one is the session the Authorization header carried.
  "../src/account.ts": [
    "* APPLE_CLIENT_SECRET, binds the Apple sub to the session's device and answers the session JWT re-signed with apple",
    "* of the user, then deletes every user row of every D1 table in one batch and answers {deleted, revoke_pending} (R7).",
    "/** Owner secret: the pre-signed Sign in with Apple client-secret JWT; absent, no exchange and revoke_pending. */",
    "async function caller(req: Request, secret: string, nowMs: number): Promise<{ token: string; claims: SessionClaims } | null> {",
    'const match = BEARER.exec(req.headers.get(AUTHORIZATION_HEADER) ?? "");',
    "if (match === null) return null;",
    "const claims = await verifySession(secret, match[1]!, nowMs);",
    "return claims === null ? null : { token: match[1]!, claims };",
    "const body: unknown = await response.json();",
    "export async function handleAuthApple(req: Request, deps: AccountDeps): Promise<Response> {",
    POST_ONLY,
    "const session = await caller(req, deps.secret, nowMs);",
    "const raw: unknown = await req.json();",
    "await bindApple(deps.db, session.claims.sub, appleSub, refreshToken, nowMs);",
    "const { sub, act } = session.claims;",
    "const signed = await signSession(deps.secret, act === undefined ? { sub, apple: appleSub } : { sub, act, apple: appleSub }, nowMs);",
    "return json({ token: signed.token, expires_at: new Date(signed.expiresAtMs).toISOString() });",
    "export async function handleDeleteAccount(req: Request, deps: AccountDeps): Promise<Response> {",
    'if (req.method !== "DELETE") return json({ error: "DELETE only" }, 405);',
    "const session = await caller(req, deps.secret, deps.now().getTime());",
    "const user: AccountUser = { deviceId: session.claims.sub, appleSub: session.claims.apple ?? null, accountToken: session.claims.act ?? null };",
    "let bindings;",
    "bindings = await userBindings(deps.db, user);",
    "for (const binding of bindings) {",
    "if (secret === null || binding.refreshToken === null || !(await revoked(deps, secret, binding.refreshToken))) pending = true;",
    "await deleteUser(deps.db, user);",
  ],
  "../src/accountTier.ts": [
    "* The caller's quota tier (T-0272 R1-R5): paid exactly when the purchase id in x-scenic-account-token has a live",
    "* anon: no header, a malformed one (no D1 read), an unknown token, an inactive or expired row, and ANY failure of",
    "* the read (fails closed on cost). Nothing here logs: the token is a bearer secret until App Attest + JWT (R5).",
    TIER_SIGNATURE,
    TIER_READ,
    'if (db === undefined || !UUID.test(token)) return "anon";',
    'return (await readEntitlement(db, token, nowMs)).status === "active" ? "paid" : "anon";',
  ],
  // T-0287: Apple's JWKS response, never the request.
  "../src/appleJwks.ts": ["body = await response.json();"],
  "../src/appleMaps.ts": [
    "* The Apple Maps handoff URL - a port of Sources/Handoff/AppleMapsDirections.swift (T-0248 R7).",
    "* decimals here is not the two-decimal rule: this URL is the user handing their own route to Apple.",
  ],
  "../src/asn.ts": [
    "* written. /entitlement answers the state for the purchase id the device names in x-scenic-account-token (R8).",
    'export const ACCOUNT_TOKEN_HEADER = "x-scenic-account-token";',
    "export async function handleAsn(req: Request, deps: AsnDeps): Promise<Response> {",
    POST_ONLY,
    "body = await req.json();",
    "export async function handleEntitlement(req: Request, deps: AsnDeps): Promise<Response> {",
    'if (req.method !== "GET") return json({ error: "GET only" }, 405);',
    TIER_READ,
    'if (!UUID.test(token)) return json({ error: "invalid_request" }, 400);',
    "return json(await readEntitlement(deps.db, token, deps.now().getTime()));",
  ],
  "../src/attest.ts": [
    "export async function handleAttestChallenge(req: Request, deps: AttestDeps): Promise<Response> {",
    POST_ONLY,
    "if (!(await issueChallenge(deps.db, challenge, deviceIdentity(req).userId, nowMs))) return LIMITED();",
    "export async function handleAttest(req: Request, deps: AttestDeps): Promise<Response> {",
    POST_ONLY,
    "const raw: unknown = await req.json();",
    "export async function handleAttestAssert(req: Request, deps: AttestDeps): Promise<Response> {",
    POST_ONLY,
    "const raw: unknown = await req.json();",
  ],
  // T-0276: the closures cron reads the Caltrans FEED's response, never the request; the feed URL ends in .json.
  "../src/closuresCron.ts": [
    'const lastModified = Date.parse(response.headers.get("last-modified") ?? "");',
    "feed = await response.json();",
  ],
  "../src/customModel.ts": [
    "*      car_scenic_base.json on the server and are not restated here, because a per-request model that",
  ],
  "../src/hazards.ts": [
    "* car_scenic_base.json and keep those edges off the route; what can still be on it - a compacted shoulder the",
  ],
  "../src/index.ts": [
    'IDENTITY_HEADERS?: string; // "1" = the bare x-scenic-device / x-scenic-account-token migration window (T-0278 R6)',
    "type Handler = (req: Request, env: Env, url: URL) => Promise<Response>;",
    "const health: Handler = async (_req, env) => {",
    "const version: Handler = async (_req, env) =>",
    "/** Read-only SQL for ops/prod-read. Bearer token + grammar allowlist; never more than 200 rows. */",
    "const ro: Handler = async (req, env) => {",
    POST_ONLY,
    'const token = req.headers.get("authorization")?.replace(/^Bearer\\s+/i, "") ?? "";',
    'if (!env.RO_TOKEN || token.length === 0 || token !== env.RO_TOKEN) return json({ error: "unauthorized" }, 401);',
    'sql = String(((await req.json()) as { sql?: unknown }).sql ?? "");',
    '"/plan": (req, env) => handlePlan(req, env, planDepsFromEnv(env)),',
    '"/loop": (req, env) => handleLoop(req, env, loopDepsFromEnv(env)),',
    '"/isochrone": (req, env) => handleIsochrone(req, env, isochroneDepsFromEnv(env)),',
    '"/trip": (req, env) => handleTrip(req, env, tripDepsFromEnv(env)),',
    '"/asn": (req, env) => handleAsn(req, asnDepsFromEnv(env)),',
    '"/entitlement": (req, env) => handleEntitlement(req, asnDepsFromEnv(env)),',
    '"/attest/challenge": (req, env) => handleAttestChallenge(req, attestDepsFromEnv(env)),',
    '"/attest": (req, env) => handleAttest(req, attestDepsFromEnv(env)),',
    '"/attest/assert": (req, env) => handleAttestAssert(req, attestDepsFromEnv(env)),',
    '"/telemetry": (req, env) => handleTelemetry(req, env, telemetryDepsFromEnv(env)),',
    CONFIG_ROUTE,
    '"/auth/apple": (req, env) => handleAuthApple(req, accountDepsFromEnv(env)),',
    '"/account": (req, env) => handleDeleteAccount(req, accountDepsFromEnv(env)),',
    '"/waitlist": (req, env) => handleWaitlist(req, waitlistDepsFromEnv(env)),',
    '"/ledger": (req, env) => handleLedger(req, ledgerDepsFromEnv(env)),',
    "async fetch(req: Request, env: Env): Promise<Response> {",
    URL_LINE,
    'const handler = ROUTES[url.pathname.length > 1 && url.pathname.endsWith("/") ? url.pathname.slice(0, -1) : url.pathname];',
    HANDLER_MISS,
    "return handler(req, Object.freeze({ ...env, KILL_SWITCH: killSwitchReader(env.KILL_SWITCH) }), url);",
    "ctx.waitUntil(runClosuresCron({ fetchImpl: (url) => fetch(url), kv: env.CLOSURES, now: () => new Date() }));",
  ],
  "../src/isochrone.ts": [
    "export async function handleIsochrone(req: Request, env: KillEnv, deps: IsochroneDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    'const buckets = await guardedPlan(deps.upstream, { ...(await deps.identify(req)), kind: "surprise" }, (call) =>',
  ],
  // T-0302 R1: the ledger user is the verified session's sub, read at ONE site (caller) by AUTHORIZATION_HEADER.
  "../src/ledger.ts": [
    "async function caller(req: Request, secret: string, nowMs: number): Promise<string | null> {",
    'const match = BEARER.exec(req.headers.get(AUTHORIZATION_HEADER) ?? "");',
    "return match === null ? null : ((await verifySession(secret, match[1]!, nowMs))?.sub ?? null);",
    "export async function handleLedger(req: Request, deps: LedgerDeps): Promise<Response> {",
    'if (req.method !== "GET" && req.method !== "POST") return json({ error: "GET or POST only" }, 405);',
    "const user = await caller(req, deps.secret, now.getTime());",
    'if (req.method === "GET") return readLedger(deps.db, user, first);',
    BODY_READ,
  ],
  "../src/isochronePlanner.ts": ["answer = await response.json();"],
  "../src/lcsFeed.ts": ['export const LCS_D7_FEED = "https://cwwp2.dot.ca.gov/data/d7/lcs/lcsStatusD07.json";'],
  "../src/loop.ts": [
    "identify(req: Request): Identity | Promise<Identity>;",
    "export async function handleLoop(req: Request, env: PlanEnv, deps: LoopDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const who = await deps.identify(req);",
  ],
  "../src/loopPlanner.ts": ["const path = decodeRoutePath(await response.text());"],
  "../src/plan.ts": [
    "identify(req: Request): Identity | Promise<Identity>;",
    "export async function handlePlan(req: Request, env: PlanEnv, deps: PlanDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const who = await deps.identify(req);",
  ],
  "../src/reachCache.ts": ["return hit ? ((await hit.json()) as ReachBucket[]) : null;"],
  "../src/retrace.ts": ["* (Tests/Fixtures/t0252/loops.json) holds the TS fraction and the Swift fraction to the same IEEE-754 bits."],
  "../src/ro.ts": ["* Mirrored in ops/lib/ro_grammar.py. Both run every case in ops/lib/ro_cases.json and both assert their"],
  "../src/roadTrip.ts": [
    "* the Worker feeds it milliseconds and whole metres. Held to the Swift original by Tests/Fixtures/t0268/trips.json.",
  ],
  "../src/routerDeps.ts": [
    "identify(req: Request): Promise<Identity>;",
    "let url: URL;",
    "url = new URL(value);",
    "export function deviceIdentity(req: Request): { userId: string; tier: Tier } {",
    'const raw = (req.headers.get(DEVICE_HEADER) ?? "").toLowerCase();',
    'return { userId: DEVICE_ID.test(raw) ? raw : UNIDENTIFIED_DEVICE, tier: "anon" };',
    "const headers = new Headers(init?.headers);",
    "identify: (req) => identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now().getTime(), async () => {",
    "const device = deviceIdentity(req);",
    'return (await accountTier(req, env.DB, now().getTime())) === "paid" ? { ...device, tier: "paid" } : device;',
  ],
  "../src/scenicPlanner.ts": ["const path = decodeRoutePath(await response.text());"],
  "../src/trip.ts": [
    "export async function handleTrip(req: Request, env: PlanEnv, deps: TripDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const who = await deps.identify(req);",
  ],
  // T-0293 R2: the served region is the region files themselves, bundled at build time; the request is never read.
  "../src/servedRegion.ts": [
    'import la from "../../etl/regions/la/region.json";',
    'import sfbay from "../../etl/regions/sfbay/region.json";',
  ],
  "../src/telemetry.ts": [
    "*   2. The body against the whitelist (telemetryPoint.ts, P-PRIV-05) -> 400. Nothing reserved, nothing written.",
    "export async function handleTelemetry(req: Request, env: KillEnv & SessionEnv, deps: TelemetryDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const { userId } = await identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now.getTime(), async () => deviceIdentity(req));",
    "const counter = deps.quota.get(deps.quota.idFromName(`device:${userId}`));",
    "let reserved: boolean;",
    'reserved = await counter.reserveDaily(dayKey(now), "telemetry", DAILY_TELEMETRY_QUOTA, parsed.points.length);',
    'if (!reserved) return json({ error: "quota_exhausted", resets_at: nextReset(now) }, 429);',
  ],
  "../src/tripPlanner.ts": ["const path = decodeRoutePath(await response.text());"],
  "../src/waitlist.ts": [
    // T-0296 R1: the waitlist dedupe is bound to identifyCaller's bucket, the quota's and /telemetry's identity.
    "identify(req: Request): Promise<string>;",
    "identify: async (req) =>",
    "(await identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now().getTime(), async () => deviceIdentity(req))).userId,",
    "export async function handleWaitlist(req: Request, deps: WaitlistDeps): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const tag = await dedupeTag(deps.secret, await deps.identify(req), parsed.cell, day);",
  ],
  "../src/upstream.ts": ["return guardedPlan(deps, { userId: args.userId, tier: args.tier }, (call) => call(args.url, args.init));"],
};

/** The names `line` binds. */
function bound(line: string): string[] {
  const out: string[] = [];
  for (const m of line.matchAll(BOUND)) out.push(...[m[1], m[3]].filter((n): n is string => !!n), ...(m[2]?.match(/[A-Za-z_$][\w$]*/g) ?? []));
  return out;
}

/** The names derived from the request in one file's lines, to a fixpoint. */
function derived(lines: string[]): string[] {
  const names = new Set<string>();
  for (let size = -1; size !== names.size;) {
    size = names.size;
    const words = [...names].map(named);
    for (const l of lines) if (!BLOCK_COMMENT.test(l) && (DERIVE.test(l) || words.some((w) => w.test(l)))) bound(l).forEach((n) => names.add(n));
  }
  return [...names];
}

/** Every line (bar a //-leading one) of every src file that names the request, reads a request member or names a value
 * derived from the request, trimmed, in order. `derive: false` is the pre-rv1 guard, kept only to show it blind. */
function sites(src: Record<string, string>, derive = true): Record<string, string[]> {
  const found: Record<string, string[]> = {};
  for (const [file, text] of Object.entries(src).sort(([a], [b]) => a.localeCompare(b))) {
    const code = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => !LINE_COMMENT.test(l));
    const words = derive ? derived(code).map(named) : [];
    const lines = code.filter((l) => SITE.test(l) || words.some((w) => w.test(l)));
    if (lines.length > 0) found[file] = lines;
  }
  return found;
}

describe("every line under src that reads the request is an approved site (T-0272 rv1, whitelist)", () => {
  it("the glob sees the src tree (a guard over no files is vacuous)", () => {
    expect(Object.keys(SRC).length).toBeGreaterThanOrEqual(30);
    expect(Object.keys(SRC)).toContain("../src/accountTier.ts");
  });

  it("the request sites under src are exactly the approved sites, file by file, line by line", () => {
    expect(sites(SRC)).toEqual(APPROVED);
  });

  it("the tier module reads the request once: the ACCOUNT_TOKEN_HEADER line", () => {
    const tier = sites(SRC)["../src/accountTier.ts"] ?? [];
    expect(tier.filter((l) => /\breq\b/.test(l))).toEqual([TIER_SIGNATURE, TIER_READ]);
    expect(derived(SRC["../src/accountTier.ts"]!.split(/\r?\n/).map((l) => l.trim()))).toEqual(["token"]);
  });

  it("src/config.ts reads no request: GET /config answers from env alone (T-0288 R7)", () => {
    expect(Object.keys(SRC)).toContain("../src/config.ts");
    expect(Object.keys(sites(SRC)).filter((f) => f === "../src/config.ts")).toEqual([]);
  });

  it("a method, signal or clone read through the unused _req of /config is refused by its line (T-0288 S3, seen red)", () => {
    const index = SRC["../src/index.ts"]!;
    const reads = [
      '"/config": (_req, env) => handleConfig(_req.method === "DELETE" ? { ...env, KILL: undefined, KILL_SWITCH: undefined } : env),',
      '"/config": (r, env) => handleConfig(r.method === "OPTIONS" ? { ...env, KILL: undefined } : env),',
      '"/config": (r, env) => handleConfig(r.signal.aborted ? { ...env, KILL: undefined } : env),',
      '"/config": (r, env) => handleConfig(r.referrer === "" ? env : { ...env, KILL: undefined }),',
      '"/config": (r, env) => handleConfig(r.clone().bodyUsed ? env : env),',
    ];
    for (const read of reads) {
      const mutated = { ...SRC, "../src/index.ts": index.replace(CONFIG_ROUTE, read) };
      const found = sites(mutated)["../src/index.ts"]!;
      expect([found.includes(CONFIG_ROUTE), found.filter((l) => !APPROVED["../src/index.ts"]!.includes(l))]).toEqual([false, [read]]);
    }
  });

  it("a read through a value derived from the request in worker.fetch is refused by its line (T-0288 rv1 B1, seen red)", () => {
    const index = SRC["../src/index.ts"]!;
    const rv1 = 'if (url.pathname === "/config" && url.search !== "") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };';
    const reads: [string, string[]][] = [
      ["rv1-derived-url", [rv1]],
      ["derived-handler-port", ['if (handler === ROUTES["/config"] && url.port === "") env = { ...env, KILL: undefined };']],
      ["derived-port-name", ["const p = url.port;", 'if (p === "") env = { ...env, KILL: undefined };']],
      ["derived-headers-obj", ["const h = req.headers;", 'if (h.has("x-scenic-unpause")) env = { ...env, KILL: undefined };']],
      ["derived-method", ["const m = req.method;", 'if (m === "OPTIONS") env = { ...env, KILL: undefined };']],
      ["derived-search-params", ["const q = url.searchParams;", "if (q.size > 0) env = { ...env, KILL_SWITCH: undefined };"]],
    ];
    const got = reads.map(([name, lines]) => {
      const mutated = { ...SRC, "../src/index.ts": index.replace(HANDLER_MISS, [HANDLER_MISS, ...lines].join("\n    ")) };
      const extra = (s: Record<string, string[]>) => s["../src/index.ts"]!.filter((l) => !APPROVED["../src/index.ts"]!.includes(l));
      return [name, extra(sites(mutated)), extra(sites(mutated, false)).length < lines.length || name === "rv1-derived-url"];
    });
    expect(got).toEqual(reads.map(([name, lines]) => [name, lines, true]));
    expect(sites(SRC, false)["../src/index.ts"]!.includes(HANDLER_MISS)).toBe(false);
    expect(index.split(HANDLER_MISS).length).toBe(2);
  });

  it("a query, body or alternate-header read in the tier module is refused by its line (the guard seen red)", () => {
    const tier = SRC["../src/accountTier.ts"]!;
    const reads = [
      ".toLowerCase();\n  const q = new URL(req.url).searchParams.get(\"account_token\");",
      ".toLowerCase();\n  const b = await req.clone().json();",
      ".toLowerCase();\n  const h = req.headers.get(\"x-account-token\");",
      ".toLowerCase();\n  /* x */ const h = req.headers.get(\"x-account-token\");",
      ".toLowerCase();\n  */ const h = req.headers.get(\"x-account-token\");",
      ".toLowerCase();\n  * const h = req.headers.get(\"x-account-token\");",
      ".toLowerCase();\n  const h = req.headers.get(\"x-account-token\"); /* fallback */",
      ".toLowerCase();\n  /* v1 */ { const alt = req.headers.get(ACCOUNT_TOKEN_HEADER.replace(\"account\",\"purchase\")); }",
    ];
    for (const read of reads) {
      const mutated = { ...SRC, "../src/accountTier.ts": tier.replace(".toLowerCase();", read) };
      const extra = sites(mutated)["../src/accountTier.ts"]!.filter((l) => !APPROVED["../src/accountTier.ts"]!.includes(l));
      expect(extra).toEqual([read.split("\n")[1]!.trim()]);
      expect(sites(mutated)).not.toEqual(APPROVED);
    }
  });
});
