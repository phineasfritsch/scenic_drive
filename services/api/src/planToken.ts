/**
 * The plan token (T-0319 R2/R3/R6): what lets a reroute ask for "the rest of THIS drive" while the device sends
 * one 2-dp coordinate and nothing else that locates anyone.
 *
 * Every 200 from /plan is remembered under a fresh token - the device it was planned for, the destination place,
 * the pins it answered and the lambda it chose - in the PLANS KV namespace for PLAN_TOKEN_TTL_SECONDS. A reroute
 * names the token and the index of its first remaining pin; the Worker reads the pins back itself, so they never
 * travel from the device. A token that cannot be used for any reason recalls as null (R5: the fresh plan).
 */
import type { LatLon } from "./latLon";
import { LAMBDA_MAX, LAMBDA_MIN } from "./customModel";
import { MAX_WAYPOINTS } from "./planWaypoints";

/** crypto.randomUUID()'s spelling, lowercase: the only token /plan accepts. */
export const PLAN_TOKEN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
/** 12 h: the longest drive is a fastest of hours plus a 180-minute budget (R3). */
export const PLAN_TOKEN_TTL_SECONDS = 43_200;
const KEY_PREFIX = "plan:";

/** What a plan token remembers. */
export interface RememberedPlan {
  device: string;
  place: string;
  pins: LatLon[];
  lambda: number;
}

/** The two KV calls the store makes - a KVNamespace satisfies it. */
export interface PlanTokenKv {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, options: { expirationTtl: number }): Promise<void>;
}

export interface PlanTokens {
  /** The remembered plan, or null: unknown, expired, unreadable or malformed are all null. */
  recall(token: string): Promise<RememberedPlan | null>;
  /** A fresh token now naming `plan`, or null when the write failed - the plan is answered either way (R6). */
  remember(plan: RememberedPlan): Promise<string | null>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

const finite = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);

function pin(value: unknown): LatLon | null {
  if (!isRecord(value) || !finite(value.lat) || !finite(value.lon)) return null;
  return { lat: value.lat, lon: value.lon };
}

/** The stored text back into a plan, or null when any field is not what remember() wrote. */
export function rememberedPlan(text: string): RememberedPlan | null {
  let raw: unknown;
  try {
    raw = JSON.parse(text);
  } catch {
    return null;
  }
  if (!isRecord(raw) || typeof raw.device !== "string" || typeof raw.place !== "string") return null;
  if (!finite(raw.lambda) || raw.lambda < LAMBDA_MIN || raw.lambda > LAMBDA_MAX) return null;
  if (!Array.isArray(raw.pins) || raw.pins.length > MAX_WAYPOINTS) return null;
  const pins = raw.pins.map(pin);
  if (pins.some((p) => p === null)) return null;
  return { device: raw.device, place: raw.place, pins: pins as LatLon[], lambda: raw.lambda };
}

export function kvPlanTokens(kv: PlanTokenKv, mint: () => string = () => crypto.randomUUID()): PlanTokens {
  return {
    async recall(token) {
      let text: string | null;
      try {
        text = await kv.get(KEY_PREFIX + token);
      } catch {
        return null;
      }
      return text === null ? null : rememberedPlan(text);
    },
    async remember(plan) {
      const token = mint();
      const value = JSON.stringify({ device: plan.device, place: plan.place, pins: plan.pins, lambda: plan.lambda });
      try {
        await kv.put(KEY_PREFIX + token, value, { expirationTtl: PLAN_TOKEN_TTL_SECONDS });
      } catch {
        return null;
      }
      return token;
    },
  };
}
