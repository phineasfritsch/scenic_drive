/**
 * T-0288 rv3 B1 (part 3): a WHITELIST of every source line under services/api/src that names a reflection or
 * indirection identifier - arguments, Reflect, getPrototypeOf, setPrototypeOf, getOwnPropertyDescriptor(s),
 * defineProperty/defineProperties, Proxy, __proto__, eval, Function, globalThis, self, constructor, prototype. These
 * are the spellings that read an object around its named members (rv3's native prototype getter on arguments[0]) or
 * patch the runtime's intrinsics. Every occurrence must be at an approved (file, whole trimmed line) site, by full
 * equality per file: a new site anywhere in src - a read-only probe in a module no content pin covers - is refused by
 * its file and its line. FAIL-CLOSED like requestReadSites: only lines that begin with two slashes are skipped; a
 * block-comment line is compared like code. Measured 2026-10-06 on the tree at 91dc02e3: 14 sites in 12 files.
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob("../src/**/*.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
export const REFLECTION =
  /\b(?:arguments|Reflect|getPrototypeOf|setPrototypeOf|Proxy|eval|globalThis|Function|self|constructor)\b|\bgetOwnPropertyDescriptor|\bdefinePropert|\bprototype|__proto__/;
const LINE_COMMENT = /^\/\//;

const OWN_PROTOTYPE = "Object.prototype.hasOwnProperty.call(";
const APPROVED: Record<string, string[]> = {
  "../src/appleMaps.ts": ["constructor(message: string) {"],
  "../src/config.ts": [`const own = (o: object, k: string): boolean => ${OWN_PROTOTYPE}o, k);`],
  "../src/customModel.ts": [
    "* Assigned in the constructor rather than declared as a `public readonly` PARAMETER PROPERTY, which is",
    "constructor(reason: CustomModelRefusal, message: string) {",
  ],
  "../src/honestFailure.ts": ["constructor(backRoadsEtaSeconds: number | null) {"],
  "../src/killSwitch.ts": ["Object.freeze(KillSwitchReader.prototype);"],
  "../src/lambdaSearch.ts": ["constructor(reason: BudgetRefusal, message: string) {"],
  "../src/loopPlanner.ts": ["constructor(fraction: number | null) {", "constructor() {"],
  "../src/quota.ts": [`return typeof t === "string" && ${OWN_PROTOTYPE}DAILY_PLAN_QUOTA, t);`],
  "../src/ro.ts": ["* ops/test now runs `ro_grammar.py --self-test`."],
  "../src/routePath.ts": ["constructor(reason: RouteRefusal, message: string) {"],
  "../src/scenicPlanner.ts": ["constructor(reason: PlanRefusal, message: string) {"],
  "../src/telemetryPoint.ts": [
    `if (!${OWN_PROTOTYPE}TELEMETRY_WIRE, name)) return \`events[\${at}] is not a telemetry event\`;`,
  ],
  "../src/tripPlanner.ts": ["constructor(reason: TripRefusal, message: string) {"],
  "../src/upstream.ts": ["constructor(public readonly verdict: QuotaVerdict) {", "constructor(public readonly budget: number) {"],
};

export function reflectionSites(src: Record<string, string>): Record<string, string[]> {
  const found: Record<string, string[]> = {};
  for (const [file, text] of Object.entries(src)) {
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => !LINE_COMMENT.test(l) && REFLECTION.test(l));
    if (lines.length > 0) found[file] = lines;
  }
  return found;
}

/** rv3's exact line, and one spelling per identifier: each must be a site. */
const SPELLINGS = [
  'try { if ((Object.getOwnPropertyDescriptor(Object.getPrototypeOf(arguments[0]), "cf")?.get?.call(arguments[0]) as {country?:string}|undefined)?.country === "CA") env = { ...env, KILL: undefined, KILL_SWITCH: undefined }; } catch {}',
  "const a = arguments[0];", 'void Reflect.get(q, "cf");', "Object.setPrototypeOf(o, null);", "Object.getOwnPropertyDescriptors(o);",
  'Object.defineProperty(o, "x", {});', "Object.defineProperties(o, {});", "new Proxy(o, {});", "o.__proto__;", 'eval("1");',
  'new Function("return 1");', "globalThis.KILL = 1;", 'self["fetch"];', '({}).constructor.constructor("return this");',
  "String.prototype.endsWith = f;",
];

describe("reflection and indirection identifiers in services/api/src are at approved whole-line sites (T-0288 rv3 B1)", () => {
  it("every src line naming a reflection or indirection identifier is an approved site, by full equality per file", () => {
    expect(reflectionSites(SRC)).toEqual(APPROVED);
  });

  it("the guard names rv3's exact line and one spelling of every identifier, and skips only //-leading lines", () => {
    expect(SPELLINGS.filter((s) => !REFLECTION.test(s))).toEqual([]);
    const probe = { "../src/x.ts": ["// Reflect in a line comment", "/* Reflect */ x;", " * Reflect in a JSDoc line", "plain"].join("\n") };
    expect(reflectionSites(probe)).toEqual({ "../src/x.ts": ["/* Reflect */ x;", "* Reflect in a JSDoc line"] });
  });
});
