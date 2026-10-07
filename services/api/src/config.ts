// GET /config (T-0288): the app's remote config - one closed JSON object built from the compiled DEFAULTS overlaid by
// the KV record CONFIG/config/v1, field by field through the FIELDS whitelist. An invalid field drops to its default
// alone and is named in config_warnings; an unbound CONFIG or an absent key is pure defaults; a CONFIG that throws or
// holds anything but a JSON object is pure defaults with the warning "record". planning_paused is the kill switch OR
// the KV's own true: KV can make it MORE restrictive, never less (a KV false cannot unpause an env KILL=1). The quota
// numbers are quota.ts's, by dailyQuota, never retyped. The handler takes env only - it reads no request - and the
// kill switch never blocks it: the app learns it is paused FROM /config.
import { killSwitch, type KillEnv } from "./killSwitch";
import { DAILY_PLAN_QUOTA, dailyQuota, type QuotaKind, type Tier } from "./quota";

export const CONFIG_KEY = "config/v1";
export const CONFIG_MAX_AGE_S = 300;
export const MAX_APP_BUILD = 2_147_483_647;
export const SUPPORTED_REGIONS: readonly string[] = ["la"];

// The user-facing allowances the app displays; telemetry is not a feature and is not shown.
const DISPLAY_KINDS: readonly QuotaKind[] = ["plan", "loop", "surprise", "trip"];

export interface ConfigEnv extends KillEnv {
  CONFIG?: KVNamespace;
}

const isBool = (v: unknown): boolean => typeof v === "boolean";
const isRegion = (r: unknown): boolean => SUPPORTED_REGIONS.includes(r as string);

// The whitelist: each KV field and the ONLY values it admits (R3). Key order is the answer's and the warnings'.
export const FIELDS = {
  min_app_build: (v) => Number.isInteger(v) && (v as number) >= 1 && (v as number) <= MAX_APP_BUILD,
  planning_paused: isBool,
  supported_regions: (v) => Array.isArray(v) && v.length >= 1 && new Set(v).size === v.length &&
    v.every(isRegion),
  feature_loop: isBool,
  feature_trip: isBool,
  feature_surprise: isBool,
} satisfies Record<string, (v: unknown) => boolean>;
type Field = keyof typeof FIELDS;

export const DEFAULTS: Record<Field, unknown> = {
  min_app_build: 1,
  planning_paused: false,
  supported_regions: SUPPORTED_REGIONS,
  feature_loop: true,
  feature_trip: true,
  feature_surprise: true,
};

const own = (o: object, k: string): boolean => Object.prototype.hasOwnProperty.call(o, k);

async function readRecord(kv: KVNamespace | undefined, warnings: string[]): Promise<Record<string, unknown> | null> {
  if (!kv) return null;
  let parsed: unknown;
  try {
    const text = await kv.get(CONFIG_KEY);
    if (text === null) return null;
    parsed = JSON.parse(text);
  } catch {
    warnings.push("record");
    return null;
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    warnings.push("record");
    return null;
  }
  return parsed as Record<string, unknown>;
}

function overlay(record: Record<string, unknown> | null, warnings: string[]): Partial<Record<Field, unknown>> {
  const valid: Partial<Record<Field, unknown>> = {};
  if (record === null) return valid;
  for (const field of Object.keys(FIELDS) as Field[]) {
    if (!own(record, field)) continue;
    if (FIELDS[field](record[field])) valid[field] = record[field];
    else warnings.push(field);
  }
  if (Object.keys(record).some((k) => !own(FIELDS, k))) warnings.push("unknown_keys");
  return valid;
}

function quotaDisplay(): Record<Tier, Record<string, number>> {
  const out = {} as Record<Tier, Record<string, number>>;
  for (const tier of Object.keys(DAILY_PLAN_QUOTA) as Tier[]) {
    out[tier] = {};
    for (const kind of DISPLAY_KINDS) out[tier][kind] = dailyQuota(kind, tier);
  }
  return out;
}

/** The whole /config answer for `env`. */
export async function configAnswer(env: ConfigEnv): Promise<Record<string, unknown>> {
  const warnings: string[] = [];
  const merged = { ...DEFAULTS, ...overlay(await readRecord(env.CONFIG, warnings), warnings) };
  const killed = await killSwitch(env);
  return {
    ...merged,
    planning_paused: killed || merged.planning_paused === true,
    quota: quotaDisplay(),
    config_warnings: warnings,
  };
}

export async function handleConfig(env: ConfigEnv): Promise<Response> {
  return new Response(JSON.stringify(await configAnswer(env)), {
    status: 200,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${CONFIG_MAX_AGE_S}` },
  });
}
