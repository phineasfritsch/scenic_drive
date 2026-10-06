/**
 * T-0272 (rv1 BLOCKING): a WHITELIST of every source line under services/api/src that names the request - the
 * identifier req, the type Request - or reads a request member (.headers .url .json .text .formData .arrayBuffer
 * .blob .body .cf, URL, searchParams). The lines found are compared WHOLE (trimmed) to the approved sites below, per
 * file, by full equality: a new site - a query-string fallback, a body read, another header name, a new file that
 * reads the request - is refused by its file and its line. FAIL-CLOSED (rv2): only lines that begin with two slashes
 * are skipped. A line that begins a block comment, closes one, or continues one is compared like code - a block
 * comment can open or close in front of code on the same line - so the JSDoc lines that name a request word are
 * approved sites below, by full equality, like every other line.
 * The tier module's ONLY request read is the one ACCOUNT_TOKEN_HEADER line. T-0278: the session JWT is read at ONE
 * site, routerDeps' identify, by AUTHORIZATION_HEADER; sessionIdentity.ts takes that string and reads no request.
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob("../src/**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const SITE = /\b(req|Request)\b|\.(headers|url|json|text|formData|arrayBuffer|blob|body|cf)\b|\bURL\b|searchParams/;
const LINE_COMMENT = /^\/\//;

const POST_ONLY = 'if (req.method !== "POST") return json({ error: "POST only" }, 405);';
const BODY_READ = "raw = await req.json();";
const TIER_READ = 'const token = (req.headers.get(ACCOUNT_TOKEN_HEADER) ?? "").toLowerCase();';

const APPROVED: Record<string, string[]> = {
  "../src/accountTier.ts": [
    "export async function accountTier(req: Request, db: D1Database | undefined, nowMs: number): Promise<Tier> {",
    TIER_READ,
  ],
  "../src/appleMaps.ts": [
    "* The Apple Maps handoff URL - a port of Sources/Handoff/AppleMapsDirections.swift (T-0248 R7).",
    "* decimals here is not the two-decimal rule: this URL is the user handing their own route to Apple.",
  ],
  "../src/asn.ts": [
    "export async function handleAsn(req: Request, deps: AsnDeps): Promise<Response> {",
    POST_ONLY,
    "body = await req.json();",
    "export async function handleEntitlement(req: Request, deps: AsnDeps): Promise<Response> {",
    'if (req.method !== "GET") return json({ error: "GET only" }, 405);',
    TIER_READ,
  ],
  "../src/attest.ts": [
    "export async function handleAttestChallenge(req: Request, deps: AttestDeps): Promise<Response> {",
    POST_ONLY,
    "export async function handleAttest(req: Request, deps: AttestDeps): Promise<Response> {",
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
    "type Handler = (req: Request, env: Env, url: URL) => Promise<Response>;",
    "const ro: Handler = async (req, env) => {",
    POST_ONLY,
    'const token = req.headers.get("authorization")?.replace(/^Bearer\\s+/i, "") ?? "";',
    'sql = String(((await req.json()) as { sql?: unknown }).sql ?? "");',
    '"/plan": (req, env) => handlePlan(req, env, planDepsFromEnv(env)),',
    '"/loop": (req, env) => handleLoop(req, env, loopDepsFromEnv(env)),',
    '"/isochrone": (req, env) => handleIsochrone(req, env, isochroneDepsFromEnv(env)),',
    '"/trip": (req, env) => handleTrip(req, env, tripDepsFromEnv(env)),',
    '"/asn": (req, env) => handleAsn(req, asnDepsFromEnv(env)),',
    '"/entitlement": (req, env) => handleEntitlement(req, asnDepsFromEnv(env)),',
    '"/attest/challenge": (req, env) => handleAttestChallenge(req, attestDepsFromEnv(env)),',
    '"/attest": (req, env) => handleAttest(req, attestDepsFromEnv(env)),',
    '"/telemetry": (req, env) => handleTelemetry(req, env, telemetryDepsFromEnv(env)),',
    "async fetch(req: Request, env: Env): Promise<Response> {",
    "const url = new URL(req.url);",
    "return handler(req, env, url);",
  ],
  "../src/isochrone.ts": [
    "export async function handleIsochrone(req: Request, env: KillEnv, deps: IsochroneDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    'const buckets = await guardedPlan(deps.upstream, { ...(await deps.identify(req)), kind: "surprise" }, (call) =>',
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
    "const plan = await guardedPlan(upstream, await deps.identify(req), (call) =>",
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
  "../src/telemetry.ts": [
    "export async function handleTelemetry(req: Request, env: KillEnv & SessionEnv, deps: TelemetryDeps | null): Promise<Response> {",
    POST_ONLY,
    BODY_READ,
    "const { userId } = await identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now.getTime(), async () => deviceIdentity(req));",
  ],
  "../src/tripPlanner.ts": ["const path = decodeRoutePath(await response.text());"],
  "../src/upstream.ts": ["return guardedPlan(deps, { userId: args.userId, tier: args.tier }, (call) => call(args.url, args.init));"],
};

/** Every line (bar a //-leading one) of every src file that names the request or reads a request member, trimmed, in order. */
function sites(src: Record<string, string>): Record<string, string[]> {
  const found: Record<string, string[]> = {};
  for (const [file, text] of Object.entries(src).sort(([a], [b]) => a.localeCompare(b))) {
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => !LINE_COMMENT.test(l) && SITE.test(l));
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
    expect(tier.filter((l) => l !== APPROVED["../src/accountTier.ts"]![0])).toEqual([TIER_READ]);
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
