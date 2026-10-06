/**
 * T-0288 R3/R8: every field of the config/v1 whitelist at every bound, through ROUTES['/config']. Each value rides in a
 * BASE record whose other fields are valid and NOT the defaults, so an invalid field that drops the whole record (or a
 * neighbour) is seen; each row runs under no KILL and env KILL=1. Accepted: the value is in the answer, no warning.
 * Refused: the default is in the answer and config_warnings names exactly that field.
 */
import { describe, expect, it } from "vitest";
import { configKv, DEFAULTS, expected, FIELDS, getConfig } from "./configHarness";

const BASE: Record<string, unknown> = {
  min_app_build: 42, planning_paused: false, supported_regions: ["la"], feature_loop: false, feature_trip: false, feature_surprise: false,
};
const KILLED: [string, Record<string, unknown>, boolean][] = [["no KILL", {}, false], ["env KILL=1", { KILL: "1" }, true]];
const BOOL_REFUSED = ['"true"', '"false"', "1", "0", "null", "[]", "{}", '"1"'];

/** [field, raw JSON text of the value, the parsed value it must answer] - parsed is the answer's, not the text's. */
const ACCEPTED: [string, string, unknown][] = [
  ["min_app_build", "1", 1],
  ["min_app_build", "2", 2],
  ["min_app_build", "1.0", 1],
  ["min_app_build", "1e3", 1000],
  ["min_app_build", "2147483646", 2147483646],
  ["min_app_build", "2147483647", 2147483647],
  ["planning_paused", "true", true],
  ["planning_paused", "false", false],
  ["supported_regions", '["la"]', ["la"]],
  ...["feature_loop", "feature_trip", "feature_surprise"].flatMap((f): [string, string, unknown][] => [[f, "true", true], [f, "false", false]]),
];

const REFUSED: [string, string][] = [
  ...["0", "-1", "0.9999999999999999", "1.5", "2147483647.5", "2147483648", "1e400", "-1e400", '"7"', "true", "null", "[]", "{}", "[7]"]
    .map((raw): [string, string] => ["min_app_build", raw]),
  ...BOOL_REFUSED.map((raw): [string, string] => ["planning_paused", raw]),
  ...["[]", '["la","la"]', '["sf"]', '["LA"]', '[" la"]', '["la","sf"]', '["sf","la"]', '"la"', "[1]", "[null]", "null", "{}", '{"0":"la","length":1}']
    .map((raw): [string, string] => ["supported_regions", raw]),
  ...["feature_loop", "feature_trip", "feature_surprise"].flatMap((f) => BOOL_REFUSED.map((raw): [string, string] => [f, raw])),
];

/** BASE without `field`, then `field` as raw JSON text - so 1e400 and 1.0 reach the parser as written. */
function record(field: string, raw: string): string {
  const rest = Object.fromEntries(Object.entries(BASE).filter(([k]) => k !== field));
  return `${JSON.stringify(rest).slice(0, -1)},"${field}":${raw}}`;
}

describe("config/v1 whitelist at every bound, through ROUTES['/config'] (T-0288)", () => {
  it("the tables cover every field on both sides", () => {
    expect([...new Set(ACCEPTED.map(([f]) => f))]).toEqual(FIELDS);
    expect([...new Set(REFUSED.map(([f]) => f))]).toEqual(FIELDS);
    expect(Object.keys(BASE)).toEqual(FIELDS);
    expect(FIELDS.filter((f) => JSON.stringify(BASE[f]) === JSON.stringify(DEFAULTS[f]))).toEqual(["planning_paused", "supported_regions"]);
  });

  it("every accepted value at its bound is answered, with no warning, under each KILL variant", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [field, raw, value] of ACCEPTED) {
      for (const [kill, source, killed] of KILLED) {
        got.push([field, raw, kill, await getConfig({ ...source, CONFIG: configKv(record(field, raw)) })]);
        want.push([field, raw, kill, expected({ ...BASE, [field]: value }, killed, [])]);
      }
    }
    expect(got).toEqual(want);
  });

  it("every refused value drops that field alone to its default and names it, under each KILL variant", async () => {
    const got: unknown[] = [];
    const want: unknown[] = [];
    for (const [field, raw] of REFUSED) {
      for (const [kill, source, killed] of KILLED) {
        got.push([field, raw, kill, await getConfig({ ...source, CONFIG: configKv(record(field, raw)) })]);
        want.push([field, raw, kill, expected({ ...BASE, [field]: DEFAULTS[field] }, killed, [field])]);
      }
    }
    expect(got).toEqual(want);
  });
});

/** R8: every line of src/config.ts that carries a digit, trimmed, in order - a retyped quota number is a new line. */
const SRC = import.meta.glob("../src/config.ts", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const DIGIT_LINES = [
  'export const CONFIG_KEY = "config/v1";',
  "export const CONFIG_MAX_AGE_S = 300;",
  "export const MAX_APP_BUILD = 2_147_483_647;",
  "min_app_build: (v) => Number.isInteger(v) && (v as number) >= 1 && (v as number) <= MAX_APP_BUILD,",
  "Array.isArray(v) && v.length >= 1 && new Set(v).size === v.length &&",
  "min_app_build: 1,",
];

describe("src/config.ts numerals are a whitelist (T-0288 R1: quota numbers are read from quota.ts, never retyped)", () => {
  it("every line of src/config.ts carrying a digit is an approved whole line", () => {
    const text = SRC["../src/config.ts"] ?? "";
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter((l) => !l.startsWith("//") && /[0-9]/.test(l));
    expect(text.length).toBeGreaterThan(0);
    expect(lines).toEqual(DIGIT_LINES);
  });
});
