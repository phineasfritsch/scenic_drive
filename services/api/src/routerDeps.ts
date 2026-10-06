/**
 * The production half of /plan's and /loop's deps (T-0256 R1-R3, R7, R8): the quota counters, the router base
 * and the caller's identity, built from env - or null, so the route answers 503 planning_unavailable with zero
 * upstream calls, when ANY of the QUOTA binding, a routable ROUTER_URL or the ROUTER_SECRET secret is missing.
 */
import { accountTier } from "./accountTier";
import type { QuotaCounter } from "./QuotaCounter";
import type { Tier } from "./quota";
import { countersFromNamespace } from "./quotaCounters";
import type { UpstreamDeps } from "./upstream";

/** Every request to our GraphHopper carries this, valued ROUTER_SECRET; the VPS refuses without it (P-COST-03). */
export const ROUTER_SECRET_HEADER = "x-scenic-router-secret";
/** The app's install UUID. Not attested (no App Attest yet, R2): it scopes the daily allowance, nothing more. */
export const DEVICE_HEADER = "x-scenic-device";
/** The one bucket every caller without a well-formed device id shares - fails closed on cost (R2). */
export const UNIDENTIFIED_DEVICE = "unidentified";

const DEVICE_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export interface RouterEnv {
  QUOTA?: DurableObjectNamespace<QuotaCounter>;
  /** https://... of our GraphHopper; `/route` is appended. https://router.invalid is the shipped placeholder. */
  ROUTER_URL?: string;
  /** secret: `wrangler secret put ROUTER_SECRET`. */
  ROUTER_SECRET?: string;
  /** The entitlements table the tier is read from (T-0272); absent, every caller is anon. */
  DB?: D1Database;
}

export interface Identity {
  userId: string;
  tier: Tier;
}

export interface RouterDeps {
  upstream: UpstreamDeps;
  routerBase: string;
  identify(req: Request): Promise<Identity>;
}

/** The router base, or null when ROUTER_URL is absent, not https, or under RFC 2606's reserved .invalid (R8). */
export function routerBase(value: unknown): string | null {
  if (typeof value !== "string") return null;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return null;
  }
  if (url.protocol !== "https:") return null;
  if (url.hostname === "invalid" || url.hostname.endsWith(".invalid")) return null;
  return value.replace(/\/+$/, "");
}

/** Who is calling: the install UUID, lowercased, or the shared unidentified bucket; always anon (R2, R3). */
export function deviceIdentity(req: Request): { userId: string; tier: Tier } {
  const raw = (req.headers.get(DEVICE_HEADER) ?? "").toLowerCase();
  return { userId: DEVICE_ID.test(raw) ? raw : UNIDENTIFIED_DEVICE, tier: "anon" };
}

export function routerDepsFromEnv(env: RouterEnv): RouterDeps | null {
  const base = routerBase(env.ROUTER_URL);
  const secret = env.ROUTER_SECRET;
  if (!env.QUOTA || base === null || typeof secret !== "string" || secret.length === 0) return null;
  const fetchImpl = (url: string, init?: RequestInit): Promise<Response> => {
    const headers = new Headers(init?.headers);
    headers.set(ROUTER_SECRET_HEADER, secret);
    return fetch(url, { ...init, headers });
  };
  const now = () => new Date();
  return {
    upstream: { counters: countersFromNamespace(env.QUOTA), fetchImpl, now, killed: () => false },
    routerBase: base,
    // The bucket is the install (R2); a live entitlement of x-scenic-account-token lifts anon to paid (T-0272 R1-R4).
    identify: async (req) => {
      const device = deviceIdentity(req);
      return (await accountTier(req, env.DB, now().getTime())) === "paid" ? { ...device, tier: "paid" } : device;
    },
  };
}
