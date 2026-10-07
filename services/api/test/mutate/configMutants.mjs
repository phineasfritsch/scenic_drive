#!/usr/bin/env node
/**
 * Mutation population for GET /config (T-0288 R9): the whitelist, the overlay, the record reader, the more-restrictive
 * planning_paused, the quota display and the cache header (config.ts), and its wiring in ROUTES (index.ts). The
 * telemetryMutants.mjs shape.
 *
 *   node services/api/test/mutate/configMutants.mjs                  run the population
 *   node services/api/test/mutate/configMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/configMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                              run only the named entries
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named
 * failure (a mutant that does not load) is a TRAP and does not count. An anchor that does not occur exactly
 * once is STALE and the run refuses before mutating anything. Pass condition: caught == MUTATIONS.length.
 * THE FLOOR is literal: MIN_MUTATIONS, and every SUBJECT is mutated by at least one entry. EQUIVALENT entries
 * carry a witness - the reason no test CAN tell them apart - and are never run.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-config");

export const MIN_MUTATIONS = 81;
export const SUBJECTS = ["src/config.ts", "src/index.ts"];
const TESTS = ["test/configRoutes.test.ts", "test/configFields.test.ts", "test/routes.test.ts", "test/requestReadSites.test.ts",
  "test/killSwitchRoutes.test.ts", "test/configWorker.test.ts", "test/configAnswerPath.test.ts",
  "test/reflectionSites.test.ts", "test/configSweep.test.ts", "test/sharedEnvWorker.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
const C = "config.ts";
const I = "index.ts";
const ROUTE = "\"/config\": (_req, env) => handleConfig(env),";
const PAUSED = "killed || merged.planning_paused === true";
const MERGE = "const merged = { ...DEFAULTS, ...overlay(await readRecord(env.CONFIG, warnings), warnings) };\n  const killed = await killSwitch(env);";
const URL_LINE = "const url = new URL(req.url);";
const PLAN_ANCHOR = "import { killSwitch, type KillEnv } from \"./killSwitch\";";
const PLAN_HANDLER = "export async function handlePlan(req: Request, env: PlanEnv, deps: PlanDeps | null): Promise<Response> {";
const TELEMETRY_HANDLER = "export async function handleTelemetry(req: Request, env: KillEnv & SessionEnv, deps: TelemetryDeps | null): Promise<Response> {";
const KINDS = "[\"plan\", \"loop\", \"surprise\", \"trip\"]";
const ATTEST_DEPS = "export function attestDepsFromEnv(env: AttestEnv): AttestDeps {";
const FROZEN = "return handler(req, Object.freeze({ ...env }), url);";
const SESSION_VERIFIED = "  if (claims === null) return { userId: UNIDENTIFIED_SESSION, tier: \"anon\" };";
export const MUTATIONS = [
  m("key-v2", C, "CONFIG_KEY = \"config/v1\";", "CONFIG_KEY = \"config/v2\";"),
  m("max-age-60", C, "CONFIG_MAX_AGE_S = 300;", "CONFIG_MAX_AGE_S = 60;"),
  m("cache-private", C, "\"cache-control\": `public, max-age=", "\"cache-control\": `private, max-age="),
  m("content-type-dropped", C, "\"content-type\": \"application/json; charset=utf-8\", ", ""),
  m("status-203", C, "status: 200,", "status: 203,"),
  m("build-low-0", C, "(v as number) >= 1 &&", "(v as number) >= 0 &&"),
  m("build-low-dropped", C, "Number.isInteger(v) && (v as number) >= 1 &&", "Number.isInteger(v) &&"),
  m("build-high-open", C, "(v as number) <= MAX_APP_BUILD", "(v as number) < MAX_APP_BUILD"),
  m("build-high-dropped", C, " && (v as number) <= MAX_APP_BUILD,", ","),
  m("build-max-plus-one", C, "MAX_APP_BUILD = 2_147_483_647;", "MAX_APP_BUILD = 2_147_483_648;"),
  m("build-not-integer", C, "Number.isInteger(v) &&", "typeof v === \"number\" &&"),
  m("paused-any-value", C, "  planning_paused: isBool,", "  planning_paused: (v) => v !== undefined,"),
  m("paused-kv-false-unpauses", C, MERGE, "const kv = overlay(await readRecord(env.CONFIG, warnings), warnings);\n  "
    + "const merged = { ...DEFAULTS, ...kv };\n  const killed = kv.planning_paused === false ? false : await killSwitch(env);"),
  m("paused-kv-ignored", C, PAUSED, "killed"),
  m("paused-kill-ignored", C, PAUSED, "merged.planning_paused === true"),
  m("kill-env-only", C, "await killSwitch(env)", "await killSwitch({ KILL: env.KILL })"),
  m("regions-empty-admitted", C, "v.length >= 1 && ", ""),
  m("regions-duplicates-admitted", C, "new Set(v).size === v.length &&", "true &&"),
  m("regions-any-string", C, "v.every(isRegion)", "v.every((r) => typeof r === \"string\")"),
  m("regions-not-array", C, "Array.isArray(v) && v.length", "v.length"),
  m("regions-case-folded", C, "SUPPORTED_REGIONS.includes(r as string)", "SUPPORTED_REGIONS.includes(String(r).toLowerCase().trim())"),
  m("regions-prefix", C, "SUPPORTED_REGIONS.includes(r as string)",
    "typeof r === \"string\" && SUPPORTED_REGIONS.some((s) => r.startsWith(s))"),
  m("regions-substring", C, "SUPPORTED_REGIONS.includes(r as string)",
    "typeof r === \"string\" && SUPPORTED_REGIONS.some((s) => r.includes(s))"),
  m("regions-truncated", C, "SUPPORTED_REGIONS.includes(r as string)",
    "typeof r === \"string\" && SUPPORTED_REGIONS.some((s) => s.startsWith(r))"),
  m("regions-widened", C, "SUPPORTED_REGIONS: readonly string[] = [\"la\"];", "SUPPORTED_REGIONS: readonly string[] = [\"la\", \"sf\"];"),
  m("feature-loop-any", C, "  feature_loop: isBool,", "  feature_loop: (v) => v !== null,"),
  m("feature-trip-any", C, "  feature_trip: isBool,", "  feature_trip: (v) => v !== null,"),
  m("feature-surprise-any", C, "  feature_surprise: isBool,", "  feature_surprise: (v) => v !== null,"),
  m("default-loop-off", C, "  feature_loop: true,", "  feature_loop: false,"),
  m("default-trip-off", C, "  feature_trip: true,", "  feature_trip: false,"),
  m("default-surprise-off", C, "  feature_surprise: true,", "  feature_surprise: false,"),
  m("default-build-0", C, "  min_app_build: 1,", "  min_app_build: 0,"),
  m("default-paused", C, "  planning_paused: false,", "  planning_paused: true,"),
  m("default-regions-empty", C, "  supported_regions: SUPPORTED_REGIONS,", "  supported_regions: [],"),
  m("record-array-admitted", C, " || Array.isArray(parsed)", ""),
  m("record-null-admitted", C, "parsed === null || ", ""),
  m("record-primitive-admitted", C, "typeof parsed !== \"object\" || ", ""),
  m("record-throw-silent", C, "} catch {\n    warnings.push(\"record\");", "} catch {"),
  m("record-shape-silent", C, "Array.isArray(parsed)) {\n    warnings.push(\"record\");", "Array.isArray(parsed)) {"),
  m("throw-read-as-empty", C, "const text = await kv.get(CONFIG_KEY);", "const text = await kv.get(CONFIG_KEY).catch(() => \"{}\");"),
  m("absent-warns-record", C, "if (text === null) return null;", "if (text === null) throw new Error(\"absent\");"),
  m("blank-as-absent", C, "if (text === null) return null;", "if (text === null || text.trim() === \"\") return null;"),
  m("empty-as-absent", C, "if (text === null) return null;", "if (!text) return null;"),
  m("unknown-silent", C, "if (Object.keys(record).some((k) => !own(FIELDS, k))) warnings.push(\"unknown_keys\");", ""),
  m("unknown-proto-in", C, "!own(FIELDS, k)", "!(k in FIELDS)"),
  m("one-bad-drops-all", C, "else warnings.push(field);", "else { warnings.push(field); return {}; }"),
  m("invalid-admitted", C, "if (FIELDS[field](record[field])) valid[field]", "if (true || FIELDS[field](record[field])) valid[field]"),
  m("warnings-reversed", C, "for (const field of Object.keys(FIELDS) as Field[])", "for (const field of (Object.keys(FIELDS) as Field[]).reverse())"),
  m("absent-field-warns", C, "if (!own(record, field)) continue;", "if (!own(record, field)) { warnings.push(field); continue; }"),
  m("quota-retyped", C, "out[tier][kind] = dailyQuota(kind, tier);",
    "out[tier][kind] = ({ anon: 3, free: 10, paid: 200 } as Record<string, number>)[tier]! * 0 + dailyQuota(kind, tier);"),
  m("quota-telemetry-shown", C, KINDS, "[\"plan\", \"loop\", \"surprise\", \"trip\", \"telemetry\"]"),
  m("quota-trip-dropped", C, KINDS, "[\"plan\", \"loop\", \"surprise\"]"),
  m("quota-tier-dropped", C, "Object.keys(DAILY_PLAN_QUOTA) as Tier[]", "(Object.keys(DAILY_PLAN_QUOTA) as Tier[]).slice(1)"),
  m("quota-surprise-as-plan", C, "dailyQuota(kind, tier)", "dailyQuota(kind === \"surprise\" ? \"plan\" : kind, tier)"),
  m("warnings-dropped", C, "config_warnings: warnings,", "config_warnings: [],"),
  m("extra-key", C, "config_warnings: warnings,", "config_warnings: warnings,\n    config_key: CONFIG_KEY,"),
  m("quota-key-renamed", C, "quota: quotaDisplay(),", "quotas: quotaDisplay(),"),
  m("kill-blocks-config", C, "export async function handleConfig(env: ConfigEnv): Promise<Response> {",
    "export async function handleConfig(env: ConfigEnv): Promise<Response> {\n"
    + "  if (await killSwitch(env)) return new Response(JSON.stringify({ error: \"planning_paused\" }), { status: 503 });"),
  m("route-dropped", I, `  ${ROUTE}\n`, ""),
  m("route-kill-blind", I, ROUTE, "\"/config\": (_req, env) => handleConfig({ ...env, KILL: undefined }),"),
  m("route-kill-switch-blind", I, ROUTE, "\"/config\": (_req, env) => handleConfig({ ...env, KILL_SWITCH: undefined }),"),
  m("route-config-blind", I, ROUTE, "\"/config\": (_req, env) => handleConfig({ ...env, CONFIG: undefined }),"),
  m("route-reads-request", I, ROUTE, "\"/config\": (req, env) => handleConfig(req.headers.get(\"x-scenic-config\") === null ? env : env),"),
  m("route-method-unpause", I, ROUTE, "\"/config\": (_req, env) => handleConfig(_req.method === \"DELETE\" "
    + "? { ...env, KILL: undefined, KILL_SWITCH: undefined } : env),"),
  m("route-options-empty", I, ROUTE,
    "\"/config\": (_req, env) => (_req.method === \"OPTIONS\" ? Promise.resolve(new Response(null, { status: 204 })) : handleConfig(env)),"),
  m("route-method-gated", I, ROUTE,
    "\"/config\": (req, env) => (req.method === \"GET\" ? handleConfig(env) : Promise.resolve(new Response(null, { status: 405 }))),"),
  // T-0288 rv1 B1: unpauses in the SHIPPED worker.fetch gated on a request property (the table drives worker.fetch over
  // request variants; the requestReadSites derived-name guard refuses the line).
  m("fetch-derived-url-unpause", I, URL_LINE, `${URL_LINE}\n    if (url.pathname === "/config" && url.search !== "") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  m("fetch-header-unpause", I, URL_LINE, `${URL_LINE}\n    if (req.headers.has("x-scenic-unpause")) env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  m("fetch-method-unpause", I, URL_LINE, `${URL_LINE}\n    if (req.method === "OPTIONS" || req.method === "HEAD") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  // T-0288 rv2 B1: the same unpause through spellings the text guard does not key on. The behaviour table sees them
  // through its cookie and cf variants; the runtime read recorder sees the read itself (APPROVED_READS = ["url"]).
  m("fetch-reflect-cf-unpause", I, URL_LINE, `${URL_LINE}
    if (Reflect.get(arguments[0], "cf")?.country === "US") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  m("fetch-arguments-cookie-unpause", I, URL_LINE, `${URL_LINE}
    if ((arguments[0] as Request).headers.get("cookie")?.includes("planning_paused=false")) env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  m("fetch-destructure-cf-unpause", I, URL_LINE, `${URL_LINE}
    const { cf } = req as unknown as { cf?: { colo?: string } };
    if (cf?.colo === "LAX") env = { ...env, KILL: undefined, KILL_SWITCH: undefined };`),
  // T-0288 rv3 B1: rv3's exact line - a native prototype getter called on arguments[0], which the read recorder cannot
  // see (the brand check throws on its Proxy). Refused by the content pin (configAnswerPath) and the reflection whitelist.
  m("fetch-proto-getter-cf-unpause", I, URL_LINE, `${URL_LINE}
    try { if ((Object.getOwnPropertyDescriptor(Object.getPrototypeOf(arguments[0]), "cf")?.get?.call(arguments[0]) as {country?:string}|undefined)?.country === "CA") env = { ...env, KILL: undefined, KILL_SWITCH: undefined }; } catch {}`),
  // Its sibling outside the pinned files, spelled by computed members no identifier guard names: plan.ts patches
  // String.prototype.endsWith and JSON.stringify at load and unpauses /config/. The intrinsics snapshot refuses it.
  m("plan-load-intrinsic-patch-unpause", "plan.ts", PLAN_ANCHOR, `${PLAN_ANCHOR}
const SP = String["proto" + "type" as "prototype"];
const EW = SP.endsWith;
let FLAG = false;
SP.endsWith = function (this: string, s: string) { if (this === "/config/") FLAG = true; return EW.call(this, s); };
const JS = JSON.stringify;
JSON.stringify = ((v: any, ...r: any[]) => JS(FLAG && v && v.config_warnings ? { ...v, planning_paused: false } : v, ...r)) as typeof JSON.stringify;`),
  // T-0288 rv4 B1: rv4's exact patch - REQUEST-time, in an unpinned module: the first POST /plan replaces JSON.stringify
  // so every later /config body says planning_paused false under KILL. The post-sweep table (oracle built with the
  // JSON.stringify captured before src loads) and the post-sweep intrinsics snapshot (configSweep.test.ts) refuse it.
  m("plan-request-time-stringify-unpause", "plan.ts", PLAN_HANDLER, `let unpaused = false;
${PLAN_HANDLER}
  if (!unpaused) { unpaused = true; const JS = JSON.stringify; JSON.stringify = ((v: any, ...r: any[]) => JS(v && typeof v === "object" && "planning_paused" in v ? { ...v, planning_paused: false } : v, ...r)) as typeof JSON.stringify; }`),
  // Its sibling: an nth-call patch (the 11th /telemetry call - the first of the sweep's SECOND pass, one pass makes 10)
  // of Response.prototype.text by a computed spelling, rewriting a /config body's planning_paused to false.
  m("telemetry-request-time-nth-text-unpause", "telemetry.ts", TELEMETRY_HANDLER, `let nth = 0;
${TELEMETRY_HANDLER}
  if (++nth === 11) { const RP = (Response as any)["proto" + "type"]; const T = RP.text; RP.text = async function (this: Response) { const t: string = await T.call(this); return t.includes('"config_warnings"') ? t.replace('"planning_paused":true', '"planning_paused":false') : t; }; }`),
  // T-0292 R7: a handler that deletes env.KILL on its first call - in an operational route's deps builder, which runs
  // under KILL=1 - so on a shared env every later request is unpaused. The shared-env sweep refuses it: the frozen env
  // turns the delete into a TypeError the sweep names.
  m("attest-first-call-deletes-kill", "attest.ts", ATTEST_DEPS, `let attestCalls = 0;
${ATTEST_DEPS}
  if (attestCalls++ === 0) delete (env as { KILL?: string }).KILL;`),
  // Its sibling gated on an AUTHENTICATED caller (a verified session JWT): identifyCaller replaces JSON.stringify once,
  // writing planning_paused false into every later /config body. Only the authenticated shared-env sweep makes it fire.
  m("session-authenticated-stringify-unpause", "sessionIdentity.ts", SESSION_VERIFIED, `${SESSION_VERIFIED}
  if (!(JSON.stringify as unknown as { t?: 1 }).t) { const JS = JSON.stringify; JSON.stringify = Object.assign(((v: any, ...r: any[]) => JS(v && typeof v === "object" && "planning_paused" in v ? { ...v, planning_paused: false } : v, ...r)) as typeof JSON.stringify, { t: 1 }); }`),
  // T-0292 R1: the frozen per-request copy. Handing handlers the shared binding object, or an unfrozen copy (a write
  // then succeeds silently on the copy), is refused by the freeze test by name.
  m("fetch-env-shared", I, FROZEN, "return handler(req, env, url);"),
  m("fetch-env-copy-unfrozen", I, FROZEN, "return handler(req, { ...env }, url);"),
  m("fetch-trailing-slash-404", I, "ROUTES[url.pathname.length > 1 && url.pathname.endsWith(\"/\") ? url.pathname.slice(0, -1) : url.pathname]", "ROUTES[url.pathname]"),
];

export const EQUIVALENT = [
  { id: "field-own-to-in", file: "src/config.ts", find: "if (!own(record, field)) continue;", replace: "if (!(field in record)) continue;",
    witness: "the record is JSON.parse output, whose prototype is Object.prototype, and no FIELDS name (min_app_build, "
      + "planning_paused, supported_regions, feature_*) is an Object.prototype member, so `field in record` and the own-"
      + "property test agree on every record JSON can produce; a __proto__ key in the text becomes an OWN property, which "
      + "the unknown_keys check (own(FIELDS, k), mutated by unknown-proto-in) is what sees." },
];

export function floorRefusal(mutations = MUTATIONS, subjects = SUBJECTS) {
  if (mutations.length < MIN_MUTATIONS) return `population ${mutations.length} is below the floor ${MIN_MUTATIONS}`;
  for (const subject of subjects) {
    if (!mutations.some((x) => x.file === subject)) return `subject ${subject} has no mutation`;
  }
  return null;
}

function vitest(extra, tag) {
  mkdirSync(OUT, { recursive: true });
  const report = join(OUT, `${tag}.json`);
  writeFileSync(report, "");
  const bin = join(API, "node_modules", "vitest", "vitest.mjs");
  const run = spawnSync(process.execPath, [bin, "run", ...TESTS, "--reporter=json", `--outputFile=${report}`, ...extra],
    { cwd: API, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  let named = [];
  let total = 0;
  try {
    const parsed = JSON.parse(readFileSync(report, "utf8"));
    total = parsed.numTotalTests;
    for (const file of parsed.testResults) {
      for (const result of file.assertionResults) if (result.status === "failed") named.push(result.title);
    }
  } catch {
    named = [];
  }
  return { status: run.status, named, total };
}

function verdict(run) {
  if (run.named.length > 0) return "CAUGHT";
  return run.status === 0 ? "MISSED" : "TRAP";
}

function main(argv) {
  if (argv.includes("--prove-floor")) {
    const arms = [
      ["empty table", floorRefusal([])],
      ["one short of the floor", floorRefusal(MUTATIONS.slice(0, MIN_MUTATIONS - 1))],
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/index.ts").concat(
        Array.from({ length: MIN_MUTATIONS }, () => MUTATIONS[0])))],
      ["a new subject with none", floorRefusal(MUTATIONS, [...SUBJECTS, "src/newModule.ts"])],
    ];
    for (const [arm, refusal] of arms) console.log(`prove-floor ${arm}: ${refusal === null ? "QUIET (WRONG)" : `REFUSED - ${refusal}`}`);
    const real = floorRefusal();
    console.log(`prove-floor real population: ${real === null ? "quiet" : `REFUSED - ${real}`}`);
    return arms.every(([, r]) => r !== null) && real === null ? 0 : 1;
  }

  const refusal = floorRefusal();
  if (refusal) { console.log(`REFUSING TO RUN: ${refusal}`); return 2; }
  for (const x of [...MUTATIONS, ...EQUIVALENT]) {
    const count = readFileSync(join(API, x.file), "utf8").split(x.find).length - 1;
    if (count !== 1) { console.log(`STALE ${x.id}: anchor occurs ${count} times in ${x.file}`); return 2; }
  }
  const dirty = spawnSync("git", ["status", "--porcelain", "--", "src"], { cwd: API, encoding: "utf8" });
  if (dirty.status !== 0 || dirty.stdout.trim() !== "") { console.log("REFUSING TO RUN: services/api/src is not clean"); return 2; }

  const prove = argv.includes("--prove-vacuity");
  const only = argv.find((a) => a.startsWith("--only="))?.slice("--only=".length).split(",") ?? null;
  const unknown = (only ?? []).filter((id) => !MUTATIONS.some((x) => x.id === id));
  if (only !== null && (only.length === 0 || unknown.length > 0)) { console.log(`REFUSING: unknown --only id(s) ${unknown.join(",")}`); return 2; }
  const run = only === null ? MUTATIONS : MUTATIONS.filter((x) => only.includes(x.id));
  const extra = prove ? ["-t", "^no test is named this$", "--passWithNoTests"] : [];
  console.log(`population mutations=${MUTATIONS.length} (floor ${MIN_MUTATIONS}) equivalent=${EQUIVALENT.length} `
    + `subjects=${SUBJECTS.length} tests=${TESTS.length}${prove ? " PROVE-VACUITY" : ""}${only ? ` ONLY=${run.length}` : ""}`);
  if (!prove) {
    const base = vitest([], "baseline");
    if (base.status !== 0 || base.total === 0) { console.log(`REFUSING: the baseline is not green (${base.named.join("; ")})`); return 2; }
    console.log(`baseline green tests=${base.total}`);
  }

  const tally = { CAUGHT: 0, MISSED: 0, TRAP: 0 };
  for (const x of run) {
    const path = join(API, x.file);
    const original = readFileSync(path, "utf8");
    let result;
    try {
      writeFileSync(path, original.replace(x.find, x.replace));
      result = vitest(extra, x.id);
    } finally {
      writeFileSync(path, original);
    }
    const v = verdict(result);
    tally[v] += 1;
    console.log(`${v.padEnd(6)} ${x.id}${result.named.length ? ` by "${result.named[0]}"` : ""}`);
  }
  console.log(`RESULT caught=${tally.CAUGHT} missed=${tally.MISSED} trap=${tally.TRAP} of ${run.length}`);
  if (prove) return tally.MISSED === run.length ? 0 : 1;
  return tally.CAUGHT === run.length ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main(process.argv.slice(2)));
