/**
 * The place id /search issues for each result and /plan resolves (T-0362 R1-R4, P-PRIV-05).
 *
 * The server never receives more than one coordinate per user action. A searched address therefore never travels back
 * from the device as a coordinate: /search remembers each result's {lat, lon} in PLANS under `plan:<identity>:<id>`
 * and answers only the id; /plan's existing `destination: {place}` carries the id and the Worker reads the coordinate
 * back itself, for the SAME identity only. The id is a negative integer in [-(2^53 - 1), -1]: corpus place ids are
 * always >= 1 (segid.place_id), so the two namespaces never meet and the app's Int64 place path carries both. The key
 * shares plan tokens' per-device prefix, so DELETE /account's sweep reaches it (planSweep.ts).
 */
import type { LatLon } from "./latLon";
import { planKeyPrefix } from "./planToken";

/** The spelling of a searched place id: a minus sign and 1-16 digits with no leading zero. */
export const SEARCH_PLACE_ID = /^-[1-9][0-9]{0,15}$/;
/** 24 h: a search, then a plan, then that plan token's 12 h of reroutes. */
export const SEARCH_PLACE_TTL_SECONDS = 86_400;
/** Ids are minted in [-(2^52), -1]; any id down to -(2^53 - 1) is read, nothing further. */
const MINT_SPAN = 2 ** 52;

/** A searched place id /plan may resolve: the spelling, and a value JavaScript holds exactly. */
export function isSearchPlaceId(id: string): boolean {
  return SEARCH_PLACE_ID.test(id) && Number(id) >= -Number.MAX_SAFE_INTEGER;
}

/** The two KV calls the store makes - a KVNamespace satisfies it. */
export interface SearchPlaceKv {
  get(key: string): Promise<string | null>;
  put(key: string, value: string, options: { expirationTtl: number }): Promise<void>;
}

export interface SearchPlaces {
  /** A fresh id now naming `at` for `identity`, or null when the write failed (the row is then answered without one). */
  remember(identity: string, at: LatLon): Promise<string | null>;
  /** `identity`'s remembered place, or null: unknown, expired, another identity's or malformed. A KV failure throws. */
  recall(identity: string, id: string): Promise<LatLon | null>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function inRange(value: unknown, limit: number): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= -limit && value <= limit;
}

/** A stored value read FAIL-CLOSED: exactly the keys lat and lon, each a finite number in range. */
export function readSearchPlace(text: string | null): LatLon | null {
  if (text === null) return null;
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return null;
  }
  if (!isRecord(value)) return null;
  const keys = Object.keys(value).sort();
  if (keys.length !== 2 || keys[0] !== "lat" || keys[1] !== "lon") return null;
  const { lat, lon } = value;
  if (!inRange(lat, 90) || !inRange(lon, 180)) return null;
  return { lat, lon };
}

function mint(): string {
  const [high, low] = crypto.getRandomValues(new Uint32Array(2));
  return `-${(((high ?? 0) % 2 ** 20) * 2 ** 32 + (low ?? 0)) % MINT_SPAN + 1}`;
}

export function kvSearchPlaces(kv: SearchPlaceKv): SearchPlaces {
  return {
    async remember(identity, at) {
      const id = mint();
      try {
        await kv.put(planKeyPrefix(identity) + id, JSON.stringify({ lat: at.lat, lon: at.lon }),
          { expirationTtl: SEARCH_PLACE_TTL_SECONDS });
      } catch {
        return null;
      }
      return id;
    },
    async recall(identity, id) {
      if (!isSearchPlaceId(id)) return null;
      return readSearchPlace(await kv.get(planKeyPrefix(identity) + id));
    },
  };
}
