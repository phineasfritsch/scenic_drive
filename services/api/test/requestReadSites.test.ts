/**
 * T-0272 (rv1 BLOCKING): a WHITELIST of every source line under services/api/src that names the request - the
 * identifier req, the type Request - or reads a request member (.headers .url .json .text .formData .arrayBuffer
 * .blob .body .cf, URL, searchParams). The lines found are compared WHOLE (trimmed) to the approved sites below, per
 * file, by full equality: a new site - a query-string fallback, a body read, another header name, a new file that
 * reads the request - is refused by its file and its line. Only comment lines (leading //, /*, * or * /) are skipped.
 * The tier module's ONLY request read is the one ACCOUNT_TOKEN_HEADER line.
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob("../src/**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const SITE = /\b(req|Request)\b|\.(headers|url|json|text|formData|arrayBuffer|blob|body|cf)\b|\bURL\b|searchParams/;
const COMMENT = /^(\/\/|\/\*|\*\/|\* |\*$)/;

const POST_ONLY = 'if (req.method !== "POST") return json({ error: "POST only" }, 405);';
const BODY_READ = "raw = await req.json();";
const TIER_READ = 'const token = (req.headers.get(ACCOUNT_TOKEN_HEADER) ?? "").toLowerCase();';

const APPROVED: Record<string, string[]> = {
  "../src/accountTier.ts": [
    "export async function accountTier(req: Request, db: D1Database | undefined, nowMs: number): Promise<Tier> {",
    TIER_READ,
  ],
  "../src/asn.ts": [
    "export async function handleAsn(req: Request, deps: AsnDeps): Promise<Response> {",
    POST_ONLY,
    "body = await req.json();",
    "export async function handleEntitlement(req: Request, deps: AsnDeps): Promise<Response> {",
    'if (req.method !== "GET") return json({ error: "GET only" }, 405);',
    TIER_READ,
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
  "../src/routerDeps.ts": [
    "identify(req: Request): Promise<Identity>;",
    "let url: URL;",
    "url = new URL(value);",
    "export function deviceIdentity(req: Request): { userId: string; tier: Tier } {",
    'const raw = (req.headers.get(DEVICE_HEADER) ?? "").toLowerCase();',
    "const headers = new Headers(init?.headers);",
    "identify: async (req) => {",
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
  "../src/tripPlanner.ts": ["const path = decodeRoutePath(await response.text());"],
  "../src/upstream.ts": ["return guardedPlan(deps, { userId: args.userId, tier: args.tier }, (call) => call(args.url, args.init));"],
};

/** Every non-comment line of every src file that names the request or reads a request member, trimmed, in order. */
function sites(src: Record<string, string>): Record<string, string[]> {
  const found: Record<string, string[]> = {};
  for (const [file, text] of Object.entries(src).sort(([a], [b]) => a.localeCompare(b))) {
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => !COMMENT.test(l) && SITE.test(l));
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
    ];
    for (const read of reads) {
      const mutated = { ...SRC, "../src/accountTier.ts": tier.replace(".toLowerCase();", read) };
      const extra = sites(mutated)["../src/accountTier.ts"]!.filter((l) => !APPROVED["../src/accountTier.ts"]!.includes(l));
      expect(extra).toEqual([read.split("\n")[1]!.trim()]);
      expect(sites(mutated)).not.toEqual(APPROVED);
    }
  });
});
