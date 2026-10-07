/**
 * T-0288: the CONFIG rows - every KV state /config must answer - shared by the ROUTES table (configRoutes.test.ts)
 * and the shipped worker.fetch table (configWorker.test.ts). Each row names its expected overrides and warnings.
 */
import { fakeKv } from "./doFake";
import { configKv, DEFAULTS, FIELDS } from "./configHarness";

export type Row = { name: string; config: unknown; overrides: Record<string, unknown>; warnings: string[] };
const row = (name: string, config: unknown, overrides: Record<string, unknown>, warnings: string[]): Row =>
  ({ name, config, overrides, warnings });

const MAX = 2147483647;
const ALL_INVALID = '{"min_app_build":0,"planning_paused":"1","supported_regions":[],"feature_loop":"false",'
  + '"feature_trip":0,"feature_surprise":null}';
const LOW = { min_app_build: 1, planning_paused: false, supported_regions: ["la"], feature_loop: false, feature_trip: false, feature_surprise: false };
const HIGH = { min_app_build: MAX, planning_paused: true, supported_regions: ["la"], feature_loop: true, feature_trip: true, feature_surprise: true };

export const ROWS: Row[] = [
  row("CONFIG unbound", undefined, {}, []),
  row("config/v1 absent", fakeKv({}), {}, []),
  row("CONFIG throws", fakeKv({}, true), {}, ["record"]),
  row("not JSON", configKv("{"), {}, ["record"]),
  row("empty text", configKv(""), {}, ["record"]),
  row("whitespace-only text", configKv("  \n\t "), {}, ["record"]),
  row("JSON null", configKv("null"), {}, ["record"]),
  row("JSON array", configKv('[{"min_app_build":7}]'), {}, ["record"]),
  row("JSON string", configKv('"min_app_build"'), {}, ["record"]),
  row("JSON number", configKv("7"), {}, ["record"]),
  row("empty object", configKv("{}"), {}, []),
  row("defaults restated", configKv(JSON.stringify(DEFAULTS)), {}, []),
  row("every field invalid", configKv(ALL_INVALID), {}, [...FIELDS]),
  row("every field at its low bound, features off", configKv(JSON.stringify(LOW)), LOW, []),
  row("every field at its high bound, KV pauses", configKv(JSON.stringify(HIGH)), HIGH, []),
  row("KV planning_paused false alone", configKv('{"planning_paused":false}'), { planning_paused: false }, []),
  row("unknown keys beside a valid field", configKv('{"quota":{"anon":{"plan":999}},"min_app_build":7,"kill":false}'),
    { min_app_build: 7 }, ["unknown_keys"]),
  row("__proto__ key", configKv('{"__proto__":{"min_app_build":9},"feature_trip":false}'), { feature_trip: false }, ["unknown_keys"]),
  row("one invalid among valid", configKv(`{"min_app_build":${MAX + 1},"feature_loop":false,"supported_regions":["la"]}`),
    { feature_loop: false, supported_regions: ["la"] }, ["min_app_build"]),
];
/** Rows whose KV pauses on its own, so killed and not-killed answer alike - the only rows allowed to ignore KILL. */
export const KV_PAUSES = ["every field at its high bound, KV pauses"];
